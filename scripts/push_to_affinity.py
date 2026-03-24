#!/usr/bin/env python3
"""
Push companies from yc-deal-analysis SQLite database to Affinity CRM.

Usage:
    python scripts/push_to_affinity.py [--dry-run] [--source "PNP (3/20/26)"] [--limit 10]

Environment variables required:
    AFFINITY_API_KEY - Your Affinity API key
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Affinity configuration (same as BV-Acceleratorbot)
AFFINITY_API_KEY = os.getenv("AFFINITY_API_KEY")
AFFINITY_BASE_URL = "https://api.affinity.co"
AFFINITY_AUTH = ('', AFFINITY_API_KEY) if AFFINITY_API_KEY else None

AFFINITY_LIST_ID = 324289
AFFINITY_FIELD_IDS = {
    "company_url": 5418321,
    "contact_name": 5561645,
    "contact_email": 5500551,
    "contact_position": 5561646,
    "contact_linkedin": 5582251,
    "description": 5418322,
    "batch_name": 5418323,
    "year_season": 5418324,
    "accelerator": 5418325,
    "industry": 5418326,
    "investor": 5418327,
    "investors": 5572905,
    "ranking": 5458698,
    "date_last_updated": 5418329,
}

VALID_INVESTORS = {"Rick", "Wes", "Lyndsey"}


@dataclass
class Company:
    """Company data for Affinity."""
    company_name: str
    company_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_position: Optional[str] = None
    contact_linkedin: Optional[str] = None
    description: Optional[str] = None
    batch_name: str = "N/A"
    year_season: str = "N/A"
    accelerator: str = "YC"
    industry: Optional[str] = None
    investor: Optional[str] = None
    ranking: int = 0
    date_last_updated: str = ""
    thesis_fit_theme: Optional[str] = None


def get_data_path() -> str:
    """Get the path to the seed data JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'seed-data.json')


def fetch_companies(source_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Company]:
    """Fetch companies from seed-data.json file."""
    data_path = get_data_path()

    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        sys.exit(1)

    with open(data_path, 'r') as f:
        data = json.load(f)

    raw_companies = data.get('companies', [])

    # Filter by source if specified
    if source_filter:
        raw_companies = [c for c in raw_companies if c.get('source') == source_filter]

    # Sort by weighted_total descending
    raw_companies.sort(key=lambda c: c.get('weighted_total') or 0, reverse=True)

    # Apply limit
    if limit:
        raw_companies = raw_companies[:limit]

    companies = []
    for row in raw_companies:
        # Parse batch to year_season
        batch = row.get('batch') or ''
        year_season = batch
        if 'Winter' in batch or batch.startswith('W'):
            year_season = "2026 Winter"
        elif 'Summer' in batch or batch.startswith('S'):
            year_season = "2026 Summer"

        # Determine accelerator from source
        source = row.get('source') or ''
        if 'YC' in source:
            accelerator = "YC"
        elif 'Deepchecks' in source:
            accelerator = "Deepchecks"
        elif 'PNP' in source:
            accelerator = "Plug and Play"
        else:
            accelerator = source or "YC"

        # Map owner to investor
        owner = row.get('owner')
        investor = owner if owner in VALID_INVESTORS else None

        # Convert weighted_total to ranking (already 0-10 scale)
        weighted = row.get('weighted_total') or 0
        ranking = round(weighted) if weighted > 0 else 0

        # Get first founder info
        founders = row.get('founders', [])
        first_founder = founders[0] if founders else {}

        # Also check founder_linkedin_data for contact info
        founder_data = row.get('founder_linkedin_data', '')
        contact_name = first_founder.get('name')
        contact_linkedin = first_founder.get('linkedin')
        contact_email = first_founder.get('email') or row.get('contact_email')
        contact_position = first_founder.get('title')

        # Parse founder_linkedin_data if we don't have founder info
        if not contact_name and founder_data:
            # Format: "Name::LinkedInURL::Email|||Name2::LinkedInURL2::Email2"
            parts = founder_data.split('|||')[0].split('::')
            if len(parts) >= 1:
                contact_name = parts[0]
            if len(parts) >= 2:
                contact_linkedin = parts[1] or contact_linkedin
            if len(parts) >= 3:
                contact_email = parts[2] or contact_email

        # Build description with thesis fit theme
        one_liner = row.get('one_liner') or ''
        thesis_theme = row.get('thesis_fit_theme') or ''
        description = one_liner
        if thesis_theme and thesis_theme not in ('Neutral', 'Off-Thesis'):
            description = f"[{thesis_theme}] {one_liner}"

        company = Company(
            company_name=row.get('name'),
            company_url=row.get('website'),
            contact_name=contact_name,
            contact_email=contact_email,
            contact_position=contact_position,
            contact_linkedin=contact_linkedin,
            description=description,
            batch_name=batch or "W26",
            year_season=year_season,
            accelerator=accelerator,
            industry=row.get('industries'),
            investor=investor,
            ranking=ranking,
            date_last_updated=datetime.now().strftime("%m-%d-%Y"),
            thesis_fit_theme=thesis_theme,
        )
        companies.append(company)

    return companies


