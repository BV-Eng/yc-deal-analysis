#!/usr/bin/env node
/**
 * Hunter.io Email Enrichment Script
 *
 * Fetches emails for founders of companies marked as "Interested"
 * using the Hunter.io Email Finder API.
 *
 * Usage:
 *   HUNTER_API_KEY=your_key node enrich_emails.js
 *   HUNTER_API_KEY=your_key node enrich_emails.js --dry-run
 *   HUNTER_API_KEY=your_key node enrich_emails.js --status "Meeting Scheduled"
 */

const fs = require('fs');
const path = require('path');

const SEED_FILE = path.join(__dirname, 'data', 'seed-data.json');
const LOCAL_FILE = path.join(__dirname, 'data', 'local-data.json');
const HUNTER_API_KEY = process.env.HUNTER_API_KEY;
const API_BASE = 'https://api.hunter.io/v2';

// Parse command line args
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const statusIndex = args.indexOf('--status');
const targetStatus = statusIndex !== -1 ? args[statusIndex + 1] : 'Interested';

if (!HUNTER_API_KEY) {
  console.error('Error: HUNTER_API_KEY environment variable is required');
  console.error('Usage: HUNTER_API_KEY=your_key node enrich_emails.js');
  process.exit(1);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function extractDomain(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

async function findEmail(domain, firstName, lastName) {
  const params = new URLSearchParams({
    domain,
    first_name: firstName,
    last_name: lastName,
    api_key: HUNTER_API_KEY
  });

  const response = await fetch(`${API_BASE}/email-finder?${params}`);
  const data = await response.json();

  if (data.errors) {
    console.error(`  Hunter API error: ${JSON.stringify(data.errors)}`);
    return null;
  }

  if (data.data && data.data.email) {
    return {
      email: data.data.email,
      confidence: data.data.score || 0
    };
  }

  return null;
}

function loadData() {
  // Try local-data.json first (has latest updates)
  if (fs.existsSync(LOCAL_FILE)) {
    return JSON.parse(fs.readFileSync(LOCAL_FILE, 'utf-8'));
  }
  // Fall back to seed-data.json
  if (fs.existsSync(SEED_FILE)) {
    return JSON.parse(fs.readFileSync(SEED_FILE, 'utf-8'));
  }
  throw new Error('No data file found');
}

function saveData(data) {
  fs.writeFileSync(LOCAL_FILE, JSON.stringify(data, null, 2));
}

async function main() {
  console.log(`\nHunter.io Email Enrichment`);
  console.log(`==========================`);
  console.log(`Target status: "${targetStatus}"`);
  console.log(`Dry run: ${dryRun}\n`);

  const data = loadData();

  // Get companies with the target status
  const companies = data.companies.filter(c => c.status === targetStatus);

  console.log(`Found ${companies.length} companies with status "${targetStatus}"\n`);

  let enriched = 0;
  let skipped = 0;
  let errors = 0;

  for (const company of companies) {
    const domain = extractDomain(company.website);

    if (!domain) {
      console.log(`[${company.name}] No valid website/domain, skipping`);
      skipped++;
      continue;
    }

    // Get founders without emails for this company
    const founders = (company.founders || []).filter(f => !f.email);

    if (founders.length === 0) {
      console.log(`[${company.name}] All founders already have emails`);
      skipped++;
      continue;
    }

    console.log(`[${company.name}] (${domain}) - ${founders.length} founder(s) to enrich`);

    for (const founder of founders) {
      // Parse name if first/last not set
      let firstName = founder.first_name;
      let lastName = founder.last_name;

      if (!firstName || !lastName) {
        const nameParts = (founder.name || '').trim().split(/\s+/);
        firstName = firstName || nameParts[0] || '';
        lastName = lastName || nameParts.slice(1).join(' ') || '';
      }

      if (!firstName) {
        console.log(`  - ${founder.name}: Cannot determine first name, skipping`);
        continue;
      }

      console.log(`  - ${founder.name} (${firstName} ${lastName})...`);

      if (dryRun) {
        console.log(`    [DRY RUN] Would search for: ${firstName} ${lastName} @ ${domain}`);
        continue;
      }

      try {
        const result = await findEmail(domain, firstName, lastName);

        if (result) {
          console.log(`    Found: ${result.email} (confidence: ${result.confidence}%)`);

          founder.email = result.email;
          founder.email_confidence = result.confidence;

          enriched++;
        } else {
          console.log(`    No email found`);
        }

        // Rate limit: Hunter allows 10 requests/second on paid plans
        await sleep(150);
      } catch (err) {
        console.error(`    Error: ${err.message}`);
        errors++;
      }
    }
  }

  if (!dryRun) {
    saveData(data);
    console.log(`\nData saved to ${LOCAL_FILE}`);
  }

  console.log(`\n==========================`);
  console.log(`Results:`);
  console.log(`  Emails found: ${enriched}`);
  console.log(`  Companies skipped: ${skipped}`);
  console.log(`  Errors: ${errors}`);

  if (dryRun) {
    console.log(`\nThis was a dry run. Run without --dry-run to actually update the data.`);
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
