#!/usr/bin/env python3
"""
Pull company data from Affinity CRM back into the Deal Analysis tool.

Syncs: Owner (investor), Contact Name, Contact Email, Contact LinkedIn,
       Thesis Fit Theme, and Founder info from Affinity into seed-data.json.

Usage:
    python scripts/pull_from_affinity.py [--dry-run] [--limit 10]

Environment variables required:
    AFFINITY_API_KEY - Your Affinity API key
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

# Affinity configuration (matches push_to_affinity.py)
AFFINITY_API_KEY = os.getenv("AFFINITY_API_KEY")
AFFINITY_BASE_URL = "https://api.affinity.co"
AFFINITY_AUTH = ('', AFFINITY_API_KEY) if AFFINITY_API_KEY else None

AFFINITY_LIST_ID = 324289

# Field IDs -> field names (reverse of push script)
AFFINITY_FIELD_IDS = {
    5418321: "company_url",
    5561645: "contact_name",
    5500551: "contact_email",
    5561646: "contact_position",
    5582251: "contact_linkedin",
    5418322: "description",
    5418323: "batch_name",
    5418324: "year_season",
    5418325: "accelerator",
    5418326: "industry",
    5418327: "investor",       # Single investor (owner)
    5572905: "investors",      # Multi-select dropdown
    5458698: "ranking",
    5418329: "date_last_updated",
}

VALID_OWNERS = {"Rick", "Wes", "Lyndsey"}


def get_data_path() -> str:
    """Get the path to the seed data JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '..', 'data', 'seed-data.json')


