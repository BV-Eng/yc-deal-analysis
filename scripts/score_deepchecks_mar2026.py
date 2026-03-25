#!/usr/bin/env python3
"""
Score Deepchecks Mar 2026 founders with 9-dimension methodology.
Designed for differentiated scores - not all 6's and 7's.

Tier 1 (8+): Elite schools, PhD/MD, top companies (FAANG, SpaceX, etc.), exits
Tier 2 (6-7): Solid credentials, good experience
Tier 3 (4-5): Limited data or weak credentials
"""

import json
import csv
import re
from pathlib import Path

# Elite credentials
ELITE_SCHOOLS = {
    'stanford': 'Stanford', 'harvard': 'Harvard', 'mit': 'MIT', 'yale': 'Yale',
    'princeton': 'Princeton', 'berkeley': 'UC Berkeley', 'caltech': 'Caltech',
    'columbia': 'Columbia', 'penn': 'Penn', 'wharton': 'Wharton', 'cornell': 'Cornell',
    'duke': 'Duke', 'northwestern': 'Northwestern', 'chicago': 'UChicago',
    'oxford': 'Oxford', 'cambridge': 'Cambridge', 'carnegie mellon': 'CMU', 'cmu': 'CMU',
    'georgia tech': 'Georgia Tech', 'johns hopkins': 'Johns Hopkins', 'hopkins': 'Hopkins',
    'ucla': 'UCLA', 'nyu': 'NYU', 'insead': 'INSEAD', 'london business': 'LBS',
    'imperial': 'Imperial', 'eth': 'ETH Zurich', 'epfl': 'EPFL',
    'illinois': 'UIUC', 'michigan': 'Michigan', 'purdue': 'Purdue',
}

TOP_COMPANIES = {
    'google': 'Google', 'meta': 'Meta', 'facebook': 'Facebook/Meta', 'apple': 'Apple',
    'amazon': 'Amazon', 'microsoft': 'Microsoft', 'netflix': 'Netflix', 'uber': 'Uber',
    'airbnb': 'Airbnb', 'stripe': 'Stripe', 'openai': 'OpenAI', 'anthropic': 'Anthropic',
    'palantir': 'Palantir', 'snowflake': 'Snowflake', 'databricks': 'Databricks',
    'mckinsey': 'McKinsey', 'bain': 'Bain', 'bcg': 'BCG', 'goldman': 'Goldman',
    'sequoia': 'Sequoia', 'a16z': 'a16z', 'tesla': 'Tesla', 'spacex': 'SpaceX',
    'nasa': 'NASA', 'nih': 'NIH', 'arpa': 'ARPA', 'darpa': 'DARPA',
    'lockheed': 'Lockheed', 'boeing': 'Boeing', 'raytheon': 'Raytheon',
    'nvidia': 'NVIDIA', 'intel': 'Intel', 'qualcomm': 'Qualcomm',
    'jp morgan': 'JPMorgan', 'morgan stanley': 'Morgan Stanley',
}

THESIS_KEYWORDS = {
    'Sustainable Industry': ['climate', 'energy', 'solar', 'renewable', 'sustainability',
        'carbon', 'clean', 'electrification', 'ev', 'battery', 'hydrogen', 'biotech',
        'biomanufacturing', 'circular', 'recycling', 'waste', 'agriculture', 'agtech'],
    'Human Health': ['health', 'medical', 'patient', 'clinical', 'physician', 'doctor',
        'hospital', 'biotech', 'therapeutic', 'pharma', 'surgery', 'cardio', 'neuro',
        'oncol', 'diagnostic', 'drug', 'medicine', 'longevity', 'wellness'],
    'Tomorrow\'s Workforce': ['education', 'learning', 'training', 'skill', 'workforce',
        'hiring', 'talent', 'ai tool', 'productivity', 'smb', 'automation'],
}


def find_elite_schools(text):
    """Find all elite schools mentioned."""
    found = []
    text_lower = text.lower()
    for key, name in ELITE_SCHOOLS.items():
        if key in text_lower and name not in found:
            found.append(name)
    return found


def find_top_companies(text):
    """Find all top companies mentioned."""
    found = []
    text_lower = text.lower()
    for key, name in TOP_COMPANIES.items():
        if key in text_lower and name not in found:
            found.append(name)
    return found


