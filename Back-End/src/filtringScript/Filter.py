import json
import re
from pathlib import Path
import sys

# Comprehensive keyword list (same as provided)
KEYWORDS = [
    # Arabic Keywords
    "مواجهة", "فيينيقي", "أمازيغي", "غزو", "رومان", "موريتانيا", "وندال", "إعادة", "الفتح",
    "بيزنطي", "بداية", "الفتوحات", "العربية", "فتح", "أموي", "إسلامي", "مغرب", "ثورة", "أمازيغ",
    "تأسيسي", "إدريسي", "صراع", "فاطمي", "أموي", "مغراوة", "زناتة", "مرابطون", "صعود", "انحدار",
    "إمبراطورية", "غانا", "أندلس", "معركة", "زلاقة", "قشتالة", "موحدين", "ثورة", "توحيد",
    "حملات", "المرينيين", "غرناطة", "احتلال", "برتغالي", "سبتة", "طنجة", "أصيلة", "وادي", "مخازن",
    "قصر", "كبير", "سعديين", "غزو", "سنغاي", "توترات", "عثمانية", "سعدية", "حرب", "أهلية",
    "زعامة", "زاوية", "العلويين", "استيلاء", "قيادة", "رشيد", "توحيد", "الدولة", "حصار",
    "مدن", "إسبانية", "بريطانيا", "طرد", "تغلغل", "europäi", "صراعات", "سلالية", "تجدد",
    "مازاغان", "إنجليزي", "مغربي", "بربري", "ولايات", "متّحدة", "قبلية", "قرن", "تاسع", "عشر",
    "فرنسي", "إسباني", "تطوان", "أزمة", " الأولى", "الثانية", "أغادير", "معاهدة", "فاس",
    "مؤسسة", "للحماية", "مقاومة", "استعمارية", "حملات", "مبكرة", "ريف", "عبد", "الكريم",
    "خطابي", "أنوال", "هزيمة", "إسبانيا", "عمليات", "مشتركة", "ضد", "الريف", "حركات",
    "حضرية", "ظهير", "بربري", "حزب", "استقلال", "حملة", "وطنية", "نفي", "محمد", "خامس",
    "جيش", "تحرير", "صراعات", "ما", "بعد", "استقلال", "حدودية", "الجزائر", "حرب", "إفني",
    "رمال", "نزاعات", "ترسيم", "الحدود", "مسيرة", "خضراء", "الصحراء", "الغربية", "جبهة",
    "البوليساريو", "بناء", "الجدران", "الدفاعية", "عمليات", "ضد", "تمرد", "اتفاق", "وقف",
    "إطلاق", "نار", "مراقبة", "الأمم", "المتحدة", "خطة", "بيكر", "السلام", "توترات",
    "دورية", "معبر", "الكركرات", "عمل", "عسكري", "تأمين", "اعتراف", "الولايات", "المتحدة",
    "بالسيادة", "المغربية", "قطع", "العلاقات", "الدبلوماسية", "تعيين", "مبعوث", "أممي",
    "جديد", "دعم", "خطة", "الحكم", "الذاتي", "الإسرائيلي", "الفرنسي",

    # English Keywords
    "Confrontation", "Phoenician", "Berber", "Invasion", "Roman", "Mauretania", "Vandal",
    "Reconquest", "Byzantine", "Beginning", "Arab", "Conquests", "Islamic", "Morocco",
    "Revolt", "Founding", "Idrisid", "State", "Fatimid", "Umayyad", "Conflicts", "Maghrawa",
    "Zenata", "Almoravids", "Rise", "Empire", "Ghana", "Intervention", "Andalusia", "Battle",
    "Zallaqa", "Castile", "Almohads", "Revolt", "Unification", "Maghreb", "Decline", "Power",
    "Marinids", "Campaigns", "Tlemcen", "Interventions", "Granada", "Defeat", "Portuguese",
    "Occupation", "Ceuta", "Expansion", "Atlantic", "Coast", "Wattasids", "Takeover", "Asilah",
    "Saadians", "Sultanate", "Songhai", "Ottoman", "Civil", "War", "Dila'iyya", "Revolt",
    "Alawites", "Moulay", "al-Rachid", "Ismaïl", "Siege", "Spanish", "Cities", "Expulsion",
    "British", "European", "Penetration", "Dynastic", "Conflicts", "Renewed", "Melilla",
    "Mazagan", "Anglo-Moroccan", "Barbary", "Tribal", "19th", "Century", "Franco-Moroccan",
    "Isly", "Hispano-Moroccan", "Tétouan", "First", "Crisis", "Bombardment", "French",
    "Agadir", "Protectorate", "Colonial", "Resistance", "Early", "Rif", "Abdelkrim", "Khattabi",
    "Annual", "Joint", "Operations", "Urban", "Movements", "Berber", "Dahir", "Protest",
    "Formation", "Istiqlal", "Party", "Exile", "Mohammed", "V", "Liberation", "Army",
    "Post-Independence", "Border", "Tensions", "Algeria", "Ifni", "Sand", "Delimitation",
    "Green", "March", "Western", "Sahara", "Polisario", "Construction", "Defensive", "Walls",
    "Insurgencies", "Ceasefire", "UN", "Monitored", "Baker's", "Peace", "Plans", "Failure",
    "Periodic", "Guerguerat", "Crossing", "Military", "Action", "Recognition", "Sovereignty",
    "United", "States", "Skirmishes", "Algeria", "Severs", "Diplomatic", "Relations", "New",
    "UN", "Envoy", "Staffan", "de", "Mistura", "Spain", "Supports", "Autonomy", "Israel",
    "France",

    # French Keywords
    "Confrontation", "Phénicien", "Berbère", "Invasion", "Romaine", "Maurétanie", "Vandale",
    "Reconquête", "Byzantine", "Début", "Conquêtes", "Arabes", "Islamique", "Maroc", "Révolte",
    "Fondation", "État", "Idrisside", "Fatimides", "Omeyyades", "Conflits", "Maghrawa",
    "Zenata", "Almoravides", "Ascension", "Empire", "Ghana", "Intervention", "Andalousie",
    "Bataille", "Zallaqa", "Castille", "Almohades", "Révolte", "Unification", "Maghreb",
    "Déclin", "Puissance", "Mérinides", "Campagnes", "Tlemcen", "Interventions", "Grenade",
    "Défaite", "Occupation", "Portugaise", "Céuta", "Expansion", "Côte", "Atlantique",
    "Wattassides", "Prise", "Pouvoir", "Asilah", "Saadiens", "Empire", "Songhaï", "Ottomans",
    "Guerre", "Civile", "Révolte", "Zaouïa", "Alaouites", "Moulay", "al-Rachid", "Ismaïl",
    "Siège", "Villes", "Espagnoles", "Expulsion", "Britanniques", "Tanger", "Pénétration",
    "Européenne", "Conflits", "Dynastiques", "Renouvellement", "Melilla", "Mazagan",
    "Guerre", "Anglo-Marocaine", "Barbaresque", "Révoltes", "XIXème", "Siècle", "Franco-Marocaine",
    "Isly", "Hispano-Marocaine", "Tétouan", "Crise", "Bombardement", "Français", "Agadir",
    "Traité", "Fès", "Protectorat", "Résistance", "Coloniale", "Premières", "Campagnes",
    "Rif", "Abdelkrim", "Khattabi", "Anoual", "Opérations", "Conjointes", "Mouvements",
    "Révolte", "Dahir", "Parti", "Istiqlal", "Exil", "Mohammed", "V", "Armée", "Libération",
    "Post-Indépendance", "Tensions", "Frontalières", "Algérie", "Ifni", "Guerre", "Sables",
    "Conflits", "Délimitation", "Marche", "Verte", "Sahara", "Occidental", "Front", "Polisario",
    "Construction", "Murs", "Défensifs", "Opérations", "Insurrections", "Accord", "Cessez-le-feu",
    "ONU", "Surveillance", "Échec", "Plans", "Paix", "Baker", "Périodiques", "Guerguerat",
    "Action", "Militaire", "Reconnaissance", "Souveraineté", "États-Unis", "Entraînements",
    "Algérie", "Rompre", "Relations", "Diplomatiques", "Nouveau", "Envoyé", "Spécial", "ONU",
    "Espagne", "Soutient", "Plan", "Autonomie", "Israël", "France",

    # Spanish Keywords
    "Confrontación", "Fenicio", "Beréber", "Invasión", "Romana", "Mauritania", "Vándala",
    "Reconquista", "Bizantina", "Inicio", "Conquistas", "Árabes", "Islámica", "Marruecos",
    "Rebelión", "Fundación", "Estado", "Idrisí", "Fatimíes", "Omeos", "Conflictos", "Magrawa",
    "Zenata", "Almorávides", "Ascenso", "Imperio", "Ghana", "Intervención", "Al-Ándalus",
    "Batalla", "Zallaqa", "Castilla", "Almohades", "Rebelión", "Unificación", "Magreb",
    "Declive", "Poder", "Merínidas", "Campañas", "Tlemcén", "Intervenciones", "Granada",
    "Derrota", "Ocupación", "Portuguesa", "Ceuta", "Expansión", "Costa", "Atlántica",
    "Wattásidas", "Toma", "Poder", "Aşīlah", "Saadíes", "Imperio", "Songhai", "Otomanos",
    "Guerra", "Civil", "Rebelión", "Zawiya", "Alauitas", "Moulay", "al-Rashid", "Ismael",
    "Asedio", "Ciudades", "Españolas", "Expulsión", "Británicos", "Tánger", "Penetración",
    "Europea", "Conflictos", "Dinásticos", "Renovado", "Melilla", "Mazagán", "Guerrea",
    "Anglo-Marroquí", "Barbária", "Rebeliones", "Siglo", "XIX", "Franco-Marroquí", "Isly",
    "Hispano-Marroquí", "Tetuán", "Crisis", "Bombardeo", "Francés", "Agadir", "Tratado",
    "Fez", "Protectorado", "Resistencia", "Colonial", "Primeras", "Campañas", "Rif",
    "Abdelkrim", "El", "Khattabi", "Anual", "Operaciones", "Conjuntas", "Movimientos",
    "Rebelión", "Dahir", "Partido", "Istiqlal", "Exilio", "Mohammed", "V", "Ejército",
    "Liberación", "Post-Independencia", "Tensiones", "Fronterizas", "Argelia", "Ifni",
    "Guerra", "de", "las", "Arenas", "Disputas", "Demarcación", "Marcha", "Verde", "Sáhara",
    "Occidental", "Frente", "Polisario", "Construcción", "Murallas", "Defensivas", "Operaciones",
    "Insurrecciones", "Acuerdo", "Cese", "Fuego", "ONU", "Supervisión", "Fracaso", "Planes",
    "Paz", "Baker", "Periódicas", "Guerguerat", "Acción", "Militar", "Reconocimiento",
    "Soberanía", "Estados", "Unidos", "Enfrentamientos", "Argelia", "Rompe", "Relaciones",
    "Diplomáticas", "Nuevo", "Emisario", "ONU", "España", "Apoya", "Plan", "Autonomía",
    "Israel", "Francia"
]

