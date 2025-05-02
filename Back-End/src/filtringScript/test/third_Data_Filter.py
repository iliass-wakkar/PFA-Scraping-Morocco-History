import json
import re
from pathlib import Path
from pymongo import MongoClient

# Step 1: Define all keywords
KEYWORDS = {
    # 🔥 General Conflict & War Terms
    'حرب', 'معركة', 'معارك', 'صراع', 'صراعات', 'نزاع', 'نزاعات',
    'ثورة', 'ثورات', 'مقاومة', 'احتلال', 'مستعمر', 'استعمار', 'تحرير',
    'جهاد', 'انتفاضة', 'تمرد', 'انقلاب', 'عصيان', 'اشتباك', 'صدام',
    'حصار', 'قتال', 'سلاح', 'مجزرة', 'دمار', 'اجتياح', 'هجوم', 'تفجير',
    'غزو', 'دم', 'شهداء', 'ضحايا',
    
    # 🏰 Historical Entities & Dynasties
    'المرابطين', 'الموحدين', 'المرينيين', 'الوطاسيين', 'السعديين',
    'العلويين', 'الأدارسة', 'الزيانيين', 'الجزائريين',
    
    # 🗺️ Colonial & Resistance Context 
    'الاحتلال الفرنسي', 'الاحتلال الإسباني', 'الحماية الفرنسية',
    'الاستعمار', 'الاستقلال', 'التحرر', 'حركة وطنية', 'جيش التحرير',
    'الكفاح المسلح', 'المقاومة الشعبية', 'ثورة الملك والشعب', 'الظهير البربري',
    'المنفى', 'المناضلين',
    
    # 🌍 Modern Conflicts & Regions
    'الصحراء المغربية', 'الصحراء الغربية', 'نزاع الصحراء', 'البوليساريو',
    'الجزائر', 'المناوشات الحدودية', 'مينورسو', 'الكركرات', 'الجدار الأمني',
    'الأقاليم الجنوبية',
    
    # 🧠 Other Helpful Keywords
    'شهداء', 'مستعمرات', 'الاستقلال', 'حرب العصابات', 'التوتر السياسي',
    'الانتفاضات', 'الطرد الجماعي', 'مطالبة', 'حقوق', 'تقرير المصير',
    'السيادة الوطنية'
}

def clean_text(text):
    """Clean text for processing by removing punctuation and normalizing spaces"""
    # Remove punctuation and diacritics
    text = re.sub(r'[^\w\s]', '', str(text).strip())
    # Normalize Arabic characters (optional)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'[ة]', 'ه', text)
    text = re.sub(r'[ؤ]', 'ء', text)
    text = re.sub(r'[ئ]', 'ء', text)
    # Convert multiple spaces to single space
    return re.sub(r'\s+', ' ', text)

def count_words(text):
    """Count words in Arabic text"""
    return len(clean_text(text).split())

def contains_keywords(text):
    """Check if text contains any keywords as substrings"""
    cleaned = clean_text(text)
    return any(kw in cleaned for kw in KEYWORDS)

def calculate_relevance(title, description):
    """Calculate relevance score based on keyword substring matches"""
    cleaned_title = clean_text(title)
    cleaned_desc = clean_text(description)
    
    # Find all unique keywords present in either title or description
    title_matches = {kw for kw in KEYWORDS if kw in cleaned_title}
    desc_matches = {kw for kw in KEYWORDS if kw in cleaned_desc}
    
    return len(title_matches.union(desc_matches))

def apply_filters(entries, min_words=5, min_relevance=1):
    filtered = []
    for entry in entries:
        try:
            # Step 1: Title length check
            if count_words(entry.get('title', '')) < min_words:
                continue
                
            # Step 2: Keyword presence check
            title_has_keywords = contains_keywords(entry.get('title', ''))
            desc_has_keywords = contains_keywords(entry.get('description', ''))
            
            if not (title_has_keywords or desc_has_keywords):
                continue
                
            # Step 3: Calculate relevance score
            relevance = calculate_relevance(
                entry.get('title', ''),
                entry.get('description', '')
            )
            
            if relevance >= min_relevance:
                entry['relevance_score'] = relevance
                filtered.append(entry)
                
        except Exception as e:
            print(f"Error processing entry: {e}")
            continue
            
    return filtered

def save_to_mongodb(data):
    """Save filtered data to MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['Staging_data']
        collection = db['init_Data']
        
        # Clear existing data
        collection.delete_many({})
        
        # Insert new data
        if data:
            result = collection.insert_many(data)
            print(f"\nSuccessfully saved {len(result.inserted_ids)} documents to MongoDB")
        else:
            print("\nNo data to save to MongoDB")
            
        client.close()
    except Exception as e:
        print(f"\nError saving to MongoDB: {e}")

def main():
    # Path configuration
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    input_path = project_root / "src" / "Data" / "filter2_morocco_history_research_.json"
    output_path = project_root / "src" / "Data" / "filter3_morocco_history_research_.json"

    # Create Data directory if it doesn't exist
    (project_root / "src" / "Data").mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        print("Please ensure the file exists or check the path.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {input_path}")
        return

    # Apply filters
    filtered_data = apply_filters(data)

    # Save results to JSON file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Error saving output file: {e}")
        return

    # Save results to MongoDB
    save_to_mongodb(filtered_data)

    # Print statistics
    print(f"\n{'='*50}")
    print(f"{'Filtering Results':^50}")
    print(f"{'='*50}")
    print(f"Initial entries: {len(data)}")
    print(f"Filtered entries: {len(filtered_data)}")
    print(f"Retention rate: {len(filtered_data)/len(data)*100:.1f}%")
    
    if filtered_data:
        print(f"\nRelevance distribution:")
        scores = [e['relevance_score'] for e in filtered_data]
        print(f"- Average score: {sum(scores)/len(scores):.1f}")
        print(f"- Max score: {max(scores)}")
        print(f"- Min score: {min(scores)}")
        print(f"\nEntries by score:")
        for score in sorted(set(scores)):
            print(f"  {score}: {scores.count(score)} entries")
    
    print(f"\nJSON output saved to: {output_path}")

if __name__ == "__main__":
    main()