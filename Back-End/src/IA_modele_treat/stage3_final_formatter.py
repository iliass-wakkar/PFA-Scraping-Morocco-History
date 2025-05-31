#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
import sys

# --- Global Configuration ---
STATE_FILE = "stage3_processing_state.json" # Name of the state file
logger = logging.getLogger(__name__) # Global logger instance

# --- Logging Setup ---
class ColorFormatter(logging.Formatter):
    """Adds color to log messages for console output."""
    COLORS = {
        'WARNING': '\033[93m',  # Yellow
        'INFO': '\033[92m',     # Green
        'DEBUG': '\033[94m',    # Blue
        'CRITICAL': '\033[91m', # Red
        'ERROR': '\033[91m'     # Red
    }
    RESET = '\033[0m'

    def format(self, record):
        log_message = super().format(record)
        if sys.stdout.isatty(): # Only apply colors if output is a TTY
            return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.RESET}"
        return log_message

def setup_logging(debug=False, log_file="process_stage3.log"):
    """Configures logging for the script."""
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs if re-called
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler (logs everything from DEBUG level)
    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')
    fh.setFormatter(file_formatter)
    logger.addHandler(fh)

    # Console Handler (respects debug flag for verbosity)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

# --- Article Parsing Logic ---
def parse_article_text(article_text_raw, article_title_from_stage2, source_references_ordered, event_name):
    """
    Parses the raw article text into sections and paragraphs, linking citations.
    """
    sections_data = []

    # 1. Handle and remove potential markdown title from article_text_raw
    normalized_title_from_stage2 = ' '.join(article_title_from_stage2.strip().lower().split())
    lines = article_text_raw.splitlines()
    content_to_process_lines = []
    if lines:
        first_line_stripped = lines[0].strip()
        if first_line_stripped.startswith('# '): # Check for Markdown H1
            title_in_text = first_line_stripped[2:].strip() # Extract text after '# '
            normalized_title_in_text = ' '.join(title_in_text.strip().lower().split())
            if normalized_title_in_text == normalized_title_from_stage2:
                content_to_process_lines = lines[1:] # Remove title line
                logger.debug(f"Event '{event_name}': Removed matching H1 title from article_text_raw.")
            else:
                logger.warning(f"Event '{event_name}': Article text starts with H1 ('{title_in_text}') that doesn't match Stage 2 article_title ('{article_title_from_stage2}'). Processing text as is, including this H1.")
                content_to_process_lines = lines
        else:
            content_to_process_lines = lines
    content_to_parse = "\n".join(content_to_process_lines).strip()

    # 2. Split text into logical section parts
    structured_section_parts = []
    if not content_to_parse:
        logger.warning(f"Event '{event_name}': Article text is empty after title handling.")
    elif not content_to_parse.startswith("## "): # Text has an introductory part
        parts = content_to_parse.split("\n## ", 1) # Split only on the first "## "
        structured_section_parts.append({"type": "intro", "content": parts[0].strip()})
        if len(parts) > 1: # Sections follow the intro
            for section_block_text in parts[1].split("\n## "):
                structured_section_parts.append({"type": "section", "content": section_block_text.strip()})
    else: # Text starts directly with "## "
        first_section_content_plus_remaining = content_to_parse[3:] # Remove initial "## "
        for section_block_text in first_section_content_plus_remaining.split("\n## "):
            structured_section_parts.append({"type": "section", "content": section_block_text.strip()})
            
    # 3. Process each logical section part
    section_index_counter = 0
    for part_info in structured_section_parts:
        section_paragraphs = []
        subtitle_text = ""
        actual_content_for_paragraphs = ""

        if part_info["type"] == "intro":
            subtitle_text = "Introduction" # Default for introductory content
            actual_content_for_paragraphs = part_info["content"]
        else: # part_info["type"] == "section"
            block_lines = part_info["content"].splitlines()
            if not block_lines: 
                logger.debug(f"Event '{event_name}', Section Index {section_index_counter}: Empty section block encountered.")
                continue 
            subtitle_text = block_lines[0].strip()
            actual_content_for_paragraphs = "\n".join(block_lines[1:]).strip()

        if subtitle_text == "Introduction" and not actual_content_for_paragraphs and len(structured_section_parts) > 1:
            logger.debug(f"Event '{event_name}': Skipping empty 'Introduction' section as other sections exist.")
            continue

        raw_paragraphs = re.split(r'\n\s*\n+', actual_content_for_paragraphs)
        
        paragraph_index_counter = 0
        for para_text_raw in raw_paragraphs:
            para_text_raw_stripped = para_text_raw.strip()
            if not para_text_raw_stripped: 
                continue

            paragraph_id = f"s{section_index_counter}_p{paragraph_index_counter}"
            
            # Regex for citation markers: [1], [1,2], [ 1 , 2 , 3 ]
            citation_pattern = r"\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]"
            paragraph_source_uids = []

            for match in re.finditer(citation_pattern, para_text_raw_stripped):
                marker_content = match.group(1) 
                numbers_str_list = marker_content.split(',')
                for num_str in numbers_str_list:
                    try:
                        ref_num = int(num_str.strip())
                        if ref_num <= 0: 
                            logger.warning(f"Event '{event_name}', Para '{paragraph_id}': Invalid citation number {ref_num} (must be > 0). Skipping.")
                            continue
                        
                        ref_index = ref_num - 1 
                        if 0 <= ref_index < len(source_references_ordered):
                            uid_or_url = source_references_ordered[ref_index]
                            if uid_or_url not in paragraph_source_uids: 
                                paragraph_source_uids.append(uid_or_url)
                        else:
                            logger.warning(f"Event '{event_name}', Para '{paragraph_id}': Citation number {ref_num} (index {ref_index}) is out of bounds for source_references_ordered (length {len(source_references_ordered)}). Skipping.")
                    except ValueError:
                        logger.warning(f"Event '{event_name}', Para '{paragraph_id}': Could not parse number from citation marker part '{num_str}'. Skipping.")
            
            # Clean paragraph text (remove markers)
            cleaned_text = re.sub(citation_pattern, "", para_text_raw_stripped).strip()
            cleaned_text = re.sub(r'\s\s+', ' ', cleaned_text).strip() 

            section_paragraphs.append({
                "paragraph_id": paragraph_id,
                "text": cleaned_text,
                "source_URLs": sorted(list(set(paragraph_source_uids))) 
            })
            paragraph_index_counter += 1
        
        if subtitle_text or section_paragraphs:
            sections_data.append({
                "subtitle": subtitle_text,
                "paragraphs": section_paragraphs
            })
            section_index_counter += 1

    return sections_data

