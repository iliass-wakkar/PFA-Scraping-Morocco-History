import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_PATH = PROJECT_ROOT / "src" / "Data" / "filtered_results_Content-v1.json"
OUTPUT_PATH = PROJECT_ROOT / "src" / "Data" / "Content" / "filtered_clean_content.json"

# Arabic Unicode ranges (includes letters, numbers, and punctuation)
ARABIC_PATTERN = re.compile(
    r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
)

def is_google_books(link):
    """Check if the link is from Google Books"""
    try:
        parsed = urlparse(link)
        return 'books.google.com' in parsed.netloc
    except:
        return False

def is_entry_empty(entry):
    """Check if entry has no usable content"""
    # Check main content
    content_empty = True
    if entry.get('content'):
        if entry['content'].get('main_title'):
            content_empty = False
        elif entry['content'].get('sections'):
            if any(section.get('paragraph') for section in entry['content']['sections']):
                content_empty = False
    
    # Check PDF content
    pdf_empty = True
    if entry.get('pdf_content'):
        for pdf in entry['pdf_content']:
            # Handle case where pdf might be a string instead of dict
            if isinstance(pdf, str):
                if pdf.strip():  # If pdf string is not empty
                    pdf_empty = False
                    break
            elif isinstance(pdf, dict):
                if pdf.get('main_title') or pdf.get('full_text'):
                    pdf_empty = False
                    break
                if pdf.get('sections'):
                    if any(s.get('content') for s in pdf['sections']):
                        pdf_empty = False
                        break
    
    return content_empty and pdf_empty

def get_text_from_content(content):
    """Extract all text from content structure"""
    text = []
    if isinstance(content, dict):
        text.append(content.get('main_title', ''))
        for section in content.get('sections', []):
            text.append(section.get('sub_title', ''))
            text.append(section.get('paragraph', ''))
    return ' '.join(text)

def calculate_arabic_ratio(text):
    """Calculate percentage of Arabic characters in text"""
    if not text:
        return 0.0
    
    # Remove whitespace and punctuation
    clean_text = re.sub(r'\s+', '', text)
    if len(clean_text) < 10:  # Minimum meaningful text length
        return 0.0
    
    arabic_chars = ARABIC_PATTERN.findall(clean_text)
    return len(arabic_chars) / len(clean_text)

def has_arabic_content(entry):
    """Check if entry contains sufficient Arabic content"""
    # Combine all text sources
    all_text = []
    
    # Web content
    if entry.get('content'):
        all_text.append(get_text_from_content(entry['content']))
    
    # PDF content
    if entry.get('pdf_content'):
        for pdf in entry['pdf_content']:
            # Handle case where pdf might be a string instead of dict
            if isinstance(pdf, str):
                all_text.append(pdf)
            elif isinstance(pdf, dict):
                all_text.append(pdf.get('main_title', ''))
                all_text.append(pdf.get('full_text', ''))
                if pdf.get('sections'):
                    for section in pdf['sections']:
                        all_text.append(section.get('sub_title', ''))
                        all_text.append(section.get('content', ''))
    
    combined_text = ' '.join(filter(None, all_text))  # Filter out None values
    return calculate_arabic_ratio(combined_text) >= 0.5

def has_arabic_description(entry):
    """Check if entry's description contains sufficient Arabic content"""
    description = entry.get('description', '')
    return calculate_arabic_ratio(description) >= 0.5

def filter_data(input_data):
    """Main filtering pipeline with comprehensive checks"""
    filtered_data = []
    
    stats = {
        'total_entries': len(input_data),
        'removed_google_books': 0,
        'removed_errors': 0,
        'removed_empty_content': 0,
        'removed_non_arabic': 0,
        'removed_non_arabic_description': 0,
        'kept_entries': 0
    }
    
    for i, entry in enumerate(input_data):
        # Print progress occasionally
        if i % 50 == 0:
            print(f"Processing entry {i+1}/{len(input_data)}...")
            
        # Remove Google Books entries
        if is_google_books(entry.get('link', '')):
            stats['removed_google_books'] += 1
            continue
            
        # Remove entries with errors
        if entry.get('error'):
            stats['removed_errors'] += 1
            continue
            
        # Remove empty content entries
        if is_entry_empty(entry):
            stats['removed_empty_content'] += 1
            continue
            
        # Remove entries with non-Arabic descriptions
        if not has_arabic_description(entry):
            stats['removed_non_arabic_description'] += 1
            continue
            
        # Remove non-Arabic content
        if not has_arabic_content(entry):
            stats['removed_non_arabic'] += 1
            continue
            
        filtered_data.append(entry)
    
    stats['kept_entries'] = len(filtered_data)
    stats['total_removed'] = sum(v for k,v in stats.items() if k.startswith('removed'))
    
    return filtered_data, stats

def main():
    try:
        # Load data
        print(f"Loading data from {INPUT_PATH}...")
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        print(f"Loaded {len(input_data)} entries. Starting filtering...")
        
        # Filter data
        filtered_data, stats = filter_data(input_data)
        
        # Save results
        print(f"Saving {len(filtered_data)} filtered entries...")
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        print(f"📊 Filtering Results:")
        print(f"➖ Total entries processed: {stats['total_entries']}")
        print(f"✅ Kept entries: {stats['kept_entries']}")
        print(f"🚮 Total removed: {stats['total_removed']}")
        print("\nRemoval Details:")
        print(f"  📚 Google Books: {stats['removed_google_books']}")
        print(f"  ❌ Errors: {stats['removed_errors']}")
        print(f"  📭 Empty content: {stats['removed_empty_content']}")
        print(f"  🌍 Non-Arabic content: {stats['removed_non_arabic']}")
        print(f"  📝 Non-Arabic description: {stats['removed_non_arabic_description']}")
        print(f"\n💾 Clean data saved to: {OUTPUT_PATH}")
        
    except FileNotFoundError:
        print(f"❌ Error: Input file not found at {INPUT_PATH}")
        print(f"🔍 Check if file exists: {INPUT_PATH.absolute()}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full traceback for debugging

if __name__ == "__main__":
    main()