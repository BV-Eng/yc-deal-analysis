// Database layer using Upstash Redis with JSON file fallback
const fs = require('fs');
const path = require('path');

// Redis client (lazy loaded)
let redis = null;

function getRedis() {
  if (redis) return redis;

  // Check for Vercel KV environment variables
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

  if (url && token) {
    const { Redis } = require('@upstash/redis');
    redis = new Redis({ url, token });
    console.log('Using Upstash Redis for storage');
    return redis;
  }

  console.log('No Redis credentials found, using local JSON storage');
  return null;
}

const DATA_KEY = 'yc-deals:data';
const SEED_FILE = path.join(__dirname, '..', 'data', 'seed-data.json');
const LOCAL_FILE = path.join(__dirname, '..', 'data', 'local-data.json');

// Load seed data
function loadSeedData() {
  if (fs.existsSync(SEED_FILE)) {
    return JSON.parse(fs.readFileSync(SEED_FILE, 'utf-8'));
  }
  return {
    companies: [],
    settings: { company_score_weight: '50', founder_score_weight: '50' },
    nextIds: { company: 1, founder: 1, interaction: 1, note: 1 }
  };
}

// Get all data
async function getData() {
  const r = getRedis();

  if (r) {
    try {
      const data = await r.get(DATA_KEY);
      if (data) {
        return typeof data === 'string' ? JSON.parse(data) : data;
      }
      // Initialize from seed data
      const seed = loadSeedData();
      await r.set(DATA_KEY, JSON.stringify(seed));
      return seed;
    } catch (e) {
      console.error('Redis error, falling back to local:', e.message);
    }
  }

  // Local file fallback
  if (fs.existsSync(LOCAL_FILE)) {
    return JSON.parse(fs.readFileSync(LOCAL_FILE, 'utf-8'));
  }

  // Initialize from seed
  const seed = loadSeedData();
  fs.writeFileSync(LOCAL_FILE, JSON.stringify(seed, null, 2));
  return seed;
}

// Save all data
async function saveData(data) {
  const r = getRedis();

  if (r) {
    try {
      await r.set(DATA_KEY, JSON.stringify(data));
      return;
    } catch (e) {
      console.error('Redis error, falling back to local:', e.message);
    }
  }

  // Local file fallback
  fs.writeFileSync(LOCAL_FILE, JSON.stringify(data, null, 2));
}

// ==========================================
// COMPANIES
// ==========================================

