import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const loader = await import('../src/loader.js');
const adjacency = await import('../src/adjacency.js');

test('computeAdjacencyScore weighted Jaccard basic', () => {
  const a = { A: 5, B: 3 };
  const b = { A: 5, B: 4, C: 2 };

  // sumMin: min(5,5)+min(3,4)+min(0,2)=5+3+0=8
  // sumMax: max(5,5)+max(3,4)+max(0,2)=5+4+2=11
  // score = 8/11 = 0.727...
  const score = adjacency.computeAdjacencyScore(a, b);
  assert.ok(score > 0.72 && score < 0.74, `score was ${score}`);
});

test('loader can read sample JSON from backend repo', () => {
  const jsonDir = path.resolve(__dirname, '../../data/imports');
  loader.initLoader(jsonDir, { verbose: false });

  const roles = loader.getRoles();
  assert.ok(Array.isArray(roles) && roles.length > 0, 'roles should be non-empty');

  const chiefMap = loader.getCompetencyMapForRole('Chief Architect');
  assert.ok(chiefMap && typeof chiefMap === 'object', 'should return competency map');

  // From provided sample data, Chief Architect has Technical Architecture: 5
  assert.equal(chiefMap['Technical Architecture'], 5);
});

test('getAdjacentRoles returns results for a known role', () => {
  const items = adjacency.getAdjacentRoles('Chief Architect', { limit: 10, minScore: 0 });
  assert.ok(Array.isArray(items), 'should return array');
  assert.ok(items.length >= 1, 'should return at least one suggestion');
});

test('getAdjacencyDetails returns competency deltas between roles', () => {
  const details = adjacency.getAdjacencyDetails('Chief Architect', 'CTO');
  assert.equal(details.currentRole, 'Chief Architect');
  assert.equal(details.targetRole, 'CTO');
  assert.ok(typeof details.score === 'number');
  assert.ok(Array.isArray(details.shared));
  assert.ok(Array.isArray(details.missingInCurrent));
  assert.ok(Array.isArray(details.extraInCurrent));
});
