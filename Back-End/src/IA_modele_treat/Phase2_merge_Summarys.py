import os
import sys
import json
import time
import random
import logging
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set, Union 
from datetime import datetime
from requests.exceptions import RequestException, Timeout
from dotenv import load_dotenv

# ==============================================
# <<< FIX FOR UNICODEENCODEERROR >>>
# ==============================================
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# ==============================================

# ==============================================
# <<< LOAD ENVIRONMENT VARIABLES >>>
# ==============================================
try:
    script_path = Path(__file__).resolve()
    project_backend_dir = script_path.parent.parent.parent
    dotenv_path = project_backend_dir / '.env'
    loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
    if loaded:
        print(f"[INFO] Loaded environment variables from: {dotenv_path}")
    else:
        print(f"[WARNING] .env file not found at {dotenv_path}. Relying solely on system environment variables.")
except NameError:
     print("[WARNING] Could not determine script path automatically. Searching for .env in current/parent dirs.")
     loaded = load_dotenv(override=True)
     if not loaded:
          print("[WARNING] .env file not found in current or parent directories.")
except Exception as e:
     print(f"[ERROR] An error occurred locating the .env file path: {e}")

# ============================================================================
# CONFIGURATION
# ============================================================================
API_KEYS_MODELS = []
gemini_key_env = os.getenv('GEMINI_API_KEY')
if gemini_key_env:
    API_KEYS_MODELS.extend([
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
    logging.warning("GEMINI_API_KEY not found in environment variables.")

if not API_KEYS_MODELS:
    raise ValueError("No API keys configured. Please set GEMINI_API_KEY in environment variables or .env file.")

TOKEN_RATIO = 4
PROMPT_BUFFER_TOKENS = 2000
MIN_TEXT_LENGTH_CHARS = 50
API_TIMEOUT_SECONDS = 500
MAX_RETRIES_PER_KEY = 3
API_CALL_DELAY_SECONDS = 1
ERROR_DELAY_SECONDS = 5
KEY_SWITCH_DELAY_SECONDS = 10
STATE_FILE = "stage2_progress.json"

LLM_STAGE2_PROMPT_TEMPLATE = """
You are an expert historical author and synthesist tasked with writing a comprehensive, well-structured article about a specific historical event, based *only* on provided information from multiple sources.

The event you are writing about is: "{event_name}"

Below is the information extracted from multiple relevant sources about this event. Each source is identified by a number and its unique ID (UID) or URL, followed by the summary and key facts extracted from that source.

--- Source Information ---

{consolidated_source_data}

--- End Source Information ---

Your task is to synthesize ALL of the historical information provided in the "Source Information" section into a single, coherent, and well-written historical article about "{event_name}".

**The output article MUST be written entirely in ENGLISH.**

**Crucial Instructions:**
1.  **Comprehensiveness:** Include all significant events, facts, figures, dates, and details found in the provided summaries and key facts. Aim for comprehensive coverage based *only* on the input you are given. Combine related points from different sources.
2.  **Objectivity:** Do not add outside information or personal opinions. Maintain a formal, objective historical tone.
3.  **Structure:** **Organize the synthesized information into logical sections.** Use appropriate subtitles for each section. Break the text within sections into clear paragraphs.
4.  **Title Generation:** **Create a suitable and informative English title for this article.** This title should accurately reflect the event "{event_name}" but must be in English.
5.  **Citation:** As you write the article, you must include **simple citation markers** directly in the text. Immediately after you present information that is primarily drawn from a specific source, insert the source number from the "Source Information" list enclosed in square brackets, like this: `[#]`.
    * If information in a sentence or clause comes from Source 1, add `[1]`.
    * If information comes from Sources 1 and 3, you could add `[1, 3]` or `[1][3]`. Prioritize accuracy in linking information to its source number. Include markers throughout the text as appropriate.

**Output Format:**
Return *only* the synthesized article text.
The article must adhere strictly to the following Markdown formatting for structure:
* Start directly with the **English** main title you generated: Use a Markdown H1 heading (e.g., `# English Article Title`).
* For each section subtitle: Use a Markdown H2 heading (e.g., `## Section Subtitle`).
* The body of the article must contain the `[#]` citation markers as instructed above.
* **CRITICAL NEGATIVE CONSTRAINT:** DO NOT include any markdown code block delimiters (like ` ```markdown `, ` ```english ` , ` ```json ` , ` ``` `) or any text outside of the formatted article content.
Do NOT include any other text, explanations, or JSON structure in your response. Only the article text formatted in Markdown.
"""

TRANSLATION_PROMPTS = {
    'ar': "Translate the following historical article text into Arabic. Translate the main title (the H1 heading starting with `#`) as well. It is critical to preserve the original structure defined by the Markdown headings (`#` for the main title, `##` for section subtitles) and to preserve all citation markers like `[1]`, `[2]`, `[1, 3]`, etc. exactly as they appear within the translated text. **CRITICAL NEGATIVE CONSTRAINT: DO NOT include any markdown code block delimiters (like ` ```arabic `, ` ```markdown `, ` ``` `) or any text outside of the translated article content.** Only return the fully translated text with the original structure and citations perfectly preserved:",
    'fr': "Translate the following historical article text into French. Translate the main title (the H1 heading starting with `#`) as well. It is critical to preserve the original structure defined by the Markdown headings (`#` for the main title, `##` for section subtitles) and to preserve all citation markers like `[1]`, `[2]`, `[1, 3]`, etc. exactly as they appear within the translated text. **CRITICAL NEGATIVE CONSTRAINT: DO NOT include any markdown code block delimiters (like ` ```french `, ` ```markdown `, ` ``` `) or any text outside of the translated article content.** Only return the fully translated text with the original structure and citations perfectly preserved:",
    'es': "Translate the following historical article text into Spanish. Translate the main title (the H1 heading starting with `#`) as well. It is critical to preserve the original structure defined by the Markdown headings (`#` for the main title, `##` for section subtitles) and to preserve all citation markers like `[1]`, `[2]`, `[1, 3]`, etc. exactly as they appear within the translated text. **CRITICAL NEGATIVE CONSTRAINT: DO NOT include any markdown code block delimiters (like ` ```spanish `, ` ```markdown `, ` ``` `) or any text outside of the translated article content.** Only return the fully translated text with the original structure and citations perfectly preserved:",
}
TARGET_LANGUAGES_FOR_TRANSLATION = ['ar', 'fr', 'es']

# ============================================================================
# LOGGING SETUP
# ============================================================================
class ColorFormatter(logging.Formatter):
    colors = {
        'DEBUG': '\033[94m', 'INFO': '\033[92m', 'WARNING': '\033[93m',
        'ERROR': '\033[91m', 'CRITICAL': '\033[91m\033[1m', 'RESET': '\033[0m'
    }
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.colors:
            return f"{self.colors[record.levelname]}{log_message}{self.colors['RESET']}"
        return log_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.handlers = []
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))
console_handler.encoding = 'utf-8'
console_handler.errors = 'replace'
logger.addHandler(console_handler)
file_handler = logging.FileHandler('process_stage2.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_state() -> Tuple[Set[str], int]:
    processed_set = set()
    active_key_index = 0
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                processed_set = set(state_data.get('processed_events', []))
                active_key_index = state_data.get('active_key_index', 0)
                logging.info(f"Loaded state: {len(processed_set)} processed events, active key index: {active_key_index}")
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error loading state file: {e}. Starting fresh.")
    return processed_set, active_key_index

def save_state(processed_set: Set[str], active_key_index: int) -> None:
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'processed_events': list(processed_set),
                'active_key_index': active_key_index,
                'last_updated': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logging.error(f"Error saving state file: {e}")

def get_event_id(event_name: str, input_file_path: str) -> str:
    return f"{input_file_path}|{event_name}"

def estimate_tokens(text: str) -> int:
    return len(text) // TOKEN_RATIO

def escape_curly_braces(text: str) -> str:
    if not isinstance(text, str): return text
    return text.replace('{', '{{').replace('}', '}}')

def build_consolidated_prompt_and_refs(source_items: List[Dict]) -> Tuple[str, List[str]]:
    formatted_text = ""
    source_references_ordered = []
    for i, source in enumerate(source_items, 1): # 'i' is the source number here
        # Get the URL from original_source_metadata if available, otherwise fall back to source_uid
        source_url = source.get('original_source_metadata', {}).get('source_url', 
                   source.get('source_url', source.get('source_uid', f'unknown_ref_{i}')))
        source_references_ordered.append(source_url)
        
        # Use source_num_str in the f-string
        source_num_str = str(i)
        formatted_text += f"Source {source_num_str} (Reference: {source_url}):\n" 
        formatted_text += f"  Summary: {escape_curly_braces(source.get('source_summary', ''))}\n"
        formatted_text += "  Key Facts:\n"
        key_facts = source.get('extracted_key_facts', [])
        if isinstance(key_facts, list):
             for fact in key_facts:
                 formatted_text += f"   - {escape_curly_braces(fact)}\n"
        else:
             logging.warning(f"Expected list for key_facts for source {source_url}, got {type(key_facts)}.")
        formatted_text += "\n"
    return formatted_text, source_references_ordered

# ============================================================================
# API HANDLING FUNCTIONS
# ============================================================================
def is_rate_limit_error(response) -> bool:
    if response.status_code == 429: return True
    try:
        error = response.json().get('error', {})
        if isinstance(error, dict): return error.get('status') == 'RESOURCE_EXHAUSTED'
    except: pass
    return False

def is_input_token_limit_error(response) -> bool:
    if response.status_code == 400:
        try:
            error_message = response.json().get('error', {}).get('message', '').lower()
            return 'token limit' in error_message or 'too long' in error_message
        except: pass
    return False

def is_invalid_key_error(response) -> bool:
    if response.status_code == 400:
        try:
            error_message = response.json().get('error', {}).get('message', '').lower()
            return 'api key not valid' in error_message or 'invalid api key' in error_message
        except: pass
    return False

def is_overload_error(response) -> bool:
    return response.status_code == 503

def call_gemini_api(api_key: str, model: str, prompt: str) -> Tuple[Optional[str], Optional[Exception], Optional[requests.Response]]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    data = {
        "contents": [{"parts":[{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "topK": 40, "topP": 0.95, "maxOutputTokens": 8192}
    }
    response_text, exception, raw_response = None, None, None
    try:
        raw_response = requests.post(url, headers=headers, params=params, json=data, timeout=API_TIMEOUT_SECONDS)
        raw_response.raise_for_status()
        response_json = raw_response.json()
        if 'candidates' in response_json and response_json['candidates']:
            candidate = response_json['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                 response_text = candidate['content']['parts'][0]['text']
            elif 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
                logging.warning(f"API call blocked due to safety settings for model {model}.")
                exception = ValueError("Blocked due to safety settings")
            else:
                 exception = ValueError("LLM response structure error: Missing content or parts.")
        else:
             exception = ValueError("LLM response structure error: Missing candidates or content.")
    except Timeout as e:
        exception = e
        logging.warning(f"API request timed out for model {model}")
    except RequestException as e:
        exception = e
        logging.warning(f"API request failed for model {model} with status {raw_response.status_code if raw_response else 'N/A'}: {str(e)}")
        if raw_response is not None: logging.debug(f"Failed response content: {raw_response.text[:500]}")
    except (json.JSONDecodeError, ValueError) as e:
         exception = e
         logging.warning(f"API response parsing or structure error for model {model}: {str(e)}")
         if raw_response is not None: logging.debug(f"Problematic response content: {raw_response.text[:500]}")
    return response_text, exception, raw_response

def parse_llm_output(raw_text_output: str, event_name: str) -> Dict[str, str]:
    article_title = f"Article on {event_name}" 
    article_text_raw = raw_text_output.strip()
    lines = article_text_raw.split('\n')
    if lines:
        first_line = lines[0].strip()
        if first_line.startswith('# '):
            article_title = first_line[2:].strip()
    if not article_text_raw:
        logging.warning(f"LLM output for '{event_name}' is empty.")
    return {"article_title": article_title, "article_text_raw": article_text_raw}

def translate_text(text_to_translate: str, target_lang: str, api_key: str, model_for_translation: str) -> Optional[str]:
    if not text_to_translate.strip():
        logging.warning(f"translate_text: Input text for {target_lang} is empty, skipping translation.")
        return None
    if target_lang not in TRANSLATION_PROMPTS:
        logging.warning(f"No translation prompt defined for language: {target_lang}. Skipping translation.")
        return None
        
    prompt = f"{TRANSLATION_PROMPTS[target_lang]}\n\n---\n\n{text_to_translate}"
    logging.debug(f"Translation prompt for {target_lang} starts with: {prompt[:200]}...")

    translated_text, exception, raw_response = call_gemini_api(api_key, model_for_translation, prompt)
    
    if exception:
        logging.error(f"Error during translation API call to {target_lang} for text starting with '{text_to_translate[:50]}...': {exception}")
        if raw_response: logging.error(f"Translation API response status: {raw_response.status_code}, content: {raw_response.text[:500]}")
        return None
    if translated_text:
        return translated_text.strip()
    else:
        logging.warning(f"Translation to {target_lang} for text starting with '{text_to_translate[:50]}...' returned empty text.")
        if raw_response: logging.debug(f"Empty translation response content: {raw_response.text[:500]}")
        return None

def get_relative_output_path(input_file_path: str, input_dir: str, output_dir: str) -> str:
    """Get the output path maintaining the input folder structure relative to input_dir"""
    # Get the relative path from input_dir to the input file
    relative_path = os.path.relpath(input_file_path, input_dir)
    # Remove the filename to get just the directory structure
    relative_dir = os.path.dirname(relative_path)
    # Join with output_dir to create the mirror structure
    return os.path.join(output_dir, relative_dir)

# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================
def process_event(input_file_path: str, event_name: str, relevant_sources: List[Dict],
                 active_key_index: int, output_dir: str, input_dir: str) -> Tuple[Optional[Dict], int]:
    if not relevant_sources:
        logging.warning(f"No relevant sources for event: {event_name}")
        return {"processing_status": "skipped_no_sources", "error_message": "No relevant sources"}, active_key_index

    consolidated_source_data, source_references_ordered = build_consolidated_prompt_and_refs(relevant_sources)
    prompt = LLM_STAGE2_PROMPT_TEMPLATE.format(event_name=event_name, consolidated_source_data=consolidated_source_data)
    logging.info(f"Estimated tokens for prompt for '{event_name}': {estimate_tokens(prompt)}")

    keys_tried, max_keys = 0, len(API_KEYS_MODELS)
    initial_llm_raw_text: Optional[str] = None
    
    current_api_key, current_model = "", "" # For use in translation calls

    while keys_tried < max_keys:
        key_config = API_KEYS_MODELS[active_key_index]
        current_api_key, current_model = key_config["key"], key_config["model"]
        logging.info(f"Using API key {active_key_index + 1}/{max_keys} (model {current_model}) for event '{event_name}' (Initial Synthesis)")

        for attempt in range(MAX_RETRIES_PER_KEY):
            logging.info(f"Initial synthesis attempt {attempt + 1}/{MAX_RETRIES_PER_KEY} for '{event_name}'")
            initial_llm_raw_text, exception, raw_response = call_gemini_api(current_api_key, current_model, prompt)

            if initial_llm_raw_text is not None and raw_response and raw_response.status_code == 200:
                if not initial_llm_raw_text.strip():
                    logging.warning(f"LLM returned empty article text for '{event_name}' on attempt {attempt + 1}. Retrying if possible.")
                    initial_llm_raw_text = None # Force retry
                else:
                    logging.info(f"Successfully received initial (English) text from LLM for '{event_name}'.")
                    break # Success for initial synthesis
            
            error_handled_for_retry = False
            if raw_response:
                if is_invalid_key_error(raw_response) or is_rate_limit_error(raw_response):
                    logging.warning(f"API key/rate limit issue for '{event_name}'. Switching key.")
                    initial_llm_raw_text = None # Ensure outer loop continues if this was the last attempt for key
                    break 
                if is_input_token_limit_error(raw_response):
                    logging.error(f"Input token limit exceeded for '{event_name}'. Cannot process.")
                    return {"processing_status": "failed_token_limit", "error_message": "Input token limit"}, active_key_index
                if is_overload_error(raw_response) and attempt < MAX_RETRIES_PER_KEY - 1:
                    logging.warning(f"Server overload for '{event_name}'. Retrying after {ERROR_DELAY_SECONDS}s...")
                    time.sleep(ERROR_DELAY_SECONDS)
                    error_handled_for_retry = True
                    continue
            if attempt < MAX_RETRIES_PER_KEY - 1 and not error_handled_for_retry:
                logging.warning(f"API call/parsing failed for '{event_name}'. Retrying after {ERROR_DELAY_SECONDS}s... (Exception: {exception})")
                time.sleep(ERROR_DELAY_SECONDS)
            elif not error_handled_for_retry:
                 logging.error(f"All retries failed for current key for '{event_name}'. (Exception: {exception})")
        
        if initial_llm_raw_text: break # Got initial text, move to processing and translation
        
        keys_tried += 1
        active_key_index = (active_key_index + 1) % max_keys
        if keys_tried < max_keys:
            logging.info(f"Switching to next API key for initial synthesis (index {active_key_index}). Delaying {KEY_SWITCH_DELAY_SECONDS}s...")
            time.sleep(KEY_SWITCH_DELAY_SECONDS)

    if not initial_llm_raw_text:
        logging.error(f"Failed to synthesize initial article for '{event_name}' with all API keys.")
        return {"processing_status": "failed_all_keys", "error_message": "Initial synthesis failed with all keys"}, active_key_index

    # --- Process and Save English Version ---
    parsed_english_output = parse_llm_output(initial_llm_raw_text, event_name)
    output_files_saved = []
    safe_event_name = "".join(c if c.isalnum() else "_" for c in event_name)

    english_data = {
        "event_name": event_name,
        "article_title": parsed_english_output["article_title"],
        "article_text_raw": parsed_english_output["article_text_raw"],
        "source_references_ordered": source_references_ordered
    }
    
    # Create mirror directory structure in output
    relative_output_path = get_relative_output_path(input_file_path, input_dir, output_dir)
    os.makedirs(relative_output_path, exist_ok=True)
    
    en_filename = f"{safe_event_name}_stage2_output_en.json"
    en_filepath = os.path.join(relative_output_path, en_filename)
    try:
        with open(en_filepath, 'w', encoding='utf-8') as f: json.dump(english_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Saved English version: {en_filepath}")
        output_files_saved.append(en_filepath)
    except IOError as e:
        logging.error(f"Failed to save English version {en_filepath}: {e}")

    # --- Translations ---
    for lang_code in TARGET_LANGUAGES_FOR_TRANSLATION:
        logging.info(f"Translating article for '{event_name}' to {lang_code.upper()}.")
        # Use the English raw text (which includes its own H1 title) for translation.
        translated_full_article_text = translate_text(
            parsed_english_output["article_text_raw"], 
            lang_code, 
            current_api_key, # Use the key that worked for initial synthesis for translations
            current_model    # Use the model that worked for initial synthesis
        )
        if translated_full_article_text:
            parsed_translated_output = parse_llm_output(translated_full_article_text, event_name) # event_name as fallback
            translated_data = {
                "event_name": event_name,
                "article_title": parsed_translated_output["article_title"], # Correctly parsed title
                "article_text_raw": parsed_translated_output["article_text_raw"], # Full translated text
                "source_references_ordered": source_references_ordered
            }
            lang_filename = f"{safe_event_name}_stage2_output_{lang_code}.json"
            lang_filepath = os.path.join(relative_output_path, lang_filename)
            try:
                with open(lang_filepath, 'w', encoding='utf-8') as f: json.dump(translated_data, f, ensure_ascii=False, indent=2)
                logging.info(f"Saved {lang_code.upper()} version: {lang_filepath}")
                output_files_saved.append(lang_filepath)
            except IOError as e:
                logging.error(f"Failed to save {lang_code.upper()} version {lang_filepath}: {e}")
        else:
            logging.warning(f"Translation to {lang_code.upper()} for '{event_name}' failed or returned empty.")

    if output_files_saved:
        return {"processing_status": "success", "output_files": output_files_saved}, active_key_index
    else: # Only if even English failed to save (though initial LLM call was successful)
        return {"processing_status": "failed_save", "error_message": "LLM call successful but failed to save any article version"}, active_key_index


def process_files(input_dir: str, output_dir: str) -> None:
    if not API_KEYS_MODELS:
        logging.critical("No API keys. Cannot proceed.")
        return

    processed_events_set, active_key_index = load_state()
    input_files = [os.path.join(root, file) for root, _, files in os.walk(input_dir) for file in files if file.endswith('.json')]
    logging.info(f"Found {len(input_files)} files from {input_dir}")
    stats = {'total_files': len(input_files), 'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}

    for input_file_path in input_files:
        stats['processed'] += 1
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f: input_data = json.load(f)
            event_name = input_data.get('event', '')
            if not event_name:
                logging.warning(f"No event name in {input_file_path}. Skipping.")
                stats['skipped'] += 1
                continue

            event_processing_id = get_event_id(event_name, input_file_path)
            if event_processing_id in processed_events_set:
                logging.info(f"Event ID '{event_processing_id}' already processed. Skipping.")
                stats['skipped'] += 1
                continue

            relevant_sources = []
            stage1_results = input_data.get('stage1_processed_results', {})
            sources_to_check = stage1_results.get('en', []) if isinstance(stage1_results, dict) else stage1_results if isinstance(stage1_results, list) else []
            
            # If sources_to_check is not a list (e.g. it's a dict of lists from stage1 by language)
            # you might need to iterate through its values if 'en' is not always present or is nested differently.
            # For simplicity, assuming 'en' list or direct list of sources:
            temp_sources_list = []
            if isinstance(stage1_results, dict): # If it's a dict like {'en': [...], 'fr': [...]}
                 for lang_key, lang_sources_list in stage1_results.items():
                    if isinstance(lang_sources_list, list):
                        temp_sources_list.extend(lang_sources_list)
            elif isinstance(stage1_results, list): # If it's already a list of sources
                temp_sources_list = stage1_results


            for i, source in enumerate(temp_sources_list):
                if source and isinstance(source, dict) and source.get('processing_status') == 'success' and \
                isinstance(source.get('llm_processed_output'), dict) and \
                source['llm_processed_output'].get('relevance_status') == 'relevant':
                    # Get the URL from original_source_metadata if available
                    source_url = source.get('original_source_metadata', {}).get('source_url', 
                            source.get('source_url', source.get('source_uid', f'unknown_uid_{input_file_path}_{i}')))
                    
                    relevant_sources.append({
                        'source_uid': source.get('source_uid', f'unknown_uid_{input_file_path}_{i}'),
                        'source_url': source_url,  # Use the extracted URL here
                        'source_summary': source['llm_processed_output'].get('source_summary', ''),
                        'extracted_key_facts': source['llm_processed_output'].get('extracted_key_facts', [])
                    })
            
            if not relevant_sources:
                logging.warning(f"No relevant sources for '{event_name}' in {input_file_path}. Skipping.")
                stats['skipped'] += 1
                processed_events_set.add(event_processing_id) # Add to skip in future
                save_state(processed_events_set, active_key_index)
                continue

            logging.info(f"Processing event '{event_name}' from {input_file_path} with {len(relevant_sources)} sources.")
            result, active_key_index = process_event(input_file_path, event_name, relevant_sources, active_key_index, output_dir, input_dir)

            if result and result.get('processing_status') == 'success':
                stats['successful'] += 1
                processed_events_set.add(event_processing_id)
            elif result and result.get('processing_status') == 'failed_token_limit':
                stats['failed'] += 1
                processed_events_set.add(event_processing_id) # Mark as processed to avoid retries
            elif result and result.get('processing_status') != 'skipped_no_sources':
                stats['failed'] += 1
            
            save_state(processed_events_set, active_key_index)
            time.sleep(API_CALL_DELAY_SECONDS)
        except Exception as e:
            logging.error(f"Unhandled error for file {input_file_path}: {e}", exc_info=True)
            stats['failed'] += 1
            save_state(processed_events_set, active_key_index) # Save state on unhandled error

    logging.info(f"Processing Summary: Total Files={stats['total_files']}, Processed Attempts={stats['processed']}, Successful Events={stats['successful']}, Failed={stats['failed']}, Skipped={stats['skipped']}")

# ============================================================================
# MAIN FUNCTION
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description='Stage 2: Synthesize articles and translate from Stage 1 outputs.')
    parser.add_argument('--input_dir', type=str, required=False, help='Directory of Stage 1 JSON outputs.')
    parser.add_argument('--output_dir', type=str, required=False, help='Directory to save Stage 2 JSON articles.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers: handler.setLevel(logging.DEBUG)

    input_dir = args.input_dir or input("Enter path to Stage 1 output directory: ")
    output_dir = args.output_dir or input("Enter path to Stage 2 output directory: ")
    input_dir, output_dir = os.path.abspath(input_dir), os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Input directory: {input_dir}")
    logging.info(f"Output directory: {output_dir}")

    try:
        process_files(input_dir, output_dir)
    except KeyboardInterrupt:
        logging.info("Processing interrupted by user. State is saved incrementally.")
    except Exception as e:
        logging.critical(f"Critical error during script execution: {e}", exc_info=True)
        logging.info("Attempting to save state due to critical error. State may be from last successful operation.")

if __name__ == "__main__":
    main()