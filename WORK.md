<!-- this_file: WORK.md -->

# Work

## 2026-10-02 — Metal rerun and benchmark explorer

Rune mradermacher Q4 completed alone on Metal (`--gpu-layers -1`, MTL0),
with 106 finite normalized results and three question-type smokes. Mean
classification latency is 124.782090 ms translated and 125.138806 ms direct;
scores remain 63/67 and 64/67. All 106 task answers match the earlier CPU-weight
run. All original cache records and all fields of the 290 earlier classifier
rows are preserved; the new run has a distinct ID. No other models rerun.

Every classifier now has execution configuration and evidence: 246 G, 19 C,
19 C+G, two C+N, four A and one R. Automatic placement remains unprofiled.
CPU labels appear in private reports, public tables, quantization grids,
landing bars, charts, tooltips and downloadable data. CPU audit lists all C
and C+G runs. Direct-mode charts use original-text timings.

Added standard-library diagram generator and vendored Plotly basic 3.1.0/MIT.
The explorer provides threshold/device/engine/family/search filters, live
Pareto frontiers for speed and file size, fastest qualifying bars, shareable
URLs, CSV and SVG exports, and a self-contained offline HTML. Weight size is
explicitly distinguished from RAM; the Jev Decision Index suite is described
without mixing its scores or timings with this routing test.

Validation: 60 package tests (13 engine tests deselected), four Node math
tests, strict 18-page build, fresh desktop/mobile/dark browser checks, URL
reload, CSV, SVG and completely offline report passed. Historical evidence
was audited from recorded launches and runtime settings, not GPU utilization
traces. Publication and live acceptance pending.

## 2026-10-02 — issue 102, complete measurement set

All 24 weight variants are measured through 32 methods: 290 public rows,
with all original 258 field-identical. Every new method has 106 distinct
texts, no error and finite normalized five-way probabilities. JPT Q8 files
are local conversions of the requested repositories' pinned BF16 files;
the sanitized conversion manifests record hashes and tensor types. mys Kev
Q4/Q8 remain incompatible with dohnuts and explicitly use ggmlc Metal.

Rune Q5 on pcdServer scores 65/67 in both modes (962 ms/query, CPU weights).
Rune Q3 scores 64/64 at 146 ms. Q4/Q5 retain Metal compute with CPU weights;
Q8 disables GPU weights, compute and KV offload after earlier guarded loads
exceeded disk/swap limits. Swap grew during the larger attempts; no run loaded
a second model. All requested downloaded models and BF16 inputs are retained.

The bundled engine forks are dohnuts dbf48c0 (llama.cpp 7fe450e, 0.5.0-dev)
and pcdServer 1046a00 (llama.cpp v0.4.1). Native
JPT prompts match the pinned source renderer byte for byte; Jet and JPT
label mappings now follow their respective question types. pcdServer adds a
Jinja fallback and avoids a duplicated Gemma 4 BOS. Registered metadata/head
overrides work; three native profiles are bundled. `gpu=False` disables pcd
GPU weights, compute and KV offload. Five further registry entries added.

Validation: 55 package unit tests and all 13 real-engine integration tests (including ollaya); ruff clean; 70 pcdServer CTests passed with
a real JPT GGUF; Gemma 4 native template/BOS test passed (9 assertions);
dohnuts helper CTest passed; 63 private tests passed, one optional skip.
Strict book build: 16 pages. Native wheel and sdist built; both engine binaries
and all three profiles inspected directly. Packaged pcd Rune and dohnuts JPT binaries passed choice, yes/no and score smoke checks. Published commit `be02eaa1fb01b9c030b6e8da9475af6d4706cd3e`; Pages run
`37057357552` succeeded. Fresh live landing/results/details/package/choosing
reads match the generated content after the CDN script and email-marker changes;
both full tables contain exactly 290 rows and every method ID. The public
conversion manifest matches its pinned committed bytes.

## 2026-10-02 — issue 102, native Bosun and ggmlc Kev

Added three further measured rows: Bosun Q5_K_M (55/67 in both modes, 130.8 ms),
mys Kev Q8 (57/67 translated, 45/67 direct, 199.8 ms) and dynamic Q4 (54/67,
43/67, 207.2 ms). Each measured all 106 texts alone under the watchdog, with
zero swap growth. The book now includes 264 methods; all 258 earlier rows are
field-identical. Both mys Kev files fail to load in current dohnuts because their
architecture is ggmlc, so the published rows use ggmlc Metal. Bosun uses native
stable-slot prompts and valid decision-token logits, with exact prompt checks
against its pinned source renderer and tokenizer template. Private tests:
63 passed, one optional skip. Full issue remains open for larger files and
unpublished JPT Q8 variants. No existing model files removed.

