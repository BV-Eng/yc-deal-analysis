// Enrich founder profiles by fetching LinkedIn public pages
// Uses a headless approach with proper headers to get past auth wall

const https = require('https');
const db = require('better-sqlite3')('data/yc_deals.db');

function fetchUrl(url) {
  return new Promise(function(resolve, reject) {
    // Normalize URL to ensure https://www.linkedin.com format
    url = url.replace('http://', 'https://');
    if (url.indexOf('www.linkedin.com') === -1) {
      url = url.replace('linkedin.com', 'www.linkedin.com');
    }

    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive'
      }
    };

    const req = https.request(options, function(res) {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        var loc = res.headers.location;
        if (loc.startsWith('/')) loc = 'https://www.linkedin.com' + loc;
        return fetchUrl(loc).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', function(chunk) { data += chunk; });
      res.on('end', function() { resolve({ status: res.statusCode, body: data }); });
    });
    req.on('error', reject);
    req.setTimeout(10000, function() { req.destroy(); reject(new Error('Timeout')); });
    req.end();
  });
}

function decodeHtml(text) {
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/\\u002F/g, '/')
    .replace(/\\u0026/g, '&')
    .replace(/<[^>]*>/g, '')
    .trim();
}

function parseLinkedInProfile(html) {
  var result = {
    schools: [],
    employers: [],
    distinctions: [],
    headline: '',
    summary: ''
  };

  // Try to extract JSON-LD
  var jsonLdMatches = html.match(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g) || [];
  jsonLdMatches.forEach(function(match) {
    try {
      var jsonStr = match.replace(/<script[^>]*>/, '').replace(/<\/script>/, '');
      var data = JSON.parse(jsonStr);

      // Person schema
      if (data['@type'] === 'Person') {
        if (data.alumniOf) {
          var alumni = Array.isArray(data.alumniOf) ? data.alumniOf : [data.alumniOf];
          alumni.forEach(function(a) {
            var name = typeof a === 'string' ? a : (a.name || a.legalName || '');
            if (name && result.schools.indexOf(name) === -1) {
              result.schools.push(name);
            }
          });
        }
        if (data.worksFor) {
          var works = Array.isArray(data.worksFor) ? data.worksFor : [data.worksFor];
          works.forEach(function(w) {
            var name = typeof w === 'string' ? w : (w.name || '');
            if (name && result.employers.indexOf(name) === -1) {
              result.employers.push(name);
            }
          });
        }
        if (data.jobTitle) result.headline = data.jobTitle;
        if (data.description) result.summary = data.description;
        if (data.award) {
          var awards = Array.isArray(data.award) ? data.award : [data.award];
          awards.forEach(function(a) {
            if (typeof a === 'string') result.distinctions.push(a);
          });
        }
      }
    } catch(e) { /* skip malformed JSON */ }
  });

  // Parse meta description for additional info
  var descMatch = html.match(/<meta[^>]*name="description"[^>]*content="([^"]*)"/) ||
                  html.match(/<meta[^>]*content="([^"]*)"[^>]*name="description"/);
  if (descMatch) {
    var desc = decodeHtml(descMatch[1]);
    result.metaDesc = desc;

    // Parse "Experience: X, Y · Education: Z" pattern from meta description
    var expPart = desc.match(/Experience:?\s*([^·]+?)(?:\s*·|$)/i);
    if (expPart) {
      var emps = expPart[1].split(/[,;]/).map(function(e) { return e.trim(); }).filter(function(e) {
        return e.length > 1 && e.length < 60;
      });
      emps.forEach(function(e) {
        if (result.employers.indexOf(e) === -1) result.employers.push(e);
      });
    }

    var eduPart = desc.match(/Education:?\s*([^·]+?)(?:\s*·|$)/i);
    if (eduPart) {
      var schools = eduPart[1].split(/[,;]/).map(function(s) { return s.trim(); }).filter(function(s) {
        return s.length > 1 && s.length < 80;
      });
      schools.forEach(function(s) {
        if (result.schools.indexOf(s) === -1) result.schools.push(s);
      });
    }
  }

  // Parse og:description too
  var ogDescMatch = html.match(/<meta[^>]*property="og:description"[^>]*content="([^"]*)"/) ||
                    html.match(/<meta[^>]*content="([^"]*)"[^>]*property="og:description"/);
  if (ogDescMatch) {
    var ogDesc = decodeHtml(ogDescMatch[1]);

    var ogExpPart = ogDesc.match(/Experience:?\s*([^·]+?)(?:\s*·|$)/i);
    if (ogExpPart) {
      ogExpPart[1].split(/[,;]/).map(function(e) { return e.trim(); }).filter(function(e) {
        return e.length > 1 && e.length < 60;
      }).forEach(function(e) {
        if (result.employers.indexOf(e) === -1) result.employers.push(e);
      });
    }

    var ogEduPart = ogDesc.match(/Education:?\s*([^·]+?)(?:\s*·|$)/i);
    if (ogEduPart) {
      ogEduPart[1].split(/[,;]/).map(function(s) { return s.trim(); }).filter(function(s) {
        return s.length > 1 && s.length < 80;
      }).forEach(function(s) {
        if (result.schools.indexOf(s) === -1) result.schools.push(s);
      });
    }
  }

  // Look for distinction keywords in all text
  var fullText = result.summary + ' ' + result.headline + ' ' + (result.metaDesc || '');
  var distinctionPatterns = [
    { pattern: /Forbes\s+30\s*(?:Under|U)\s*30/i, label: 'Forbes 30 Under 30' },
    { pattern: /Thiel\s+Fellow/i, label: 'Thiel Fellow' },
    { pattern: /Rhodes\s+Scholar/i, label: 'Rhodes Scholar' },
    { pattern: /Marshall\s+Scholar/i, label: 'Marshall Scholar' },
    { pattern: /Fulbright/i, label: 'Fulbright Scholar' },
    { pattern: /valedictorian/i, label: 'Valedictorian' },
    { pattern: /summa\s+cum\s+laude/i, label: 'Summa Cum Laude' },
    { pattern: /magna\s+cum\s+laude/i, label: 'Magna Cum Laude' },
    { pattern: /Olympiad/i, label: 'Olympiad' },
    { pattern: /gold\s+medal/i, label: 'Gold Medal' },
    { pattern: /national\s+champion/i, label: 'National Champion' },
    { pattern: /(?:Ph\.?D|PhD|Doctorate)/i, label: 'PhD' },
    { pattern: /(?:patent|patented)/i, label: 'Patent holder' },
    { pattern: /published\s+(?:author|researcher)/i, label: 'Published researcher' },
    { pattern: /ex[- ](?:Google|Meta|Apple|Amazon|Microsoft|Stripe|Uber|Airbnb|SpaceX|Tesla|Goldman|McKinsey)/i, label: null }
  ];

  distinctionPatterns.forEach(function(dp) {
    if (dp.pattern.test(fullText) && dp.label) {
      if (result.distinctions.indexOf(dp.label) === -1) {
        result.distinctions.push(dp.label);
      }
    }
  });

  return result;
}