def prepare_keyword_pattern():
    """Create a regex pattern for keyword matching"""
    escaped_keywords = [re.escape(kw.lower()) for kw in KEYWORDS]
    return re.compile(r'\b\w*?(?:%s)\w*\b' % '|'.join(escaped_keywords), re.IGNORECASE)

def is_bad_url(url):
    """Check if URL contains forbidden patterns"""
    url_lower = (url or '').lower()
    return any(pattern in url_lower for pattern in ['.dz', 'books.google.'])

def contains_keyword(text, pattern):
    """Check if text contains any keyword using regex pattern"""
    return bool(pattern.search(text.lower())) if text else False

def clean_data(json_data, keyword_pattern):
    """Clean and filter the JSON data structure"""
    if not isinstance(json_data, dict):
        print("  Warning: Invalid JSON structure. Expected dictionary.")
        return None, None

    cleaned = {
        "event": json_data.get("event"),
        "date": json_data.get("date"),
        "results": {}
    }

    stats = {
        'total_removed': 0,
        'url_filtered': 0,
        'keyword_filtered': 0,
        'per_language': {}
    }

    for lang, results in json_data.get('results', {}).items():
        lang_stats = {
            'original': len(results),
            'url_filtered': 0,
            'keyword_filtered': 0,
            'remaining': 0
        }
        
        filtered = []
        for result in results:
            # URL filtering
            if is_bad_url(result.get('url')):
                lang_stats['url_filtered'] += 1
                continue
            
            # Keyword checking
            title = result.get('title') or ''
            snippet = result.get('snippet') or ''
            if not (contains_keyword(title, keyword_pattern) or 
                    contains_keyword(snippet, keyword_pattern)):
                lang_stats['keyword_filtered'] += 1
                continue
            
            filtered.append(result)
        
        lang_stats['remaining'] = len(filtered)
        stats['per_language'][lang] = lang_stats
        stats['url_filtered'] += lang_stats['url_filtered']
        stats['keyword_filtered'] += lang_stats['keyword_filtered']
        cleaned['results'][lang] = filtered

    stats['total_removed'] = stats['url_filtered'] + stats['keyword_filtered']
    return cleaned, stats

