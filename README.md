# YC Deal Analysis Dashboard

A CRM-style dashboard for tracking startup deals, founders, and investment decisions.

**Production URL:** https://bv-deal-analysis.vercel.app/

## Architecture

### Storage
- **Production (Vercel):** Uses Upstash Redis via `server-redis.js` and `database-redis.js`
- **Local Development:** Uses SQLite via `server.js` and `database.js`

### Data Flow
```
seed-data.json → Upstash Redis (on first load or reload)
                        ↓
                  Dashboard API
```

## Updating Data

### IMPORTANT: Updating seed-data.json is NOT enough!

The production dashboard uses Upstash Redis, which caches data. When you update `data/seed-data.json`:

1. **Commit and push** the changes to GitHub
2. **Call the reload endpoint** to sync Redis with the new seed data:

```bash
curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
```

This returns: `{"success":true,"companies":261}` (or current count)

### When to Reload

Reload after:
- Adding new companies or founders to seed-data.json
- Updating founder scores or data
- Any batch updates to the JSON file

### Reload Behavior

The `/api/admin/reload-seed` endpoint:
- Reads `data/seed-data.json`
- **Replaces ALL data** in Redis with the seed file contents
- Any manual edits made via the UI will be overwritten

**To preserve UI edits:** First export current data, merge changes, then reload.

## Syncing Data from Affinity

### Quick Reference

Export a CSV from Affinity, then run the appropriate sync script:

```bash
# DealBot companies (thesis scores, founder scores, owner, email, raised)
python3 scripts/sync_dealbot_enrichment.py

# AcceleratorBot companies (thesis scores, themes, owner)
python3 scripts/sync_acceleratorbot_scores.py

# StealthBot people (founder scores across 9 criteria, thesis themes)
python3 scripts/sync_stealthbot_scores.py

# Then commit, push, and reload production
git add data/seed-data.json && git commit -m "Sync from Affinity"
git push origin main
curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
```

### CSV Export Locations

Update the CSV paths in each script, or copy your exports to these default locations:
- DealBot: `/Users/Ryan/Downloads/Dealbot_unsaved_view__export_Mar-24-2026.csv`
- AcceleratorBot: `/Users/Ryan/Downloads/AcceleratorBot_unsaved_view__export_Mar-24-2026.csv`
- StealthBot: `/Users/Ryan/Downloads/StealthBot_Outreach_unsaved_view__export_Mar-24-2026.csv`

### What Each Script Syncs

| Script | Source | Fields Synced |
|--------|--------|---------------|
| `sync_dealbot_enrichment.py` | DealBot CSV | thesis_fit_score (BV Rank ÷3), thesis_fit_theme, owner, email, total_raised, all 9 founder scores |
| `sync_acceleratorbot_scores.py` | AcceleratorBot CSV | thesis_fit_score (ranking), thesis_fit_theme (from industry), owner |
| `sync_stealthbot_scores.py` | StealthBot CSV | founder_score, all 9 criteria scores, thesis_fit_theme, company_score |
| `assign_owners_fast.py` | None | owner (based on thesis theme + keywords) |
| `enrich_stealthbot_founders.py` | LinkedIn CSV | All 9 founder scores + justifications from LinkedIn data |

### Field Mapping (Affinity → Dashboard)

**DealBot/AcceleratorBot:**
| Affinity Column | Dashboard Field | Transform |
|-----------------|-----------------|-----------|
| BV Rank 1-30 | thesis_fit_score | ÷ 3 |
| ranking | thesis_fit_score | direct |
| Owners | owner, contact_email | parse "Name <email>" |
| Pb Total Raised | total_raised | format as $XM |
| industry | thesis_fit_theme | keyword classify |

**Founder Scores:**
| Affinity Column | Dashboard Field |
|-----------------|-----------------|
| Founder Score Total | founder_score |
| Founder Breakthrough | breakthrough_score |
| Founder Mission | mission_score |
| Founder Achievements | achievements_score |
| Founder Execution | work_ethic_score |
| Founder Grit | grit_score |
| Founder Magnetism | magnetism_score |
| Founder Coachability | coachability_score |
| Founder Team | team_chemistry_score |

## Common Workflows

### ⚠️ CRITICAL: Always Reload After Updating seed-data.json

Any script that modifies `data/seed-data.json` requires THREE steps:

```bash
# 1. Run your script (updates seed-data.json locally)
python3 scripts/your_script.py

# 2. Commit and push to GitHub
git add data/seed-data.json
git commit -m "Description of changes"
git push origin main

# 3. Wait ~10 seconds for Vercel to deploy the new commit
sleep 10

# 4. RELOAD PRODUCTION (this is the step that actually updates the dashboard!)
curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
```

**If you skip step 4, the dashboard will show stale data!**

**If you reload too fast**, Vercel may not have deployed the latest commit yet, and the reload will read the old seed-data.json. Wait for Vercel deployment to complete before reloading.

### Auto-Assign Owners to Companies

```bash
# Assigns owners based on thesis theme + keyword matching
python3 scripts/assign_owners_fast.py

# Commit, push, reload
git add data/seed-data.json && git commit -m "Auto-assign owners" && git push origin main
curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
```

### Enrich StealthBot Founders from LinkedIn Data

```bash
# Requires LinkedIn CSV export (from PhantomBuster or similar)
# Update CSV path in script, then run:
python3 scripts/enrich_stealthbot_founders.py

# Commit, push, reload
git add data/seed-data.json && git commit -m "Enrich StealthBot founders" && git push origin main
curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
```

**What it does:**
- Matches founders to LinkedIn profiles by name
- Generates scores based on: education prestige, previous companies, credentials (PhD/MD/MBA), followers, domain alignment
- Generates justifications for all 9 founder scoring criteria
- Updates company_score = founder_score for person-based entries

---

## Adding Founder Data (PhantomBuster)

### Recommended Workflow

1. **Get LinkedIn data** via PhantomBuster
2. **Score founders** using the scoring script:
   ```bash
   cd /Users/Ryan/BV-Acceleratorbot
   python3 scripts/score_pnp_founders.py /path/to/phantom_data.json
   ```
3. **Commit the updated seed-data.json**
4. **Reload production:** `curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed`

## API Endpoints

### Companies
- `GET /api/companies` - List all companies (supports filters)
- `GET /api/companies/:id` - Get company with founders
- `PUT /api/companies/:id` - Update company
- `PUT /api/companies/:id/scores` - Update company scores

### Founders
- `PUT /api/founders/:id` - Update founder profile
- `PUT /api/founders/:id/scores` - Update founder scores

### Admin
- `POST /api/admin/reload-seed` - Reload all data from seed-data.json
- `GET /api/export/csv` - Export companies as CSV

### Analytics
- `GET /api/analytics` - Get dashboard analytics

## Local Development

```bash
npm install
npm run dev
```

Local server runs on http://localhost:3456

## Files

- `data/seed-data.json` - Source of truth for initial/reload data
- `data/local-data.json` - Local development data (gitignored)
- `backend/server-redis.js` - Production server (Vercel)
- `backend/server.js` - Local development server
- `frontend/` - React frontend
