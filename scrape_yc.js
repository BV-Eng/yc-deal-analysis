const https = require('https');
const fs = require('fs');

function fetchYCBatch(page = 0) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      query: "",
      page: page,
      hitsPerPage: 200,
      facetFilters: [["batch:Winter 2026"]]
    });

    const options = {
      hostname: '45bwzj1sgc-dsn.algolia.net',
      path: '/1/indexes/YCCompany_production/query',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-algolia-application-id': '45BWZJ1SGC',
        'x-algolia-api-key': 'ZjA3NWMwMmNhMzEwZmMxOThkZDlkMjFmNDAwNTNjNjdkZjdhNWJkOWRjMThiODQwMjUyZTVkYjA4YjFlMmU2YnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(options, (res) => {
      const chunks = [];
      res.on('data', (d) => chunks.push(d));
      res.on('end', () => {
        try {
          const data = JSON.parse(Buffer.concat(chunks).toString());
          resolve(data);
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function main() {
  console.log('Fetching YC Winter 2026 batch...');

  const data = await fetchYCBatch(0);
  console.log(`Total companies found: ${data.nbHits}`);
  console.log(`Companies returned: ${data.hits.length}`);

  if (data.hits.length > 0) {
    console.log('\nSample company keys:', Object.keys(data.hits[0]).join(', '));
  }

  // Process and save all companies
  const companies = data.hits.map((hit, idx) => ({
    id: idx + 1,
    yc_id: hit.objectID || '',
    name: hit.name || '',
    slug: hit.slug || '',
    one_liner: hit.one_liner || '',
    long_description: hit.long_description || '',
    batch: hit.batch || 'W26',
    status: hit.status || '',
    industries: (hit.industries || []).join(', '),
    subindustry: hit.subindustry || '',
    tags: (hit.tags || []).join(', '),
    website: hit.website || '',
    all_locations: hit.all_locations || '',
    team_size: hit.team_size || 0,
    is_hiring: hit.isHiring || false,
    year_founded: hit.year_founded || null,
    logo_url: hit.smallLogoUrl || hit.logoUrl || '',
    // Founders
    founders: (hit.founders || []).map(f => ({
      name: f.full_name || `${f.first_name || ''} ${f.last_name || ''}`.trim(),
      first_name: f.first_name || '',
      last_name: f.last_name || '',
      title: f.title || '',
      linkedin: f.linkedin_url || '',
      avatar_url: f.avatar_thumb || '',
      is_female: f.is_female || false,
      is_black: f.is_black || false,
      is_hispanic_latino: f.is_hispanic_latino || false
    })),
    // Raw data for later processing
    raw: hit
  }));

  // Save raw data
  fs.writeFileSync('data/yc_w26_raw.json', JSON.stringify(data.hits, null, 2));

  // Save processed data
  fs.writeFileSync('data/yc_w26_companies.json', JSON.stringify(companies, null, 2));

  console.log(`\nSaved ${companies.length} companies to data/yc_w26_companies.json`);

  // Print first 10 companies
  console.log('\n=== FIRST 10 COMPANIES ===');
  companies.slice(0, 10).forEach((c, i) => {
    console.log(`\n${i+1}. ${c.name}`);
    console.log(`   ${c.one_liner}`);
    console.log(`   Industry: ${c.industries}`);
    console.log(`   Location: ${c.all_locations}`);
    console.log(`   Website: ${c.website}`);
    console.log(`   Founders: ${c.founders.map(f => `${f.name} (${f.title})`).join(', ')}`);
  });

  // Print diversity stats
  let totalFounders = 0;
  let femaleFounders = 0;
  let bipocFounders = 0;
  companies.forEach(c => {
    c.founders.forEach(f => {
      totalFounders++;
      if (f.is_female) femaleFounders++;
      if (f.is_black || f.is_hispanic_latino) bipocFounders++;
    });
  });

  console.log(`\n=== BATCH STATS ===`);
  console.log(`Total companies: ${companies.length}`);
  console.log(`Total founders: ${totalFounders}`);
  console.log(`Female founders: ${femaleFounders} (${(femaleFounders/totalFounders*100).toFixed(1)}%)`);
  console.log(`BIPOC founders (Black/Hispanic): ${bipocFounders} (${(bipocFounders/totalFounders*100).toFixed(1)}%)`);

  // Print all company names
  console.log(`\n=== ALL ${companies.length} COMPANY NAMES ===`);
  companies.forEach((c, i) => {
    console.log(`${i+1}. ${c.name} - ${c.one_liner.substring(0, 80)}`);
  });
}

main().catch(console.error);