## 2026-10-02 — issue 102, first measurements

Added three measured methods and retained all 258 earlier exported rows field by field.
Tev1 Q8 on dohnuts: 59/67 translated, 62/67 direct, 61.5 ms/query.
Tev1 MLX 4-bit: 60/67, 59/67, 64.8 ms/query. Kev Core ML fp16 L512/K16
CPU + GPU: 60/67, 62/67, 121.3 ms/query. The 106 distinct texts per method
are cached. Each ran alone under the watchdog; swap stayed at zero.

Registered Tev1 and updated dohnuts to fork f1658b9 (upstream 85a917a plus ordered Tev1 score criteria; includes merged cache PR).
The native macOS wheel and sdist build passed; 51 package tests passed.
Private input and download tests: 56 passed, one optional test skipped.
Issue 102 remains in progress: the other downloads and measurements need storage;
JPT Q8 files are absent from the requested repositories. Initial publication passed Pages run 37033687821 and fresh live-page checks.


## 2026-09-30 — issue 101: the book for the second benchmark round

Exported the second round into `src_docs/data/` (258 methods: the 208 earlier rows unchanged field by
field, 50 new; 234 with a size) and rewrote the affected chapters from that data: 3, 4, 5, 6, 7, 8, 9, 10,
12, 1 and the index, plus the README's model paragraph. `gen_tables.py` now counts the rows in its caption
and orders the MLX, MXFP, `q4_0` and `q8_0` labels in the quantization grid.

Results: `./docs.sh` builds 14 pages with `--strict`; `./test.sh` passes (ruff clean, 47 unit tests, 13
engine tests deselected). The ollaya engine test is still not run (see TODO).

## 2026-09-29 — issue 101, task 2: the ollaya engine and new models

Added the `ollaya` engine and twelve registry entries (ten ollaya tags, JevK5 4B and APUS-OpenJev 35B on
pcdServer). Models that need their own runtimes (NeoHorse, Jev-Omni head, MLX, ONNX, Core ML) stay
benchmark-only and are named in the README.

Checked against ollaya 0.7.5 with a bare daemon on a private port and no model loaded:

- `GET /` answers `Ollaya is running`, and `/health` is 404.
- `OLLAYA_KEEP_ALIVE=-1` is accepted.
- `/api/tags` lists `name` and `model` as `kev:0.8b`.
- A 422 body is `{"error": …, "code": …}`.
- `ollaya stop` with our `OLLAYA_HOST` ends the server.

Results: ruff clean, 47 unit tests pass, and 13 engine tests are deselected. `mypy --strict src` shows 6
errors. All 6 were there before this change, which removed 3 others: the CLI `engine` types.

Not yet run: `test_engine_ollaya_when_kev_then_one_decision`, which loads kev:0.8b. Run it when nothing else
is resident:

```sh
OLLAYA_MODELS=<store with kev:0.8b> uv run pytest -q -m engine tests/test_ollaya.py
```

## 2026-09-24 — shared FontLab documentation design

Use the published Marketing/styleguide editorial assets, typography, five-theme
selector, collapsible contents and FontLab menu/footer. Group Home with Concepts
and show Concepts, Benchmarks and The package as tabs. Preserve chapter URLs,
article text, benchmark data, sorting/filtering, code copying and chapter links.

Baseline: 28 package tests passed (12 engine tests excluded). Strict docs build
passed. All 14 generated article bodies and anchor lists match the baseline.
The in-app browser runtime reported no available browsers; rendered checks use
the existing Playwright installation.

Candidate acceptance passed at 390, 800, 1100, 1440 and 1920px: all five themes
and persistence, header/footer, section tabs, contents toggle, actual clipboard
copying, local search, scrolling, sticky local controls and keyboard focus.
All 208 full-result benchmark rows remain present; sorting and filtering work.
The four shared page/history shortcuts pass. Screenshots and the reproducible
browser check are in `/tmp/ornotto-theme-qa/`.

Published `81274ec` to main; Pages run `36015636925` succeeded. The full live
check passed at https://fontlab.org/ornotto/ after dismissing the consent dialog:
five persisted themes, all five viewport widths, local search and drawer focus,
contents toggle, clipboard copying, all 208 benchmark rows with sorting/filtering,
and all four navigation/history shortcuts. No page errors were reported.
Evidence: `/tmp/ornotto-theme-qa/live-report.json` and `live-*.png` screenshots.
The final strict docs build and 28 package tests passed (12 engine tests excluded).
