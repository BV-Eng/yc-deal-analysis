# Deepchecks Monthly Import Runbook

This document outlines the process for importing new Deepchecks company batches into the Deal Analysis CRM.

## Overview

The import process has two phases:

### Phase 1: Initial Import
**User provides:** Deepchecks HTML export
**Claude outputs:** Companies added to dashboard + Excel for LinkedIn/Pitchbook lookup

### Phase 2: Enrichment
**User provides:** Scraped LinkedIn profiles + Pitchbook URLs
**Claude outputs:** Fully populated and scored companies

---

## Phase 1: Initial Import

### Step 1.1: Export from Deepchecks
1. Go to the Deepchecks deals page
2. Save the page as HTML (File → Save Page As → Web Page, Complete)
3. Share the HTML file path with Claude

### Step 1.2: Extract and Import Companies
Claude will run:
```bash
python3 scripts/1_extract_from_html.py /path/to/deepchecks.html "Deepchecks Mar 2026"
```

This script extracts:
- Company name, valuation range, industry
- Full description with bullet points
- Founder's pitch (their own words)
- Founder's work & education
- Deck URLs (Google Drive links)
- Contact emails and websites
- Founder names and LinkedIn URLs

### Step 1.3: Data Format
The script creates structured descriptions with three sections:
```
**DESCRIPTION**
[Main company description with bullet points using •]

**FOUNDER'S PITCH**
[Founder's own pitch text]

**FOUNDER'S WORK & EDUCATION**
[Background info: companies, universities]
```

The frontend automatically parses this format to render:
- Bold section headings
- Bullet points as proper lists
- Paragraph breaks

### Step 1.4: Generate Lookup Sheet
The script outputs a CSV with columns:
- Website (for Pitchbook lookup)
- Pitchbook URL (empty - for user to fill)
- Company Name
- ID
- Founder Name
- Founder LinkedIn

**User Action:**
1. Fill in Pitchbook URLs for each company
2. Verify/add missing founder LinkedIn URLs
3. Use a LinkedIn scraper to get founder profile data

---

## Phase 2: Enrichment

### Step 2.1: Import LinkedIn Profiles
User provides the scraped LinkedIn JSON file.

Claude will run:
```bash
python3 scripts/3_import_linkedin_and_score.py /path/to/linkedin_profiles.json
```

This enriches founder records with:
- Bio/description
- Schools and degrees
- Prior employers
- Technical competence assessment
- Repeat founder flag

### Step 2.2: Score Founders (Manual with Claude)
Founder scoring requires LLM-based holistic analysis. Claude will:

1. Review each founder's LinkedIn profile data
2. Score on 9 categories (1-10 scale):
   - **Breakthrough Idea**: Non-obvious insights, living in the future
   - **Mission Intentionality**: Authenticity, personal connection
   - **Extraordinary Achievements**: Academic honors, patents, exits
   - **Work Ethic & Execution**: Track record of delivery
   - **Grit & Perseverance**: Overcoming adversity
   - **Magnetism**: Network size, leadership presence
   - **Intellectual Curiosity**: Breadth of learning
   - **Coachability & EQ**: Openness to feedback
   - **Team Chemistry**: Collaboration ability

3. Calculate `founder_score` = average of 9 scores
4. Update `weighted_total` = 30% company_score + 70% founder_score

**Batch Processing:** Claude processes ~10 founders at a time to manage context.

### Step 2.3: Import Pitchbook URLs
User provides the CSV with Pitchbook URLs filled in.

Claude will run:
```bash
python3 scripts/4_import_pitchbook_urls.py /path/to/pitchbook_urls.csv
```

### Step 2.4: Deploy
```bash
# Commit changes
git add data/seed-data.json
git commit -m "Add Deepchecks [Month Year] batch with founder scoring"
git push origin main

# Wait 20 seconds for Vercel deployment, then reload:
curl -X POST https://yc-deal-analysis.vercel.app/api/admin/reload-seed
```

---

## Data Structure Reference

### Company Fields
| Field | Description |
|-------|-------------|
| `id` | Unique identifier (auto-incremented) |
| `name` | Company name |
| `one_liner` | Short description |
| `long_description` | Full description with **SECTION** headers |
| `batch` | e.g., "Deepchecks Mar 2026" |
| `source` | "Deepchecks" or "YC" |
| `website` | Company website URL |
| `deck_url` | Google Drive link to pitch deck |
| `pitchbook_url` | Pitchbook profile URL |
| `valuation_range` | e.g., "$5M - $10M", "$26M+", "Under $5M" |
| `all_locations` | Default: "United States" for Deepchecks |
| `thesis_fit_theme` | "Sustainable Industry", "Human Health", "Tomorrow's Workforce", or "Neutral" |
| `thesis_fit_score` | 1-10 score |
| `company_score` | Weighted average of category scores |
| `avg_founder_score` | Average of founder scores |
| `weighted_total` | 30% company + 70% founder |

