# ==============================================
# <<< IMPORTS >>>
# ==============================================

import os
import sys
import re
import time
import random
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Tuple, Set, Optional
import argparse
from requests.exceptions import RequestException, Timeout  # Add Timeout import here


# ==============================================
# <<< LOAD ENVIRONMENT VARIABLES >>>
# ==============================================
# Construct the path to the .env file expected in the Back-End directory
# Assumes this script is located at Back-End/src/IA_modele_treat/
try:
    script_path = Path(__file__).resolve() # Get absolute path of the script
    # Go up three levels (IA_modele_treat -> src -> Back-End)
    project_backend_dir = script_path.parent.parent.parent
    dotenv_path = project_backend_dir / '.env'

    # Load the .env file
    loaded = load_dotenv(dotenv_path=dotenv_path, override=True) # Override system env vars if conflicts

    if loaded:
        print(f"[INFO] Loaded environment variables from: {dotenv_path}")
    else:
        print(f"[WARNING] .env file not found at {dotenv_path}. Relying solely on system environment variables.")

except NameError:
     # Handle case where __file__ is not defined (e.g., interactive interpreter)
     print("[WARNING] Could not determine script path automatically. Searching for .env in current/parent dirs.")
     loaded = load_dotenv(override=True)
     if not loaded:
          print("[WARNING] .env file not found in current or parent directories.")
except Exception as e:
     print(f"[ERROR] An error occurred locating the .env file path: {e}")
# ==============================================
# <<< CONFIGURATION >>>
# ==============================================

# --- API Key Configuration ---
# Load from environment variable first, then potentially fallback or error
gemini_key_env = os.environ.get('GEMINI_API_KEY')
API_KEYS_MODELS = []

# Add keys/models - PRIORITIZE environment variable if found
if gemini_key_env:
    print(f"Using API key from environment variable.")
    # Add models associated with the environment key first if desired
    # Example: Assuming the env key works for all these
    API_KEYS_MODELS.extend([
    {
        'key': gemini_key_env, # <-- REPLACE
        'model': 'gemini-1.5-pro',
        'max_tokens': 1048575  # Verify
    },
    {
        'key': gemini_key_env, # <-- REPLACE
        'model': 'gemini-2.0-flash',
        'max_tokens': 1048575  # Verify
    },
    {
        'key': gemini_key_env, # <-- REPLACE
        'model': 'gemini-2.0-flash-lite',
        'max_tokens': 262144 # Verify
    },
    {
        'key': gemini_key_env, # <-- REPLACE
        'model': 'gemini-1.5-flash',
        'max_tokens': 1048575  # Verify
    }
    ])
else:
    print("WARNING: GEMINI_API_KEY environment variable not set. Script will fail if no keys are hardcoded below.")
    # Add hardcoded keys as fallback ONLY IF NECESSARY and you understand the risk
    # Example:
    # API_KEYS_MODELS.append({
    #     'key': 'YOUR_HARDCODED_KEY_1', # Replace or remove
    #     'model': 'gemini-1.5-flash',
    #     'max_tokens': 1048575
    # })

# Error out if no keys were configured
if not API_KEYS_MODELS:
    logging.critical("FATAL ERROR: No Gemini API keys configured via environment variable or hardcoding.")
    sys.exit("API key configuration missing. Set GEMINI_API_KEY environment variable or configure keys in the script.")

# --- Processing Configuration ---
TOKEN_ESTIMATION_RATIO = 4
PROMPT_TOKEN_BUFFER = 2000
MIN_TEXT_LENGTH = 100
API_REQUEST_TIMEOUT_SECONDS = 120
RETRY_ATTEMPTS_PER_KEY = 3 # How many times to retry with the *same* key for retryable errors
DELAY_BETWEEN_API_CALLS_SECONDS = (1, 3) # Base delay before *any* API call attempt
DELAY_ON_ERROR_SECONDS = 20 # Delay *specifically* after a retryable error (503, Timeout, JSON Fail) before retrying SAME key
DELAY_AFTER_KEY_SWITCH = 5   # Shorter delay after switching keys due to rate limit/invalid key
STATE_FILE_NAME = 'stage1_progress.json'

# --- LLM Output Structure Examples ---
LLM_RELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE = { "relevance_status": "relevant", "source_summary": "...", "extracted_key_facts": ["...", "..."] }
LLM_IRRELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE = { "relevance_status": "irrelevant", "relevance_reason": "..." }

