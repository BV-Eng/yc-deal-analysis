# Lessons Learned & Update Guide

## Quick Update Workflow

### Syncing from Affinity (Most Common)

1. **Export CSV from Affinity** (DealBot, AcceleratorBot, or StealthBot view)
2. **Update CSV path** in the appropriate script (or save to default location)
3. **Run the sync script:**
   ```bash
   python3 scripts/sync_dealbot_enrichment.py      # For DealBot
   python3 scripts/sync_acceleratorbot_scores.py   # For AcceleratorBot
   python3 scripts/sync_stealthbot_scores.py       # For StealthBot
   ```
4. **Commit and push:**
   ```bash
   git add data/seed-data.json
   git commit -m "Sync [Source] data from Affinity"
   git push origin main
   ```
5. **Reload production:**
   ```bash
   curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed
   ```

### Adding New Companies from a New Source

1. Create a new import script in `scripts/` following existing patterns
2. Ensure you set appropriate `source` field (e.g., "NewSource (Month Year)")
3. For person-based sources (like StealthBot), set `company_score = founder_score`
4. Run script, commit, push, reload

---

## Scripts Reference

| Script | Purpose | CSV Required |
|--------|---------|--------------|
| `sync_dealbot_enrichment.py` | Sync DealBot scores, owner, email, raised | DealBot export |
| `sync_acceleratorbot_scores.py` | Sync AcceleratorBot thesis scores | AcceleratorBot export |
| `sync_stealthbot_scores.py` | Sync StealthBot founder scores (all 9 criteria) | StealthBot export |
| `restore_pnp_enrichment.py` | Restore PnP data from git history | None (uses git) |
| `import_stealthbot_march.py` | Initial StealthBot import | StealthBot JSON |
| `pull_from_affinity.py` | Pull data directly from Affinity API | None (uses API) |
| `push_to_affinity.py` | Push updates back to Affinity | None (uses API) |

---

## Data Model Notes

### Company Types

| Source | Type | company_score Calculation |
|--------|------|---------------------------|
| YC, Deepchecks, DealBot, AcceleratorBot | Company-based | Weighted avg of team, product, thesis, etc. |
| StealthBot | Person-based | `company_score = founder_score` |

### Thesis Fit Themes

Map to Better Ventures investment thesis:
- **Sustainable Industry**: climate, energy, materials, manufacturing, agriculture
- **Human Health**: healthcare, biotech, medical, therapeutics, wellness
- **Tomorrow's Workforce**: education, HR, productivity, AI for SMBs

### 9 Founder Scoring Criteria

1. `breakthrough_score` - Contrarian thinking, innovation
2. `mission_score` - Personal connection to problem
3. `achievements_score` - Credentials, exits, awards
4. `work_ethic_score` - Execution track record
5. `grit_score` - Resilience, overcoming adversity
6. `curiosity_score` - Intellectual curiosity, learning
7. `magnetism_score` - Network, leadership presence
8. `coachability_score` - Self-awareness, adaptability
9. `team_chemistry_score` - Team building ability

---

## 2026-03-24: Data Enrichment Restoration

### Problem
AcceleratorBot import (commit d6e5d46) overwrote 34 properly enriched PnP companies with less-enriched versions. DealBot companies lacked scores that existed in Affinity. StealthBot entries showed near-zero company scores.

### Root Causes
1. Import scripts didn't check for existing enriched data before overwriting
2. StealthBot `company_score` was calculated from company metrics (all zeros) instead of founder_score

### Solutions Applied
1. Restored PnP enrichment from git history (commit 848f62e)
2. Synced DealBot scores from Affinity CSV export
3. Synced AcceleratorBot thesis scores from CSV
4. Populated all 9 founder criteria for StealthBot
5. Fixed StealthBot `company_score = founder_score`

### Prevention Checklist
- [ ] Before batch imports, check for existing companies by name (case-insensitive)
- [ ] Merge rather than overwrite when enriched data exists
- [ ] For person-based sources, use `company_score = founder_score`
- [ ] Test with `--dry-run` if available
- [ ] Verify scores in dashboard after reload

---

## Troubleshooting

### Scores showing as 0 or very low
- Check if `company_score` is being calculated correctly
- For person-based sources, ensure `company_score = founder_score`
- Verify the founder scores are populated in seed-data.json

### Changes not appearing in production
1. Did you push to GitHub? `git push origin main`
2. Did you reload? `curl -X POST https://bv-deal-analysis.vercel.app/api/admin/reload-seed`
3. Wait 10-15 seconds for Vercel deployment, then reload again

### Data was overwritten
- Check git history: `git log --oneline data/seed-data.json`
- Restore from previous commit: `git show <commit>:data/seed-data.json > /tmp/backup.json`
- Use `restore_pnp_enrichment.py` as a template for restoration scripts

### CSV not matching companies
- Check for name mismatches (case sensitivity, special characters)
- Scripts use case-insensitive matching but exact spelling matters
- Print unmatched companies to identify issues
