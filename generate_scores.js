const path = require('path');
const { getDb, initializeDatabase, importCompanies } = require('./backend/database');
const fs = require('fs');

// ==========================================
// BETTER VENTURES THESIS ALIGNMENT CLASSIFIER
// ==========================================
// Better Ventures invests in: Climate/Sustainability, Human Health, Tomorrow's Workforce
// B2B solutions using AI/ML, software, materials science, biotech
// Must address UN SDGs. Pre-seed/seed. $500K-$1M initial checks.

// Theme 1: BUILD SUSTAINABLE INDUSTRY
// Reducing carbon emissions, waste, pollution. Electrification, food/ag, bioeconomy, circular economy.
const CLIMATE_KEYWORDS = [
  'energy', 'solar', 'battery', 'carbon', 'emission', 'climate', 'sustainable', 'sustainability',
  'renewable', 'clean energy', 'electric vehicle', 'ev ', 'charging', 'grid', 'electrification',
  'decarboniz', 'circular economy', 'recycl', 'waste', 'pollution',
  'agriculture', 'farming', 'farm', 'crop', 'food system', 'food tech',
  'bioeconomy', 'bio-based', 'fermentation', 'biomanufact',
  'water', 'conservation', 'biodiversity', 'reforestation', 'forest',
  'building efficiency', 'hvac', 'insulation', 'green building',
  'supply chain sustainab', 'esg', 'environmental',
  'fish farm', 'aquaculture', 'hatchery',
  'cattle', 'livestock', 'regenerative',
  'materials science', 'textile', 'plastic',
];

const CLIMATE_INDUSTRY_TAGS = [
  'energy', 'climate', 'agriculture', 'renewable energy', 'electric vehicles',
  'clean tech', 'sustainability', 'food tech', 'circular economy',
];

// Theme 2: IMPROVE HUMAN HEALTH
// Bio insights, digital tools. Behavioral health, personalized health, food as medicine, longevity.
const HEALTH_KEYWORDS = [
  'health', 'healthcare', 'medical', 'patient', 'clinical', 'doctor', 'physician',
  'diagnosis', 'diagnostic', 'therapy', 'therapeutic', 'treatment',
  'mental health', 'behavioral health', 'psychiatr', 'psycholog',
  'longevity', 'aging', 'wellness',
  'drug discovery', 'pharmaceutical', 'biopharma', 'biotech',
  'gene therapy', 'cell therapy', 'genomic', 'proteomic',
  'wearable health', 'digital health', 'telehealth', 'telemedicine',
  'primary care', 'care coordination', 'value-based care',
  'biologic', 'autoimmune', 'immun', 'vaccine',
  'food as medicine', 'nutrition', 'personalized care',
  'protein characterization', 'drug development',
  'sleep', 'cardiac', 'dental', 'vision',
  'insurance' // health insurance admin
];

const HEALTH_INDUSTRY_TAGS = [
  'healthcare', 'health tech', 'digital health', 'drug discovery',
  'consumer health', 'biotech', 'biotechnology', 'therapeutics',
  'medical devices', 'clinical',
];

// Theme 3: EQUIP TOMORROW'S WORKFORCE
// Skills, reskilling, workforce augmentation, AI for SMBs, personalized learning.
const WORKFORCE_KEYWORDS = [
  'workforce', 'reskill', 'upskill', 'training', 'learning platform',
  'education', 'edtech', 'tutoring', 'curriculum', 'literacy',
  'hiring', 'recruiting', 'talent', 'human resources', 'hr tech',
  'skills assessment', 'skill matching', 'career',
  'smb', 'small business', 'home service',
  'accessibility', 'inclusion', 'equity',
  'language barrier', 'translation', 'multilingual',
  'underserved', 'emerging market', 'financial inclusion',
  'broadband', 'connectivity',
  'freelance', 'gig economy', 'flexible work',
  'ai for smb', 'operational efficiency for small',
];

const WORKFORCE_INDUSTRY_TAGS = [
  'education', 'edtech', 'human resources', 'hr tech', 'recruiting',
  'workforce', 'learning', 'smb',
];

