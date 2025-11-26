/**
 * Adjacency logic for roles based on competency overlap and required levels.
 * Core similarity uses weighted Jaccard over required levels:
 *    score = sum(min(a_i, b_i)) / sum(max(a_i, b_i))
 */
const {
  getRoleByName,
  getRoleNames,
  getCompetencyMapForRole,
  getOptionalAdjacencyOverrides,
} = require('./loader');

// Compute score using weighted Jaccard similarity between two competency maps
// PUBLIC_INTERFACE
function computeAdjacencyScore(mapA, mapB) {
  /**
   * @param {Record<string, number>} mapA
   * @param {Record<string, number>} mapB
   * @returns {number} score in [0..1]
   */
  const keys = new Set([...Object.keys(mapA || {}), ...Object.keys(mapB || {})]);
  let sumMin = 0;
  let sumMax = 0;
  keys.forEach((k) => {
    const a = toInt(mapA?.[k] || 0);
    const b = toInt(mapB?.[k] || 0);
    if (a === 0 && b === 0) return; // skip pure zeros
    sumMin += Math.min(a, b);
    sumMax += Math.max(a, b);
  });
  if (sumMax === 0) return 0;
  return sumMin / sumMax;
}

function toInt(x) {
  const n = Number.parseInt(String(x), 10);
  return Number.isFinite(n) ? n : 0;
}

function setDiff(aKeys, bKeys) {
  const set = new Set(aKeys);
  for (const k of bKeys) set.delete(k);
  return set;
}

// PUBLIC_INTERFACE
function getAdjacentRoles(roleName, options = {}) {
  /**
   * Compute adjacency suggestions for a role.
   * @param {string} roleName - The role to compute adjacency for
   * @param {object} options - { limit: number=10, minScore: number=0 }
   * @returns {Array<{ role: string, score: number, sharedCompetencies: number, missingInCurrent: number, extraInCurrent: number }>}
   */
  const role = getRoleByName(roleName);
  if (!role) throw new Error(`Role not found: ${roleName}`);

  const mapA = getCompetencyMapForRole(role.name) || {};
  const names = getRoleNames().filter((n) => n.toLowerCase() !== role.name.toLowerCase());

  const limit = Number.isFinite(options.limit) ? options.limit : 10;
  const minScore = Number.isFinite(options.minScore) ? options.minScore : 0;

  const overrides = buildAdjacencyOverrideMap(getOptionalAdjacencyOverrides());

  const results = [];
  for (const otherName of names) {
    const mapB = getCompetencyMapForRole(otherName) || {};

    // override score if provided, else compute
    const overrideKey = `${role.name.toLowerCase()}||${otherName.toLowerCase()}`;
    let score = overrides.has(overrideKey) ? overrides.get(overrideKey) : computeAdjacencyScore(mapA, mapB);

    // quick stats
    const sharedCompetencies = intersectCount(Object.keys(mapA), Object.keys(mapB));
    const missingInCurrent = diffCount(Object.keys(mapB), Object.keys(mapA)); // present in target but not in current
    const extraInCurrent = diffCount(Object.keys(mapA), Object.keys(mapB));   // present in current but not in target

    results.push({
      role: otherName,
      score: round2(score),
      sharedCompetencies,
      missingInCurrent,
      extraInCurrent,
    });
  }

  const filtered = results
    .filter((r) => r.score >= minScore)
    .sort((a, b) => b.score - a.score);

  return filtered.slice(0, limit);
}

function round2(x) {
  return Math.round((x + Number.EPSILON) * 100) / 100;
}

function buildAdjacencyOverrideMap(arr) {
  const m = new Map();
  for (const item of arr || []) {
    const a = item.currentRole || item.from || item.role || null;
    const b = item.targetRole || item.to || item.role2 || null;
    const s = typeof item.score === 'number' ? item.score : null;
    if (!a || !b || s === null) continue;
    m.set(`${String(a).toLowerCase()}||${String(b).toLowerCase()}`, s);
  }
  return m;
}

function intersectCount(a, b) {
  const set = new Set(a);
  let c = 0;
  for (const k of b) if (set.has(k)) c += 1;
  return c;
}
function diffCount(a, b) {
  const setB = new Set(b);
  let c = 0;
  for (const k of a) if (!setB.has(k)) c += 1;
  return c;
}

// PUBLIC_INTERFACE
function getAdjacencyDetails(currentRoleName, targetRoleName) {
  /**
   * Return a detailed view of adjacency, including competency deltas.
   * @param {string} currentRoleName
   * @param {string} targetRoleName
   * @returns {{
   *   currentRole: string,
   *   targetRole: string,
   *   score: number,
   *   shared: Array<{ competency: string, current_level: number, target_level: number, delta: number }>,
   *   missingInCurrent: Array<{ competency: string, target_level: number }>,
   *   extraInCurrent: Array<{ competency: string, current_level: number }>,
   *   stats: { sharedCompetencies: number, missingInCurrent: number, extraInCurrent: number }
   * }}
   */
  const a = getRoleByName(currentRoleName);
  if (!a) throw new Error(`Role not found: ${currentRoleName}`);
  const b = getRoleByName(targetRoleName);
  if (!b) throw new Error(`Role not found: ${targetRoleName}`);

  const mapA = getCompetencyMapForRole(a.name) || {};
  const mapB = getCompetencyMapForRole(b.name) || {};

  const score = computeAdjacencyScore(mapA, mapB);
  const setA = new Set(Object.keys(mapA));
  const setB = new Set(Object.keys(mapB));

  const shared = [];
  for (const comp of setA) {
    if (setB.has(comp)) {
      const curr = toInt(mapA[comp]);
      const targ = toInt(mapB[comp]);
      shared.push({
        competency: comp,
        current_level: curr,
        target_level: targ,
        delta: targ - curr,
      });
    }
  }
  // Sorted to keep responses stable
  shared.sort((x, y) => x.competency.localeCompare(y.competency));

  const missingInCurrent = [];
  for (const comp of setB) {
    if (!setA.has(comp)) {
      missingInCurrent.push({ competency: comp, target_level: toInt(mapB[comp]) });
    }
  }
  missingInCurrent.sort((x, y) => x.competency.localeCompare(y.competency));

  const extraInCurrent = [];
  for (const comp of setA) {
    if (!setB.has(comp)) {
      extraInCurrent.push({ competency: comp, current_level: toInt(mapA[comp]) });
    }
  }
  extraInCurrent.sort((x, y) => x.competency.localeCompare(y.competency));

  return {
    currentRole: a.name,
    targetRole: b.name,
    score: round2(score),
    shared,
    missingInCurrent,
    extraInCurrent,
    stats: {
      sharedCompetencies: shared.length,
      missingInCurrent: missingInCurrent.length,
      extraInCurrent: extraInCurrent.length,
    },
  };
}

module.exports = {
  // PUBLIC_INTERFACE
  computeAdjacencyScore,
  // PUBLIC_INTERFACE
  getAdjacentRoles,
  // PUBLIC_INTERFACE
  getAdjacencyDetails,
};
