#!/usr/bin/env python3
"""
Step 3: Import LinkedIn profiles and score founders

Usage:
    python3 scripts/3_import_linkedin_and_score.py /path/to/linkedin_profiles.json

This script:
1. Reads scraped LinkedIn profile data (JSON format from LinkedIn scraper)
2. Matches profiles to founders in seed-data.json
3. Enriches founder records with bio, schools, employers, etc.

NOTE: Founder scoring (the 9-category LLM-based scoring) should be done
manually with Claude, as it requires nuanced analysis of each profile.
This script prepares the data for that process.

Expected LinkedIn JSON format (array of profiles):
[
    {
        "profileUrl": "https://linkedin.com/in/...",
        "firstName": "John",
        "lastName": "Doe",
        "linkedinHeadline": "CEO at Company",
        "linkedinDescription": "Bio text...",
        "linkedinSchoolName": "MIT",
        "linkedinSchoolDegree": "PhD",
        "linkedinPreviousSchoolName": "Stanford",
        "linkedinPreviousSchoolDegree": "BS",
        "companyName": "Current Company",
        "previousCompanyName": "Previous Company",
        "linkedinJobTitle": "CEO",
        ...
    }
]
"""

import sys
import json
from pathlib import Path

def parse_linkedin_data(profiles):
    """Parse LinkedIn profile data into structured format."""
    parsed = []

    for profile in profiles:
        # Skip error profiles
        if profile.get('error'):
            continue

        data = {
            'linkedin_url': profile.get('profileUrl', profile.get('linkedinProfileUrl', '')),
            'name': f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
            'headline': profile.get('linkedinHeadline', ''),
            'bio': profile.get('linkedinDescription', ''),
            'company': profile.get('companyName', profile.get('linkedinCompanyName', '')),
            'job_title': profile.get('linkedinJobTitle', ''),
            'location': profile.get('location', ''),
            'connections': profile.get('linkedinConnectionsCount', 0),
            'followers': profile.get('linkedinFollowersCount', 0),
        }

        # Parse schools
        schools = []
        degrees = []
        if profile.get('linkedinSchoolName'):
            schools.append(profile['linkedinSchoolName'])
            if profile.get('linkedinSchoolDegree'):
                degrees.append(profile['linkedinSchoolDegree'])
        if profile.get('linkedinPreviousSchoolName'):
            schools.append(profile['linkedinPreviousSchoolName'])
            if profile.get('linkedinPreviousSchoolDegree'):
                degrees.append(profile['linkedinPreviousSchoolDegree'])

        data['schools'] = ', '.join(schools)
        data['degrees'] = ', '.join(degrees)

        # Parse prior employers
        employers = []
        if profile.get('previousCompanyName'):
            employers.append(profile['previousCompanyName'])
        if profile.get('linkedinPreviousJobTitle'):
            # Try to extract more employers from job history if available
            pass

        data['prior_employers'] = ', '.join(employers)

        # Determine technical competence
        tech_keywords = ['phd', 'engineer', 'scientist', 'researcher', 'professor', 'technical', 'cto', 'developer', 'architect']
        bio_lower = (data['bio'] + ' ' + data['headline'] + ' ' + ' '.join(degrees)).lower()

        if any(kw in bio_lower for kw in ['phd', 'professor', 'scientist', 'researcher']):
            data['technical_competence'] = 'High'
        elif any(kw in bio_lower for kw in ['engineer', 'cto', 'developer', 'technical']):
            data['technical_competence'] = 'Medium'
        else:
            data['technical_competence'] = 'Low'

        # Check for repeat founder
        founder_keywords = ['founder', 'co-founder', 'cofounder', 'started', 'founded']
        bio_lower = data['bio'].lower()
        is_repeat = sum(1 for kw in founder_keywords if kw in bio_lower) > 1
        data['is_repeat_founder'] = 1 if is_repeat else 0

        parsed.append(data)

    return parsed

