# -*- coding: utf-8 -*-
"""
Web scraping script with structured, sequential-style logging.
Fetches content from URLs listed in JSON files, extracts text from
HTML and PDF documents (including linked PDFs), and saves structured results.
Logs are grouped by the main URL being processed.
"""

import json
import requests
import time
import sys
import io
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import urljoin, urlparse
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set

# --- Configuration ---

PDF_LINK_KEYWORDS: Set[str] = {
    'pdf', 'download', 'document', 'paper', 'article', 'full text', 'report',
    'télécharger', 'fichier', 'texte intégral', 'rapport', # French
    'descargar', 'documento', 'artículo', 'texto completo', 'informe', # Spanish
    'تحميل', 'وثيقة', 'ملف', 'مقال', 'نص كامل', 'تقرير', 'tasjil', 'malaf' # Arabic
}
MAX_PDF_SIZE: int = 20_000_000  # 20MB
MAX_WORKERS: int = 5 # Reduced for potentially less log interleaving, adjust as needed
REQUEST_TIMEOUT: int = 30
USER_AGENT: str = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/120.0.0.0 Safari/537.36')
ACCEPT_LANGUAGE: str = 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7,es;q=0.6'

# --- Error Handling & Logging Setup ---

class ScrapingError(Exception):
    """Custom exception for general scraping errors."""
    pass

# Fix potential Windows console encoding issues
if sys.platform.startswith('win'):
    try:
        stdout_wrapper = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
        sys.stdout = stdout_wrapper
    except (AttributeError, io.UnsupportedOperation):
        print("Warning: Could not reconfigure sys.stdout for UTF-8.", file=sys.stderr)
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f"Warning: Failed fallback stdout reconfiguration: {e}", file=sys.stderr)

# Configure logging - Simpler format for console readability
log_filename = f'scraping_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S') # Time only for brevity

# File Handler - Detailed logs
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG) # Log everything to file

# Console Handler - Cleaner, less verbose logs (INFO level)
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO) # Show INFO and above on console

# Setup root logger
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler]) # Base level DEBUG to allow file handler

# Silence noisy libraries
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
logging.getLogger("fitz").setLevel(logging.WARNING) # Silence PyMuPDF info/debug

logger = logging.getLogger(__name__)

def log_stage(message: str) -> None:
    """Log processing stage with emphasis."""
    border = "=" * 70
    logger.info(f"\n{border}\n{message.upper():^70}\n{border}")

# --- Core Functions ---

def extract_text_from_pdf(pdf_content: bytes, pdf_url: str) -> Tuple[str, Optional[str]]:
    """Extracts text from PDF bytes. Returns (text, error_message_or_None)."""
    if len(pdf_content) > MAX_PDF_SIZE:
        size_mb = len(pdf_content) / 1_048_576
        msg = f"PDF size {size_mb:.1f} MiB exceeds limit"
        # Logged as WARNING where called
        return "", msg

    logger.debug(f"Starting PDF text extraction for: {pdf_url}")
    start_time = time.time()
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        # Use simple text extraction, join pages with form feed
        text = chr(12).join(page.get_text("text") for page in doc).strip()
        doc.close()
        duration = time.time() - start_time
        logger.debug(f"Extracted {len(text)} chars from PDF {pdf_url} in {duration:.2f}s")
        if not text:
            return "", "No text content found in PDF" # Return specific message
        return text, None
    except Exception as e:
        logger.error(f"PDF extraction failed for {pdf_url}: {e}", exc_info=False) # Keep error brief
        return "", f"PDF processing failed: {e}"

def is_pdf_link(url: str, link_text: Optional[str] = None) -> bool:
    """Checks if a URL likely points to a PDF."""
    if not url: return False
    url_lower = url.lower().strip()
    parsed_url = urlparse(url_lower)
    if parsed_url.path.endswith('.pdf'): return True
    if '.pdf' in parsed_url.query: return True
    if link_text:
        text_lower = link_text.lower()
        if any(keyword in text_lower for keyword in PDF_LINK_KEYWORDS): return True
    return False

