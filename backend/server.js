const express = require('express');
const cors = require('cors');
const path = require('path');
const { getDb, initializeDatabase, importCompanies } = require('./database');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3456;

app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: '50mb' }));

app.use(express.static(path.join(__dirname, '..', 'frontend', 'dist')));

// ==========================================
// COMPANIES
// ==========================================

app.get('/api/companies', (req, res) => {
  const db = getDb();
  try {
    const { status, industry, location, search, minScore, maxScore, diversity, sort, order, tag, source } = req.query;

    let sql = `
      SELECT c.*,
        cs.weighted_total as company_score,
        cs.team_score, cs.product_score, cs.business_model_score,
        cs.market_score, cs.impact_score, cs.traction_score, cs.deal_score,
        cs.thesis_fit_score, cs.thesis_fit_theme,
        (SELECT GROUP_CONCAT(f.name, ', ') FROM founders f WHERE f.company_id = c.id) as founder_names,
        (SELECT GROUP_CONCAT(f.name || '::' || COALESCE(f.linkedin,'') || '::' || COALESCE(f.email,''), '|||') FROM founders f WHERE f.company_id = c.id) as founder_linkedin_data,
        (SELECT MAX(f.is_female) FROM founders f WHERE f.company_id = c.id) as has_female_founder,
        (SELECT MAX(f.is_black) FROM founders f WHERE f.company_id = c.id) as has_black_founder,
        (SELECT MAX(f.is_hispanic_latino) FROM founders f WHERE f.company_id = c.id) as has_hispanic_founder,
        (SELECT MAX(i.date) FROM interactions i WHERE i.company_id = c.id) as last_interaction_date,
        (SELECT AVG(fs2.weighted_total) FROM founders f2 JOIN founder_scores fs2 ON fs2.founder_id = f2.id WHERE f2.company_id = c.id) as avg_founder_score
      FROM companies c
      LEFT JOIN company_scores cs ON cs.company_id = c.id
      WHERE 1=1
    `;
    const params = [];

    if (status) {
      sql += ` AND c.status = ?`;
      params.push(status);
    }
    if (industry) {
      sql += ` AND c.industries LIKE ?`;
      params.push(`%${industry}%`);
    }
    if (location) {
      sql += ` AND c.all_locations LIKE ?`;
      params.push(`%${location}%`);
    }
    if (search) {
      sql += ` AND (c.name LIKE ? OR c.one_liner LIKE ? OR c.long_description LIKE ? OR c.contact_email LIKE ? OR EXISTS (SELECT 1 FROM founders f WHERE f.company_id = c.id AND (f.name LIKE ? OR f.email LIKE ?)))`;
      params.push(`%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`);
    }
    if (tag) {
      sql += ` AND (c.tags LIKE ? OR c.custom_tags LIKE ?)`;
      params.push(`%${tag}%`, `%${tag}%`);
    }
    if (diversity === 'female') {
      sql += ` AND EXISTS (SELECT 1 FROM founders f WHERE f.company_id = c.id AND f.is_female = 1)`;
    }
    if (diversity === 'bipoc') {
      sql += ` AND EXISTS (SELECT 1 FROM founders f WHERE f.company_id = c.id AND (f.is_black = 1 OR f.is_hispanic_latino = 1))`;
    }

    // Thesis theme filter
    const { theme } = req.query;
    if (theme) {
      if (theme === 'on-thesis') {
        sql += ` AND cs.thesis_fit_theme NOT IN ('Off-Thesis', 'Neutral')`;
      } else if (theme === 'off-thesis') {
        sql += ` AND cs.thesis_fit_theme IN ('Off-Thesis', 'Neutral')`;
      } else {
        sql += ` AND cs.thesis_fit_theme LIKE ?`;
        params.push(`%${theme}%`);
      }
    }

    // Owner filter
    const { owner: ownerFilter } = req.query;
    if (ownerFilter) {
      if (ownerFilter === 'unassigned') {
        sql += ` AND (c.owner IS NULL OR c.owner = '')`;
      } else {
        sql += ` AND c.owner = ?`;
        params.push(ownerFilter);
      }
    }

    // Source filter
    if (source) {
      sql += ` AND c.source = ?`;
      params.push(source);
    }

    const sortCol = sort || 'company_score';
    const sortOrder = order || 'DESC';
    const validSorts = ['name', 'company_score', 'status', 'industries', 'all_locations', 'last_interaction_date', 'avg_founder_score', 'team_score', 'product_score', 'market_score', 'thesis_fit_score', 'impact_score', 'owner', 'weighted_total'];
    if (validSorts.includes(sortCol)) {
      sql += ` ORDER BY ${sortCol} ${sortOrder === 'ASC' ? 'ASC' : 'DESC'}`;
    } else {
      sql += ` ORDER BY cs.weighted_total DESC`;
    }

    const companies = db.prepare(sql).all(...params);
    res.json(companies);
  } finally {
    db.close();
  }
});

