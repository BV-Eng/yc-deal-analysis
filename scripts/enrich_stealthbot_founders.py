#!/usr/bin/env python3
"""
Enrich StealthBot founders with scores and justifications from LinkedIn data.
No API calls - uses rule-based scoring from profile data.
"""

import csv
import json
import re

# Prestige indicators
ELITE_SCHOOLS = ['stanford', 'harvard', 'mit', 'yale', 'princeton', 'berkeley', 'caltech',
                 'columbia', 'penn', 'wharton', 'cornell', 'duke', 'northwestern', 'chicago',
                 'oxford', 'cambridge', 'carnegie mellon', 'georgia tech', 'ucla', 'nyu']
TOP_COMPANIES = ['google', 'meta', 'facebook', 'apple', 'amazon', 'microsoft', 'netflix',
                 'uber', 'airbnb', 'stripe', 'openai', 'anthropic', 'palantir', 'snowflake',
                 'salesforce', 'tesla', 'spacex', 'mckinsey', 'bain', 'bcg', 'goldman',
                 'morgan stanley', 'jpmorgan', 'sequoia', 'a16z', 'andreessen']
HEALTH_KEYWORDS = ['health', 'medical', 'clinical', 'patient', 'hospital', 'pharma',
                   'biotech', 'therapeutic', 'diagnostic', 'disease', 'care']
CLIMATE_KEYWORDS = ['climate', 'energy', 'solar', 'renewable', 'sustainability', 'carbon',
                    'cleantech', 'environmental', 'green']
WORKFORCE_KEYWORDS = ['education', 'learning', 'training', 'workforce', 'skill', 'hr',
                      'talent', 'recruiting', 'career']

def normalize_name(name):
    """Normalize name for matching."""
    return re.sub(r'[^a-z\s]', '', name.lower()).strip()

def check_elite_school(text):
    """Check if text contains elite school."""
    text_lower = text.lower()
    for school in ELITE_SCHOOLS:
        if school in text_lower:
            return school.title()
    return None

def check_top_company(text):
    """Check if text contains top company."""
    text_lower = text.lower()
    for company in TOP_COMPANIES:
        if company in text_lower:
            return company.title()
    return None

def get_domain_alignment(text):
    """Check alignment with Better Ventures themes."""
    text_lower = text.lower()
    domains = []
    if any(k in text_lower for k in HEALTH_KEYWORDS):
        domains.append('health')
    if any(k in text_lower for k in CLIMATE_KEYWORDS):
        domains.append('climate')
    if any(k in text_lower for k in WORKFORCE_KEYWORDS):
        domains.append('workforce')
    return domains