def extract_credentials(name, text):
    """Extract degrees and credentials."""
    creds = []
    combined = f"{name.lower()} {text.lower()}"

    if 'ph.d' in combined or 'phd' in combined or 'doctor of philosophy' in combined:
        creds.append('PhD')
    if ', md' in combined or ' md,' in combined or 'doctor of medicine' in combined or 'm.d.' in combined:
        creds.append('MD')
    if ', jd' in combined or 'juris doctor' in combined or 'j.d.' in combined:
        creds.append('JD')
    if 'mba' in combined or 'master of business' in combined:
        creds.append('MBA')
    if 'master' in combined or ', ms' in combined or 'm.s.' in combined:
        creds.append('MS')
    if 'mph' in combined or 'master of public health' in combined:
        creds.append('MPH')
    if 'd.eng' in combined or 'doctor of engineering' in combined:
        creds.append('D.Eng')

    return creds


def detect_thesis_theme(all_text):
    """Detect which Better Ventures thesis theme best fits."""
    text_lower = all_text.lower()
    scores = {}

    for theme, keywords in THESIS_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[theme] = score

    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return 'General'


def score_founder(profile):
    """Generate detailed scores with full-sentence justifications."""

    # Extract all available data
    name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
    headline = profile.get('linkedinHeadline', '') or ''
    bio = profile.get('linkedinDescription', '') or ''
    job_title = profile.get('linkedinJobTitle', '') or ''
    job_desc = profile.get('linkedinJobDescription', '') or ''
    prev_title = profile.get('linkedinPreviousJobTitle', '') or ''
    prev_company = profile.get('previousCompanyName', '') or ''
    prev_job_desc = profile.get('linkedinPreviousJobDescription', '') or ''
    school = profile.get('linkedinSchoolName', '') or ''
    degree = profile.get('linkedinSchoolDegree', '') or ''
    field = profile.get('linkedinSchoolFieldOfStudy', '') or ''
    prev_school = profile.get('linkedinPreviousSchoolName', '') or ''
    prev_degree = profile.get('linkedinPreviousSchoolDegree', '') or ''
    skills = profile.get('linkedinSkillsLabel', '') or ''
    followers = int(profile.get('linkedinFollowersCount', 0) or 0)
    connections = int(profile.get('linkedinConnectionsCount', 0) or 0)
    company_desc = profile.get('linkedinCompanyDescription', '') or ''
    company_name = profile.get('companyName', profile.get('Company Name', ''))

    # Combine text for analysis
    all_text = f"{name} {headline} {bio} {job_title} {job_desc} {prev_title} {prev_job_desc} {company_desc}"
    edu_text = f"{school} {degree} {field} {prev_school} {prev_degree}"
    work_text = f"{prev_company} {prev_title} {job_title}"

    # Extract key info
    elite_schools = find_elite_schools(edu_text + " " + bio)
    top_companies = find_top_companies(all_text + " " + prev_company)
    credentials = extract_credentials(name, edu_text + " " + bio + " " + headline)
    thesis_theme = detect_thesis_theme(all_text + " " + company_desc)

    # Detect patterns
    is_phd = 'PhD' in credentials
    is_md = 'MD' in credentials
    is_mba = 'MBA' in credentials
    is_deng = 'D.Eng' in credentials
    has_advanced_degree = is_phd or is_md or is_deng

    is_repeat_founder = ('founder' in prev_title.lower() or 'ceo' in prev_title.lower() or
                         'co-founder' in bio.lower())
    is_current_founder = 'founder' in job_title.lower() or 'ceo' in job_title.lower()

    # Check for Forbes 30 under 30 or similar
    has_forbes = '30 under 30' in headline.lower() or 'forbes' in headline.lower()

    # Check for YC or notable backing
    has_notable_backing = any(b in all_text.lower() for b in ['1517', 'yc', 'y combinator', 'sequoia', 'a16z'])

    # Check for exits
    has_exit = any(k in all_text.lower() for k in ['acquired', 'acquisition', 'exit', 'sold to', 'ipo'])

    scores = {}
    justifications = {}

    # ============ BREAKTHROUGH SCORE ============
    b_score = 4.5  # Start lower for differentiation
    b_parts = []

    if has_advanced_degree:
        b_score += 3.0
        b_parts.append(f"{'/'.join(credentials[:2])} demonstrates deep technical expertise")
    if elite_schools:
        b_score += 1.5
        b_parts.append(f"Education at {', '.join(elite_schools[:2])} indicates intellectual caliber")
    if top_companies:
        b_score += 1.5
        b_parts.append(f"Experience at {', '.join(top_companies[:2])} exposes to world-class practices")
    if 'arpa' in all_text.lower() or 'darpa' in all_text.lower():
        b_score += 2.5
        b_parts.append("ARPA/DARPA involvement signals frontier research")
    if has_forbes:
        b_score += 1.5
        b_parts.append("Forbes 30 Under 30 recognition validates breakthrough potential")

    if not b_parts:
        b_parts.append("Limited evidence of breakthrough thinking from profile data")
        b_score = 4.0

    scores['breakthrough_score'] = min(10.0, round(b_score, 1))
    justifications['breakthrough_justification'] = ". ".join(b_parts) + "."

    # ============ MISSION SCORE ============
    m_score = 4.5
    m_parts = []

    if thesis_theme != 'General':
        m_score += 2.0
        m_parts.append(f"Company focus on {thesis_theme} aligns with Better Ventures thesis")
    if 'obsessed' in bio.lower() or 'passionate' in bio.lower() or 'mission' in bio.lower():
        m_score += 1.0
        m_parts.append("Language suggests mission-driven motivation")
    if is_repeat_founder:
        m_score += 1.5
        m_parts.append("Repeat founder shows sustained commitment to building")
    if has_advanced_degree:
        m_score += 1.5
        m_parts.append("Advanced degree pursuit indicates deep domain commitment")
    if 'climate' in all_text.lower() or 'decarboniz' in all_text.lower():
        m_score += 1.5
        m_parts.append("Direct focus on climate impact")
    if 'health' in all_text.lower() and (is_md or 'clinical' in all_text.lower()):
        m_score += 1.5
        m_parts.append("Healthcare background with clinical connection")

    if not m_parts:
        m_parts.append("Mission alignment unclear from available data")
        m_score = 4.0

    scores['mission_score'] = min(10.0, round(m_score, 1))
    justifications['mission_justification'] = ". ".join(m_parts) + "."

    # ============ ACHIEVEMENTS SCORE ============
    a_score = 4.0
    a_parts = []

    if is_phd:
        a_score += 3.0
        a_parts.append("PhD demonstrates intellectual rigor and sustained research achievement")
    if is_md:
        a_score += 2.5
        a_parts.append("Medical degree requires exceptional academic achievement")
    if is_mba:
        a_score += 1.0
        a_parts.append("MBA adds business acumen")
    if elite_schools:
        a_score += 2.0
        a_parts.append(f"Elite education ({', '.join(elite_schools[:2])}) demonstrates excellence")
    if top_companies:
        a_score += 1.5
        a_parts.append(f"Experience at {top_companies[0]} validates caliber")
    if has_exit:
        a_score += 2.5
        a_parts.append("Previous exit demonstrates ability to build valuable companies")
    if has_forbes:
        a_score += 2.0
        a_parts.append("Forbes recognition is significant external validation")
    if has_notable_backing:
        a_score += 1.0
        a_parts.append("Notable VC backing validates market potential")

    if not a_parts:
        a_parts.append("Standard credentials without standout achievements visible")
        a_score = 4.0

    scores['achievements_score'] = min(10.0, round(a_score, 1))
    justifications['achievements_justification'] = ". ".join(a_parts) + "."

    # ============ WORK ETHIC SCORE ============
    w_score = 5.0
    w_parts = []

    if is_repeat_founder:
        w_score += 2.0
        w_parts.append("Repeat founder has proven ability to build")
    if top_companies:
        w_score += 1.5
        w_parts.append(f"Operating at {top_companies[0]} requires high performance")
    if has_advanced_degree:
        w_score += 1.5
        w_parts.append("Completing rigorous training demonstrates sustained effort")
    if has_exit:
        w_score += 1.5
        w_parts.append("Previous exit shows ability to execute through full lifecycle")
    if 'built' in all_text.lower() or 'scaled' in all_text.lower():
        w_score += 0.5
        w_parts.append("Evidence of building/scaling in background")

    if not w_parts:
        w_parts.append("Limited evidence of exceptional execution from profile")
        w_score = 5.0

    scores['work_ethic_score'] = min(10.0, round(w_score, 1))
    justifications['work_ethic_justification'] = ". ".join(w_parts) + "."

    # ============ GRIT SCORE ============
    g_score = 5.0
    g_parts = []

    if is_repeat_founder:
        g_score += 2.0
        g_parts.append("Starting multiple companies shows persistence through setbacks")
    if is_phd:
        g_score += 2.5
        g_parts.append("PhD completion requires 5-7 years of perseverance")
    if is_md:
        g_score += 1.5
        g_parts.append("Medical training is grueling multi-year commitment")
    if 'immigrant' in bio.lower() or 'first-generation' in bio.lower():
        g_score += 2.0
        g_parts.append("Overcame significant personal challenges")

    if not g_parts:
        g_parts.append("Limited evidence of overcoming significant adversity")
        g_score = 5.0

    scores['grit_score'] = min(10.0, round(g_score, 1))
    justifications['grit_justification'] = ". ".join(g_parts) + "."

    # ============ MAGNETISM SCORE ============
    mag_score = 4.5
    mag_parts = []

    if followers >= 10000:
        mag_score += 3.5
        mag_parts.append(f"Strong LinkedIn following ({followers:,}) indicates industry influence")
    elif followers >= 5000:
        mag_score += 2.5
        mag_parts.append(f"Solid LinkedIn presence ({followers:,} followers)")
    elif followers >= 2000:
        mag_score += 1.5
        mag_parts.append(f"Moderate following ({followers:,} followers)")
    elif followers >= 1000:
        mag_score += 0.5
        mag_parts.append(f"Basic following ({followers:,} followers)")

    if connections >= 5000:
        mag_score += 1.5
        mag_parts.append(f"Extensive network ({connections:,}+ connections)")
    elif connections >= 2000:
        mag_score += 1.0
        mag_parts.append(f"Strong network ({connections:,}+ connections)")

    if has_forbes:
        mag_score += 1.5
        mag_parts.append("Public recognition enhances personal brand")

    if not mag_parts:
        mag_parts.append("Limited public profile data to assess influence")
        mag_score = 4.5

    scores['magnetism_score'] = min(10.0, round(mag_score, 1))
    justifications['magnetism_justification'] = ". ".join(mag_parts) + "."

    # ============ CURIOSITY SCORE ============
    c_score = 5.0
    c_parts = []

    skill_list = [s.strip() for s in skills.split(',') if s.strip()]
    if len(skill_list) >= 15:
        c_score += 1.5
        c_parts.append(f"Broad skill set ({len(skill_list)}+ skills) indicates continuous learning")
    elif len(skill_list) >= 8:
        c_score += 1.0
        c_parts.append(f"Diverse skills ({len(skill_list)} listed)")

    if is_phd and is_mba:
        c_score += 1.5
        c_parts.append("PhD and MBA shows intellectual range across research and business")
    if len(elite_schools) >= 2:
        c_score += 1.0
        c_parts.append("Multiple institutions suggests pursuit of learning")

    if not c_parts:
        c_parts.append("Standard professional development visible")
        c_score = 5.0

    scores['curiosity_score'] = min(10.0, round(c_score, 1))
    justifications['curiosity_justification'] = ". ".join(c_parts) + "."

    # ============ COACHABILITY SCORE ============
    coach_score = 6.5  # Hard to assess, default neutral-positive
    coach_parts = []

    if is_mba:
        coach_score += 1.0
        coach_parts.append("MBA suggests openness to learning business skills")
    if 'advisor' in all_text.lower() or 'mentor' in all_text.lower():
        coach_score += 1.0
        coach_parts.append("Engagement with advisors suggests receptiveness")
    if is_repeat_founder:
        coach_score += 0.5
        coach_parts.append("Repeat founder likely learned from previous experiences")

    if not coach_parts:
        coach_parts.append("Limited data to assess coachability. Baseline assumption positive")

    scores['coachability_score'] = min(10.0, round(coach_score, 1))
    justifications['coachability_justification'] = ". ".join(coach_parts) + "."

    # ============ TEAM CHEMISTRY SCORE ============
    team_score = 6.0
    team_parts = []

    if 'co-founder' in headline.lower():
        team_score += 1.5
        team_parts.append("Co-founder role indicates ability to work with partners")
    if 'co-founder' in prev_title.lower():
        team_score += 1.0
        team_parts.append("Previous co-founding experience")
    if 'team' in all_text.lower() or 'led' in all_text.lower():
        team_score += 0.5
        team_parts.append("Leadership experience visible")

    if not team_parts:
        team_parts.append("Limited data on team dynamics from profile")

    scores['team_chemistry_score'] = min(10.0, round(team_score, 1))
    justifications['team_chemistry_justification'] = ". ".join(team_parts) + "."

    # Calculate overall founder score
    all_scores = [scores[f'{k}_score'] for k in ['breakthrough', 'mission', 'achievements',
                  'work_ethic', 'grit', 'magnetism', 'curiosity', 'coachability', 'team_chemistry']]
    scores['founder_score'] = round(sum(all_scores) / len(all_scores), 2)

    # Build founder profile
    founder_profile = {
        'name': name,
        'linkedin': profile.get('profileUrl', profile.get('linkedinProfileUrl', '')),
        'bio': bio[:500] if bio else '',
        'schools': ', '.join(filter(None, [school, prev_school])),
        'degrees': ', '.join(filter(None, [degree, prev_degree])),
        'prior_employers': prev_company,
        'headline': headline,
        'location': profile.get('location', ''),
        'technical_competence': 'High' if has_advanced_degree or top_companies else 'Medium',
        'is_repeat_founder': 1 if is_repeat_founder else 0,
    }

    # Add scores and justifications
    founder_profile.update(scores)
    founder_profile.update(justifications)

    return founder_profile, thesis_theme


