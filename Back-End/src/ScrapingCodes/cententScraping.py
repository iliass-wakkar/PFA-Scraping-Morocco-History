#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from colorama import Fore, Style, init
from urllib.parse import urljoin

# ====================== CONFIGURATION ======================
REQUEST_TIMEOUT = 40  # seconds
RATE_LIMIT_DELAY_SECONDS = (5, 10)  # min and max delay between requests
PDF_SIZE_LIMIT_MB = 20
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
ACCEPT_LANGUAGE = 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7,es;q=0.6'
PROGRESS_UPDATE_INTERVAL = 10  # Show progress every 10 processed items
MAX_URL_DISPLAY_LENGTH = 50    # Truncate long URLs in messages

PDF_LINK_KEYWORDS = {
    # English
    'pdf', 'download', 'document', 'paper', 'article', 'full text', 'report', 'view',
    # French
    'télécharger', 'document', 'fichier', 'article', 'texte intégral', 'rapport', 'voir', 'pdf',
    # Spanish
    'descargar', 'documento', 'artículo', 'texto completo', 'informe', 'ver', 'pdf',
    # Arabic
    'تحميل', 'وثيقة', 'ملف', 'مقال', 'نص كامل', 'تقرير', 'عرض', 'pdf', 'download', 'tasjil', 'malaf', 'wathiqa', 'taqrir', 'maqal'
}

# ====================== LOGGING SETUP ======================
init(autoreset=True)  # Colorama initialization

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

def setup_logging(output_root: Path):
    log_file = output_root / 'logs' / f'scrape_content_{time.strftime("%Y%m%d_%H%M%S")}.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

# ====================== HELPER FUNCTIONS ======================
def fetch_url(url: str, timeout: int, headers: dict) -> dict:
    """Fetch URL with rate limiting and size checks"""
    time.sleep(random.uniform(*RATE_LIMIT_DELAY_SECONDS))
    
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            stream=True
        )
        response.raise_for_status()

        content_length = int(response.headers.get('Content-Length', 0))
        if content_length > PDF_SIZE_LIMIT_MB * 1024 * 1024:
            return {
                'status': 'fetch_error',
                'error_message': f'Content size {content_length/(1024*1024):.2f}MB exceeds limit',
                'content': None,
                'content_type': response.headers.get('Content-Type', '')
            }

        content = b''
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > PDF_SIZE_LIMIT_MB * 1024 * 1024:
                response.close()
                return {
                    'status': 'fetch_error',
                    'error_message': f'Content size exceeded limit during download',
                    'content': None,
                    'content_type': response.headers.get('Content-Type', '')
                }

        return {
            'status': 'success',
            'content': content,
            'content_type': response.headers.get('Content-Type', ''),
            'error_message': None
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'fetch_error',
            'error_message': str(e),
            'content': None,
            'content_type': ''
        }

def detect_content_type(content_type: str, url: str) -> str:
    """Determine content type from headers and URL"""
    content_type = content_type.lower()
    if 'html' in content_type:
        return 'html'
    if 'pdf' in content_type or url.lower().endswith('.pdf'):
        return 'pdf'
    return 'other'

