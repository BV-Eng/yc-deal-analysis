#!/usr/bin/env python3
"""
Add investor assignments and industry classification to Deepchecks Mar 2026 batch.
"""

import json
import re
from pathlib import Path

# Industry classification keywords
INDUSTRY_KEYWORDS = {
    'Biotech': ['biotech', 'biomanufacturing', 'ferment', 'microb', 'enzyme', 'protein', 'cell culture', 'biolog'],
    'Clean Energy': ['hydrogen', 'solar', 'renewable', 'battery', 'energy storage', 'grid', 'power', 'electrification'],
    'Climate Tech': ['carbon', 'decarboniz', 'emission', 'climate', 'sustainability', 'clean'],
    'Healthcare': ['health', 'medical', 'diagnostic', 'therapeutic', 'patient', 'clinical', 'pharma', 'drug'],
    'Neurotech': ['neuro', 'brain', 'cognitive', 'neural', 'sleep', 'eeg'],
    'AgTech': ['agriculture', 'farm', 'crop', 'soil', 'nutrient', 'biostimulant', 'agri'],
    'Robotics': ['robot', 'autonomous', 'automat', 'drone', 'unmanned'],
    'Construction Tech': ['construction', 'building', 'housing', 'modular'],
    'Space Tech': ['space', 'satellite', 'orbit', 'payload', 'launch', 'rocket'],
    'Logistics': ['delivery', 'logistics', 'supply chain', 'freight', 'shipping', 'curb'],
    'Industrial': ['industrial', 'manufacturing', 'factory', 'production'],
    'Materials': ['material', 'chemical', 'solvent', 'polymer', 'composite'],
    'Defense': ['defense', 'military', 'security', 'surveillance', 'tactical'],
    'AI/ML': ['artificial intelligence', 'machine learning', 'ai', 'ml', 'deep learning', 'neural network', 'llm'],
    'SaaS': ['software', 'saas', 'platform', 'cloud', 'api'],
    'Hardware': ['hardware', 'device', 'sensor', 'chip', 'semiconductor', 'imaging'],
    'Fintech': ['finance', 'banking', 'payment', 'lending', 'insurance'],
    'Education': ['education', 'learning', 'training', 'skill', 'workforce'],
}

# Keywords for investor assignment
RICK_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'llm',
    'electrification', 'ev', 'electric vehicle', 'heat pump', 'grid',
    'building', 'construction', 'hvac', 'real estate',
    'wearable', 'remote monitoring', 'medtech', 'medical device',
    'quantum', 'semiconductor', 'chip',
    'robotics', 'automation', 'drone', 'hardware',
    'saas', 'b2b', 'enterprise', 'infrastructure',
    'security', 'cybersecurity',
    'space', 'aerospace', 'satellite',
    'imaging', 'sensor', 'detection',
]

WES_KEYWORDS = [
    'agriculture', 'agtech', 'farm', 'crop', 'food', 'nutrition',
    'health', 'healthcare', 'medical', 'clinical', 'patient', 'care',
    'metabolic', 'gut', 'microbiome', 'probiotic',
    'longevity', 'aging', 'lifespan', 'healthspan',
    'biotech', 'therapeutics', 'drug', 'pharma', 'medicine',
    'genomic', 'proteomic', 'diagnostic',
    'mental health', 'behavioral', 'wellness',
    'fertility', 'reproductive',
    'brain', 'neuro', 'cognitive',
]

LYNDSEY_KEYWORDS = [
    'education', 'learning', 'training', 'skill', 'workforce',
    'reskill', 'upskill', 'credential',
    'circular', 'recycling', 'waste', 'upcycl',
    'climate', 'carbon', 'emission', 'sustainability',
    'supply chain', 'logistics', 'manufacturing', 'industrial',
    'smb', 'small business', 'trade',
    'water', 'wastewater', 'desalination', 'cleantech',
    'biodiversity', 'conservation', 'environmental',
    'chemical', 'material', 'solvent',
]


def classify_industry(company):
    """Classify company into industries based on description."""
    name = company.get('name', '') or ''
    one_liner = company.get('one_liner', '') or ''
    description = company.get('long_description', '') or ''

    # Also get company description from founder's LinkedIn
    founders = company.get('founders', [])
    founder_company_desc = ''
    if founders:
        f = founders[0]
        founder_company_desc = f.get('headline', '') or ''

    all_text = f"{name} {one_liner} {description} {founder_company_desc}".lower()

    matched = []
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                if industry not in matched:
                    matched.append(industry)
                break

    # Return top 2 most relevant
    if matched:
        return ', '.join(matched[:2])
    return 'Deep Tech'


