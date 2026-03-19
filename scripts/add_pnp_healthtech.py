#!/usr/bin/env python3
"""
Add PNP Health Tech Pitch Session companies (3/20/2026) to seed-data.json
"""

import json
from datetime import datetime

# Company data from the PDF
companies_raw = [
    {
        "name": "Orange Biomed",
        "brief": "Orange Biomed provides an at-home HbA1c monitoring system that delivers lab-quality results in minutes. Our microfluidic technology makes routine A1c tracking simple, accurate, and accessible for people with diabetes.",
        "raised": "$7M",
        "country": "S.Korea",
        "website": "https://orangebiomed.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "SynchNeuro",
        "brief": "We are developing the world's first brain signal-based non-invasive glucose monitor for metabolic health management. Our system provides actionable daily guidance related to glucose fluctuations, sleep quality, stress and activity levels to guide lifestyle decisions.",
        "raised": "$5.6M",
        "country": "USA",
        "website": "https://synchneuro.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "giftshed",
        "brief": "We Provide the Ultimate Liquid Biopsy Platform for Early Cancer Detection.",
        "raised": "$500K",
        "country": "USA/S.Korea",
        "website": "https://www.giftshed.bio/",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Ilico Genetics",
        "brief": "Ilico Genetics pioneers early gastric cancer detection with a patented liquid biopsy test using methylated DNA biomarkers and a ML algorithm. Our minimally invasive solution enables accurate, cost-effective screening, improving survival rates and reducing healthcare costs.",
        "raised": "$1M",
        "country": "USA",
        "website": "https://ilicogenetics.com",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Amplified Sciences",
        "brief": "Amplified Sciences is revolutionizing disease detection with a commercial stage test that helps physicians more accurately detect risk for pancreatic cancer built on their ultra-sensitive optical reporter platform.",
        "raised": "$6.4M",
        "country": "USA",
        "website": "https://amplifiedsciences.com",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Grannus Therapeutics",
        "brief": "Grannus therapeutics is a biotech company focused on the development of a new therapeutic option for patients with ovarian, prostate, breast, and pancreatic cancers. Our lead program leverages synthetic lethality to increase the number of patients eligible for PARPi by inducing 'BRCAness'.",
        "raised": "$3.5M",
        "country": "USA",
        "website": "https://grannustherapeutics.com",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "BioPhenyx",
        "brief": "BioPhenyx has invented CRISPR-Select, your Truth Detector in Drug Development and Use, Improving Success-Rates from Targets to Patients.",
        "raised": "€300K",
        "country": "Denmark",
        "website": "https://biophenyx.com",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Variational AI",
        "brief": "Foundation model for small molecule drug discovery.",
        "raised": "$9M",
        "country": "Canada",
        "website": "https://variational.ai",
        "category": "Biotech/AI",
        "thesis_theme": "Human Health"
    },
    {
        "name": "iOrganBio",
        "brief": "iOrganBio's (iOB) CellForge™ Platform brings precision engineering to the creation of human cells and organoids with unmatched reproducible, scalable, and AI-guided cell manufacturing for in vitro modeling and cell therapies.",
        "raised": "$2M",
        "country": "USA",
        "website": "https://iorgan.bio",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Forage Evolution",
        "brief": "Forage Evolution is building the next-generation workhorse for biotech discovery, a variant of the fastest growing organism on Earth that we engineered with the first molecular DNA data port. Our flagship Forager-1 cuts hands-on processing by 85% and accelerates timelines >3 fold.",
        "raised": "$410K",
        "country": "USA",
        "website": "https://forageevo.com",
        "category": "Biotech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Fermeate",
        "brief": "Fermeate pioneers optogenetics (light) and photomolecular gene circuits to control microbial fermentation. Essentially, software-like level of control, and on-demand on/off switching that allows biology to live up to the ideal of 'programmability'.",
        "raised": "$875K",
        "country": "USA",
        "website": "https://fermeate.com",
        "category": "Biotech",
        "thesis_theme": "Sustainable Industry"
    },
    {
        "name": "Weddell Technologies",
        "brief": "Weddell Technologies is developing a semiconductor chip sensor technology for accurate and portable DNA sequencing for wellness and healthcare applications. The company has proof of concept data for the technology through non-dilutive grants, and is raising funding for system integration.",
        "raised": "$750K",
        "country": "USA",
        "website": None,  # Not in PDF links
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "LiVeritas Biosciences",
        "brief": "LiVeritas is building the agentic AI Lab Operating System for biopharma, automating regulated testing and FDA submissions with compliance-grade intelligence and structured, traceable data.",
        "raised": "$2M",
        "country": "USA",
        "website": "https://liveritas.bio",
        "category": "Biotech/AI",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Hill Research (TriClick)",
        "brief": "Hill Research developed TriClick, a multi-agent AI platform that helps pharmaceutical and biotech companies automate clinical data analysis and reporting. By reducing programming errors by 45%, TriClick improves efficiency, accuracy, and regulatory compliance in clinical submissions.",
        "raised": "$15M",
        "country": "USA",
        "website": "https://hillresearch.ai",
        "category": "Biotech/AI",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Turbo Radiology",
        "brief": "Software as a service, Radiology.",
        "raised": "$1.5M",
        "country": "USA",
        "website": "https://turborad.com/",
        "category": "Health Tech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Wosler",
        "brief": "Wosler Corp. delivers remote robotic ultrasound and AI-powered admin automation to solve sonographer shortages and reduce imaging clinic costs. Its flagship SonoSystem enables diagnostic-quality scans without patient-side staff, expanding access to care in underserved regions.",
        "raised": "$1M",
        "country": "Canada",
        "website": "https://wosler.ca",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Siloton",
        "brief": "Siloton is a MedTech-DeepTech start up solving capacity and access challenges in ophthalmology with an innovative new diagnostic imaging device. Using optical chip technology paired with AI, Siloton unlocks greater efficiency for providers and improved care for patients.",
        "raised": "£1.3M",
        "country": "UK",
        "website": "https://siloton.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Azalea Vision",
        "brief": "Azalea Vision is a health-tech company developing the first intelligent, lens-embedded system that senses, adapts, and connects in real time to improve vision and monitor eye health. Our lens integrates adaptive optics, microelectronics, and connectivity. It can measure biomarkers like glucose.",
        "raised": "$17M",
        "country": "Belgium",
        "website": "https://azaleavision.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Lambda Surgical",
        "brief": "Lambda is building the physical intelligence layer for surgery. Our proprietary LiDAR-based platform improves precision in minimally invasive procedures and unlocks the missing ingredient for surgical autonomy: an adaptive world model of the operative field that can learn from human surgeons.",
        "raised": "$1M",
        "country": "USA",
        "website": "https://lambdasurgical.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "KOVE Medical",
        "brief": "We help saving babies before they are born by tackling premature birth following in-utero surgeries.",
        "raised": "$3M",
        "country": "Switzerland",
        "website": "https://kovemedical.com",
        "category": "Medtech (Hardware)",
        "thesis_theme": "Human Health"
    },
    {
        "name": "GelSana",
        "brief": "GelSana is developing innovative polymer wound dressings to generate better clinical outcomes. Our product Cleragel is the only wound care solution with potential to address all major challenges of the wound healing cascade by reducing inflammation, repelling bacteria, and balancing moisture.",
        "raised": "$5.5M",
        "country": "USA",
        "website": "https://gelsanatherapeutics.com",
        "category": "Medtech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Paperbox",
        "brief": "Paperbox is building gaming solution to allow early identification of neurodevelopmental issues, providing early and preventive intervention.",
        "raised": "$600K",
        "country": "Italy",
        "website": "https://paperbox.health",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Actuwell Health Application",
        "brief": "We are patient focused medical app to help schedule appointments, share medical documents and track health.",
        "raised": "$150K",
        "country": "Canada",
        "website": "https://actuwell.ca",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Vayo Technologies",
        "brief": "Vayo is an AI-powered patient management and coordination SaaS platform that streamlines access to support resources for both individuals and organizations.",
        "raised": "$125K",
        "country": "USA",
        "website": "https://myvayo.com",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "DataSense (SolidHealth.AI)",
        "brief": "SolidHealth.AI is a care continuity concierge that consolidates fragmented consumer EHR data into a health profile, enriched with wearables and ambient sensor data to reduce care gaps and improve outcomes.",
        "raised": "$240K",
        "country": "USA",
        "website": "https://solidhealth.ai",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "THIER",
        "brief": "THIER the AI Enabled Mobile Platform for the Prevention of Lifestyle Diseases.",
        "raised": "$10K",
        "country": "UK",
        "website": "https://www.thier.io/",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Lumina Salud",
        "brief": "Obesity is rising globally, yet traditional weight-loss methods have a long-term success rate of less than 1%. Lumina is a comprehensive digital clinic using GLP-1 medications as a tool to enable lasting lifestyle changes and sustainable weight loss.",
        "raised": "$350K",
        "country": "Spain",
        "website": "https://luminasalud.com",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "OwnaHealth",
        "brief": "OwnaHealth is a clinically-proven, tech-enabled service that combines medical supervision, one-on-one coaching, continuous health tracking, and therapeutic nutrition to drive real, lasting results in patients with type 2 diabetes — even in the hardest-to-treat populations.",
        "raised": "$2.4M",
        "country": "USA",
        "website": "https://owna.health",
        "category": "Digital Health",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Avacina Diagnostics",
        "brief": "Avacina Diagnostics delivers integrated hardware and software solutions for diabetes care. Our proprietary Senna platform combines novel glucose testing hardware (SennaOne), clinical decision support for physicians (SennaMD), and population health analytics for insurers (SennaEnterprise).",
        "raised": "$150K",
        "country": "USA",
        "website": "https://avacina.com",
        "category": "Medtech",
        "thesis_theme": "Human Health"
    },
    {
        "name": "Healthpro.id",
        "brief": "Smart workforce solution for healthcare.",
        "raised": "$300K",
        "country": "Indonesia",
        "website": "https://healthpro.id",
        "category": "Health Tech",
        "thesis_theme": "Tomorrow's Workforce"
    },
    {
        "name": "Ninacare",
        "brief": "Ninacare is Italy's leading AI-powered platform connecting healthcare professionals and organizations, cutting hiring time by 75%.",
        "raised": "€225K",
        "country": "Italy",
        "website": "https://ninacare.it",
        "category": "Health Tech",
        "thesis_theme": "Tomorrow's Workforce"
    },
    {
        "name": "Mora Health",
        "brief": "Mora Health is an AI platform that recruits, trains, and places Latin American nurses in U.S. hospitals through TN visas. It automates screening, education, and placement to scale cross-border staffing efficiently. The company partners with top U.S. staffing agencies to power global nurse mobility.",
        "raised": "$1.4M",
        "country": "USA",
        "website": "https://mora.health",
        "category": "Health Tech",
        "thesis_theme": "Tomorrow's Workforce"
    },
    {
        "name": "databaum",
        "brief": "Data intelligence for regenerative agriculture. We transform complex field & climate data to actionable insights.",
        "raised": "$500K",
        "country": "Switzerland/Germany",
        "website": "https://databaum.ch",
        "category": "AgTech",
        "thesis_theme": "Sustainable Industry"
    },
    {
        "name": "Knex (Birdoo)",
        "brief": "Birdoo is a HESaaS precision farming platform for broilers. We use advanced vision intelligence and planning tools to help integrators manage flock growth with real time interventions and align the whole value chain.",
        "raised": "$4M",
        "country": "USA",
        "website": "https://birdoo.us",
        "category": "AgTech",
        "thesis_theme": "Sustainable Industry"
    }
]

