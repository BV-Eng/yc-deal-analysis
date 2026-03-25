#!/usr/bin/env python3
"""
Re-score StealthBot founders with detailed justifications and better differentiation.
Tier 1 (8+): Exceptional - elite schools, advanced degrees, top companies, successful exits
Tier 2 (6-7): Solid - good credentials, relevant experience
Tier 3 (4-5): Limited - sparse data or weak credentials
"""

import json
import csv
import re

# Elite credentials
ELITE_SCHOOLS = {
    'stanford': 'Stanford',
    'harvard': 'Harvard',
    'mit': 'MIT',
    'yale': 'Yale',
    'princeton': 'Princeton',
    'berkeley': 'UC Berkeley',
    'caltech': 'Caltech',
    'columbia': 'Columbia',
    'penn': 'Penn',
    'wharton': 'Wharton',
    'cornell': 'Cornell',
    'duke': 'Duke',
    'northwestern': 'Northwestern',
    'chicago': 'UChicago',
    'oxford': 'Oxford',
    'cambridge': 'Cambridge',
    'carnegie mellon': 'CMU',
    'cmu': 'CMU',
    'georgia tech': 'Georgia Tech',
    'johns hopkins': 'Johns Hopkins',
    'hopkins': 'Johns Hopkins',
    'ucla': 'UCLA',
    'nyu': 'NYU',
    'insead': 'INSEAD',
    'london business': 'LBS',
    'hbs': 'HBS',
}

