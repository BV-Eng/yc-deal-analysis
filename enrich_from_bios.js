// Extract schools, employers, and distinctions from existing bio text
// This doesn't require any external API calls

const db = require('better-sqlite3')('data/yc_deals.db');

// Comprehensive lists of known schools and companies
const SCHOOLS = [
  // Top US Universities
  'MIT', 'Stanford', 'Harvard', 'Yale', 'Princeton', 'Columbia', 'Cornell', 'Penn',
  'UPenn', 'University of Pennsylvania', 'Brown', 'Dartmouth',
  'Berkeley', 'UC Berkeley', 'Caltech', 'Carnegie Mellon', 'CMU',
  'Georgia Tech', 'UCLA', 'UCSB', 'UCSD', 'UC San Diego', 'UC Davis', 'UC Irvine',
  'University of Michigan', 'UMich', 'University of Illinois', 'UIUC',
  'University of Texas', 'UT Austin', 'Texas A&M',
  'Duke', 'Northwestern', 'Rice', 'Vanderbilt', 'Emory',
  'Johns Hopkins', 'USC', 'NYU', 'UChicago', 'University of Chicago',
  'University of Washington', 'UW', 'University of Virginia', 'UVA',
  'University of Wisconsin', 'Purdue', 'Ohio State',
  'University of Maryland', 'UMD', 'Boston University', 'BU',
  'Northeastern', 'Tufts', 'Georgetown',
  'Wharton', 'HBS', 'Harvard Business School', 'Kellogg', 'Booth',
  'Stanford GSB', 'Sloan', 'MIT Sloan', 'Columbia Business School',
  'University of Florida', 'UF', 'Penn State', 'University of Minnesota',
  'Indiana University', 'University of Colorado', 'Arizona State', 'ASU',
  'University of North Carolina', 'UNC', 'Wake Forest',
  'Rutgers', 'University of Pittsburgh', 'Syracuse', 'RPI',
  'Case Western', 'Lehigh', 'Villanova', 'Santa Clara',
  'University of Notre Dame', 'Notre Dame',
  'Williams', 'Amherst', 'Pomona', 'Swarthmore', 'Wellesley',
  'Harvey Mudd', 'Claremont McKenna',
  'Reed', 'Grinnell', 'Oberlin', 'Carleton', 'Bowdoin',
  'West Point', 'Naval Academy', 'Air Force Academy',
  // International
  'Oxford', 'Cambridge', 'Imperial College', 'Imperial', 'UCL',
  'London School of Economics', 'LSE', 'Kings College',
  'ETH Zurich', 'ETH', 'EPFL', 'Sorbonne',
  'University of Toronto', 'UofT', 'McGill', 'Waterloo', 'UBC',
  'IIT', 'IIT Bombay', 'IIT Delhi', 'IIT Madras', 'IIT Kanpur', 'IIT Kharagpur',
  'IIT Roorkee', 'IIT Guwahati', 'IIT Hyderabad',
  'BITS Pilani', 'NIT', 'ISB', 'IIM', 'IIM Ahmedabad',
  'National University of Singapore', 'NUS', 'NTU', 'Nanyang',
  'Tsinghua', 'Peking University', 'PKU', 'Fudan', 'Zhejiang',
  'University of Tokyo', 'Todai', 'Kyoto University', 'Keio', 'Waseda',
  'Seoul National University', 'SNU', 'KAIST', 'Yonsei',
  'Technion', 'Hebrew University', 'Tel Aviv University',
  'INSEAD', 'HEC Paris', 'London Business School', 'LBS',
  'University of Melbourne', 'ANU', 'University of Sydney', 'UNSW',
  'University of Cape Town', 'Stellenbosch',
  'TU Munich', 'TU Berlin', 'RWTH Aachen', 'Heidelberg',
  'KTH', 'Chalmers', 'DTU', 'Aalto', 'TU Delft',
  'Polytechnique', 'Ecole Polytechnique', 'ENS', 'CentraleSupelec',
  'Bocconi', 'Politecnico di Milano',
  'University of Sao Paulo', 'USP', 'UNICAMP',
  'Tec de Monterrey', 'UNAM',
  'HKUST', 'University of Hong Kong', 'HKU',
  // Y Combinator
  'Y Combinator', 'YC'
];

