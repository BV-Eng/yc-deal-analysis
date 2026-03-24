#!/usr/bin/env python3
"""
Restore 34 enriched PnP companies from git backup, replacing the less-enriched
AcceleratorBot duplicates. Tags restored companies with dual source.
"""

import json
from pathlib import Path

PNP_BACKUP_PATH = "/tmp/pnp_backup.json"
SEED_DATA_PATH = Path(__file__).parent.parent / "data" / "seed-data.json"

def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    return name.strip().lower()

def main():
    # Load PnP backup (from git commit 848f62e)
    with open(PNP_BACKUP_PATH) as f:
        pnp_data = json.load(f)

    # Load current seed data
    with open(SEED_DATA_PATH) as f:
        seed_data = json.load(f)

    # Extract PnP companies from backup
    pnp_companies = {
        normalize_name(c["name"]): c
        for c in pnp_data["companies"]
        if "PNP" in c.get("source", "")
    }

    print(f"Loaded {len(pnp_companies)} PnP companies from backup")

    # Track what we do
    replaced = 0
    kept_accel_only = 0

    # Process current companies
    updated_companies = []
    for company in seed_data["companies"]:
        source = company.get("source", "")
        name_key = normalize_name(company["name"])

        # Check if this is an AcceleratorBot company that matches a PnP company
        if "AcceleratorBot" in source and name_key in pnp_companies:
            # Get enriched PnP version
            pnp_company = pnp_companies[name_key].copy()

            # Preserve AcceleratorBot's ID to avoid breaking references
            pnp_company["id"] = company["id"]

            # Update founder IDs to match current
            if pnp_company.get("founders") and company.get("founders"):
                for i, founder in enumerate(pnp_company["founders"]):
                    if i < len(company["founders"]):
                        founder["id"] = company["founders"][i]["id"]
                        founder["company_id"] = company["id"]

            # Set dual source tag
            pnp_company["source"] = "PNP (3/20/26), AcceleratorBot (March 2026)"

            updated_companies.append(pnp_company)
            replaced += 1
            print(f"  Replaced: {company['name']}")
        else:
            # Keep as is (non-PnP AcceleratorBot or other source)
            if "AcceleratorBot" in source:
                kept_accel_only += 1
            updated_companies.append(company)

    # Update seed data
    seed_data["companies"] = updated_companies

    # Write back
    with open(SEED_DATA_PATH, "w") as f:
        json.dump(seed_data, f, indent=2)

    print()
    print(f"Summary:")
    print(f"  Replaced with enriched PnP data: {replaced}")
    print(f"  Kept AcceleratorBot-only: {kept_accel_only}")
    print(f"  Total companies: {len(updated_companies)}")

if __name__ == "__main__":
    main()
