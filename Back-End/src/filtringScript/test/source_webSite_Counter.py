import json
from urllib.parse import urlparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_PATH = PROJECT_ROOT / "src" / "Data" / "Content" / "filtered_clean_content.json"

# Load your JSON data
with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

domain_counts = {}

# Count domain occurrences
for entry in data:
    if 'link' in entry:
        domain = urlparse(entry['link']).netloc
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

# Format results
result = [{"website": domain, "count": count} for domain, count in domain_counts.items()]

print(json.dumps(result, indent=2, ensure_ascii=False))