import json
import os
import sys
import requests
import re
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from io import BytesIO
import pdfplumber
import PyPDF2
import concurrent.futures
from time import sleep
from datetime import datetime

# --- Configuration ---
MAX_WORKERS = 5
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36'
}
PDF_KEYWORDS = [
    # English
    "download pdf", "pdf document", "full text pdf", "report pdf",
    # Arabic
    "تحميل pdf", "ملف pdf", "نص كامل",
    # Spanish
    "descargar pdf", "documento pdf", 
    # French
    "télécharger pdf", "document pdf"
]

# --- Logging Setup ---
logging.basicConfig(
    filename='content_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

# --- Helper Functions ---
def print_status(message: str, status: str = 'info'):
    colors = {
        'success': '\033[92m', 'error': '\033[91m',
        'warning': '\033[93m', 'info': '\033[94m', 'reset': '\033[0m'
    }
    timestamp = datetime.now().strftime('[%H:%M:%S]')
    print(f"{timestamp} {colors.get(status, '')}{message}{colors['reset']}")

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip() if text else ''

def is_likely_pdf(url: str) -> bool:
    return url.lower().endswith('.pdf')

def get_absolute_url(base: str, relative: str) -> str:
    try:
        return urljoin(base, relative).split('#')[0]
    except:
        return None

# --- Content Extraction ---
def extract_html_content(base_url: str, html: str) -> tuple:
    soup = BeautifulSoup(html, 'html.parser')
    content = []
    pdf_urls = []
    current_heading = "Start of Document"
    paragraphs = []

    # Focus only on main content areas
    main_content = soup.find('main') or soup.find('article') or soup.find('body') or soup

    # Extract headings and paragraphs
    for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element.name.startswith('h'):
            if paragraphs:
                content.append(f"{current_heading}\n{' '.join(paragraphs)}")
            current_heading = clean_text(element.get_text()) or "Unnamed Section"
            paragraphs = []
        elif element.name == 'p':
            text = clean_text(element.get_text())
            if text: 
                paragraphs.append(text)

    if paragraphs:
        content.append(f"{current_heading}\n{' '.join(paragraphs)}")

    # Find PDF links with strict checks
    base_domain = urlparse(base_url).netloc
    for link in main_content.find_all('a', href=True):
        abs_url = get_absolute_url(base_url, link['href'])
        if not abs_url:
            continue

        # Domain verification
        if urlparse(abs_url).netloc != base_domain:
            continue

        # Strict keyword matching
        link_text = clean_text(link.get_text()).lower()
        if any(kw in link_text for kw in PDF_KEYWORDS) and is_likely_pdf(abs_url):
            pdf_urls.append(abs_url)

    return content, pdf_urls

def extract_pdf_content(pdf_bytes: bytes) -> list:
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            full_text = '\n\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
    except:
        return []

    content = []
    current_heading = "PDF Document"
    current_lines = []
    
    for line in full_text.split('\n'):
        line = line.strip()
        if not line: continue
        
        if len(line) < 100 and line[0].isupper() and not line.endswith('.'):
            if current_lines:
                content.append(f"{current_heading}\n{' '.join(current_lines)}")
            current_heading = line
            current_lines = []
        else:
            current_lines.append(line)
    
    if current_lines:
        content.append(f"{current_heading}\n{' '.join(current_lines)}")
    
    return content if content else []

# --- Processing Functions ---
def process_url(url: str) -> tuple:
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        resp.raise_for_status()

        if is_likely_pdf(url):
            content = extract_pdf_content(resp.content)
            return content, []
        else:
            return extract_html_content(url, resp.text)

    except Exception as e:
        return [], []

def process_json_file(json_path: Path):
    print_status(f"Processing {json_path.name}", 'info')
    all_content = []
    processed_urls = set()

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        initial_urls = list({entry.get('url', '').rstrip('/') for entry in data if isinstance(entry, dict)})
        initial_urls = [u for u in initial_urls if u and u.startswith('http')]
    except Exception as e:
        print_status(f"Failed to load JSON: {str(e)}", 'error')
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_url, url): url for url in initial_urls}
        
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                content, pdf_urls = future.result()
                all_content.extend(content)
                
                # Process PDFs from same domain immediately
                for pdf_url in pdf_urls:
                    if pdf_url not in processed_urls:
                        pdf_content, _ = process_url(pdf_url)
                        all_content.extend(pdf_content)
                        processed_urls.add(pdf_url)
                        print_status(f"Processed PDF: {pdf_url}", 'success')
                
                print_status(f"Processed: {url} ({len(content)} sections)", 'success')
            except:
                print_status(f"Failed: {url}", 'error')

    output_file = json_path.with_suffix('.txt')
    try:
        if all_content:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(all_content))
            print_status(f"Saved {len(all_content)} sections to {output_file.name}", 'success')
        else:
            print_status("No content generated", 'warning')
    except Exception as e:
        print_status(f"Failed to save results: {str(e)}", 'error')

# --- Main Execution ---
if __name__ == "__main__":
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(input("Enter directory path: ").strip())
    
    if not input_dir.exists():
        print_status("Invalid directory path", 'error')
        sys.exit(1)

    json_files = list(input_dir.rglob('*.json'))
    json_files = [f for f in json_files if f.is_file()]
    
    if not json_files:
        print_status("No JSON files found", 'warning')
        sys.exit(0)

    print_status(f"Found {len(json_files)} JSON files", 'info')
    
    for idx, json_file in enumerate(json_files, 1):
        print_status(f"Processing file {idx}/{len(json_files)} ({json_file.name})", 'info')
        try:
            process_json_file(json_file)
        except Exception as e:
            print_status(f"Critical error: {str(e)}", 'error')
        sleep(0.1)

    print_status("All files processed", 'success')