// OFF-THESIS categories that should be scored low
const OFF_THESIS_KEYWORDS = [
  'gaming', 'game engine', 'grand strategy', 'trading card',
  'crypto', 'cryptocurrency', 'web3', 'nft', 'stablecoin', 'blockchain', 'defi',
  'defense', 'military', 'strike drone', 'weapon', 'hostile drone',
  'space hotel', 'moon hotel', 'space tourism',
  'attention exchange', 'cultural attention',
  'luxury concierge',
];

const OFF_THESIS_INDUSTRIES = [
  'gaming', 'defense', 'cryptocurrency',
];

// ADJACENT / NEUTRAL - not core thesis but could have impact
// These get a middling thesis score
const ADJACENT_KEYWORDS = [
  'developer tool', 'devops', 'infrastructure',
  'legal', 'compliance', 'regulatory',
  'payments', 'fintech', 'accounting', 'finance',
  'security', 'cybersecurity',
  'marketing', 'sales', 'advertising',
  'real estate', 'construction',
  'robotics', 'manufacturing', 'automation',
  'video editor', 'filmmaking',
  'note-taking', 'productivity',
  'semiconductor', 'chip design',
];

function classifyThesisFit(company) {
  const desc = ((company.long_description || '') + ' ' + (company.one_liner || '')).toLowerCase();
  const industries = (company.industries || '').toLowerCase();
  const tags = (company.tags || '').toLowerCase();
  const combined = desc + ' ' + industries + ' ' + tags;

  let climateScore = 0;
  let healthScore = 0;
  let workforceScore = 0;
  let offThesisScore = 0;

  // Check climate keywords
  for (const kw of CLIMATE_KEYWORDS) {
    if (combined.includes(kw)) climateScore += 2;
  }
  for (const tag of CLIMATE_INDUSTRY_TAGS) {
    if (industries.includes(tag) || tags.includes(tag)) climateScore += 3;
  }

  // Check health keywords
  for (const kw of HEALTH_KEYWORDS) {
    if (combined.includes(kw)) healthScore += 2;
  }
  for (const tag of HEALTH_INDUSTRY_TAGS) {
    if (industries.includes(tag) || tags.includes(tag)) healthScore += 3;
  }

  // Check workforce keywords
  for (const kw of WORKFORCE_KEYWORDS) {
    if (combined.includes(kw)) workforceScore += 2;
  }
  for (const tag of WORKFORCE_INDUSTRY_TAGS) {
    if (industries.includes(tag) || tags.includes(tag)) workforceScore += 3;
  }

  // Check off-thesis
  for (const kw of OFF_THESIS_KEYWORDS) {
    if (combined.includes(kw)) offThesisScore += 3;
  }
  for (const tag of OFF_THESIS_INDUSTRIES) {
    if (industries.includes(tag) || tags.includes(tag)) offThesisScore += 4;
  }

  // Determine primary theme
  const maxTheme = Math.max(climateScore, healthScore, workforceScore);
  let theme = 'Off-Thesis';
  let thesisScore = 0;
  let justification = '';

  if (maxTheme >= 4 && offThesisScore < maxTheme) {
    if (climateScore === maxTheme) {
      theme = 'Sustainable Industry';
      thesisScore = Math.min(10, 5 + climateScore * 0.4);
      justification = 'Aligns with Better.vc Sustainable Industry theme.';
    } else if (healthScore === maxTheme) {
      theme = 'Human Health';
      thesisScore = Math.min(10, 5 + healthScore * 0.4);
      justification = 'Aligns with Better.vc Human Health theme.';
    } else {
      theme = "Tomorrow's Workforce";
      thesisScore = Math.min(10, 5 + workforceScore * 0.4);
      justification = "Aligns with Better.vc Tomorrow's Workforce theme.";
    }

    // B2B bonus (Better.vc focuses on B2B)
    if (industries.includes('b2b')) {
      thesisScore = Math.min(10, thesisScore + 0.5);
      justification += ' B2B model aligns with fund focus.';
    }

    // Breakthrough tech bonus (AI/ML, biotech, materials science)
    if (tags.includes('artificial intelligence') || tags.includes('biotech') || tags.includes('biotechnology') ||
        desc.includes('materials science') || desc.includes('machine learning')) {
      thesisScore = Math.min(10, thesisScore + 0.5);
      justification += ' Uses breakthrough technology (AI/biotech/materials).';
    }
  } else if (maxTheme >= 2 && offThesisScore < 4) {
    // Weak alignment
    if (climateScore >= healthScore && climateScore >= workforceScore) {
      theme = 'Sustainable Industry';
    } else if (healthScore >= workforceScore) {
      theme = 'Human Health';
    } else {
      theme = "Tomorrow's Workforce";
    }
    theme += ' (Weak)';
    thesisScore = 3 + maxTheme * 0.3;
    justification = 'Weak alignment with Better.vc thesis. Some relevant keywords but not core focus.';
  } else if (offThesisScore > 0) {
    theme = 'Off-Thesis';
    thesisScore = Math.max(1, 2 - offThesisScore * 0.3);
    justification = 'Does not align with Better.vc investment themes (Climate, Health, Workforce). ' +
      (industries.includes('gaming') ? 'Gaming company. ' : '') +
      (combined.includes('crypto') || combined.includes('web3') ? 'Crypto/Web3 company. ' : '') +
      (industries.includes('defense') ? 'Defense company. ' : '') +
      'Consider passing unless thesis evolves.';
  } else {
    // Neutral / unclear
    theme = 'Neutral';
    thesisScore = 2.5;
    justification = 'No clear alignment with Better.vc investment themes. Generic B2B/tech company without clear impact angle on climate, health, or workforce.';

    // Check if it has any adjacent value
    let adjacentHits = 0;
    for (const kw of ADJACENT_KEYWORDS) {
      if (combined.includes(kw)) adjacentHits++;
    }
    if (adjacentHits > 0) {
      thesisScore = Math.min(4, 2.5 + adjacentHits * 0.2);
      justification = 'Adjacent to thesis but no direct climate/health/workforce impact. ' +
        'Could potentially serve impact sectors but not core thesis fit.';
    }
  }

  return {
    theme,
    score: Math.round(thesisScore * 2) / 2, // round to nearest 0.5
    justification
  };
}