### Founder Fields
| Field | Description |
|-------|-------------|
| `name` | Full name |
| `linkedin` | LinkedIn profile URL |
| `bio` | Summary from LinkedIn |
| `schools` | Comma-separated schools |
| `degrees` | Comma-separated degrees |
| `prior_employers` | Previous companies |
| `technical_competence` | "High", "Medium", or "Low" |
| `is_repeat_founder` | 0 or 1 |
| `founder_score` | Average of 9 category scores |
| `breakthrough_score` | 1-10 |
| `breakthrough_justification` | Reasoning |
| ... | (9 score/justification pairs) |

### Description Format
The `long_description` field uses this format for proper frontend rendering:
```
**DESCRIPTION**
Main description text here.

• Bullet point one
• Bullet point two
• Bullet point three

**FOUNDER'S PITCH**
The founder's own pitch in their words.

**FOUNDER'S WORK & EDUCATION**
Company1, Company2, University1, University2
```

The frontend parses:
- `**SECTION**` → Bold heading
- `•` → Bullet list item
- Double newlines → Paragraph breaks

### Valuation Ranges
Common formats:
- `$5M - $10M`
- `$11M - $15M`
- `$16M - $20M`
- `$21M - $25M`
- `$26M+`
- `Under $5M`

### Thesis Themes
| Theme | Keywords |
|-------|----------|
| Sustainable Industry | climate, energy, materials, manufacturing, chemicals |
| Human Health | medical, biotech, pharma, healthcare, therapeutic |
| Tomorrow's Workforce | robotics, automation, AI, autonomous, drones |
| Neutral | Off-thesis or unclear |

---

## Scoring Weights
| Category | Weight |
|----------|--------|
| Thesis Fit | 25% |
| Impact | 20% |
| Team | 15% |
| Product | 10% |
| Business Model | 10% |
| Market | 10% |
| Traction | 5% |
| Deal | 5% |

---

## Quick Reference Commands

```bash
# Extract from HTML (includes valuation, descriptions, deck URLs)
python3 scripts/1_extract_from_html.py ~/Downloads/deepchecks.html "Deepchecks Apr 2026"

# Import LinkedIn profiles
python3 scripts/3_import_linkedin_and_score.py ~/Downloads/linkedin_profiles.json

# Import Pitchbook URLs
python3 scripts/4_import_pitchbook_urls.py ~/Downloads/pitchbook_urls.csv

# Deploy
git add data/seed-data.json && git commit -m "Add batch" && git push origin main

# Reload production data
curl -X POST https://yc-deal-analysis.vercel.app/api/admin/reload-seed
```

---

## Troubleshooting

### Companies not showing up
1. Check if deployment completed (wait 20+ seconds)
2. Run the reload-seed endpoint
3. Hard refresh the browser (Cmd+Shift+R)

### Founder scores not displaying
1. Verify the founder has all 9 score fields populated
2. Check that `founder_score` is set (average of 9 scores)
3. Verify `weighted_total` is recalculated

### Description not rendering properly
1. Ensure sections use `**SECTION NAME**` format (double asterisks)
2. Use `•` character for bullet points (not `-` or `*`)
3. Use double newlines between sections

### Git push rejected
Ensure git config is correct:
```bash
git config user.email "eng@better.vc"
```

### Valuation not showing
1. Check `valuation_range` field is populated in seed-data.json
2. Verify format matches expected patterns ($XM - $YM)

---

## Files Reference

| File | Purpose |
|------|---------|
| `data/seed-data.json` | Main data file with all companies |
| `scripts/1_extract_from_html.py` | Parse Deepchecks HTML, extract all data |
| `scripts/3_import_linkedin_and_score.py` | Import LinkedIn data |
| `scripts/4_import_pitchbook_urls.py` | Import Pitchbook URLs |
| `frontend/dist/index.html` | Single-file React frontend |
| `backend/server-redis.js` | Express API server |

---

## Checklist for New Batch

- [ ] Save Deepchecks page as HTML
- [ ] Run extraction script with batch name
- [ ] Verify company count and valuation ranges
- [ ] Fill in Pitchbook URLs in generated CSV
- [ ] Scrape LinkedIn profiles for founders
- [ ] Import LinkedIn data
- [ ] Score founders with Claude (10 at a time)
- [ ] Import Pitchbook URLs
- [ ] Commit with eng@better.vc email
- [ ] Push to trigger Vercel deploy
- [ ] Wait 20+ seconds
- [ ] Reload seed data
- [ ] Hard refresh and verify all data displays