app.get('/api/companies/:id', (req, res) => {
  const db = getDb();
  try {
    const company = db.prepare(`
      SELECT c.*,
        cs.*,
        c.id as id
      FROM companies c
      LEFT JOIN company_scores cs ON cs.company_id = c.id
      WHERE c.id = ?
    `).get(req.params.id);

    if (!company) return res.status(404).json({ error: 'Company not found' });

    const founders = db.prepare(`
      SELECT f.*, fs.*,
        f.id as id, f.name as name
      FROM founders f
      LEFT JOIN founder_scores fs ON fs.founder_id = f.id
      WHERE f.company_id = ?
    `).all(req.params.id);

    const interactions = db.prepare(`
      SELECT * FROM interactions WHERE company_id = ? ORDER BY date DESC
    `).all(req.params.id);

    const notes = db.prepare(`
      SELECT * FROM notes WHERE company_id = ? ORDER BY created_at DESC
    `).all(req.params.id);

    res.json({ company, founders, interactions, notes });
  } finally {
    db.close();
  }
});

app.put('/api/companies/:id', (req, res) => {
  const db = getDb();
  try {
    const { status, next_action, custom_tags, b2b_b2c, technology_type, business_model, owner, contact_email } = req.body;
    db.prepare(`
      UPDATE companies SET
        status = COALESCE(?, status),
        next_action = COALESCE(?, next_action),
        custom_tags = COALESCE(?, custom_tags),
        b2b_b2c = COALESCE(?, b2b_b2c),
        technology_type = COALESCE(?, technology_type),
        business_model = COALESCE(?, business_model),
        owner = COALESCE(?, owner),
        contact_email = COALESCE(?, contact_email),
        updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(status, next_action, custom_tags, b2b_b2c, technology_type, business_model, owner, contact_email, req.params.id);
    res.json({ success: true });
  } finally {
    db.close();
  }
});

// ==========================================
// COMPANY SCORES
// ==========================================

app.put('/api/companies/:id/scores', (req, res) => {
  const db = getDb();
  try {
    const scores = req.body;
    const fields = [
      'thesis_fit_score', 'thesis_fit_weight', 'thesis_fit_justification', 'thesis_fit_theme',
      'team_score', 'team_weight', 'team_justification',
      'product_score', 'product_weight', 'product_justification',
      'business_model_score', 'business_model_weight', 'business_model_justification',
      'market_score', 'market_weight', 'market_justification',
      'impact_score', 'impact_weight', 'impact_justification',
      'traction_score', 'traction_weight', 'traction_justification',
      'deal_score', 'deal_weight', 'deal_justification'
    ];

    // Calculate weighted total
    const categories = ['thesis_fit', 'team', 'product', 'business_model', 'market', 'impact', 'traction', 'deal'];
    let totalWeight = 0;
    let weightedSum = 0;
    for (const cat of categories) {
      const score = scores[`${cat}_score`] || 0;
      const weight = scores[`${cat}_weight`] || 0;
      totalWeight += weight;
      weightedSum += score * weight;
    }
    const weightedTotal = totalWeight > 0 ? weightedSum / totalWeight : 0;

    const setClauses = fields.map(f => `${f} = @${f}`).join(', ');
    db.prepare(`
      UPDATE company_scores SET ${setClauses}, weighted_total = @weighted_total, updated_at = CURRENT_TIMESTAMP
      WHERE company_id = @company_id
    `).run({
      ...Object.fromEntries(fields.map(f => [f, scores[f] !== undefined ? scores[f] : null])),
      weighted_total: weightedTotal,
      company_id: req.params.id
    });

    res.json({ success: true, weighted_total: weightedTotal });
  } finally {
    db.close();
  }
});

// ==========================================
// FOUNDER SCORES
// ==========================================

app.put('/api/founders/:id/scores', (req, res) => {
  const db = getDb();
  try {
    const scores = req.body;
    const categories = ['breakthrough', 'mission', 'achievements', 'work_ethic', 'grit', 'magnetism', 'curiosity', 'coachability', 'team_chemistry'];

    let sum = 0;
    let count = 0;
    for (const cat of categories) {
      const score = scores[`${cat}_score`] || 0;
      if (score > 0) {
        sum += score;
        count++;
      }
    }
    const weightedTotal = count > 0 ? sum / count : 0;

    const fields = categories.flatMap(c => [`${c}_score`, `${c}_justification`]);
    const setClauses = fields.map(f => `${f} = @${f}`).join(', ');

    db.prepare(`
      UPDATE founder_scores SET ${setClauses}, weighted_total = @weighted_total, updated_at = CURRENT_TIMESTAMP
      WHERE founder_id = @founder_id
    `).run({
      ...Object.fromEntries(fields.map(f => [f, scores[f] !== undefined ? scores[f] : null])),
      weighted_total: weightedTotal,
      founder_id: req.params.id
    });

    res.json({ success: true, weighted_total: weightedTotal });
  } finally {
    db.close();
  }
});

app.put('/api/founders/:id', (req, res) => {
  const db = getDb();
  try {
    const { schools, degrees, prior_employers, technical_competence, publications_count, citations_count, awards, patents, is_repeat_founder, is_colocated, age_range } = req.body;
    db.prepare(`
      UPDATE founders SET
        schools = COALESCE(?, schools),
        degrees = COALESCE(?, degrees),
        prior_employers = COALESCE(?, prior_employers),
        technical_competence = COALESCE(?, technical_competence),
        publications_count = COALESCE(?, publications_count),
        citations_count = COALESCE(?, citations_count),
        awards = COALESCE(?, awards),
        patents = COALESCE(?, patents),
        is_repeat_founder = COALESCE(?, is_repeat_founder),
        is_colocated = COALESCE(?, is_colocated),
        age_range = COALESCE(?, age_range)
      WHERE id = ?
    `).run(schools, degrees, prior_employers, technical_competence, publications_count, citations_count, awards, patents, is_repeat_founder, is_colocated, age_range, req.params.id);
    res.json({ success: true });
  } finally {
    db.close();
  }
});

// ==========================================
// INTERACTIONS
// ==========================================

app.post('/api/companies/:id/interactions', (req, res) => {
  const db = getDb();
  try {
    const { type, date, participants, notes, outcome, next_steps, follow_up_date } = req.body;
    const result = db.prepare(`
      INSERT INTO interactions (company_id, type, date, participants, notes, outcome, next_steps, follow_up_date)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(req.params.id, type, date, participants, notes, outcome, next_steps, follow_up_date);
    res.json({ success: true, id: result.lastInsertRowid });
  } finally {
    db.close();
  }
});

app.delete('/api/interactions/:id', (req, res) => {
  const db = getDb();
  try {
    db.prepare('DELETE FROM interactions WHERE id = ?').run(req.params.id);
    res.json({ success: true });
  } finally {
    db.close();
  }
});

// ==========================================
// NOTES
// ==========================================

app.post('/api/companies/:id/notes', (req, res) => {
  const db = getDb();
  try {
    const { content } = req.body;
    const result = db.prepare(`
      INSERT INTO notes (company_id, content) VALUES (?, ?)
    `).run(req.params.id, content);
    res.json({ success: true, id: result.lastInsertRowid });
  } finally {
    db.close();
  }
});

app.put('/api/notes/:id', (req, res) => {
  const db = getDb();
  try {
    const { content } = req.body;
    db.prepare('UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?').run(content, req.params.id);
    res.json({ success: true });
  } finally {
    db.close();
  }
});

app.delete('/api/notes/:id', (req, res) => {
  const db = getDb();
  try {
    db.prepare('DELETE FROM notes WHERE id = ?').run(req.params.id);
    res.json({ success: true });
  } finally {
    db.close();
  }
});

// ==========================================
// SETTINGS
// ==========================================

app.get('/api/settings', (req, res) => {
  const db = getDb();
  try {
    const settings = db.prepare('SELECT * FROM settings').all();
    const result = {};
    settings.forEach(s => { result[s.key] = s.value; });
    res.json(result);
  } finally {
    db.close();
  }
});

app.put('/api/settings', (req, res) => {
  const db = getDb();
  try {
    const upsert = db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)');
    for (const [key, value] of Object.entries(req.body)) {
      upsert.run(key, String(value));
    }
    res.json({ success: true });
  } finally {
    db.close();
  }
});

