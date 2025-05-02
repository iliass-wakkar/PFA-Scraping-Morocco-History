import os
import requests
import json
import hashlib
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
import trafilatura
import logging
from io import BytesIO
import pdfplumber
import PyPDF2
import concurrent.futures

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "Data", "Part1_islam", 
                    "إعادة الفتح البيزنطي (533-550 م)", "Byzantine reconquest (533–550 CE).json"))
OUTPUT_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "Data", "Part1_islam", 
                     "إعادة الفتح البيزنطي (533-550 م)2", "Byzantine reconquest (533–550 CE).json"))
MAX_WORKERS = 3

logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_id(title, url):
    """Create unique ID from title and URL"""
    base_str = f"{title[:50]}{url}".encode('utf-8')
    return hashlib.md5(base_str).hexdigest()[:12]

def clean_text(text):
    """Basic text cleaner preserving multilingual content"""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def extract_structured_content(html):
    """Extract content with hierarchical headings"""
    soup = BeautifulSoup(html, 'html.parser')
    structure = {
        'title': '',
        'sections': []
    }

    # Find main title
    for level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        title_tag = soup.find(level)
        if title_tag:
            structure['title'] = clean_text(title_tag.get_text())
            break
    else:
        title_tag = soup.find('title')
        if title_tag:
            structure['title'] = clean_text(title_tag.get_text())

    # Extract sections
    current_section = {'subtitle': '', 'paragraphs': []}
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element.name.startswith('h'):
            if current_section['subtitle'] or current_section['paragraphs']:
                structure['sections'].append(current_section)
                current_section = {'subtitle': '', 'paragraphs': []}
            current_section['subtitle'] = clean_text(element.get_text())
        else:
            paragraph = clean_text(element.get_text())
            if paragraph:
                current_section['paragraphs'].append(paragraph)

    if current_section['subtitle'] or current_section['paragraphs']:
        structure['sections'].append(current_section)

    return structure

def validate_pdf_url(url):
    """Verify if URL points to a PDF using HEAD request"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
            return True
        if response.status_code != 200:
            logging.warning(f"Non-200 status code for PDF URL: {url}")
        return False
    except Exception as e:
        logging.error(f"HEAD request failed for {url}: {str(e)}")
        return False

def extract_pdf_content(url):
    """Extract structured content from PDFs with validation"""
    if not validate_pdf_url(url):
        return None

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = BytesIO(response.content)
        
        pdf_data = {'full_text': '', 'sections': []}

        # Try both PDF libraries
        for lib in [pdfplumber, PyPDF2]:
            try:
                content.seek(0)  # Reset buffer for each attempt
                if lib == pdfplumber:
                    with pdfplumber.open(content) as pdf:
                        pdf_data['full_text'] = '\n\n'.join(
                            [clean_text(page.extract_text()) for page in pdf.pages]
                        )
                else:
                    reader = lib.PdfReader(content)
                    pdf_data['full_text'] = '\n\n'.join(
                        [clean_text(page.extract_text()) for page in reader.pages]
                    )
                break
            except Exception as e:
                logging.debug(f"{lib.__name__} failed: {str(e)}")
                continue

        if not pdf_data['full_text']:
            return None

        # Extract structure
        current_section = {'subtitle': 'Document', 'paragraphs': []}
        for line in pdf_data['full_text'].split('\n'):
            line = clean_text(line)
            if line:
                if line.isupper() and len(line) < 100:
                    if current_section['paragraphs']:
                        pdf_data['sections'].append(current_section)
                    current_section = {'subtitle': line, 'paragraphs': [line]}
                else:
                    current_section['paragraphs'].append(line)
        if current_section['paragraphs']:
            pdf_data['sections'].append(current_section)

        return pdf_data

    except Exception as e:
        logging.error(f"PDF processing failed for {url}: {str(e)}")
        return None

def find_pdf_links(html, base_url):
    """Find and validate PDF links in HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    pdf_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        
        # Check URL patterns
        if re.search(r'\.pdf($|\?|/)', absolute_url, re.I) or '/pdf' in absolute_url.lower():
            pdf_links.add(absolute_url)

    return list(pdf_links)

def process_entry(entry):
    """Process each entry with enhanced PDF detection"""
    result = {
        "id": generate_id(entry.get('title', ''), entry.get('url', '')),
        "title": clean_text(entry.get('title', '')),
        "summary": clean_text(entry.get('abstract', '')),
        "sources": [{
            "authors": clean_text(entry.get('authors', '')),
            "journal": clean_text(entry.get('journal', '')),
            "year": entry.get('year'),
            "url": entry.get('url')
        }],
        "sections": [],
        "pdf": None,
        "linked_pdfs": []
    }

    try:
        # Direct PDF processing
        if entry['url'].lower().endswith('.pdf'):
            pdf_content = extract_pdf_content(entry['url'])
            if pdf_content:
                result["pdf"] = {
                    "full_text": pdf_content['full_text'][:10000],
                    "sections": pdf_content['sections']
                }
            return result

        # HTML content processing
        response = requests.get(entry['url'], timeout=30)
        response.raise_for_status()

        # Extract main content structure
        content_structure = extract_structured_content(response.text)
        if not result['title']:
            result['title'] = content_structure['title']

        # Format sections
        for section in content_structure['sections']:
            result["sections"].append({
                "subtitle": section['subtitle'],
                "paragraph": '\n\n'.join(section['paragraphs'][:3])
            })

        # Fallback content extraction
        if not result["sections"]:
            extracted = trafilatura.extract(response.text)
            if extracted:
                result["sections"].append({
                    "subtitle": "Main Content",
                    "paragraph": clean_text(extracted)[:2000]
                })

        # Generate summary
        if not result["summary"] and result["sections"]:
            result["summary"] = result["sections"][0]["paragraph"][:300]

        # Find and process PDF links
        pdf_urls = find_pdf_links(response.text, entry['url'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_url = {
                executor.submit(extract_pdf_content, url): url
                for url in pdf_urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                pdf_content = future.result()
                if pdf_content:
                    result["linked_pdfs"].append({
                        "url": future_to_url[future],
                        "full_text": pdf_content['full_text'][:10000],
                        "sections": pdf_content['sections']
                    })

    except Exception as e:
        logging.error(f"Processing failed for {entry.get('url')}: {str(e)}")
        result["error"] = str(e)

    return result

def process_all_entries():
    """Main processing function with concurrency"""
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_entry, entry) for entry in entries]
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                print(f"Processed {len(results)}/{len(entries)} entries")

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Successfully processed {len(results)} entries")

    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        raise

if __name__ == "__main__":
    process_all_entries()