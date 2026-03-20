#!/usr/bin/env python3
"""
Re-score PNP companies using Claude API with Better Ventures thesis alignment.
Updates both seed-data.json and Affinity.
"""

import os
import sys
import json
import time
import requests
from anthropic import Anthropic

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AFFINITY_API_KEY = os.getenv("AFFINITY_API_KEY")

if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set")
    sys.exit(1)

client = Anthropic(api_key=ANTHROPIC_API_KEY)

BETTER_VENTURES_THESIS = """
Better Ventures backs startups leveraging science & technology to build the Better Economy, where people and the planet flourish.

INVESTMENT THEMES:

1. BUILD SUSTAINABLE INDUSTRY (Climate/Sustainability)
   Novel solutions for reducing carbon emissions, waste, and pollution across industries.
   Focus Areas: Electrification, Food & Ag, Bioeconomy, Circular Economy
   Examples: Green chemistry, biomanufacturing, textile recycling, carbon reduction, regenerative agriculture

2. IMPROVE HUMAN HEALTH
   Biological insights and digital tools to improve health and reduce the cost of care.
   Focus Areas: Behavioral Health, Personalized Health, Food as Medicine, Longevity
   Examples: Chronic disease reversal, preventive health, AI diagnostics, healthspan extension, digital therapeutics

3. EQUIP TOMORROW'S WORKFORCE
   Building the skills required to thrive in the modern economy.
   Focus Areas: Personalized Learning, Reskilling, Workforce Augmentation, AI for SMBs
   Examples: Skills-based hiring, AI productivity tools, alternative credentials, workforce training

WHAT MAKES A STRONG FIT:
- Uses breakthrough technology (AI/ML, biotech, materials science)
- Clear impact on people or planet
- B2B model preferred
- Addresses a large market with novel approach
"""

SCORING_PROMPT = """You are evaluating startups for Better Ventures, a VC fund.

{thesis}

COMPANY TO EVALUATE:
Name: {name}
Description: {description}
Industry: {industry}

SCORING CRITERIA (use the FULL 1-10 range):

9-10: EXCEPTIONAL FIT
- Core business directly addresses a thesis pillar using breakthrough science/technology
- Clear, measurable impact on climate, health, or workforce
- Novel approach to large market
- Example: AI platform reversing chronic disease, carbon capture biotech

7-8: STRONG FIT
- Good alignment with thesis themes
- Uses technology meaningfully
- Clear path to impact
- Example: Digital health tool improving care access, agtech reducing emissions

5-6: MODERATE FIT
- Some thesis relevance but not core focus
- Technology angle exists but not breakthrough
- Impact is indirect or unclear
- Example: Healthcare SaaS with efficiency gains but no health outcomes focus

3-4: WEAK FIT
- Tangential connection to themes at best
- Generic tech/software without clear impact angle
- Would need significant pivot to align
- Example: General B2B SaaS, fintech without inclusion angle

1-2: NOT A FIT
- No alignment with thesis
- Off-thesis categories (gaming, crypto, defense, luxury)
- No science/technology differentiation
- Example: Consumer social app, crypto trading platform

BE DISCRIMINATING. Most companies should NOT score 7+. Reserve high scores for truly exceptional thesis alignment.

Respond with ONLY a JSON object:
{{
  "score": <number 1-10>,
  "theme": "<Sustainable Industry|Human Health|Tomorrow's Workforce|Off-Thesis>",
  "justification": "<2-3 sentence explanation>",
  "investor": "<Rick|Wes|Lyndsey>"
}}

INVESTOR ASSIGNMENT:
- Rick: Health AI, Electrification, Buildings, EV Fleets, Medtech, Digital Health
- Wes: Agriculture, Food, Metabolic health, Nutrition, Food as Medicine
- Lyndsey: Education, Workforce training, Circular economy, Recycling
"""


def score_company_with_claude(company):
    """Score a single company using Claude."""
    name = company.get('name', '')
    description = company.get('one_liner', '') or company.get('long_description', '')
    industry = company.get('industries', '')

    prompt = SCORING_PROMPT.format(
        thesis=BETTER_VENTURES_THESIS,
        name=name,
        description=description[:1000],  # Limit description length
        industry=industry
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Parse JSON response
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)
        return result

    except Exception as e:
        print(f"  Error scoring {name}: {e}")
        return None


