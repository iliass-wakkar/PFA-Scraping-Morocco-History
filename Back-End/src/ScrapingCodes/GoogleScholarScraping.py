# ==============================================
# <<< IMPORTS >>>
# ==============================================
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
import re
from urllib.parse import quote_plus
from pathlib import Path
from fake_useragent import UserAgent
import logging
from datetime import datetime
import sys

# ==============================================
# <<< CONFIGURATION >>>
# ==============================================

# --- Input/Output Configuration ---
DEFAULT_OUTPUT_DIR = Path("../Data/data_raw_auto_retry_hierarchical")
PROXY_FILE = "proxies.txt"

# --- Scraping Parameters ---
PAGES_TO_SCRAPE_PER_LANG = 30
RESULTS_PER_PAGE = 10
DELAY_RANGE_PAGES = (6, 15)
DELAY_RANGE_LANGS = (8, 20)
DELAY_AFTER_EVENT = (5, 10)

# --- Network & Retry Parameters ---
REQUEST_TIMEOUT = 40
MAX_REQUEST_ATTEMPTS = 5
RETRY_DELAY_BASE = 5
MAX_EXP_BACKOFF_DELAY = 120
INITIAL_REQ_DELAY = (1, 3)
MAX_CONSECUTIVE_PAGE_FAILURES = 3

# --- Logging Setup ---
log_file_path = Path(__file__).parent / 'scholar_scraper_auto_retry.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================================
# <<< HELPER FUNCTIONS >>>
# ==============================================

def print_status(message: str, status: str = 'info'):
    """Prints status messages with timestamp and color, and logs."""
    colors = { 'success': '\033[92m', 'error': '\033[91m', 'warning': '\033[93m', 'info': '\033[94m', 'debug': '\033[90m', 'reset': '\033[0m' }
    timestamp = datetime.now().strftime('[%H:%M:%S]')
    print(f"{timestamp} {colors.get(status, colors['info'])}{str(message)}{colors['reset']}")
    if status == 'error': logging.error(message)
    elif status == 'warning': logging.warning(message)
    elif status == 'info' and logger.isEnabledFor(logging.INFO): logging.info(message)
    elif status == 'debug' and logger.isEnabledFor(logging.DEBUG): logging.debug(message)

def sanitize_filename(filename):
    """Remove or replace characters illegal in filenames/folder names."""
    if not isinstance(filename, str): filename = str(filename)
    sanitized = re.sub(r'[\\/*?:"<>|]', '', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = sanitized.strip('_. ')
    max_len = 80
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len].strip('_')
        logger.debug(f"Sanitized name truncated to {len(sanitized)} chars.")
    return sanitized if sanitized else "unnamed_item"

def human_delay(delay_range):
    """Randomized delay between actions."""
    try:
        delay = random.uniform(delay_range[0], delay_range[1])
        logger.debug(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)
    except Exception as e:
        print_status(f"Error during sleep: {e}", "warning")
        time.sleep(delay_range[0])

def clean_arabic_query(query: str) -> str:
    """Cleans Arabic query strings before URL encoding."""
    if not query: return ""
    cleaned = re.sub(r'\s+', ' ', query).strip()
    cleaned = re.sub(r'[%?؟]+', '', cleaned)
    cleaned = cleaned.rstrip('.,;:!؟')
    return cleaned