def parse_raised(raised_str):
    """Convert raised string to numeric value for scoring"""
    if not raised_str:
        return 0
    raised_str = raised_str.replace(",", "").strip()
    multiplier = 1
    if "M" in raised_str:
        multiplier = 1000000
        raised_str = raised_str.replace("M", "")
    elif "K" in raised_str:
        multiplier = 1000
        raised_str = raised_str.replace("K", "")
    # Remove currency symbols
    for c in ["$", "€", "£"]:
        raised_str = raised_str.replace(c, "")
    try:
        return float(raised_str) * multiplier
    except:
        return 0

def generate_scores(company):
    """Generate scores based on company characteristics"""
    theme = company["thesis_theme"]
    category = company["category"]
    raised = parse_raised(company["raised"])

    # Thesis fit score (25% weight)
    thesis_scores = {
        "Human Health": 8.0,
        "Sustainable Industry": 7.5,
        "Tomorrow's Workforce": 7.0,
        "Off-Thesis": 4.0
    }
    thesis_fit_score = thesis_scores.get(theme, 5.0)

    # Boost for certain categories within themes
    if theme == "Human Health" and "Biotech" in category:
        thesis_fit_score += 0.5
    if theme == "Sustainable Industry" and "AgTech" in category:
        thesis_fit_score += 0.5

    thesis_fit_justification = f"Aligns with Better.vc {theme} theme. " + \
        (f"Deep tech focus in {category}." if "Deep Tech" in category or "Biotech" in category or "Medtech" in category else f"Focus area: {category}.")

    # Product score (10% weight) - based on category depth
    product_scores = {
        "Biotech": 7.0,
        "Biotech/AI": 7.5,
        "Medtech (Hardware)": 7.0,
        "Medtech": 6.5,
        "Digital Health": 5.5,
        "Health Tech": 5.5,
        "AgTech": 6.5
    }
    product_score = product_scores.get(category, 5.5)
    product_justification = f"{company['brief'][:100]}... Category: {category}."

    # Traction score (5% weight) - based on funding
    if raised >= 10000000:
        traction_score = 8.0
    elif raised >= 5000000:
        traction_score = 7.0
    elif raised >= 2000000:
        traction_score = 6.0
    elif raised >= 1000000:
        traction_score = 5.5
    elif raised >= 500000:
        traction_score = 5.0
    else:
        traction_score = 4.0
    traction_justification = f"Raised {company['raised']}. PNP Health Tech batch acceptance signals validation."

    # Team score (15% weight) - placeholder since we don't have founder data
    team_score = 5.5
    team_justification = "Founder data pending enrichment."

    # Business model score (10% weight)
    business_model_score = 6.0
    business_model_justification = "B2B healthcare model (aligns with fund focus)."

    # Market score (10% weight)
    market_score = 6.5
    market_justification = f"Operating in {category} market. Healthcare/Health Tech markets have strong tailwinds."

    # Impact score (20% weight)
    if theme == "Human Health":
        impact_score = 7.0
        impact_justification = "Potential to improve health outcomes and reduce cost of care."
    elif theme == "Sustainable Industry":
        impact_score = 7.0
        impact_justification = "Potential to reduce environmental impact and improve sustainability."
    elif theme == "Tomorrow's Workforce":
        impact_score = 6.5
        impact_justification = "Potential to improve workforce efficiency and access."
    else:
        impact_score = 5.0
        impact_justification = ""

    # Deal score (5% weight)
    deal_score = 6.0
    deal_justification = f"PNP Health Tech batch company. Location: {company['country']}."

    # Calculate weighted total
    weighted_total = (
        thesis_fit_score * 0.25 +
        team_score * 0.15 +
        product_score * 0.10 +
        business_model_score * 0.10 +
        market_score * 0.10 +
        impact_score * 0.20 +
        traction_score * 0.05 +
        deal_score * 0.05
    )

    return {
        "thesis_fit_theme": theme,
        "thesis_fit_score": round(thesis_fit_score, 1),
        "thesis_fit_weight": 25,
        "thesis_fit_justification": thesis_fit_justification,
        "team_score": round(team_score, 1),
        "team_weight": 15,
        "team_justification": team_justification,
        "product_score": round(product_score, 1),
        "product_weight": 10,
        "product_justification": product_justification,
        "business_model_score": round(business_model_score, 1),
        "business_model_weight": 10,
        "business_model_justification": business_model_justification,
        "market_score": round(market_score, 1),
        "market_weight": 10,
        "market_justification": market_justification,
        "impact_score": round(impact_score, 1),
        "impact_weight": 20,
        "impact_justification": impact_justification,
        "traction_score": round(traction_score, 1),
        "traction_weight": 5,
        "traction_justification": traction_justification,
        "deal_score": round(deal_score, 1),
        "deal_weight": 5,
        "deal_justification": deal_justification,
        "company_score": round(weighted_total, 2),
        "weighted_total": round(weighted_total, 2)
    }