def score_founder(profile):
    """Generate scores and justifications from LinkedIn profile."""

    # Extract fields
    first_name = profile.get('firstName', '')
    last_name = profile.get('lastName', '')
    headline = profile.get('linkedinHeadline', '')
    bio = profile.get('linkedinDescription', '')
    job_title = profile.get('linkedinJobTitle', '')
    job_desc = profile.get('linkedinJobDescription', '')
    prev_title = profile.get('linkedinPreviousJobTitle', '')
    prev_company = profile.get('previousCompanyName', '')
    prev_job_desc = profile.get('linkedinPreviousJobDescription', '')
    school = profile.get('linkedinSchoolName', '')
    degree = profile.get('linkedinSchoolDegree', '')
    field = profile.get('linkedinSchoolFieldOfStudy', '')
    prev_school = profile.get('linkedinPreviousSchoolName', '')
    prev_degree = profile.get('linkedinPreviousSchoolDegree', '')
    skills = profile.get('linkedinSkillsLabel', '')
    followers = int(profile.get('linkedinFollowersCount', 0) or 0)
    connections = int(profile.get('linkedinConnectionsCount', 0) or 0)
    location = profile.get('location', '')
    company_name = profile.get('companyName', '')
    company_desc = profile.get('linkedinCompanyDescription', '')

    # Combine all text for analysis
    all_text = f"{headline} {bio} {job_title} {job_desc} {prev_title} {prev_job_desc} {skills} {company_desc}"
    edu_text = f"{school} {degree} {prev_school} {prev_degree} {field}"

    scores = {}
    justifications = {}

    # ===== BREAKTHROUGH SCORE =====
    # Cross-domain expertise, novel combinations, technical depth
    breakthrough = 5.0
    breakthrough_notes = []

    elite = check_elite_school(edu_text)
    top_co = check_top_company(f"{prev_company} {all_text}")
    domains = get_domain_alignment(all_text)

    has_phd = 'phd' in edu_text.lower() or 'ph.d' in edu_text.lower() or 'doctorate' in edu_text.lower()
    has_md = ', md' in f"{first_name} {last_name}".lower() or 'medical doctor' in edu_text.lower()
    has_mba = 'mba' in edu_text.lower()
    is_technical = any(k in skills.lower() for k in ['python', 'machine learning', 'ai', 'engineering', 'software', 'data science'])

    if has_phd:
        breakthrough += 1.5
        breakthrough_notes.append("PhD holder")
    if has_md:
        breakthrough += 1.0
        breakthrough_notes.append("Medical degree")
    if elite:
        breakthrough += 0.5
        breakthrough_notes.append(f"{elite} education")
    if top_co:
        breakthrough += 0.5
        breakthrough_notes.append(f"Ex-{top_co}")
    if is_technical and has_mba:
        breakthrough += 0.5
        breakthrough_notes.append("Technical + business background")
    if len(domains) >= 2:
        breakthrough += 0.5
        breakthrough_notes.append("Cross-domain expertise")

    breakthrough = min(10.0, max(4.0, breakthrough))
    scores['breakthrough_score'] = round(breakthrough, 1)
    justifications['breakthrough_justification'] = "; ".join(breakthrough_notes) if breakthrough_notes else "Limited evidence of breakthrough thinking from available profile data."

    # ===== MISSION SCORE =====
    # Career consistency, domain dedication, personal connection
    mission = 5.0
    mission_notes = []

    if len(domains) >= 1:
        mission += 1.0
        domain_str = "/".join(domains)
        mission_notes.append(f"Focus on {domain_str}")

    # Check for founder experience
    is_repeat_founder = 'founder' in prev_title.lower() or 'co-founder' in prev_title.lower()
    if is_repeat_founder:
        mission += 1.0
        mission_notes.append("Repeat founder")

    # Career in same domain
    if bio and len(bio) > 100:
        mission += 0.5
        if any(k in bio.lower() for k in ['passionate', 'dedicated', 'mission', 'impact', 'believe']):
            mission += 0.5
            mission_notes.append("Mission-driven language in bio")

    if has_md and any(k in all_text.lower() for k in HEALTH_KEYWORDS):
        mission += 1.0
        mission_notes.append("MD building in healthcare")

    mission = min(10.0, max(4.0, mission))
    scores['mission_score'] = round(mission, 1)
    justifications['mission_justification'] = "; ".join(mission_notes) if mission_notes else "Career trajectory shows general professional progression."

    # ===== ACHIEVEMENTS SCORE =====
    # Credentials, titles, company prestige
    achievements = 5.0
    achievements_notes = []

    if elite:
        achievements += 1.5
        achievements_notes.append(f"{elite} graduate")
    if has_phd:
        achievements += 1.5
        achievements_notes.append("PhD")
    if has_md:
        achievements += 1.5
        achievements_notes.append("MD")
    if has_mba:
        achievements += 0.5
        achievements_notes.append("MBA")
    if top_co:
        achievements += 1.0
        achievements_notes.append(f"Ex-{top_co}")

    # Senior titles
    senior_titles = ['ceo', 'cto', 'cfo', 'vp', 'vice president', 'director', 'head of', 'principal', 'partner']
    if any(t in prev_title.lower() for t in senior_titles):
        achievements += 0.5
        achievements_notes.append(f"Senior role: {prev_title[:30]}")

    achievements = min(10.0, max(4.0, achievements))
    scores['achievements_score'] = round(achievements, 1)
    justifications['achievements_justification'] = "; ".join(achievements_notes) if achievements_notes else "Standard professional credentials."

    # ===== WORK ETHIC SCORE =====
    # Execution track record, career progression
    work_ethic = 5.5
    work_ethic_notes = []

    if top_co:
        work_ethic += 1.0
        work_ethic_notes.append(f"Operated at {top_co}")
    if is_repeat_founder:
        work_ethic += 1.0
        work_ethic_notes.append("Built companies before")
    if prev_job_desc and len(prev_job_desc) > 100:
        work_ethic += 0.5
        work_ethic_notes.append("Detailed execution history")
    if job_desc and ('built' in job_desc.lower() or 'led' in job_desc.lower() or 'launched' in job_desc.lower()):
        work_ethic += 0.5
        work_ethic_notes.append("Evidence of shipping/building")

    work_ethic = min(10.0, max(4.0, work_ethic))
    scores['work_ethic_score'] = round(work_ethic, 1)
    justifications['work_ethic_justification'] = "; ".join(work_ethic_notes) if work_ethic_notes else "Professional work history with limited execution details."

    # ===== GRIT SCORE =====
    # Adversity, unconventional paths, persistence
    grit = 5.5
    grit_notes = []

    if is_repeat_founder:
        grit += 1.0
        grit_notes.append("Repeat founder shows persistence")

    # Look for adversity/persistence signals
    grit_keywords = ['immigrant', 'first-generation', 'self-taught', 'dropped out', 'pivoted', 'overcame', 'resilience']
    if any(k in bio.lower() for k in grit_keywords):
        grit += 1.5
        grit_notes.append("Adversity signals in background")

    # Long career = persistence
    if prev_title and prev_company:
        grit += 0.5
        grit_notes.append("Sustained career progression")

    grit = min(10.0, max(4.0, grit))
    scores['grit_score'] = round(grit, 1)
    justifications['grit_justification'] = "; ".join(grit_notes) if grit_notes else "Standard career path without notable adversity signals."

    # ===== MAGNETISM SCORE =====
    # Network, followers, leadership presence
    magnetism = 5.0
    magnetism_notes = []

    if followers >= 10000:
        magnetism += 2.0
        magnetism_notes.append(f"{followers:,} LinkedIn followers")
    elif followers >= 5000:
        magnetism += 1.5
        magnetism_notes.append(f"{followers:,} LinkedIn followers")
    elif followers >= 2000:
        magnetism += 1.0
        magnetism_notes.append(f"{followers:,} LinkedIn followers")
    elif followers >= 1000:
        magnetism += 0.5
        magnetism_notes.append(f"{followers:,} LinkedIn followers")

    if connections >= 5000:
        magnetism += 1.0
        magnetism_notes.append(f"{connections:,}+ connections")
    elif connections >= 2000:
        magnetism += 0.5
        magnetism_notes.append(f"{connections:,}+ connections")

    # Leadership titles suggest magnetism
    if any(t in headline.lower() for t in ['ceo', 'founder', 'partner']):
        magnetism += 0.5
        magnetism_notes.append("Leadership positioning")

    magnetism = min(10.0, max(4.0, magnetism))
    scores['magnetism_score'] = round(magnetism, 1)
    justifications['magnetism_justification'] = "; ".join(magnetism_notes) if magnetism_notes else "Moderate professional network."

    # ===== CURIOSITY SCORE =====
    # Diverse skills, cross-domain, learning
    curiosity = 5.5
    curiosity_notes = []

    skill_list = [s.strip() for s in skills.split(',') if s.strip()]
    if len(skill_list) >= 15:
        curiosity += 1.0
        curiosity_notes.append(f"Broad skill set ({len(skill_list)}+ skills)")
    elif len(skill_list) >= 10:
        curiosity += 0.5
        curiosity_notes.append(f"Diverse skills ({len(skill_list)} listed)")

    if len(domains) >= 2:
        curiosity += 1.0
        curiosity_notes.append("Cross-domain experience")

    if has_mba and is_technical:
        curiosity += 0.5
        curiosity_notes.append("Technical + business learning")

    if prev_school and school and prev_school.lower() != school.lower():
        curiosity += 0.5
        curiosity_notes.append("Multiple institutions")

    curiosity = min(10.0, max(4.0, curiosity))
    scores['curiosity_score'] = round(curiosity, 1)
    justifications['curiosity_justification'] = "; ".join(curiosity_notes) if curiosity_notes else "Standard professional development."

    # ===== COACHABILITY SCORE =====
    # Career pivots, growth, learning evidence
    coachability = 6.0  # Default slightly higher - hard to assess
    coachability_notes = []

    # Career pivots suggest adaptability
    if prev_title and job_title:
        if prev_title.lower() != job_title.lower():
            coachability += 0.5
            coachability_notes.append("Career evolution from previous role")

    if has_mba:
        coachability += 0.5
        coachability_notes.append("Pursued MBA (growth mindset)")

    if 'advisor' in all_text.lower() or 'mentor' in all_text.lower():
        coachability += 0.5
        coachability_notes.append("Engages with advisors/mentors")

    coachability = min(10.0, max(4.0, coachability))
    scores['coachability_score'] = round(coachability, 1)
    justifications['coachability_justification'] = "; ".join(coachability_notes) if coachability_notes else "Limited data on coachability; assuming baseline openness."

    # ===== TEAM CHEMISTRY SCORE =====
    # Co-founder experience, team leadership
    team_chemistry = 5.5
    team_chemistry_notes = []

    if 'co-founder' in headline.lower() or 'co-founder' in job_title.lower():
        team_chemistry += 1.0
        team_chemistry_notes.append("Current co-founder (working with partners)")

    if 'co-founder' in prev_title.lower():
        team_chemistry += 1.0
        team_chemistry_notes.append("Previous co-founder experience")

    team_keywords = ['team', 'led', 'managed', 'cross-functional', 'collaboration']
    if any(k in all_text.lower() for k in team_keywords):
        team_chemistry += 0.5
        team_chemistry_notes.append("Team leadership experience")

    team_chemistry = min(10.0, max(4.0, team_chemistry))
    scores['team_chemistry_score'] = round(team_chemistry, 1)
    justifications['team_chemistry_justification'] = "; ".join(team_chemistry_notes) if team_chemistry_notes else "Limited data on team dynamics."

    # Calculate founder_score (average of 9 criteria)
    all_scores = [scores['breakthrough_score'], scores['mission_score'], scores['achievements_score'],
                  scores['work_ethic_score'], scores['grit_score'], scores['magnetism_score'],
                  scores['curiosity_score'], scores['coachability_score'], scores['team_chemistry_score']]
    scores['founder_score'] = round(sum(all_scores) / len(all_scores), 2)

    return scores, justifications