# --- State Management ---
def load_processing_state():
    """Loads the processing state from STATE_FILE."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Ensure basic structure
                if "processed_files" not in state: state["processed_files"] = []
                if "failed_files" not in state: state["failed_files"] = []
                return state
        except json.JSONDecodeError:
            logger.warning(f"Could not decode state file {STATE_FILE}. Starting with a fresh state.")
        except Exception as e:
            logger.warning(f"Error loading state file {STATE_FILE}: {e}. Starting with a fresh state.")
    return {"processed_files": [], "failed_files": []}

def save_processing_state(state):
    """Saves the processing state to STATE_FILE."""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except IOError:
        logger.error(f"Could not write to state file {STATE_FILE}.")
    except Exception as e:
        logger.error(f"Unexpected error saving state file {STATE_FILE}: {e}", exc_info=True)

def get_relative_output_path(input_file_path: str, input_dir: str, output_dir: str) -> str:
    """Get the output path maintaining the input folder structure relative to input_dir"""
    # Get the relative path from input_dir to the input file
    relative_path = os.path.relpath(input_file_path, input_dir)
    # Remove the filename to get just the directory structure
    relative_dir = os.path.dirname(relative_path)
    # Join with output_dir to create the mirror structure
    return os.path.join(output_dir, relative_dir)

# --- Main Processing Function for a Single Event ---
def process_single_event_file(stage2_filepath, output_dir, input_dir):
    """
    Processes a single Stage 2 event file to produce a Stage 3 output file.
    """
    event_filename = os.path.basename(stage2_filepath)
    logger.info(f"Processing Stage 2 file: {event_filename}")
    
    try:
        with open(stage2_filepath, 'r', encoding='utf-8') as f:
            stage2_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Stage 2 file not found: {stage2_filepath}")
        return "failed"
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from Stage 2 file {event_filename}: {stage2_filepath}")
        return "failed"
    except Exception as e:
        logger.error(f"Unexpected error opening/reading Stage 2 file {event_filename}: {e}", exc_info=True)
        return "failed"

    event_name = stage2_data.get("event_name")
    article_title = stage2_data.get("article_title")
    article_text_raw = stage2_data.get("article_text_raw")
    source_references_ordered = stage2_data.get("source_references_ordered")

    if not all([event_name, article_title, article_text_raw is not None, source_references_ordered is not None]):
        logger.error(f"Missing critical data in {event_filename}. Required: event_name, article_title, article_text_raw, source_references_ordered.")
        return "failed"
    
    # Parse article and build structured data
    sections = parse_article_text(
        article_text_raw, article_title, source_references_ordered, event_name
    )

    final_output_data = {
        "event_name": event_name,
        "article_title": article_title,
        "sections": sections
    }

    # Extract language code from filename (e.g., _en.json, _ar.json)
    lang_code = "_en"  # default
    if "_ar.json" in event_filename.lower():
        lang_code = "_ar"
    elif "_es.json" in event_filename.lower():
        lang_code = "_es"
    elif "_fr.json" in event_filename.lower():
        lang_code = "_fr"

    # Save the final JSON output
    sanitized_event_name_for_file = re.sub(r'[<>:"/\\|?*]', '_', event_name)
    sanitized_event_name_for_file = sanitized_event_name_for_file.replace(' ', '_')
    output_filename = f"{sanitized_event_name_for_file}_stage3_final{lang_code}.json"
    
    # Create mirror directory structure in output
    relative_output_path = get_relative_output_path(stage2_filepath, input_dir, output_dir)
    os.makedirs(relative_output_path, exist_ok=True)
    output_filepath = os.path.join(relative_output_path, output_filename)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(final_output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully processed event '{event_name}'. Output saved to: {output_filepath}")
        return "processed"
    except IOError as e:
        logger.error(f"Failed to write output file {output_filepath} for event '{event_name}': {e}")
        return "failed"
    except Exception as e:
        logger.error(f"An unexpected error occurred during saving output for event '{event_name}': {e}", exc_info=True)
        return "failed"
    
# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3: Structure article text and link sources from Stage 2 output.")
    parser.add_argument("--stage2_dir", type=str, help="Path to the directory containing Stage 2 output JSON files.")
    parser.add_argument("--output_dir", type=str, help="Path to the directory where Stage 3 output JSON files should be saved.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--log_file", default="process_stage3.log", help="Path to the log file (e.g., process_stage3.log).")
    
    args = parser.parse_args()

    # Prompt for missing paths
    if not args.stage2_dir:
        args.stage2_dir = input("Enter path to Stage 2 directory: ").strip()
    if not args.output_dir:
        args.output_dir = input("Enter path to Output directory: ").strip()

    setup_logging(args.debug, args.log_file)
    
    logger.info("--- Stage 3 Processing Script Started ---")
    logger.info(f"Stage 2 Input Directory: {args.stage2_dir}")
    logger.info(f"Stage 3 Output Directory: {args.output_dir}")
    if args.debug: logger.debug("Debug mode is enabled.")

    # Validate directories
    if not os.path.isdir(args.stage2_dir):
        logger.critical(f"Error: Stage 2 directory does not exist or is not a directory: {args.stage2_dir}")
        sys.exit(1)
    
    try:
        os.makedirs(args.output_dir, exist_ok=True)
        logger.info(f"Ensured output directory exists: {args.output_dir}")
    except OSError as e:
        logger.critical(f"Error: Could not create output directory {args.output_dir}: {e}")
        sys.exit(1)

    # Load processing state
    processing_state = load_processing_state()
    # Use normalized absolute paths for robust state tracking
    processed_files_set = set(os.path.normpath(os.path.abspath(p)) for p in processing_state.get("processed_files", []))
    failed_files_set = set(os.path.normpath(os.path.abspath(p)) for p in processing_state.get("failed_files", []))

        # Collect Stage 2 files to process (recursively)
    stage2_files_to_process = []
    try:
        for root, _, files in os.walk(args.stage2_dir):
            for filename in files:
                if filename.endswith(".json"):
                    full_path = os.path.join(root, filename)
                    stage2_files_to_process.append(os.path.normpath(os.path.abspath(full_path)))
    except FileNotFoundError:
        logger.critical(f"Error: Cannot list files in Stage 2 directory (not found): {args.stage2_dir}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error listing files in Stage 2 directory {args.stage2_dir}: {e}", exc_info=True)
        sys.exit(1)
        
    logger.info(f"Found {len(stage2_files_to_process)} JSON files in Stage 2 directory.")

    # Counters for summary
    total_files_considered = len(stage2_files_to_process)
    newly_processed_count = 0
    skipped_as_processed_count = 0
    skipped_as_failed_count = 0
    newly_failed_count = 0

    for stage2_filepath_abs_norm in stage2_files_to_process:
        event_short_filename = os.path.basename(stage2_filepath_abs_norm)
        
        if stage2_filepath_abs_norm in processed_files_set:
            logger.info(f"Skipping (already processed): {event_short_filename}")
            skipped_as_processed_count += 1
            continue
        
        if stage2_filepath_abs_norm in failed_files_set:
            logger.warning(f"Skipping (previously failed; remove from {STATE_FILE} to retry): {event_short_filename}")
            skipped_as_failed_count +=1
            continue

        # Process the file
        status = process_single_event_file(stage2_filepath_abs_norm, args.output_dir, args.stage2_dir)
        
        # Update state
        if status == "processed":
            processing_state.setdefault("processed_files", []).append(stage2_filepath_abs_norm)
            newly_processed_count += 1
        elif status == "failed":
            processing_state.setdefault("failed_files", []).append(stage2_filepath_abs_norm)
            newly_failed_count += 1
        
        save_processing_state(processing_state) # Save state after each file

    logger.info("--- Stage 3 Processing Finished ---")
    logger.info(f"Summary - Total Stage 2 files considered: {total_files_considered}")
    logger.info(f"  Newly processed in this run: {newly_processed_count}")
    logger.info(f"  Skipped (already processed): {skipped_as_processed_count}")
    logger.info(f"  Skipped (previously failed): {skipped_as_failed_count}")
    logger.info(f"  Newly failed in this run: {newly_failed_count}")
    logger.info(f"Total files now in 'processed' state: {len(processing_state.get('processed_files',[]))}")
    logger.info(f"Total files now in 'failed' state: {len(processing_state.get('failed_files',[]))}")
    logger.info(f"Log file available at: {os.path.abspath(args.log_file)}")
    logger.info(f"State file available at: {os.path.abspath(STATE_FILE)}")