#!/usr/bin/env python3
"""
Sync DealBot companies with enrichment data from Affinity CSV.
Includes: owner, email, total raised, thesis fit (LLM-classified), and scores.
"""

import csv
import json
import re
import os
from pathlib import Path

CSV_PATH = "/Users/Ryan/Downloads/Dealbot_unsaved_view__export_Mar-24-2026.csv"
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed-data.json"

# Better Ventures investment themes and keywords
THESIS_THEMES = {
    "Sustainable Industry": {
        "keywords": [
            "carbon", "climate", "energy", "renewable", "solar", "wind", "battery",
            "storage", "grid", "electrification", "ev", "electric vehicle",
            "recycling", "circular", "waste", "sustainability", "green",
            "bioeconomy", "biofuel", "biomass", "biomanufacturing", "fermentation",
            "materials", "manufacturing", "industrial", "chemicals", "polymer",
            "agriculture", "farming", "food production", "agtech", "agritech",
            "water", "cleantech", "decarbonization", "emissions", "net zero",
            "hydrogen", "ammonia", "mining", "minerals", "construction"
        ],
        "score": 0
    },
    "Human Health": {
        "keywords": [
            "health", "healthcare", "medical", "medicine", "clinical", "patient",
            "biotech", "therapeutics", "drug", "pharma", "pharmaceutical",
            "diagnostics", "diagnostic", "cancer", "oncology", "disease",
            "hospital", "clinic", "care", "treatment", "therapy",
            "mental health", "behavioral", "wellness", "nutrition", "diet",
            "longevity", "aging", "chronic", "diabetes", "cardiovascular",
            "genomics", "genetics", "personalized medicine", "precision medicine",
            "medtech", "medical device", "implant", "surgical", "radiology"
        ],
        "score": 0
    },
    "Tomorrow's Workforce": {
        "keywords": [
            "education", "learning", "training", "skill", "workforce",
            "hr", "human resources", "talent", "hiring", "recruiting",
            "productivity", "automation", "ai assistant", "workflow",
            "smb", "small business", "enterprise software", "saas",
            "coaching", "mentoring", "career", "professional development",
            "reskilling", "upskilling", "credential", "certification"
        ],
        "score": 0
    }
}

def classify_thesis_fit(description: str, keywords: str, name: str) -> str:
    """Classify company into Better Ventures thesis theme using keyword matching."""
    text = f"{name} {description} {keywords}".lower()

    scores = {theme: 0 for theme in THESIS_THEMES}

    for theme, config in THESIS_THEMES.items():
        for keyword in config["keywords"]:
            if keyword in text:
                scores[theme] += 1
                # Boost for exact word matches
                if re.search(rf'\b{re.escape(keyword)}\b', text):
                    scores[theme] += 1

    # Find best match
    best_theme = max(scores, key=scores.get)
    best_score = scores[best_theme]

    # Only return theme if we have meaningful matches
    if best_score >= 2:
        return best_theme
    return "Neutral"

def parse_owner(owner_str: str) -> tuple:
    """Parse 'Name <email>' format into (name, email)."""
    if not owner_str:
        return None, None

    match = re.match(r'(.+?)\s*<(.+?)>', owner_str)
    if match:
        name = match.group(1).strip()
        email = match.group(2).strip()
        # Extract first name only
        first_name = name.split()[0] if name else None
        return first_name, email
    return owner_str.strip(), None

def parse_total_raised(raised_str: str) -> str:
    """Parse total raised into displayable format."""
    if not raised_str:
        return None
    try:
        amount = float(raised_str)
        if amount >= 1000:
            return f"${amount/1000:.1f}B"
        elif amount >= 1:
            return f"${amount:.1f}M"
        else:
            return f"${amount*1000:.0f}K"
    except (ValueError, TypeError):
        return raised_str

def safe_float(value, default=None):
    """Safely convert to float."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_company_score(company):
    """Recalculate weighted company score."""
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
    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0

# Founder score field mapping
FOUNDER_SCORE_MAP = {
    "Founder Score Total": "founder_score",
    "Founder Breakthrough": "breakthrough_score",
    "Founder Mission": "mission_score",
    "Founder Achievements": "achievements_score",
    "Founder Execution": "work_ethic_score",
    "Founder Grit": "grit_score",
    "Founder Magnetism": "magnetism_score",
    "Founder Coachability": "coachability_score",
    "Founder Team": "team_chemistry_score",
}

def main():
    # Load CSV
    csv_data = {}
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip()
            if name:
                csv_data[name] = row

    print(f"Loaded {len(csv_data)} companies from CSV")

    # Load seed data
    with open(SEED_DATA_PATH) as f:
        seed_data = json.load(f)

    updated = 0
    thesis_counts = {"Sustainable Industry": 0, "Human Health": 0, "Tomorrow's Workforce": 0, "Neutral": 0}

    for company in seed_data["companies"]:
        if company.get("source") != "DealBot (March 2026)":
            continue

        name = company["name"]
        csv_row = csv_data.get(name)
        if not csv_row:
            continue

        # Parse owner
        owner_name, owner_email = parse_owner(csv_row.get("Owners", ""))
        if owner_name:
            company["owner"] = owner_name
        if owner_email:
            company["contact_email"] = owner_email

        # Parse total raised
        total_raised = parse_total_raised(csv_row.get("Pb Total Raised"))
        if total_raised:
            company["total_raised"] = total_raised

        # Classify thesis fit
        description = csv_row.get("Pb Description", "")
        keywords = csv_row.get("Pb Keywords", "")
        thesis_theme = classify_thesis_fit(description, keywords, name)
        company["thesis_fit_theme"] = thesis_theme
        thesis_counts[thesis_theme] += 1

        # Update thesis_fit_score based on theme match
        bv_rank = safe_float(csv_row.get("BV Rank 1-30"))
        if bv_rank is not None:
            company["thesis_fit_score"] = round(bv_rank / 3, 2)

        # Update founder scores
        if company.get("founders"):
            founder = company["founders"][0]
            for csv_col, founder_field in FOUNDER_SCORE_MAP.items():
                score = safe_float(csv_row.get(csv_col))
                if score is not None:
                    founder[founder_field] = score

            founder_score = safe_float(csv_row.get("Founder Score Total"))
            if founder_score is not None:
                company["avg_founder_score"] = founder_score

            # Add reasoning as bio if empty
            reasoning = csv_row.get("Founder Score Reasoning", "").strip()
            if reasoning and not founder.get("bio"):
                founder["bio"] = reasoning

        # Recalculate company score
        company["company_score"] = calculate_company_score(company)

        updated += 1
        print(f"  {name}: {thesis_theme}, owner={owner_name}, raised={total_raised}")

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Updated: {updated}")
    print(f"  Thesis fit distribution:")
    for theme, count in thesis_counts.items():
        print(f"    {theme}: {count}")

if __name__ == "__main__":
    main()