def create_company_entry(company, idx, start_id):
    """Create a full company entry for seed-data.json"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scores = generate_scores(company)

    slug = company["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace(".", "")

    entry = {
        "id": start_id + idx,
        "name": company["name"],
        "slug": slug,
        "one_liner": company["brief"][:200] + "..." if len(company["brief"]) > 200 else company["brief"],
        "long_description": company["brief"],
        "batch": "PNP Health Tech Mar 2026",
        "source": "PNP (3/20/26)",
        "status": "Not Contacted",
        "industries": company["category"],
        "subindustry": company["category"],
        "tags": f"Health Tech, {company['category']}, PNP",
        "website": company["website"],
        "all_locations": company["country"],
        "team_size": 0,
        "year_founded": None,
        "logo_url": "",
        "b2b_b2c": "B2B",
        "technology_type": "Deep Tech" if "Biotech" in company["category"] or "Medtech" in company["category"] else "Software",
        "business_model": None,
        "next_action": None,
        "custom_tags": None,
        "created_at": now,
        "updated_at": now,
        "owner": None,
        "contact_email": None,
        "pitchbook_url": None,
        "founders": [],
        "interactions": [],
        "notes": [],
        "founder_names": "",
        "founder_linkedin_data": None,
        "has_female_founder": 0,
        "has_black_founder": 0,
        "has_hispanic_founder": 0,
        "last_interaction_date": None,
        "avg_founder_score": None,
        **scores
    }

    return entry

def main():
    # Load existing seed data
    with open("data/seed-data.json", "r") as f:
        data = json.load(f)

    # Find max ID
    max_id = max(c["id"] for c in data["companies"])
    start_id = max_id + 1

    print(f"Existing companies: {len(data['companies'])}")
    print(f"Starting ID: {start_id}")

    # Create new company entries
    new_companies = []
    for idx, company in enumerate(companies_raw):
        entry = create_company_entry(company, idx, start_id)
        new_companies.append(entry)
        print(f"Added: {entry['name']} (ID: {entry['id']}, Score: {entry['company_score']})")

    # Add to data
    data["companies"].extend(new_companies)

    # Save
    with open("data/seed-data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Added {len(new_companies)} PNP Health Tech companies")
    print(f"Total companies now: {len(data['companies'])}")

if __name__ == "__main__":
    main()