# ==============================================
# <<< SCHOLAR SCRAPER CLASS >>>
# ==============================================
class ScholarlyScraper:
    """Handles scraping for a single query/language with auto-retries and proxy rotation."""

    def __init__(self, language_code, proxy_list=None):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.language_code = language_code
        self.proxy_list = proxy_list if proxy_list else []
        self._current_proxy_dict = None
        self._current_proxy_str = None
        self._switch_proxy()

    def _get_random_proxy(self):
        if not self.proxy_list: return None
        if len(self.proxy_list) == 1: return self.proxy_list[0]
        possible_proxies = [p for p in self.proxy_list if p != self._current_proxy_str]
        if not possible_proxies: return random.choice(self.proxy_list)
        else: return random.choice(possible_proxies)

    def _switch_proxy(self):
        if not self.proxy_list: 
            self._current_proxy_dict = None
            self._current_proxy_str = None
            return False
        new_proxy_str = self._get_random_proxy()
        if new_proxy_str:
            self._current_proxy_str = new_proxy_str
            protocol = new_proxy_str.split("://")[0]
            if protocol not in ['http', 'https', 'socks5h']: 
                print_status(f"Proxy protocol '{protocol}' assumed http/https.", "warning")
            self._current_proxy_dict = {'http': new_proxy_str, 'https': new_proxy_str}
            masked_proxy = re.sub(r':\/\/(.+?:.+?)@', r'://*****:*****@', new_proxy_str)
            print_status(f"🔄 Switched proxy to: {masked_proxy}", 'info')
            return True
        else: 
            self._current_proxy_dict = None
            self._current_proxy_str = None
            return False

    def get_headers(self):
        return { 
            'User-Agent': self.ua.random, 
            'Accept-Language': f'{self.language_code},en;q=0.9', 
            'Accept-Encoding': 'gzip, deflate, br', 
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 
            'Referer': 'https://scholar.google.com/', 
            'DNT': '1', 
            'Upgrade-Insecure-Requests': '1', 
            'Sec-Fetch-Dest': 'document', 
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Site': 'same-origin', 
        }

    def make_request(self, url):
        """Make request with AUTOMATIC retries, exponential backoff, and proxy rotation."""
        attempts = 0
        if self.proxy_list and self._current_proxy_dict is None: 
            self._switch_proxy()

        while attempts < MAX_REQUEST_ATTEMPTS:
            attempts += 1
            headers = self.get_headers()
            proxies = self._current_proxy_dict

            if attempts == 1: 
                human_delay(INITIAL_REQ_DELAY)

            print_status(f"🔗 Attempt {attempts}/{MAX_REQUEST_ATTEMPTS} [{self.language_code.upper()}]: Requesting: {url[:100]}...", 'info')
            if proxies: 
                logger.debug(f"Using Proxy: {self._current_proxy_str}")

            try:
                response = self.session.get(url, headers=headers, proxies=proxies, timeout=REQUEST_TIMEOUT)
                if response.status_code == 429: 
                    raise requests.exceptions.RequestException(f"⛔ HTTP 429")
                response.raise_for_status()
                return response
            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                print_status(f"⚠️ Attempt {attempts} failed: {e}", 'warning')
                if attempts < MAX_REQUEST_ATTEMPTS:
                    print_status(f"Automatic retry {attempts+1}/{MAX_REQUEST_ATTEMPTS}...", 'info')
                    if self.proxy_list: 
                        self._switch_proxy()
                    backoff_time = RETRY_DELAY_BASE * (2 ** (attempts - 1))
                    backoff_time = min(backoff_time, MAX_EXP_BACKOFF_DELAY)
                    actual_delay = backoff_time + random.uniform(0, backoff_time * 0.3)
                    print_status(f"Applying backoff delay: {actual_delay:.1f}s", "warning")
                    time.sleep(actual_delay)
                else: 
                    print_status(f"🚨 Failed after {MAX_REQUEST_ATTEMPTS} attempts. Giving up.", 'error')
                    return None
        logger.error(f"🚨 Request loop unexpected exit: {url}")
        return None

    def parse_result_item(self, item_soup):
        try:
            title_tag = item_soup.select_one('.gs_rt a')
            title = title_tag.get_text(strip=True) if title_tag else None
            url = title_tag['href'] if title_tag else None
            if not title or not url: 
                return None
            snippet_tag = item_soup.select_one('.gs_rs')
            snippet = snippet_tag.get_text(strip=True).replace('\n', ' ') if snippet_tag else None
            source_line_tag = item_soup.select_one('.gs_a')
            source_line_text = source_line_tag.get_text(strip=True) if source_line_tag else ""
            authors, journal_venue = None, None
            parts = source_line_text.split(' - ')
            if parts:
                authors = parts[0].strip()
                if len(parts) > 1:
                    journal_venue_raw = parts[1].strip()
                    year_match = re.search(r'(?:,\s*|\s+-)\s*(\b\d{4}\b)\s*$', journal_venue_raw)
                    if year_match: 
                        journal_venue = journal_venue_raw[:year_match.start()].strip(', ')
                    else: 
                        journal_venue = journal_venue_raw
                elif len(parts) == 1 and not re.search(r'\d', authors): 
                    pass
                elif len(parts) == 1: 
                    journal_venue, authors = authors, None
            return {
                'title': title, 
                'url': url, 
                'snippet': snippet, 
                'source': {
                    'authors': authors, 
                    'journal_venue': journal_venue
                }
            }
        except Exception as e: 
            logger.error(f"Error parsing result item: {e}", exc_info=False)
            return None

    def _handle_empty_results(self, response, current_page_human, url):
        """Handle cases where no results containers are found (blocking or genuine empty results)."""
        no_results_messages = [
            "did not match any articles",
            "لم تعثر",
            "aucun article", 
            "ningún artículo"
        ]
        
        # Case 1: Genuine "no results" page (no retry needed)
        if any(msg in response.text for msg in no_results_messages):
            print_status(f"✔️ No results found on page {current_page_human} [{self.language_code.upper()}].", 'info')
            return []  # Empty list indicates end of results
        
        # Case 2: Suspicious empty page (likely blocking)
        print_status(
            f"⚠️ No results containers on page {current_page_human} [{self.language_code.upper()}]. Possible blocking.",
            'warning'
        )
        
        while True:
            retry_choice = input("Retry request? (y/n): ").lower().strip()
            if retry_choice == 'y':
                print_status("Retrying request...", 'info')
                human_delay(INITIAL_REQ_DELAY)
                new_response = self.make_request(url)
                if new_response:
                    soup = BeautifulSoup(new_response.text, 'html.parser')
                    raw_results = soup.select('.gs_r.gs_or.gs_scl')
                    if raw_results:  # If results now exist, parse them
                        items_parsed = 0
                        results = []
                        for item_soup in raw_results:
                            parsed_item = self.parse_result_item(item_soup)
                            if parsed_item:
                                results.append(parsed_item)
                                items_parsed += 1
                        print_status(f"📄 Found {items_parsed} items after retry.", 'info')
                        return results
                    # If still no results, will loop again
            elif retry_choice == 'n':
                print_status("Skipping this page.", 'info')
                return []
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")

    def scrape_page(self, page_num, search_query_encoded):
        start_index = page_num * RESULTS_PER_PAGE
        url = f"https://scholar.google.com/scholar?start={start_index}&hl={self.language_code}&as_sdt=0%2C5&q={search_query_encoded}"
        current_page_human = page_num + 1
        response = self.make_request(url)
        
        if response is None:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results_on_page = []
        raw_results = soup.select('.gs_r.gs_or.gs_scl')
        
        if not raw_results:
            return self._handle_empty_results(response, current_page_human, url)
        
        items_parsed = 0
        for item_soup in raw_results:
            parsed_item = self.parse_result_item(item_soup)
            if parsed_item:
                results_on_page.append(parsed_item)
                items_parsed += 1
                
        print_status(f"📄 Found {items_parsed} items on page {current_page_human} [{self.language_code.upper()}].", 'info')
        return results_on_page

    def run_scrape(self, search_query, num_pages):
        """Runs scraping for query/language, handles failures, includes AR query cleaning."""
        search_query_to_encode = search_query
        if self.language_code == 'ar':
            print_status(f"Original AR query: '{search_query}'", 'debug')
            cleaned_query = clean_arabic_query(search_query)
            if cleaned_query != search_query:
                print_status(f"Cleaned AR query : '{cleaned_query}'", 'debug')
            search_query_to_encode = cleaned_query

        print_status(f"🚀 Scrape Start: '{search_query_to_encode}' [{self.language_code.upper()}] for up to {num_pages} pages.", 'info')
        search_query_encoded = quote_plus(search_query_to_encode)

        all_results_for_lang = []
        consecutive_page_failures = 0
        max_consecutive_failures_before_prompt = MAX_CONSECUTIVE_PAGE_FAILURES

        for page_num in range(num_pages):
            page_results = self.scrape_page(page_num, search_query_encoded)

            if page_results is None:
                print_status(f"🚨 Failed definitively page {page_num + 1} for [{self.language_code.upper()}].", 'error')
                consecutive_page_failures += 1
                if consecutive_page_failures >= max_consecutive_failures_before_prompt:
                    print_status(f" Encountered {consecutive_page_failures} consecutive definitive failures.", 'error')
                    while True:
                        skip_lang_choice = input(f"Skip remaining pages for language [{self.language_code.upper()}]? (y/n): ").lower().strip()
                        if skip_lang_choice in ['y', 'n']: 
                            break
                        else: 
                            print("Invalid choice.")
                    if skip_lang_choice == 'y':
                        print_status(f"User skipping remaining pages for [{self.language_code.upper()}].", 'warning')
                        break
                    else:
                        print_status("User continuing...", 'info')
                        consecutive_page_failures = 0
                        print_status("Extra delay...", 'info')
                        human_delay((20, 40))
                        continue
                else:
                    print_status("Attempting next page after definitive failure...", 'info')
                    human_delay((5,10))
                    continue
            elif not page_results:
                consecutive_page_failures = 0
                break
            else:
                consecutive_page_failures = 0
                all_results_for_lang.extend(page_results)
                if page_num < num_pages - 1:
                    human_delay(DELAY_RANGE_PAGES)

        self._current_proxy_dict = None
        self._current_proxy_str = None

        print_status(f"🏁 Scrape Finish: '{search_query_to_encode}' [{self.language_code.upper()}]. Collected {len(all_results_for_lang)} results.", 'info')
        return all_results_for_lang