def match_and_update_founders(linkedin_data, company_ids=None):
    """Match LinkedIn profiles to founders and update seed-data.json."""
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'

    with open(seed_path, 'r') as f:
        seed_data = json.load(f)

    updated = []

    for company in seed_data['companies']:
        # Filter by company IDs if specified
        if company_ids and company['id'] not in company_ids:
            continue

        for founder in company.get('founders', []):
            # Try to match by LinkedIn URL or name
            matched_profile = None

            for profile in linkedin_data:
                # Match by LinkedIn URL
                if founder.get('linkedin') and profile.get('linkedin_url'):
                    if founder['linkedin'].rstrip('/') in profile['linkedin_url'] or \
                       profile['linkedin_url'].rstrip('/') in founder['linkedin']:
                        matched_profile = profile
                        break

                # Match by name (fuzzy)
                if founder.get('name') and profile.get('name'):
                    founder_name = founder['name'].lower().strip()
                    profile_name = profile['name'].lower().strip()
                    if founder_name == profile_name or \
                       founder_name in profile_name or \
                       profile_name in founder_name:
                        matched_profile = profile
                        break

            if matched_profile:
                # Update founder record
                founder['bio'] = matched_profile.get('bio', founder.get('bio', ''))[:500]
                founder['schools'] = matched_profile.get('schools', founder.get('schools', ''))
                founder['degrees'] = matched_profile.get('degrees', founder.get('degrees', ''))
                founder['prior_employers'] = matched_profile.get('prior_employers', founder.get('prior_employers', ''))
                founder['technical_competence'] = matched_profile.get('technical_competence', founder.get('technical_competence', ''))
                founder['is_repeat_founder'] = matched_profile.get('is_repeat_founder', founder.get('is_repeat_founder', 0))

                if matched_profile.get('linkedin_url') and not founder.get('linkedin'):
                    founder['linkedin'] = matched_profile['linkedin_url']

                updated.append({
                    'company': company['name'],
                    'company_id': company['id'],
                    'founder': founder['name'],
                    'profile': matched_profile['name']
                })

    # Save updated seed data
    with open(seed_path, 'w') as f:
        json.dump(seed_data, f, indent=2)

    return updated

def generate_scoring_prompt(company_ids=None):
    """Generate a prompt for Claude to score founders."""
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'

    with open(seed_path, 'r') as f:
        seed_data = json.load(f)

    prompt = """Please score the following founders using the 9-category methodology (1-10 scale):

SCORING CATEGORIES:
1. Breakthrough Idea (breakthrough_score): Non-obvious insights, causal chain thinking
2. Mission Intentionality (mission_score): Authenticity, personal connection
3. Extraordinary Achievements (achievements_score): Academic honors, patents, exits
4. Work Ethic & Execution (work_ethic_score): Track record of delivery
5. Grit & Perseverance (grit_score): Overcoming adversity
6. Magnetism (magnetism_score): Network, leadership presence
7. Intellectual Curiosity (curiosity_score): Breadth of interests, learning
8. Coachability & EQ (coachability_score): Openness to feedback
9. Team Chemistry (team_chemistry_score): Collaboration ability

For each founder, provide:
- Score (1-10) for each category
- Brief justification for each score
- Overall founder_score (average of 9 scores)

FOUNDERS TO SCORE:
"""

    for company in seed_data['companies']:
        if company_ids and company['id'] not in company_ids:
            continue

        if company.get('source') != 'Deepchecks':
            continue

        for founder in company.get('founders', []):
            if founder.get('founder_score'):
                continue  # Already scored

            prompt += f"\n{'='*60}\n"
            prompt += f"Company: {company['name']} (ID: {company['id']})\n"
            prompt += f"Founder: {founder['name']}\n"
            prompt += f"LinkedIn: {founder.get('linkedin', 'N/A')}\n"
            prompt += f"Bio: {founder.get('bio', 'N/A')}\n"
            prompt += f"Schools: {founder.get('schools', 'N/A')}\n"
            prompt += f"Degrees: {founder.get('degrees', 'N/A')}\n"
            prompt += f"Prior Employers: {founder.get('prior_employers', 'N/A')}\n"
            prompt += f"Technical Competence: {founder.get('technical_competence', 'N/A')}\n"

    return prompt

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 3_import_linkedin_and_score.py <linkedin_json> [company_id_start] [company_id_end]")
        print("Example: python3 3_import_linkedin_and_score.py ~/Downloads/linkedin_profiles.json 210 249")
        sys.exit(1)

    linkedin_path = sys.argv[1]

    # Optional: filter by company ID range
    company_ids = None
    if len(sys.argv) >= 4:
        start_id = int(sys.argv[2])
        end_id = int(sys.argv[3])
        company_ids = list(range(start_id, end_id + 1))

    print(f"Loading LinkedIn profiles from {linkedin_path}...")
    with open(linkedin_path, 'r') as f:
        raw_profiles = json.load(f)

    print(f"Parsing {len(raw_profiles)} profiles...")
    linkedin_data = parse_linkedin_data(raw_profiles)
    print(f"Parsed {len(linkedin_data)} valid profiles\n")

    print("Matching and updating founders...")
    updated = match_and_update_founders(linkedin_data, company_ids)
    print(f"Updated {len(updated)} founder records:\n")

    for u in updated:
        print(f"  {u['company']} ({u['company_id']}): {u['founder']} <- {u['profile']}")

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. The founder records have been enriched with LinkedIn data")
    print("2. Now ask Claude to score the founders using the 9-category methodology")
    print("3. Paste the following prompt to Claude:\n")

    # Generate scoring prompt
    prompt = generate_scoring_prompt(company_ids)
    prompt_path = Path(linkedin_path).parent / 'founder_scoring_prompt.txt'
    with open(prompt_path, 'w') as f:
        f.write(prompt)
    print(f"Scoring prompt saved to: {prompt_path}")