def match_keywords(text, keywords):
    """Count keyword matches in text."""
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        if kw in text_lower:
            count += 1
    return count


def assign_owner(company, current_counts):
    """Assign owner based on theme and keywords."""
    theme = company.get('thesis_fit_theme', '') or ''
    name = company.get('name', '') or ''
    one_liner = company.get('one_liner', '') or ''
    description = company.get('long_description', '') or ''

    # Get founder info too
    founders = company.get('founders', [])
    founder_text = ''
    if founders:
        f = founders[0]
        founder_text = f"{f.get('headline', '')} {f.get('bio', '')} {f.get('prior_employers', '')}"

    all_text = f"{name} {one_liner} {description} {founder_text}"

    # Theme-based assignment
    if theme == 'Human Health':
        return 'Wes', 'theme:Human Health'
    elif theme == "Tomorrow's Workforce":
        return 'Lyndsey', "theme:Tomorrow's Workforce"
    elif theme == 'Sustainable Industry':
        # Check sub-category
        rick_score = match_keywords(all_text, ['electrification', 'ev', 'electric', 'grid', 'building', 'hvac', 'hardware', 'robotics', 'chip', 'semiconductor', 'space', 'satellite', 'imaging', 'sensor'])
        wes_score = match_keywords(all_text, ['biotech', 'biomanufacturing', 'ferment', 'agriculture', 'food', 'health', 'therapeutic'])
        lyndsey_score = match_keywords(all_text, ['circular', 'recycling', 'waste', 'water', 'climate', 'carbon', 'supply chain', 'manufacturing', 'chemical', 'material'])

        scores = {'Rick': rick_score, 'Wes': wes_score, 'Lyndsey': lyndsey_score}
        winner = max(scores, key=scores.get)
        if scores[winner] > 0:
            return winner, f'theme:Sustainable+{winner.lower()}'
        return 'Lyndsey', 'theme:Sustainable Industry'

    # For Neutral/Off-Thesis, use keyword matching
    rick_score = match_keywords(all_text, RICK_KEYWORDS)
    wes_score = match_keywords(all_text, WES_KEYWORDS)
    lyndsey_score = match_keywords(all_text, LYNDSEY_KEYWORDS)

    scores = {'Rick': rick_score, 'Wes': wes_score, 'Lyndsey': lyndsey_score}
    max_score = max(scores.values())

    if max_score > 0:
        winner = max(scores, key=scores.get)
        return winner, f'keywords:{winner}={max_score}'

    # Fallback: load balance
    winner = min(current_counts, key=current_counts.get)
    return winner, 'fallback:load-balance'


def main():
    print("=" * 70)
    print("Enriching Deepchecks Mar 2026 - Owners + Industries")
    print("=" * 70)

    # Load data
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'
    with open(seed_path, 'r') as f:
        data = json.load(f)

    # Get current owner counts
    current_counts = {'Rick': 0, 'Wes': 0, 'Lyndsey': 0}
    for c in data['companies']:
        owner = c.get('owner')
        if owner in current_counts:
            current_counts[owner] += 1

    print(f"Current totals: Rick={current_counts['Rick']}, Wes={current_counts['Wes']}, Lyndsey={current_counts['Lyndsey']}")
    print()

    # Find Mar 2026 Deepchecks companies
    assignments = {'Rick': 0, 'Wes': 0, 'Lyndsey': 0}

    for i, c in enumerate(data['companies']):
        if c.get('source') != 'Deepchecks':
            continue

        name = c.get('name', 'Unknown')

        # Assign owner
        owner, reason = assign_owner(c, {
            'Rick': current_counts['Rick'] + assignments['Rick'],
            'Wes': current_counts['Wes'] + assignments['Wes'],
            'Lyndsey': current_counts['Lyndsey'] + assignments['Lyndsey'],
        })

        # Classify industry
        industries = classify_industry(c)

        # Update
        data['companies'][i]['owner'] = owner
        data['companies'][i]['industries'] = industries

        assignments[owner] += 1

        print(f"{name[:30]:<30} | {owner:<8} | {industries[:25]:<25} | {reason}")

    # Save
    with open(seed_path, 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Assigned: Rick={assignments['Rick']}, Wes={assignments['Wes']}, Lyndsey={assignments['Lyndsey']}")

    final = {k: current_counts[k] + assignments[k] for k in current_counts}
    print(f"Final totals: Rick={final['Rick']}, Wes={final['Wes']}, Lyndsey={final['Lyndsey']}")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. git add data/seed-data.json")
    print("2. git commit -m 'Add owners and industries to Deepchecks Mar 2026'")
    print("3. git push origin main")
    print("4. curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed")


if __name__ == "__main__":
    main()
