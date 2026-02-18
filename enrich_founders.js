const https = require('https');
const http = require('http');
const db = require('better-sqlite3')('data/yc_deals.db');

function fetch(url) {
  return new Promise(function(resolve, reject) {
    const mod = url.startsWith('https') ? https : http;
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9'
      }
    };
    mod.get(url, options, function(res) {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch(res.headers.location).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', function(chunk) { data += chunk; });
      res.on('end', function() { resolve({ status: res.statusCode, body: data }); });
    }).on('error', reject);
  });
}

function decodeHtml(html) {
  return html
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function sleep(ms) {
  return new Promise(function(resolve) { setTimeout(resolve, ms); });
}

async function searchFounder(name, companyName) {
  const query = encodeURIComponent(name + ' ' + companyName + ' linkedin');
  const url = 'https://html.duckduckgo.com/html/?q=' + query;

  try {
    const result = await fetch(url);
    if (result.status !== 200) return null;

    var info = {
      schools: [],
      employers: [],
      distinctions: []
    };

    // Extract all snippets
    var snippets = result.body.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/a/g) || [];
    var titles = result.body.match(/class="result__a"[^>]*>([\s\S]*?)<\/a/g) || [];
    var allText = '';

    snippets.forEach(function(s) {
      var text = decodeHtml(s.replace(/class="result__snippet"[^>]*>/, ''));
      allText += ' ' + text;
    });
    titles.forEach(function(t) {
      var text = decodeHtml(t.replace(/class="result__a"[^>]*>/, ''));
      allText += ' ' + text;
    });

    // Parse LinkedIn-style snippet patterns
    // "Experience: Company1, Company2 · Education: School1"
    var expMatch = allText.match(/Experience:?\s*([^·|]+?)(?:\s*[·|]|$)/i);
    if (expMatch) {
      var employers = expMatch[1].split(/[,;]/).map(function(e) { return e.trim(); }).filter(function(e) {
        return e.length > 1 && e.length < 50 && e.toLowerCase() !== name.toLowerCase();
      });
      info.employers = employers;
    }

    var eduMatch = allText.match(/Education:?\s*([^·|]+?)(?:\s*[·|]|$)/i);
    if (eduMatch) {
      var schools = eduMatch[1].split(/[,;]/).map(function(s) { return s.trim(); }).filter(function(s) {
        return s.length > 1 && s.length < 80;
      });
      info.schools = schools;
    }

    // Also look for school names in text
    var knownSchools = [
      'MIT', 'Stanford', 'Harvard', 'Yale', 'Princeton', 'Columbia', 'Cornell', 'Penn',
      'Berkeley', 'Caltech', 'Carnegie Mellon', 'Georgia Tech', 'UCLA', 'UCSB', 'UCSD',
      'University of Michigan', 'University of Illinois', 'University of Texas',
      'Oxford', 'Cambridge', 'Imperial College', 'ETH Zurich', 'IIT', 'Waterloo',
      'Duke', 'Northwestern', 'Brown', 'Dartmouth', 'Rice', 'Vanderbilt',
      'Johns Hopkins', 'USC', 'NYU', 'UChicago', 'University of Chicago',
      'Wharton', 'INSEAD', 'London Business School', 'HBS',
      'University of Washington', 'University of Toronto', 'McGill',
      'National University of Singapore', 'Tsinghua', 'Peking University'
    ];

    knownSchools.forEach(function(school) {
      if (allText.indexOf(school) > -1 && info.schools.indexOf(school) === -1) {
        // Check it's not already captured
        var alreadyHave = info.schools.some(function(s) { return s.indexOf(school) > -1; });
        if (!alreadyHave) info.schools.push(school);
      }
    });

    // Look for notable employers
    var knownCompanies = [
      'Google', 'Meta', 'Facebook', 'Apple', 'Amazon', 'Microsoft', 'Netflix', 'Stripe',
      'Uber', 'Airbnb', 'SpaceX', 'Tesla', 'Palantir', 'Coinbase', 'Robinhood',
      'Goldman Sachs', 'McKinsey', 'BCG', 'Bain', 'JPMorgan', 'Morgan Stanley',
      'DoorDash', 'Instacart', 'Lyft', 'Twitter', 'X Corp', 'LinkedIn',
      'Salesforce', 'Oracle', 'SAP', 'IBM', 'Intel', 'Nvidia', 'AMD',
      'Snap', 'Pinterest', 'Reddit', 'Figma', 'Notion', 'Slack',
      'Brex', 'Plaid', 'Square', 'Block', 'PayPal', 'Visa',
      'DeepMind', 'OpenAI', 'Anthropic', 'Databricks', 'Snowflake',
      'Accenture', 'Deloitte', 'PwC', 'EY', 'KPMG',
      'Y Combinator', 'Sequoia', 'a16z', 'Andreessen Horowitz'
    ];

    knownCompanies.forEach(function(company) {
      if (allText.indexOf(company) > -1 && info.employers.indexOf(company) === -1) {
        var alreadyHave = info.employers.some(function(e) { return e.indexOf(company) > -1; });
        if (!alreadyHave) info.employers.push(company);
      }
    });

    // Look for distinctions
    var distinctionPatterns = [
      /Forbes\s+30\s+Under\s+30/i,
      /Thiel\s+Fellow/i,
      /Rhodes\s+Scholar/i,
      /Marshall\s+Scholar/i,
      /Fulbright/i,
      /valedictorian/i,
      /summa\s+cum\s+laude/i,
      /magna\s+cum\s+laude/i,
      /cum\s+laude/i,
      /Ph\.?D\.?/i,
      /MBA/,
      /M\.?S\.?(?:\s|,|$)/,
      /Olympiad/i,
      /gold\s+medal/i,
      /national\s+(?:team|champion)/i,
      /patent/i,
      /published/i,
      /peer.?reviewed/i,
      /TechCrunch/i,
      /Y\s*Combinator\s+alum/i
    ];

    distinctionPatterns.forEach(function(pattern) {
      var match = allText.match(pattern);
      if (match) {
        // Get surrounding context (up to 40 chars around)
        var idx = allText.search(pattern);
        var start = Math.max(0, idx - 20);
        var end = Math.min(allText.length, idx + match[0].length + 20);
        var context = allText.substring(start, end).trim();
        info.distinctions.push(match[0]);
      }
    });

    // Remove Y Combinator from employers (they're all YC companies)
    info.employers = info.employers.filter(function(e) {
      return e !== 'Y Combinator' && e.indexOf('Y Combinator') === -1;
    });

    // Remove the current company from employers
    info.employers = info.employers.filter(function(e) {
      return e.toLowerCase() !== companyName.toLowerCase();
    });

    // Remove YC from schools
    info.schools = info.schools.filter(function(s) {
      return s !== 'Y Combinator' && s.indexOf('Y Combinator') === -1;
    });

    // Deduplicate
    info.schools = Array.from(new Set(info.schools));
    info.employers = Array.from(new Set(info.employers));
    info.distinctions = Array.from(new Set(info.distinctions));

    return info;
  } catch(e) {
    console.log('  Error:', e.message);
    return null;
  }
}

