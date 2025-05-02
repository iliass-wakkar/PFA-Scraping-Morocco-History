
**Prompt for AI:**

**Role:** Act as an experienced Python developer specializing in web scraping, data extraction, and data structuring.

**Context:** I am working on a big data project focused on collecting historical information about Moroccan wars and events. The first step involves scraping relevant search results from Google Scholar.

**My Existing Script:**
Below is the Python code for my current Google Scholar scraping script.

**Python**

```
# ==============================================
# <<< import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
import re
from urllib.parse import quote_plus, unquote
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
import subprocess
import logging

# --- Configuration ---
INPUT_QUERIES_FILE = "queries.txt"  # File containing search queries, one per line
# NEW: Base directory where individual query folders will be created
BASE_OUTPUT_DIR = "../Data/Scraped_Results_By_Query"
MAX_PAGES_PER_QUERY = 30           # Max pages to scrape per query
RESULTS_PER_PAGE = 10              # Google Scholar results per page (usually fixed at 10)
DELAY_RANGE = (15, 40)             # Base delay range (seconds) between page requests
INITIAL_BACKOFF_DELAY = 30         # Initial delay (seconds) on blocking/CAPTCHA
MAX_BACKOFF_DELAY = 240            # Maximum backoff delay (seconds)
REQUEST_TIMEOUT = 40               # Timeout for individual HTTP requests
TOR_PASSWORD = "iliass2001"        # Your Tor control port password
USE_TOR = True                     # Set to False to disable Tor/VPN rotation
USE_VPN_FALLBACK = True            # Set to False to disable VPN fallback attempt

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Remove or replace characters illegal in filenames/folder names."""
    # Remove characters that are definitely problematic in most OS
    sanitized = re.sub(r'[\\/*?:"<>|]', '', filename)
    # Replace long whitespace sequences with a single underscore
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove leading/trailing underscores/spaces
    sanitized = sanitized.strip('_ ')
    # Optional: Truncate long names
    max_len = 100
    if len(sanitized) > max_len:
        original_len = len(sanitized)
        # Try to cut at last underscore within limit
        truncated = sanitized[:max_len]
        last_underscore_pos = truncated.rfind('_')
        if last_underscore_pos > max_len / 2 : # Only cut if underscore isn't too early
             sanitized = truncated[:last_underscore_pos]
        else:
             sanitized = truncated # Fallback to simple truncate if no good underscore found
        logger.debug(f"Sanitized name truncated from {original_len} to {len(sanitized)} chars.")

    # Ensure filename is not empty after sanitization
    return sanitized if sanitized else "default_query_name"

class ScholarlyScraper:
    # ... (Keep the __init__, setup_tor, rotate_tor_ip, connect_vpn, disconnect_vpn methods exactly as before) ...
    def __init__(self, search_query, output_file):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.current_proxy = None
        self.controller = None
        self.search_query_raw = search_query # Keep raw query for logging/filenames
        self.search_query_encoded = quote_plus(search_query)
        # output_file now includes the query-specific folder path
        self.output_file = output_file
        self.backoff_delay = INITIAL_BACKOFF_DELAY
        self.tor_enabled = USE_TOR
        self.vpn_fallback_enabled = USE_VPN_FALLBACK

        if self.tor_enabled:
            self.setup_tor()
            if self.controller:
                self.rotate_tor_ip() # Start with a fresh Tor IP

    def setup_tor(self):
        """Initialize Tor connection."""
        if not self.tor_enabled:
            logger.info("Tor usage is disabled in configuration.")
            return
        try:
            self.controller = Controller.from_port(port=9051)
            self.controller.authenticate(password=TOR_PASSWORD)
            logger.info("✅ Tor controller initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Tor controller connection failed: {e}. Check if Tor is running and configured.")
            logger.warning("🔓 Proceeding without Tor/VPN rotation (higher detection risk).")
            self.controller = None
            self.tor_enabled = False # Disable further Tor attempts if setup fails

    def rotate_tor_ip(self):
        """Rotate Tor exit node."""
        if not self.controller:
            logger.debug("Tor controller not available for IP rotation.")
            return False
        try:
            self.controller.signal(Signal.NEWNYM)
            # Wait for Tor circuit to establish
            time.sleep(self.controller.get_newnym_wait())
            self.current_proxy = {
                'http': 'socks5h://localhost:9050', # Use socks5h for DNS resolution via Tor
                'https': 'socks5h://localhost:9050'
            }
            logger.info("🔄 Tor IP rotated successfully.")
            # Reset backoff delay after successful rotation, assuming it fixed the issue
            self.backoff_delay = INITIAL_BACKOFF_DELAY
            return True
        except Exception as e:
            logger.error(f"⚠️ Tor IP rotation failed: {e}")
            return False

    def connect_vpn(self):
        """Connect to VPN as a fallback (example using Windscribe CLI)."""
        if not self.vpn_fallback_enabled:
             logger.info("VPN fallback disabled.")
             return False
        try:
            logger.info("Attempting VPN connection via Windscribe (France)...")
            # Make sure the command works in your terminal first
            # You might need to adjust the command or location
            subprocess.run(["windscribe", "connect", "france"], check=True, timeout=60)
            self.current_proxy = None # VPN affects system globally, no proxy needed in requests
            logger.info("🔒 VPN connected successfully.")
            # Reset backoff delay after successful connection
            self.backoff_delay = INITIAL_BACKOFF_DELAY
            return True
        except FileNotFoundError:
             logger.error("⚠️ VPN connection failed: 'windscribe' command not found. Is Windscribe CLI installed and in PATH?")
             return False
        except subprocess.CalledProcessError as e:
            logger.error(f"⚠️ VPN connection failed: Windscribe command error: {e}")
            return False
        except subprocess.TimeoutExpired:
             logger.error("⚠️ VPN connection failed: Command timed out.")
             return False
        except Exception as e:
            logger.error(f"⚠️ VPN connection failed with unexpected error: {e}")
            return False

    def disconnect_vpn(self):
        """Disconnect VPN (if needed)."""
        if not self.vpn_fallback_enabled:
            return
        try:
            logger.info("Attempting VPN disconnection...")
            subprocess.run(["windscribe", "disconnect"], check=True, timeout=30)
            logger.info("🔌 VPN disconnected.")
        except Exception as e:
            logger.warning(f"⚠️ VPN disconnection failed: {e}")

    def get_headers(self):
        """Generate random headers."""
        return {
            'User-Agent': self.ua.random,
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7', # Broader language acceptance
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/', # More generic referer
            'DNT': '1', # Do Not Track
            'Upgrade-Insecure-Requests': '1'
        }

    def human_delay(self, base_range=DELAY_RANGE):
        """Randomized delay between actions."""
        delay = random.uniform(base_range[0], base_range[1])
        logger.debug(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def make_request(self, url):
        """Make request with retries, Tor/VPN rotation, and exponential backoff."""
        attempts = 0
        max_attempts = 5 # Total attempts for a single URL

        while attempts < max_attempts:
            attempts += 1
            proxies = self.current_proxy
            headers = self.get_headers()
            logger.info(f"🔗 Attempt {attempts}/{max_attempts}: Requesting URL: {url}")
            logger.debug(f"Using Headers: {headers}")
            logger.debug(f"Using Proxies: {proxies}")

            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=REQUEST_TIMEOUT
                )

                # Check for CAPTCHA or blocking patterns
                if "CAPTCHA" in response.text or "recaptcha" in response.text or response.status_code == 429:
                    raise requests.exceptions.RequestException("⛔ CAPTCHA or block detected")

                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                logger.info(f"✅ Request successful (Status: {response.status_code})")
                return response

            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Request attempt {attempts} timed out.")
                if not self.try_rotation_strategies():
                     logger.error("🚨 Rotation strategies failed after timeout. Giving up on this URL.")
                     return None

            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Request attempt {attempts} failed: {e}")
                if "CAPTCHA" in str(e) or "block" in str(e) or "429" in str(e):
                    logger.warning(f"🚨 Block detected! Initiating backoff: {self.backoff_delay}s")
                    time.sleep(self.backoff_delay)
                    self.backoff_delay = min(self.backoff_delay * 2, MAX_BACKOFF_DELAY)
                    if not self.try_rotation_strategies():
                         logger.error("🚨 Rotation strategies failed after block. Giving up on this URL.")
                         return None
                else:
                    time.sleep(5)

            time.sleep(random.uniform(1, 3))

        logger.error(f"🚨 Request failed after {max_attempts} attempts for URL: {url}")
        return None

    def try_rotation_strategies(self):
        """Attempt Tor rotation, then VPN connection as fallback."""
        if self.tor_enabled and self.rotate_tor_ip():
            return True
        elif self.vpn_fallback_enabled and self.connect_vpn():
            return True
        else:
             logger.warning("⚠️ Both Tor rotation and VPN fallback failed or are disabled.")
             return False

    def parse_source(self, source_text):
        """Parse author/journal/year from source line more robustly."""
        authors = None
        journal = None
        year = None
        try:
            parts = source_text.split(' - ')
            authors = parts[0].strip()
            if len(parts) > 1:
                year_match = re.search(r'\b(\d{4})\b', parts[1])
                if year_match:
                    year = year_match.group(1)
                    journal = parts[1].split(year)[0].strip(', ')
                else:
                    journal = parts[1].strip()
                if year is None and len(parts) > 2:
                     year_match_p3 = re.search(r'\b(\d{4})\b', parts[2])
                     if year_match_p3:
                         year = year_match_p3.group(1)
                         if not journal: journal = parts[1].strip() # Journal might still be in part 2
            authors = authors if authors else None
            journal = journal if journal else None
            year = int(year) if year else None
        except Exception as e:
            logger.warning(f"⚠️ Could not parse source string: '{source_text}'. Error: {e}")
        return {'authors': authors, 'journal': journal, 'year': year}

    def scrape_page(self, page_num):
        """Scrape a single page."""
        start_index = page_num * RESULTS_PER_PAGE
        url = f"https://scholar.google.com/scholar?start={start_index}&hl=en&as_sdt=0%2C5&q={self.search_query_encoded}"
        current_page_human = page_num + 1
        logger.info(f"\n📖 Scraping Page {current_page_human} (Results {start_index+1}-{start_index+RESULTS_PER_PAGE}) for query: '{self.search_query_raw}'")
        logger.debug(f"🌐 URL: {url}")

        response = self.make_request(url)
        if not response:
            logger.error(f"🚨 Failed to retrieve page {current_page_human}. Skipping.")
            return None # Indicate request failure

        soup = BeautifulSoup(response.text, 'html.parser')
        results_on_page = []
        raw_results = soup.select('.gs_r.gs_or.gs_scl')

        if not raw_results:
             if "did not match any articles" in response.text or "reached the end of the results" in response.text:
                 logger.info(f"✔️ No results found on page {current_page_human}. Likely end of results.")
                 return [] # Indicate end of results
             else:
                 logger.warning(f"⚠️ Found no result containers on page {current_page_human}, but no 'end of results' message.")
                 return [] # Treat as empty

        for item in raw_results:
            try:
                title_tag = item.select_one('.gs_rt a')
                title = title_tag.get_text(strip=True) if title_tag else None
                url = title_tag['href'] if title_tag else None

                if not title or not url:
                    logger.warning("⚠️ Skipping item due to missing title or URL.")
                    continue

                source_tag = item.select_one('.gs_a')
                source_text = source_tag.get_text(strip=True) if source_tag else ""
                source_info = self.parse_source(source_text)

                abstract_tag = item.select_one('.gs_rs')
                abstract = abstract_tag.get_text(strip=True).replace('\n', ' ') if abstract_tag else None

                cite_link = item.select_one('a[href*="cites="]')
                citations = None
                if cite_link and 'Cited by' in cite_link.text:
                    cite_match = re.search(r'\d+', cite_link.text)
                    if cite_match: citations = int(cite_match.group())

                pdf_link_tag = item.select_one('.gs_or_ggsm a')
                pdf_link = pdf_link_tag['href'] if pdf_link_tag else None

                results_on_page.append({
                    'query': self.search_query_raw,
                    'title': title,
                    'url': url,
                    'authors': source_info['authors'],
                    'journal': source_info['journal'],
                    'year': source_info['year'],
                    'abstract': abstract,
                    'citations': citations,
                    'pdf_link': pdf_link,
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'page_number': current_page_human
                })
            except Exception as e:
                logger.error(f"⚠️ Error processing item on page {current_page_human}: {e}", exc_info=False)
                continue

        logger.info(f"📄 Found {len(results_on_page)} items on page {current_page_human}.")
        return results_on_page

    def save_results(self, new_data, existing_data):
        """Append new, unique results to existing data and save to the specific query file."""
        if not new_data:
            logger.info("No new results from the last page to save.")
            return existing_data # Return unchanged data

        # Use the full path stored in self.output_file
        output_filepath = self.output_file

        existing_urls = {item.get('url') for item in existing_data if item.get('url')}
        actually_new_items = []
        for item in new_data:
            if item.get('url') not in existing_urls:
                actually_new_items.append(item)
                existing_urls.add(item.get('url'))

        if actually_new_items:
            combined_data = existing_data + actually_new_items
            try:
                # Directory should already exist, created in the main loop
                # os.makedirs(os.path.dirname(output_filepath), exist_ok=True) # Keep for safety maybe? Redundant now.
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(combined_data, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 Saved {len(actually_new_items)} new items ({len(combined_data)} total) to: {output_filepath}")
                return combined_data # Return the updated data
            except IOError as e:
                 logger.error(f"🚨 Error saving data to {output_filepath}: {e}")
                 return existing_data # Return original data if save failed
            except Exception as e:
                 logger.error(f"🚨 Unexpected error during saving to {output_filepath}: {e}")
                 return existing_data
        else:
            logger.info("🔄 No unique new items found on the last page to save.")
            return existing_data # Return unchanged data


    def load_existing_results(self):
        """Load existing results for the current query's specific output file."""
         # Use the full path stored in self.output_file
        output_filepath = self.output_file
        if os.path.exists(output_filepath):
            try:
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.info(f"📂 Loaded {len(existing_data)} existing records from {output_filepath}")
                return existing_data
            except json.JSONDecodeError:
                logger.error(f"🚨 Error decoding JSON from {output_filepath}. Starting fresh for this query.")
                return []
            except Exception as e:
                logger.error(f"⚠️ Error loading existing data from {output_filepath}: {e}. Starting fresh.")
                return []
        else:
            logger.info(f"No existing file found at {output_filepath}. Starting fresh.")
            return []


    def run(self):
        """Main execution flow for the current query."""
        logger.info(f"\n{'='*20} Starting Query: '{self.search_query_raw}' {'='*20}")
        logger.info(f"🎯 Target: Up to {MAX_PAGES_PER_QUERY} pages.")
        # Use the full path stored in self.output_file for logging
        logger.info(f"💾 Output File: {self.output_file}")

        all_results_for_query = self.load_existing_results()
        total_new_results_count = 0

        for page_num in range(MAX_PAGES_PER_QUERY):
            page_results = self.scrape_page(page_num)

            if page_results is None:
                logger.error(f"🚨 Critical error scraping page {page_num + 1}, stopping scrape for query '{self.search_query_raw}'.")
                break

            elif not page_results:
                logger.info(f"🏁 No more results found on page {page_num + 1}. Stopping scrape for query '{self.search_query_raw}'.")
                break

            else:
                new_items_before_save = len(all_results_for_query)
                all_results_for_query = self.save_results(page_results, all_results_for_query)
                total_new_results_count += (len(all_results_for_query) - new_items_before_save)

            if page_num < MAX_PAGES_PER_QUERY - 1:
                 logger.info(f"⏳ Delaying before next page...")
                 self.human_delay()

        logger.info(f"\n{'='*20} Finished Query: '{self.search_query_raw}' {'='*20}")
        logger.info(f"✨ Collected {total_new_results_count} new results during this run.")
        logger.info(f"💾 Final data for this query ({len(all_results_for_query)} total items) is in: {self.output_file}")

        # Optional: Disconnect VPN if it was connected during this query's run
        # self.disconnect_vpn()

        return len(all_results_for_query)


def print_instructions():
    """Enhanced setup instructions including new output structure."""
    print("\n" + "="*60)
    print("      GOOGLE SCHOLAR SCRAPER - AUTOMATED VERSION")
    print("="*60)
    print("SETUP:")
    print(f"1. Create a file named '{INPUT_QUERIES_FILE}' in the same directory as the script.")
    print("   - Add your Google Scholar search queries to this file, one query per line.")
    print("2. Configure the base output directory:")
    print(f"  - Default: '{BASE_OUTPUT_DIR}' (relative to script execution location)")
    print("   - The script will create a sub-folder inside this directory for each query.")
    print("   - Example: Results for query 'abc xyz' will be in:")
    print(f"     '{os.path.join(BASE_OUTPUT_DIR, 'abc_xyz', 'abc_xyz.json')}'")
    print("3. Ensure the BASE output directory exists or can be created by the script.")
    print("4. Configure Tor (if USE_TOR = True):")
    print("   - Install Tor Browser or Tor service.")
    print("   - Ensure Tor control port is enabled (e.g., add 'ControlPort 9051' to torrc).")
    print("   - Set a password for the control port ('tor --hash-password your_password')")
    print(f"  - Update 'TOR_PASSWORD' in the script with your actual password.")
    print("5. Configure VPN Fallback (Optional, if USE_VPN_FALLBACK = True):")
    print("   - Requires a VPN with CLI support (example uses Windscribe).")
    print("   - Ensure the VPN CLI command works in your terminal.")
    print("   - Adjust `connect_vpn` and `disconnect_vpn` methods if needed.")
    print("6. Install Python Dependencies:")
    print("   pip install requests beautifulsoup4 stem fake-useragent")
    print("="*60 + "\n")

if __name__ == "__main__":
    print_instructions()

    # --- Read Queries from File ---
    try:
        with open(INPUT_QUERIES_FILE, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        if not queries:
            logger.error(f"❌ Input file '{INPUT_QUERIES_FILE}' is empty or contains no valid queries.")
            exit(1) # Use non-zero exit code for errors
        logger.info(f"🔍 Found {len(queries)} queries in '{INPUT_QUERIES_FILE}'.")
    except FileNotFoundError:
        logger.error(f"❌ Input file '{INPUT_QUERIES_FILE}' not found. Please create it.")
        exit(1)
    except Exception as e:
         logger.error(f"❌ Error reading input file '{INPUT_QUERIES_FILE}': {e}")
         exit(1)

    # --- Ensure Base Output Directory Exists ---
    # Note: Individual query folders are created within the loop below
    try:
        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        logger.info(f"📂 Base output directory set to: {BASE_OUTPUT_DIR}")
    except OSError as e:
        logger.error(f"🚨 Could not create base output directory '{BASE_OUTPUT_DIR}': {e}. Please check permissions or create it manually.")
        exit(1)


    # --- Process Each Query ---
    total_results_all_queries = 0
    start_time = time.time()

    for i, query in enumerate(queries):
        logger.info(f"\n{'#'*30} Processing Query {i+1}/{len(queries)} {'#'*30}")

        # --- Create Query-Specific Folder and File Path ---
        sanitized_name = sanitize_filename(query)
        query_specific_folder = os.path.join(BASE_OUTPUT_DIR, sanitized_name)
        output_filepath = os.path.join(query_specific_folder, sanitized_name + ".json")

        try:
            # Create the specific folder for this query's results
            os.makedirs(query_specific_folder, exist_ok=True)
            logger.info(f"📂 Results for this query will be saved in: {query_specific_folder}")

            # Instantiate scraper with the full path to the final JSON file
            scraper = ScholarlyScraper(search_query=query, output_file=output_filepath)
            num_results = scraper.run()
            # This counts total items in file after run, including previously existing ones
            # total_results_all_queries += num_results
        except OSError as e:
             logger.error(f"🚨 Could not create query-specific directory '{query_specific_folder}': {e}")
             logger.error("Skipping this query...")
             continue # Skip to the next query
        except Exception as e:
            logger.error(f"🚨 Unhandled exception during scraping for query '{query}': {e}", exc_info=True)
            logger.error("Moving to the next query if available...")
        finally:
             # Optional cleanup like VPN disconnect could go here if needed between queries
             # scraper.disconnect_vpn()
             # Add a delay between processing different queries
             if i < len(queries) - 1:
                 inter_query_delay = random.uniform(5, 15)
                 logger.info(f"\n--- Delaying {inter_query_delay:.1f}s before next query ---")
                 time.sleep(inter_query_delay)


    # --- End Summary ---
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 All queries processed!")
    logger.info(f"⏱️ Total execution time: {duration:.2f} seconds ({duration/60:.2f} minutes).")
    logger.info(f"📂 Results saved in subfolders within: {BASE_OUTPUT_DIR}")
    logger.info("="*60) >>>
# ==============================================
```

