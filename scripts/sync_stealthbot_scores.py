#!/usr/bin/env python3
"""
Sync StealthBot companies with individual scores and thesis fit from CSV.
Estimates all 9 founder criteria based on methodology text and founder_score.
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
        "industrial", "construction", "infrastructure", "mining", "chemicals",
        "electrification", "ev", "hydrogen", "biomass", "waste"
    ],
    "Human Health": [
        "health", "healthcare", "medical", "medicine", "clinical", "patient",
        "biotech", "therapeutics", "drug", "pharma", "diagnostics", "cancer",
        "disease", "hospital", "wellness", "nutrition", "mental health",
        "longevity", "genomics", "personalized medicine", "medtech", "surgical",
        "physician", "doctor", "md", "nurse", "dental", "ortho"
    ],
    "Tomorrow's Workforce": [
        "education", "learning", "training", "workforce", "hr", "talent",
        "productivity", "ai assistant", "automation", "smb", "small business",
        "enterprise", "coaching", "career", "skill", "reskilling", "edtech",
        "hiring", "recruiting", "saas", "b2b software"
    ]
}

# All 9 criteria with positive signal keywords (boosts score)
CRITERIA_POSITIVE = {
    "breakthrough": [
        "innovative", "breakthrough", "novel", "contrarian", "unique", "pioneering",
        "first", "revolutionary", "disruptive", "cutting-edge", "advanced", "new approach",
        "patent", "invention", "research", "phd", "scientist", "r&d"
    ],
    "mission": [
        "mission", "purpose", "passion", "authentic", "personal connection", "motivated",
        "driven", "committed", "dedicated", "believes in", "cares about", "impact",
        "solve", "problem", "vision", "why"
    ],
    "achievements": [
        "award", "achievement", "exit", "published", "phd", "prestigious", "elite",
        "stanford", "harvard", "mit", "yc", "founder", "ceo", "vp", "director",
        "raised", "revenue", "growth", "scaled", "led", "built", "launched",
        "mba", "md", "jd", "top", "best", "recognized", "notable"
    ],
    "work_ethic": [
        "execution", "shipped", "built", "launched", "track record", "delivered",
        "experience", "years", "managed", "led", "implemented", "developed",
        "founded", "started", "created", "established", "grew", "scaled"
    ],
    "grit": [
        "resilient", "grit", "perseverance", "overcome", "adversity", "persistent",
        "determined", "tenacious", "challenges", "difficult", "tough", "survived",
        "bootstrapped", "self-funded", "pivoted", "rebuilt"
    ],
    "curiosity": [
        "curious", "learn", "research", "explore", "diverse", "multiple", "various",
        "phd", "academic", "studied", "degree", "education", "continuous learning",
        "self-taught", "breadth", "interests", "versatile"
    ],
    "magnetism": [
        "network", "connections", "leadership", "charisma", "attract", "talent",
        "influence", "presence", "community", "followers", "team", "hired",
        "recruited", "built team", "relationships", "well-connected", "advisor"
    ],
    "coachability": [
        "coachable", "learn", "adapt", "growth mindset", "self-aware", "feedback",
        "humble", "open", "flexible", "willing", "collaborative", "listens",
        "mentor", "advised", "improved", "evolved"
    ],
    "team_chemistry": [
        "team", "co-founder", "collaborate", "complementary", "chemistry",
        "partner", "together", "working with", "joined", "built team",
        "cross-functional", "diverse team", "leadership team"
    ]
}

# Negative signals (reduces score slightly)
NEGATIVE_SIGNALS = [
    "lacks", "no evidence", "limited", "unclear", "insufficient", "missing",
    "weak", "concern", "risk", "question", "doubt", "unknown", "unproven"
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
    return best if scores[best] >= 1 else "Neutral"

def estimate_criteria_scores(founder_score: float, methodology: str) -> dict:
    """
    Estimate all 9 criteria scores based on founder_score and methodology.
    Uses founder_score as baseline with adjustments based on keyword signals.
    """
    text = methodology.lower()
    base = founder_score

    # Count overall positive/negative tone
    negative_count = sum(1 for neg in NEGATIVE_SIGNALS if neg in text)
    is_negative_heavy = negative_count >= 3

    scores = {}
    for criterion, positive_keywords in CRITERIA_POSITIVE.items():
        # Start with base score
        score = base

        # Check for positive mentions - boost score
        positive_count = sum(1 for kw in positive_keywords if kw in text)

        if positive_count >= 3:
            score = min(10, base + 2.0)
        elif positive_count >= 2:
            score = min(10, base + 1.5)
        elif positive_count >= 1:
            score = min(10, base + 0.5)

        # Only penalize if there's specific negative mention for this criterion
        criterion_mentioned_negatively = False
        for neg in ["lacks", "no evidence", "limited", "weak"]:
            if neg in text:
                # Check if negative is near any of our keywords
                neg_pos = text.find(neg)
                context = text[neg_pos:neg_pos+80]
                if any(kw in context for kw in positive_keywords[:5]):
                    criterion_mentioned_negatively = True
                    break

        if criterion_mentioned_negatively:
            score = max(base - 1.0, score - 1.5)

        # Ensure reasonable bounds (don't go below 3 or above 10)
        score = max(3.0, min(10.0, score))

        # Round to 1 decimal
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
            # Still estimate scores for those not in CSV using existing bio
            if company.get("founders"):
                founder = company["founders"][0]
                existing_score = founder.get("founder_score", 5.0) or 5.0
                bio = founder.get("bio", "")
                if bio:
                    individual_scores = estimate_criteria_scores(existing_score, bio)
                    for field, score in individual_scores.items():
                        founder[field] = score
                    # Classify thesis from bio
                    thesis_theme = classify_thesis_fit(bio)
                    company["thesis_fit_theme"] = thesis_theme
                    thesis_counts[thesis_theme] += 1
                    print(f"  {company['name']} (from bio): score={existing_score}, theme={thesis_theme}")
                    updated += 1
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

            # Estimate all 9 criteria scores
            individual_scores = estimate_criteria_scores(founder_score, methodology)
            for field, score in individual_scores.items():
                founder[field] = score

            # Update bio with methodology
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
            match = re.match(r'(.+?)\s*<', owner)
            if match:
                company["owner"] = match.group(1).strip().split()[0]
            else:
                company["owner"] = owner.split()[0] if owner else None

        # For StealthBot (person-based entries), company_score = founder_score
        # since there's no company data, only founder data
        company["company_score"] = founder_score

        updated += 1
        if company.get("founders"):
            f = company["founders"][0]
            print(f"  {company['name']}: score={founder_score}, theme={thesis_theme}, "
                  f"break={f.get('breakthrough_score')}, curiosity={f.get('curiosity_score')}")

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Updated: {updated}")
    print(f"  Not found in CSV (used bio): {not_found}")
    print(f"  Thesis fit distribution:")
    for theme, count in thesis_counts.items():
        print(f"    {theme}: {count}")

if __name__ == "__main__":
    main()
