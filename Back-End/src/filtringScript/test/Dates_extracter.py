import re
import json
from pathlib import Path

class DateRangeExtractor:
    def __init__(self):
        self.date_patterns = {
            'year': r'(?<!\d)(1\d{3}|20[0-2]\d)(?!\d)',
            'range': r'(?<!\d)(\d{3,4})\s*[-–ـ—]\s*(\d{3,4})(?!\d)',
            'hijri_range': r'(\d{3})\s*[-–ـ—]\s*(\d{3})\s*هـ',
            'gregorian_range': r'(\d{3,4})\s*[-–ـ—]\s*(\d{3,4})\s*م'
        }

        self.historical_periods = {
            # Algerian history periods
            "الاحتلال الفرنسي": (1830, 1962),
            "الاستعمار الفرنسي": (1830, 1962),
            "الثورة الجزائرية": (1954, 1962),
            "العصر العثماني": (1517, 1830),
            
            # General Islamic history
            "الدولة الأموية": (661, 750),
            "الدولة العباسية": (750, 1258),
            "الدولة الفاطمية": (909, 1171),
            
            # Centuries
            "القرن التاسع عشر": (1801, 1900),
            "القرن العشرين": (1901, 2000),
            "القرن الحادي والعشرين": (2001, 2100)
        }

        self.century_map = {
            'التاسع عشر': (1801, 1900),
            'العشرين': (1901, 2000),
            'الحادي والعشرين': (2001, 2100),
            'الثامن عشر': (1701, 1800),
            'السابع عشر': (1601, 1700),
            'السادس عشر': (1501, 1600),
            'الخامس عشر': (1401, 1500)
        }

    def _extract_dates(self, text):
        dates = []
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)  # Remove zero-width spaces
        
        # Extract Hijri date ranges and convert to Gregorian
        for match in re.finditer(self.date_patterns['hijri_range'], text):
            start_hijri, end_hijri = map(int, match.groups())
            start_gregorian = int(start_hijri * 0.97 + 622)
            end_gregorian = int(end_hijri * 0.97 + 622)
            if 500 <= start_gregorian <= end_gregorian <= 2025:
                dates.extend([start_gregorian, end_gregorian])
        
        # Extract Gregorian date ranges with 'م' marker
        for match in re.finditer(self.date_patterns['gregorian_range'], text):
            start, end = map(int, match.groups())
            if 500 <= start <= end <= 2025:
                dates.extend([start, end])
        
        # Extract standard year ranges
        for match in re.finditer(self.date_patterns['range'], text):
            start, end = map(int, match.groups())
            if 500 <= start <= end <= 2025:
                dates.extend([start, end])
        
        # Extract standalone years
        for match in re.finditer(self.date_patterns['year'], text):
            year = int(match.group())
            if 500 <= year <= 2025:
                dates.append(year)
        
        return dates

    def _parse_century(self, text):
        for century, years in self.century_map.items():
            if re.search(fr'\b{century}\b', text):
                return years
        return None

    def _find_historical_period(self, text):
        for period, years in self.historical_periods.items():
            if re.search(fr'\b{period}\b', text):
                return years
        return None

    def _process_content(self, content):
        dates = []
        historical_period = None
        
        if isinstance(content, dict):
            for value in content.values():
                d, hp = self._process_content(value)
                dates.extend(d)
                historical_period = historical_period or hp
        elif isinstance(content, list):
            for item in content:
                d, hp = self._process_content(item)
                dates.extend(d)
                historical_period = historical_period or hp
        elif isinstance(content, str):
            dates.extend(self._extract_dates(content))
            if not historical_period:
                historical_period = self._find_historical_period(content)
        
        return dates, historical_period

    def _process_entry(self, entry):
        all_dates = []
        historical_period = None
        
        # Process main fields
        for field in ['title', 'description', 'source']:
            if content := entry.get(field):
                if isinstance(content, str):
                    all_dates.extend(self._extract_dates(content))
                    if not historical_period:
                        historical_period = self._find_historical_period(content)
                else:
                    d, hp = self._process_content(content)
                    all_dates.extend(d)
                    historical_period = historical_period or hp

        # Process nested content
        if content := entry.get('content'):
            d, hp = self._process_content(content)
            all_dates.extend(d)
            historical_period = historical_period or hp

        # Process centuries
        century_text = ' '.join([entry.get(f, '') for f in ['title', 'description']])
        if century_range := self._parse_century(century_text):
            all_dates.extend(century_range)

        # Determine final range
        date_range = {'start': None, 'end': None}
        
        if all_dates:
            valid_dates = [d for d in all_dates if 500 <= d <= 2025]
            if valid_dates:
                date_range['start'] = min(valid_dates)
                date_range['end'] = max(valid_dates)
        elif historical_period:
            date_range['start'] = historical_period[0]
            date_range['end'] = historical_period[1]

        # Only validate if start > end, don't filter by range size
        if date_range['start'] and date_range['end']:
            if date_range['start'] > date_range['end']:
                date_range['start'], date_range['end'] = date_range['end'], date_range['start']

        entry['date_range'] = date_range if date_range['start'] else None
        return entry

def process_data(input_file, output_file):
    extractor = DateRangeExtractor()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = [extractor._process_entry(entry) for entry in data]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    input_path = project_root / "src" / "Data" / "Content" / "filtered_clean_content.json"
    output_path = project_root / "src" / "Data" / "Content" / "filtered_clean_content2.json"

    process_data(input_path, output_path)
    print("✅ Date range extraction completed successfully!")