def process_json_file(file_path, keyword_pattern):
    """Process a single JSON file with the new structure"""
    print(f"\n--- Processing: {file_path} ---")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)
    except Exception as e:
        print(f"  Error loading file: {str(e)}")
        return

    cleaned_data, stats = clean_data(original_data, keyword_pattern)
    
    if not cleaned_data:
        print("  No cleaning performed due to invalid structure")
        return

    # Save cleaned data back to original file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  Error saving file: {str(e)}")
        return

    # Print statistics
    total_original = sum(lang['original'] for lang in stats['per_language'].values())
    total_remaining = sum(lang['remaining'] for lang in stats['per_language'].values())
    
    print(f"  Original entries: {total_original}")
    print(f"  Remaining entries: {total_remaining}")
    print(f"  Total removed: {stats['total_removed']}")
    print("  Removal breakdown:")
    print(f"  - URL filtered: {stats['url_filtered']}")
    print(f"  - Keyword filtered: {stats['keyword_filtered']}")
    
    # Print per-language stats if any removals
    for lang, lang_stats in stats['per_language'].items():
        if lang_stats['original'] > 0:
            print(f"  {lang.upper()} results:")
            print(f"    Original: {lang_stats['original']}")
            print(f"    Remaining: {lang_stats['remaining']}")
            print(f"    URL filtered: {lang_stats['url_filtered']}")
            print(f"    Keyword filtered: {lang_stats['keyword_filtered']}")

    print(f"--- Finished: {file_path} ---")

def main():
    """Main execution function"""
    # Get target directory
    target_dir_str = input("Please enter the path to the folder containing JSON files: ")
    target_dir = Path(target_dir_str)
    
    if not target_dir.is_dir():
        print(f"Error: Invalid directory: {target_dir_str}")
        sys.exit(1)

    # Prepare keyword pattern once
    keyword_pattern = prepare_keyword_pattern()
    
    # Find all JSON files
    json_files = list(target_dir.rglob('*.json'))
    if not json_files:
        print("No JSON files found")
        sys.exit(0)

    print(f"\nFound {len(json_files)} JSON files. Starting processing...")

    # Process files
    processed_count = 0
    for json_file in json_files:
        try:
            process_json_file(json_file, keyword_pattern)
            processed_count += 1
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")

    print(f"\nProcessed {processed_count} files")

if __name__ == "__main__":
    main()