const COMPANIES = [
  // FAANG+
  'Google', 'Meta', 'Facebook', 'Apple', 'Amazon', 'AWS', 'Microsoft', 'Netflix',
  // Big Tech
  'Stripe', 'Uber', 'Airbnb', 'SpaceX', 'Tesla', 'Palantir', 'Coinbase',
  'Robinhood', 'DoorDash', 'Instacart', 'Lyft', 'Twitter', 'X',
  'Salesforce', 'Oracle', 'SAP', 'IBM', 'Intel', 'Nvidia', 'AMD', 'Qualcomm',
  'Snap', 'Pinterest', 'Reddit', 'Figma', 'Notion', 'Slack', 'Dropbox',
  'Shopify', 'Square', 'Block', 'PayPal', 'Visa', 'Mastercard',
  'Snowflake', 'Databricks', 'Datadog', 'Cloudflare', 'HashiCorp',
  'Twitch', 'Zoom', 'DocuSign', 'Okta', 'CrowdStrike', 'Splunk',
  // AI
  'DeepMind', 'OpenAI', 'Anthropic', 'Waymo', 'Cruise', 'Aurora',
  // Fintech
  'Brex', 'Plaid', 'Chime', 'Affirm', 'Klarna', 'Revolut', 'Wise',
  'Goldman Sachs', 'JPMorgan', 'JP Morgan', 'Morgan Stanley', 'Citadel',
  'Two Sigma', 'Jane Street', 'Bridgewater', 'BlackRock', 'Blackstone',
  'Deutsche Bank', 'Bank of America', 'Citigroup', 'Barclays', 'HSBC',
  'Wells Fargo', 'Credit Suisse', 'UBS',
  // Consulting
  'McKinsey', 'BCG', 'Bain', 'Accenture', 'Deloitte', 'PwC', 'EY', 'KPMG',
  'Boston Consulting', 'Oliver Wyman',
  // VC/PE
  'Y Combinator', 'YC', 'Sequoia', 'a16z', 'Andreessen Horowitz',
  'Kleiner Perkins', 'Benchmark', 'Index Ventures', 'Greylock',
  'Lightspeed', 'Founders Fund', 'Tiger Global', 'Insight Partners',
  // Healthcare/Pharma
  'Pfizer', 'Johnson & Johnson', 'J&J', 'Merck', 'Roche', 'Novartis',
  'AbbVie', 'Bristol-Myers', 'Amgen', 'Gilead', 'Regeneron', 'Moderna',
  'Genentech', 'AstraZeneca', 'Eli Lilly', 'Abbott',
  // Defense/Aerospace
  'Boeing', 'Lockheed Martin', 'Raytheon', 'Northrop Grumman', 'NASA',
  'General Dynamics', 'BAE Systems', 'Anduril',
  // Energy
  'ExxonMobil', 'Chevron', 'Shell', 'BP', 'NextEra', 'Enphase',
  // Other notable
  'Johnson Controls', 'Siemens', 'GE', 'General Electric',
  'Nike', 'Disney', 'Warner Bros', 'Sony', 'Samsung',
  'Walmart', 'Target', 'Costco', 'Home Depot',
  'Procter & Gamble', 'P&G', 'Unilever', 'Nestle',
  'Toyota', 'Ford', 'GM', 'General Motors', 'BMW', 'Mercedes',
  'Citi', 'Capital One', 'American Express', 'Amex',
  'LinkedIn', 'Atlassian', 'Twilio', 'HubSpot', 'ServiceNow',
  'VMware', 'Dell', 'HP', 'Hewlett-Packard', 'Cisco',
  'Lockheed', 'Raytheon', 'DARPA',
  'McKinsey & Company', 'Boston Consulting Group',
  'Bain & Company', 'PricewaterhouseCoopers',
  'Ernst & Young', 'Deloitte & Touche',
  'World Bank', 'IMF', 'United Nations', 'UN',
  'National Institutes of Health', 'NIH',
  'Center for Disease Control', 'CDC'
];