// ==========================================
// ANALYTICS
// ==========================================

app.get('/api/analytics', (req, res) => {
  const db = getDb();
  try {
    const statusCounts = db.prepare(`
      SELECT status, COUNT(*) as count FROM companies GROUP BY status ORDER BY count DESC
    `).all();

    const industryCounts = db.prepare(`
      SELECT industries, COUNT(*) as count FROM companies GROUP BY industries ORDER BY count DESC
    `).all();

    const locationCounts = db.prepare(`
      SELECT all_locations, COUNT(*) as count FROM companies WHERE all_locations != '' GROUP BY all_locations ORDER BY count DESC LIMIT 20
    `).all();

    const scoreDistribution = db.prepare(`
      SELECT
        CASE
          WHEN cs.weighted_total = 0 THEN 'Unscored'
          WHEN cs.weighted_total < 3 THEN '1-3'
          WHEN cs.weighted_total < 5 THEN '3-5'
          WHEN cs.weighted_total < 7 THEN '5-7'
          WHEN cs.weighted_total < 9 THEN '7-9'
          ELSE '9-10'
        END as range,
        COUNT(*) as count
      FROM company_scores cs
      GROUP BY range ORDER BY range
    `).all();

    const top20 = db.prepare(`
      SELECT c.id, c.name, c.one_liner, c.industries, cs.weighted_total, cs.thesis_fit_theme,
        (SELECT AVG(fs.weighted_total) FROM founders f JOIN founder_scores fs ON fs.founder_id = f.id WHERE f.company_id = c.id) as avg_founder_score
      FROM companies c
      LEFT JOIN company_scores cs ON cs.company_id = c.id
      ORDER BY cs.weighted_total DESC
      LIMIT 20
    `).all();

    const diversityStats = db.prepare(`
      SELECT
        (SELECT COUNT(DISTINCT c.id) FROM companies c JOIN founders f ON f.company_id = c.id WHERE f.is_female = 1) as companies_with_female_founder,
        (SELECT COUNT(DISTINCT c.id) FROM companies c JOIN founders f ON f.company_id = c.id WHERE f.is_black = 1 OR f.is_hispanic_latino = 1) as companies_with_bipoc_founder,
        (SELECT COUNT(*) FROM founders WHERE is_female = 1) as total_female_founders,
        (SELECT COUNT(*) FROM founders WHERE is_black = 1 OR is_hispanic_latino = 1) as total_bipoc_founders,
        (SELECT COUNT(*) FROM founders) as total_founders,
        (SELECT COUNT(*) FROM companies) as total_companies
    `).get();

    let interactionStats = { total_interactions: 0, companies_contacted: 0, interactions_this_week: 0 };
    try {
      const intCount = db.prepare('SELECT COUNT(*) as c FROM interactions').get();
      if (intCount.c > 0) {
        interactionStats = db.prepare(`
          SELECT
            COUNT(*) as total_interactions,
            COUNT(DISTINCT company_id) as companies_contacted,
            (SELECT COUNT(*) FROM interactions WHERE date >= date('now', '-7 days')) as interactions_this_week
          FROM interactions
        `).get();
      }
    } catch(e) { /* empty table */ }

    res.json({
      statusCounts,
      industryCounts,
      locationCounts,
      scoreDistribution,
      top20,
      diversityStats,
      interactionStats
    });
  } finally {
    db.close();
  }
});

