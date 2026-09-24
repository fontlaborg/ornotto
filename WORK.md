<!-- this_file: WORK.md -->

# Work

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
