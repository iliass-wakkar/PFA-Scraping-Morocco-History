import json
import re
from pathlib import Path

def clean_brackets(text):
    """Remove ALL content within square brackets AND unwanted Unicode control characters."""
    if not text:
        return ""

    # Step 1: Remove standard bracket content
    cleaned = re.sub(r'\[[^\]]*\]', '', str(text))

    # Step 2: Specifically target [U+XXXX] patterns
    cleaned = re.sub(r'\[U\+[0-9A-F]{4,6}\]', '', cleaned)

    # Step 3: Remove standalone Unicode control characters
    cleaned = re.sub(r'[\u200E\u200F\u202A-\u202E]', '', cleaned)

    # Step 4: Strip extra whitespace
    return cleaned.strip()

def is_arabic_dominant(text):
    """Check if Arabic characters dominate (>50% of non-space characters)"""
    if not text:
        return False
    
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total_chars = len(text.replace(" ", ""))
    
    return (arabic_chars / total_chars) > 0.5 if total_chars > 0 else False

def validate_entry(entry):
    """Check if entry has valid link and source"""
    has_link = bool(entry.get("link")) and str(entry["link"]).strip() not in ["", "null", "None"]
    has_source = bool(entry.get("source")) and str(entry["source"]).strip() not in ["", "null", "None"]
    return has_link and has_source

def second_filter(entries):
    filtered = []
    for entry in entries:
        # Skip entries without links or sources
        if not validate_entry(entry):
            continue
            
        # Clean all fields
        entry["title"] = clean_brackets(entry.get("title", ""))
        entry["source"] = clean_brackets(entry.get("source", ""))
        entry["description"] = clean_brackets(entry.get("description", ""))
        
        # Check Arabic dominance
        if is_arabic_dominant(entry["title"]) or is_arabic_dominant(entry["description"]):
            filtered.append(entry)
    return filtered

# Path configuration
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_path = project_root / "src" / "Data" / "filter1_morocco_history_research_.json"
output_path = project_root / "src" / "Data" / "filter2_morocco_history_research_.json"

# Load and process data
with open(input_path, "r", encoding="utf-8") as f:
    filtered1_data = json.load(f)

filtered2_data = second_filter(filtered1_data)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered2_data, f, ensure_ascii=False, indent=2)

# Print detailed removal stats
removed_count = len(filtered1_data) - len(filtered2_data)
invalid_entries = len([e for e in filtered1_data if not validate_entry(e)])
arabic_removed = removed_count - invalid_entries

print(f"Initial entries: {len(filtered1_data)}")
print(f"Final entries: {len(filtered2_data)}")
print(f"Removed entries: {removed_count}")
print(f"  - Missing link/source: {invalid_entries}")
print(f"  - Non-Arabic content: {arabic_removed}")