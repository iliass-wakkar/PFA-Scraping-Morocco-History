import json
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# ==============================================
# <<< CONFIGURATION >>>
# ==============================================
DEFAULT_SCRAPED_DIR = Path("../Data/data_raw_auto_retry_hierarchical")

# --- Logging Setup ---
log_file_path = Path(__file__).parent / 'date_adder.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_status(message: str, status: str = 'info'):
    """Prints status messages with timestamp and color, and logs."""
    colors = { 'success': '\033[92m', 'error': '\033[91m', 'warning': '\033[93m', 'info': '\033[94m', 'debug': '\033[90m', 'reset': '\033[0m' }
    timestamp = datetime.now().strftime('[%H:%M:%S]')
    print(f"{timestamp} {colors.get(status, colors['info'])}{str(message)}{colors['reset']}")
    if status == 'error': logging.error(message)
    elif status == 'warning': logging.warning(message)
    elif status == 'info' and logger.isEnabledFor(logging.INFO): logging.info(message)
    elif status == 'debug' and logger.isEnabledFor(logging.DEBUG): logging.debug(message)

# ==============================================
# <<< HELPER FUNCTIONS >>>
# ==============================================

def build_event_date_map(historical_data):
    """
    Traverses the historical data structure and creates a flat map
    from event Arabic name (stripped) to its combined date object
    """
    event_map = {}
    duplicates_found = []

    def traverse(node):
        if isinstance(node, dict):
            # Handle events array (both main periods and sub-periods)
            if "events" in node and isinstance(node["events"], list):
                for event in node["events"]:
                    if isinstance(event, dict) and "name" in event:
                        event_name = event["name"].strip()
                        
                        # Extract date info from 'date' key
                        date_object = {}
                        if "date" in event and isinstance(event["date"], dict):
                            date_entry = event["date"]
                            if "milady" in date_entry and isinstance(date_entry["milady"], dict):
                                date_object["milady"] = date_entry["milady"]
                            if "hijry" in date_entry and isinstance(date_entry["hijry"], dict):
                                date_object["hijry"] = date_entry["hijry"]

                        # Only add if we have date info
                        if event_name and date_object:
                            if event_name in event_map and event_map[event_name] != date_object:
                                if event_name not in duplicates_found:
                                    logger.warning(f"Duplicate event '{event_name}' with different dates")
                                    duplicates_found.append(event_name)
                            event_map[event_name] = date_object

            # Recurse into sub-periods
            if "sub_periods" in node and isinstance(node["sub_periods"], list):
                for sub_node in node["sub_periods"]:
                    traverse(sub_node)
                    
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(historical_data)
    return event_map

