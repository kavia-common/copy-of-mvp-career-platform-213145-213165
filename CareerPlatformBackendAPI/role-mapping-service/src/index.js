/**
 * Compatibility export: allows ESM test imports to load CJS modules easily.
 * Not used by the server directly, but useful for external consumers/tests.
 */
const loader = require('./loader');
const adjacency = require('./adjacency');

module.exports = {
  ...loader,
  ...adjacency,
};
