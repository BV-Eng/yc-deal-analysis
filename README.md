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

## Adding Founder Data

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
