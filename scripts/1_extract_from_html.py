#!/usr/bin/env python3
"""
Step 1: Extract companies from Deepchecks HTML export

Usage:
    python3 scripts/1_extract_from_html.py /path/to/deepchecks_export.html

This script:
1. Parses the Deepchecks HTML export
2. Extracts company names, descriptions, deck URLs, founder info
3. Adds companies to seed-data.json with initial scoring
4. Generates lookup sheet for LinkedIn/Pitchbook research
"""

import sys
import re
import json
from pathlib import Path

# Thesis theme mapping based on industry keywords
THEME_MAPPING = {
    'Sustainable Industry': ['climate', 'energy', 'solar', 'battery', 'carbon', 'sustainable', 'green', 'renewable', 'cleantech', 'materials', 'industrial', 'manufacturing', 'chemicals', 'metals', 'mining'],
    'Human Health': ['health', 'medical', 'medtech', 'biotech', 'pharma', 'therapeutic', 'diagnostic', 'healthcare', 'life science', 'drug', 'clinical'],
    "Tomorrow's Workforce": ['robotics', 'automation', 'ai', 'autonomous', 'drone', 'logistics', 'workforce', 'labor'],
}

def classify_theme(industries, tags, description):
    """Classify company into thesis theme based on keywords."""
    text = f"{industries} {tags} {description}".lower()

    for theme, keywords in THEME_MAPPING.items():
        for keyword in keywords:
            if keyword in text:
                return theme
    return 'Neutral'

def parse_html(html_path):
    """Parse Deepchecks HTML export and extract company data."""
    with open(html_path, 'r') as f:
        html = f.read()

    sections = html.split('class="company-row"')
    companies = []
    seen_names = set()

    for section in sections[1:]:
        # Extract name
        name_match = re.search(r'class="company-name"[^>]*>([^<]+)<', section)
        if not name_match:
            continue

        name = name_match.group(1).strip()
        if name in seen_names:
            continue
        seen_names.add(name)

        company = {'name': name}

        # Extract slogan (one-liner)
        slogan_match = re.search(r'class="company-slogan[^"]*"[^>]*>([^<]+)<', section)
        if slogan_match:
            company['one_liner'] = slogan_match.group(1).strip()

        # Extract descriptions
        desc_matches = re.findall(r'class="company-desc"[^>]*>([^<]+)<', section)
        for d in desc_matches:
            if len(d.strip()) > 100 and 'University' not in d and 'School' not in d:
                company['long_description'] = d.strip().replace('&amp;', '&').replace('&nbsp;', ' ').replace('&gt;', '>').replace('&lt;', '<')
                break

        # Extract deck URL
        deck_match = re.search(r'href="(https://drive\.google\.com/file/d/[^"]+)"', section)
        if deck_match:
            url = deck_match.group(1)
            if 'https://' in url[8:]:
                url = url.split('https://')[0]
            company['deck_url'] = url

        # Extract founder names and LinkedIn URLs
        founder_pattern = r'class="founder-name[^"]*"[^>]*>([^<]+)<'
        linkedin_pattern = r'href="(https://(?:www\.)?linkedin\.com/in/[^"]+)"'

        founder_names = re.findall(founder_pattern, section)
        linkedin_urls = re.findall(linkedin_pattern, section)

        # Also try to extract from company-desc that look like founder info
        if not founder_names:
            # Look for names that appear before LinkedIn-like patterns
            email_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)[^@]*@', section)
            if email_match:
                founder_names = [email_match.group(1)]

        company['founders'] = []
        for i, name in enumerate(founder_names[:3]):  # Max 3 founders
            founder = {'name': name.strip()}
            if i < len(linkedin_urls):
                founder['linkedin'] = linkedin_urls[i]
            company['founders'].append(founder)

        # Extract contact email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', section)
        if email_match:
            company['contact_email'] = email_match.group(1)

        # Extract website from email domain
        if company.get('contact_email'):
            domain = company['contact_email'].split('@')[1]
            company['website'] = f"https://{domain}/"

        # Extract industry/tags
        tag_matches = re.findall(r'class="sector-pill[^"]*"[^>]*>[^<]*<[^>]*>([^<]+)<', section)
        if tag_matches:
            company['industries'] = tag_matches[0] if tag_matches else ''
            company['tags'] = ', '.join(tag_matches)

        companies.append(company)

    return companies

