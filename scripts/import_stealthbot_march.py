#!/usr/bin/env python3
"""
Import StealthBot March 2026 people into seed-data.json as new company entries.
Reads 99 people from /tmp/stealthbot_march.json and appends them to the companies array.
"""

import json
from datetime import datetime, timezone

STEALTHBOT_PATH = "/tmp/stealthbot_march.json"
SEED_DATA_PATH = "/Users/wesleyselke/Dropbox/Claude Code/yc-deal-analysis/data/seed-data.json"

def main():
    # Load inputs
    with open(STEALTHBOT_PATH, "r") as f:
        stealthbot_people = json.load(f)

    with open(SEED_DATA_PATH, "r") as f:
        seed_data = json.load(f)

    companies = seed_data["companies"]

    # Determine starting IDs - use max of existing IDs and nextIds to avoid collisions
    max_company_id = max(c["id"] for c in companies) if companies else 0
    next_company_id = max(max_company_id + 1, seed_data["nextIds"]["company"])

    max_founder_id = 0
    for c in companies:
        for founder in c.get("founders", []):
            if "id" in founder and isinstance(founder["id"], (int, float)):
                max_founder_id = max(max_founder_id, founder["id"])
    next_founder_id = max(max_founder_id + 1, seed_data["nextIds"]["founder"])

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Loaded {len(stealthbot_people)} StealthBot people")
    print(f"Existing companies: {len(companies)}")
    print(f"Starting company ID: {next_company_id}")
    print(f"Starting founder ID: {next_founder_id}")

    new_companies = []
    current_company_id = next_company_id
    current_founder_id = next_founder_id

    for person in stealthbot_people:
        name = person.get("name", "Unknown")
        email = person.get("email") or ""
        fields = person.get("fields", {})

        # Try multiple email sources
        contact_email = fields.get("Email") or email
        if not contact_email and person.get("emails"):
            contact_email = person["emails"][0] if person["emails"] else ""

        linkedin = fields.get("LinkedIn") or ""
        title = fields.get("Title") or "Founder"
        founder_score = fields.get("Founder Score", 0) or 0
        score_methodology = fields.get("Score Methodology") or ""

        # Build founder_linkedin_data string: "Name::LinkedInURL::Email"
        founder_linkedin_data = f"{name}::{linkedin}::{contact_email}"

        # Build slug from name
        slug = name.lower().replace(" ", "-").replace("'", "").replace(".", "")

        # Create founder entry matching existing schema
        founder_entry = {
            "id": current_founder_id,
            "company_id": current_company_id,
            "name": name,
            "first_name": name.split()[0] if name.split() else "",
            "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "title": title,
            "linkedin": linkedin,
            "twitter": "",
            "avatar_url": "",
            "bio": score_methodology,
            "is_female": 0,
            "is_black": 0,
            "is_hispanic_latino": 0,
            "schools": "",
            "degrees": "",
            "prior_employers": "",
            "technical_competence": "",
            "publications_count": 0,
            "citations_count": 0,
            "awards": "",
            "patents": None,
            "is_repeat_founder": 0,
            "is_colocated": 0,
            "age_range": None,
            "created_at": now_str,
            "breakthrough_score": 0,
            "breakthrough_justification": "",
            "mission_score": 0,
            "mission_justification": "",
            "achievements_score": 0,
            "achievements_justification": "",
            "work_ethic_score": 0,
            "work_ethic_justification": "",
            "grit_score": 0,
            "grit_justification": "",
            "magnetism_score": 0,
            "magnetism_justification": "",
            "curiosity_score": 0,
            "curiosity_justification": "",
            "coachability_score": 0,
            "coachability_justification": "",
            "team_chemistry_score": 0,
            "team_chemistry_justification": "",
            "founder_score": founder_score
        }

        # Create company entry matching the full schema
        company_entry = {
            "id": current_company_id,
            "yc_id": None,
            "name": name,
            "slug": slug,
            "one_liner": "",
            "long_description": "",
            "batch": None,
            "status": "Not Contacted",
            "industries": "",
            "subindustry": "",
            "tags": "",
            "website": "",
            "all_locations": "",
            "team_size": 0,
            "year_founded": None,
            "logo_url": "",
            "b2b_b2c": None,
            "technology_type": None,
            "business_model": None,
            "next_action": None,
            "custom_tags": None,
            "created_at": now_str,
            "updated_at": now_str,
            "thesis_fit_theme": "Neutral",
            "owner": None,
            "team_score": 0,
            "team_weight": 15,
            "team_justification": "",
            "product_score": 0,
            "product_weight": 10,
            "product_justification": "",
            "business_model_score": 0,
            "business_model_weight": 10,
            "business_model_justification": "",
            "market_score": 0,
            "market_weight": 10,
            "market_justification": "",
            "impact_score": 0,
            "impact_weight": 20,
            "impact_justification": "",
            "traction_score": 0,
            "traction_weight": 5,
            "traction_justification": "",
            "deal_score": 0,
            "deal_weight": 5,
            "deal_justification": "",
            "thesis_fit_score": 0,
            "thesis_fit_weight": 25,
            "thesis_fit_justification": "",
            "company_score": 0,
            "founders": [founder_entry],
            "interactions": [],
            "notes": [],
            "contact_email": contact_email,
            "founder_names": name,
            "founder_linkedin_data": founder_linkedin_data,
            "has_female_founder": 0,
            "has_black_founder": 0,
            "has_hispanic_founder": 0,
            "last_interaction_date": None,
            "avg_founder_score": founder_score,
            "weighted_total": 0,
            "source": "StealthBot (March 2026)"
        }

        new_companies.append(company_entry)
        current_company_id += 1
        current_founder_id += 1

    # Append new companies
    companies.extend(new_companies)

    # Update nextIds
    seed_data["nextIds"]["company"] = current_company_id
    seed_data["nextIds"]["founder"] = current_founder_id

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print(f"\nAdded {len(new_companies)} new StealthBot companies")
    print(f"Total companies now: {len(companies)}")
    print(f"Updated nextIds: {seed_data['nextIds']}")
    print(f"ID range: {next_company_id} - {current_company_id - 1}")


if __name__ == "__main__":
    main()