def find_or_create_organization(name: str, domain: Optional[str]) -> int:
    """Find or create an organization in Affinity."""
    # Search for existing organization
    response = requests.get(
        f"{AFFINITY_BASE_URL}/organizations",
        auth=AFFINITY_AUTH,
        params={"term": name}
    )

    orgs = response.json().get('organizations', [])

    # If found, return existing org ID
    if orgs:
        for org in orgs:
            if domain and org.get('domain') == domain:
                return org['id']
            if org['name'].lower() == name.lower():
                return org['id']

    # Not found, create new organization
    response = requests.post(
        f"{AFFINITY_BASE_URL}/organizations",
        auth=AFFINITY_AUTH,
        json={"name": name, "domain": domain}
    )
    return response.json()['id']


def write_company_to_affinity(company: Company, dry_run: bool = False) -> bool:
    """Write a single company to Affinity."""
    if dry_run:
        print(f"[DRY RUN] Would add: {company.company_name} (ranking: {company.ranking}, investor: {company.investor})")
        return True

    try:
        # 1. Find or create organization
        org_id = find_or_create_organization(
            company.company_name,
            company.company_url
        )

        # 2. Add to list (skip if already in list)
        try:
            entry_response = requests.post(
                f"{AFFINITY_BASE_URL}/lists/{AFFINITY_LIST_ID}/list-entries",
                auth=AFFINITY_AUTH,
                json={"entity_id": org_id}
            )
            entry_response.raise_for_status()
            list_entry_id = entry_response.json()['id']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:  # Duplicate entry
                entries_response = requests.get(
                    f"{AFFINITY_BASE_URL}/lists/{AFFINITY_LIST_ID}/list-entries",
                    auth=AFFINITY_AUTH
                )
                entries = entries_response.json().get('list_entries', [])
                entry = next((e for e in entries if e['entity_id'] == org_id), None)
                if entry:
                    list_entry_id = entry['id']
                else:
                    raise
            else:
                raise

        # 3. Update fields
        field_values = {
            "company_url": company.company_url,
            "contact_name": company.contact_name,
            "contact_email": company.contact_email,
            "contact_position": company.contact_position,
            "contact_linkedin": company.contact_linkedin,
            "description": company.description,
            "batch_name": company.batch_name,
            "year_season": company.year_season,
            "accelerator": company.accelerator,
            "industry": company.industry,
            "investor": company.investor,
            "ranking": company.ranking,
            "date_last_updated": company.date_last_updated,
        }

        for field_name, value in field_values.items():
            if value is not None and value != "" and field_name in AFFINITY_FIELD_IDS:
                response = requests.post(
                    f"{AFFINITY_BASE_URL}/field-values",
                    auth=AFFINITY_AUTH,
                    json={
                        "field_id": AFFINITY_FIELD_IDS[field_name],
                        "entity_id": org_id,
                        "list_entry_id": list_entry_id,
                        "value": value,
                    },
                    timeout=10,
                )
                if not response.ok:
                    print(f"  ⚠️  Field '{field_name}' failed for {company.company_name}: {response.status_code}")

        # 4. Write to investors multi-select dropdown
        if company.investor and company.investor in VALID_INVESTORS:
            response = requests.post(
                f"{AFFINITY_BASE_URL}/field-values",
                auth=AFFINITY_AUTH,
                json={
                    "field_id": AFFINITY_FIELD_IDS["investors"],
                    "entity_id": org_id,
                    "list_entry_id": list_entry_id,
                    "value": company.investor,
                },
                timeout=10,
            )
            if not response.ok:
                print(f"  ⚠️  Field 'investors' failed for {company.company_name}: {response.status_code}")

        print(f"✓ Added/Updated {company.company_name}")
        return True

    except Exception as e:
        print(f"✗ Failed to add {company.company_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Push companies to Affinity CRM")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--source", type=str, help="Filter by source (e.g., 'PNP (3/20/26)')")
    parser.add_argument("--limit", type=int, help="Limit number of companies")
    parser.add_argument("--min-ranking", type=int, default=0, help="Minimum ranking score (0-10)")
    args = parser.parse_args()

    if not AFFINITY_API_KEY and not args.dry_run:
        print("Error: AFFINITY_API_KEY environment variable not set")
        print("Set it with: export AFFINITY_API_KEY='your-api-key'")
        sys.exit(1)

    print("=" * 60)
    print("🚀 Pushing companies to Affinity")
    print("=" * 60)

    if args.source:
        print(f"📁 Source filter: {args.source}")
    if args.limit:
        print(f"📊 Limit: {args.limit}")
    if args.min_ranking > 0:
        print(f"⭐ Min ranking: {args.min_ranking}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    print()

    # Fetch companies
    companies = fetch_companies(source_filter=args.source, limit=args.limit)

    # Filter by ranking
    if args.min_ranking > 0:
        companies = [c for c in companies if c.ranking >= args.min_ranking]

    print(f"Found {len(companies)} companies to push\n")

    if not companies:
        print("No companies to push.")
        return

    # Push to Affinity
    success_count = 0
    for company in companies:
        if write_company_to_affinity(company, dry_run=args.dry_run):
            success_count += 1

    print()
    print("=" * 60)
    print(f"✅ Successfully processed {success_count}/{len(companies)} companies")
    print("=" * 60)


if __name__ == "__main__":
    main()
