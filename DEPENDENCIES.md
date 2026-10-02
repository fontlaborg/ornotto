---
this_file: DEPENDENCIES.md
---

# Dependencies

Package, development and documentation dependencies are declared in
[`pyproject.toml`](pyproject.toml) and pinned in `uv.lock`.
Native engine dependencies are the pinned submodules in `engines/`.

OpenRouter support reuses the existing **httpx** dependency for authenticated
sync/async System One requests; no OpenRouter SDK is needed. The optional
pydantic-ai integration reuses its existing TypeSafe SDK and HTTPX2 transport.
Request and response contracts were checked against OpenRouter's
[System One reference](https://openrouter.ai/docs/api/api-reference/systemone/submit-a-system-one-request)
and current OpenAPI schema on 2026-10-03.

The benchmark explorer uses **Plotly.js basic 3.1.0** (MIT), vendored in
`src_docs/md/js/vendor/` together with its licence. It supplies scatter plots,
bars, zoom, hover, reactive updates and SVG exports. It is loaded only on pages
with an explorer, and embedded in the standalone HTML so that downloads work
offline. Sources: [release](https://github.com/plotly/plotly.js/releases/tag/v3.1.0),
[function reference](https://plotly.com/javascript/plotlyjs-function-reference/).

`src_docs/gen_diagrams.py` uses only the Python standard library. Node.js runs
the browser mathematics tests when available; package tests skip that check on
environments without Node. Playwright was used for local browser acceptance
and is not a package or site dependency.
