import json
import os
from pathlib import Path
from urllib.parse import urlparse

def is_morocco_related(entry):
    """Check if entry contains Morocco-related keywords (supports merged words)"""
    morocco_keywords = [
        'المغرب', 'المغربي', 'المغربية', 'المغاربة',
        'المغرب العربي', 'المغرب الأقصى', 'المملكة المغربية',
        'المغرب الكبير', 'المغرب التاريخي', 'الصحراء المغربية',
        'المغرب الحديث', 'المغرب العريق'
    ]
    
    # Merge title + description without spaces for substring checks
    text = f"{entry.get('title', '')}{entry.get('description', '')}".lower()
    return any(keyword in text for keyword in morocco_keywords)

def is_valid_domain(link):
    """Exclude .dz domains"""
    try:
        domain = urlparse(link).netloc
        return not domain.endswith('.dz')
    except:
        return False

def clean_data(input_json):
    """Main cleaning pipeline with statistics"""
    seen = set()
    cleaned_data = []
    
    removal_stats = {
        'missing_link': 0,
        'non_moroccan': 0,
        'invalid_domain': 0,
        'duplicates': 0
    }

    for entry in input_json:
        # Missing link check
        if not entry.get('link'):
            removal_stats['missing_link'] += 1
            continue
            
        # Morocco content filter
        if not is_morocco_related(entry):
            removal_stats['non_moroccan'] += 1
            continue
            
        # Domain validation
        if not is_valid_domain(entry['link']):
            removal_stats['invalid_domain'] += 1
            continue
            
        # Duplicate check
        identifier = (
            entry.get('title', '').strip().lower(),
            entry['link'].strip().lower()
        )
        if identifier in seen:
            removal_stats['duplicates'] += 1
            continue
            
        seen.add(identifier)
        cleaned_data.append(entry)
            
    return cleaned_data, removal_stats

# Path configuration
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_path = project_root / "src" / "Data" / "morocco_history_research.json"
output_path = project_root / "src" / "Data" / "filter1_morocco_history_research_.json"

try:
    with open(input_path, "r", encoding="utf-8") as f:
        original_data = json.load(f)
        
    cleaned_data, stats = clean_data(original_data)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
    # Display results
    print(f"Original entries: {len(original_data)}")
    print(f"Cleaned entries: {len(cleaned_data)}")
    print("\nRemoval Statistics:")
    print(f"- Missing 'link' field: {stats['missing_link']}")
    print(f"- Non-Moroccan content: {stats['non_moroccan']}")
    print(f"- .dz domains excluded: {stats['invalid_domain']}")
    print(f"- Duplicates removed: {stats['duplicates']}")
    print(f"\nTotal removed: {sum(stats.values())}")

except FileNotFoundError:
    print(f"Error: File not found at {input_path}")
    print(f"Absolute path: {os.path.abspath(input_path)}")