# --- LLM Prompt Template ---
LLM_STAGE1_PROMPT_TEMPLATE = """{truncation_note}You are a highly diligent expert historian and data analyst tasked with thoroughly processing a historical source related to the event: "{event_name}".

Your primary task is to determine if the content of the provided source text is **directly relevant** to the event "{event_name}".

Based on your assessment, output your result strictly in ONE of the two following JSON formats. Ensure the output is valid, complete, and well-formed JSON according to the chosen format. Do NOT include any extra text or formatting outside the JSON block.

**--- INSTRUCTIONS FOR RELEVANT SOURCES ---**
If the source text IS **directly relevant** to "{event_name}", perform the following tasks with the **highest priority given to comprehensive extraction of information**, even if it makes the summary less brief:

1.  **Comprehensive Key Information Extraction:** Carefully read the entire relevant text provided. **Identify and extract ALL significant historical entities, specific dates (or date ranges/periods), key events, actions, concepts, relationships between entities, findings, arguments, or data points** that are discussed and are relevant to the historical context. Extract as much concrete historical detail as possible. List these in the `extracted_key_facts` list. Each item in the list should be a clear, concise statement of a single fact or data point. Where possible, include relevant context (like associated dates, people, or places) directly in the fact statement itself.
2.  **Detailed Historical Summary:** Based on the key information you have extracted, write a detailed summary of the historical content presented in this source that relates to the event "{event_name}". This summary should cover the main findings, arguments, or the narrative flow of the source. **Ensure the summary incorporates or reflects the key facts identified in your extraction.** Prioritize covering the important historical points over extreme brevity.

Output your result strictly in this JSON format for **RELEVANT** sources:
{relevant_output_structure}

**--- INSTRUCTIONS FOR IRRELEVANT SOURCES ---**
If the source text is **NOT directly relevant** to "{event_name}":

1.  Provide a brief, specific reason why it is not relevant, referencing the content's actual focus.
2.  Output your result strictly in this JSON format for **IRRELEVANT** sources:
    {irrelevant_output_structure}

---

[SOURCE_TEXT]
{source_text}
[/SOURCE_TEXT]

---

Please provide the JSON output corresponding to either the RELEVANT or IRRELEVANT format, based on the relevance of the source text to "{event_name}". Provide only the JSON object.
"""

# ==============================================
# <<< LOGGING SETUP >>>
# ==============================================
# (ColorFormatter and logger setup remain the same as previous version)
class ColorFormatter(logging.Formatter):
    COLORS = { 'DEBUG': '\033[90m', 'INFO': '\033[94m', 'WARNING': '\033[93m', 'ERROR': '\033[91m', 'CRITICAL': '\033[91m\033[1m', 'RESET': '\033[0m' }
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        message = super().format(record)
        if sys.stderr.isatty(): return f"{log_color}{message}{self.COLORS['RESET']}"
        else: return message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    log_file_path = Path(__file__).parent / 'process_stage1.log'
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s [%(funcName)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stderr)
    console_formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO) # Default console level
    logger.addHandler(console_handler)

# ==============================================
# <<< HELPER FUNCTIONS >>>
# ==============================================
# (load_state, save_state, get_source_uid, estimate_tokens, truncate_text remain the same)
def load_state(state_path: Path) -> Tuple[Set[str], int]:
    try:
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f: state = json.load(f)
            processed = set(state.get('processed', [])); active_key_index = state.get('active_key_index', 0)
            if active_key_index >= len(API_KEYS_MODELS): logger.warning(f"State index {active_key_index} out of bounds. Reset 0."); active_key_index = 0
            logger.info(f"Loaded state: {len(processed)} processed, key index {active_key_index}")
            return processed, active_key_index
    except Exception as e: logger.error(f"Error loading state from {state_path}: {e}. Starting fresh.")
    return set(), 0

def save_state(state_path: Path, processed: Set[str], active_key_index: int):
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f: json.dump({'processed': sorted(list(processed)), 'active_key_index': active_key_index }, f, indent=2)
        logger.debug(f"Saved state: {len(processed)} items, key index {active_key_index}")
    except Exception as e: logger.error(f"Error saving state to {state_path}: {e}")

