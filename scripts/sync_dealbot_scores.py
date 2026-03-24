#!/usr/bin/env python3
"""
Sync DealBot company scores from Affinity CSV export.
Rescales thesis score from 30-point to 10-point scale.
Maps founder scores to correct fields.
"""

import csv
import json
from pathlib import Path

CSV_PATH = "/Users/Ryan/Downloads/Dealbot_unsaved_view__export_Mar-24-2026.csv"
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed-data.json"

# CSV column -> founder field mapping
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

def safe_float(value, default=None):
    """Safely convert to float, returning default if empty/invalid."""
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
    weighted_sum = 0

    for field, weight in weights.items():
        score = company.get(field, 0) or 0
        weighted_sum += score * weight

    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0

def main():
    # Load CSV data
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

    # Track updates
    updated = 0
    not_found = 0

    for company in seed_data["companies"]:
        if company.get("source") != "DealBot (March 2026)":
            continue

        name = company["name"]
        csv_row = csv_data.get(name)

        if not csv_row:
            print(f"  Not found in CSV: {name}")
            not_found += 1
            continue

        # Update thesis_fit_score (rescale from 30 to 10)
        bv_rank = safe_float(csv_row.get("BV Rank 1-30"))
        if bv_rank is not None:
            company["thesis_fit_score"] = round(bv_rank / 3, 2)

        # Update founder scores
        if company.get("founders"):
            founder = company["founders"][0]  # Primary founder

            for csv_col, founder_field in FOUNDER_SCORE_MAP.items():
                score = safe_float(csv_row.get(csv_col))
                if score is not None:
                    founder[founder_field] = score

            # Update avg_founder_score on company
            founder_score = safe_float(csv_row.get("Founder Score Total"))
            if founder_score is not None:
                company["avg_founder_score"] = founder_score

            # Store founder score reasoning as bio if available
            reasoning = csv_row.get("Founder Score Reasoning", "").strip()
            if reasoning and not founder.get("bio"):
                founder["bio"] = reasoning

        # Recalculate company score
        company["company_score"] = calculate_company_score(company)

        updated += 1
        print(f"  Updated: {name} (thesis: {company['thesis_fit_score']}, company: {company['company_score']})")

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Updated: {updated}")
    print(f"  Not found: {not_found}")

if __name__ == "__main__":
    main()
