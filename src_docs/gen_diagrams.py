#!/usr/bin/env python3
# this_file: src_docs/gen_diagrams.py
# ruff: noqa: E501  # Embedded HTML is kept readable as markup.
"""Generate the report's interactive explorer and a self-contained offline HTML.

Usage: python3 src_docs/gen_diagrams.py [--data FILE] [--out FILE]
No Python plotting dependencies or network access are required.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MD = HERE / "md"
DEVICES = {"C", "G", "C+G", "C+N", "A", "R", "?"}


def version_assets(config: Path, asset_root: Path = MD) -> None:
    """Bind published asset URLs to their bytes so CDN caches cannot mix releases."""
    text = config.read_text()
    for asset in ("css/benchmark.css", "js/benchmark-math.js", "js/benchmark.js"):
        source = asset_root / asset
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        versioned = source.with_name(f"{source.stem}.{digest}{source.suffix}")
        versioned.write_bytes(source.read_bytes())
        stem, suffix = asset.rsplit(".", 1)
        pattern = r"(?m)  - " + re.escape(stem) + r"(?:\.[a-f0-9]{12})?\." + suffix + r"(?:\?v=[^\s]+)?$"
        text = re.sub(pattern, f"  - {stem}.{digest}.{suffix}", text)
    config.write_text(text)


def read_runs(path: Path) -> list[dict]:
    """Reject ambiguous device records and malformed scores before chart generation."""
    rows = json.loads(path.read_text())
    if not rows or len({r["method"] for r in rows}) != len(rows):
        raise ValueError("Expected nonempty runs with unique method IDs")
    for r in rows:
        if r.get("device") not in DEVICES or not r.get("device_detail") or not r.get("device_evidence"):
            raise ValueError(f"Missing execution evidence: {r['method']}")
        for field in ("ms", "ms_direct", "gb", "translated", "direct"):
            value = r.get(field)
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise ValueError(f"Invalid {field}: {r['method']}")
        for field in ("translated", "direct"):
            if r.get(field) is not None and not 0 <= r[field] <= 67:
                raise ValueError(f"Score outside 0..67: {r['method']}")
    return rows


def select(name: str, label: str, values: list[str], labels: dict | None = None) -> str:
    """Render labelled controls using escaped data values."""
    options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape((labels or {}).get(v, v) or "All")}</option>'
        for v in values
    )
    return f'<label>{label}<select name="{name}">{options}</select></label>'


def widget(rows: list[dict]) -> str:
    """A shared component for the book and standalone report, backed by the same JSON."""
    controls = select(
        "mode", "Scoring mode", ["translated", "direct"], {"translated": "Translated", "direct": "Direct"}
    )
    controls += select("device", "Execution device", ["", *sorted({r["device"] for r in rows})])
    controls += select("engine", "Engine", ["", *sorted({r["engine"] for r in rows})])
    controls += select("family", "Model family", ["", "dedicated", "fine-tuned", "vanilla"])
    controls += (
        '<label>Minimum correct / 67<input name="minScore" type="number" min="0" max="67" value="50"></label>'
    )
    controls += '<label>Maximum ms/query<input name="maxMs" type="number" min="0" step="any" placeholder="No limit"></label>'
    controls += '<label>Search runs<input name="benchSearch" type="search" placeholder="e.g. rune q4"></label>'
    controls += select(
        "scale", "Horizontal scale", ["log", "linear"], {"log": "Logarithmic", "linear": "Linear"}
    )
    controls += '<label class="be-check"><input name="frontOnly" type="checkbox">Pareto frontier only</label>'
    payload = json.dumps(rows, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    return f"""<section class="benchmark-explorer" data-plotly="../../js/vendor/plotly-basic-3.1.0.min.js" aria-label="Interactive benchmark explorer">
<script type="application/json" class="be-data">{payload}</script>
<form class="be-controls">{controls}<button type="reset">Reset filters</button><button type="button" class="be-csv">Download filtered CSV</button></form>
<p class="be-status" role="status" aria-live="polite">Loading interactive charts…</p>
<p class="be-legend">C = CPU · G = GPU · C+G = mixed · C+N = CPU + Neural Engine · A = automatic CPU/GPU/Neural Engine placement · R = remote · ? = CPU/GPU unrecorded. Configuration describes the run; it is not a hardware utilization trace.</p>
<div class="be-chart" data-chart="latency" role="img" aria-label="Accuracy versus latency, with Pareto frontier"></div>
<div class="be-chart" data-chart="size" role="img" aria-label="Accuracy versus weight file size, with Pareto frontier"></div>
<div class="be-chart be-bars" data-chart="fastest" role="img" aria-label="Fastest qualifying benchmark runs"></div>
<p class="be-detail" tabindex="0">Hover a point for its exact run. Click a point or a table row for execution evidence.</p>
<div class="be-table"><table><caption>Filtered runs, fastest first. Pareto membership is calculated within the current filters.</caption><thead><tr><th>Run</th><th>C/G</th><th>Correct / 67</th><th>ms/query</th><th>Weight GB</th><th>Pareto</th><th>Readout</th></tr></thead><tbody></tbody></table></div>
<noscript>Enable JavaScript for the diagrams. The full report tables remain readable without it.</noscript>
</section>"""


def generate(data: Path, out: Path, snippet: Path | None = None) -> None:
    """Produce portable interactive diagrams, with all assets and results embedded."""
    component = widget(read_runs(data))
    css = (MD / "css" / "benchmark.css").read_text()
    scripts = [
        (MD / "js" / p).read_text().replace("</script", "<\\/script")
        for p in ("vendor/plotly-basic-3.1.0.min.js", "benchmark-math.js", "benchmark.js")
    ]
    document = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    document += (
        "<title>Ornotto benchmark explorer</title><style>body{font:16px system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#222;background:#fff}"
        + css
        + "</style><main><h1>Ornotto benchmark explorer</h1>"
    )
    document += "<p>67 FontLab routing queries in 30 languages, five choices. Apple M4 Max, 48 GiB; hosted Jev is a remote reference. Scores and timings are single recorded passes, not confidence intervals. Weight GB is disk size, not peak RAM. Classification latency excludes translation and loading.</p>"
    document += (
        component
        + '<p>Generated from the public benchmark JSON. Charts: Plotly.js 3.1.0 (MIT). <a href="https://fontlab.org/ornotto/results/explorer/">Methodology and current report</a>.</p></main>'
    )
    document += "".join("<script>" + s + "</script>" for s in scripts) + "</html>\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document)
    if snippet:
        snippet.parent.mkdir(parents=True, exist_ok=True)
        snippet.write_text(component + "\n")
    print(f"Generated {out} ({len(read_runs(data))} runs)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=HERE / "data" / "classifiers.json")
    parser.add_argument("--out", type=Path, default=MD / "downloads" / "benchmark-explorer.html")
    parser.add_argument("--snippet", type=Path, help="Optional book include; custom exports leave it untouched")
    parser.add_argument("--version-assets", action="store_true", help="Version the book's CSS/JS URLs by content")
    args = parser.parse_args()
    if args.version_assets:
        version_assets(HERE / "properdocs.yml")
    generate(args.data, args.out, args.snippet)