def get_source_uid(input_path: Path, source_url: str) -> str:
    """Generates a unique identifier for a source based on its input file and URL."""
    try:
        base_input_dir = input_path
        # --- CORRECTED: Move while loop to the next line ---
        while base_input_dir.name != 'input' and base_input_dir.parent != base_input_dir:
            base_input_dir = base_input_dir.parent
    except Exception as e:
        # Fallback if error occurs during parent traversal (e.g., missing .name)
        logger.warning(f"Error finding 'input' ancestor for {input_path}: {e}. Using original path.")
        base_input_dir = input_path

    try:
        # Attempt to get path relative to parent of 'input' dir if found
        if base_input_dir.name == 'input' and base_input_dir.parent != base_input_dir:
            relative_path = input_path.relative_to(base_input_dir.parent)
        else:
            # Fallback to absolute path if 'input' not found or other issue
            relative_path = input_path.resolve()
            if base_input_dir.name != 'input':
                 logger.debug(f"Ancestor 'input' directory not found for {input_path}. Using absolute path for UID.")

    except ValueError:
        # Fallback if relative_to fails (e.g., different drives)
        relative_path = input_path.resolve()
        logger.warning(f"Could not get relative path for {input_path}. Using absolute path for UID.")
    except Exception as e:
         # Catch other unexpected errors during path handling
         relative_path = input_path.resolve()
         logger.error(f"Unexpected error getting relative path for {input_path}: {e}. Using absolute path.")

    # Ensure source_url is a string before joining
    if not isinstance(source_url, str):
        source_url = str(source_url)

    # Combine relative (or absolute fallback) path and URL
    return f"{relative_path}|{source_url}"

def estimate_tokens(text: str) -> int: return len(text or "") // TOKEN_ESTIMATION_RATIO

def truncate_text(text: str, max_tokens: int) -> Tuple[str, dict]:
    max_chars = max(0, max_tokens * TOKEN_ESTIMATION_RATIO); original_length = len(text or "")
    trunc_meta = {'truncated': False, 'original_length_chars': original_length, 'truncated_length_chars': original_length, 'max_chars_allowed': max_chars, 'estimated_tokens': estimate_tokens(text or "")}
    if original_length > max_chars:
        truncated = (text or "")[:max_chars]; trunc_meta.update({'truncated': True, 'truncated_length_chars': len(truncated), 'estimated_tokens': estimate_tokens(truncated)})
        return truncated, trunc_meta
    else: return text or "", trunc_meta

# ==============================================
# <<< NEW ERROR CHECKING HELPERS >>>
# ==============================================
def is_rate_limit_error(response: Optional[requests.Response]) -> bool:
    if response is None: return False
    if response.status_code == 429: return True
    try:
        error_body = response.json().get("error", {})
        if error_body.get("status") == "RESOURCE_EXHAUSTED": return True
        return any('RATE_LIMIT_EXCEEDED' in detail.get('reason', '') for detail in error_body.get('details', []))
    except Exception: return False

def is_input_token_limit_error(response: Optional[requests.Response]) -> bool:
    if response is None or response.status_code != 400: return False
    try:
        message = response.json().get('error', {}).get('message', '').lower()
        return "input token count" in message and "exceeds the maximum" in message
    except Exception: return False

def is_invalid_key_error(response: Optional[requests.Response]) -> bool:
    if response is None or response.status_code != 400: return False
    try:
        # Gemini specific error check - adjust if needed for other APIs
        message = response.json().get('error', {}).get('message', '')
        return "API_KEY_INVALID" in message or "API key not valid" in message
    except Exception: return False

def is_overload_error(response: Optional[requests.Response]) -> bool:
     if response is None: return False
     # Standard HTTP code for temporary server overload
     return response.status_code == 503