async function main() {
  // Get all founders with their company names
  const founders = db.prepare(`
    SELECT f.id, f.name, f.schools, f.prior_employers, f.awards, f.bio, c.name as company_name
    FROM founders f
    JOIN companies c ON f.company_id = c.id
    ORDER BY f.id
  `).all();

  console.log('Enriching ' + founders.length + ' founders via DuckDuckGo search...\n');

  const updateStmt = db.prepare(`
    UPDATE founders SET
      schools = CASE WHEN ? != '' THEN ? ELSE schools END,
      prior_employers = CASE WHEN ? != '' THEN ? ELSE prior_employers END,
      awards = CASE WHEN ? != '' THEN ? ELSE awards END
    WHERE id = ?
  `);

  var enriched = 0;
  var skipped = 0;
  var errors = 0;

  for (var i = 0; i < founders.length; i++) {
    var f = founders[i];

    // Rate limit - 1 request per second to be polite
    if (i > 0) await sleep(1200);

    process.stdout.write('[' + (i + 1) + '/' + founders.length + '] ' + f.name + ' (' + f.company_name + ')... ');

    var info = await searchFounder(f.name, f.company_name);
    if (!info) {
      console.log('❌ failed');
      errors++;
      continue;
    }

    var newSchools = info.schools.length > 0 ? info.schools.join(', ') : '';
    var newEmployers = info.employers.length > 0 ? info.employers.join(', ') : '';
    var newAwards = info.distinctions.length > 0 ? info.distinctions.join(', ') : '';

    // Merge with existing data rather than overwriting
    if (f.schools && newSchools) {
      // Combine unique schools
      var allSchools = (f.schools + ', ' + newSchools).split(/,\s*/);
      var uniqueSchools = Array.from(new Set(allSchools.map(function(s) { return s.trim(); }).filter(Boolean)));
      newSchools = uniqueSchools.join(', ');
    } else if (f.schools) {
      newSchools = f.schools;
    }

    if (f.prior_employers && newEmployers) {
      var allEmps = (f.prior_employers + ', ' + newEmployers).split(/,\s*/);
      var uniqueEmps = Array.from(new Set(allEmps.map(function(e) { return e.trim(); }).filter(Boolean)));
      newEmployers = uniqueEmps.join(', ');
    } else if (f.prior_employers) {
      newEmployers = f.prior_employers;
    }

    if (f.awards && newAwards) {
      var allAwards = (f.awards + ', ' + newAwards).split(/,\s*/);
      var uniqueAwards = Array.from(new Set(allAwards.map(function(a) { return a.trim(); }).filter(Boolean)));
      newAwards = uniqueAwards.join(', ');
    } else if (f.awards) {
      newAwards = f.awards;
    }

    var changed = (newSchools !== (f.schools || '')) || (newEmployers !== (f.prior_employers || '')) || (newAwards !== (f.awards || ''));

    if (changed) {
      updateStmt.run(newSchools, newSchools, newEmployers, newEmployers, newAwards, newAwards, f.id);
      var parts = [];
      if (newSchools) parts.push('🎓 ' + newSchools);
      if (newEmployers) parts.push('💼 ' + newEmployers);
      if (newAwards) parts.push('🏆 ' + newAwards);
      console.log('✅ ' + parts.join(' | '));
      enriched++;
    } else {
      console.log('— no new data');
      skipped++;
    }
  }

  console.log('\n============================');
  console.log('Done! Enriched: ' + enriched + ', Unchanged: ' + skipped + ', Errors: ' + errors);
  console.log('============================');

  // Print coverage stats
  console.log('\nUpdated coverage:');
  console.log('With schools:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE schools IS NOT NULL AND schools != ''").get().c + ' / ' + founders.length);
  console.log('With employers:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE prior_employers IS NOT NULL AND prior_employers != ''").get().c + ' / ' + founders.length);
  console.log('With awards:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE awards IS NOT NULL AND awards != ''").get().c + ' / ' + founders.length);
}

main().catch(console.error);
