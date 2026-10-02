// this_file: src_docs/md/js/benchmark.js
(function () {
  'use strict';
  const colors = {G: '#ce3333', C: '#286da8', 'C+G': '#9652ae', 'C+N': '#26806b', A: '#ab740c', R: '#555', '?': '#888'};
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const fmt = v => v == null ? '—' : Number(v).toFixed(1);
  const keys = ['mode', 'device', 'engine', 'family', 'minScore', 'maxMs', 'search', 'scale', 'frontOnly'];
  const config = {responsive: true, displaylogo: false, toImageButtonOptions: {format: 'svg', filename: 'ornotto-benchmark'}, modeBarButtonsToRemove: ['select2d', 'lasso2d']};
  let plotlyPromise;
  function loadPlotly(widget) {
    if (window.Plotly) return Promise.resolve();
    if (!plotlyPromise) plotlyPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = widget.dataset.plotly;
      script.onload = resolve;
      script.onerror = () => {plotlyPromise = null; reject(new Error('Charts could not load; use the offline HTML download.'));};
      document.head.appendChild(script);
    });
    return plotlyPromise;
  }
  function layout(widget, title, xTitle, scale) {
    const style = getComputedStyle(widget);
    return {title: {text: title, font: {size: 17}}, margin: {l: 55, r: 20, t: 60, b: 70},
      font: {color: style.color, family: 'system-ui, sans-serif', size: 12},
      paper_bgcolor: style.getPropertyValue('--be-paper').trim() || '#fff',
      plot_bgcolor: style.getPropertyValue('--be-paper').trim() || '#fff',
      xaxis: {title: {text: xTitle}, type: scale, gridcolor: '#8883', zeroline: false},
      yaxis: {title: {text: 'Correct answers / 67'}, range: [0, 68], gridcolor: '#8883', zeroline: false},
      legend: {orientation: 'h', y: -.22}, hovermode: 'closest'};
  }
  function scatter(widget, rows, x, title, xTitle, state) {
    const {pareto} = window.BenchmarkMath;
    const measured = rows.filter(r => typeof r[x] === 'number' && r[x] > 0);
    const front = pareto(measured, x, 'score');
    const ids = new Set(front.map(r => r.method));
    const visible = state.frontOnly ? front : measured;
    const traces = Object.keys(colors).map(device => {
      const rs = visible.filter(r => r.device === device);
      return {type: 'scatter', mode: 'markers', name: device, x: rs.map(r => r[x]), y: rs.map(r => r.score),
        customdata: rs.map(r => r.method), text: rs.map(r => `${esc(r.method)}<br>${esc(r.device)} · ${r.score}/67 · ${fmt(r.latency)} ms<br>${r.gb ?? 'unknown'} weight GB`),
        hovertemplate: '%{text}<extra></extra>', marker: {color: colors[device], size: rs.map(r => ids.has(r.method) ? 11 : 7),
          opacity: rs.map(r => ids.has(r.method) ? 1 : .55), line: {width: 1, color: colors[device]}}};
    }).filter(t => t.x.length);
    const unique = front.filter((r, i, a) => a.findIndex(v => v[x] === r[x] && v.score === r.score) === i).sort((a, b) => a[x] - b[x]);
    traces.push({type: 'scatter', mode: 'lines', name: 'Pareto frontier', x: unique.map(r => r[x]), y: unique.map(r => r.score),
      line: {color: '#888', width: 2, dash: 'dot'}, hoverinfo: 'skip'});
    const l = layout(widget, title, xTitle, state.scale);
    l.yaxis.range = [Math.max(0, state.minScore - 3), 68];
    l.shapes = [{type: 'line', xref: 'paper', x0: 0, x1: 1, y0: state.minScore, y1: state.minScore, line: {color: '#888', width: 1, dash: 'dash'}}];
    return {traces, layout: l, front, omitted: rows.length - measured.length};
  }
  function showDetail(widget, row) {
    if (!row) return;
    widget.querySelector('.be-detail').textContent = `${row.method} — ${row.device}: ${row.device_detail}. Evidence: ${row.device_evidence}. ${row.score}/67, ${fmt(row.latency)} ms/query; ${row.gb ?? 'unknown'} weight GB. ${row.note || ''}`;
  }
  function stateOf(form) {
    const state = Object.fromEntries(keys.map(k => [k, form.elements[k].type === 'checkbox' ? form.elements[k].checked : form.elements[k].value]));
    state.minScore = Math.max(0, Math.min(67, Number(state.minScore)));
    state.maxMs = Math.max(0, Number(state.maxMs));
    return state;
  }
  function restore(form) {
    form.reset();
    const params = new URL(location.href).searchParams;
    keys.forEach(k => {if (params.has('bench_' + k)) {
      const input = form.elements[k], value = params.get('bench_' + k);
      if (input.type === 'checkbox') input.checked = value === 'true';
      else input.value = value;
    }});
  }
  function share(state) {
    const url = new URL(location.href);
    keys.forEach(k => {url.searchParams.delete('bench_' + k); if (String(state[k]) !== String({mode: 'translated', minScore: 50, scale: 'log', frontOnly: false, maxMs: 0}[k] ?? '')) url.searchParams.set('bench_' + k, state[k]);});
    history.replaceState(null, '', url);
  }
  function csv(rows) {
    const fields = ['method', 'mode', 'device', 'device_detail', 'device_evidence', 'engine', 'family', 'score', 'latency', 'gb'];
    const quote = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
    return [fields.join(','), ...rows.map(r => fields.map(k => quote(r[k])).join(','))].join('\r\n');
  }
  async function init(widget) {
    if (widget.dataset.ready) return;
    widget.dataset.ready = 'true';
    const all = JSON.parse(widget.querySelector('.be-data').textContent), form = widget.querySelector('form');
    const status = widget.querySelector('.be-status');
    let current = [], pending = Promise.resolve();
    restore(form);
    function update() {
      if (!widget.isConnected) return;
      const state = stateOf(form);
      share(state);
      const rows = window.BenchmarkMath.filterRuns(all, state).sort((a, b) => a.latency - b.latency || b.score - a.score);
      const speed = scatter(widget, rows, 'latency', 'Accuracy × classification latency', 'Mean ms/query · lower is faster', state);
      const size = scatter(widget, rows, 'gb', 'Accuracy × weight file size', 'Weight files, decimal GB · not peak RAM', state);
      const speedIds = new Set(speed.front.map(r => r.method)), sizeIds = new Set(size.front.map(r => r.method));
      current = state.frontOnly ? rows.filter(r => speedIds.has(r.method)) : rows;
      const best = rows[0];
      status.textContent = `${rows.length} of ${all.length} runs qualify. ${best ? `Fastest: ${best.method} (${best.device}), ${best.score}/67 at ${fmt(best.latency)} ms.` : 'No runs match these filters.'} Speed frontier: ${speed.front.length}; size frontier: ${size.front.length}. ${size.omitted} runs have no measured weight size.`;
      widget.querySelector('tbody').innerHTML = current.map(r => `<tr><td><button type="button" data-method="${esc(r.method)}">${esc(r.method)}</button></td><td title="${esc(r.device_detail)}">${esc(r.device)}</td><td>${r.score}/67</td><td>${fmt(r.latency)}</td><td>${r.gb ?? '—'}</td><td>${[speedIds.has(r.method) ? 'Speed' : '', sizeIds.has(r.method) ? 'Size' : ''].filter(Boolean).join(', ') || '—'}</td></tr>`).join('');
      widget.querySelectorAll('tbody button').forEach(b => b.onclick = () => showDetail(widget, rows.find(r => r.method === b.dataset.method)));
      widget.querySelector('.be-detail').textContent = 'Hover a point for its exact run. Click a point or a table row for execution evidence.';
      const fastest = current.slice(0, 15).reverse();
      const barLayout = layout(widget, 'Fastest runs meeting your score threshold', 'Mean ms/query', state.scale);
      barLayout.margin.l = Math.min(250, widget.clientWidth * .42);
      const labelLimit = widget.clientWidth < 500 ? 16 : 26;
      barLayout.yaxis = {type: 'category', tickfont: {size: 10}, automargin: false,
        tickvals: fastest.map(r => r.method), ticktext: fastest.map(r => `${r.model.slice(0, labelLimit)}${r.model.length > labelLimit ? '…' : ''} ${r.quant} · ${r.device}`)};
      const bars = [{type: 'bar', orientation: 'h', x: fastest.map(r => r.latency), y: fastest.map(r => r.method), customdata: fastest.map(r => r.method),
        marker: {color: fastest.map(r => colors[r.device])}, text: fastest.map(r => `${esc(r.method)}<br>${r.score}/67 · ${fmt(r.latency)} ms`), hovertemplate: '%{text}<extra></extra>'}];
      // Serialize updates so rapid slider/filter changes cannot leave stale plots.
      pending = pending.catch(() => {}).then(async () => {
        await loadPlotly(widget);
        const plots = [...widget.querySelectorAll('.be-chart')];
        await Promise.all([Plotly.react(plots[0], speed.traces, speed.layout, config), Plotly.react(plots[1], size.traces, size.layout, config), Plotly.react(plots[2], bars, barLayout, config)]);
        plots.forEach(plot => {plot.removeAllListeners('plotly_click'); plot.on('plotly_click', e => showDetail(widget, rows.find(r => r.method === e.points[0].customdata)));});
      }).catch(e => {status.textContent += ' ' + e.message;});
    }
    form.onsubmit = e => e.preventDefault();
    form.oninput = update;
    form.onreset = () => setTimeout(update, 0);
    widget.querySelector('.be-csv').onclick = () => {
      const url = URL.createObjectURL(new Blob([csv(current)], {type: 'text/csv;charset=utf-8'}));
      const a = document.createElement('a'); a.href = url; a.download = 'ornotto-filtered-' + form.elements.mode.value + '.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    window.addEventListener('popstate', () => {if (widget.isConnected) {restore(form); update();}});
    new MutationObserver(update).observe(document.documentElement, {attributes: true, attributeFilter: ['data-md-color-scheme']});
    let width = widget.clientWidth;
    new ResizeObserver(() => {if (widget.clientWidth !== width) {width = widget.clientWidth; update();}}).observe(widget);
    update();
  }
  function setUp() {document.querySelectorAll('.benchmark-explorer').forEach(init);}
  if (typeof document$ !== 'undefined') document$.subscribe(setUp);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setUp);
  else setUp();
})();
