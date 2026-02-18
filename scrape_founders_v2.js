const https = require('https');
const http = require('http');
const fs = require('fs');

function fetch(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' } }, res => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch(res.headers.location).then(resolve).catch(reject);
      }
      const chunks = [];
      res.on('data', d => chunks.push(d));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error', reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('timeout')); });
  });
}

function parseCompanyPage(html) {
  const match = html.match(/data-page="([^"]+)"/);
  if (!match) return null;

  const decoded = match[1]
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'");

  try {
    const data = JSON.parse(decoded);
    return data.props?.company || null;
  } catch(e) {
    return null;
  }
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  const companies = JSON.parse(fs.readFileSync('data/yc_w26_companies.json', 'utf-8'));
  let succeeded = 0;
  let failed = 0;
  let totalFounders = 0;

  console.log(`Scraping ${companies.length} company pages for founder data...`);
  console.log('');

  for (let i = 0; i < companies.length; i++) {
    const company = companies[i];
    const slug = company.slug || company.raw?.slug;
    if (!slug) {
      console.log(`[${i+1}/${companies.length}] ${company.name} - NO SLUG, skipping`);
      failed++;
      continue;
    }

    const url = `https://www.ycombinator.com/companies/${slug}`;
    process.stdout.write(`[${i+1}/${companies.length}] ${company.name}... `);

    try {
      const { status, body } = await fetch(url);

      if (status !== 200) {
        console.log(`HTTP ${status}`);
        failed++;
        continue;
      }

      const companyData = parseCompanyPage(body);
      if (!companyData) {
        console.log('NO DATA FOUND');
        failed++;
        continue;
      }

      // Extract company details
      company.long_description = companyData.long_description || company.long_description || '';
      company.website = companyData.website || company.website || '';
      company.all_locations = companyData.location || company.all_locations || '';
      company.team_size = companyData.team_size || company.team_size || 0;
      company.year_founded = companyData.year_founded || company.year_founded || null;
      company.logo_url = companyData.small_logo_url || companyData.logo_url || company.logo_url || '';
      company.linkedin_url = companyData.linkedin_url || '';
      company.twitter_url = companyData.twitter_url || '';
      company.github_url = companyData.github_url || '';
      company.cb_url = companyData.cb_url || '';

      // Extract founders
      const founders = (companyData.founders || []).map(f => ({
        name: f.full_name || `${f.first_name || ''} ${f.last_name || ''}`.trim(),
        first_name: f.first_name || '',
        last_name: f.last_name || '',
        title: f.title || '',
        linkedin: f.linkedin_url || '',
        twitter: f.twitter_url || '',
        avatar_url: f.avatar_medium || f.avatar_thumb || '',
        bio: f.bio || '',
        is_female: f.is_female || false,
        is_black: f.is_black || false,
        is_hispanic_latino: f.is_hispanic_latino || false
      }));

      company.founders = founders;
      totalFounders += founders.length;
      succeeded++;

      console.log(`OK (${founders.length} founders: ${founders.map(f => f.name).join(', ')})`);

    } catch(e) {
      console.log(`ERROR: ${e.message}`);
      failed++;
    }

    // Rate limiting - be polite
    if (i % 15 === 14) {
      await sleep(2000);
    } else {
      await sleep(300);
    }
  }

  // Save updated data
  fs.writeFileSync('data/yc_w26_companies.json', JSON.stringify(companies, null, 2));

  console.log(`\n${'='.repeat(50)}`);
  console.log(`Done! Succeeded: ${succeeded}, Failed: ${failed}`);
  console.log(`Total founders found: ${totalFounders}`);

  // Founder stats
  let withLinkedin = 0;
  let withBio = 0;
  let femaleCount = 0;
  let bipocCount = 0;

  companies.forEach(c => {
    (c.founders || []).forEach(f => {
      if (f.linkedin) withLinkedin++;
      if (f.bio) withBio++;
      if (f.is_female) femaleCount++;
      if (f.is_black || f.is_hispanic_latino) bipocCount++;
    });
  });

  console.log(`\n=== FOUNDER STATS ===`);
  console.log(`Total founders: ${totalFounders}`);
  console.log(`With LinkedIn: ${withLinkedin}`);
  console.log(`With Bio: ${withBio}`);
  console.log(`Female: ${femaleCount}`);
  console.log(`BIPOC (Black/Hispanic): ${bipocCount}`);

  // Print companies without founders
  const noFounders = companies.filter(c => !c.founders || c.founders.length === 0);
  if (noFounders.length > 0) {
    console.log(`\nCompanies without founder data (${noFounders.length}):`);
    noFounders.forEach(c => console.log(`  - ${c.name}`));
  }
}

main().catch(console.error);
