// this_file: src_docs/md/js/benchmark-math.js
(function (root) {
  'use strict';
  const finite = v => typeof v === 'number' && Number.isFinite(v);
  function pareto(rows, x, y) {
    const measured = rows.filter(r => finite(r[x]) && r[x] > 0 && finite(r[y]));
    return measured.filter(a => !measured.some(b =>
      b[x] <= a[x] && b[y] >= a[y] && (b[x] < a[x] || b[y] > a[y])));
  }
  function filterRuns(rows, options) {
    const mode = options.mode || 'translated';
    const words = (options.search || '').toLowerCase().split(/\s+/).filter(Boolean);
    return rows.map(r => ({...r, mode, score: r[mode], latency: mode === 'direct' ? r.ms_direct : r.ms}))
      .filter(r => finite(r.score) && finite(r.latency) && r.latency > 0
        && r.score >= (options.minScore ?? 0) && (!options.maxMs || r.latency <= options.maxMs)
        && ['device', 'engine', 'family'].every(k => !options[k] || options[k] === r[k])
        && words.every(w => `${r.method} ${r.engine} ${r.family} ${r.device_detail}`.toLowerCase().includes(w)));
  }
  const api = {pareto, filterRuns};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BenchmarkMath = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