Based on how I currently use it, this script likely takes a single search query (e.g., a string representing a historical event name), performs a search on Google Scholar for that specific query, scrapes a certain number of result pages (which might not be fixed at 30), extracts some basic information from each search result (like title and URL), and saves this output to a file or folder, possibly named after the input query. It might already include some form of delay or waiting mechanism between requests.

**My Goal: Modify the Script for Step 1 Requirements**
I need you to significantly modify and enhance the provided script to meet the requirements for the first core step of my data collection plan. The script should now be designed to process a list of historical events, perform searches for each event in multiple languages, scrape a fixed number of result  *pages* , extract specific data points from  *each result* , and finally structure and save the collected data into a specific, detailed JSON format per event.

**Detailed Requirements for Modification:**

1. **Input List of Events:** The script should be designed to process a predefined list containing the historical events and their translations. Assume this list will be provided directly within the script code (or you can suggest how it should be loaded, e.g., from a file, if that's better). A Python list of dictionaries is a good format, like this example:

   **Python**

   ```
   events_to_scrape = [
       {'main_name': 'Roman Invasion of Mauretania', 'en': 'Roman invasion of Mauretania', 'ar': 'الغزو الروماني لموريتانيا', 'fr': 'Invasion romaine de la Maurétanie', 'es': 'Invasión romana de Mauritania'},
       {'main_name': 'Battle of Zallaqa', 'en': 'Battle of Zallaqa', 'ar': 'معركة الزلاقة', 'fr': 'Bataille de Zallaqa', 'es': 'Batalla de Sagrajas'},
       # ... add the rest of your historical events here following the same structure
   ]
   ```

   The script should iterate through each dictionary in this `events_to_scrape` list.
2. **Multilingual Searching per Event:** For *each* historical event dictionary in the list:

   * Perform **four separate search queries** on Google Scholar.
   * Use the English name (`'en'`) from the dictionary for one search.
   * Use the Arabic name (`'ar'`) for a second search.
   * Use the French name (`'fr'`) for a third search.
   * Use the Spanish name (`'es'`) for a fourth search.
   * Ensure that each search request is appropriately configured for the target language if the Google Scholar URL or parameters require it (e.g., using language codes in the URL if your current script doesn't handle this).
3. **Fixed Scraping Depth:** For *each of these four searches per event* (i.e., for each language of each event), the script must scrape the **first 30 pages of search results** returned by Google Scholar. It's important to scrape exactly 30 result pages if possible, rather than a different fixed number of results.
4. **Detailed Data Extraction per Result:** From *each individual search result entry* found on those 30 pages (for each of the four searches per event), extract the following specific metadata points:

   * **`title`** : The main title of the search result.
   * **`url`** : The URL (link) associated with the result.
   * **`snippet`** : The short descriptive text under the title in the search result.
   * **`source`** : Information about the publication or website (if available).
   * "authors": "إبراهيم سلام, صلاح خلیل - حوليات أداب عين شمس, 2016‎",
   * "journal": "journals.ekb.eg",
5. **Structured JSON Output per Event:** After successfully performing the searches and scraping the 30 pages for *all four languages* for a *single* event, collect all the extracted results for that event and structure them into a **single Python dictionary** that matches the following specific JSON structure:

   **JSON**

   ```
   {
     "event": "[Value of 'main_name' from the event dictionary]",
     "results": {
       "en": [ {'title': '...', 'url': '...', 'snippet': '...', 'source': '...'}, // List of dictionaries for all extracted English results
               {'title': '...', 'url': '...', 'snippet': '...', 'source': '...'}, ... ],
       "ar": [ {'title': '...', 'url': '...', 'snippet': '...', 'source': '...'}, // List of dictionaries for all extracted Arabic results
               ... ],
       "fr": [ {'title': '...', 'url': '...', 'snippet': '...', 'source': '...'}, // List of dictionaries for all extracted French results
               ... ],
       "es": [ {'title': '...', 'url': '...', 'snippet': '...', 'source': '...'}, // List of dictionaries for all extracted Spanish results
               ... ]
     }
   }
   ```

   Ensure the keys within the result dictionaries (`title`, `url`, `snippet`, `source`) match the data points you are extracting.
6. **File Saving:** Save the structured dictionary created for each event as a  **JSON file** . The filename should be based on the `main_name` of the event (e.g., `Roman_Invasion_of_Mauretania.json`). Ensure the filename is file-system safe (e.g., replace spaces with underscores, remove special characters). Save each event's JSON file in a designated output directory (you can create a 'data_raw' directory, for example).
7. **Rate Limiting/Anti-Blocking:** Ensure that the script incorporates appropriate delays between requests, especially between searches for different languages or events. Using random delays within a reasonable range (e.g., 5 to 15 seconds) is advisable. If your existing script has waits, integrate them correctly into the new loop structure. Mention in the code comments or explanation that external tools like a VPN are also necessary to handle potential IP blocking, as this isn't something the script fully controls.

**Your Task for the AI:**

Modify my provided Python script code (`<<< import requests
from bs4 import BeautifulSoup
import time
import random
import json
import os
import re
from urllib.parse import quote_plus, unquote
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
import subprocess
import logging

# --- Configuration ---

INPUT_QUERIES_FILE = "queries.txt"  # File containing search queries, one per line

# NEW: Base directory where individual query folders will be created

BASE_OUTPUT_DIR = "../Data/Scraped_Results_By_Query"
MAX_PAGES_PER_QUERY = 30           # Max pages to scrape per query
RESULTS_PER_PAGE = 10              # Google Scholar results per page (usually fixed at 10)
DELAY_RANGE = (15, 40)             # Base delay range (seconds) between page requests
INITIAL_BACKOFF_DELAY = 30         # Initial delay (seconds) on blocking/CAPTCHA
MAX_BACKOFF_DELAY = 240            # Maximum backoff delay (seconds)
REQUEST_TIMEOUT = 40               # Timeout for individual HTTP requests
TOR_PASSWORD = "iliass2001"        # Your Tor control port password
USE_TOR = True                     # Set to False to disable Tor/VPN rotation
USE_VPN_FALLBACK = True            # Set to False to disable VPN fallback attempt

# --- Logging Setup ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Remove or replace characters illegal in filenames/folder names."""
    # Remove characters that are definitely problematic in most OS
    sanitized = re.sub(r'[\\/*?:"<>|]', '', filename)
    # Replace long whitespace sequences with a single underscore
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove leading/trailing underscores/spaces
    sanitized = sanitized.strip('_ ')
    # Optional: Truncate long names
    max_len = 100
    if len(sanitized) > max_len:
        original_len = len(sanitized)
        # Try to cut at last underscore within limit
        truncated = sanitized[:max_len]
        last_underscore_pos = truncated.rfind('_')
        if last_underscore_pos > max_len / 2 : # Only cut if underscore isn't too early
             sanitized = truncated[:last_underscore_pos]
        else:
             sanitized = truncated # Fallback to simple truncate if no good underscore found
        logger.debug(f"Sanitized name truncated from {original_len} to {len(sanitized)} chars.")

    # Ensure filename is not empty after sanitization
    return sanitized if sanitized else "default_query_name"

class ScholarlyScraper:
    # ... (Keep the __init__, setup_tor, rotate_tor_ip, connect_vpn, disconnect_vpn methods exactly as before) ...
    def __init__(self, search_query, output_file):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.current_proxy = None
        self.controller = None
        self.search_query_raw = search_query # Keep raw query for logging/filenames
        self.search_query_encoded = quote_plus(search_query)
        # output_file now includes the query-specific folder path
        self.output_file = output_file
        self.backoff_delay = INITIAL_BACKOFF_DELAY
        self.tor_enabled = USE_TOR
        self.vpn_fallback_enabled = USE_VPN_FALLBACK

    if self.tor_enabled:
            self.setup_tor()
            if self.controller:
                self.rotate_tor_ip() # Start with a fresh Tor IP

    def setup_tor(self):
        """Initialize Tor connection."""
        if not self.tor_enabled:
            logger.info("Tor usage is disabled in configuration.")
            return
        try:
            self.controller = Controller.from_port(port=9051)
            self.controller.authenticate(password=TOR_PASSWORD)
            logger.info("✅ Tor controller initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Tor controller connection failed: {e}. Check if Tor is running and configured.")
            logger.warning("🔓 Proceeding without Tor/VPN rotation (higher detection risk).")
            self.controller = None
            self.tor_enabled = False # Disable further Tor attempts if setup fails

    def rotate_tor_ip(self):
        """Rotate Tor exit node."""
        if not self.controller:
            logger.debug("Tor controller not available for IP rotation.")
            return False
        try:
            self.controller.signal(Signal.NEWNYM)
            # Wait for Tor circuit to establish
            time.sleep(self.controller.get_newnym_wait())
            self.current_proxy = {
                'http': 'socks5h://localhost:9050', # Use socks5h for DNS resolution via Tor
                'https': 'socks5h://localhost:9050'
            }
            logger.info("🔄 Tor IP rotated successfully.")
            # Reset backoff delay after successful rotation, assuming it fixed the issue
            self.backoff_delay = INITIAL_BACKOFF_DELAY
            return True
        except Exception as e:
            logger.error(f"⚠️ Tor IP rotation failed: {e}")
            return False

    def connect_vpn(self):
        """Connect to VPN as a fallback (example using Windscribe CLI)."""
        if not self.vpn_fallback_enabled:
             logger.info("VPN fallback disabled.")
             return False
        try:
            logger.info("Attempting VPN connection via Windscribe (France)...")
            # Make sure the command works in your terminal first
            # You might need to adjust the command or location
            subprocess.run(["windscribe", "connect", "france"], check=True, timeout=60)
            self.current_proxy = None # VPN affects system globally, no proxy needed in requests
            logger.info("🔒 VPN connected successfully.")
            # Reset backoff delay after successful connection
            self.backoff_delay = INITIAL_BACKOFF_DELAY
            return True
        except FileNotFoundError:
             logger.error("⚠️ VPN connection failed: 'windscribe' command not found. Is Windscribe CLI installed and in PATH?")
             return False
        except subprocess.CalledProcessError as e:
            logger.error(f"⚠️ VPN connection failed: Windscribe command error: {e}")
            return False
        except subprocess.TimeoutExpired:
             logger.error("⚠️ VPN connection failed: Command timed out.")
             return False
        except Exception as e:
            logger.error(f"⚠️ VPN connection failed with unexpected error: {e}")
            return False

    def disconnect_vpn(self):
        """Disconnect VPN (if needed)."""
        if not self.vpn_fallback_enabled:
            return
        try:
            logger.info("Attempting VPN disconnection...")
            subprocess.run(["windscribe", "disconnect"], check=True, timeout=30)
            logger.info("🔌 VPN disconnected.")
        except Exception as e:
            logger.warning(f"⚠️ VPN disconnection failed: {e}")

    def get_headers(self):
        """Generate random headers."""
        return {
            'User-Agent': self.ua.random,
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7', # Broader language acceptance
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/', # More generic referer
            'DNT': '1', # Do Not Track
            'Upgrade-Insecure-Requests': '1'
        }

    def human_delay(self, base_range=DELAY_RANGE):
        """Randomized delay between actions."""
        delay = random.uniform(base_range[0], base_range[1])
        logger.debug(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    def make_request(self, url):
        """Make request with retries, Tor/VPN rotation, and exponential backoff."""
        attempts = 0
        max_attempts = 5 # Total attempts for a single URL

    while attempts < max_attempts:
            attempts += 1
            proxies = self.current_proxy
            headers = self.get_headers()
            logger.info(f"🔗 Attempt {attempts}/{max_attempts}: Requesting URL: {url}")
            logger.debug(f"Using Headers: {headers}")
            logger.debug(f"Using Proxies: {proxies}")

    try:
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=REQUEST_TIMEOUT
                )

    # Check for CAPTCHA or blocking patterns
                if "CAPTCHA" in response.text or "recaptcha" in response.text or response.status_code == 429:
                    raise requests.exceptions.RequestException("⛔ CAPTCHA or block detected")

    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                logger.info(f"✅ Request successful (Status: {response.status_code})")
                return response

    except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Request attempt {attempts} timed out.")
                if not self.try_rotation_strategies():
                     logger.error("🚨 Rotation strategies failed after timeout. Giving up on this URL.")
                     return None

    except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ Request attempt {attempts} failed: {e}")
                if "CAPTCHA" in str(e) or "block" in str(e) or "429" in str(e):
                    logger.warning(f"🚨 Block detected! Initiating backoff: {self.backoff_delay}s")
                    time.sleep(self.backoff_delay)
                    self.backoff_delay = min(self.backoff_delay * 2, MAX_BACKOFF_DELAY)
                    if not self.try_rotation_strategies():
                         logger.error("🚨 Rotation strategies failed after block. Giving up on this URL.")
                         return None
                else:
                    time.sleep(5)

    time.sleep(random.uniform(1, 3))

    logger.error(f"🚨 Request failed after {max_attempts} attempts for URL: {url}")
        return None

    def try_rotation_strategies(self):
        """Attempt Tor rotation, then VPN connection as fallback."""
        if self.tor_enabled and self.rotate_tor_ip():
            return True
        elif self.vpn_fallback_enabled and self.connect_vpn():
            return True
        else:
             logger.warning("⚠️ Both Tor rotation and VPN fallback failed or are disabled.")
             return False

    def parse_source(self, source_text):
        """Parse author/journal/year from source line more robustly."""
        authors = None
        journal = None
        year = None
        try:
            parts = source_text.split(' - ')
            authors = parts[0].strip()
            if len(parts) > 1:
                year_match = re.search(r'\b(\d{4})\b', parts[1])
                if year_match:
                    year = year_match.group(1)
                    journal = parts[1].split(year)[0].strip(', ')
                else:
                    journal = parts[1].strip()
                if year is None and len(parts) > 2:
                     year_match_p3 = re.search(r'\b(\d{4})\b', parts[2])
                     if year_match_p3:
                         year = year_match_p3.group(1)
                         if not journal: journal = parts[1].strip() # Journal might still be in part 2
            authors = authors if authors else None
            journal = journal if journal else None
            year = int(year) if year else None
        except Exception as e:
            logger.warning(f"⚠️ Could not parse source string: '{source_text}'. Error: {e}")
        return {'authors': authors, 'journal': journal, 'year': year}

    def scrape_page(self, page_num):
        """Scrape a single page."""
        start_index = page_num * RESULTS_PER_PAGE
        url = f"https://scholar.google.com/scholar?start={start_index}&hl=en&as_sdt=0%2C5&q={self.search_query_encoded}"
        current_page_human = page_num + 1
        logger.info(f"\n📖 Scraping Page {current_page_human} (Results {start_index+1}-{start_index+RESULTS_PER_PAGE}) for query: '{self.search_query_raw}'")
        logger.debug(f"🌐 URL: {url}")

    response = self.make_request(url)
        if not response:
            logger.error(f"🚨 Failed to retrieve page {current_page_human}. Skipping.")
            return None # Indicate request failure

    soup = BeautifulSoup(response.text, 'html.parser')
        results_on_page = []
        raw_results = soup.select('.gs_r.gs_or.gs_scl')

    if not raw_results:
             if "did not match any articles" in response.text or "reached the end of the results" in response.text:
                 logger.info(f"✔️ No results found on page {current_page_human}. Likely end of results.")
                 return [] # Indicate end of results
             else:
                 logger.warning(f"⚠️ Found no result containers on page {current_page_human}, but no 'end of results' message.")
                 return [] # Treat as empty

    for item in raw_results:
            try:
                title_tag = item.select_one('.gs_rt a')
                title = title_tag.get_text(strip=True) if title_tag else None
                url = title_tag['href'] if title_tag else None

    if not title or not url:
                    logger.warning("⚠️ Skipping item due to missing title or URL.")
                    continue

    source_tag = item.select_one('.gs_a')
                source_text = source_tag.get_text(strip=True) if source_tag else ""
                source_info = self.parse_source(source_text)

    abstract_tag = item.select_one('.gs_rs')
                abstract = abstract_tag.get_text(strip=True).replace('\n', ' ') if abstract_tag else None

    cite_link = item.select_one('a[href*="cites="]')
                citations = None
                if cite_link and 'Cited by' in cite_link.text:
                    cite_match = re.search(r'\d+', cite_link.text)
                    if cite_match: citations = int(cite_match.group())

    pdf_link_tag = item.select_one('.gs_or_ggsm a')
                pdf_link = pdf_link_tag['href'] if pdf_link_tag else None

    results_on_page.append({
                    'query': self.search_query_raw,
                    'title': title,
                    'url': url,
                    'authors': source_info['authors'],
                    'journal': source_info['journal'],
                    'year': source_info['year'],
                    'abstract': abstract,
                    'citations': citations,
                    'pdf_link': pdf_link,
                    'scraped_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'page_number': current_page_human
                })
            except Exception as e:
                logger.error(f"⚠️ Error processing item on page {current_page_human}: {e}", exc_info=False)
                continue

    logger.info(f"📄 Found {len(results_on_page)} items on page {current_page_human}.")
        return results_on_page

    def save_results(self, new_data, existing_data):
        """Append new, unique results to existing data and save to the specific query file."""
        if not new_data:
            logger.info("No new results from the last page to save.")
            return existing_data # Return unchanged data

    # Use the full path stored in self.output_file
        output_filepath = self.output_file

    existing_urls = {item.get('url') for item in existing_data if item.get('url')}
        actually_new_items = []
        for item in new_data:
            if item.get('url') not in existing_urls:
                actually_new_items.append(item)
                existing_urls.add(item.get('url'))

    if actually_new_items:
            combined_data = existing_data + actually_new_items
            try:
                # Directory should already exist, created in the main loop
                # os.makedirs(os.path.dirname(output_filepath), exist_ok=True) # Keep for safety maybe? Redundant now.
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(combined_data, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 Saved {len(actually_new_items)} new items ({len(combined_data)} total) to: {output_filepath}")
                return combined_data # Return the updated data
            except IOError as e:
                 logger.error(f"🚨 Error saving data to {output_filepath}: {e}")
                 return existing_data # Return original data if save failed
            except Exception as e:
                 logger.error(f"🚨 Unexpected error during saving to {output_filepath}: {e}")
                 return existing_data
        else:
            logger.info("🔄 No unique new items found on the last page to save.")
            return existing_data # Return unchanged data

    def load_existing_results(self):
        """Load existing results for the current query's specific output file."""
         # Use the full path stored in self.output_file
        output_filepath = self.output_file
        if os.path.exists(output_filepath):
            try:
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.info(f"📂 Loaded {len(existing_data)} existing records from {output_filepath}")
                return existing_data
            except json.JSONDecodeError:
                logger.error(f"🚨 Error decoding JSON from {output_filepath}. Starting fresh for this query.")
                return []
            except Exception as e:
                logger.error(f"⚠️ Error loading existing data from {output_filepath}: {e}. Starting fresh.")
                return []
        else:
            logger.info(f"No existing file found at {output_filepath}. Starting fresh.")
            return []

    def run(self):
        """Main execution flow for the current query."""
        logger.info(f"\n{'='*20} Starting Query: '{self.search_query_raw}' {'='*20}")
        logger.info(f"🎯 Target: Up to {MAX_PAGES_PER_QUERY} pages.")
        # Use the full path stored in self.output_file for logging
        logger.info(f"💾 Output File: {self.output_file}")

    all_results_for_query = self.load_existing_results()
        total_new_results_count = 0

    for page_num in range(MAX_PAGES_PER_QUERY):
            page_results = self.scrape_page(page_num)

    if page_results is None:
                logger.error(f"🚨 Critical error scraping page {page_num + 1}, stopping scrape for query '{self.search_query_raw}'.")
                break

    elif not page_results:
                logger.info(f"🏁 No more results found on page {page_num + 1}. Stopping scrape for query '{self.search_query_raw}'.")
                break

    else:
                new_items_before_save = len(all_results_for_query)
                all_results_for_query = self.save_results(page_results, all_results_for_query)
                total_new_results_count += (len(all_results_for_query) - new_items_before_save)

    if page_num < MAX_PAGES_PER_QUERY - 1:
                 logger.info(f"⏳ Delaying before next page...")
                 self.human_delay()

    logger.info(f"\n{'='*20} Finished Query: '{self.search_query_raw}' {'='*20}")
        logger.info(f"✨ Collected {total_new_results_count} new results during this run.")
        logger.info(f"💾 Final data for this query ({len(all_results_for_query)} total items) is in: {self.output_file}")

    # Optional: Disconnect VPN if it was connected during this query's run
        # self.disconnect_vpn()

    return len(all_results_for_query)

def print_instructions():
    """Enhanced setup instructions including new output structure."""
    print("\n" + "="*60)
    print("      GOOGLE SCHOLAR SCRAPER - AUTOMATED VERSION")
    print("="*60)
    print("SETUP:")
    print(f"1. Create a file named '{INPUT_QUERIES_FILE}' in the same directory as the script.")
    print("   - Add your Google Scholar search queries to this file, one query per line.")
    print("2. Configure the base output directory:")
    print(f"  - Default: '{BASE_OUTPUT_DIR}' (relative to script execution location)")
    print("   - The script will create a sub-folder inside this directory for each query.")
    print("   - Example: Results for query 'abc xyz' will be in:")
    print(f"     '{os.path.join(BASE_OUTPUT_DIR, 'abc_xyz', 'abc_xyz.json')}'")
    print("3. Ensure the BASE output directory exists or can be created by the script.")
    print("4. Configure Tor (if USE_TOR = True):")
    print("   - Install Tor Browser or Tor service.")
    print("   - Ensure Tor control port is enabled (e.g., add 'ControlPort 9051' to torrc).")
    print("   - Set a password for the control port ('tor --hash-password your_password')")
    print(f"  - Update 'TOR_PASSWORD' in the script with your actual password.")
    print("5. Configure VPN Fallback (Optional, if USE_VPN_FALLBACK = True):")
    print("   - Requires a VPN with CLI support (example uses Windscribe).")
    print("   - Ensure the VPN CLI command works in your terminal.")
    print("   - Adjust `connect_vpn` and `disconnect_vpn` methods if needed.")
    print("6. Install Python Dependencies:")
    print("   pip install requests beautifulsoup4 stem fake-useragent")
    print("="*60 + "\n")

if __name__ == "__main__":
    print_instructions()

    # --- Read Queries from File ---
    try:
        with open(INPUT_QUERIES_FILE, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        if not queries:
            logger.error(f"❌ Input file '{INPUT_QUERIES_FILE}' is empty or contains no valid queries.")
            exit(1) # Use non-zero exit code for errors
        logger.info(f"🔍 Found {len(queries)} queries in '{INPUT_QUERIES_FILE}'.")
    except FileNotFoundError:
        logger.error(f"❌ Input file '{INPUT_QUERIES_FILE}' not found. Please create it.")
        exit(1)
    except Exception as e:
         logger.error(f"❌ Error reading input file '{INPUT_QUERIES_FILE}': {e}")
         exit(1)

    # --- Ensure Base Output Directory Exists ---
    # Note: Individual query folders are created within the loop below
    try:
        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        logger.info(f"📂 Base output directory set to: {BASE_OUTPUT_DIR}")
    except OSError as e:
        logger.error(f"🚨 Could not create base output directory '{BASE_OUTPUT_DIR}': {e}. Please check permissions or create it manually.")
        exit(1)

    # --- Process Each Query ---
    total_results_all_queries = 0
    start_time = time.time()

    for i, query in enumerate(queries):
        logger.info(f"\n{'#'*30} Processing Query {i+1}/{len(queries)} {'#'*30}")

    # --- Create Query-Specific Folder and File Path ---
        sanitized_name = sanitize_filename(query)
        query_specific_folder = os.path.join(BASE_OUTPUT_DIR, sanitized_name)
        output_filepath = os.path.join(query_specific_folder, sanitized_name + ".json")

    try:
            # Create the specific folder for this query's results
            os.makedirs(query_specific_folder, exist_ok=True)
            logger.info(f"📂 Results for this query will be saved in: {query_specific_folder}")

    # Instantiate scraper with the full path to the final JSON file
            scraper = ScholarlyScraper(search_query=query, output_file=output_filepath)
            num_results = scraper.run()
            # This counts total items in file after run, including previously existing ones
            # total_results_all_queries += num_results
        except OSError as e:
             logger.error(f"🚨 Could not create query-specific directory '{query_specific_folder}': {e}")
             logger.error("Skipping this query...")
             continue # Skip to the next query
        except Exception as e:
            logger.error(f"🚨 Unhandled exception during scraping for query '{query}': {e}", exc_info=True)
            logger.error("Moving to the next query if available...")
        finally:
             # Optional cleanup like VPN disconnect could go here if needed between queries
             # scraper.disconnect_vpn()
             # Add a delay between processing different queries
             if i < len(queries) - 1:
                 inter_query_delay = random.uniform(5, 15)
                 logger.info(f"\n--- Delaying {inter_query_delay:.1f}s before next query ---")
                 time.sleep(inter_query_delay)

    # --- End Summary ---
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 All queries processed!")
    logger.info(f"⏱️ Total execution time: {duration:.2f} seconds ({duration/60:.2f} minutes).")
    logger.info(f"📂 Results saved in subfolders within: {BASE_OUTPUT_DIR}")
    logger.info("="*60) >>>`) to implement all the requirements detailed above under "New Functionality Details".

**Expected Output from AI:**

1. The complete, modified Python script code.
2. A clear explanation of the significant changes you made compared to the original script.
3. Instructions on how to use the modified script, including how to define and structure the `events_to_scrape` list, and where the output files will be saved.
4. Any necessary import statements (e.g., `json`, `time`, `random`, relevant scraping libraries like `requests`, `BeautifulSoup`).
