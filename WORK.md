<!-- this_file: WORK.md -->

# Work

## 2026-10-03 — completed local retry results

Exported two complete runs: Rune Q5 full Metal, 64/64 at 153.3/152.8 ms
translated/direct, and Ornith Splash, 62/63 at 322.4/328.5 ms. Q5 is 6.3 times
faster than mixed execution but changes one answer and loses one correct answer
in each mode. All 300 prior public rows, 31,834 baseline query records and frozen
translations are unchanged. Splash has its own Metal engine filter, native-choice
readout and package/storage size; calibration and exact GPU operation placement
are not asserted. Reports, rankings, tables and the offline explorer now have 302
configurations. Nine remote endpoints and their readouts remain intact.

Qwen3.6 preflight refused loading at 33/40 GiB. Small ggmlc Laya Q8 Metal
loaded, then aborted on unsupported MAP_CUSTOM2; no valid records were saved.
Related F16/Q4 attempts are deferred. Swift/storage kernel-panic investigation,
Rune Q8 and dense Qwen3.8 exclusions remain unresolved. The GPU audit is not
complete. Private guards now include positional GGUF bytes in preflight and
exit unsuccessfully on classifier errors rather than accepting a report's exit 0.

Validation: private suite 98 passed, one optional skip; package suite 98 passed,
13 engine tests deselected, lint/format and JavaScript diagram mathematics pass.
Strict 18-page build and actual local browser checks pass all three plots,
Splash engine/direct/readout CSV, Q5 accuracy comparison, Q4 regression, all
nine remote rows, URL reload, Pareto, CSV/SVG, empty results, mobile/dark,
offline HTML and homepage navigation with zero script exceptions.
Publication and live acceptance are pending.


## 2026-10-03 — full remote benchmarks and report rebuild

Completed all nine requested endpoints on 106 distinct inputs each: 954
successful requests, evaluated on 67 translated and 67 direct queries.
Frozen translations and all 30,880 prior query records are unchanged; after
export, all fields of the 291 prior classifier rows are identical. The report
now has 300 configurations: 246 G, 19 C, 19 C+G, two C+N, four A and ten R.
Remote hardware and precision remain undisclosed. Six endpoints use native
choice; Respan's three use five noul questions, argmax P(true), and normalized
weights, explicitly labelled noul OVR without a calibration claim. Record
resolved versions and providers. Pacing and transient-error waits are outside
request latency; successful responses resume from durable checkpoints.

Fresh OpenRouter Jev scores 65/67 in both modes at 364.4/375.1 ms translated/
direct. Tev1 scores 64/65 at 339.3/335.1 ms; Kev scores 65/65 at 1653.0/1525.0 ms.
All three Respan variants score 56/60. The existing hosted Jev row is retained.
Rebuilt the private report, exported all public aggregates, and added a remote
results table. The explorer groups all nine under OpenRouter API and shows
readout labels in its table and CSV; the homepage ranking now uses the same
JSON. Validation: 98 package tests pass (13 local-engine tests deselected),
81 private tests pass (one optional skipped), Ruff passes, and the strict
18-page build succeeds. Fresh local browser checks pass all three plots,
all nine API rows and readouts, filter reload, remote CSV, Pareto changes,
Rune Q4 comparison, direct timing, mobile/dark layouts, SVG, offline HTML
and homepage navigation with zero JavaScript errors. Published `a274b83`; Pages run `37076500508` succeeded. Fresh browser
acceptance on the real HTTPS URL passes all the checks above with zero
JavaScript errors, including the nine-row OpenRouter API filter and CSV.
Twelve live HTML/assets match the reviewed build after accounting for CDN
HTML injection. Remote benchmark, local/live browser and deployment evidence
are retained privately. No package release was performed.

## 2026-10-03 — remote decision models

Added nine OpenRouter IDs and explicit arbitrary decision IDs, authenticated
sync/async native System One requests, typed extraction, CLI discovery, and
the actual TypeSafe SDK transport for pydantic-ai. Calls never download or
launch local weights. Record requested/resolved model, provider, response ID
and reported usage/cost; mark calibration as unrecorded. Handle malformed
probabilities, missing answers, auth/credit/rate-limit/provider errors and
timeouts without retries. Remote keys are not sent to local engines.

The private harness accepts an explicit OPENROUTER_MODELS list; exports mark
remote rows as R rather than inventing CPU/GPU placement. Existing benchmark
results are untouched. Initial verification checked only the process environment;
the user pointed out the existing credential in ~/.env. Loading it through the
same python-dotenv path as the harness enabled authenticated inference. Six
models passed native choice/noul/score. All three Respan variants passed noul
but rejected choice/score; OPENROUTER_KINDS now records this and unsupported
calls fail locally before inference. The TypeSafe integration converts Respan
questions to plain strings and enforces the same capabilities. Initial and
corrected smoke responses, provider/model IDs, usage/cost and timings are
retained outside the public repository. They are protocol smoke checks,
not accuracy benchmarks. OpenRouter model pages and OpenAPI were consulted.
Validation: 97 package tests pass (13 local-engine tests deselected), including
actual TypeSafe and pydantic-ai transports and the Respan boolean bridge.
Authenticated pydantic-ai Agents also pass on Liquid and Respan Lite free.
The strict 18-page docs build, fresh source distribution and private suite
(81 passed, one optional skipped) also pass. All 291 benchmark rows remain
unchanged; protocol checks have not been presented as accuracy measurements. No package
release was performed.

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

Validation: 61 package tests (13 engine tests deselected), four Node math
tests, strict 18-page build, fresh desktop/mobile/dark browser checks, URL
reload, CSV, SVG and completely offline report passed. Historical evidence
was audited from recorded launches and runtime settings, not GPU utilization
traces. Initial publication exposed a CDN cache mismatch: new HTML requested
old unversioned JavaScript, which still expected the reserved search field.
The docs build now derives benchmark CSS/JS filenames from content hashes;
a regression test checks the versions and build idempotence. Local browser
acceptance passed after the fix. Published `cecfecd`; Pages run `37065299780`
succeeded. Fresh acceptance on the actual public URL passed all three charts,
filters, Pareto membership, URL reload, CSV/SVG exports, mobile and dark layouts,
offline HTML and homepage navigation with zero JavaScript errors. Analytics
requests were blocked; the Cloudflare cookie dialog was dismissed with Reject
All before interacting. All eight deployed artifacts match the reviewed build
(HTML comparisons account for Cloudflare injection). Evidence remains in the
private run folder as `browser-proof.json` and `live-proof.json`.

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
