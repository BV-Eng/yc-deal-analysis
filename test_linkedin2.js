const https = require('https');
const http = require('http');

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

async function main() {
  // Try Google search for LinkedIn profile info
  const name = 'Devi Jha';
  const query = encodeURIComponent(name + ' linkedin founder');

  // Try DuckDuckGo instead (less blocking)
  console.log('Trying DuckDuckGo search...');
  const ddg = await fetch('https://html.duckduckgo.com/html/?q=' + query);
  console.log('DDG Status:', ddg.status);

  // Extract snippets that mention education/work
  var snippets = ddg.body.match(/class="result__snippet"[^>]*>([\s\S]*?)<\//g) || [];
  snippets.slice(0, 5).forEach(function(s, i) {
    var text = s.replace(/<[^>]*>/g, '').replace(/class="result__snippet"[^>]*>/, '');
    console.log('Snippet ' + (i+1) + ':', text.substring(0, 200));
  });

  // Try the Proxycurl-like approach - just Google the person
  console.log('\n\nTrying Google search...');
  const goog = await fetch('https://www.google.com/search?q=' + query + '&num=3');
  console.log('Google Status:', goog.status);
  if (goog.status === 200) {
    // Extract any visible text about the person
    var textContent = goog.body.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ');
    var relevant = textContent.match(/(?:Harvard|MIT|Stanford|Google|Meta|Facebook|Microsoft|PhD|degree|founded|CEO|CTO)[^.]{0,100}/gi) || [];
    relevant.slice(0, 5).forEach(function(r, i) {
      console.log('Match ' + (i+1) + ':', r.trim());
    });
  }
}

main().catch(console.error);
