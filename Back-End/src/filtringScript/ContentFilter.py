# ==============================================
# <<< IMPORTS >>>
# ==============================================
import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Set
from datetime import datetime
import time

# ==============================================
# <<< CONFIGURATION >>>
# ==============================================
DEFAULT_INPUT_DIR = Path("../Data/data_raw_auto_retry_hierarchical")
DEFAULT_OUTPUT_DIR = Path("data_filtered_final")

MIN_WORD_COUNT = 300  # Configurable word threshold
VALID_TEXT_STATUS = {'success', 'content_empty', 'ok', 'fetch_error'}

# ==============================================
# <<< LOGGING SETUP >>>
# ==============================================
log_file_path = Path(__file__).parent / 'filter_scraped_content.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def print_status(message: str, status: str = 'info'):
    """Color-coded status messages with timestamp"""
    colors = {
        'success': '\033[92m',
        'error': '\033[91m',
        'warning': '\033[93m',
        'info': '\033[94m',
        'debug': '\033[90m',
        'reset': '\033[0m'
    }
    timestamp = datetime.now().strftime('[%H:%M:%S]')
    colored_msg = f"{timestamp} {colors.get(status, colors['info'])}{message}{colors['reset']}"
    print(colored_msg)
    
    if status == 'error':
        logger.error(message)
    elif status == 'warning':
        logger.warning(message)
    else:
        logger.info(message)

# ==============================================
# <<< HELPER FUNCTIONS >>>
# ==============================================
def get_word_count(text: str) -> int:
    """Robust word count calculation"""
    return len(re.findall(r'\b\w+\b', text.strip())) if text else 0

# ==============================================
# <<< CORE PROCESSING >>>
# ==============================================
def process_file(input_path: Path, output_path: Path, processed_urls: Set[str]) -> bool:
    """Process single JSON file with all filtering rules"""
    print_status(f"Processing: {input_path.relative_to(input_path.parent.parent)}", 'debug')
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print_status(f"Error reading {input_path.name}: {str(e)}", 'error')
        return False

    # Initialize filtered data structure
    filtered_data = {
        key: data.get(key) 
        for key in ['event', 'historical_date', 'scraped_timestamp']
        if key in data
    }
    filtered_data['scraped_results'] = {}

    # CRITICAL FIX: Use correct key 'scraped_results' instead of 'results'
    scraped_results = data.get('scraped_results', {})
    kept_items = 0

    for lang, lang_items in scraped_results.items():
        filtered_lang = []
        
        for item in lang_items:
            # Collect all URLs for duplicate check
            item_urls = set()
            main_url = item.get('main_url_scrape', {}).get('url')
            if main_url:
                item_urls.add(main_url)
            
            for pdf in item.get('linked_pdfs_found', []):
                if pdf_url := pdf.get('pdf_url'):
                    item_urls.add(pdf_url)

            # Skip if any URL already processed
            if item_urls & processed_urls:
                logger.debug(f"Skipping duplicate URLs in {input_path.name} [{lang}]")
                continue

            # Process content
            output_item = {
                'original_result': item.get('original_result', {}),
                'main_url_scrape': None,
                'linked_pdfs_found': []
            }
            keep_item = False
            kept_urls = set()

            # Check main URL
            main_scrape = item.get('main_url_scrape')
            if main_scrape:
                status = main_scrape.get('status', '').lower()
                text = main_scrape.get('scraped_text', '')
                url = main_scrape.get('url')
                
                if (status in VALID_TEXT_STATUS and 
                    get_word_count(text) >= MIN_WORD_COUNT and 
                    url):
                    output_item['main_url_scrape'] = main_scrape
                    kept_urls.add(url)
                    keep_item = True

            # Check PDFs
            kept_pdfs = []
            for pdf in item.get('linked_pdfs_found', []):
                status = pdf.get('status', '').lower()
                text = pdf.get('scraped_text', '')
                pdf_url = pdf.get('pdf_url')
                
                if (status in VALID_TEXT_STATUS and 
                    get_word_count(text) >= MIN_WORD_COUNT and 
                    pdf_url):
                    kept_pdfs.append(pdf)
                    kept_urls.add(pdf_url)
                    keep_item = True
            
            output_item['linked_pdfs_found'] = kept_pdfs
            
            if keep_item:
                filtered_lang.append(output_item)
                kept_items += 1
                processed_urls.update(kept_urls)

        if filtered_lang:
            filtered_data['scraped_results'][lang] = filtered_lang

    # Save results
    if kept_items > 0:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            print_status(f"Saved {output_path} ({kept_items} items)", 'success')
            return True
        except Exception as e:
            print_status(f"Error writing {output_path}: {e}", 'error')
            return False
    else:
        print_status(f"No items kept in {input_path.name}", 'info')
        return False

