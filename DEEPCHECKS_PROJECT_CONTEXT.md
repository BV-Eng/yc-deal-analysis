# Deepchecks Integration Project Context

## Project Overview
Adapting YC Deal Analysis CRM to also handle Deepchecks deals (deep tech startups from Julian Shapiro's platform).

## Repository
- GitHub: https://github.com/BV-Eng/yc-deal-analysis
- Live: https://yc-deal-analysis.vercel.app/
- Deployment: Vercel (auto-deploys from commits by eng@better.vc)

## Data Structure
- **189 total companies**: 149 YC + 40 Deepchecks
- Stored in Upstash Redis (production) or seed-data.json (local)
- Reload endpoint: `POST /api/admin/reload-seed`

## Key Files
- `frontend/dist/index.html` - Single-file React app
- `backend/server-redis.js` - Express API server
- `backend/database-redis.js` - Database layer
- `data/seed-data.json` - Seed data with all companies

## Completed Work
1. Added 40 Deepchecks companies from Feb 2026 batch
2. Added "source" filter dropdown (YC/Deepchecks)
3. Added "Source" column with badges
4. Changed title to "Deal Analysis"
5. Fixed founder names (from "Founder" placeholder to actual names)
6. Fixed default sort to show newest first (ID DESC)
7. Fixed scoring to use company_score when no founder data

## Deepchecks Companies (in order)
1. Convergent Bioscience - Agriculture - james.kirk@convergent-bio.com
2. Orbital Sentry - Climate (Hardware) - mark@orbitalsentry.ai
3. Quantum Light - Materials - olga@quantumlight.co
4. RetinaLogik - Medtech (Hardware) - asarhan@retinalogik.ca
5. Substance Corp - Robotics - gaurav.agrawal@substance-corp.com
... (40 total, ending with LNK Energies)

## Remaining Issues to Fix
1. ~~**Score column missing**~~ - FIXED: Removed CSS containment rules causing rendering issues
2. ~~**Thesis Fit badges missing**~~ - FIXED: Added explicit column widths
3. **LinkedIn not hyperlinked** - Founder names should link to LinkedIn (partially done - works for companies with founder_linkedin_data)
4. **Scrolling lag** - Performance issues when scrolling (may need further optimization)

## Scoring System
- Thesis Fit: 25% weight
- Impact: 20% weight
- Team: 15% weight
- Product: 10% weight
- Business Model: 10% weight
- Market: 10% weight
- Traction: 5% weight
- Deal: 5% weight

## Thesis Themes
- Sustainable Industry (Climate/Energy)
- Human Health
- Tomorrow's Workforce
- Off-Thesis / Neutral

## Git Config
Must use: `git config user.email "eng@better.vc"` for Vercel auto-deploy

## Key Data Files
- `/Users/Ryan/Downloads/deepchecks_companies.json` - Raw Deepchecks data
- `/Users/Ryan/Downloads/deepchecks_scored.json` - Scored Deepchecks data
- `/Users/Ryan/Downloads/current_yc_data.json` - Exported YC data with changes

## Next Steps
1. Fix missing Score column in table
2. Fix Thesis Fit badges
3. Hyperlink founder names to LinkedIn
4. Wait for LinkedIn profile data for founder enrichment
