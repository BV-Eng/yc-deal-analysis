const https = require('https');
const fs = require('fs');
const { getDb } = require('./backend/database');

function fetch(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)' } }, res => {
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
  const decoded = match[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'").replace(/&#x27;/g, "'");
  try {
    return JSON.parse(decoded).props.company;
  } catch(e) { return null; }
}

// Parse a founder bio to extract structured info
function parseBio(bio) {
  if (!bio) return {};
  const result = {};

  // Clean up HTML entities
  bio = bio.replace(/&#x27;/g, "'").replace(/&amp;/g, '&').replace(/&quot;/g, '"');

  // Extract schools
  const schoolPatterns = [
    /(?:graduated?\s+(?:from|at|with)?|studied\s+at|alumni?\s+of|attended|bachelor'?s?\s+(?:from|at)|master'?s?\s+(?:from|at)|PhD\s+(?:from|at|in)|BS\s+(?:from|at)|MS\s+(?:from|at)|MBA\s+(?:from|at)|B\.?Tech\.?\s+(?:from|at)|M\.?Tech\.?\s+(?:from|at))\s+([^.;,\n]+)/gi,
    /(MIT|Stanford|Harvard|Yale|Princeton|Caltech|Carnegie Mellon|CMU|Berkeley|UC Berkeley|Columbia|Cornell|Oxford|Cambridge|IIT\s+\w+|Georgia Tech|Waterloo|University of \w+|NYU|UCLA|UIUC|ETH|EPFL|Tsinghua|Peking University|NUS)/gi
  ];

  const schools = new Set();
  for (const pattern of schoolPatterns) {
    let m;
    while ((m = pattern.exec(bio)) !== null) {
      schools.add(m[1].trim().replace(/\.$/, ''));
    }
  }
  if (schools.size > 0) result.schools = [...schools].join(', ');

  // Extract degrees
  const degreePatterns = /((?:B\.?S\.?|M\.?S\.?|Ph\.?D\.?|MBA|B\.?Tech|M\.?Tech|B\.?Eng|M\.?Eng|Bachelor'?s?|Master'?s?|Doctorate)\s*(?:in\s+[^.,;]+)?)/gi;
  const degrees = new Set();
  let dm;
  while ((dm = degreePatterns.exec(bio)) !== null) {
    degrees.add(dm[1].trim().replace(/\.$/, ''));
  }
  if (degrees.size > 0) result.degrees = [...degrees].join(', ');

  // Extract prior employers
  const employerPatterns = [
    /(?:prev(?:iously|\.)?|formerly|ex-|worked?\s+at|@)\s*(?:@\s*)?([^.,;\n]+)/gi,
    /(Google|Meta|Facebook|Apple|Amazon|Microsoft|Netflix|Tesla|Stripe|Airbnb|Uber|Lyft|Palantir|SpaceX|OpenAI|Anthropic|DeepMind|McKinsey|BCG|Bain|Goldman Sachs|Morgan Stanley|JP Morgan|JPMorgan|Citadel|Two Sigma|Jane Street|Bridgewater|a16z|Sequoia|Y Combinator|AT Kearney|Accenture|Deloitte|KPMG|EY|PwC|IBM|Oracle|Salesforce|Intel|Nvidia|AMD|Qualcomm|Samsung|LinkedIn|Twitter|X\.com|Snap|Pinterest|Reddit|Coinbase|Robinhood|Square|Block|Plaid)/gi
  ];

  const employers = new Set();
  for (const pattern of employerPatterns) {
    let em;
    while ((em = pattern.exec(bio)) !== null) {
      let emp = em[1].trim().replace(/\.$/, '').replace(/^@\s*/, '');
      // Filter out non-employer matches
      if (emp.length > 2 && emp.length < 80 && !emp.match(/^(and|the|a|an|in|at|for|to|with|of)$/i)) {
        employers.add(emp);
      }
    }
  }
  if (employers.size > 0) result.prior_employers = [...employers].join(', ');

  // Determine technical competence
  const techKeywords = /engineer|developer|programmer|CTO|technical|software|machine learning|ML|AI|deep learning|research|scientist|PhD|computer science|CS|data science|architecture|systems|infrastructure|backend|frontend|fullstack|full-stack|robotics/i;
  const businessKeywords = /CEO|COO|CFO|business|operations|strategy|sales|marketing|growth|product manager|PM|finance|consulting|MBA|analyst|investment|venture|partnerships/i;

  if (bio.match(techKeywords)) {
    if (bio.match(/PhD|published|research|professor|scientist/i)) {
      result.technical_competence = 'High';
    } else if (bio.match(/senior|staff|principal|lead|architect|CTO/i)) {
      result.technical_competence = 'High';
    } else {
      result.technical_competence = 'Medium';
    }
  } else if (bio.match(businessKeywords)) {
    result.technical_competence = 'Non-technical';
  }

  // Check repeat founder
  if (bio.match(/(?:serial|repeat|previous|prior)\s*(?:entrepreneur|founder)|founded\s+\d|(?:co-)?founded\s+(?:and\s+)?(?:sold|exited|acquired)|prev(?:ious)?\s+(?:co-)?founder|latest_yc_company/i)) {
    result.is_repeat_founder = 1;
  }

  // Publications
  if (bio.match(/published|publication|paper|NeurIPS|ICML|ICLR|ACL|CVPR|AAAI|Interspeech|EMNLP|Nature|Science|Cell|journal|conference/i)) {
    result.publications_count = 1; // Flag that they have publications
  }

  // Awards
  const awardMatch = bio.match(/(?:award|prize|fellowship|scholar|honor|medal|olympiad|won|recipient)[^.;]*/gi);
  if (awardMatch) {
    result.awards = awardMatch.map(a => a.trim()).join('; ');
  }

  // Patents
  if (bio.match(/patent/i)) {
    result.patents = 'Has patents (see LinkedIn)';
  }

  return result;
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const db = getDb();
  const companies = db.prepare('SELECT id, slug, name FROM companies ORDER BY id').all();

  console.log('Scraping founder bios for ' + companies.length + ' companies...\n');

  const updateFounder = db.prepare(`
    UPDATE founders SET
      bio = COALESCE(?, bio),
      schools = COALESCE(?, schools),
      degrees = COALESCE(?, degrees),
      prior_employers = COALESCE(?, prior_employers),
      technical_competence = COALESCE(?, technical_competence),
      is_repeat_founder = COALESCE(?, is_repeat_founder),
      publications_count = CASE WHEN ? > 0 THEN ? ELSE publications_count END,
      awards = COALESCE(?, awards),
      patents = COALESCE(?, patents)
    WHERE company_id = ? AND name = ?
  `);

  let totalUpdated = 0;
  let totalWithBio = 0;
  let totalWithSchools = 0;
  let totalWithEmployers = 0;

  for (let i = 0; i < companies.length; i++) {
    const company = companies[i];
    const url = 'https://www.ycombinator.com/companies/' + company.slug;
    process.stdout.write('[' + (i+1) + '/' + companies.length + '] ' + company.name + '... ');

    try {
      const { status, body } = await fetch(url);
      if (status !== 200) { console.log('HTTP ' + status); continue; }

      const companyData = parseCompanyPage(body);
      if (!companyData || !companyData.founders) { console.log('NO DATA'); continue; }

      const founderInfos = [];
      for (const f of companyData.founders) {
        const bio = (f.founder_bio || '').replace(/&#x27;/g, "'").replace(/&amp;/g, '&');
        const parsed = parseBio(bio);

        // Check if this founder has appeared in another YC company (repeat founder)
        if (f.latest_yc_company && f.latest_yc_company.name !== company.name) {
          parsed.is_repeat_founder = 1;
        }

        updateFounder.run(
          bio || null,
          parsed.schools || null,
          parsed.degrees || null,
          parsed.prior_employers || null,
          parsed.technical_competence || null,
          parsed.is_repeat_founder || null,
          parsed.publications_count || 0, parsed.publications_count || 0,
          parsed.awards || null,
          parsed.patents || null,
          company.id,
          f.full_name
        );

        totalUpdated++;
        if (bio) totalWithBio++;
        if (parsed.schools) totalWithSchools++;
        if (parsed.prior_employers) totalWithEmployers++;

        founderInfos.push(f.full_name + (parsed.schools ? ' [' + parsed.schools + ']' : '') + (parsed.prior_employers ? ' {' + parsed.prior_employers + '}' : ''));
      }

      console.log(founderInfos.join(', '));
    } catch(e) {
      console.log('ERROR: ' + e.message);
    }

    if (i % 15 === 14) await sleep(2000);
    else await sleep(300);
  }

  console.log('\n' + '='.repeat(60));
  console.log('Founders updated: ' + totalUpdated);
  console.log('With bio: ' + totalWithBio);
  console.log('With schools: ' + totalWithSchools);
  console.log('With employers: ' + totalWithEmployers);

  // Print sample
  const sample = db.prepare(`
    SELECT name, bio, schools, prior_employers, technical_competence, is_repeat_founder
    FROM founders WHERE bio IS NOT NULL AND bio != '' LIMIT 10
  `).all();

  console.log('\n=== SAMPLE FOUNDERS WITH DATA ===');
  sample.forEach(f => {
    console.log('\n' + f.name + ':');
    console.log('  Bio: ' + (f.bio || '').substring(0, 120));
    console.log('  Schools: ' + (f.schools || '-'));
    console.log('  Employers: ' + (f.prior_employers || '-'));
    console.log('  Technical: ' + (f.technical_competence || '-'));
    console.log('  Repeat: ' + (f.is_repeat_founder ? 'Yes' : 'No'));
  });

  db.close();
}

main().catch(console.error);