# ==============================================
# <<< HIERARCHICAL PROCESSING LOGIC >>>
# ==============================================

def scrape_single_event(event_dict, output_json_path, proxy_list):
    event_name = event_dict.get('name')
    if not event_name:
        print_status(f"⚠️ Skip event: missing 'name'", "warning")
        return
    print_status(f"\n--- Processing Event: '{event_name}' ---", "info")
    print_status(f"Output target: {output_json_path}", "info")

    all_language_results = {"en": [], "ar": [], "fr": [], "es": []}
    languages = ['en', 'ar', 'fr', 'es']
    any_language_attempted = False

    for lang_code in languages:
        query_string = event_dict.get(lang_code)
        if not query_string:
            print_status(f"No query for lang '{lang_code}'.", 'debug')
            continue

        any_language_attempted = True
        print_status(f"--- Starting [{lang_code.upper()}] search for '{event_name}' ---", 'info')
        try:
            scraper = ScholarlyScraper(language_code=lang_code, proxy_list=proxy_list)
            lang_results = scraper.run_scrape(query_string, PAGES_TO_SCRAPE_PER_LANG)
            all_language_results[lang_code] = lang_results
            if lang_code != languages[-1]:
                print_status(f"--- Delaying after [{lang_code.upper()}] ---", 'info')
                human_delay(DELAY_RANGE_LANGS)
        except Exception as e:
            print_status(f"🚨 Unhandled exception: event '{event_name}', lang '{lang_code}': {e}", 'error')
            logging.exception(f"Unhandled exception event: {event_name} lang: {lang_code}")

    if any_language_attempted:
        output_data = {
            "event": event_name,
            "scraped_timestamp": datetime.now().isoformat(),
            "results": all_language_results
        }
        try:
            output_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print_status(f"💾 Saved results for '{event_name}' to: {output_json_path.name}", 'success')
        except Exception as e:
            print_status(f"🚨 Error saving data to {output_json_path}: {e}", 'error')
            logging.exception(f"Error saving {output_json_path}")
    else:
        print_status(f"No languages attempted for '{event_name}', nothing saved.", 'warning')

    print_status(f"--- Delaying after event '{event_name}' ---", 'info')
    human_delay(DELAY_AFTER_EVENT)

