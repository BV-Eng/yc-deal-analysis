#!/usr/bin/env python3
"""
Step 4: Import Pitchbook URLs from CSV

Usage:
    python3 scripts/4_import_pitchbook_urls.py /path/to/pitchbook_urls.csv

Expected CSV format:
    Website,Pitchbook URL,Company Name,ID
    https://example.com,https://my.pitchbook.com/profile/...,Company Name,123

URLs with value "N/A" or empty will be skipped.
"""

import sys
import csv
import json
from pathlib import Path

def import_pitchbook_urls(csv_path):
    """Import Pitchbook URLs from CSV into seed-data.json."""
    # Read Pitchbook URLs from CSV
    pitchbook_urls = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('Pitchbook URL', '').strip()
            company_id = row.get('ID', '').strip()

            if url and url != 'N/A' and company_id:
                pitchbook_urls[int(company_id)] = url

    print(f"Found {len(pitchbook_urls)} Pitchbook URLs\n")

    # Update seed data
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'

    with open(seed_path, 'r') as f:
        seed_data = json.load(f)

    updated = 0
    for company in seed_data['companies']:
        if company['id'] in pitchbook_urls:
            company['pitchbook_url'] = pitchbook_urls[company['id']]
            print(f"  {company['name']}: {pitchbook_urls[company['id']][:60]}...")
            updated += 1

    # Save updated seed data
    with open(seed_path, 'w') as f:
        json.dump(seed_data, f, indent=2)

    return updated

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 4_import_pitchbook_urls.py <csv_file>")
        print("Example: python3 4_import_pitchbook_urls.py ~/Downloads/pitchbook_urls.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    print(f"Importing Pitchbook URLs from {csv_path}...")
    updated = import_pitchbook_urls(csv_path)

    print(f"\nUpdated {updated} companies with Pitchbook URLs")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Commit changes: git add data/seed-data.json && git commit -m 'Add Pitchbook URLs'")
    print("2. Push to deploy: git push origin main")
    print("3. Reload seed data: curl -X POST https://yc-deal-analysis.vercel.app/api/admin/reload-seed")
