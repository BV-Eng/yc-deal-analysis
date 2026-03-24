const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'data', 'yc_deals.db');

function getDb() {
  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  return db;
}

function initializeDatabase() {
  const db = getDb();

  db.exec(`
    CREATE TABLE IF NOT EXISTS companies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      yc_id TEXT UNIQUE,
      name TEXT NOT NULL,
      slug TEXT,
      one_liner TEXT,
      long_description TEXT,
      batch TEXT DEFAULT 'Winter 2026',
      source TEXT,
      status TEXT DEFAULT 'Not Contacted',
      industries TEXT,
      subindustry TEXT,
      tags TEXT,
      website TEXT,
      all_locations TEXT,
      team_size INTEGER DEFAULT 0,
      year_founded INTEGER,
      logo_url TEXT,
      b2b_b2c TEXT,
      technology_type TEXT,
      business_model TEXT,
      next_action TEXT,
      custom_tags TEXT,
      owner TEXT,
      contact_email TEXT,
      pitchbook_url TEXT,
      valuation_range TEXT,
      total_raised TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS founders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      first_name TEXT,
      last_name TEXT,
      title TEXT,
      linkedin TEXT,
      twitter TEXT,
      email TEXT,
      email_confidence INTEGER DEFAULT 0,
      avatar_url TEXT,
      bio TEXT,
      is_female INTEGER DEFAULT 0,
      is_black INTEGER DEFAULT 0,
      is_hispanic_latino INTEGER DEFAULT 0,
      schools TEXT,
      degrees TEXT,
      prior_employers TEXT,
      technical_competence TEXT,
      publications_count INTEGER DEFAULT 0,
      citations_count INTEGER DEFAULT 0,
      awards TEXT,
      patents TEXT,
      is_repeat_founder INTEGER DEFAULT 0,
      is_colocated INTEGER DEFAULT 0,
      age_range TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS company_scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL UNIQUE,
      thesis_fit_score REAL DEFAULT 0,
      thesis_fit_justification TEXT,
      thesis_fit_theme TEXT,
      team_score REAL DEFAULT 0,
      team_weight REAL DEFAULT 20,
      team_justification TEXT,
      product_score REAL DEFAULT 0,
      product_weight REAL DEFAULT 15,
      product_justification TEXT,
      business_model_score REAL DEFAULT 0,
      business_model_weight REAL DEFAULT 15,
      business_model_justification TEXT,
      market_score REAL DEFAULT 0,
      market_weight REAL DEFAULT 15,
      market_justification TEXT,
      impact_score REAL DEFAULT 0,
      impact_weight REAL DEFAULT 10,
      impact_justification TEXT,
      traction_score REAL DEFAULT 0,
      traction_weight REAL DEFAULT 15,
      traction_justification TEXT,
      deal_score REAL DEFAULT 0,
      deal_weight REAL DEFAULT 10,
      deal_justification TEXT,
      weighted_total REAL DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS founder_scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      founder_id INTEGER NOT NULL UNIQUE,
      breakthrough_score REAL DEFAULT 0,
      breakthrough_justification TEXT,
      mission_score REAL DEFAULT 0,
      mission_justification TEXT,
      achievements_score REAL DEFAULT 0,
      achievements_justification TEXT,
      work_ethic_score REAL DEFAULT 0,
      work_ethic_justification TEXT,
      grit_score REAL DEFAULT 0,
      grit_justification TEXT,
      magnetism_score REAL DEFAULT 0,
      magnetism_justification TEXT,
      curiosity_score REAL DEFAULT 0,
      curiosity_justification TEXT,
      coachability_score REAL DEFAULT 0,
      coachability_justification TEXT,
      team_chemistry_score REAL DEFAULT 0,
      team_chemistry_justification TEXT,
      weighted_total REAL DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (founder_id) REFERENCES founders(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS interactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      type TEXT NOT NULL,
      date TEXT NOT NULL,
      participants TEXT,
      notes TEXT,
      outcome TEXT,
      next_steps TEXT,
      follow_up_date TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      content TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS settings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
    CREATE INDEX IF NOT EXISTS idx_companies_industries ON companies(industries);
    CREATE INDEX IF NOT EXISTS idx_founders_company ON founders(company_id);
    CREATE INDEX IF NOT EXISTS idx_interactions_company ON interactions(company_id);
    CREATE INDEX IF NOT EXISTS idx_notes_company ON notes(company_id);
  `);

  // Insert default settings
  const insertSetting = db.prepare('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)');
  insertSetting.run('company_score_weight', '50');
  insertSetting.run('founder_score_weight', '50');

  db.close();
  console.log('Database initialized successfully');
}