// ==========================================
// EXPORT
// ==========================================

app.get('/api/export/csv', (req, res) => {
  const db = getDb();
  try {
    const companies = db.prepare(`
      SELECT c.*,
        cs.thesis_fit_score, cs.thesis_fit_weight, cs.thesis_fit_justification, cs.thesis_fit_theme,
        cs.team_score, cs.team_weight, cs.team_justification,
        cs.product_score, cs.product_weight, cs.product_justification,
        cs.business_model_score, cs.business_model_weight, cs.business_model_justification,
        cs.market_score, cs.market_weight, cs.market_justification,
        cs.impact_score, cs.impact_weight, cs.impact_justification,
        cs.traction_score, cs.traction_weight, cs.traction_justification,
        cs.deal_score, cs.deal_weight, cs.deal_justification,
        cs.weighted_total as company_weighted_total,
        (SELECT GROUP_CONCAT(f.name, '; ') FROM founders f WHERE f.company_id = c.id) as founder_names,
        (SELECT GROUP_CONCAT(f.linkedin, '; ') FROM founders f WHERE f.company_id = c.id) as founder_linkedins,
        (SELECT AVG(fs.weighted_total) FROM founders f JOIN founder_scores fs ON fs.founder_id = f.id WHERE f.company_id = c.id) as avg_founder_score
      FROM companies c
      LEFT JOIN company_scores cs ON cs.company_id = c.id
      ORDER BY cs.weighted_total DESC
    `).all();

    const headers = Object.keys(companies[0] || {});
    const csvRows = [headers.join(',')];

    for (const row of companies) {
      const values = headers.map(h => {
        const val = row[h];
        if (val === null || val === undefined) return '';
        const str = String(val).replace(/"/g, '""');
        return str.includes(',') || str.includes('"') || str.includes('\n') ? `"${str}"` : str;
      });
      csvRows.push(values.join(','));
    }

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=yc_w26_deals.csv');
    res.send(csvRows.join('\n'));
  } finally {
    db.close();
  }
});

// ==========================================
// BULK OPERATIONS
// ==========================================

app.post('/api/bulk/status', (req, res) => {
  const db = getDb();
  try {
    const { companyIds, status } = req.body;
    const placeholders = companyIds.map(() => '?').join(',');
    db.prepare(`UPDATE companies SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id IN (${placeholders})`).run(status, ...companyIds);
    res.json({ success: true, updated: companyIds.length });
  } finally {
    db.close();
  }
});

// ==========================================
// SERVE FRONTEND
// ==========================================

app.get('/{*splat}', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
});

// ==========================================
// STARTUP
// ==========================================

function startup() {
  console.log('Initializing database...');
  initializeDatabase();

  // Import companies data if database is empty
  const db = getDb();
  const count = db.prepare('SELECT COUNT(*) as count FROM companies').get().count;
  db.close();

  if (count === 0) {
    const dataPath = path.join(__dirname, '..', 'data', 'seed-data.json');
    if (fs.existsSync(dataPath)) {
      console.log('Importing company data from seed-data.json...');
      importCompanies(fs.readFileSync(dataPath, 'utf-8'));
    }
  } else {
    console.log(`Database already has ${count} companies`);
  }

  app.listen(PORT, () => {
    console.log(`\n🚀 YC Deal Analysis CRM running at http://localhost:${PORT}`);
    console.log(`   API: http://localhost:${PORT}/api/companies`);
  });
}

startup();