# ==============================================
# <<< MAIN LOGIC >>>
# ==============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("     SCRAPED DATA DATE INJECTOR SCRIPT")
    print("="*60)
    print("Adds/updates 'date' object from source data into scraped JSON files.")
    print("="*60 + "\n")

    # --- Get Historical JSON File ---
    historical_data_path = None
    while True:
        input_path_str = input("Enter path to historical events JSON file (with dates): ").strip()
        input_path = Path(input_path_str)
        if input_path.is_file():
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    historical_events_data = json.load(f)
                # Validate it's a list
                if not isinstance(historical_events_data, list): 
                    print_status("❌ Input JSON top level not list.", 'error')
                    continue
                print_status(f"✔️ Loaded historical data from {input_path.name}", 'success')
                historical_data_path = input_path
                break
            except Exception as e: 
                print_status(f"❌ Error loading historical JSON: {e}", 'error')
        else: 
            print_status(f"❌ File not found: {input_path_str}", 'error')
            print("Try again.")

    # --- Build Event Date Map ---
    event_date_mapping = build_event_date_map(historical_events_data)
    if not event_date_mapping:
        print_status("❌ Event date map is empty. Check historical data format ('name' and 'date' keys inside events).", 'error')
        sys.exit(1)
    print_status(f"Built map for {len(event_date_mapping)} unique event names with dates.", 'info')

    # --- Target Scraped Data Directory ---
    target_dir_str = input(f"Enter path to directory with scraped JSON files [default: '{DEFAULT_SCRAPED_DIR}']: ").strip()
    target_dir = Path(target_dir_str) if target_dir_str else DEFAULT_SCRAPED_DIR

    if not target_dir.is_dir(): 
        print_status(f"❌ Target directory not found: {target_dir.resolve()}", 'error')
        sys.exit(1)
    print_status(f"📂 Target directory: {target_dir.resolve()}", 'info')

    # --- Walk Directory and Update Files ---
    files_processed = 0
    files_updated = 0
    files_skipped_no_event = 0
    files_skipped_no_match = 0
    
    print_status(f"\n{'#'*25} Starting File Scan and Update {'#'*25}", 'info')
    logging.info(f"Date Injection Start. Target Dir: {target_dir}")

    try:
        for filepath in target_dir.rglob('*.json'):
            if not filepath.is_file(): 
                continue

            files_processed += 1
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)

                if isinstance(scraped_data, dict) and "event" in scraped_data:
                    event_name_from_json = scraped_data["event"]
                    if not isinstance(event_name_from_json, str):
                        print_status(f"⚠️ 'event' in {filepath.name} not string. Skipping.", 'warning')
                        files_skipped_no_event += 1
                        continue

                    event_name_lookup = event_name_from_json.strip()
                    logger.debug(f"Checking {filepath.name}, Event='{event_name_lookup}'")

                    if event_name_lookup in event_date_mapping:
                        date_object_to_add = event_date_mapping[event_name_lookup]
                        current_date = scraped_data.get("date")
                        
                        if current_date != date_object_to_add:
                            # Create new ordered dictionary to maintain key position
                            updated_data = {}
                            added_date = False
                            
                            for key in scraped_data:
                                updated_data[key] = scraped_data[key]
                                if key == "event":
                                    updated_data["date"] = date_object_to_add
                                    added_date = True
                            
                            # If "event" was last key, add date at end
                            if not added_date:
                                updated_data["date"] = date_object_to_add

                            with open(filepath, 'w', encoding='utf-8') as f_write:
                                json.dump(updated_data, f_write, ensure_ascii=False, indent=2)
                            print_status(f"✔️ Injected/Updated 'date' for '{event_name_lookup}' in {filepath.name}", 'success')
                            files_updated += 1
                        else:
                            print_status(f"➡️ 'date' correct for '{event_name_lookup}' in {filepath.name}.", 'info')
                    else:
                        print_status(f"⚠️ Event name '{event_name_lookup}' (from {filepath.name}) not found in map. Skipping.", 'warning')
                        logger.debug(f"Failed lookup key: '{event_name_lookup}'")
                        files_skipped_no_match += 1
                else:
                    print_status(f"⚠️ File {filepath.name} missing 'event' key or not dict. Skipping.", 'warning')
                    files_skipped_no_event += 1

            except json.JSONDecodeError:
                print_status(f"❌ Error decoding JSON from {filepath.name}. Skipping.", 'error')
            except Exception as e:
                print_status(f"🚨 Error processing file {filepath.name}: {e}", 'error')
                logging.exception(f"Error processing file: {filepath}")

    except Exception as e:
        print_status(f"🚨 Critical error during directory scan: {e}", 'error')
        logging.exception("Critical error scanning directory.")

    # --- End Summary ---
    print_status(f"\n{'='*60}", 'info')
    print_status(f"🏁 Date injection process finished!", 'info')
    print_status(f"Files scanned: {files_processed}", 'info')
    print_status(f"Files updated : {files_updated}", 'success')
    print_status(f"Skipped (no 'event' key/not dict): {files_skipped_no_event}", 'warning')
    print_status(f"Skipped (name not in map): {files_skipped_no_match}", 'warning')
    print_status(f"📜 Log file: {log_file_path.resolve()}", 'info')
    print_status("="*60, 'info')