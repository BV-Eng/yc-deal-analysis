#!/usr/bin/env python3
"""
Fast owner assignment using thesis themes + keyword matching.
No API calls needed - runs instantly.
"""

import json
import re
import os

# Keywords for each investor
RICK_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'llm', 'gpt',
    'electrification', 'ev', 'electric vehicle', 'heat pump', 'grid',
    'building', 'construction', 'hvac', 'real estate',
    'wearable', 'remote monitoring', 'medtech', 'medical device',
    'quantum', 'semiconductor', 'chip',
    'no-code', 'developer tool', 'devops', 'software',
    'robotics', 'automation', 'drone', 'hardware',
    'saas', 'b2b', 'enterprise', 'infrastructure',
    'security', 'cybersecurity', 'identity',
    'space', 'aerospace', 'satellite',
]

WES_KEYWORDS = [
    'agriculture', 'agtech', 'farm', 'crop', 'food', 'nutrition',
    'health', 'healthcare', 'medical', 'clinical', 'patient', 'care',
    'metabolic', 'gut', 'microbiome', 'probiotic', 'prebiotic',
    'longevity', 'aging', 'lifespan', 'healthspan',
    'biotech', 'therapeutics', 'drug', 'pharma', 'medicine',
    'genomic', 'proteomic', 'multiomics', 'diagnostic',
    'mental health', 'behavioral', 'wellness',
    'ivf', 'fertility', 'reproductive',
    'diabetes', 'chronic', 'disease',
]

LYNDSEY_KEYWORDS = [
    'education', 'learning', 'training', 'skill', 'workforce',
    'reskill', 'upskill', 'credential', 'certification',
    'circular', 'recycling', 'waste', 'upcycl',
    'climate', 'carbon', 'emission', 'sustainability', 'sustainable',
    'supply chain', 'logistics', 'manufacturing', 'industrial',
    'smb', 'small business', 'trade', 'hvac', 'electrician', 'plumber',
    'water', 'wastewater', 'desalination', 'cleantech',
    'biodiversity', 'conservation', 'environmental',
    'gig', 'freelance', 'contractor',
    'compliance', 'governance', 'policy', 'legal',
]

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
    industries = company.get('industries', '') or ''
    tags = company.get('tags', '') or ''

    # Combine all text for keyword matching
    all_text = f"{name} {one_liner} {description} {industries} {tags}"

    # Theme-based assignment
    if theme == 'Human Health':
        return 'Wes', 'theme:Human Health'
    elif theme == 'Tomorrow\'s Workforce':
        return 'Lyndsey', 'theme:Tomorrow\'s Workforce'
    elif theme == 'Sustainable Industry':
        # Sustainable Industry could be Lyndsey (climate/circular) or Rick (electrification)
        # Check keywords to decide
        rick_score = match_keywords(all_text, ['electrification', 'ev', 'electric', 'grid', 'building', 'hvac', 'hardware', 'robotics', 'chip', 'semiconductor'])
        lyndsey_score = match_keywords(all_text, ['circular', 'recycling', 'waste', 'water', 'climate', 'carbon', 'supply chain', 'manufacturing'])
        if rick_score > lyndsey_score:
            return 'Rick', 'theme:Sustainable+electrification'
        else:
            return 'Lyndsey', 'theme:Sustainable Industry'

    # For Neutral/Off-Thesis, use keyword matching
    rick_score = match_keywords(all_text, RICK_KEYWORDS)
    wes_score = match_keywords(all_text, WES_KEYWORDS)
    lyndsey_score = match_keywords(all_text, LYNDSEY_KEYWORDS)

    # Get winner
    scores = {'Rick': rick_score, 'Wes': wes_score, 'Lyndsey': lyndsey_score}
    max_score = max(scores.values())

    if max_score > 0:
        # Return the one with highest score
        winner = max(scores, key=scores.get)
        return winner, f'keywords:{winner}={max_score}'

    # Fallback: assign to person with fewest
    winner = min(current_counts, key=current_counts.get)
    return winner, 'fallback:load-balance'

def main():
    print("=" * 70)
    print("Fast Owner Assignment (Theme + Keywords)")
    print("=" * 70)

    # Load data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'seed-data.json')
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Get current counts
    current_counts = {'Rick': 0, 'Wes': 0, 'Lyndsey': 0}
    for c in data['companies']:
        owner = c.get('owner')
        if owner in current_counts:
            current_counts[owner] += 1

    print(f"Current: Rick={current_counts['Rick']}, Wes={current_counts['Wes']}, Lyndsey={current_counts['Lyndsey']}")
    print()

    # Find unassigned
    unassigned = [(i, c) for i, c in enumerate(data['companies']) if not c.get('owner')]
    print(f"Unassigned: {len(unassigned)} companies\n")

    # Track assignments
    new_assignments = {'Rick': 0, 'Wes': 0, 'Lyndsey': 0}
    assignment_log = []

    for idx, company in unassigned:
        name = company.get('name', 'Unknown')
        owner, reason = assign_owner(company, {
            'Rick': current_counts['Rick'] + new_assignments['Rick'],
            'Wes': current_counts['Wes'] + new_assignments['Wes'],
            'Lyndsey': current_counts['Lyndsey'] + new_assignments['Lyndsey'],
        })

        new_assignments[owner] += 1
        data['companies'][idx]['owner'] = owner
        assignment_log.append({
            'name': name,
            'owner': owner,
            'reason': reason,
            'one_liner': company.get('one_liner', '')[:60],
            'theme': company.get('thesis_fit_theme', ''),
        })

        print(f"{name[:40]:<40} → {owner:<8} ({reason})")

    # Save
    with open(data_path, 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"New assignments: Rick={new_assignments['Rick']}, Wes={new_assignments['Wes']}, Lyndsey={new_assignments['Lyndsey']}")

    final_counts = {
        'Rick': current_counts['Rick'] + new_assignments['Rick'],
        'Wes': current_counts['Wes'] + new_assignments['Wes'],
        'Lyndsey': current_counts['Lyndsey'] + new_assignments['Lyndsey'],
    }
    print(f"Final totals:   Rick={final_counts['Rick']}, Wes={final_counts['Wes']}, Lyndsey={final_counts['Lyndsey']}")
    print(f"\nSaved to {data_path}")

    # Output sample for spot-checking
    print("\n" + "=" * 70)
    print("SAMPLE FOR SPOT-CHECK (first 20)")
    print("=" * 70)
    for item in assignment_log[:20]:
        print(f"{item['name'][:35]:<35} | {item['owner']:<8} | {item['reason']:<25} | {item['one_liner'][:40]}")

if __name__ == "__main__":
    main()
