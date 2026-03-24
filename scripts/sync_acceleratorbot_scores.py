#!/usr/bin/env python3
"""
Sync non-PnP AcceleratorBot companies with thesis scores and owner from CSV.
"""

import csv
import json
import re
from pathlib import Path

CSV_PATH = "/Users/Ryan/Downloads/AcceleratorBot_unsaved_view__export_Mar-24-2026.csv"
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed-data.json"

# Map industry to Better Ventures thesis themes
INDUSTRY_TO_THEME = {
    # Sustainable Industry
    "electrification": "Sustainable Industry",
    "energy": "Sustainable Industry",
    "climate": "Sustainable Industry",
    "cleantech": "Sustainable Industry",
    "materials": "Sustainable Industry",
    "manufacturing": "Sustainable Industry",
    "food & ag": "Sustainable Industry",
    "agriculture": "Sustainable Industry",
    "circular economy": "Sustainable Industry",
    "bioeconomy": "Sustainable Industry",
    "buildings and construction": "Sustainable Industry",
    "construction": "Sustainable Industry",
    "industrial": "Sustainable Industry",

    # Human Health
    "health tech": "Human Health",
    "healthcare": "Human Health",
    "biotech": "Human Health",
    "medtech": "Human Health",
    "medical": "Human Health",
    "therapeutics": "Human Health",
    "diagnostics": "Human Health",
    "personalized health": "Human Health",
    "behavioral health": "Human Health",
    "longevity": "Human Health",

    # Tomorrow's Workforce
    "ai for smbs": "Tomorrow's Workforce",
    "workforce": "Tomorrow's Workforce",
    "education": "Tomorrow's Workforce",
    "learning": "Tomorrow's Workforce",
    "reskilling": "Tomorrow's Workforce",
    "productivity": "Tomorrow's Workforce",
    "hr tech": "Tomorrow's Workforce",
}

def classify_thesis_theme(industry: str) -> str:
    """Classify industry into Better Ventures thesis theme."""
    if not industry:
        return "Neutral"
    industry_lower = industry.lower().strip()
    return INDUSTRY_TO_THEME.get(industry_lower, "Neutral")

def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    return name.strip().lower()

def main():
    # Load CSV
    csv_data = {}
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip()
            if name:
                csv_data[normalize_name(name)] = row

    print(f"Loaded {len(csv_data)} companies from AcceleratorBot CSV")

    # Load seed data
    with open(SEED_DATA_PATH) as f:
        seed_data = json.load(f)

    updated = 0
    skipped_pnp = 0

    for company in seed_data["companies"]:
        if company.get("source") != "AcceleratorBot (March 2026)":
            continue

        name_key = normalize_name(company["name"])
        csv_row = csv_data.get(name_key)

        if not csv_row:
            continue

        # Skip PnP companies (they already have good data)
        batch = csv_row.get("batch_name", "")
        accel = csv_row.get("accelerator", "")
        if "PNP" in batch or "Plug" in accel:
            skipped_pnp += 1
            continue

        # Update thesis score from ranking (already on 1-9 scale, close to our 1-10)
        ranking = csv_row.get("ranking")
        if ranking:
            try:
                company["thesis_fit_score"] = float(ranking)
            except ValueError:
                pass

        # Update thesis theme from industry
        industry = csv_row.get("industry", "")
        thesis_theme = classify_thesis_theme(industry)
        company["thesis_fit_theme"] = thesis_theme

        # Update owner from investors field
        owner = csv_row.get("investors", "").strip()
        if owner:
            company["owner"] = owner

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
        print(f"  {company['name']}: thesis={company['thesis_fit_score']}, theme={thesis_theme}, owner={owner}")

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Updated non-PnP: {updated}")
    print(f"  Skipped PnP: {skipped_pnp}")

if __name__ == "__main__":
    main()
