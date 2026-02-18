const { getDb } = require('./backend/database');

// Known top-tier schools
const TIER1_SCHOOLS = ['MIT', 'Stanford', 'Harvard', 'Yale', 'Princeton', 'Caltech', 'Carnegie Mellon', 'CMU', 'Columbia', 'Cornell', 'Oxford', 'Cambridge', 'UC Berkeley', 'Berkeley', 'ETH', 'EPFL'];
const TIER2_SCHOOLS = ['IIT Bombay', 'IIT Delhi', 'Georgia Tech', 'Waterloo', 'NYU', 'UCLA', 'UIUC', 'UCSB', 'NUS', 'Tsinghua', 'University of Michigan', 'University of Wisconsin', 'University of Washington', 'University of Chicago', 'Purdue', 'Princeton'];
const TOP_EMPLOYERS = ['Google', 'Meta', 'Facebook', 'Apple', 'Amazon', 'Microsoft', 'Netflix', 'Tesla', 'Stripe', 'Airbnb', 'Uber', 'Lyft', 'Palantir', 'SpaceX', 'OpenAI', 'Anthropic', 'DeepMind', 'McKinsey', 'BCG', 'Bain', 'Goldman Sachs', 'Morgan Stanley', 'JP Morgan', 'JPMorgan', 'Citadel', 'Two Sigma', 'Jane Street', 'Bridgewater', 'Coinbase', 'Robinhood', 'Square', 'Block', 'Plaid', 'DoorDash', 'Roblox', 'Intel', 'Nvidia', 'AMD', 'Qualcomm', 'Oracle', 'Salesforce', 'LinkedIn', 'Snap', 'Docker', 'Databricks', 'TikTok', 'Brex', 'Deloitte', 'Accenture', 'KPMG', 'EY', 'PwC', 'AT Kearney', 'IBM', 'Samsung', 'CERN', 'NASA', 'Zoox', 'Illumina', 'Federal Reserve'];

function extractCleanSchools(bio) {
  if (!bio) return '';
  const allSchools = [...TIER1_SCHOOLS, ...TIER2_SCHOOLS];
  const found = new Set();

  for (const school of allSchools) {
    if (bio.toLowerCase().includes(school.toLowerCase())) {
      found.add(school);
    }
  }

  // Also check for IIT variants
  const iitMatch = bio.match(/IIT\s+\w+/gi);
  if (iitMatch) iitMatch.forEach(m => found.add(m));

  // Check for "University of X" patterns
  const uniMatch = bio.match(/University of \w+/gi);
  if (uniMatch) uniMatch.forEach(m => {
    if (!m.match(/University of (the|a|an|my|our)/i)) found.add(m);
  });

  // Check for degree info
  const degreeMatch = bio.match(/(?:PhD|Ph\.D\.|Doctorate|Masters?|MBA|BTech|MTech|BS|MS|B\.S\.|M\.S\.)\s+(?:in\s+)?([A-Z][^.,;]{3,40})/g);
  if (degreeMatch) {
    degreeMatch.forEach(d => {
      const clean = d.replace(/^\S+\s+(?:in\s+)?/, '').trim();
      if (clean.length > 3 && clean.length < 50) found.add(clean + ' (degree)');
    });
  }

  return [...found].join(', ');
}