# ==============================================
# <<< INTERACTIVE INPUT HANDLING >>>
# ==============================================
def get_input_directory(default: str = None) -> Path:
    """Prompt for valid input directory"""
    while True:
        path_str = input(f"Enter INPUT directory [default: {DEFAULT_INPUT_DIR}]: ").strip() or default
        path = Path(path_str) if path_str else DEFAULT_INPUT_DIR
        
        if path.exists() and path.is_dir():
            return path.resolve()
        print_status(f"Invalid directory: {path}", 'error')

def get_output_directory(default: str = None) -> Path:
    """Prompt for valid output directory"""
    while True:
        path_str = input(f"Enter OUTPUT directory [default: {DEFAULT_OUTPUT_DIR}]: ").strip() or default
        path = Path(path_str) if path_str else DEFAULT_OUTPUT_DIR
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path.resolve()
        except Exception as e:
            print_status(f"Can't create directory: {e}", 'error')

# ==============================================
# <<< MAIN EXECUTION >>>
# ==============================================
def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(
        description='Filter scraped content by word count and URL duplicates',
        add_help=False
    )
    parser.add_argument('--input_dir', help='Input directory path')
    parser.add_argument('--output_dir', help='Output directory path')
    args = parser.parse_args()

    # Interactive mode if no arguments provided
    if not args.input_dir or not args.output_dir:
        print("\n" + "="*60)
        print("     SCRAPED CONTENT FILTER SCRIPT")
        print("="*60)
        print("Running in interactive mode (press Enter for defaults)\n")
        input_dir = get_input_directory(args.input_dir)
        output_dir = get_output_directory(args.output_dir)
    else:  # Use command-line args
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Processing setup
    print_status(f"\n{'='*40}", 'info')
    print_status(f"INPUT: {input_dir.resolve()}", 'info')
    print_status(f"OUTPUT: {output_dir.resolve()}", 'info')
    print_status(f"MIN WORDS: {MIN_WORD_COUNT}", 'info')
    print_status(f"VALID STATUSES: {VALID_TEXT_STATUS}", 'info')
    print_status(f"{'='*40}\n", 'info')

    processed_urls: Set[str] = set()
    json_files = list(input_dir.rglob('*.json'))
    
    start_time = time.time()
    processed_count = 0
    kept_count = 0

    for input_path in json_files:
        output_path = output_dir / input_path.relative_to(input_dir)
        if process_file(input_path, output_path, processed_urls):
            kept_count += 1
        processed_count += 1

    # Final report
    duration = time.time() - start_time
    print_status(f"\n{'='*60}", 'info')
    print_status(f"PROCESSING COMPLETE", 'success')
    print_status(f"Files processed: {processed_count}", 'info')
    print_status(f"Files with kept content: {kept_count}", 'info')
    print_status(f"Unique URLs tracked: {len(processed_urls)}", 'info')
    print_status(f"Time elapsed: {duration:.2f} seconds", 'info')
    print_status(f"Log file: {log_file_path.resolve()}", 'info')
    print_status(f"{'='*60}", 'info')

if __name__ == '__main__':
    main()