async function getCompanies(filters = {}) {
  const data = await getData();

  // Get scoring weights from settings
  const companyWeight = parseFloat(data.settings?.company_score_weight || 50) / 100;
  const founderWeight = parseFloat(data.settings?.founder_score_weight || 50) / 100;

  let companies = data.companies.map(c => {
    const avg_founder_score = c.founders?.length > 0
      ? c.founders.reduce((sum, f) => sum + (f.founder_score || 0), 0) / c.founders.length
      : 0;

    // Calculate weighted total score combining company and founder scores
    const weighted_total = (c.company_score || 0) * companyWeight + avg_founder_score * founderWeight;

    return {
      ...c,
      founder_names: c.founders?.map(f => f.name).join(', ') || '',
      founder_linkedin_data: c.founders?.map(f => `${f.name}::${f.linkedin || ''}::${f.email || ''}`).join('|||') || '',
      has_female_founder: c.founders?.some(f => f.is_female) ? 1 : 0,
      has_black_founder: c.founders?.some(f => f.is_black) ? 1 : 0,
      has_hispanic_founder: c.founders?.some(f => f.is_hispanic_latino) ? 1 : 0,
      last_interaction_date: c.interactions?.[0]?.date || null,
      avg_founder_score,
      weighted_total: Math.round(weighted_total * 100) / 100
    };
  });

  // Apply filters
  const { status, industry, location, search, diversity, theme, owner: ownerFilter, tag, source } = filters;

  if (source) {
    companies = companies.filter(c => c.source === source);
  }
  if (status) {
    companies = companies.filter(c => c.status === status);
  }
  if (industry) {
    companies = companies.filter(c => c.industries?.toLowerCase().includes(industry.toLowerCase()));
  }
  if (location) {
    companies = companies.filter(c => c.all_locations?.toLowerCase().includes(location.toLowerCase()));
  }
  if (search) {
    const s = search.toLowerCase();
    companies = companies.filter(c =>
      c.name?.toLowerCase().includes(s) ||
      c.one_liner?.toLowerCase().includes(s) ||
      c.long_description?.toLowerCase().includes(s) ||
      c.founder_names?.toLowerCase().includes(s)
    );
  }
  if (tag) {
    companies = companies.filter(c =>
      c.tags?.toLowerCase().includes(tag.toLowerCase()) ||
      c.custom_tags?.toLowerCase().includes(tag.toLowerCase())
    );
  }
  if (diversity === 'female') {
    companies = companies.filter(c => c.has_female_founder);
  }
  if (diversity === 'bipoc') {
    companies = companies.filter(c => c.has_black_founder || c.has_hispanic_founder);
  }
  if (theme) {
    if (theme === 'on-thesis') {
      companies = companies.filter(c => c.thesis_fit_theme && !['Off-Thesis', 'Neutral'].includes(c.thesis_fit_theme));
    } else if (theme === 'off-thesis') {
      companies = companies.filter(c => !c.thesis_fit_theme || ['Off-Thesis', 'Neutral'].includes(c.thesis_fit_theme));
    } else {
      companies = companies.filter(c => c.thesis_fit_theme?.toLowerCase().includes(theme.toLowerCase()));
    }
  }
  if (ownerFilter) {
    if (ownerFilter === 'unassigned') {
      companies = companies.filter(c => !c.owner);
    } else {
      companies = companies.filter(c => c.owner === ownerFilter);
    }
  }

  // Sort - default to weighted_total which combines company + founder scores
  const { sort = 'weighted_total', order = 'DESC' } = filters;
  companies.sort((a, b) => {
    const aVal = a[sort] ?? 0;
    const bVal = b[sort] ?? 0;
    if (typeof aVal === 'string') {
      return order === 'ASC' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return order === 'ASC' ? aVal - bVal : bVal - aVal;
  });

  return companies;
}

async function getCompanyById(id) {
  const data = await getData();
  const company = data.companies.find(c => c.id === parseInt(id));
  if (!company) return null;

  return {
    company: { ...company },
    founders: company.founders || [],
    interactions: company.interactions || [],
    notes: company.notes || []
  };
}

async function updateCompany(id, updates) {
  const data = await getData();
  const idx = data.companies.findIndex(c => c.id === parseInt(id));
  if (idx === -1) return false;

  const { status, next_action, custom_tags, b2b_b2c, technology_type, business_model, owner, contact_email } = updates;
  const company = data.companies[idx];

  if (status !== undefined) company.status = status;
  if (next_action !== undefined) company.next_action = next_action;
  if (custom_tags !== undefined) company.custom_tags = custom_tags;
  if (b2b_b2c !== undefined) company.b2b_b2c = b2b_b2c;
  if (technology_type !== undefined) company.technology_type = technology_type;
  if (business_model !== undefined) company.business_model = business_model;
  if (owner !== undefined) company.owner = owner;
  if (contact_email !== undefined) company.contact_email = contact_email;
  company.updated_at = new Date().toISOString();

  await saveData(data);
  return true;
}

async function bulkUpdateStatus(companyIds, status) {
  const data = await getData();
  let updated = 0;

  for (const id of companyIds) {
    const company = data.companies.find(c => c.id === parseInt(id));
    if (company) {
      company.status = status;
      company.updated_at = new Date().toISOString();
      updated++;
    }
  }

  await saveData(data);
  return updated;
}

// ==========================================
// COMPANY SCORES
// ==========================================

async function updateCompanyScores(companyId, scores) {
  const data = await getData();
  const company = data.companies.find(c => c.id === parseInt(companyId));
  if (!company) return null;

  // Update score fields
  const scoreFields = [
    'thesis_fit_score', 'thesis_fit_weight', 'thesis_fit_justification', 'thesis_fit_theme',
    'team_score', 'team_weight', 'team_justification',
    'product_score', 'product_weight', 'product_justification',
    'business_model_score', 'business_model_weight', 'business_model_justification',
    'market_score', 'market_weight', 'market_justification',
    'impact_score', 'impact_weight', 'impact_justification',
    'traction_score', 'traction_weight', 'traction_justification',
    'deal_score', 'deal_weight', 'deal_justification'
  ];

  for (const field of scoreFields) {
    if (scores[field] !== undefined) {
      company[field] = scores[field];
    }
  }

  // Calculate weighted total
  const categories = ['thesis_fit', 'team', 'product', 'business_model', 'market', 'impact', 'traction', 'deal'];
  let totalWeight = 0;
  let weightedSum = 0;
  for (const cat of categories) {
    const score = company[`${cat}_score`] || 0;
    const weight = company[`${cat}_weight`] || 0;
    totalWeight += weight;
    weightedSum += score * weight;
  }
  company.company_score = totalWeight > 0 ? weightedSum / totalWeight : 0;
  company.updated_at = new Date().toISOString();

  await saveData(data);
  return company.company_score;
}

// ==========================================
// FOUNDERS
// ==========================================

async function updateFounder(founderId, updates) {
  const data = await getData();

  for (const company of data.companies) {
    const founder = company.founders?.find(f => f.id === parseInt(founderId));
    if (founder) {
      const fields = ['schools', 'degrees', 'prior_employers', 'technical_competence',
        'publications_count', 'citations_count', 'awards', 'patents',
        'is_repeat_founder', 'is_colocated', 'age_range', 'email', 'email_confidence'];
      for (const field of fields) {
        if (updates[field] !== undefined) {
          founder[field] = updates[field];
        }
      }
      await saveData(data);
      return true;
    }
  }
  return false;
}

async function updateFounderScores(founderId, scores) {
  const data = await getData();

  for (const company of data.companies) {
    const founder = company.founders?.find(f => f.id === parseInt(founderId));
    if (founder) {
      const categories = ['breakthrough', 'mission', 'achievements', 'work_ethic',
        'grit', 'magnetism', 'curiosity', 'coachability', 'team_chemistry'];

      let sum = 0;
      let count = 0;
      for (const cat of categories) {
        if (scores[`${cat}_score`] !== undefined) {
          founder[`${cat}_score`] = scores[`${cat}_score`];
        }
        if (scores[`${cat}_justification`] !== undefined) {
          founder[`${cat}_justification`] = scores[`${cat}_justification`];
        }
        const score = founder[`${cat}_score`] || 0;
        if (score > 0) {
          sum += score;
          count++;
        }
      }
      founder.founder_score = count > 0 ? sum / count : 0;

      await saveData(data);
      return founder.founder_score;
    }
  }
  return null;
}

// ==========================================
// INTERACTIONS
// ==========================================

async function addInteraction(companyId, interaction) {
  const data = await getData();
  const company = data.companies.find(c => c.id === parseInt(companyId));
  if (!company) return null;

  if (!company.interactions) company.interactions = [];

  const newId = data.nextIds.interaction++;
  const newInteraction = {
    id: newId,
    company_id: parseInt(companyId),
    ...interaction,
    created_at: new Date().toISOString()
  };
  company.interactions.unshift(newInteraction);

  await saveData(data);
  return newId;
}

async function deleteInteraction(interactionId) {
  const data = await getData();

  for (const company of data.companies) {
    const idx = company.interactions?.findIndex(i => i.id === parseInt(interactionId));
    if (idx !== undefined && idx !== -1) {
      company.interactions.splice(idx, 1);
      await saveData(data);
      return true;
    }
  }
  return false;
}

// ==========================================
// NOTES
// ==========================================

async function addNote(companyId, content) {
  const data = await getData();
  const company = data.companies.find(c => c.id === parseInt(companyId));
  if (!company) return null;

  if (!company.notes) company.notes = [];

  const newId = data.nextIds.note++;
  const newNote = {
    id: newId,
    company_id: parseInt(companyId),
    content,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  company.notes.unshift(newNote);

  await saveData(data);
  return newId;
}

async function updateNote(noteId, content) {
  const data = await getData();

  for (const company of data.companies) {
    const note = company.notes?.find(n => n.id === parseInt(noteId));
    if (note) {
      note.content = content;
      note.updated_at = new Date().toISOString();
      await saveData(data);
      return true;
    }
  }
  return false;
}

async function deleteNote(noteId) {
  const data = await getData();

  for (const company of data.companies) {
    const idx = company.notes?.findIndex(n => n.id === parseInt(noteId));
    if (idx !== undefined && idx !== -1) {
      company.notes.splice(idx, 1);
      await saveData(data);
      return true;
    }
  }
  return false;
}

// ==========================================
// SETTINGS
// ==========================================

async function getSettings() {
  const data = await getData();
  return data.settings || {};
}

async function updateSettings(updates) {
  const data = await getData();
  data.settings = { ...data.settings, ...updates };
  await saveData(data);
  return true;
}

// ==========================================
// ANALYTICS
// ==========================================

async function getAnalytics() {
  const data = await getData();
  const companies = data.companies;

  // Status counts
  const statusCounts = {};
  companies.forEach(c => {
    statusCounts[c.status || 'Not Contacted'] = (statusCounts[c.status || 'Not Contacted'] || 0) + 1;
  });

  // Industry counts
  const industryCounts = {};
  companies.forEach(c => {
    if (c.industries) {
      industryCounts[c.industries] = (industryCounts[c.industries] || 0) + 1;
    }
  });

  // Location counts
  const locationCounts = {};
  companies.forEach(c => {
    if (c.all_locations) {
      locationCounts[c.all_locations] = (locationCounts[c.all_locations] || 0) + 1;
    }
  });

  // Score distribution
  const scoreDistribution = { 'Unscored': 0, '1-3': 0, '3-5': 0, '5-7': 0, '7-9': 0, '9-10': 0 };
  companies.forEach(c => {
    const score = c.company_score || 0;
    if (score === 0) scoreDistribution['Unscored']++;
    else if (score < 3) scoreDistribution['1-3']++;
    else if (score < 5) scoreDistribution['3-5']++;
    else if (score < 7) scoreDistribution['5-7']++;
    else if (score < 9) scoreDistribution['7-9']++;
    else scoreDistribution['9-10']++;
  });

  // Top 20
  const top20 = [...companies]
    .sort((a, b) => (b.company_score || 0) - (a.company_score || 0))
    .slice(0, 20)
    .map(c => ({
      id: c.id,
      name: c.name,
      one_liner: c.one_liner,
      industries: c.industries,
      weighted_total: c.company_score,
      thesis_fit_theme: c.thesis_fit_theme,
      avg_founder_score: c.founders?.length > 0
        ? c.founders.reduce((sum, f) => sum + (f.founder_score || 0), 0) / c.founders.length
        : 0
    }));

  // Diversity stats
  const allFounders = companies.flatMap(c => c.founders || []);
  const diversityStats = {
    companies_with_female_founder: companies.filter(c => c.founders?.some(f => f.is_female)).length,
    companies_with_bipoc_founder: companies.filter(c => c.founders?.some(f => f.is_black || f.is_hispanic_latino)).length,
    total_female_founders: allFounders.filter(f => f.is_female).length,
    total_bipoc_founders: allFounders.filter(f => f.is_black || f.is_hispanic_latino).length,
    total_founders: allFounders.length,
    total_companies: companies.length
  };

  // Interaction stats
  const allInteractions = companies.flatMap(c => c.interactions || []);
  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const interactionStats = {
    total_interactions: allInteractions.length,
    companies_contacted: companies.filter(c => c.interactions?.length > 0).length,
    interactions_this_week: allInteractions.filter(i => i.date >= oneWeekAgo).length
  };

  return {
    statusCounts: Object.entries(statusCounts).map(([status, count]) => ({ status, count })),
    industryCounts: Object.entries(industryCounts).map(([industries, count]) => ({ industries, count })).sort((a, b) => b.count - a.count),
    locationCounts: Object.entries(locationCounts).map(([all_locations, count]) => ({ all_locations, count })).sort((a, b) => b.count - a.count).slice(0, 20),
    scoreDistribution: Object.entries(scoreDistribution).map(([range, count]) => ({ range, count })),
    top20,
    diversityStats,
    interactionStats
  };
}

// ==========================================
// EXPORT
// ==========================================

async function exportCSV() {
  const companies = await getCompanies({});

  const headers = [
    'id', 'name', 'one_liner', 'industries', 'status', 'source', 'website', 'all_locations',
    'team_size', 'year_founded', 'thesis_fit_theme', 'company_score',
    'team_score', 'product_score', 'business_model_score', 'market_score',
    'impact_score', 'traction_score', 'deal_score', 'founder_names', 'avg_founder_score',
    'contact_email', 'deck_url', 'pitchbook_url'
  ];

  const rows = [headers.join(',')];
  for (const c of companies) {
    const values = headers.map(h => {
      const val = c[h];
      if (val === null || val === undefined) return '';
      const str = String(val).replace(/"/g, '""');
      return str.includes(',') || str.includes('"') || str.includes('\n') ? `"${str}"` : str;
    });
    rows.push(values.join(','));
  }

  return rows.join('\n');
}

module.exports = {
  getCompanies,
  getCompanyById,
  updateCompany,
  bulkUpdateStatus,
  updateCompanyScores,
  updateFounder,
  updateFounderScores,
  addInteraction,
  deleteInteraction,
  addNote,
  updateNote,
  deleteNote,
  getSettings,
  updateSettings,
  getAnalytics,
  exportCSV
};