function extractCleanEmployers(bio) {
  if (!bio) return '';
  const found = new Set();

  for (const emp of TOP_EMPLOYERS) {
    // Match whole word
    const regex = new RegExp('\\b' + emp.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
    if (regex.test(bio)) {
      found.add(emp);
    }
  }

  return [...found].join(', ');
}

function determineTechCompetence(bio, title) {
  if (!bio && !title) return '';
  const combined = ((bio || '') + ' ' + (title || '')).toLowerCase();

  // Strong technical signals
  if (combined.match(/phd|ph\.d|published|research scientist|professor|neurips|icml|iclr|cvpr|acl|chief technology|gpu kernel/i)) {
    return 'High';
  }
  if (combined.match(/cto|senior engineer|staff engineer|principal engineer|tech lead|machine learning|ml engineer|ai engineer|systems architect|built.*platform|software architect/i)) {
    return 'High';
  }
  if (combined.match(/engineer|developer|programmer|software|swe |cs @|computer science|data science|robotics|full.?stack|backend|frontend|infra/i)) {
    return 'Medium';
  }
  if (combined.match(/ceo|coo|cfo|cbo|business|operations|strategy|sales|marketing|growth|consulting|consultant|product manager|pm |finance|analyst|investment|venture|partnerships|legal|lawyer|attorney|designer/i)) {
    return 'Non-technical';
  }
  return '';
}

function isRepeatFounder(bio) {
  if (!bio) return 0;
  const lower = bio.toLowerCase();
  if (lower.match(/serial entrepreneur|repeat founder|founded.*(?:sold|exited|acquired)|co-?founded.*yc\s*[swf]\d|prev(?:ious)?(?:ly)?\s+(?:co-?)?founded|second|third.*company|multiple.*compan/i)) return 1;
  // Check for YC batch references suggesting prior YC company
  if (lower.match(/yc\s+[swf]\d{2}/gi)) {
    const matches = lower.match(/yc\s+[swf]\d{2}/gi);
    if (matches && matches.length > 1) return 1; // Multiple YC batches
  }
  if (lower.match(/\((?:s|w|f)\d{2}\)/gi)) {
    const matches = lower.match(/\((?:s|w|f)\d{2}\)/gi);
    if (matches && matches.length > 0) return 1;
  }
  return 0;
}

function hasPublications(bio) {
  if (!bio) return 0;
  if (bio.match(/published|publication|20\+\s+publication|paper|NeurIPS|ICML|ICLR|ACL|CVPR|AAAI|Interspeech|EMNLP|Nature|Science|Cell|IEEE|SIGMOD|KDD|journal|conference|arxiv/i)) {
    return 1;
  }
  return 0;
}

function extractAwards(bio) {
  if (!bio) return '';
  const patterns = [
    /Forbes\s+30\s+Under\s+30/i,
    /Fulbright\s+scholar/i,
    /Olympiad/i,
    /(?:gold|silver|bronze)\s+medal/i,
    /valedictorian/i,
    /summa\s+cum\s+laude/i,
    /highest\s+honors/i,
    /national\s+(?:science|math)\s+award/i,
    /(?:chess|FIDE)\s+\d{4}/i,
    /national\s+(?:team|youth)/i,
  ];
  const awards = [];
  for (const p of patterns) {
    const m = bio.match(p);
    if (m) awards.push(m[0]);
  }
  return awards.join(', ');
}

function main() {
  const db = getDb();

  const founders = db.prepare(`
    SELECT f.id, f.name, f.title, f.bio, f.company_id,
      c.name as company_name
    FROM founders f
    JOIN companies c ON c.id = f.company_id
    ORDER BY f.id
  `).all();

  console.log('Cleaning data for ' + founders.length + ' founders...\n');

  const update = db.prepare(`
    UPDATE founders SET
      schools = ?,
      prior_employers = ?,
      technical_competence = ?,
      is_repeat_founder = ?,
      publications_count = ?,
      awards = ?
    WHERE id = ?
  `);

  let schoolCount = 0, empCount = 0, techCount = 0, repeatCount = 0, pubCount = 0;

  const transaction = db.transaction(() => {
    for (const f of founders) {
      const schools = extractCleanSchools(f.bio);
      const employers = extractCleanEmployers(f.bio);
      const techComp = determineTechCompetence(f.bio, f.title);
      const repeat = isRepeatFounder(f.bio);
      const pubs = hasPublications(f.bio);
      const awards = extractAwards(f.bio);

      if (schools) schoolCount++;
      if (employers) empCount++;
      if (techComp) techCount++;
      if (repeat) repeatCount++;
      if (pubs) pubCount++;

      update.run(
        schools || null,
        employers || null,
        techComp || null,
        repeat,
        pubs,
        awards || null,
        f.id
      );
    }
  });

  transaction();

  console.log('=== CLEANUP COMPLETE ===');
  console.log('Founders with schools: ' + schoolCount);
  console.log('Founders with employers: ' + empCount);
  console.log('Founders with tech competence: ' + techCount);
  console.log('Repeat founders: ' + repeatCount);
  console.log('Founders with publications: ' + pubCount);

  // Print sample
  const sample = db.prepare(`
    SELECT name, title, schools, prior_employers, technical_competence, is_repeat_founder, publications_count, awards, bio
    FROM founders
    WHERE schools IS NOT NULL OR prior_employers IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 20
  `).all();

  console.log('\n=== SAMPLE FOUNDERS ===');
  sample.forEach(f => {
    console.log('\n' + f.name + ' (' + (f.title || '') + '):');
    console.log('  Schools: ' + (f.schools || '-'));
    console.log('  Employers: ' + (f.prior_employers || '-'));
    console.log('  Technical: ' + (f.technical_competence || '-'));
    console.log('  Repeat: ' + (f.is_repeat_founder ? 'Yes' : 'No'));
    if (f.publications_count) console.log('  Publications: Yes');
    if (f.awards) console.log('  Awards: ' + f.awards);
  });

  db.close();
}

main();
