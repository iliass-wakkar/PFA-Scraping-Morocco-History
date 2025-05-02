import json
import os
import re

FORBIDDEN_KEYWORDS = {
    'access', 'buy', 'purchase', 'copyright', 'proquest',
    'subscribe', 'membership', 'full text', 'complete full text',
    'denied', 'restricted', 'login', 'sign in', 'register'
}

def clean_text(text):
    """Clean text by removing special patterns and fixing newlines"""
    if not isinstance(text, str):
        return text
    
    # Replace escaped newlines with actual newlines
    text = text.replace('\\n', '\n')
    
    # Remove (cid:XX) patterns
    text = re.sub(r'\(cid:\d+\)', '', text)
    
    # Remove other common problematic patterns
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # Remove control chars
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    
    return text

def clean_sections(entry):
    """Remove empty sections and clean text"""
    if 'sections' not in entry:
        return entry
        
    cleaned_sections = []
    for section in entry['sections']:
        subtitle = clean_text(section.get('subtitle', ''))
        paragraph = clean_text(section.get('paragraph', ''))
        
        if subtitle and paragraph:
            cleaned_sections.append({
                'subtitle': subtitle,
                'paragraph': paragraph
            })
    
    entry['sections'] = cleaned_sections
    return entry

def contains_forbidden_content(text):
    """Check for restricted content keywords"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FORBIDDEN_KEYWORDS)

def is_valid_entry(entry):
    """Validate entry meets all requirements"""
    if not entry.get('title'):
        return False
    
    # Check PDF content
    if entry.get('pdf') and entry['pdf'].get('full_text'):
        clean_pdf_text = clean_text(entry['pdf']['full_text'])
        if len(clean_pdf_text.split()) >= 50:
            entry['pdf']['full_text'] = clean_pdf_text
            return True
    
    # Check sections content
    for section in entry.get('sections', []):
        combined_text = f"{section['subtitle']} {section['paragraph']}"
        if len(combined_text.split()) >= 50:
            return True
    
    return False

def filter_json(input_file, output_file):
    """Main processing function"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = []
    for entry in data:
        # Clean entry data
        entry['title'] = clean_text(entry.get('title', ''))
        entry['summary'] = clean_text(entry.get('summary', ''))
        
        entry = clean_sections(entry)
        sections = entry.get('sections', [])
        
        # Skip if contains forbidden content
        if any(contains_forbidden_content(f"{s['subtitle']} {s['paragraph']}") for s in sections):
            continue
            
        # Skip single-section entries
        if len(sections) == 1:
            continue
            
        if is_valid_entry(entry):
            processed_data.append(entry)
    
    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"Processed {len(data)} entries")
    print(f"Saved {len(processed_data)} valid entries")
    print(f"Removed {len(data) - len(processed_data)} entries")

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "Data", "Part1_islam", "إعادة الفتح البيزنطي (533-550 م)2" , "Byzantine reconquest (533–550 CE).json"))
    OUTPUT_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "Data", "Part1_islam", "إعادة الفتح البيزنطي (533-550 م)2" , "Byzantine reconquest (533–550 CE)2.json"))

    filter_json(INPUT_FILE, OUTPUT_FILE)