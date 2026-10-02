// this_file: tests/benchmark.test.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const { pareto, filterRuns } = require('../src_docs/md/js/benchmark-math.js');
const row = (method, ms, translated, extra = {}) => ({method, ms, translated, device: 'G', engine: 'pcd', family: 'dedicated', ...extra});

test('Pareto keeps equal points and excludes strictly dominated points', () => {
  const rows = [row('a', 1, 50), row('b', 1, 50), row('c', 2, 50), row('d', 2, 60), row('e', 3, 59)];
  assert.deepEqual(pareto(rows, 'ms', 'translated').map(r => r.method), ['a', 'b', 'd']);
});
test('Pareto excludes missing, zero and nonfinite x without inventing sizes', () => {
  assert.deepEqual(pareto([row('a', null, 60), row('b', 0, 61), row('c', Infinity, 62)], 'ms', 'translated'), []);
  assert.deepEqual(pareto([row('a', 2, 60, {gb: null}), row('b', 3, 55, {gb: 1})], 'gb', 'translated').map(r => r.method), ['b']);
});
test('Direct mode uses direct latency and excludes English-only runs', () => {
  const rows = [row('a', 1, 60, {direct: 51, ms_direct: 8}), row('b', 2, 61, {direct: null, ms_direct: null})];
  const selected = filterRuns(rows, {mode: 'direct', minScore: 50, maxMs: 10});
  assert.equal(selected.length, 1);
  assert.equal(selected[0].latency, 8);
  assert.equal(selected[0].score, 51);
  assert.deepEqual(filterRuns(rows, {mode: 'direct', minScore: 50, maxMs: 7}), []);
});
test('Filters combine device, family, engine, score and all search words', () => {
  const rows = [row('Rune Q4', 124, 63), row('Rune Q4 CPU', 487, 63, {device: 'C+G'})];
  assert.equal(filterRuns(rows, {mode: 'translated', minScore: 50, device: 'G', search: 'rune q4'}).length, 1);
  assert.equal(filterRuns(rows, {mode: 'translated', minScore: 64}).length, 0);
  assert.equal(filterRuns(rows, {mode: 'translated', family: 'vanilla'}).length, 0);
});