def fetch_url(url: str) -> Dict[str, Any]:
    """Fetches a URL. Returns dict with status, content, etc."""
    logger.debug(f"Fetching: {url}")
    headers = {'User-Agent': USER_AGENT, 'Accept-Language': ACCEPT_LANGUAGE, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8'}
    start_time = time.time()
    result = {'status': 'pending', 'final_url': url, 'content': None, 'content_type': None, 'error': None, 'status_code': None}

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        result['status_code'] = response.status_code
        result['final_url'] = response.url
        result['content_type'] = response.headers.get('Content-Type', '').lower()

        response.raise_for_status() # Check for HTTP errors

        result['content'] = response.content
        result['status'] = 'success'
        duration = time.time() - start_time
        size_kb = len(result['content']) / 1024 if result['content'] else 0
        # Log success only at DEBUG level to reduce console noise
        logger.debug(f"Fetch OK: {result['final_url']} [Status:{result['status_code']}] [Size:{size_kb:.1f}KB] [Type:{result['content_type']}] [Time:{duration:.2f}s]")

    except requests.exceptions.Timeout as e:
        result['status'], result['error'] = 'timeout_error', f"Timeout after {REQUEST_TIMEOUT}s"
        logger.warning(f"Fetch Timeout: {url} ({result['error']})")
    except requests.exceptions.HTTPError as e:
        result['status'], result['error'] = 'http_error', f"HTTP Error {result['status_code']}: {response.reason}"
        logger.warning(f"Fetch HTTP Error: {url} ({result['error']})")
    except requests.exceptions.RequestException as e:
        result['status'], result['error'] = 'fetch_error', f"Request failed: {e}"
        logger.warning(f"Fetch Error: {url} ({result['error']})") # Downgrade to WARNING for console
    except Exception as e:
        result['status'], result['error'] = 'fetch_error', f"Unexpected fetch error: {e}"
        logger.error(f"Fetch Unexpected Error: {url} ({result['error']})", exc_info=False)

    return result

def scrape_html_content(html_content: bytes, base_url: str, encoding: Optional[str] = 'utf-8') -> Dict[str, Any]:
    """Parses HTML, extracts text and potential PDF links."""
    logger.debug(f"Parsing HTML from {base_url}")
    result: Dict[str, Any] = {'text': '', 'pdf_links': [], 'error': None}
    try:
        # Determine encoding or let BS4 handle it
        detected_encoding = encoding or 'utf-8' # Fallback needed if requests didn't find one
        try:
             soup = BeautifulSoup(html_content, 'lxml', from_encoding=detected_encoding)
        except FeatureNotFound:
             logger.debug("lxml not found, using html.parser for {base_url}")
             soup = BeautifulSoup(html_content, 'html.parser', from_encoding=detected_encoding)


        # Simplified text extraction
        text_content = ""
        main_sections = soup.find_all(['article', 'main', 'section']) # Try specific tags first
        target_element = main_sections[0] if main_sections else soup.body # Fallback to body

        if target_element:
            # Get text, remove excessive whitespace
            paragraphs = target_element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            text_content = "\n".join( re.sub(r'\s+', ' ', p.get_text()).strip() for p in paragraphs if p.get_text(strip=True))
        result['text'] = text_content.strip()


        # Find PDF links
        pdf_links_found: Set[Tuple[str, str]] = set()
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if not href or href.startswith(('#', 'javascript:', 'mailto:')): continue

            link_text = link.get_text(strip=True) or link.get('title', '') or href

            try:
                absolute_url = urljoin(base_url, href)
                parsed_link = urlparse(absolute_url)
                if parsed_link.scheme not in ('http', 'https'): continue
            except ValueError: continue

            if is_pdf_link(absolute_url, link_text):
                pdf_links_found.add((absolute_url, link_text))
                logger.debug(f"Potential PDF link found: {absolute_url}")

        result['pdf_links'] = [{'url': url, 'text': txt} for url, txt in pdf_links_found]
        logger.debug(f"HTML parsed from {base_url}. Found {len(result['pdf_links'])} PDF links. Extracted ~{len(result['text'])} chars.")

    except Exception as e:
        logger.error(f"HTML parsing failed for {base_url}: {e}", exc_info=False)
        result['error'] = f"HTML parsing failed: {e}"

    return result

def process_pdf_link(pdf_link_info: Dict[str, str], source_url: str) -> Dict[str, Any]:
    """Fetches and extracts text from a single linked PDF."""
    pdf_url = pdf_link_info['url']
    link_text = pdf_link_info['text']
    # Use indentation for sub-task logging
    log_prefix = "  "
    logger.info(f"{log_prefix}Processing Linked PDF: {pdf_url}")

    pdf_data = {'pdf_url': pdf_url, 'link_text': link_text, 'scraped_text': '', 'status': 'pending', 'error_message': None}

    try:
        fetch_result = fetch_url(pdf_url)

        if fetch_result['status'] != 'success':
            pdf_data['status'] = fetch_result['status']
            pdf_data['error_message'] = fetch_result.get('error')
            logger.warning(f"{log_prefix}--> Failed to fetch linked PDF: {pdf_data['status']} ({pdf_data['error_message']})")
            return pdf_data

        content_type = fetch_result['content_type'] or ''
        final_url = fetch_result['final_url']

        # Check if it's actually a PDF
        is_pdf = 'application/pdf' in content_type or final_url.lower().endswith('.pdf')
        if not is_pdf:
            pdf_data['status'] = 'unsupported_type'
            pdf_data['error_message'] = f"Expected PDF, got Content-Type: {content_type}"
            logger.warning(f"{log_prefix}--> Not a PDF: {pdf_url} ({pdf_data['error_message']})")
            return pdf_data

        # Extract text
        extracted_text, extraction_error = extract_text_from_pdf(fetch_result['content'], pdf_url)
        pdf_data['scraped_text'] = extracted_text
        pdf_data['error_message'] = extraction_error

        if extraction_error:
            if "exceeds limit" in extraction_error:
                pdf_data['status'] = 'size_limit_exceeded'
            elif "No text content" in extraction_error:
                pdf_data['status'] = 'content_empty'
            else:
                pdf_data['status'] = 'processing_error'
            logger.warning(f"{log_prefix}--> PDF processing issue: {pdf_data['status']} ({extraction_error})")
        else:
            pdf_data['status'] = 'success'
            logger.info(f"{log_prefix}--> Successfully processed linked PDF ({len(extracted_text)} chars)")

    except Exception as e:
        logger.error(f"{log_prefix}--> Unexpected error processing PDF link {pdf_url}: {e}", exc_info=False)
        pdf_data['status'] = 'processing_error'
        pdf_data['error_message'] = f"Unexpected error: {e}"

    return pdf_data


def process_result(result_item: Dict[str, Any]) -> Dict[str, Any]:
    """Processes a single main URL result, including its linked PDFs sequentially in logs."""
    original_url = result_item.get('url', 'URL_MISSING')
    logger.info(f"Processing Main URL: {original_url}") # Log Start

    output = {
        'original_result': result_item,
        'main_url_scrape': {'url': original_url, 'content_type': 'unknown', 'scraped_text': '', 'status': 'pending', 'error_message': None},
        'linked_pdfs_found': []
    }

    processed_successfully = False # Flag to track if main URL processing was ok

    try:
        # 1. Fetch Main URL
        fetch_result = fetch_url(original_url)
        output['main_url_scrape']['url'] = fetch_result['final_url'] # Update URL

        if fetch_result['status'] != 'success':
            output['main_url_scrape']['status'] = fetch_result['status']
            output['main_url_scrape']['error_message'] = fetch_result.get('error')
            logger.warning(f"--> Failed to fetch main URL: {fetch_result['status']} ({fetch_result.get('error')})")
            # Cannot proceed further with this item
            return output

        # If fetch succeeded, log it briefly
        logger.info(f"--> Fetched main URL successfully [Type: {fetch_result['content_type']}]")

        content = fetch_result['content']
        content_type_header = fetch_result['content_type'] or ''
        encoding = fetch_result.get('encoding') # Encoding might be None
        final_url = fetch_result['final_url']

        # 2. Determine Content Type and Process
        content_type_detected = 'other'
        if 'html' in content_type_header: content_type_detected = 'html'
        elif 'pdf' in content_type_header or final_url.lower().endswith('.pdf'): content_type_detected = 'pdf'

        output['main_url_scrape']['content_type'] = content_type_detected

        # 3a. Process PDF
        if content_type_detected == 'pdf':
            logger.info("--> Content is PDF, extracting text...")
            text, error = extract_text_from_pdf(content, final_url)
            output['main_url_scrape']['scraped_text'] = text
            output['main_url_scrape']['error_message'] = error
            if error:
                status = 'processing_error'
                if "exceeds limit" in error: status = 'size_limit_exceeded'
                elif "No text content" in error: status = 'content_empty'
                output['main_url_scrape']['status'] = status
                logger.warning(f"--> PDF processing issue: {status} ({error})")
            else:
                output['main_url_scrape']['status'] = 'success'
                logger.info(f"--> PDF text extracted successfully ({len(text)} chars)")
                processed_successfully = True

        # 3b. Process HTML
        elif content_type_detected == 'html':
            logger.info("--> Content is HTML, parsing content...")
            html_scrape_result = scrape_html_content(content, final_url, encoding)
            output['main_url_scrape']['scraped_text'] = html_scrape_result['text']
            output['main_url_scrape']['error_message'] = html_scrape_result['error']

            if html_scrape_result['error']:
                output['main_url_scrape']['status'] = 'processing_error'
                logger.error(f"--> HTML parsing failed: {html_scrape_result['error']}")
            elif not html_scrape_result['text']:
                output['main_url_scrape']['status'] = 'content_empty'
                logger.info("--> HTML parsed, but no main text content extracted.")
                processed_successfully = True # Still consider it processed
            else:
                output['main_url_scrape']['status'] = 'success'
                logger.info(f"--> HTML parsed successfully ({len(html_scrape_result['text'])} chars).")
                processed_successfully = True

            # 4. Process Linked PDFs (Only if HTML was parsed)
            pdf_links = html_scrape_result.get('pdf_links', [])
            if pdf_links:
                logger.info(f"--> Found {len(pdf_links)} potential PDF links. Processing them now...")
                processed_pdfs = []
                # Use a nested ThreadPoolExecutor to fetch linked PDFs concurrently
                # but log results sequentially as they complete for THIS main URL.
                with ThreadPoolExecutor(max_workers=max(1, MAX_WORKERS // 2), thread_name_prefix='PdfLinkWorker') as pdf_executor:
                    future_to_pdf = {pdf_executor.submit(process_pdf_link, pdf_info, final_url): pdf_info for pdf_info in pdf_links}
                    for future in as_completed(future_to_pdf):
                        pdf_info = future_to_pdf[future]
                        try:
                            pdf_result = future.result()
                            processed_pdfs.append(pdf_result)
                            # Logging happens *inside* process_pdf_link now
                        except Exception as exc:
                            logger.error(f"  --> Error processing future for linked PDF {pdf_info['url']}: {exc}", exc_info=False)
                            processed_pdfs.append({'pdf_url': pdf_info['url'], 'status': 'future_error', 'error_message': f"Task execution failed: {exc}"})

                output['linked_pdfs_found'] = processed_pdfs
                logger.info(f"--> Finished processing {len(pdf_links)} linked PDFs.")
            elif processed_successfully: # Log only if HTML parsing didn't fail
                logger.info("--> No PDF links found on the page.")

        # 3c. Handle Other Content Types
        else:
            output['main_url_scrape']['status'] = 'unsupported_type'
            output['main_url_scrape']['error_message'] = f"Unsupported Content-Type: {content_type_header}"
            logger.warning(f"--> Unsupported content type: {content_type_header}")

    except Exception as e:
        logger.critical(f"CRITICAL UNHANDLED error processing URL {original_url}: {e}", exc_info=True)
        output['main_url_scrape']['status'] = 'critical_error'
        output['main_url_scrape']['error_message'] = f"Unexpected critical error: {e}"

    logger.info(f"Finished Processing Main URL: {original_url} [Status: {output['main_url_scrape']['status']}]\n") # Log End + Newline
    return output


def process_json_file(input_path: Path, output_dir: Path) -> Optional[Path]:
    """Loads, processes (concurrently per main URL), and saves results for a JSON file."""
    logger.info(f"Starting processing for file: {input_path.name}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        num_entries = sum(len(v) for v in data.get('results', {}).values())
        logger.info(f"Loaded '{input_path.name}' with {num_entries} total results.")
        if num_entries == 0:
            logger.warning(f"'{input_path.name}' contains no results. Skipping.")
            return None
    except Exception as e:
        logger.error(f"Failed to load or parse JSON '{input_path.name}': {e}", exc_info=False)
        return None

    output_data = {
        'event': data.get('event', f'Unknown Event from {input_path.name}'),
        'source_file': str(input_path.relative_to(input_path.parent.parent)),
        'processing_timestamp': datetime.now().isoformat(),
        'scraped_results': {}
    }
    total_processed_count = 0
    file_start_time = time.time()

    for lang, results in data.get('results', {}).items():
        lang_start_time = time.time()
        num_results_lang = len(results)
        if not results:
             logger.info(f"Skipping empty result list for language: '{lang}'")
             output_data['scraped_results'][lang] = []
             continue

        logger.info(f"\n--- Processing Language: '{lang.upper()}' ({num_results_lang} URLs) ---")
        processed_lang_results = []

        # Process main URLs concurrently
        with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix=f'{lang}_MainWorker') as executor:
            future_to_url = {executor.submit(process_result, res): res.get('url') for res in results}
            logger.info(f"Submitted {num_results_lang} main URL tasks for '{lang}'.")

            processed_count_lang = 0
            # as_completed yields results as they finish processing (including nested linked PDFs)
            for future in as_completed(future_to_url):
                url = future_to_url[future] # Get URL for context in case of error
                try:
                    processed_item = future.result() # Contains main scrape + linked pdfs
                    processed_lang_results.append(processed_item)
                    processed_count_lang += 1
                    # Logging now happens *inside* process_result, giving grouped output
                    # We only log overall progress here.
                    if processed_count_lang % 5 == 0 or processed_count_lang == num_results_lang:
                         logger.info(f"    [{lang.upper()}] Progress: {processed_count_lang}/{num_results_lang} main URLs processed.")

                except Exception as exc:
                    logger.error(f"CRITICAL failure in future for URL {url} (lang: {lang}): {exc}", exc_info=True)
                    # Add placeholder? process_result should handle internal errors
                    # This catches errors in the executor/future itself.

        output_data['scraped_results'][lang] = processed_lang_results
        lang_duration = time.time() - lang_start_time
        total_processed_count += num_results_lang
        logger.info(f"--- Finished Language: '{lang.upper()}'. Processed {processed_count_lang}/{num_results_lang} URLs in {lang_duration:.2f}s ---")

    output_filename = f"{input_path.stem}_scraped.json"
    output_path = output_dir / output_filename

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        file_duration = time.time() - file_start_time
        logger.info(f"Successfully saved results for '{input_path.name}' to: {output_path.name}")
        logger.info(f"Total time for file '{input_path.name}': {file_duration:.2f}s")
        return output_path
    except Exception as e:
         logger.error(f"Failed to write output file {output_path.name}: {e}", exc_info=False)
         return None

# --- Main Execution ---

def main() -> None:
    """Main function to drive the scraping process."""
    session_start_time = time.time()
    log_stage("Scraping Session Started")

    try:
        # 1. Get Input Directory
        input_dir_str = input("Enter path to the directory containing filtered JSON files: ").strip()
        input_dir = Path(input_dir_str)
        if not input_dir.is_dir(): raise ScrapingError(f"Not a valid directory: {input_dir}")
        logger.info(f"Input directory: {input_dir.resolve()}")

        # 2. Setup Output Directory
        output_dir = input_dir.parent / f"{input_dir.name}_scraped_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir.resolve()}")

        # 3. Find JSON Files
        json_files = sorted(list(input_dir.rglob('*.json')))
        if not json_files:
            logger.warning(f"No '.json' files found in '{input_dir.resolve()}'.")
            print("No JSON files found to process.")
            return

        logger.info(f"Found {len(json_files)} JSON file(s):")
        for idx, f_path in enumerate(json_files, 1):
            logger.info(f"  {idx}. {f_path.relative_to(input_dir)}") # Cleaner display

        # 4. Confirm Processing
        confirm = input("Press Enter to start processing, or 'N' to cancel: ").strip().lower()
        if confirm in ['n', 'no']:
            logger.info("Processing cancelled by user.")
            print("Operation cancelled.")
            return
        logger.info("User confirmed. Starting processing...")

        # 5. Process Files
        processed_count = 0
        failed_count = 0
        total_files = len(json_files)
        log_stage("Starting File Processing")

        for idx, json_file_path in enumerate(json_files, 1):
            logger.info(f"--- Processing File {idx}/{total_files}: {json_file_path.name} ---")
            output_file = process_json_file(json_file_path, output_dir)
            if output_file:
                processed_count += 1
            else:
                failed_count += 1
            logger.info(f"--- Finished File {idx}/{total_files}: {json_file_path.name} ---\n")

        # 6. Final Summary
        log_stage("Scraping Session Summary")
        session_duration = time.time() - session_start_time
        logger.info(f"Files processed successfully: {processed_count}/{total_files}")
        if failed_count > 0: logger.warning(f"Files failed or skipped: {failed_count}")
        logger.info(f"Total session time: {session_duration:.2f} seconds")
        logger.info(f"Results saved in: {output_dir.resolve()}")
        print(f"\nScraping finished. Results are in: {output_dir.resolve()}")

    except ScrapingError as e:
        logger.error(f"Setup error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
         logger.warning("--- Processing interrupted by user (Ctrl+C) ---")
         print("\nOperation interrupted.")
         sys.exit(1)
    except Exception as e:
        logger.critical(f"Critical unexpected error in main execution: {e}", exc_info=True)
        print(f"\nAn unexpected critical error occurred. Check the log file: {log_filename}")
        sys.exit(1)

    log_stage("Scraping Session Completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Catch final top-level errors
        print(f"\nFATAL ERROR: {e}", file=sys.stderr)
        logger.critical(f"Unhandled exception at entry point: {e}", exc_info=True)
        sys.exit(1)