function importCompanies(companiesJson) {
  const db = getDb();
  const data = JSON.parse(companiesJson);

  // Handle both formats: { companies: [...] } or direct array
  const companies = Array.isArray(data) ? data : (data.companies || []);

  const insertCompany = db.prepare(`
    INSERT OR REPLACE INTO companies (yc_id, name, slug, one_liner, long_description, batch, source, status, industries, subindustry, tags, website, all_locations, team_size, year_founded, logo_url, pitchbook_url, owner, contact_email, valuation_range, total_raised)
    VALUES (@yc_id, @name, @slug, @one_liner, @long_description, @batch, @source, @status, @industries, @subindustry, @tags, @website, @all_locations, @team_size, @year_founded, @logo_url, @pitchbook_url, @owner, @contact_email, @valuation_range, @total_raised)
  `);

  const insertFounder = db.prepare(`
    INSERT OR REPLACE INTO founders (company_id, name, first_name, last_name, title, linkedin, twitter, avatar_url, bio, is_female, is_black, is_hispanic_latino, schools, degrees, prior_employers)
    VALUES (@company_id, @name, @first_name, @last_name, @title, @linkedin, @twitter, @avatar_url, @bio, @is_female, @is_black, @is_hispanic_latino, @schools, @degrees, @prior_employers)
  `);

  const insertCompanyScore = db.prepare(`
    INSERT OR REPLACE INTO company_scores (company_id, thesis_fit_score, thesis_fit_justification, thesis_fit_theme, team_score, team_justification, product_score, product_justification, business_model_score, business_model_justification, market_score, market_justification, impact_score, impact_justification, traction_score, traction_justification, deal_score, deal_justification, weighted_total)
    VALUES (@company_id, @thesis_fit_score, @thesis_fit_justification, @thesis_fit_theme, @team_score, @team_justification, @product_score, @product_justification, @business_model_score, @business_model_justification, @market_score, @market_justification, @impact_score, @impact_justification, @traction_score, @traction_justification, @deal_score, @deal_justification, @weighted_total)
  `);

  const insertFounderScore = db.prepare(`
    INSERT OR REPLACE INTO founder_scores (founder_id, breakthrough_score, breakthrough_justification, mission_score, mission_justification, achievements_score, achievements_justification, work_ethic_score, work_ethic_justification, grit_score, grit_justification, magnetism_score, magnetism_justification, curiosity_score, curiosity_justification, coachability_score, coachability_justification, team_chemistry_score, team_chemistry_justification, weighted_total)
    VALUES (@founder_id, @breakthrough_score, @breakthrough_justification, @mission_score, @mission_justification, @achievements_score, @achievements_justification, @work_ethic_score, @work_ethic_justification, @grit_score, @grit_justification, @magnetism_score, @magnetism_justification, @curiosity_score, @curiosity_justification, @coachability_score, @coachability_justification, @team_chemistry_score, @team_chemistry_justification, @weighted_total)
  `);

  const transaction = db.transaction(() => {
    for (const company of companies) {
      const result = insertCompany.run({
        yc_id: company.yc_id || company.raw?.objectID || '',
        name: company.name,
        slug: company.slug || company.raw?.slug || '',
        one_liner: company.one_liner || '',
        long_description: company.long_description || company.raw?.long_description || '',
        batch: company.batch || 'Winter 2026',
        source: company.source || '',
        status: company.status || 'Not Contacted',
        industries: company.industries || (company.raw?.industries || []).join(', '),
        subindustry: company.subindustry || company.raw?.subindustry || '',
        tags: company.tags || (company.raw?.tags || []).join(', '),
        website: company.website || company.raw?.website || '',
        all_locations: company.all_locations || company.raw?.all_locations || '',
        team_size: company.team_size || company.raw?.team_size || 0,
        year_founded: company.year_founded || company.raw?.year_founded || null,
        logo_url: company.logo_url || company.raw?.small_logo_thumb_url || '',
        pitchbook_url: company.pitchbook_url || '',
        owner: company.owner || '',
        contact_email: company.contact_email || '',
        valuation_range: company.valuation_range || '',
        total_raised: company.total_raised || ''
      });

      const companyId = result.lastInsertRowid;

      // Insert company scores with actual values
      insertCompanyScore.run({
        company_id: companyId,
        thesis_fit_score: company.thesis_fit_score || 0,
        thesis_fit_justification: company.thesis_fit_justification || '',
        thesis_fit_theme: company.thesis_fit_theme || '',
        team_score: company.team_score || 0,
        team_justification: company.team_justification || '',
        product_score: company.product_score || 0,
        product_justification: company.product_justification || '',
        business_model_score: company.business_model_score || 0,
        business_model_justification: company.business_model_justification || '',
        market_score: company.market_score || 0,
        market_justification: company.market_justification || '',
        impact_score: company.impact_score || 0,
        impact_justification: company.impact_justification || '',
        traction_score: company.traction_score || 0,
        traction_justification: company.traction_justification || '',
        deal_score: company.deal_score || 0,
        deal_justification: company.deal_justification || '',
        weighted_total: company.weighted_total || company.company_score || 0
      });

      // Insert founders with scores
      const founders = company.founders || [];
      for (const founder of founders) {
        const fResult = insertFounder.run({
          company_id: companyId,
          name: founder.name || '',
          first_name: founder.first_name || '',
          last_name: founder.last_name || '',
          title: founder.title || '',
          linkedin: founder.linkedin || '',
          twitter: founder.twitter || '',
          avatar_url: founder.avatar_url || '',
          bio: founder.bio || '',
          is_female: founder.is_female ? 1 : 0,
          is_black: founder.is_black ? 1 : 0,
          is_hispanic_latino: founder.is_hispanic_latino ? 1 : 0,
          schools: founder.schools || '',
          degrees: founder.degrees || '',
          prior_employers: founder.prior_employers || ''
        });

        const founderId = fResult.lastInsertRowid;

        // Insert founder scores with actual values
        insertFounderScore.run({
          founder_id: founderId,
          breakthrough_score: founder.breakthrough_score || 0,
          breakthrough_justification: founder.breakthrough_justification || '',
          mission_score: founder.mission_score || 0,
          mission_justification: founder.mission_justification || '',
          achievements_score: founder.achievements_score || 0,
          achievements_justification: founder.achievements_justification || '',
          work_ethic_score: founder.work_ethic_score || 0,
          work_ethic_justification: founder.work_ethic_justification || '',
          grit_score: founder.grit_score || 0,
          grit_justification: founder.grit_justification || '',
          magnetism_score: founder.magnetism_score || 0,
          magnetism_justification: founder.magnetism_justification || '',
          curiosity_score: founder.curiosity_score || 0,
          curiosity_justification: founder.curiosity_justification || '',
          coachability_score: founder.coachability_score || 0,
          coachability_justification: founder.coachability_justification || '',
          team_chemistry_score: founder.team_chemistry_score || 0,
          team_chemistry_justification: founder.team_chemistry_justification || '',
          weighted_total: founder.founder_score || 0
        });
      }
    }
  });

  transaction();

  const companyCount = db.prepare('SELECT COUNT(*) as count FROM companies').get().count;
  const founderCount = db.prepare('SELECT COUNT(*) as count FROM founders').get().count;
  const scoredFounders = db.prepare('SELECT COUNT(*) as count FROM founder_scores WHERE weighted_total > 0').get().count;

  console.log(`Imported ${companyCount} companies, ${founderCount} founders (${scoredFounders} with scores)`);

  db.close();
}

module.exports = { getDb, initializeDatabase, importCompanies };