def update_affinity_score(company_name, score, investor):
    """Update the ranking and investor in Affinity."""
    if not AFFINITY_API_KEY:
        return False

    AFFINITY_AUTH = ('', AFFINITY_API_KEY)
    AFFINITY_BASE_URL = "https://api.affinity.co"
    AFFINITY_LIST_ID = 324289
    FIELD_IDS = {"ranking": 5458698, "investor": 5418327, "investors": 5572905}

    try:
        # Find org
        resp = requests.get(f'{AFFINITY_BASE_URL}/organizations',
                          auth=AFFINITY_AUTH, params={'term': company_name})
        orgs = resp.json().get('organizations', [])

        org = None
        for o in orgs:
            if o['name'].lower() == company_name.lower():
                org = o
                break
        if not org and orgs:
            org = orgs[0]
        if not org:
            return False

        org_id = org['id']

        # Get list entry
        entries_resp = requests.get(f'{AFFINITY_BASE_URL}/lists/{AFFINITY_LIST_ID}/list-entries',
                                   auth=AFFINITY_AUTH)
        entries = entries_resp.json()
        if isinstance(entries, list):
            entry = next((e for e in entries if e['entity_id'] == org_id), None)
        else:
            entry = next((e for e in entries.get('list_entries', []) if e['entity_id'] == org_id), None)

        if not entry:
            return False

        list_entry_id = entry['id']

        # Update ranking
        requests.post(
            f'{AFFINITY_BASE_URL}/field-values',
            auth=AFFINITY_AUTH,
            json={
                "field_id": FIELD_IDS["ranking"],
                "entity_id": org_id,
                "list_entry_id": list_entry_id,
                "value": score,
            }
        )

        # Update investor
        if investor in {"Rick", "Wes", "Lyndsey"}:
            for field in ["investor", "investors"]:
                requests.post(
                    f'{AFFINITY_BASE_URL}/field-values',
                    auth=AFFINITY_AUTH,
                    json={
                        "field_id": FIELD_IDS[field],
                        "entity_id": org_id,
                        "list_entry_id": list_entry_id,
                        "value": investor,
                    }
                )

        return True

    except Exception as e:
        print(f"  Affinity error for {company_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("Re-scoring PNP companies with Claude")
    print("=" * 60)

    # Load data
    with open('data/seed-data.json', 'r') as f:
        data = json.load(f)

    # Find PNP companies
    pnp_indices = []
    for i, c in enumerate(data['companies']):
        if 'PNP' in (c.get('source') or ''):
            pnp_indices.append(i)

    print(f"Found {len(pnp_indices)} PNP companies to re-score\n")

    scores_before = []
    scores_after = []

    for idx in pnp_indices:
        company = data['companies'][idx]
        name = company['name']
        old_score = company.get('weighted_total', 0)
        scores_before.append(old_score)

        print(f"Scoring: {name}...", end=" ", flush=True)

        result = score_company_with_claude(company)

        if result:
            new_score = result.get('score', old_score)
            theme = result.get('theme', 'Off-Thesis')
            justification = result.get('justification', '')
            investor = result.get('investor', '')

            # Update company data
            data['companies'][idx]['weighted_total'] = new_score
            data['companies'][idx]['thesis_fit_score'] = new_score
            data['companies'][idx]['thesis_fit_theme'] = theme
            data['companies'][idx]['thesis_fit_justification'] = justification
            if investor:
                data['companies'][idx]['owner'] = investor

            scores_after.append(new_score)

            # Update Affinity
            affinity_ok = update_affinity_score(name, new_score, investor)
            affinity_status = "✓" if affinity_ok else "⚠"

            change = new_score - old_score
            change_str = f"+{change:.1f}" if change > 0 else f"{change:.1f}"
            print(f"{old_score:.1f} → {new_score} ({change_str}) | {theme} | {investor} | Affinity:{affinity_status}")
        else:
            scores_after.append(old_score)
            print("FAILED")

        time.sleep(0.5)  # Rate limiting

    # Save updated data
    with open('data/seed-data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Before: Min={min(scores_before):.1f}, Max={max(scores_before):.1f}, Mean={sum(scores_before)/len(scores_before):.1f}")
    print(f"After:  Min={min(scores_after):.1f}, Max={max(scores_after):.1f}, Mean={sum(scores_after)/len(scores_after):.1f}")
    print(f"\nSaved to seed-data.json")
    print("Run: curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed")


if __name__ == "__main__":
    main()