function sleep(ms) {
  return new Promise(function(r) { setTimeout(r, ms); });
}

async function main() {
  var founders = db.prepare(`
    SELECT f.id, f.name, f.linkedin, f.schools, f.prior_employers, f.awards, c.name as company_name
    FROM founders f
    JOIN companies c ON f.company_id = c.id
    WHERE f.linkedin IS NOT NULL AND f.linkedin != ''
    ORDER BY f.id
  `).all();

  console.log('Enriching ' + founders.length + ' founders from LinkedIn...\n');

  var updateStmt = db.prepare(`
    UPDATE founders SET schools = ?, prior_employers = ?, awards = ? WHERE id = ?
  `);

  var enriched = 0;
  var unchanged = 0;
  var failed = 0;

  for (var i = 0; i < founders.length; i++) {
    var f = founders[i];

    if (i > 0) await sleep(800); // Rate limit

    process.stdout.write('[' + (i + 1) + '/' + founders.length + '] ' + f.name + '... ');

    try {
      var result = await fetchUrl(f.linkedin);

      if (result.status !== 200) {
        console.log('HTTP ' + result.status);
        failed++;
        continue;
      }

      var parsed = parseLinkedInProfile(result.body);

      // Merge with existing data
      var newSchools = parsed.schools.filter(function(s) {
        return s !== 'Y Combinator' && s.indexOf('Y Combinator') === -1;
      });
      var newEmployers = parsed.employers.filter(function(e) {
        return e !== 'Y Combinator' && e.indexOf('Y Combinator') === -1 &&
               e.toLowerCase() !== f.company_name.toLowerCase();
      });
      var newDistinctions = parsed.distinctions;

      // Merge with existing
      if (f.schools) {
        var existing = f.schools.split(/,\s*/);
        newSchools.forEach(function(s) {
          var found = existing.some(function(e) { return e.toLowerCase() === s.toLowerCase(); });
          if (!found) existing.push(s);
        });
        newSchools = existing;
      }

      if (f.prior_employers) {
        var existing = f.prior_employers.split(/,\s*/);
        newEmployers.forEach(function(e) {
          var found = existing.some(function(ex) { return ex.toLowerCase() === e.toLowerCase(); });
          if (!found) existing.push(e);
        });
        newEmployers = existing;
      }

      if (f.awards) {
        var existing = f.awards.split(/,\s*/);
        newDistinctions.forEach(function(d) {
          var found = existing.some(function(ex) { return ex.toLowerCase() === d.toLowerCase(); });
          if (!found) existing.push(d);
        });
        newDistinctions = existing;
      }

      var schoolsStr = newSchools.join(', ');
      var employersStr = newEmployers.join(', ');
      var awardsStr = newDistinctions.join(', ');

      var changed = schoolsStr !== (f.schools || '') ||
                    employersStr !== (f.prior_employers || '') ||
                    awardsStr !== (f.awards || '');

      if (changed) {
        updateStmt.run(schoolsStr || null, employersStr || null, awardsStr || null, f.id);
        var parts = [];
        if (schoolsStr) parts.push('🎓 ' + schoolsStr);
        if (employersStr) parts.push('💼 ' + employersStr);
        if (awardsStr) parts.push('🏆 ' + awardsStr);
        console.log('✅ ' + parts.join(' | '));
        enriched++;
      } else {
        console.log('— no new data');
        unchanged++;
      }

    } catch(e) {
      console.log('❌ ' + e.message);
      failed++;
    }
  }

  console.log('\n============================');
  console.log('Done!');
  console.log('Enriched: ' + enriched);
  console.log('Unchanged: ' + unchanged);
  console.log('Failed: ' + failed);
  console.log('============================');

  // Print updated coverage
  console.log('\nUpdated coverage:');
  console.log('With schools:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE schools IS NOT NULL AND schools != ''").get().c + ' / ' + founders.length);
  console.log('With employers:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE prior_employers IS NOT NULL AND prior_employers != ''").get().c + ' / ' + founders.length);
  console.log('With awards:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE awards IS NOT NULL AND awards != ''").get().c + ' / ' + founders.length);
}

main().catch(console.error);