// Heuristic scoring based on available data - THESIS ALIGNED
function scoreCompany(company) {
  const scores = {};
  const founders = company.founders || [];
  const desc = ((company.long_description || '') + ' ' + (company.one_liner || '')).toLowerCase();
  const industries = (company.industries || '').toLowerCase();
  const tags = (company.tags || '').toLowerCase();

  // ==============================
  // THESIS FIT (Weight: 25% - highest single weight)
  // ==============================
  const thesisFit = classifyThesisFit(company);
  scores.thesis_fit_score = thesisFit.score;
  scores.thesis_fit_weight = 25;
  scores.thesis_fit_justification = thesisFit.justification;
  scores.thesis_fit_theme = thesisFit.theme;

  // ---- TEAM SCORE (Weight: 15%) ----
  let teamScore = 5;
  if (founders.length >= 2) teamScore += 1;
  if (founders.length >= 3) teamScore += 0.5;
  const hasTechKeywords = founders.some(f =>
    (f.title || '').toLowerCase().match(/cto|engineer|technical|tech/));
  if (hasTechKeywords) teamScore += 1;
  const hasBusinessKeywords = founders.some(f =>
    (f.title || '').toLowerCase().match(/ceo|business|operations|growth|sales/));
  if (hasBusinessKeywords) teamScore += 0.5;
  if (founders.some(f => f.is_female)) teamScore += 0.5;
  if (founders.some(f => f.is_black || f.is_hispanic_latino)) teamScore += 0.5;

  // Thesis-aligned team bonus: domain expertise matters more
  if (thesisFit.theme.includes('Health') && founders.some(f => {
    const t = (f.title || '').toLowerCase();
    return t.includes('md') || t.includes('doctor') || t.includes('clinical') || t.includes('bio');
  })) teamScore += 1;
  if (thesisFit.theme.includes('Sustainable') && founders.some(f => {
    const t = (f.title || '').toLowerCase();
    return t.includes('energy') || t.includes('climate') || t.includes('environment');
  })) teamScore += 1;

  scores.team_score = Math.min(10, Math.max(1, teamScore));
  scores.team_weight = 15;
  scores.team_justification = `Team of ${founders.length} founder(s): ${founders.map(f => `${f.name} (${f.title})`).join(', ')}. ${hasTechKeywords ? 'Has technical co-founder. ' : ''}${hasBusinessKeywords ? 'Has business-focused founder. ' : ''}${founders.some(f => f.is_female) ? 'Diverse founding team. ' : ''}`;

  // ---- PRODUCT SCORE (Weight: 10%) ----
  let productScore = 5;
  if (tags.includes('artificial intelligence') || desc.includes('ai')) productScore += 0.5;
  if (desc.includes('first') || desc.includes('novel') || desc.includes('breakthrough')) productScore += 0.5;
  if (desc.includes('platform') || desc.includes('infrastructure')) productScore += 0.5;
  if (desc.includes('open-source') || desc.includes('open source')) productScore += 0.5;
  if (industries.includes('hardware') || desc.includes('robot') || desc.includes('hardware')) productScore += 0.5;
  // Thesis bonus: deeper tech moat in impact areas
  if (thesisFit.score >= 6 && (tags.includes('biotech') || desc.includes('materials science') ||
      desc.includes('proprietary') || desc.includes('patent'))) productScore += 1;
  scores.product_score = Math.min(10, Math.max(1, productScore));
  scores.product_weight = 10;
  scores.product_justification = `${company.one_liner}. ${tags.includes('artificial intelligence') ? 'AI/ML technology. ' : ''}Industry: ${company.industries || 'Unknown'}.`;

  // ---- BUSINESS MODEL SCORE (Weight: 10%) ----
  let bmScore = 5;
  if (industries.includes('b2b')) bmScore += 1;
  if (desc.includes('saas') || desc.includes('subscription') || desc.includes('platform')) bmScore += 0.5;
  if (desc.includes('enterprise')) bmScore += 0.5;
  // Better.vc likes B2B - penalize pure consumer
  if (industries.includes('consumer') && !industries.includes('b2b')) bmScore -= 0.5;
  scores.business_model_score = Math.min(10, Math.max(1, bmScore));
  scores.business_model_weight = 10;
  scores.business_model_justification = `${industries.includes('b2b') ? 'B2B model (aligns with fund focus). ' : ''}${industries.includes('consumer') ? 'Consumer model. ' : ''}${desc.includes('enterprise') ? 'Enterprise focus. ' : ''}`;

  // ---- MARKET SCORE (Weight: 10%) ----
  let marketScore = 5;
  if (desc.includes('billion') || desc.includes('trillion') || desc.includes('massive')) marketScore += 1;
  // Thesis-aligned markets get a bump
  if (thesisFit.score >= 6) {
    marketScore += 1; // On-thesis markets are large by definition
    if (industries.includes('healthcare')) marketScore += 0.5;
    if (industries.includes('energy')) marketScore += 0.5;
  }
  if (desc.includes('global') || desc.includes('worldwide')) marketScore += 0.5;
  scores.market_score = Math.min(10, Math.max(1, marketScore));
  scores.market_weight = 10;
  scores.market_justification = `Operating in ${company.industries || 'undisclosed'} market. ${thesisFit.score >= 6 ? 'Thesis-aligned market with strong tailwinds. ' : ''}`;

  // ---- IMPACT SCORE (Weight: 20% - second highest) ----
  let impactScore = 3; // Start lower - impact must be earned
  if (desc.includes('impact') || desc.includes('sustainable') || desc.includes('social')) impactScore += 2;
  if (desc.includes('health') || desc.includes('medical') || desc.includes('patient') || desc.includes('care')) impactScore += 2;
  if (desc.includes('energy') || desc.includes('climate') || desc.includes('carbon') || desc.includes('solar')) impactScore += 2;
  if (desc.includes('education') || desc.includes('learn')) impactScore += 1.5;
  if (desc.includes('agriculture') || desc.includes('food') || desc.includes('farm')) impactScore += 1.5;
  if (desc.includes('accessibility') || desc.includes('underserved') || desc.includes('inclusion')) impactScore += 1;
  if (desc.includes('language barrier') || desc.includes('multilingual')) impactScore += 1;
  // Penalize things with no impact angle
  if (impactScore <= 3 && (desc.includes('developer tool') || desc.includes('devops') ||
      desc.includes('marketing') || desc.includes('sales enablement'))) impactScore = 2;
  scores.impact_score = Math.min(10, Math.max(1, impactScore));
  scores.impact_weight = 20;
  scores.impact_justification = `${desc.includes('health') ? 'Healthcare impact. ' : ''}${desc.includes('energy') || desc.includes('climate') ? 'Climate/energy impact. ' : ''}${desc.includes('education') || desc.includes('learn') ? 'Education impact. ' : ''}${desc.includes('agriculture') || desc.includes('food') ? 'Agriculture/food impact. ' : ''}${impactScore <= 3 ? 'Limited measurable impact on Better.vc SDG alignment. ' : ''}`;

  // ---- TRACTION SCORE (Weight: 5%) ----
  let tractionScore = 4;
  if (company.team_size > 5) tractionScore += 1;
  if (company.team_size > 10) tractionScore += 1;
  if (company.website) tractionScore += 0.5;
  if (desc.includes('customer') || desc.includes('user') || desc.includes('client')) tractionScore += 0.5;
  if (desc.includes('revenue') || desc.includes('paying')) tractionScore += 1;
  scores.traction_score = Math.min(10, Math.max(1, tractionScore));
  scores.traction_weight = 5;
  scores.traction_justification = `Team size: ${company.team_size || 'Unknown'}. ${company.website ? 'Has website. ' : ''}YC W26 batch acceptance signals validation.`;

  // ---- DEAL SCORE (Weight: 5%) ----
  let dealScore = 6; // YC companies get baseline
  if ((company.all_locations || '').includes('San Francisco') || (company.all_locations || '').includes('New York')) dealScore += 0.5;
  scores.deal_score = Math.min(10, Math.max(1, dealScore));
  scores.deal_weight = 5;
  scores.deal_justification = `YC W26 batch company. Location: ${company.all_locations || 'Undisclosed'}. Standard YC deal terms.`;

  // Calculate weighted total
  // New weights: Thesis Fit 25%, Impact 20%, Team 15%, Product 10%, Business Model 10%, Market 10%, Traction 5%, Deal 5%
  const categories = ['thesis_fit', 'team', 'product', 'business_model', 'market', 'impact', 'traction', 'deal'];
  let totalWeight = 0, weightedSum = 0;
  for (const cat of categories) {
    totalWeight += scores[`${cat}_weight`];
    weightedSum += scores[`${cat}_score`] * scores[`${cat}_weight`];
  }
  scores.weighted_total = totalWeight > 0 ? Math.round((weightedSum / totalWeight) * 100) / 100 : 0;

  return scores;
}