def process_structure(node, current_output_path: Path, proxy_list):
    if not isinstance(node, dict):
        return
    folder_name_part = None
    if "main_title" in node:
        folder_name_part = sanitize_filename(node["main_title"])
    elif "subtitle" in node:
        folder_name_part = sanitize_filename(node["subtitle"])
    next_output_path = current_output_path
    if folder_name_part:
        next_output_path = current_output_path / folder_name_part
        try:
            next_output_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print_status(f"🚨 Dir create failed '{next_output_path}': {e}. Skip.", 'error')
            return

    if "events" in node and isinstance(node["events"], list):
        print_status(f"Found {len(node['events'])} events under '{folder_name_part or current_output_path.name}'", 'info')
        for event_dict in node["events"]:
            if isinstance(event_dict, dict) and 'name' in event_dict:
                event_name = event_dict.get('name')
                sanitized_event_name = sanitize_filename(event_name)
                event_folder_path = next_output_path / sanitized_event_name
                event_json_filepath = event_folder_path / f"{sanitized_event_name}.json"
                try:
                    event_folder_path.mkdir(parents=True, exist_ok=True)
                    scrape_single_event(event_dict, event_json_filepath, proxy_list)
                except OSError as e:
                    print_status(f"🚨 Event Dir failed '{event_folder_path}': {e}. Skip.", 'error')
                except Exception as e:
                    print_status(f"🚨 Error processing event '{event_name}': {e}", 'error')
                    logging.exception(f"Error scrape_single_event: {event_name}")
            else:
                print_status(f"⚠️ Skipping invalid item in 'events': {event_dict}", "warning")

    if "sub_periods" in node and isinstance(node["sub_periods"], list):
        print_status(f"Found {len(node['sub_periods'])} sub-periods under '{folder_name_part or current_output_path.name}'", 'info')
        for sub_node in node["sub_periods"]:
            process_structure(sub_node, next_output_path, proxy_list)