TOP_COMPANIES = {
    'google': 'Google',
    'meta': 'Meta',
    'facebook': 'Facebook/Meta',
    'apple': 'Apple',
    'amazon': 'Amazon',
    'microsoft': 'Microsoft',
    'netflix': 'Netflix',
    'uber': 'Uber',
    'airbnb': 'Airbnb',
    'stripe': 'Stripe',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'palantir': 'Palantir',
    'snowflake': 'Snowflake',
    'databricks': 'Databricks',
    'datadog': 'Datadog',
    'mckinsey': 'McKinsey',
    'bain': 'Bain',
    'bcg': 'BCG',
    'goldman': 'Goldman Sachs',
    'morgan stanley': 'Morgan Stanley',
    'jpmorgan': 'JPMorgan',
    'sequoia': 'Sequoia',
    'a16z': 'a16z',
    'andreessen': 'a16z',
    'tesla': 'Tesla',
    'spacex': 'SpaceX',
    'nasa': 'NASA',
    'nih': 'NIH',
    'arpa': 'ARPA',
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
    name_lower = name.lower()
    text_lower = text.lower()
    combined = f"{name_lower} {text_lower}"

    if 'ph.d' in combined or 'phd' in combined or 'doctor of philosophy' in combined:
        creds.append('PhD')
    if ', md' in name_lower or ' md,' in name_lower or 'doctor of medicine' in text_lower or 'm.d.' in combined:
        creds.append('MD')
    if ', jd' in name_lower or 'juris doctor' in text_lower or 'j.d.' in combined:
        creds.append('JD')
    if 'mba' in combined or 'master of business' in text_lower:
        creds.append('MBA')
    if ', ms' in name_lower or 'master of science' in text_lower:
        creds.append('MS')
    if ', mph' in name_lower or 'master of public health' in text_lower:
        creds.append('MPH')
    if ', dds' in name_lower or 'doctor of dental' in text_lower:
        creds.append('DDS')
    if 'faans' in name_lower or 'facs' in name_lower or 'facc' in name_lower:
        creds.append('Board Certified Fellow')

    return creds

def score_founder(name, profile):
    """Generate detailed scores and full-sentence justifications."""

    # Extract all available data
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

    # Combine text for analysis
    all_text = f"{name} {headline} {bio} {job_title} {job_desc} {prev_title} {prev_job_desc} {company_desc}"
    edu_text = f"{school} {degree} {field} {prev_school} {prev_degree}"

    # Extract key info
    elite_schools = find_elite_schools(edu_text + " " + bio)
    top_companies = find_top_companies(all_text + " " + prev_company)
    credentials = extract_credentials(name, edu_text + " " + bio)

    # Detect patterns
    is_phd = 'PhD' in credentials
    is_md = 'MD' in credentials
    is_jd = 'JD' in credentials
    is_mba = 'MBA' in credentials
    is_fellow = 'Board Certified Fellow' in credentials
    is_repeat_founder = 'founder' in prev_title.lower() or ('co-founder' in headline.lower() and 'founder' in bio.lower())
    is_current_founder = 'founder' in headline.lower() or 'ceo' in headline.lower()

    # Domain focus
    health_focus = any(k in all_text.lower() for k in ['health', 'medical', 'patient', 'clinical', 'physician', 'doctor', 'hospital', 'biotech', 'therapeutic', 'pharma', 'surgery', 'cardio', 'neuro', 'oncol'])
    climate_focus = any(k in all_text.lower() for k in ['climate', 'energy', 'solar', 'renewable', 'sustainability', 'carbon', 'clean'])

    # Years of experience
    years_match = re.search(r'(\d+)\+?\s*years?', bio.lower())
    years_exp = int(years_match.group(1)) if years_match else 0

    # Check for exits/acquisitions
    has_exit = any(k in all_text.lower() for k in ['acquired', 'acquisition', 'exit', 'sold to', 'ipo'])

    scores = {}
    justifications = {}

    # ============ BREAKTHROUGH SCORE ============
    b_score = 5.0
    b_parts = []

    if is_phd:
        b_score += 2.5
        field_info = field if field else "unknown field"
        b_parts.append(f"PhD candidate/holder demonstrates deep technical expertise")
    if is_md:
        b_score += 2.0
        b_parts.append(f"Medical degree provides unique clinical insights")
    if is_jd:
        b_score += 1.5
        b_parts.append(f"Legal training adds regulatory/strategic perspective")
    if elite_schools:
        b_score += 1.5
        b_parts.append(f"Education at {', '.join(elite_schools[:2])} indicates intellectual caliber")
    if top_companies:
        b_score += 1.0
        b_parts.append(f"Experience at {', '.join(top_companies[:2])} exposes to world-class practices")
    has_arpa = 'arpa' in all_text.lower() or 'darpa' in all_text.lower() or 'arpa-h' in all_text.lower()
    if has_arpa:
        b_score += 2.5
        b_parts.append(f"ARPA/DARPA/ARPA-H involvement signals working on frontier government research")
    if is_phd and is_md:
        b_score += 1.0
        b_parts.append(f"MD-PhD combination is rare and powerful for healthcare innovation")

    if not b_parts:
        b_parts.append("Limited evidence of breakthrough thinking from available profile data")

    scores['breakthrough_score'] = min(10.0, round(b_score, 1))
    justifications['breakthrough_justification'] = ". ".join(b_parts) + "."

    # ============ MISSION SCORE ============
    m_score = 5.0
    m_parts = []

    if has_arpa:
        m_score += 1.5
        m_parts.append(f"ARPA/DARPA involvement shows commitment to high-impact government research missions")
    if health_focus and is_md:
        m_score += 3.0
        m_parts.append(f"Physician founder building in healthcare shows deep personal connection to the problem")
    elif health_focus:
        m_score += 1.5
        m_parts.append(f"Healthcare focus aligns with improving human health")
    if climate_focus:
        m_score += 1.5
        m_parts.append(f"Climate/sustainability focus demonstrates commitment to planetary impact")
    if is_repeat_founder:
        m_score += 1.5
        m_parts.append(f"Repeat founder shows sustained commitment to building companies")
    if years_exp >= 15:
        m_score += 1.0
        m_parts.append(f"{years_exp}+ years in domain indicates deep commitment")
    if 'passionate' in bio.lower() or 'mission' in bio.lower() or 'dedicated' in bio.lower():
        m_score += 0.5
        m_parts.append(f"Language in bio suggests mission-driven motivation")
    if is_phd:
        m_score += 1.5
        m_parts.append(f"PhD pursuit demonstrates deep commitment to advancing knowledge in field")

    if not m_parts:
        m_parts.append("Career trajectory shows professional progression but mission alignment unclear from available data")

    scores['mission_score'] = min(10.0, round(m_score, 1))
    justifications['mission_justification'] = ". ".join(m_parts) + "."

    # ============ ACHIEVEMENTS SCORE ============
    a_score = 5.0
    a_parts = []

    if is_phd:
        a_score += 2.5
        a_parts.append(f"PhD demonstrates intellectual rigor and ability to complete multi-year research")
    if is_md:
        a_score += 2.5
        a_parts.append(f"Medical degree requires exceptional academic achievement")
    if is_jd:
        a_score += 2.0
        a_parts.append(f"Law degree from competitive institution")
    if is_fellow:
        a_score += 2.0
        a_parts.append(f"Board certification/fellowship indicates peer recognition of expertise")
    if is_mba:
        a_score += 1.0
        a_parts.append(f"MBA adds business acumen")
    if elite_schools:
        a_score += 2.0
        schools_str = ', '.join(elite_schools[:3])
        a_parts.append(f"Elite education ({schools_str}) demonstrates academic excellence")
    if top_companies:
        a_score += 1.5
        companies_str = ', '.join(top_companies[:2])
        a_parts.append(f"Experience at {companies_str} validates professional caliber")
    if has_exit:
        a_score += 2.0
        a_parts.append(f"Previous exit/acquisition demonstrates ability to build valuable companies")
    if years_exp >= 20:
        a_score += 1.0
        a_parts.append(f"20+ years of experience shows sustained professional success")

    if not a_parts:
        a_parts.append("Standard professional credentials without standout achievements visible in profile")

    scores['achievements_score'] = min(10.0, round(a_score, 1))
    justifications['achievements_justification'] = ". ".join(a_parts) + "."

    # ============ WORK ETHIC SCORE ============
    w_score = 5.5
    w_parts = []

    if is_repeat_founder:
        w_score += 2.0
        w_parts.append(f"Repeat founder has proven ability to build from scratch multiple times")
    if top_companies:
        w_score += 1.5
        w_parts.append(f"Operating at {top_companies[0]} requires high performance and execution")
    if is_phd or is_md:
        w_score += 1.5
        w_parts.append(f"Completing rigorous {credentials[0] if credentials else 'advanced'} training demonstrates sustained effort")
    if has_exit:
        w_score += 1.5
        w_parts.append(f"Previous exit shows ability to execute through full company lifecycle")
    if years_exp >= 15:
        w_score += 1.0
        w_parts.append(f"Long career ({years_exp}+ years) indicates consistent execution")
    if 'built' in all_text.lower() or 'scaled' in all_text.lower() or 'grew' in all_text.lower():
        w_score += 0.5
        w_parts.append(f"Evidence of building/scaling in background")

    if not w_parts:
        w_parts.append("Professional work history present but limited evidence of exceptional execution from profile data")

    scores['work_ethic_score'] = min(10.0, round(w_score, 1))
    justifications['work_ethic_justification'] = ". ".join(w_parts) + "."

    # ============ GRIT SCORE ============
    g_score = 5.5
    g_parts = []

    if is_repeat_founder:
        g_score += 2.0
        g_parts.append(f"Starting multiple companies shows persistence through inevitable setbacks")
    if is_phd:
        g_score += 2.5
        g_parts.append(f"PhD pursuit/completion requires 5-7 years of perseverance through research setbacks and uncertainty")
    if is_md:
        g_score += 1.5
        g_parts.append(f"Medical training is grueling multi-year commitment")
    if 'immigrant' in bio.lower() or 'first-generation' in bio.lower() or 'self-taught' in bio.lower():
        g_score += 2.0
        g_parts.append(f"Overcame significant personal challenges based on background")
    if years_exp >= 20:
        g_score += 1.0
        g_parts.append(f"20+ year career demonstrates sustained persistence")

    if not g_parts:
        g_parts.append("Career shows progression but limited evidence of overcoming significant adversity visible in profile")

    scores['grit_score'] = min(10.0, round(g_score, 1))
    justifications['grit_justification'] = ". ".join(g_parts) + "."

    # ============ MAGNETISM SCORE ============
    mag_score = 5.0
    mag_parts = []

    if followers >= 20000:
        mag_score += 4.0
        mag_parts.append(f"Exceptional LinkedIn reach ({followers:,} followers) indicates strong personal brand and influence")
    elif followers >= 10000:
        mag_score += 3.0
        mag_parts.append(f"Strong LinkedIn following ({followers:,} followers) suggests industry influence")
    elif followers >= 5000:
        mag_score += 2.0
        mag_parts.append(f"Solid LinkedIn presence ({followers:,} followers) indicates networking ability")
    elif followers >= 2000:
        mag_score += 1.0
        mag_parts.append(f"Moderate LinkedIn following ({followers:,} followers)")

    if connections >= 10000:
        mag_score += 1.5
        mag_parts.append(f"Extensive professional network ({connections:,}+ connections)")
    elif connections >= 5000:
        mag_score += 1.0
        mag_parts.append(f"Strong professional network ({connections:,}+ connections)")

    if is_fellow:
        mag_score += 1.0
        mag_parts.append(f"Professional recognition through board certification/fellowship")

    if not mag_parts:
        mag_parts.append("Moderate professional network. Limited public profile data to assess influence")

    scores['magnetism_score'] = min(10.0, round(mag_score, 1))
    justifications['magnetism_justification'] = ". ".join(mag_parts) + "."

    # ============ CURIOSITY SCORE ============
    c_score = 5.5
    c_parts = []

    skill_list = [s.strip() for s in skills.split(',') if s.strip()]
    if len(skill_list) >= 20:
        c_score += 1.5
        c_parts.append(f"Broad skill set ({len(skill_list)}+ listed skills) indicates continuous learning")
    elif len(skill_list) >= 10:
        c_score += 1.0
        c_parts.append(f"Diverse skills ({len(skill_list)} listed) show learning breadth")

    if is_phd and is_mba:
        c_score += 1.5
        c_parts.append(f"Pursued both PhD and MBA showing intellectual range across research and business")
    if is_md and is_mba:
        c_score += 1.0
        c_parts.append(f"MD + MBA combination shows breadth of interests")
    if len(elite_schools) >= 2:
        c_score += 1.0
        c_parts.append(f"Multiple elite institutions suggests continuous pursuit of learning")
    if health_focus and climate_focus:
        c_score += 1.0
        c_parts.append(f"Cross-domain interests spanning health and climate")

    if not c_parts:
        c_parts.append("Standard professional development. Limited evidence of exceptional intellectual curiosity from profile")

    scores['curiosity_score'] = min(10.0, round(c_score, 1))
    justifications['curiosity_justification'] = ". ".join(c_parts) + "."

    # ============ COACHABILITY SCORE ============
    coach_score = 7.0  # Hard to assess from LinkedIn, default to positive assumption
    coach_parts = []

    if is_mba:
        coach_score += 1.0
        coach_parts.append(f"Pursuing MBA suggests openness to learning business skills")
    if 'advisor' in all_text.lower() or 'mentor' in all_text.lower() or 'board' in all_text.lower():
        coach_score += 1.0
        coach_parts.append(f"Engagement with advisors/board suggests receptiveness to guidance")
    if is_repeat_founder:
        coach_score += 0.5
        coach_parts.append(f"Repeat founder likely learned from previous experiences")

    if not coach_parts:
        coach_parts.append("Limited data available to assess coachability. Baseline assumption of openness to feedback")

    scores['coachability_score'] = min(10.0, round(coach_score, 1))
    justifications['coachability_justification'] = ". ".join(coach_parts) + "."

    # ============ TEAM CHEMISTRY SCORE ============
    team_score = 6.5  # Default positive - most professionals can work in teams
    team_parts = []

    if 'co-founder' in headline.lower():
        team_score += 1.5
        team_parts.append(f"Current co-founder role indicates ability to work closely with partners")
    if 'co-founder' in prev_title.lower():
        team_score += 1.5
        team_parts.append(f"Previous co-founding experience shows track record of team building")
    if 'team' in all_text.lower() or 'led' in all_text.lower() or 'managed' in all_text.lower():
        team_score += 1.0
        team_parts.append(f"Leadership/management experience visible in background")

    if not team_parts:
        team_parts.append("Limited data on team dynamics and collaboration history from profile")

    scores['team_chemistry_score'] = min(10.0, round(team_score, 1))
    justifications['team_chemistry_justification'] = ". ".join(team_parts) + "."

    # Calculate overall founder score
    all_scores = [scores[f'{k}_score'] for k in ['breakthrough', 'mission', 'achievements', 'work_ethic', 'grit', 'magnetism', 'curiosity', 'coachability', 'team_chemistry']]
    scores['founder_score'] = round(sum(all_scores) / len(all_scores), 2)

    return scores, justifications


def main():
    print("=" * 70)
    print("Re-scoring StealthBot Founders v2 - Better Justifications")
    print("=" * 70)

    # Load CSV
    csv_path = '/Users/Ryan/Downloads/result (19).csv'
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        csv_data = {}
        for r in reader:
            if r.get('refreshedAt', '').startswith('2026-03'):
                name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip()
                csv_data[name.lower()] = r

    print(f"Loaded {len(csv_data)} March 2026 profiles")

    # Load seed-data
    with open('data/seed-data.json', 'r') as f:
        data = json.load(f)

    updated = 0
    tier1 = []  # 8+
    tier2 = []  # 6-8
    tier3 = []  # <6

    for i, c in enumerate(data['companies']):
        if 'StealthBot' not in (c.get('source') or ''):
            continue

        founders = c.get('founders', [])
        if not founders:
            continue

        f = founders[0]
        name = f.get('name', '')

        # Find profile
        profile = csv_data.get(name.lower())
        if not profile:
            # Try matching by first name
            for k, v in csv_data.items():
                if name.split()[0].lower() in k:
                    profile = v
                    break

        if not profile:
            continue

        old_score = f.get('founder_score', 0)
        scores, justifications = score_founder(name, profile)
        new_score = scores['founder_score']

        # Update
        for key, value in scores.items():
            data['companies'][i]['founders'][0][key] = value
        for key, value in justifications.items():
            data['companies'][i]['founders'][0][key] = value
        data['companies'][i]['company_score'] = new_score

        # Track tiers
        if new_score >= 8.0:
            tier1.append((name, new_score))
        elif new_score >= 6.0:
            tier2.append((name, new_score))
        else:
            tier3.append((name, new_score))

        if abs(new_score - old_score) > 0.3:
            arrow = "↑" if new_score > old_score else "↓"
            print(f"  {name[:40]:<40} {old_score:.1f} → {new_score:.1f} {arrow}")

        updated += 1

    # Save
    with open('data/seed-data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {updated} founders")
    print("\n" + "=" * 70)
    print("SCORE DISTRIBUTION:")
    print(f"  Tier 1 (8.0+): {len(tier1)} founders - GREEN on dashboard")
    print(f"  Tier 2 (6.0-7.9): {len(tier2)} founders")
    print(f"  Tier 3 (<6.0): {len(tier3)} founders")

    if tier1:
        print("\n" + "=" * 70)
        print("TIER 1 FOUNDERS (8.0+):")
        tier1.sort(key=lambda x: x[1], reverse=True)
        for name, score in tier1[:15]:
            print(f"  {score:.1f} - {name}")


if __name__ == "__main__":
    main()
