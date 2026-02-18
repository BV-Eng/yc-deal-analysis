const express = require('express');
const cors = require('cors');
const path = require('path');
const db = require('./database-redis');

const app = express();
const PORT = process.env.PORT || 3456;

app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: '50mb' }));

// Serve frontend
app.use(express.static(path.join(__dirname, '..', 'frontend', 'dist')));

// ==========================================
// COMPANIES
// ==========================================

app.get('/api/companies', async (req, res) => {
  try {
    const companies = await db.getCompanies(req.query);
    res.json(companies);
  } catch (e) {
    console.error('Error fetching companies:', e);
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/companies/:id', async (req, res) => {
  try {
    const result = await db.getCompanyById(req.params.id);
    if (!result) return res.status(404).json({ error: 'Company not found' });
    res.json(result);
  } catch (e) {
    console.error('Error fetching company:', e);
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/companies/:id', async (req, res) => {
  try {
    await db.updateCompany(req.params.id, req.body);
    res.json({ success: true });
  } catch (e) {
    console.error('Error updating company:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// COMPANY SCORES
// ==========================================

app.put('/api/companies/:id/scores', async (req, res) => {
  try {
    const weightedTotal = await db.updateCompanyScores(req.params.id, req.body);
    res.json({ success: true, weighted_total: weightedTotal });
  } catch (e) {
    console.error('Error updating company scores:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// FOUNDER SCORES
// ==========================================

app.put('/api/founders/:id/scores', async (req, res) => {
  try {
    const weightedTotal = await db.updateFounderScores(req.params.id, req.body);
    res.json({ success: true, weighted_total: weightedTotal });
  } catch (e) {
    console.error('Error updating founder scores:', e);
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/founders/:id', async (req, res) => {
  try {
    await db.updateFounder(req.params.id, req.body);
    res.json({ success: true });
  } catch (e) {
    console.error('Error updating founder:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// INTERACTIONS
// ==========================================

app.post('/api/companies/:id/interactions', async (req, res) => {
  try {
    const id = await db.addInteraction(req.params.id, req.body);
    res.json({ success: true, id });
  } catch (e) {
    console.error('Error adding interaction:', e);
    res.status(500).json({ error: e.message });
  }
});

app.delete('/api/interactions/:id', async (req, res) => {
  try {
    await db.deleteInteraction(req.params.id);
    res.json({ success: true });
  } catch (e) {
    console.error('Error deleting interaction:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// NOTES
// ==========================================

app.post('/api/companies/:id/notes', async (req, res) => {
  try {
    const id = await db.addNote(req.params.id, req.body.content);
    res.json({ success: true, id });
  } catch (e) {
    console.error('Error adding note:', e);
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/notes/:id', async (req, res) => {
  try {
    await db.updateNote(req.params.id, req.body.content);
    res.json({ success: true });
  } catch (e) {
    console.error('Error updating note:', e);
    res.status(500).json({ error: e.message });
  }
});

app.delete('/api/notes/:id', async (req, res) => {
  try {
    await db.deleteNote(req.params.id);
    res.json({ success: true });
  } catch (e) {
    console.error('Error deleting note:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// SETTINGS
// ==========================================

app.get('/api/settings', async (req, res) => {
  try {
    const settings = await db.getSettings();
    res.json(settings);
  } catch (e) {
    console.error('Error fetching settings:', e);
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/settings', async (req, res) => {
  try {
    await db.updateSettings(req.body);
    res.json({ success: true });
  } catch (e) {
    console.error('Error updating settings:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// ANALYTICS
// ==========================================

app.get('/api/analytics', async (req, res) => {
  try {
    const analytics = await db.getAnalytics();
    res.json(analytics);
  } catch (e) {
    console.error('Error fetching analytics:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// EXPORT
// ==========================================

app.get('/api/export/csv', async (req, res) => {
  try {
    const csv = await db.exportCSV();
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=yc_w26_deals.csv');
    res.send(csv);
  } catch (e) {
    console.error('Error exporting CSV:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// BULK OPERATIONS
// ==========================================

app.post('/api/bulk/status', async (req, res) => {
  try {
    const { companyIds, status } = req.body;
    const updated = await db.bulkUpdateStatus(companyIds, status);
    res.json({ success: true, updated });
  } catch (e) {
    console.error('Error bulk updating status:', e);
    res.status(500).json({ error: e.message });
  }
});

// ==========================================
// SERVE FRONTEND (catch-all)
// ==========================================

app.get('/{*splat}', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
});

// ==========================================
// STARTUP
// ==========================================

app.listen(PORT, () => {
  console.log(`\n🚀 YC Deal Analysis CRM running at http://localhost:${PORT}`);
  console.log(`   API: http://localhost:${PORT}/api/companies`);
});
