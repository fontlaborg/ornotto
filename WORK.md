<!-- this_file: WORK.md -->

# Work

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