def main():
    print("=" * 70)
    print("Scoring Deepchecks Mar 2026 Founders")
    print("=" * 70)

    # Load PhantomBuster data
    with open('/tmp/deepchecks_founders_linkedin_mar2026.json', 'r') as f:
        profiles = json.load(f)

    print(f"Loaded {len(profiles)} founder profiles\n")

    # Load Pitchbook URLs CSV
    pitchbook_data = {}
    csv_path = '/Users/Ryan/Downloads/DeepchecksFounders - Sheet1.csv'
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_id = row.get('ID', '')
            pitchbook_data[company_id] = row.get('Pitchbook URL', '')

    print(f"Loaded {len(pitchbook_data)} Pitchbook URLs\n")

    # Load seed-data
    seed_path = Path(__file__).parent.parent / 'data' / 'seed-data.json'
    with open(seed_path, 'r') as f:
        seed_data = json.load(f)

    # Create company ID lookup
    company_idx = {c['id']: i for i, c in enumerate(seed_data['companies'])}

    # Track score distribution
    tier1 = []  # 8+
    tier2 = []  # 6-7.9
    tier3 = []  # <6

    updated = 0
    skipped = 0

    for profile in profiles:
        company_id = profile.get('ID', '')
        if not company_id:
            skipped += 1
            continue

        try:
            company_id_int = int(company_id)
        except ValueError:
            skipped += 1
            continue

        if company_id_int not in company_idx:
            print(f"  Warning: Company ID {company_id_int} not found in seed-data")
            skipped += 1
            continue

        idx = company_idx[company_id_int]
        company = seed_data['companies'][idx]

        # Score the founder
        founder_profile, thesis_theme = score_founder(profile)

        # Update company
        seed_data['companies'][idx]['founders'] = [founder_profile]
        seed_data['companies'][idx]['company_score'] = founder_profile['founder_score']

        # Add Pitchbook URL if available
        pitchbook_url = pitchbook_data.get(company_id, '')
        if pitchbook_url:
            seed_data['companies'][idx]['pitchbook_url'] = pitchbook_url

        # Update thesis theme if detected
        if thesis_theme != 'General' and not company.get('thesis_fit_theme'):
            seed_data['companies'][idx]['thesis_fit_theme'] = thesis_theme

        # Track tier
        score = founder_profile['founder_score']
        name = founder_profile['name']
        company_name = company['name']

        if score >= 8.0:
            tier1.append((company_name, name, score))
        elif score >= 6.0:
            tier2.append((company_name, name, score))
        else:
            tier3.append((company_name, name, score))

        print(f"  {company_name[:30]:<30} | {name[:20]:<20} | Score: {score:.1f}")
        updated += 1

    # Save updated seed data
    with open(seed_path, 'w') as f:
        json.dump(seed_data, f, indent=2)

    print("\n" + "=" * 70)
    print("SCORE DISTRIBUTION:")
    print("=" * 70)
    print(f"  Tier 1 (8.0+): {len(tier1)} founders - TOP PRIORITY")
    print(f"  Tier 2 (6.0-7.9): {len(tier2)} founders - SOLID")
    print(f"  Tier 3 (<6.0): {len(tier3)} founders - LOW PRIORITY")
    print(f"\n  Updated: {updated} | Skipped: {skipped}")

    if tier1:
        print("\n" + "=" * 70)
        print("TIER 1 FOUNDERS (8.0+) - PRIORITIZE THESE:")
        print("=" * 70)
        tier1.sort(key=lambda x: x[2], reverse=True)
        for company, name, score in tier1:
            print(f"  {score:.1f} | {company[:30]:<30} | {name}")

    if tier2:
        print("\n" + "=" * 70)
        print("TIER 2 FOUNDERS (6.0-7.9):")
        print("=" * 70)
        tier2.sort(key=lambda x: x[2], reverse=True)
        for company, name, score in tier2[:10]:  # Show top 10
            print(f"  {score:.1f} | {company[:30]:<30} | {name}")
        if len(tier2) > 10:
            print(f"  ... and {len(tier2) - 10} more")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. git add data/seed-data.json")
    print("2. git commit -m 'Score Deepchecks Mar 2026 founders'")
    print("3. git push origin main")
    print("4. Wait ~10 seconds for Vercel deployment")
    print("5. curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed")


if __name__ == "__main__":
    main()
