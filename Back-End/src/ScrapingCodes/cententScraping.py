import json
import requests
import time
import random
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import fitz  # PyMuPDF
import sys
import re

# Configuration
REQUEST_TIMEOUT = 40
RATE_LIMIT_DELAY = (5, 15)  # Random delay between requests in seconds
PDF_LINK_KEYWORDS = {
    # English
    'pdf', 'download', 'document', 'paper', 'article', 'full text', 'report',
    # French
    'télécharger', 'document', 'fichier', 'article', 'texte intégral', 'rapport',
    # Spanish
    'descargar', 'documento', 'artículo', 'texto completo', 'informe',
    # Arabic (transliterated and actual Arabic)
    'تحميل', 'وثيقة', 'ملف', 'مقال', 'نص كامل', 'تقرير',
    'pdf', 'download', 'tasjil', 'malaf'
}

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content using PyMuPDF with enhanced error handling"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        full_text = "\n".join(text).strip()
        
        # Check if text extraction was successful
        if not full_text:
            return "", "PDF appears to be image-based or empty"
            
        return full_text, None
    except Exception as e:
        return "", f"PDF extraction error: {str(e)}"

def is_pdf_link(url, link_text=None):
    """Enhanced PDF link detection with multilingual support"""
    url_lower = url.lower()
    
    # Check URL pattern
    if url_lower.endswith('.pdf'):
        return True
        
    # Check link text for keywords in any language
    if link_text:
        text_lower = link_text.lower()
        for keyword in PDF_LINK_KEYWORDS:
            if keyword in text_lower:
                return True
                
    # Additional check for Arabic PDF indicators
    arabic_pdf_patterns = re.compile(r'\.pdf$|ملف|وثيقة|تحميل', re.IGNORECASE)
    if re.search(arabic_pdf_patterns, url):
        return True
        
    return False

def fetch_url(url):
    """Fetch URL with enhanced error handling and language support"""
    time.sleep(random.uniform(*RATE_LIMIT_DELAY))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7,es;q=0.6'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Handle content encoding
        if response.encoding is None:
            response.encoding = 'utf-8'
            
        return {
            'content': response.content,
            'content_type': response.headers.get('Content-Type', ''),
            'status': 'success',
            'encoding': response.encoding
        }
    except requests.exceptions.RequestException as e:
        return {
            'content': None,
            'content_type': '',
            'status': 'fetch_error',
            'error': str(e)
        }

def scrape_html_content(html_content, base_url, encoding='utf-8'):
    """Extract text and find PDF links from HTML with multilingual support"""
    try:
        # Handle different encodings
        soup = BeautifulSoup(html_content.decode(encoding, errors='replace'), 'html.parser')
        
        # Extract main text content (supporting RTL languages)
        text_parts = []
        for element in soup.find_all(re.compile(r'^h[1-6]$|^p$|^div$|^article$|^section$')):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text_parts.append('\n' + element.get_text(strip=True) + '\n')
            else:
                text_parts.append(element.get_text(strip=True) + '\n')
        
        text_content = '\n'.join(t.strip() for t in text_parts if t.strip())
        
        # Find PDF links with multilingual support
        pdf_links = set()
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            link_text = link.get_text(strip=True) or link.get('title', '')
            
            try:
                absolute_url = urljoin(base_url, href)
            except ValueError:
                continue
                
            # Skip non-HTTP links and anchors
            if absolute_url.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
                
            if is_pdf_link(absolute_url, link_text):
                pdf_links.add((absolute_url, link_text))
        
        return {
            'text': text_content,
            'pdf_links': [{'url': url, 'text': text} for url, text in pdf_links],
            'error': None
        }
    except Exception as e:
        return {
            'text': '',
            'pdf_links': [],
            'error': f"HTML processing error: {str(e)}"
        }

