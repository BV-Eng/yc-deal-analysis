const db = require('better-sqlite3')('data/yc_deals.db');

var founders = db.prepare("SELECT id, name, schools, prior_employers, awards FROM founders WHERE schools IS NOT NULL OR prior_employers IS NOT NULL OR awards IS NOT NULL").all();
var cleanStmt = db.prepare('UPDATE founders SET schools = ?, prior_employers = ?, awards = ? WHERE id = ?');
var fixed = 0;

function dedup(arr) {
  var result = [];
  arr.forEach(function(item) {
    var dominated = result.some(function(r) { return r.indexOf(item) > -1; });
    if (!dominated) {
      // Check if this item contains an existing shorter one
      var newResult = [];
      var replaced = false;
      result.forEach(function(r) {
        if (item.indexOf(r) > -1 && item !== r) {
          if (!replaced) {
            newResult.push(item);
            replaced = true;
          }
        } else {
          newResult.push(r);
        }
      });
      if (!replaced) newResult.push(item);
      result = newResult;
    }
  });
  return result;
}

founders.forEach(function(f) {
  var schools = f.schools || '';
  var employers = f.prior_employers || '';
  var awards = f.awards || '';
  var origSchools = schools;
  var origEmployers = employers;
  var origAwards = awards;

  // Remove degree artifacts from schools
  schools = schools.replace(/,\s*CS\)\s*and\s*ZFellow\s*\(degree\)/g, '');
  schools = schools.replace(/,\s*[A-Za-z\s/.()→|&]*\(degree\)/g, '');
  schools = schools.replace(/\s*\(degree\)/g, '');
  // Remove any remaining parenthetical degree info
  schools = schools.replace(/,\s*Statistics & Data Science \| Prev/g, '');
  schools = schools.replace(/,\s*ECE from [^,]*/g, '');
  schools = schools.replace(/,\s*CS \/ Co-Founder[^,]*/g, '');
  schools = schools.replace(/,\s*CS \(Automated[^,)]*/g, '');
  schools = schools.replace(/,\s*Physics from[^,]*/g, '');
  schools = schools.replace(/,\s*Computer Vision[^,]*/g, '');
  schools = schools.replace(/,\s*EE \(MIT[^,)]*/g, '');
  schools = schools.replace(/,\s*Biology from[^,]*/g, '');
  schools = schools.replace(/,\s*Computer Science from[^,]*/g, '');
  schools = schools.replace(/,\s*Formal Methods[^,]*/g, '');
  schools = schools.replace(/,\s*Millimetre-Wave[^,]*/g, '');

  // Dedup schools
  var schoolArr = schools.split(/,\s*/).filter(function(s) { return s.length > 1; });
  schoolArr = dedup(schoolArr);

  // Remove generic if specific exists
  if (schoolArr.some(function(s) { return /IIT (Bombay|Delhi|Madras|Kanpur|Kharagpur)/.test(s); })) {
    schoolArr = schoolArr.filter(function(s) { return s !== 'IIT'; });
  }
  if (schoolArr.indexOf('Imperial College') > -1) {
    schoolArr = schoolArr.filter(function(s) { return s !== 'Imperial'; });
  }
  if (schoolArr.indexOf('MIT') > -1) {
    schoolArr = schoolArr.filter(function(s) { return s !== 'Sloan' && s !== 'MIT Sloan'; });
  }
  // UC Berkeley dedup
  if (schoolArr.indexOf('UC Berkeley') > -1) {
    schoolArr = schoolArr.filter(function(s) { return s !== 'Berkeley'; });
  } else if (schoolArr.indexOf('Berkeley') > -1 && !schoolArr.some(function(s) { return s === 'UC Berkeley'; })) {
    schoolArr = schoolArr.map(function(s) { return s === 'Berkeley' ? 'UC Berkeley' : s; });
  }

  schools = Array.from(new Set(schoolArr)).join(', ');

  // Dedup employers
  var empArr = employers.split(/,\s*/).filter(function(e) { return e.length > 1; });
  empArr = dedup(empArr);
  if (empArr.indexOf('McKinsey & Company') > -1) {
    empArr = empArr.filter(function(e) { return e !== 'McKinsey'; });
  }
  if (empArr.indexOf('Bain & Company') > -1) {
    empArr = empArr.filter(function(e) { return e !== 'Bain'; });
  }
  // Remove AWS if Amazon also present
  if (empArr.indexOf('Amazon') > -1 && empArr.indexOf('AWS') > -1) {
    empArr = empArr.filter(function(e) { return e !== 'AWS'; });
  }
  employers = Array.from(new Set(empArr)).join(', ');

  // Dedup awards
  var awardArr = awards.split(/,\s*/).filter(function(a) { return a.length > 1; });
  // Remove 'gold medal' if 'Gold Medalist' present
  if (awardArr.indexOf('Gold Medalist') > -1) {
    awardArr = awardArr.filter(function(a) { return a !== 'gold medal'; });
  }
  awards = Array.from(new Set(awardArr)).join(', ');

  if (schools !== origSchools || employers !== origEmployers || awards !== origAwards) {
    cleanStmt.run(schools || null, employers || null, awards || null, f.id);
    fixed++;
  }
});

console.log('Cleaned up ' + fixed + ' founder records');

console.log('\nFinal coverage:');
console.log('With schools:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE schools IS NOT NULL AND schools != ''").get().c + ' / 326');
console.log('With employers:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE prior_employers IS NOT NULL AND prior_employers != ''").get().c + ' / 326');
console.log('With distinctions:', db.prepare("SELECT COUNT(*) as c FROM founders WHERE awards IS NOT NULL AND awards != ''").get().c + ' / 326');

// Show some cleaned samples
console.log('\n--- Notable founders ---');
var notable = db.prepare("SELECT name, schools, prior_employers, awards FROM founders WHERE awards IS NOT NULL AND awards != '' ORDER BY length(awards) DESC LIMIT 20").all();
notable.forEach(function(s) {
  console.log(s.name + ':');
  if (s.schools) console.log('  🎓 ' + s.schools);
  if (s.prior_employers) console.log('  💼 ' + s.prior_employers);
  console.log('  🏆 ' + s.awards);
});