def fetch_affinity_list_entries() -> List[Dict[str, Any]]:
    """Fetch all list entries from the Affinity list."""
    entries = []
    page_token = None

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token

        response = requests.get(
            f"{AFFINITY_BASE_URL}/lists/{AFFINITY_LIST_ID}/list-entries",
            auth=AFFINITY_AUTH,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        batch = data.get('list_entries', data) if isinstance(data, dict) else data
        if isinstance(batch, list):
            entries.extend(batch)
        elif isinstance(data, dict) and 'list_entries' in data:
            entries.extend(data['list_entries'])
        else:
            entries.extend([data] if isinstance(data, dict) and 'id' in data else [])

        # Check for pagination
        if isinstance(data, dict) and data.get('next_page_token'):
            page_token = data['next_page_token']
        else:
            break

    return entries


def fetch_field_values_for_entry(list_entry_id: int) -> Dict[str, Any]:
    """Fetch all field values for a specific list entry."""
    response = requests.get(
        f"{AFFINITY_BASE_URL}/field-values",
        auth=AFFINITY_AUTH,
        params={"list_entry_id": list_entry_id},
        timeout=30,
    )
    response.raise_for_status()
    values = response.json()

    # Parse field values into a dict
    result = {}
    for fv in values:
        field_id = fv.get('field_id')
        value = fv.get('value')
        field_name = AFFINITY_FIELD_IDS.get(field_id)
        if field_name and value:
            # Handle dropdown values (they come as objects with 'text' key)
            if isinstance(value, dict):
                value = value.get('text', value.get('value', str(value)))
            result[field_name] = value

    return result


def fetch_organization_name(org_id: int) -> Optional[str]:
    """Get organization name from Affinity."""
    try:
        response = requests.get(
            f"{AFFINITY_BASE_URL}/organizations/{org_id}",
            auth=AFFINITY_AUTH,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data.get('name')
    except Exception:
        return None


def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    return (name or '').strip().lower().replace(',', '').replace('.', '').replace(' inc', '').replace(' llc', '')


def match_company(affinity_name: str, affinity_url: str, local_companies: List[Dict]) -> Optional[int]:
    """Find matching local company by name or URL. Returns index or None."""
    norm_aff = normalize_name(affinity_name)

    # Try exact name match first
    for i, c in enumerate(local_companies):
        if normalize_name(c.get('name', '')) == norm_aff:
            return i

    # Try URL match
    if affinity_url:
        aff_domain = affinity_url.replace('https://', '').replace('http://', '').rstrip('/')
        for i, c in enumerate(local_companies):
            local_url = (c.get('website') or '').replace('https://', '').replace('http://', '').rstrip('/')
            if local_url and aff_domain and local_url == aff_domain:
                return i

    # Try fuzzy name match (contains)
    for i, c in enumerate(local_companies):
        local_norm = normalize_name(c.get('name', ''))
        if local_norm and norm_aff and (local_norm in norm_aff or norm_aff in local_norm):
            return i

    return None


def pull_from_affinity(dry_run: bool = False, limit: Optional[int] = None):
    """Pull data from Affinity and update local seed data."""
    data_path = get_data_path()

    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}")
        sys.exit(1)

    with open(data_path, 'r') as f:
        local_data = json.load(f)

    local_companies = local_data.get('companies', [])
    print(f"Local companies: {len(local_companies)}")

    # Fetch Affinity list entries
    print("Fetching Affinity list entries...")
    entries = fetch_affinity_list_entries()
    print(f"Affinity entries: {len(entries)}")

    if limit:
        entries = entries[:limit]

    updated_count = 0
    not_found_count = 0
    changes_log = []

    for entry in entries:
        entity_id = entry.get('entity_id')
        list_entry_id = entry.get('id')

        if not entity_id or not list_entry_id:
            continue

        # Get organization name
        org_name = fetch_organization_name(entity_id)
        if not org_name:
            continue

        # Get field values
        try:
            field_values = fetch_field_values_for_entry(list_entry_id)
        except Exception as e:
            print(f"  ⚠️  Failed to fetch fields for {org_name}: {e}")
            continue

        # Match to local company
        affinity_url = field_values.get('company_url', '')
        idx = match_company(org_name, affinity_url, local_companies)

        if idx is None:
            not_found_count += 1
            continue

        company = local_companies[idx]
        changes = []

        # --- Sync Owner (investor field) ---
        investor = field_values.get('investor') or field_values.get('investors')
        if investor and investor in VALID_OWNERS:
            if company.get('owner') != investor:
                changes.append(f"owner: '{company.get('owner')}' -> '{investor}'")
                if not dry_run:
                    company['owner'] = investor

        # --- Sync Contact Email ---
        contact_email = field_values.get('contact_email')
        if contact_email:
            if company.get('contact_email') != contact_email:
                changes.append(f"contact_email: '{company.get('contact_email', '')}' -> '{contact_email}'")
                if not dry_run:
                    company['contact_email'] = contact_email

        # --- Sync Contact Name (update first founder) ---
        contact_name = field_values.get('contact_name')
        if contact_name:
            founders = company.get('founders', [])
            if founders:
                # Check if this name matches any existing founder
                found_match = False
                for founder in founders:
                    if normalize_name(founder.get('name', '')) == normalize_name(contact_name):
                        found_match = True
                        # Update email on matched founder if we have it
                        if contact_email and not founder.get('email'):
                            changes.append(f"founder[{founder['name']}].email: '' -> '{contact_email}'")
                            if not dry_run:
                                founder['email'] = contact_email
                        break

        # --- Sync Contact LinkedIn ---
        contact_linkedin = field_values.get('contact_linkedin')
        if contact_linkedin:
            founders = company.get('founders', [])
            if founders:
                # Update first founder's linkedin if empty
                first_founder = founders[0]
                if not first_founder.get('linkedin') and contact_linkedin:
                    changes.append(f"founder[{first_founder.get('name','')}].linkedin: '' -> '{contact_linkedin}'")
                    if not dry_run:
                        first_founder['linkedin'] = contact_linkedin

            # Also rebuild founder_linkedin_data string
            if not dry_run and founders:
                parts = []
                for f in founders:
                    parts.append(f"{f.get('name','')}::{f.get('linkedin','')}::{f.get('email','')}")
                company['founder_linkedin_data'] = '|||'.join(parts)

        if changes:
            updated_count += 1
            changes_log.append((company['name'], changes))
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"  {prefix}✓ {company['name']}: {', '.join(changes)}")

    # Save updated data
    if not dry_run and updated_count > 0:
        with open(data_path, 'w') as f:
            json.dump(local_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved updates to {data_path}")

    print(f"\n{'=' * 60}")
    print(f"📊 Summary:")
    print(f"   Entries processed: {len(entries)}")
    print(f"   Companies updated: {updated_count}")
    print(f"   Not found locally: {not_found_count}")
    if dry_run:
        print(f"   ⚠️  DRY RUN - no changes were saved")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Pull company data from Affinity CRM")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--limit", type=int, help="Limit number of entries to process")
    args = parser.parse_args()

    if not AFFINITY_API_KEY:
        print("Error: AFFINITY_API_KEY environment variable not set")
        print("Set it with: export AFFINITY_API_KEY='your-api-key'")
        sys.exit(1)

    print("=" * 60)
    print("📥 Pulling data from Affinity into Deal Analysis")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be saved\n")
    if args.limit:
        print(f"📊 Limit: {args.limit}\n")

    pull_from_affinity(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