# ==============================================
# <<< MAIN EXECUTION >>>
# ==============================================

def print_instructions_auto_retry():
    """Updated setup instructions (Auto Retry Version + AR Cleaning)."""
    print("\n" + "="*60)
    print("  GOOGLE SCHOLAR HIERARCHICAL EVENT SCRAPER (Auto Retry + Proxies)")
    print("="*60)
    print("SETUP:")
    print("1. Input File: Prepare hierarchical JSON (e.g., 'events.json').")
    print("2. Output Directory: Choose output folder.")
    print(f"3. Proxy File (Optional): Create '{PROXY_FILE}' with one proxy URL per line.")
    print("   (e.g., http://user:pass@host:port or socks5h://host:port)")
    print("4. Install Dependencies:")
    print("   pip install requests beautifulsoup4 fake-useragent pathlib")
    print("="*60)
    print("HOW IT WORKS:")
    print("- Uses automatic retries with exponential backoff on request failure.")
    print("- Rotates proxies from 'proxies.txt' on failure (if file exists).")
    print("- Cleans Arabic queries (removes %, ?, ؟) before searching.")
    print("- If pages fail consecutively AFTER all retries/proxies, it will PAUSE")
    print("  and ask if you want to skip the rest of the pages for the")
    print("  CURRENT LANGUAGE search (requires manual input).")
    print("="*60 + "\n")