def main():
    print("=" * 70)
    print("Enriching StealthBot Founders from LinkedIn Data")
    print("=" * 70)

    # Load CSV (March 2026 only)
    csv_path = '/Users/Ryan/Downloads/result (19).csv'
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        csv_rows = {normalize_name(f"{r.get('firstName', '')} {r.get('lastName', '')}"): r
                    for r in reader if r.get('refreshedAt', '').startswith('2026-03')}

    print(f"Loaded {len(csv_rows)} March 2026 profiles from CSV")

    # Load seed-data
    with open('data/seed-data.json', 'r') as f:
        data = json.load(f)

    # Process StealthBot companies
    matched = 0
    updated = 0

    for i, company in enumerate(data['companies']):
        if 'StealthBot' not in (company.get('source') or ''):
            continue

        founders = company.get('founders', [])
        if not founders:
            continue

        founder = founders[0]
        founder_name = founder.get('name', '')
        normalized = normalize_name(founder_name)

        # Try to find in CSV
        profile = csv_rows.get(normalized)

        # Try partial matches for edge cases
        if not profile:
            for csv_name, csv_profile in csv_rows.items():
                # Check if first name and first letter of last match
                parts = normalized.split()
                csv_parts = csv_name.split()
                if len(parts) >= 1 and len(csv_parts) >= 1:
                    if parts[0] == csv_parts[0]:  # First name match
                        profile = csv_profile
                        break

        if not profile:
            print(f"  SKIP: {founder_name} (no CSV match)")
            continue

        matched += 1

        # Generate scores and justifications
        scores, justifications = score_founder(profile)

        # Update founder
        old_score = founder.get('founder_score', 0)
        for key, value in scores.items():
            data['companies'][i]['founders'][0][key] = value
        for key, value in justifications.items():
            data['companies'][i]['founders'][0][key] = value

        # Update company_score to match founder_score (for person-based sources)
        data['companies'][i]['company_score'] = scores['founder_score']

        new_score = scores['founder_score']
        change = new_score - old_score
        change_str = f"+{change:.1f}" if change > 0 else f"{change:.1f}"

        print(f"  {founder_name[:30]:<30} {old_score:.1f} → {new_score:.1f} ({change_str})")
        updated += 1

    # Save
    with open('data/seed-data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"SUMMARY: Matched {matched}, Updated {updated} founders")
    print(f"Saved to data/seed-data.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