const DISTINCTION_PATTERNS = [
  { re: /Forbes\s+30\s*(?:Under|U)\s*30/i, label: 'Forbes 30 Under 30' },
  { re: /Thiel\s+Fellow(?:ship)?/i, label: 'Thiel Fellow' },
  { re: /Rhodes\s+Scholar/i, label: 'Rhodes Scholar' },
  { re: /Marshall\s+Scholar/i, label: 'Marshall Scholar' },
  { re: /Fulbright\s+(?:Scholar|Fellow)/i, label: 'Fulbright Scholar' },
  { re: /(?:was\s+)?valedictorian/i, label: 'Valedictorian' },
  { re: /summa\s+cum\s+laude/i, label: 'Summa Cum Laude' },
  { re: /magna\s+cum\s+laude/i, label: 'Magna Cum Laude' },
  { re: /cum\s+laude/i, label: 'Cum Laude' },
  { re: /(?:math|physics|chemistry|informatics|programming|computing|science)\s+[Oo]lympiad/i, label: null }, // capture with context
  { re: /gold\s+medal(?:ist)?/i, label: 'Gold Medalist' },
  { re: /national\s+(?:team|champion|finalist)/i, label: null },
  { re: /(?:Ph\.?D|PhD|Doctorate|doctoral)/i, label: 'PhD' },
  { re: /(?:published|peer[- ]reviewed)\s+(?:research|paper|author)/i, label: 'Published Researcher' },
  { re: /patent\s+holder|hold[s]?\s+patent|patented/i, label: 'Patent holder' },
  { re: /TechCrunch\s+Disrupt/i, label: 'TechCrunch Disrupt' },
  { re: /(?:won|winner|awarded)\s+(?:the\s+)?(?:\$[\d,.]+[MmKk]?|first\s+place|grand\s+prize)/i, label: null },
  { re: /serial\s+entrepreneur/i, label: 'Serial Entrepreneur' },
  { re: /(?:2|3|two|three|multiple)(?:x|\s+time[s]?)\s+founder/i, label: 'Serial Entrepreneur' },
  { re: /repeat\s+founder/i, label: 'Repeat Founder' },
  { re: /(?:sold|acquired|exited)\s+(?:his|her|their|to\s+)/i, label: 'Previous Exit' },
  { re: /IPO/i, label: null },
  { re: /highest\s+honors/i, label: 'Highest Honors' },
  { re: /dean'?s?\s+list/i, label: "Dean's List" },
  { re: /(?:academic|merit|presidential|national)\s+scholar(?:ship)?/i, label: null },
  { re: /(?:NSF|NIH|DARPA)\s+(?:grant|fellow|funded)/i, label: null },
  { re: /Y\s*Combinator\s+(?:alum|S\d{2}|W\d{2}|F\d{2})/i, label: null } // capture with batch info
];

function extractFromBio(bio, founderName, companyName) {
  if (!bio) return { schools: [], employers: [], distinctions: [] };

  var result = { schools: [], employers: [], distinctions: [] };
  var bioLower = bio.toLowerCase();

  // Extract schools
  SCHOOLS.forEach(function(school) {
    if (school === 'YC' || school === 'Y Combinator') return; // Skip YC
    // Word boundary check
    var schoolLower = school.toLowerCase();
    var idx = bioLower.indexOf(schoolLower);
    if (idx > -1) {
      // Check it's a word boundary (not part of another word)
      var charBefore = idx > 0 ? bioLower[idx - 1] : ' ';
      var charAfter = idx + schoolLower.length < bioLower.length ? bioLower[idx + schoolLower.length] : ' ';
      var isBoundary = /[\s,.\-;:()/|]/.test(charBefore) || idx === 0;
      var isEndBoundary = /[\s,.\-;:()/|']/.test(charAfter) || (idx + schoolLower.length === bioLower.length);
      if (isBoundary && isEndBoundary) {
        // Use the original case version from bio
        var original = bio.substring(idx, idx + school.length);
        if (result.schools.indexOf(school) === -1) {
          result.schools.push(school);
        }
      }
    }
  });

  // Extract employers
  COMPANIES.forEach(function(company) {
    if (company === 'YC' || company === 'Y Combinator') return;
    if (company.toLowerCase() === companyName.toLowerCase()) return;
    var companyLower = company.toLowerCase();
    var idx = bioLower.indexOf(companyLower);
    if (idx > -1) {
      var charBefore = idx > 0 ? bioLower[idx - 1] : ' ';
      var charAfter = idx + companyLower.length < bioLower.length ? bioLower[idx + companyLower.length] : ' ';
      var isBoundary = /[\s,.\-;:()/|@]/.test(charBefore) || idx === 0;
      var isEndBoundary = /[\s,.\-;:()/|'.]/.test(charAfter) || (idx + companyLower.length === bioLower.length);
      if (isBoundary && isEndBoundary) {
        if (result.employers.indexOf(company) === -1) {
          result.employers.push(company);
        }
      }
    }
  });

  // Extract distinctions
  DISTINCTION_PATTERNS.forEach(function(dp) {
    var match = bio.match(dp.re);
    if (match) {
      var label = dp.label || match[0];
      if (result.distinctions.indexOf(label) === -1) {
        result.distinctions.push(label);
      }
    }
  });

  // Also check for "YC S/W/F##" pattern to note YC alum status
  var ycMatch = bio.match(/YC\s+([SWF]\d{2})/i) || bio.match(/Y\s*Combinator\s+([SWF]\d{2})/i);
  if (ycMatch) {
    var ycLabel = 'YC ' + ycMatch[1].toUpperCase() + ' Alum';
    if (result.distinctions.indexOf(ycLabel) === -1) {
      result.distinctions.push(ycLabel);
    }
  }

  // Check for previous exit/acquisition mentions
  var exitMatch = bio.match(/(?:sold|acquired by|acquisition by|exited to)\s+([A-Z][A-Za-z\s&]+?)[\s,.\(\)]/);
  if (exitMatch) {
    var exitLabel = 'Previous Exit (→ ' + exitMatch[1].trim() + ')';
    if (result.distinctions.indexOf(exitLabel) === -1 && !result.distinctions.some(function(d) { return d.indexOf('Exit') > -1; })) {
      result.distinctions.push(exitLabel);
    }
  }
  // Also check "Acquired by" patterns
  var acqMatch = bio.match(/[Aa]cquired\s+by\s+([A-Z][A-Za-z\s&]+?)[\s,.\(\)]/);
  if (acqMatch && !result.distinctions.some(function(d) { return d.indexOf('Exit') > -1; })) {
    result.distinctions.push('Previous Exit (→ ' + acqMatch[1].trim() + ')');
  }

  // Dedupe - remove "Cum Laude" if "Magna" or "Summa" already present
  if (result.distinctions.indexOf('Summa Cum Laude') > -1 || result.distinctions.indexOf('Magna Cum Laude') > -1) {
    result.distinctions = result.distinctions.filter(function(d) { return d !== 'Cum Laude'; });
  }

  return result;
}

function mergeArrays(existing, newItems) {
  if (!existing) return newItems;
  var existingArr = existing.split(/,\s*/);
  newItems.forEach(function(item) {
    var found = existingArr.some(function(e) { return e.toLowerCase() === item.toLowerCase(); });
    if (!found) existingArr.push(item);
  });
  return existingArr.filter(Boolean);
}

function main() {
  var founders = db.prepare(`
    SELECT f.id, f.name, f.bio, f.schools, f.prior_employers, f.awards, c.name as company_name
    FROM founders f
    JOIN companies c ON f.company_id = c.id
    ORDER BY f.id
  `).all();

  console.log('Parsing ' + founders.length + ' founder bios for schools, employers, and distinctions...\n');

  var updateStmt = db.prepare('UPDATE founders SET schools = ?, prior_employers = ?, awards = ? WHERE id = ?');
  var enriched = 0;

  founders.forEach(function(f) {
    var extracted = extractFromBio(f.bio, f.name, f.company_name);

    var schools = mergeArrays(f.schools, extracted.schools);
    var employers = mergeArrays(f.prior_employers, extracted.employers);
    var distinctions = mergeArrays(f.awards, extracted.distinctions);

    var schoolsStr = schools.join(', ');
    var employersStr = employers.join(', ');
    var distinctionsStr = distinctions.join(', ');

    var changed = schoolsStr !== (f.schools || '') ||
                  employersStr !== (f.prior_employers || '') ||
                  distinctionsStr !== (f.awards || '');

    if (changed) {
      updateStmt.run(schoolsStr || null, employersStr || null, distinctionsStr || null, f.id);
      var parts = [];
      if (schoolsStr) parts.push('🎓 ' + schoolsStr);
      if (employersStr) parts.push('💼 ' + employersStr);
      if (distinctionsStr) parts.push('🏆 ' + distinctionsStr);
      console.log(f.name + ': ' + parts.join(' | '));
      enriched++;
    }
  });

  console.log('\n============================');
  console.log('Enriched ' + enriched + ' founders from bios');
  console.log('============================');

  console.log('\nUpdated coverage:');
  console.log('With schools:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE schools IS NOT NULL AND schools != ''").get().c + ' / ' + founders.length);
  console.log('With employers:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE prior_employers IS NOT NULL AND prior_employers != ''").get().c + ' / ' + founders.length);
  console.log('With awards/distinctions:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE awards IS NOT NULL AND awards != ''").get().c + ' / ' + founders.length);

  // Show some samples
  console.log('\n--- Sample enriched profiles ---');
  var samples = db.prepare("SELECT name, schools, prior_employers, awards, bio FROM founders WHERE awards IS NOT NULL AND awards != '' LIMIT 15").all();
  samples.forEach(function(s) {
    console.log('\n' + s.name + ':');
    console.log('  Schools: ' + (s.schools || '-'));
    console.log('  Employers: ' + (s.prior_employers || '-'));
    console.log('  Distinctions: ' + (s.awards || '-'));
  });
}

main();
