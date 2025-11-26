/**
 * Loader for roles and competency mappings from JSON files.
 * Defaults to JSON_DIR (env or param), with robust fallbacks to the backend repo structure.
 */
const fs = require('fs');
const path = require('path');

let CACHE = {
  jsonDir: null,
  roles: [],
  competencies: [],
  roleCompArray: [],
  roleAdjacencyArray: [],
  roleCompMapByRole: new Map(), // roleLower -> Map(competencyName -> required_level)
  rolesByLowerName: new Map(),  // roleLower -> {name, description}
  verbose: false,
};

// PUBLIC_INTERFACE
function initLoader(jsonDir, opts = {}) {
  /**
   * Initialize loader and build in-memory caches.
   * @param {string} jsonDir - JSON directory, absolute or relative. Uses fallbacks if not found.
   * @param {object} opts - { verbose?: boolean }
   */
  const verbose = !!opts.verbose;
  CACHE.verbose = verbose;

  const resolvedDir = resolveJsonDir(jsonDir);
  if (verbose) {
    console.log(`[Loader] Resolved JSON_DIR=${resolvedDir}`);
  }
  CACHE.jsonDir = resolvedDir;

  const roles = readJsonSafe(path.join(resolvedDir, 'roles.json')) || [];
  const comps = readJsonSafe(path.join(resolvedDir, 'competencies.json')) || [];
  const roleComps = readJsonSafe(path.join(resolvedDir, 'role_competencies.json')) || [];
  const roleAdj = readJsonSafe(path.join(resolvedDir, 'role_adjacency.json')) || [];

  CACHE.roles = Array.isArray(roles) ? roles : [];
  CACHE.competencies = Array.isArray(comps) ? comps : [];
  CACHE.roleCompArray = Array.isArray(roleComps) ? roleComps : [];
  CACHE.roleAdjacencyArray = Array.isArray(roleAdj) ? roleAdj : [];

  indexRoles();
  indexRoleCompetencies();

  if (verbose) {
    console.log(`[Loader] roles=${CACHE.roles.length}, role_competencies=${CACHE.roleCompArray.length}, competencies=${CACHE.competencies.length}, role_adjacency=${CACHE.roleAdjacencyArray.length}`);
  }
}

function resolveJsonDir(provided) {
  const candidates = [];

  // 1) Provided by user (absolute or relative to CWD)
  if (provided) {
    const p = path.isAbsolute(provided) ? provided : path.resolve(process.cwd(), provided);
    candidates.push(p);
  }

  // 2) Default relative to CWD: data/imports
  candidates.push(path.resolve(process.cwd(), 'data', 'imports'));

  // 3) Relative to this file in monorepo: <service>/../../data/imports
  candidates.push(path.resolve(__dirname, '..', '..', 'data', 'imports'));

  // 4) Fallback: <service>/../data/imports
  candidates.push(path.resolve(__dirname, '..', 'data', 'imports'));

  for (const dir of candidates) {
    try {
      if (fs.existsSync(path.join(dir, 'roles.json'))) {
        return dir;
      }
    } catch (_) {
      // Ignore access errors and continue
    }
  }

  // If none matched, return the first provided; consumers will get errors on read
  return candidates[0];
}

function readJsonSafe(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (err) {
    if (CACHE.verbose) {
      console.warn(`[Loader] Unable to read ${filePath}: ${err.message}`);
    }
    return null;
  }
}

function indexRoles() {
  CACHE.rolesByLowerName = new Map();
  for (const r of CACHE.roles) {
    if (!r || !r.name) continue;
    CACHE.rolesByLowerName.set(String(r.name).toLowerCase(), { name: r.name, description: r.description || null });
  }
}

function indexRoleCompetencies() {
  CACHE.roleCompMapByRole = new Map();

  for (const item of CACHE.roleCompArray) {
    if (!item) continue;
    const roleRef = item.role_id || item.roleId || item.role || item.role_name;
    const compRef = item.competency_id || item.competencyId || item.competency || item.competency_name;
    let level = item.required_level ?? item.level ?? item.requiredLevel ?? 3;

    if (!roleRef || !compRef) continue;
    const roleLower = String(roleRef).toLowerCase();
    const compName = String(compRef);

    const levelInt = safeInt(level, 3);

    if (!CACHE.roleCompMapByRole.has(roleLower)) {
      CACHE.roleCompMapByRole.set(roleLower, new Map());
    }
    CACHE.roleCompMapByRole.get(roleLower).set(compName, levelInt);
  }
}

function safeInt(val, def) {
  const x = Number.parseInt(String(val), 10);
  return Number.isFinite(x) ? x : def;
}

// PUBLIC_INTERFACE
function getRoles() {
  /** Return list of roles: [{ name, description? }, ...] */
  ensureInitialized();
  return CACHE.roles.map(r => ({ name: r.name, description: r.description || null }));
}

// PUBLIC_INTERFACE
function getRoleByName(roleName) {
  /** Case-insensitive lookup for a role. Returns object or null */
  ensureInitialized();
  if (!roleName) return null;
  const key = String(roleName).toLowerCase();
  return CACHE.rolesByLowerName.get(key) || null;
}

// PUBLIC_INTERFACE
function getRoleNames() {
  /** Return a list of role names (string[]) */
  ensureInitialized();
  return CACHE.roles.map(r => r.name);
}

// PUBLIC_INTERFACE
function getCompetencyMapForRole(roleName) {
  /**
   * Return an object mapping { competencyName: required_level } for a given role,
   * or null if the role does not exist.
   */
  ensureInitialized();
  if (!roleName) return null;
  const roleLower = String(roleName).toLowerCase();
  if (!CACHE.rolesByLowerName.has(roleLower)) {
    return null;
  }
  const m = CACHE.roleCompMapByRole.get(roleLower) || new Map();
  const obj = {};
  for (const [k, v] of m.entries()) {
    obj[k] = v;
  }
  return obj;
}

// PUBLIC_INTERFACE
function getAllRoleCompetencyMaps() {
  /** Return a new Map(roleNameLower -> Map(competency -> level)) */
  ensureInitialized();
  return new Map(CACHE.roleCompMapByRole);
}

// PUBLIC_INTERFACE
function getOptionalAdjacencyOverrides() {
  /** Returns array of adjacency overrides if present: [{ currentRole, targetRole, score }, ...] */
  ensureInitialized();
  return CACHE.roleAdjacencyArray.slice();
}

function ensureInitialized() {
  if (!CACHE.jsonDir) {
    // Attempt default init if not yet initialized
    initLoader(process.env.JSON_DIR || 'data/imports', { verbose: false });
  }
}

module.exports = {
  // PUBLIC_INTERFACE
  initLoader,
  // PUBLIC_INTERFACE
  getRoles,
  // PUBLIC_INTERFACE
  getRoleByName,
  // PUBLIC_INTERFACE
  getRoleNames,
  // PUBLIC_INTERFACE
  getCompetencyMapForRole,
  // PUBLIC_INTERFACE
  getAllRoleCompetencyMaps,
  // PUBLIC_INTERFACE
  getOptionalAdjacencyOverrides,
};
