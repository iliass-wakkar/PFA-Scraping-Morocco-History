import json
import re
import os
from datetime import datetime

def filter_scholar_results(input_file, output_file):
    """Optimized filter that appends to existing output file"""
    
    # Convert to absolute paths
    input_path = os.path.abspath(input_file)
    output_path = os.path.abspath(output_file)
    
    print(f"\n🔍 Starting filtering: {input_path} → {output_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ Input file not found: {input_path}")

    # Enhanced keyword list for Moroccan history
    KEYWORDS = [
        # Conflict terms
        'حرب', 'معركة', 'صراع', 'نزاع', 'ثورة', 'مقاومة', 'احتلال',
        'استعمار', 'تحرير', 'جهاد', 'انتفاضة', 'تمرد', 'انقلاب',
        
        # Specific Moroccan references
        'حرب الريف', 'ثورة الملك والشعب', 'جيش التحرير', 'الظهير البربري',
        'المقاومة المغربية', 'الحركة الوطنية', 'الكفاح المسلح',
    ]

    # Load input data
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"📊 Loaded {len(results)} records from input")
    except Exception as e:
        raise Exception(f"❌ Failed to load input file: {str(e)}")

    # Load existing output data if file exists
    existing_data = []
    existing_links = set()
    
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_links = {item['link'].split('?')[0].split('#')[0].strip().lower() 
                            for item in existing_data if 'link' in item}
            print(f"📋 Found {len(existing_data)} existing records in output file")
        except Exception as e:
            print(f"⚠️ Could not load existing output file: {str(e)}")

    filtered = []
    removal_stats = {
        'no_source': 0,
        'missing_fields': 0,
        'duplicates_in_input': 0,
        'duplicates_in_output': 0,
        'short_title': 0,
        'no_keywords': 0,
        'low_quality': 0
    }

    seen_input_links = set()

    for item in results:
        try:
            # Validate required fields
            if not item.get('source') or not item['source'].strip():
                removal_stats['no_source'] += 1
                continue
                
            if not all(item.get(field) for field in ['title', 'link']):
                removal_stats['missing_fields'] += 1
                continue

            # Clean and check link
            clean_link = re.sub(r'[?#].*', '', item['link'].strip().lower())
            
            # Check against existing output
            if clean_link in existing_links:
                removal_stats['duplicates_in_output'] += 1
                continue
                
            # Check against current input
            if clean_link in seen_input_links:
                removal_stats['duplicates_in_input'] += 1
                continue
            seen_input_links.add(clean_link)

            # Prepare text
            title = item['title'].strip()
            desc = item.get('description', '').strip()
            text = f"{title} {desc} {item['source']}".lower()

            # Check Arabic content
            if len(re.sub(r'[^\u0600-\u06FF]', '', title)) < 20:
                removal_stats['short_title'] += 1
                continue

            # Keyword matching
            matches = [kw for kw in KEYWORDS if re.search(rf'\b{re.escape(kw)}\b', text)]
            if not matches:
                removal_stats['no_keywords'] += 1
                continue

            # Quality checks
            if ('books.google.com' in clean_link and not desc) or \
               any(bad in item['source'].lower() for bad in ['slideshare', 'scribd']):
                removal_stats['low_quality'] += 1
                continue

            # Calculate score
            score = sum([
                min(2, len(matches)),  # Multiple keywords
                1 if len(desc) > 100 else 0,
                1 if any(edu in item['source'].lower() for edu in ['edu', 'academic', 'جامعة']) else 0
            ])

            # Add to results
            filtered.append({
                'title': title,
                'link': item['link'].strip(),
                'source': item['source'].strip(),
                'description': desc or None,
                'keywords': matches,
                'score': score,
                'scraped_at': item.get('scraped_at') or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'page': item.get('page')
            })

        except Exception as e:
            print(f"⚠️ Error processing item: {str(e)}")
            continue

    # Combine with existing data and sort
    combined_data = existing_data + filtered
    combined_data.sort(key=lambda x: x['score'], reverse=True)
    
    # Save results
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise Exception(f"❌ Failed to save results: {str(e)}")

    # Generate report
    print(f"\n✅ Added: {len(filtered)} new records")
    print(f"📂 Total records now: {len(combined_data)}")
    print("❌ Removals:")
    for reason, count in removal_stats.items():
        print(f"- {reason.replace('_', ' ').title()}: {count}")
    
    if filtered:
        print("\n🏆 New Top Matches:")
        for item in filtered[:3]:
            print(f"- {item['title'][:60]}... (Score: {item['score']})")

# Direct paths - relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, '../Data/morocco_history_research.json')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, '../Data/filtered_morocco_conflict_studies.json')

filter_scholar_results(INPUT_FILE, OUTPUT_FILE)