def add_to_seed_data(companies, batch_name):
    """Add extracted companies to seed-data.json."""
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'

    with open(seed_path, 'r') as f:
        seed_data = json.load(f)

    # Find next available ID
    max_id = max(c['id'] for c in seed_data['companies'])
    next_id = max_id + 1

    # Find next founder ID
    max_founder_id = 0
    for c in seed_data['companies']:
        for f in c.get('founders', []):
            max_founder_id = max(max_founder_id, f.get('id', 0))
    next_founder_id = max_founder_id + 1

    added = []
    for company in companies:
        # Classify theme
        theme = classify_theme(
            company.get('industries', ''),
            company.get('tags', ''),
            company.get('long_description', company.get('one_liner', ''))
        )

        # Create company record
        record = {
            'id': next_id,
            'name': company['name'],
            'one_liner': company.get('one_liner', ''),
            'long_description': company.get('long_description', company.get('one_liner', '')),
            'batch': batch_name,
            'source': 'Deepchecks',
            'status': 'Not Contacted',
            'industries': company.get('industries', ''),
            'subindustry': company.get('industries', ''),
            'tags': company.get('tags', 'Deep Tech'),
            'website': company.get('website', ''),
            'all_locations': '',
            'team_size': 0,
            'year_founded': None,
            'logo_url': '',
            'b2b_b2c': 'B2B',
            'technology_type': 'Deep Tech',
            'business_model': None,
            'next_action': None,
            'custom_tags': None,
            'created_at': '2026-03-03 12:00:00',
            'updated_at': '2026-03-03 12:00:00',
            'owner': None,
            'contact_email': company.get('contact_email', ''),
            'pitchbook_url': '',
            'deck_url': company.get('deck_url', ''),
            'valuation_range': '$5M - $10M',

            # Initial thesis scoring (will be refined manually if needed)
            'thesis_fit_theme': theme,
            'thesis_fit_score': 7.5 if theme != 'Neutral' else 5,
            'thesis_fit_weight': 25,
            'thesis_fit_justification': f"{'Strong' if theme != 'Neutral' else 'Limited'} alignment with Better.vc {theme} theme." if theme != 'Neutral' else 'Off-thesis or unclear alignment.',

            # Default company scores (to be refined)
            'team_score': 6,
            'team_weight': 15,
            'team_justification': f"Founder: {company['founders'][0]['name'] if company.get('founders') else 'Unknown'}. Pending LinkedIn analysis.",
            'product_score': 6,
            'product_weight': 10,
            'product_justification': f"Deep tech: {company.get('industries', 'Unknown')}.",
            'business_model_score': 6.5,
            'business_model_weight': 10,
            'business_model_justification': 'Deep tech B2B model typical of Deepchecks batch.',
            'market_score': 7,
            'market_weight': 10,
            'market_justification': f"Operating in {company.get('industries', 'deep tech')} market.",
            'impact_score': 6,
            'impact_weight': 20,
            'impact_justification': '',
            'traction_score': 6,
            'traction_weight': 5,
            'traction_justification': 'Deepchecks curated batch.',
            'deal_score': 5.5,
            'deal_weight': 5,
            'deal_justification': f'{batch_name}.',
            'company_score': 7,
            'avg_founder_score': None,
            'weighted_total': 7,  # Will be recalculated after founder scoring

            'founders': [],
            'interactions': [],
            'notes': []
        }

        # Add founders
        for founder in company.get('founders', []):
            founder_record = {
                'id': next_founder_id,
                'company_id': next_id,
                'name': founder['name'],
                'first_name': '',
                'last_name': '',
                'title': 'Founder',
                'linkedin': founder.get('linkedin', ''),
                'twitter': '',
                'avatar_url': '',
                'bio': '',
                'email': company.get('contact_email', ''),
                'is_female': 0,
                'is_black': 0,
                'is_hispanic_latino': 0,
                'schools': '',
                'degrees': '',
                'prior_employers': '',
                'technical_competence': '',
                'publications_count': 0,
                'citations_count': 0,
                'awards': None,
                'patents': None,
                'is_repeat_founder': 0,
                'is_colocated': 0,
                'age_range': None,
                'created_at': '2026-03-03 12:00:00',
                'founder_score': None
            }
            record['founders'].append(founder_record)
            next_founder_id += 1

        # If no founders found, add placeholder
        if not record['founders']:
            record['founders'].append({
                'id': next_founder_id,
                'company_id': next_id,
                'name': 'Founder',
                'first_name': '',
                'last_name': '',
                'title': 'Founder',
                'linkedin': '',
                'twitter': '',
                'avatar_url': '',
                'bio': '',
                'email': company.get('contact_email', ''),
                'is_female': 0,
                'is_black': 0,
                'is_hispanic_latino': 0,
                'schools': '',
                'degrees': '',
                'prior_employers': '',
                'technical_competence': '',
                'publications_count': 0,
                'citations_count': 0,
                'awards': None,
                'patents': None,
                'is_repeat_founder': 0,
                'is_colocated': 0,
                'age_range': None,
                'created_at': '2026-03-03 12:00:00',
                'founder_score': None
            })
            next_founder_id += 1

        seed_data['companies'].append(record)
        added.append(record)
        next_id += 1

    # Save updated seed data
    with open(seed_path, 'w') as f:
        json.dump(seed_data, f, indent=2)

    return added

