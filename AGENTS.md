<!-- this_file: AGENTS.md -->

# ornotto: agent guidance

<!-- shared-theme-integration:start -->
## Shared theme maintenance

Read [THEME.md](THEME.md) before changing shared chrome, MaterialX configuration
or component assets. This repository’s role is: ornotto documentation with fontlab editorial chrome.
Shared browser behavior belongs in `fontlab-www-docstheme`; FontLab global menu
source belongs in `img/docs/menu/fontlab.js`, Vexy menu source in
`i.vexy.art/docs/menu/vexy.js`. Keep per-site content, branding and native builds here.
Preserve one menu and one search control, documented ownership defaults, scoped
`.fltheme-components` styles and `du-` component prefixes. Verify final generated
HTML after overlays; a source-only change is not proof of a live deployment.
Do not commit unrelated local edits or hand-edit generated CSS as the source fix.
Work directly unless the current user explicitly requests delegation.
<!-- shared-theme-integration:end -->

## Book build and landing page

- Build with `./docs.sh` (ProperDocs `--strict`); commit the generated `docs/` in the same push, since GitHub Pages serves `main:/docs`. When chapters are mid-edit by someone else, build and commit `docs/` from a clean worktree of `HEAD`, then fast-forward `main`.
- Mermaid: MaterialX renders diagrams in a closed shadow root and scales them to the column. Every block starts with `%%{init: {"flowchart": {"useMaxWidth": false}}}%%` (or the `sequence` key). Theme colours live in `src_docs/md/css/site.css` as `--md-mermaid-*` variables; init-directive `themeVariables` are ignored. Prefer top-down layouts for chains longer than four nodes.
- The landing page is `src_docs/md/index.md` plus scoped rules in `css/site.css` (prefixed `.md-content__inner.md-typeset`). It hides the sidebars through front matter. daisyUI `du-stat` and `du-hero` fight the shared bundle at phone width; use the editorial card and hero classes instead.
- Benchmark data comes only from `src_docs/data/*.json` (exported privately). Never write a number the JSON does not contain; a `null` direct score means an English-only model, rendered as an empty cell.
- Images under `src_docs/md/img/` are generated illustrations (editorial flat, red/black/off-white, no text); keep each under 1 MB.
