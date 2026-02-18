const https = require('https');

function fetchProfile(url) {
  return new Promise(function(resolve, reject) {
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9'
      }
    };

    https.get(url, options, function(res) {
      // Follow redirects
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetchProfile(res.headers.location).then(resolve).catch(reject);
      }
      let data = '';
      res.on('data', function(chunk) { data += chunk; });
      res.on('end', function() { resolve({ status: res.statusCode, body: data }); });
    }).on('error', reject);
  });
}

async function main() {
  const result = await fetchProfile('https://linkedin.com/in/devishijha');
  console.log('Status:', result.status);
  console.log('Body length:', result.body.length);

  // Look for JSON-LD structured data
  var jsonLdMatch = result.body.match(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/);
  if (jsonLdMatch) {
    try {
      var parsed = JSON.parse(jsonLdMatch[1]);
      console.log('\nJSON-LD data:');
      console.log(JSON.stringify(parsed, null, 2).substring(0, 2000));
    } catch(e) {
      console.log('JSON-LD (raw):', jsonLdMatch[1].substring(0, 1000));
    }
  } else {
    console.log('No JSON-LD found');
  }

  // Look for useful meta tags
  var metas = result.body.match(/<meta[^>]*>/g) || [];
  metas.forEach(function(m) {
    if (m.indexOf('description') > -1 || m.indexOf('og:title') > -1) {
      console.log('Meta:', m.substring(0, 300));
    }
  });

  // Check if we're getting auth wall
  if (result.body.indexOf('authwall') > -1 || result.body.indexOf('sign in') > -1) {
    console.log('\n⚠️  LinkedIn auth wall detected - public scraping blocked');
  }
}

main().catch(console.error);