def scrape_html_content(html_content: bytes, base_url: str) -> dict:
    """Extract text and find PDF links from HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        return {
            'text': '',
            'pdf_links': [],
            'error_message': f'HTML parsing error: {str(e)}'
        }

    text_parts = []
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'article', 'section']):
        if tag.name.startswith('h'):
            text_parts.append('\n' + tag.get_text(strip=True) + '\n')
        else:
            text_parts.append(tag.get_text(strip=True) + '\n')

    full_text = '\n'.join(text_parts).strip()

    pdf_links = []
    seen_urls = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        link_text = link.get_text(strip=True) or link.get('title', '')
        
        try:
            absolute_url = urljoin(base_url, href)
        except ValueError:
            continue
        
        if absolute_url.lower().startswith(('http://', 'https://')):
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)
            
            if is_pdf_link(absolute_url, link_text, PDF_LINK_KEYWORDS):
                pdf_links.append({
                    'url': absolute_url,
                    'text': link_text
                })

    return {
        'text': full_text,
        'pdf_links': pdf_links,
        'error_message': None
    }

def extract_text_from_pdf(pdf_content: bytes) -> Tuple[str, Optional[str]]:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        full_text = "\n".join(text).strip()
        
        if not full_text:
            return "", "PDF appears to be image-based or empty"
        return full_text, None
    except Exception as e:
        return "", f"PDF processing error: {str(e)}"

def is_pdf_link(url: str, link_text: str, keywords: set) -> bool:
    """Determine if a link points to a PDF"""
    url = url.lower()
    link_text = (link_text or '').lower()
    return url.endswith('.pdf') and any(keyword in link_text for keyword in keywords)

# ====================== MAIN PROCESSING ======================
def process_single_result_item(original_result: dict, headers: dict) -> dict:
    """Process one result item from the input JSON"""
    url = original_result.get('url', '')
    display_url = (url[:MAX_URL_DISPLAY_LENGTH] + '...') if len(url) > MAX_URL_DISPLAY_LENGTH else url
    logging.info(f"Starting processing: {display_url}")

    output_item = {
        'original_result': original_result,
        'main_url_scrape': {
            'url': url,
            'content_type': 'unknown',
            'scraped_text': '',
            'status': 'pending',
            'error_message': None
        },
        'linked_pdfs_found': []
    }

    if not url:
        output_item['main_url_scrape'].update({
            'status': 'fetch_error',
            'error_message': 'Missing URL'
        })
        return output_item

    fetch_result = fetch_url(url, REQUEST_TIMEOUT, headers)
    if fetch_result['status'] != 'success':
        output_item['main_url_scrape'].update({
            'content_type': detect_content_type(fetch_result['content_type'], url),
            'status': 'fetch_error',
            'error_message': fetch_result['error_message']
        })
        logging.warning(f"Fetch failed for {display_url}: {fetch_result['error_message']}")
        return output_item

    content_type = detect_content_type(fetch_result['content_type'], url)
    output_item['main_url_scrape']['content_type'] = content_type

    if content_type == 'pdf':
        logging.info(f"Processing PDF: {display_url}")
        if len(fetch_result['content']) > PDF_SIZE_LIMIT_MB * 1024 * 1024:
            output_item['main_url_scrape'].update({
                'status': 'unsupported_type',
                'error_message': f'PDF size exceeds limit'
            })
            return output_item

        pdf_text, pdf_error = extract_text_from_pdf(fetch_result['content'])
        output_item['main_url_scrape']['scraped_text'] = pdf_text
        if pdf_error:
            output_item['main_url_scrape'].update({
                'status': 'scrape_error' if pdf_text else 'content_empty',
                'error_message': pdf_error
            })
        else:
            output_item['main_url_scrape']['status'] = 'success' if pdf_text else 'content_empty'

    elif content_type == 'html':
        logging.info(f"Processing HTML: {display_url}")
        html_result = scrape_html_content(fetch_result['content'], url)
        output_item['main_url_scrape']['scraped_text'] = html_result['text']
        
        if html_result['error_message']:
            output_item['main_url_scrape'].update({
                'status': 'scrape_error',
                'error_message': html_result['error_message']
            })
        else:
            status = 'success' if html_result['text'] else 'content_empty'
            output_item['main_url_scrape']['status'] = status

        if output_item['main_url_scrape']['status'] in ('success', 'content_empty'):
            if html_result['pdf_links']:
                logging.info(f"Found {len(html_result['pdf_links'])} PDF links in {display_url}")
            for pdf_link in html_result['pdf_links']:
                pdf_result = process_linked_pdf(pdf_link, headers)
                output_item['linked_pdfs_found'].append(pdf_result)

    else:
        output_item['main_url_scrape'].update({
            'status': 'unsupported_type',
            'error_message': f'Unsupported content type: {content_type}'
        })

    logging.info(f"Finished {display_url} - Status: {output_item['main_url_scrape']['status'].upper()}")
    return output_item

def process_linked_pdf(pdf_link: dict, headers: dict) -> dict:
    """Process a single linked PDF"""
    pdf_result = {
        'pdf_url': pdf_link['url'],
        'link_text': pdf_link['text'],
        'scraped_text': '',
        'status': 'pending',
        'error_message': None
    }

    fetch_result = fetch_url(pdf_link['url'], REQUEST_TIMEOUT, headers)
    if fetch_result['status'] != 'success':
        pdf_result.update({
            'status': 'fetch_error',
            'error_message': fetch_result['error_message']
        })
        return pdf_result

    content_type = detect_content_type(fetch_result['content_type'], pdf_link['url'])
    if content_type != 'pdf':
        pdf_result.update({
            'status': 'unsupported_type',
            'error_message': f'Not a PDF (Content-Type: {content_type})'
        })
        return pdf_result

    if len(fetch_result['content']) > PDF_SIZE_LIMIT_MB * 1024 * 1024:
        pdf_result.update({
            'status': 'unsupported_type',
            'error_message': f'PDF size exceeds limit'
        })
        return pdf_result

    pdf_text, pdf_error = extract_text_from_pdf(fetch_result['content'])
    pdf_result['scraped_text'] = pdf_text
    if pdf_error:
        pdf_result.update({
            'status': 'scrape_error' if pdf_text else 'content_empty',
            'error_message': pdf_error
        })
    else:
        pdf_result['status'] = 'success' if pdf_text else 'content_empty'

    return pdf_result

# ====================== MAIN EXECUTION ======================
def main():
    parser = argparse.ArgumentParser(description='Scrape content from URLs in JSON files')
    parser.add_argument('input_dir', nargs='?', type=str, 
                      help='Input directory path (will prompt if not provided)')
    args = parser.parse_args()

    if not args.input_dir:
        args.input_dir = input("\nEnter the path to the input directory: ").strip()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"\n{Fore.RED}Error: Directory does not exist{Style.RESET_ALL}")
        sys.exit(1)

    output_root = input_dir.parent / 'scraped_results'
    output_root.mkdir(exist_ok=True)
    setup_logging(output_root)

    headers = {
        'User-Agent': USER_AGENT,
        'Accept-Language': ACCEPT_LANGUAGE
    }

    json_files = list(input_dir.rglob('*.json'))
    if not json_files:
        logging.warning(f"No JSON files found in {input_dir}")
        return

    logging.info(f"Found {len(json_files)} JSON files to process")

    for input_path in json_files:
        relative_path = input_path.relative_to(input_dir)
        output_path = output_root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logging.info(f"\n{'='*50}\nProcessing file: {input_path}")
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load {input_path}: {str(e)}")
            continue

        output_data = {
            'event': data.get('event', 'Unknown Event'),
            'scraped_results': {}
        }

        # Process each language separately
        for lang, results in data.get('results', {}).items():
            logging.info(f"Processing {len(results)} items for language: {lang.upper()}")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(process_single_result_item, result, headers) for result in results]
                lang_results = []
                processed_count = 0
                start_time = time.time()

                for i, future in enumerate(futures):
                    try:
                        result = future.result()
                        lang_results.append(result)
                        processed_count += 1

                        # Progress updates
                        if (i % PROGRESS_UPDATE_INTERVAL == 0) or (time.time() - start_time > 60):
                            elapsed = time.time() - start_time
                            rate = processed_count / elapsed if elapsed > 0 else 0
                            logging.info(
                                f"{lang.upper()} Progress: {processed_count}/{len(results)} "
                                f"({processed_count/len(results):.1%}) | "
                                f"Elapsed: {elapsed:.1f}s | Rate: {rate:.2f} items/s"
                            )
                    except Exception as e:
                        logging.error(f"Error processing item: {str(e)}")

                # Store language-specific results
                output_data['scraped_results'][lang] = lang_results

        # Save complete file after all languages processed
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Successfully saved ALL language results to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save {output_path}: {str(e)}")

        file_time = time.time() - start_time
        logging.info(f"File processing completed in {file_time:.1f} seconds\n{'='*50}")

if __name__ == '__main__':
    main()