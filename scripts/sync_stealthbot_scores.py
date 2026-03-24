#!/usr/bin/env python3
"""
Sync StealthBot companies with individual scores and thesis fit from CSV.
Distributes founder_score across individual criteria and classifies thesis fit
based on methodology text.
"""

import csv
import json
import re
from pathlib import Path

CSV_PATH = "/Users/Ryan/Downloads/StealthBot_Outreach_unsaved_view__export_Mar-24-2026.csv"
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed-data.json"

# Keywords for thesis fit classification from background/methodology
THESIS_KEYWORDS = {
    "Sustainable Industry": [
        "climate", "carbon", "energy", "renewable", "solar", "battery", "grid",
        "sustainability", "green", "cleantech", "manufacturing", "materials",
        "agriculture", "farming", "food production", "circular", "recycling",
        "industrial", "construction", "infrastructure", "mining", "chemicals"
    ],
    "Human Health": [
        "health", "healthcare", "medical", "medicine", "clinical", "patient",
        "biotech", "therapeutics", "drug", "pharma", "diagnostics", "cancer",
        "disease", "hospital", "wellness", "nutrition", "mental health",
        "longevity", "genomics", "personalized medicine", "medtech"
    ],
    "Tomorrow's Workforce": [
        "education", "learning", "training", "workforce", "hr", "talent",
        "productivity", "ai assistant", "automation", "smb", "small business",
        "enterprise", "coaching", "career", "skill", "reskilling"
    ]
}

# Score criteria and their typical weight in methodology mentions
SCORE_CRITERIA = [
    ("breakthrough", ["innovative", "breakthrough", "novel", "contrarian", "unique", "pioneering"]),
    ("mission", ["mission", "purpose", "passion", "authentic", "personal connection", "motivated"]),
    ("achievements", ["award", "achievement", "exit", "published", "phd", "prestigious", "elite", "stanford", "harvard", "mit", "yc"]),
    ("work_ethic", ["execution", "shipped", "built", "launched", "track record", "delivered", "experience"]),
    ("grit", ["resilient", "grit", "perseverance", "overcome", "adversity", "persistent"]),
    ("magnetism", ["network", "connections", "leadership", "charisma", "attract", "talent"]),
    ("coachability", ["coachable", "learn", "adapt", "growth mindset", "self-aware", "feedback"]),
    ("team_chemistry", ["team", "co-founder", "collaborate", "complementary", "chemistry"])
]

def classify_thesis_fit(methodology: str) -> str:
    """Classify thesis fit based on methodology text."""
    text = methodology.lower()
    scores = {theme: 0 for theme in THESIS_KEYWORDS}

    for theme, keywords in THESIS_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[theme] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "Neutral"

def distribute_scores(founder_score: float, methodology: str) -> dict:
    """
    Distribute founder_score across individual criteria based on methodology mentions.
    Uses base score with adjustments based on keyword presence.
    """
    text = methodology.lower()
    base_score = founder_score

    scores = {}
    for criterion, keywords in SCORE_CRITERIA:
        # Start with base score
        score = base_score

        # Check for positive mentions
        positive_count = sum(1 for kw in keywords if kw in text)
        if positive_count >= 2:
            score = min(10, base_score + 1.5)
        elif positive_count == 1:
            score = min(10, base_score + 0.5)

        # Check for negative mentions
        if "lacks" in text and any(kw in text[text.find("lacks"):text.find("lacks")+50] for kw in keywords):
            score = max(1, base_score - 1.5)
        elif "no evidence" in text and any(kw in text[text.find("no evidence"):text.find("no evidence")+50] for kw in keywords):
            score = max(1, base_score - 1)
        elif "limited" in text and any(kw in text[text.find("limited"):text.find("limited")+50] for kw in keywords):
            score = max(1, base_score - 0.5)

        scores[f"{criterion}_score"] = round(score, 1)

    return scores

def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    return name.strip().lower()

def main():
    # Load CSV
    csv_data = {}
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Full Name", "").strip()
            if name:
                csv_data[normalize_name(name)] = row

    print(f"Loaded {len(csv_data)} people from StealthBot CSV")

    # Load seed data
    with open(SEED_DATA_PATH) as f:
        seed_data = json.load(f)

    updated = 0
    not_found = 0
    thesis_counts = {"Sustainable Industry": 0, "Human Health": 0, "Tomorrow's Workforce": 0, "Neutral": 0}

    for company in seed_data["companies"]:
        if "StealthBot" not in company.get("source", ""):
            continue

        # Company name is founder name for StealthBot
        name_key = normalize_name(company["name"])
        csv_row = csv_data.get(name_key)

        if not csv_row:
            not_found += 1
            continue

        methodology = csv_row.get("Score Methodology", "")
        founder_score_csv = csv_row.get("Founder Score")

        # Update founder score if available
        if founder_score_csv:
            try:
                founder_score = float(founder_score_csv)
            except ValueError:
                founder_score = 5.0
        else:
            founder_score = 5.0

        # Update founder with individual scores
        if company.get("founders"):
            founder = company["founders"][0]
            founder["founder_score"] = founder_score

            # Distribute scores across criteria
            individual_scores = distribute_scores(founder_score, methodology)
            for field, score in individual_scores.items():
                founder[field] = score

            # Update bio with methodology if different
            if methodology:
                founder["bio"] = methodology

        # Classify thesis fit
        thesis_theme = classify_thesis_fit(methodology)
        company["thesis_fit_theme"] = thesis_theme
        thesis_counts[thesis_theme] += 1

        # Update avg_founder_score
        company["avg_founder_score"] = founder_score

        # Set owner from CSV if available
        owner = csv_row.get("Owners", "").strip()
        if owner:
            # Parse "Name <email>" format
            match = re.match(r'(.+?)\s*<', owner)
            if match:
                company["owner"] = match.group(1).strip().split()[0]
            else:
                company["owner"] = owner.split()[0] if owner else None

        # Recalculate company score
        weights = {
            "team_score": company.get("team_weight", 15),
            "product_score": company.get("product_weight", 10),
            "business_model_score": company.get("business_model_weight", 10),
            "market_score": company.get("market_weight", 10),
            "impact_score": company.get("impact_weight", 20),
            "traction_score": company.get("traction_weight", 5),
            "deal_score": company.get("deal_weight", 5),
            "thesis_fit_score": company.get("thesis_fit_weight", 25),
        }
        total_weight = sum(weights.values())
        weighted_sum = sum((company.get(f, 0) or 0) * w for f, w in weights.items())
        company["company_score"] = round(weighted_sum / total_weight, 2)

        updated += 1
        if company.get("founders"):
            f = company["founders"][0]
            print(f"  {company['name']}: score={founder_score}, theme={thesis_theme}, breakthrough={f.get('breakthrough_score')}")

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Updated: {updated}")
    print(f"  Not found in CSV: {not_found}")
    print(f"  Thesis fit distribution:")
    for theme, count in thesis_counts.items():
        print(f"    {theme}: {count}")

if __name__ == "__main__":
    main()
