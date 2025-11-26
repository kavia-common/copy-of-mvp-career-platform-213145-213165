/**
 * Role Mapping Service - Express server
 * Endpoints:
 *  - GET /health
 *  - GET /api/v1/roles
 *  - GET /api/v1/competency-map?role=...
 *  - GET /api/v1/adjacent-roles?role=...&limit=...&minScore=...
 *  - GET /api/v1/mappings/adjacency?currentRole=...&targetRole=...
 */
require('dotenv').config();

const express = require('express');
const cors = require('cors');

const { initLoader, getRoles, getCompetencyMapForRole } = require('./loader');
const { getAdjacentRoles, getAdjacencyDetails } = require('./adjacency');

const app = express();

// CORS configuration (restrict for production)
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

// Initialize loader on startup
const verbose = String(process.env.LOG_VERBOSE || 'false').trim().toLowerCase() === 'true';
const jsonDirEnv = process.env.JSON_DIR || 'data/imports';
initLoader(jsonDirEnv, { verbose });

// PUBLIC_INTERFACE
app.get('/health', (req, res) => {
  /** Health check endpoint. */
  return res.json({ status: 'ok' });
});

// PUBLIC_INTERFACE
app.get('/api/v1/roles', (req, res) => {
  /** List roles loaded from JSON_DIR. */
  try {
    const roles = getRoles();
    return res.json(roles);
  } catch (err) {
    if (verbose) console.error('Error listing roles:', err);
    return res.status(500).json({ error: 'Failed to load roles' });
  }
});

// PUBLIC_INTERFACE
app.get('/api/v1/competency-map', (req, res) => {
  /** Retrieve competency map for a given role. */
  const role = String(req.query.role || '').trim();
  if (!role) {
    return res.status(400).json({ error: "Missing required query parameter 'role'" });
  }
  try {
    const result = getCompetencyMapForRole(role);
    if (!result) {
      return res.status(404).json({ error: `Role not found: ${role}` });
    }
    // Normalize response shape: { role, competencies: [{name, required_level}], map: {...} }
    const competencies = Object.keys(result).sort().map((name) => ({
      name,
      required_level: result[name],
    }));
    return res.json({ role, competencies, map: result });
  } catch (err) {
    if (verbose) console.error('Error getting competency map:', err);
    return res.status(500).json({ error: 'Failed to load competency map' });
  }
});

// PUBLIC_INTERFACE
app.get('/api/v1/adjacent-roles', (req, res) => {
  /** Suggest adjacent roles for a given role using weighted Jaccard similarity. */
  const role = String(req.query.role || '').trim();
  if (!role) {
    return res.status(400).json({ error: "Missing required query parameter 'role'" });
  }
  const limit = Number.parseInt(String(req.query.limit || '10'), 10);
  const minScore = Number.parseFloat(String(req.query.minScore || '0'));
  try {
    const items = getAdjacentRoles(role, { limit, minScore });
    return res.json({ role, total: items.length, items });
  } catch (err) {
    if (String(err && err.message || '').includes('Role not found')) {
      return res.status(404).json({ error: err.message });
    }
    if (verbose) console.error('Error computing adjacent roles:', err);
    return res.status(500).json({ error: 'Failed to compute adjacent roles' });
  }
});

// PUBLIC_INTERFACE
app.get('/api/v1/mappings/adjacency', (req, res) => {
  /** Detailed adjacency comparison between currentRole and targetRole. */
  const currentRole = String(req.query.currentRole || '').trim();
  const targetRole = String(req.query.targetRole || '').trim();
  if (!currentRole || !targetRole) {
    return res.status(400).json({ error: "Missing 'currentRole' or 'targetRole' query parameter" });
  }
  try {
    const details = getAdjacencyDetails(currentRole, targetRole);
    return res.json(details);
  } catch (err) {
    if (String(err && err.message || '').includes('Role not found')) {
      return res.status(404).json({ error: err.message });
    }
    if (verbose) console.error('Error computing adjacency details:', err);
    return res.status(500).json({ error: 'Failed to compute adjacency details' });
  }
});

const PORT = Number(process.env.PORT || 4000);

// Start server
app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[RoleMappingService] Listening on port ${PORT} (JSON_DIR=${jsonDirEnv})`);
});

module.exports = { app };