if __name__ == "__main__":
    print_instructions_auto_retry()

    # --- Get Input JSON File ---
    while True:
        input_json_path_str = input("Enter the path to the hierarchical input JSON file: ").strip()
        input_json_path = Path(input_json_path_str)
        if input_json_path.is_file():
            try:
                with open(input_json_path, 'r', encoding='utf-8') as f:
                    data_structure = json.load(f)
                if not isinstance(data_structure, list):
                    raise ValueError("Top level is not LIST.")
                if not data_structure:
                    raise ValueError("JSON list empty.")
                if not isinstance(data_structure[0], dict) or "main_title" not in data_structure[0]:
                    print_status("Warn: 1st item structure?", "warning")
                print_status(f"✔️ Loaded {len(data_structure)} items from {input_json_path.name}", 'success')
                break
            except Exception as e:
                print_status(f"❌ Error loading input: {e}", 'error')
        else:
            print_status(f"❌ File not found: {input_json_path_str}", 'error')
            print("Try again.")

    # --- Get Output Folder ---
    output_dir_str = input(f"Enter base output folder path [default: '{DEFAULT_OUTPUT_DIR}']: ").strip()
    output_dir = Path(output_dir_str) if output_dir_str else DEFAULT_OUTPUT_DIR
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print_status(f"📂 Output directory: {output_dir.resolve()}", 'info')
    except OSError as e:
        print_status(f"🚨 Output dir failed '{output_dir}': {e}.", 'error')
        sys.exit(1)

    # --- Load Proxies (Optional) ---
    proxy_list = []
    proxy_file_path = Path(__file__).parent / PROXY_FILE
    if proxy_file_path.exists():
        try:
            with open(proxy_file_path, 'r') as f_proxy:
                proxy_list = [line.strip() for line in f_proxy if line.strip() and not line.startswith('#')]
            if proxy_list:
                print_status(f"✔️ Loaded {len(proxy_list)} proxies from {proxy_file_path.name}", 'success')
            else:
                print_status(f"⚠️ Proxy file '{proxy_file_path.name}' found but is empty/comments.", 'warning')
        except Exception as e:
            print_status(f"❌ Error reading proxy file '{proxy_file_path.name}': {e}", 'error')
    else:
        print_status(f"Proxy file '{proxy_file_path.name}' not found. No proxies.", 'info')

    # --- Process the entire structure ---
    start_time_all = time.time()
    print_status(f"\n{'#'*25} Starting Hierarchical Processing {'#'*25}", 'info')
    logging.info(f"Run Start. Input: {input_json_path.name}, Output: {output_dir}, Proxies: {len(proxy_list)}")

    total_top_level_items_processed = 0
    try:
        for top_level_node in data_structure:
            if isinstance(top_level_node, dict):
                process_structure(top_level_node, output_dir, proxy_list)
                total_top_level_items_processed += 1
            else:
                print_status(f"⚠️ Skipping invalid top-level item: {type(top_level_node)}", "warning")
    except Exception as e:
        print_status(f"🚨 Critical error during processing loop: {e}", 'error')
        logging.exception("Critical error in main processing loop.")

    # --- End Summary ---
    end_time_all = time.time()
    duration_all = end_time_all - start_time_all
    print_status(f"\n{'='*60}", 'info')
    print_status(f"🏁 Hierarchical processing finished!", 'info')
    print_status(f"Processed {total_top_level_items_processed}/{len(data_structure)} top-level items.", 'info')
    print_status(f"⏱️ Total execution time: {duration_all:.2f}s ({duration_all/60:.2f}m).", 'info')
    print_status(f"📂 Results saved in subfolders within: {output_dir.resolve()}", 'info')
    print_status(f"📜 Log file: {log_file_path.resolve()}", 'info')
    print_status("="*60, 'info')