def generate_lookup_sheet(companies, output_path):
    """Generate CSV for LinkedIn and Pitchbook lookup."""
    import csv

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Company Name', 'ID', 'Website', 'Founder Name', 'Founder LinkedIn', 'Pitchbook URL'])

        for company in companies:
            founders = company.get('founders', [{'name': 'Unknown', 'linkedin': ''}])
            for i, founder in enumerate(founders):
                writer.writerow([
                    company['name'] if i == 0 else '',
                    company['id'] if i == 0 else '',
                    company.get('website', '') if i == 0 else '',
                    founder.get('name', ''),
                    founder.get('linkedin', ''),
                    '' if i == 0 else ''  # Pitchbook URL column for user to fill
                ])

    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 1_extract_from_html.py <html_file> [batch_name]")
        print("Example: python3 1_extract_from_html.py ~/Downloads/deepchecks.html 'Deepchecks Mar 2026'")
        sys.exit(1)

    html_path = sys.argv[1]
    batch_name = sys.argv[2] if len(sys.argv) > 2 else 'Deepchecks Batch'

    print(f"Parsing {html_path}...")
    companies = parse_html(html_path)
    print(f"Found {len(companies)} companies\n")

    print("Adding to seed-data.json...")
    added = add_to_seed_data(companies, batch_name)
    print(f"Added {len(added)} companies (IDs {added[0]['id']} - {added[-1]['id']})\n")

    # Generate lookup sheet
    output_csv = Path(html_path).parent / f"deepchecks_lookup_{batch_name.replace(' ', '_').lower()}.csv"
    generate_lookup_sheet(added, output_csv)
    print(f"Generated lookup sheet: {output_csv}")

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Open the lookup CSV and fill in:")
    print("   - Missing founder LinkedIn URLs")
    print("   - Pitchbook URLs for each company")
    print("2. Use a LinkedIn scraper to get founder profile data")
    print("3. Run step 3 to import LinkedIn profiles and score founders")
    print("4. Run step 4 to import Pitchbook URLs")
    print("5. Commit and push, then reload seed data")