# ==============================================
# <<< UPDATED API HANDLING >>>
# ==============================================
def call_gemini_api(api_key: str, model: str, prompt: str) -> Tuple[Optional[dict], Optional[Exception], Optional[requests.Response]]:
    """Makes a single API call, returns structured result or error info."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {'Content-Type': 'application/json'}
    params = {'key': api_key}
    logger.debug(f"Calling Gemini API: {model}...")
    try:
        response = requests.post(
            url, headers=headers, params=params,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=API_REQUEST_TIMEOUT_SECONDS
        )
        # Do not raise_for_status here, let the caller inspect the response object
        return response.json(), None, response # Return JSON potentially, no Python error, raw response
    except json.JSONDecodeError as e: # Handle cases where API returns non-JSON on error
         return None, e, response # Return Python error, raw response might have info
    except Timeout as e:
        return None, e, None # Return Timeout error, no response obj
    except RequestException as e:
        return None, e, e.response # Return other requests error, maybe response obj
    except Exception as e: # Catch other unexpected errors
        logger.error(f"Unexpected error during API call setup/execution: {e}", exc_info=True)
        return None, e, None # Return general Python error, no response obj

def parse_and_validate_llm_output(raw_output_text: str) -> Tuple[Optional[dict], Optional[str]]:
    """Attempts to parse JSON, clean it, and validate against expected structures."""
    if not raw_output_text:
        return None, "LLM output was empty."

    # Basic cleaning: Remove markdown backticks if present
    cleaned_text = re.sub(r"^\s*```json\s*|\s*```\s*$", "", raw_output_text.strip(), flags=re.MULTILINE)

    try:
        parsed_data = json.loads(cleaned_text)
        if not isinstance(parsed_data, dict):
             return None, f"Parsed JSON is not a dictionary (type: {type(parsed_data)})."

        status = parsed_data.get("relevance_status")
        if status == "relevant":
            # Validate relevant structure
            if not all(k in parsed_data for k in ["source_summary", "extracted_key_facts"]):
                return None, f"Missing required keys for 'relevant' status. Found: {list(parsed_data.keys())}"
            if not isinstance(parsed_data["extracted_key_facts"], list):
                 return None, "'extracted_key_facts' is not a list."
            # Basic check passed
            return parsed_data, None
        elif status == "irrelevant":
            # Validate irrelevant structure
            if "relevance_reason" not in parsed_data:
                return None, f"Missing required 'relevance_reason' for 'irrelevant' status. Found: {list(parsed_data.keys())}"
            # Basic check passed
            return parsed_data, None
        else:
            return None, f"Invalid 'relevance_status': '{status}'. Must be 'relevant' or 'irrelevant'."

    except json.JSONDecodeError as e:
        return None, f"JSON Decode Error: {e}. Snippet: '{cleaned_text[:200]}...'"
    except Exception as e:
        logger.error(f"Unexpected error during LLM output validation: {e}", exc_info=True)
        return None, f"Unexpected validation error: {e}"


# *** REFACTORED function with specific error handling ***
def process_source(source: dict, event_name: str, state_path: Path, processed_set: Set[str], active_key_index: int) -> Tuple[Optional[dict], int]:
    """
    Processes a single source using the LLM API with specific error handling,
    retries, and key rotation based on error type.
    Returns the result entry (dict) or None (if skipped), and the
    potentially updated global active_key_index.
    """
    uid = get_source_uid(source['input_path'], source['source_url'])
    if uid in processed_set:
        logger.info(f"Skipping already processed: {source['source_url']} from {source['input_path'].name}")
        return None, active_key_index # Return None (skipped), original key index

    logger.info(f"Processing UID: {uid} for event '{event_name}'")

    # Initialize output entry structure (same as before)
    output_entry = { 'source_uid': uid, 'original_source_metadata': { 'original_item_url': source.get('original_item_url', ''), 'source_type': source.get('source_type', 'unknown'), 'source_url': source.get('source_url', ''), 'link_text': source.get('link_text'), 'original_language_section': source.get('language', 'unknown') }, 'processing_metadata': { 'text_truncated': False, 'original_text_length_chars': len(source.get('scraped_text', '')), 'truncated_text_length_chars': None, 'max_chars_allowed': None, 'estimated_tokens': None, 'api_model_used': None, 'api_key_index_used': None, }, 'llm_processed_output': None, 'processing_status': 'pending', 'error_message': None }
    source_text = source.get('scraped_text', '')

    # --- Pre-API Checks ---
    if len(source_text) < MIN_TEXT_LENGTH:
        logger.warning(f"Skipping source {uid} due to short text ({len(source_text)} chars).")
        output_entry['processing_status'] = 'skipped_short_text'; output_entry['error_message'] = f"Text length < {MIN_TEXT_LENGTH}"
        processed_set.add(uid); save_state(state_path, processed_set, active_key_index)
        return output_entry, active_key_index
    if not API_KEYS_MODELS:
        logger.critical("No API keys configured."); output_entry['processing_status'] = 'failed'; output_entry['error_message'] = "No API keys available."
        return output_entry, active_key_index

    # --- API Call Loop (Handles Key Rotation) ---
    total_keys = len(API_KEYS_MODELS)
    keys_tried_count = 0 # How many distinct keys tried for this source
    current_key_index = active_key_index # Start with the globally active key index

    while keys_tried_count < total_keys:
        key_info = API_KEYS_MODELS[current_key_index]
        current_api_key = key_info['key']
        current_model = key_info['model']
        logger.info(f"Using Key Index {current_key_index} ({current_model}). Try {keys_tried_count + 1}/{total_keys} for source {uid}")
        output_entry['processing_metadata']['api_model_used'] = current_model
        output_entry['processing_metadata']['api_key_index_used'] = current_key_index

        # --- Prepare Text and Prompt for *this specific key/model* ---
        prompt_structure_estimate = estimate_tokens(LLM_STAGE1_PROMPT_TEMPLATE.format(truncation_note="", event_name="X"*len(event_name), relevant_output_structure=json.dumps(LLM_RELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE), irrelevant_output_structure=json.dumps(LLM_IRRELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE), source_text=""))
        max_source_tokens = key_info['max_tokens'] - prompt_structure_estimate - PROMPT_TOKEN_BUFFER
        if max_source_tokens <= 0:
            logger.error(f"Prompt structure estimate + buffer exceeds model max tokens for {current_model}. Skipping key {current_key_index}.")
            output_entry['error_message'] = f"Prompt too long for model {current_model}"
            keys_tried_count += 1; current_key_index = (current_key_index + 1) % total_keys; continue # Try next key

        processed_text, trunc_meta = truncate_text(source_text, max_source_tokens)
        output_entry['processing_metadata'].update(trunc_meta)
        truncation_note = f"NOTE: Text TRUNCATED to approx {trunc_meta['estimated_tokens']} tokens. " if trunc_meta['truncated'] else ""
        if trunc_meta['truncated']: logger.warning(f"Truncated text for {uid} to {trunc_meta['truncated_length_chars']} chars for model {current_model}.")

        try:
            prompt = LLM_STAGE1_PROMPT_TEMPLATE.format(truncation_note=truncation_note, event_name=event_name, relevant_output_structure=json.dumps(LLM_RELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE, indent=2), irrelevant_output_structure=json.dumps(LLM_IRRELEVANT_SOURCE_OUTPUT_STRUCTURE_EXAMPLE, indent=2), source_text=processed_text)
        except Exception as e: logger.error(f"Failed prompt formatting for {uid}: {e}", exc_info=True); output_entry['processing_status'] = 'failed'; output_entry['error_message'] = f"Prompt format error: {e}"; processed_set.add(uid); save_state(state_path, processed_set, active_key_index); return output_entry, active_key_index

        # --- Inner Retry Loop for the CURRENT Key ---
        last_error = None
        raw_response = None
        api_response_json = None
        should_switch_key = False # Flag to indicate if we need to rotate key after this inner loop

        for attempt in range(RETRY_ATTEMPTS_PER_KEY):
            logger.info(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS_PER_KEY} with Key Index {current_key_index}...")
            time.sleep(random.uniform(*DELAY_BETWEEN_API_CALLS_SECONDS))

            api_response_json, error, raw_response = call_gemini_api(current_api_key, current_model, prompt)
            last_error = error # Store error for post-loop analysis

            # --- Handle API Call Result ---
            if api_response_json and not error and raw_response and raw_response.status_code == 200:
                # Successful API call, proceed to validation below
                break # Exit inner retry loop

            # --- Specific Error Handling ---
            error_handled = False
            if raw_response is not None: # We have an HTTP response object
                if is_input_token_limit_error(raw_response):
                    logger.error(f"FATAL for Source: Input token limit exceeded for model {current_model}. Cannot retry. UID: {uid}")
                    output_entry['processing_status'] = 'failed_input_too_large'; output_entry['error_message'] = f"Input too large for {current_model} ({trunc_meta['estimated_tokens']} vs limit near {key_info['max_tokens']})"; processed_set.add(uid); save_state(state_path, processed_set, active_key_index)
                    return output_entry, active_key_index # EXIT IMMEDIATELY for this source

                elif is_invalid_key_error(raw_response):
                    logger.error(f"FATAL for Key: Invalid API Key detected (Index {current_key_index}). Switching key.")
                    output_entry['error_message'] = f"Invalid API Key (Index {current_key_index})"
                    should_switch_key = True; error_handled = True; break # Break inner loop, force key switch

                elif is_rate_limit_error(raw_response):
                    logger.warning(f"Rate limit hit on key index {current_key_index}. Switching key.")
                    output_entry['error_message'] = f"Rate limit on Key Index {current_key_index}"
                    should_switch_key = True; error_handled = True; break # Break inner loop, force key switch

                elif is_overload_error(raw_response):
                    logger.warning(f"API Overload (503) on attempt {attempt + 1}. Retrying same key after delay...")
                    output_entry['error_message'] = "API Overload (503)"
                    error_handled = True # Fall through to wait/retry logic below

                # Add other specific HTTP status checks if needed (e.g., 403 Forbidden)

            if not error_handled and isinstance(error, Timeout):
                logger.warning(f"API Timeout on attempt {attempt + 1}. Retrying same key after delay...")
                output_entry['error_message'] = "API Request Timeout"
                error_handled = True # Fall through to wait/retry logic below

            if not error_handled:
                # Generic RequestException or other Python error during call
                logger.warning(f"API call failed on attempt {attempt+1}: {error}. Retrying same key after delay...")
                output_entry['error_message'] = f"API Call Failed: {str(error)[:200]}"
                error_handled = True # Fall through to wait/retry logic below

            # --- Wait only if retrying the SAME key ---
            if attempt < RETRY_ATTEMPTS_PER_KEY - 1 and not should_switch_key:
                 logger.info(f"Waiting {DELAY_ON_ERROR_SECONDS}s before next attempt with same key.")
                 time.sleep(DELAY_ON_ERROR_SECONDS)
            elif should_switch_key:
                 # No need to wait if we are breaking to switch key immediately
                 pass

        # --- After Inner Retry Loop (for current key) ---

        if api_response_json: # API call was successful at least once
            # --- Validate LLM Output ---
            parsed_data, validation_error = parse_and_validate_llm_output(
                api_response_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            )
            if parsed_data and not validation_error:
                logger.info(f"Successfully processed source {uid} (Status: {parsed_data['relevance_status']})")
                output_entry['llm_processed_output'] = parsed_data
                output_entry['processing_status'] = 'success'
                output_entry['error_message'] = None
                processed_set.add(uid)
                save_state(state_path, processed_set, active_key_index) # Save state with the working key index
                return output_entry, active_key_index # SUCCESS - return result, index unchanged globally

            else: # JSON validation failed
                logger.error(f"LLM output validation failed for {uid}: {validation_error}. Retrying...")
                output_entry['error_message'] = f"LLM Validation Error: {validation_error}"
                # Validation failure triggers same retry logic as overload/timeout for THIS KEY
                # Check if we exhausted retries FOR THIS KEY during the API call phase (rare case)
                # If API succeeded but JSON is bad, we might want to treat it as retryable ONCE or TWICE on same key, then switch.
                # Let's simplify: treat JSON validation failure like Overload/Timeout - retry same key up to limit, then switch.
                # Since we are *after* the inner loop, failing validation means we try the next key.
                should_switch_key = True # Force key switch after validation failure

        # --- Handle Key Switching / Final Failure ---
        if should_switch_key or api_response_json is None: # Need to switch key or all attempts failed
             keys_tried_count += 1
             if keys_tried_count < total_keys:
                  new_key_index = (current_key_index + 1) % total_keys
                  logger.warning(f"Switching from key index {current_key_index} to {new_key_index} for source {uid}.")
                  current_key_index = new_key_index
                  # Update global active key index *only* if failure was key-specific
                  if is_invalid_key_error(raw_response) or is_rate_limit_error(raw_response):
                       logger.warning(f"Updating global active key index to {current_key_index}")
                       active_key_index = current_key_index
                  save_state(state_path, processed_set, active_key_index) # Save potentially updated global index
                  time.sleep(DELAY_AFTER_KEY_SWITCH) # Small delay after switching
                  # Continue the outer `while keys_tried_count < total_keys:` loop
             else:
                  # All keys have been tried for this source
                  logger.error(f"All {total_keys} API keys tried and failed for source {uid}. Last error: {output_entry['error_message'] or last_error}")
                  exit
                #   output_entry['processing_status'] = 'failed_all_keys'
                #   # Keep the last specific error message if available
                #   processed_set.add(uid) # Mark as processed (failed)
                #   save_state(state_path, processed_set, active_key_index)
                #   return output_entry, active_key_index # Return failure

    # Should not be reached if logic is correct, but safeguard
    logger.error(f"Exited processing loop unexpectedly for {uid}.")
    output_entry['processing_status'] = 'failed_unexpected'; output_entry['error_message'] = "Unexpected exit from processing loop."
    processed_set.add(uid); save_state(state_path, processed_set, active_key_index)
    return output_entry, active_key_index


# ==============================================
# <<< MAIN PROCESSING >>>
# ==============================================
# (process_files function remains the same - it extracts sources and calls process_source)
def process_files(input_dir: Path, output_dir: Path, state_path: Path):
    if not API_KEYS_MODELS: 
        logger.critical("Cannot start: No API keys configured.")
        return

    processed_set, active_key_index = load_state(state_path)
    initial_processed_count = len(processed_set)
    files_processed_this_run = sources_attempted_this_run = sources_succeeded_this_run = sources_failed_this_run = sources_skipped_this_run = 0
    logger.info(f"Starting processing. Input: '{input_dir}', Output: '{output_dir}'")
    
    input_files = sorted(list(input_dir.rglob('*.json')))
    if not input_files: 
        logger.warning(f"No JSON files found in: {input_dir}")
        return
    
    logger.info(f"Found {len(input_files)} JSON files to potentially process.")

    for input_path in input_files:
        logger.info(f"--- Processing file: {input_path.relative_to(input_dir)} ---")
        files_processed_this_run += 1
        output_path = output_dir / input_path.relative_to(input_dir)
        
        # Initialize output data with existing results if any
        output_data = {'event': '', 'input_file_path': str(input_path.relative_to(input_dir)), 'stage1_processed_results': {}}
        if output_path.exists():
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    output_data = existing_data
                    logger.info(f"Loaded existing output with {sum(len(v) for v in existing_data['stage1_processed_results'].values())} entries")
            except Exception as e:
                logger.error(f"Error loading existing output {output_path}: {e}")

        try:
            with open(input_path, 'r', encoding='utf-8') as f: 
                data = json.load(f)
            event_name = data.get('event', input_path.stem)
            output_data['event'] = event_name  # Ensure event name is updated
        except Exception as e: 
            logger.error(f"Error reading/parsing {input_path}: {e}. Skipping file.")
            continue

        # Collect sources to process
        sources_in_file = []
        for lang, items in data.get('scraped_results', {}).items():
            if not isinstance(items, list): 
                logger.warning(f"Invalid 'scraped_results' for '{lang}' in {input_path.name}. Skipping.")
                continue
                
            for item_index, item in enumerate(items):
                if not isinstance(item, dict): 
                    logger.warning(f"Invalid item {item_index} in '{lang}' of {input_path.name}. Skipping.")
                    continue
                
                original_item_url = item.get('original_result', {}).get('url', f'unknown_{item_index}')
                
                # Process main URL scrape
                if main_scrape := item.get('main_url_scrape'):
                    if isinstance(main_scrape, dict):
                        sources_in_file.append({
                            'input_path': input_path,
                            'language': lang,
                            'original_item_url': original_item_url,
                            'source_type': 'main_url',
                            'source_url': main_scrape.get('url', ''),
                            'scraped_text': main_scrape.get('scraped_text', '')
                        })
                
                # Process PDF links
                for pdf_index, pdf in enumerate(item.get('linked_pdfs_found', [])):
                    if isinstance(pdf, dict):
                        sources_in_file.append({
                            'input_path': input_path,
                            'language': lang,
                            'original_item_url': original_item_url,
                            'source_type': 'linked_pdf',
                            'source_url': pdf.get('pdf_url', ''),
                            'link_text': pdf.get('link_text'),
                            'scraped_text': pdf.get('scraped_text', '')
                        })

        logger.info(f"Found {len(sources_in_file)} potential sources in {input_path.name}")
        
        for source in sources_in_file:
            sources_attempted_this_run += 1
            uid = get_source_uid(source['input_path'], source['source_url'])
            
            if uid in processed_set:
                logger.debug(f"Skipping already processed: {uid}")
                continue
                
            try:
                # Process source WITHOUT modifying state
                result_entry, updated_active_key_index = process_source(
                    source=source,
                    event_name=event_name,
                    state_path=state_path,
                    processed_set=processed_set.copy(),  # Pass copy to prevent modification
                    active_key_index=active_key_index
                )
                active_key_index = updated_active_key_index
                
                if result_entry:
                    # Add to output data
                    lang = source.get('language', 'unknown')
                    output_data['stage1_processed_results'].setdefault(lang, []).append(result_entry)
                    
                    # Immediately save results
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                    logger.debug(f"Incrementally saved {output_path}")
                    
                    # Update state only AFTER successful save
                    processed_set.add(uid)
                    save_state(state_path, processed_set, active_key_index)
                    
                    # Update counters
                    status = result_entry.get('processing_status', 'unknown')
                    if status == 'success': 
                        sources_succeeded_this_run += 1
                    elif status.startswith('failed'): 
                        sources_failed_this_run += 1
                    elif status.startswith('skipped'): 
                        sources_skipped_this_run += 1
                        
            except Exception as e:
                logger.error(f"Critical error processing {uid}: {e}", exc_info=True)
                save_state(state_path, processed_set, active_key_index)  # Preserve state
                continue  # Continue with next source

        # Final save to catch any remaining updates
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Final save for {input_path.name}")
        except Exception as e:
            logger.error(f"Error during final save for {input_path.name}: {e}")

    # Final summary
    final_processed_count = len(processed_set)
    newly_processed = final_processed_count - initial_processed_count
    logger.info("="*40)
    logger.info("Processing Run Summary:")
    logger.info(f"Input Directory: {input_dir}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Files Scanned This Run: {files_processed_this_run}")
    logger.info(f"Sources Attempted This Run: {sources_attempted_this_run}")
    logger.info(f"  Sources Succeeded: {sources_succeeded_this_run}")
    logger.info(f"  Sources Failed: {sources_failed_this_run}")
    logger.info(f"  Sources Skipped (e.g., short): {sources_skipped_this_run}")
    logger.info(f"Total Processed Sources (in state): {final_processed_count} (added {newly_processed} this run)")
    logger.info(f"Final Active API Key Index: {active_key_index}")
    logger.info("="*40)

# ==============================================
# <<< MAIN FUNCTION >>>
# ==============================================
# (main function remains the same - handles argparse/input prompts)
def main():
    parser = argparse.ArgumentParser(description='Process historical sources using Gemini API.')
    parser.add_argument('--input_dir', type=str, required=False, help='Input directory containing scraped JSON files.')
    parser.add_argument('--output_dir', type=str, required=False, help='Output directory for processed JSON files (default: ./stage1_output)')
    parser.add_argument('--debug', action='store_true', help='Enable DEBUG level logging.')
    args = parser.parse_args()

    if args.debug:
         for handler in logger.handlers:
              if isinstance(handler, logging.StreamHandler): handler.setLevel(logging.DEBUG)
         logger.setLevel(logging.DEBUG); logger.debug("DEBUG logging enabled.")

    input_dir_path = args.input_dir
    while not input_dir_path:
        try: user_input = input("Enter input directory path: ").strip(); temp_path = Path(user_input)
        except EOFError: logger.critical("No input provided. Exiting."); sys.exit(1)
        if temp_path.is_dir(): input_dir_path = user_input; break
        else: logger.warning(f"Path '{user_input}' not valid directory.")
    input_dir = Path(input_dir_path).resolve(); logger.info(f"Using input directory: {input_dir}")

    default_output = Path('./stage1_output').resolve(); output_dir_path = args.output_dir
    if not output_dir_path:
        try: user_output = input(f"Enter output directory path [default: {default_output}]: ").strip()
        except EOFError: user_output = "" # Handle Ctrl+D or empty input
        output_dir_path = user_output or str(default_output)
    output_dir = Path(output_dir_path).resolve(); logger.info(f"Using output directory: {output_dir}")

    state_path = output_dir / STATE_FILE_NAME

    if not input_dir.is_dir(): logger.critical(f"Input directory not found: {input_dir}"); sys.exit(1)
    try: output_dir.mkdir(parents=True, exist_ok=True); logger.info(f"Ensured output directory exists: {output_dir}")
    except Exception as e: logger.critical(f"Could not create output directory {output_dir}: {e}"); sys.exit(1)

    current_processed_set, current_key_index = load_state(state_path) # Load state for interrupt handler
    try: process_files(input_dir, output_dir, state_path)
    except KeyboardInterrupt:
        logger.info("\n--- Process interrupted by user (Ctrl+C) ---")
        current_processed_set, current_key_index = load_state(state_path) # Re-load before saving
        logger.info(f"Saving final state ({len(current_processed_set)} items, key index {current_key_index})...")
        save_state(state_path, current_processed_set, current_key_index); logger.info("State saved. Exiting.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected critical error: {e}", exc_info=True)
        current_processed_set, current_key_index = load_state(state_path) # Re-load before saving
        logger.info(f"Attempting save state after error ({len(current_processed_set)} items, key index {current_key_index})...")
        save_state(state_path, current_processed_set, current_key_index)
        sys.exit(1)

if __name__ == '__main__':
    main()