def process_result(original_result):
    """Process a single result with enhanced language support"""
    result = {
        'original_result': original_result,
        'main_url_scrape': {
            'url': original_result['url'],
            'content_type': 'other',
            'scraped_text': '',
            'status': 'pending',
            'error_message': None,
            'encoding': 'utf-8'
        },
        'linked_pdfs_found': []
    }
    
    # Fetch main URL
    main_url = original_result['url']
    fetch_result = fetch_url(main_url)
    
    if fetch_result['status'] != 'success':
        result['main_url_scrape'].update({
            'status': fetch_result['status'],
            'error_message': fetch_result.get('error'),
            'content_type': 'other'
        })
        return result
    
    # Determine content type and encoding
    content_type = fetch_result['content_type'].lower()
    encoding = fetch_result.get('encoding', 'utf-8')
    result['main_url_scrape']['encoding'] = encoding
    
    # Detect content type
    if 'html' in content_type:
        content_type = 'html'
    elif 'pdf' in content_type or main_url.lower().endswith('.pdf'):
        content_type = 'pdf'
    else:
        result['main_url_scrape'].update({
            'status': 'unsupported_type',
            'error_message': f"Unsupported content type: {content_type}"
        })
        return result
    
    result['main_url_scrape']['content_type'] = content_type
    
    try:
        if content_type == 'pdf':
            pdf_text, pdf_error = extract_text_from_pdf(fetch_result['content'])
            result['main_url_scrape']['scraped_text'] = pdf_text
            result['main_url_scrape']['status'] = 'success' if pdf_text else 'content_empty'
            if pdf_error:
                result['main_url_scrape']['error_message'] = pdf_error
                
        elif content_type == 'html':
            html_processing = scrape_html_content(
                fetch_result['content'],
                main_url,
                encoding=encoding
            )
            
            result['main_url_scrape']['scraped_text'] = html_processing['text']
            result['main_url_scrape']['status'] = 'success' if html_processing['text'] else 'content_empty'
            
            if html_processing['error']:
                result['main_url_scrape']['error_message'] = html_processing['error']
            
            # Process linked PDFs if HTML processed
            if result['main_url_scrape']['status'] in ['success', 'content_empty']:
                for pdf_link in html_processing['pdf_links']:
                    pdf_result = {
                        'pdf_url': pdf_link['url'],
                        'link_text': pdf_link['text'],
                        'scraped_text': '',
                        'status': 'pending',
                        'error_message': None
                    }
                    
                    pdf_fetch = fetch_url(pdf_link['url'])
                    if pdf_fetch['status'] != 'success':
                        pdf_result.update({
                            'status': pdf_fetch['status'],
                            'error_message': pdf_fetch.get('error')
                        })
                    else:
                        pdf_text, pdf_error = extract_text_from_pdf(pdf_fetch['content'])
                        pdf_result['scraped_text'] = pdf_text
                        pdf_result['status'] = 'success' if pdf_text else 'content_empty'
                        if pdf_error:
                            pdf_result['error_message'] = pdf_error
                    
                    result['linked_pdfs_found'].append(pdf_result)
                    
    except Exception as e:
        result['main_url_scrape']['status'] = 'scrape_error'
        result['main_url_scrape']['error_message'] = str(e)
    
    return result

def process_json_file(input_path, output_dir):
    """Process a JSON file with enhanced error handling"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {input_path}: {str(e)}")
        return None
    
    output = {
        'event': data.get('event', 'Unknown Event'),
        'scraped_results': {}
    }
    
    for lang, results in data.get('results', {}).items():
        output['scraped_results'][lang] = []
        for idx, original_result in enumerate(results):
            print(f"  Processing {lang} result {idx+1}/{len(results)}")
            processed = process_result(original_result)
            output['scraped_results'][lang].append(processed)
    
    # Create output path
    output_path = output_dir / f"{input_path.stem}_scraped.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        return output_path
    except Exception as e:
        print(f"Error saving {output_path}: {str(e)}")
        return None

def main():
    """Main function with directory processing"""
    input_dir = Path(input("Enter path to directory containing filtered JSON files: ").strip())
    if not input_dir.exists():
        print(f"Error: Directory {input_dir} does not exist")
        sys.exit(1)
        
    output_dir = input_dir.parent / "scraped_results"
    output_dir.mkdir(exist_ok=True)
    
    json_files = list(input_dir.rglob('*.json'))
    if not json_files:
        print("No JSON files found")
        sys.exit(0)
    
    print(f"Found {len(json_files)} files to process")
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"\nProcessing file {idx}/{len(json_files)}: {json_file.name}")
        start_time = time.time()
        
        result_path = process_json_file(json_file, output_dir)
        
        if result_path:
            print(f"  Saved to {result_path} in {time.time()-start_time:.1f}s")
    
    print("\nScraping process completed")

if __name__ == "__main__":
    main()