function main() {
  console.log('Initializing database...');
  initializeDatabase();

  // Import company data
  const dataPath = path.join(__dirname, 'data', 'yc_w26_companies.json');
  if (!fs.existsSync(dataPath)) {
    console.error('No company data found. Run scrape_yc.js first.');
    process.exit(1);
  }

  const db = getDb();
  const count = db.prepare('SELECT COUNT(*) as count FROM companies').get().count;

  if (count === 0) {
    console.log('Importing company data...');
    db.close();
    importCompanies(fs.readFileSync(dataPath, 'utf-8'));
  } else {
    console.log(`Database already has ${count} companies`);
    db.close();
  }

  // Generate scores
  const db2 = getDb();
  const companies = db2.prepare(`
    SELECT c.*, GROUP_CONCAT(f.name || '|' || COALESCE(f.title,'') || '|' || f.is_female || '|' || f.is_black || '|' || f.is_hispanic_latino, ';;;') as founder_data
    FROM companies c
    LEFT JOIN founders f ON f.company_id = c.id
    GROUP BY c.id
  `).all();

  console.log(`Generating thesis-aligned scores for ${companies.length} companies...`);

  const updateScore = db2.prepare(`
    UPDATE company_scores SET
      thesis_fit_score = @thesis_fit_score, thesis_fit_weight = @thesis_fit_weight,
      thesis_fit_justification = @thesis_fit_justification, thesis_fit_theme = @thesis_fit_theme,
      team_score = @team_score, team_weight = @team_weight, team_justification = @team_justification,
      product_score = @product_score, product_weight = @product_weight, product_justification = @product_justification,
      business_model_score = @business_model_score, business_model_weight = @business_model_weight, business_model_justification = @business_model_justification,
      market_score = @market_score, market_weight = @market_weight, market_justification = @market_justification,
      impact_score = @impact_score, impact_weight = @impact_weight, impact_justification = @impact_justification,
      traction_score = @traction_score, traction_weight = @traction_weight, traction_justification = @traction_justification,
      deal_score = @deal_score, deal_weight = @deal_weight, deal_justification = @deal_justification,
      weighted_total = @weighted_total,
      updated_at = CURRENT_TIMESTAMP
    WHERE company_id = @company_id
  `);

  const updateCompanyTheme = db2.prepare(`UPDATE companies SET thesis_fit_theme = ? WHERE id = ?`);

  // Theme summary
  const themeCounts = { 'Sustainable Industry': 0, 'Human Health': 0, "Tomorrow's Workforce": 0, 'Off-Thesis': 0, 'Neutral': 0 };

  const transaction = db2.transaction(() => {
    for (const company of companies) {
      // Parse founder data
      const founders = (company.founder_data || '').split(';;;').filter(Boolean).map(fd => {
        const parts = fd.split('|');
        return {
          name: parts[0] || '',
          title: parts[1] || '',
          is_female: parts[2] === '1',
          is_black: parts[3] === '1',
          is_hispanic_latino: parts[4] === '1'
        };
      });

      company.founders = founders;
      const scores = scoreCompany(company);

      updateScore.run({
        ...scores,
        company_id: company.id
      });

      // Update company theme
      updateCompanyTheme.run(scores.thesis_fit_theme, company.id);

      // Track theme counts
      const baseTheme = scores.thesis_fit_theme.replace(' (Weak)', '');
      if (themeCounts[baseTheme] !== undefined) themeCounts[baseTheme]++;
      else if (scores.thesis_fit_theme.includes('Weak')) themeCounts[baseTheme.replace(' (Weak)', '')] = (themeCounts[baseTheme.replace(' (Weak)', '')] || 0) + 1;
    }
  });

  transaction();

  // Summary
  const avgScore = db2.prepare('SELECT AVG(weighted_total) as avg FROM company_scores WHERE weighted_total > 0').get();

  console.log(`\n${'='.repeat(60)}`);
  console.log('THESIS-ALIGNED SCORING COMPLETE');
  console.log(`${'='.repeat(60)}`);
  console.log(`Average weighted score: ${(avgScore.avg || 0).toFixed(2)}`);

  // Theme distribution
  console.log('\n--- THESIS ALIGNMENT DISTRIBUTION ---');
  const themeStats = db2.prepare(`
    SELECT cs.thesis_fit_theme, COUNT(*) as count, AVG(cs.weighted_total) as avg_score
    FROM company_scores cs
    GROUP BY cs.thesis_fit_theme
    ORDER BY avg_score DESC
  `).all();
  themeStats.forEach(t => {
    console.log(`  ${t.thesis_fit_theme}: ${t.count} companies (avg score: ${(t.avg_score || 0).toFixed(2)})`);
  });

  // Top companies overall
  const topCompanies = db2.prepare(`
    SELECT c.name, c.one_liner, cs.weighted_total, cs.thesis_fit_score, cs.thesis_fit_theme, cs.impact_score
    FROM companies c
    JOIN company_scores cs ON cs.company_id = c.id
    ORDER BY cs.weighted_total DESC
    LIMIT 20
  `).all();

  console.log('\n--- TOP 20 COMPANIES (THESIS-ALIGNED) ---');
  topCompanies.forEach((c, i) => {
    console.log(`  ${i+1}. ${c.name} (${c.weighted_total.toFixed(2)}) [${c.thesis_fit_theme}] Thesis:${c.thesis_fit_score} Impact:${c.impact_score}`);
    console.log(`     ${c.one_liner}`);
  });

  // Bottom companies (off-thesis)
  const bottomCompanies = db2.prepare(`
    SELECT c.name, cs.weighted_total, cs.thesis_fit_score, cs.thesis_fit_theme
    FROM companies c
    JOIN company_scores cs ON cs.company_id = c.id
    WHERE cs.thesis_fit_theme IN ('Off-Thesis', 'Neutral')
    ORDER BY cs.weighted_total ASC
    LIMIT 15
  `).all();

  console.log('\n--- LOWEST RANKED (OFF-THESIS) ---');
  bottomCompanies.forEach((c, i) => {
    console.log(`  ${i+1}. ${c.name} (${c.weighted_total.toFixed(2)}) [${c.thesis_fit_theme}] Thesis:${c.thesis_fit_score}`);
  });

  db2.close();
}

main();
