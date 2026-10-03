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

Native encoders reuse the existing model downloader, transport and managed
process lifecycle. Their loopback server uses Python's standard `http.server`.
**laya-mlx** (optional `laya-mlx` extra, 0.3 series) implements the native MLX
encoder on Apple silicon, Python 3.11+. **xDecision** is installed separately
from [the pinned source](https://github.com/xnetsc/xDecision/tree/4082689a093393358534fda26a945699080eb572),
with `[apple]` for MLX GPU or its base dependencies for PyTorch CPU. It is not
on PyPI and is not a direct-URL package dependency. Both runtimes implement
choice, noul and score; their GGUF/checkpoint formats are not interchangeable
with the bundled llama.cpp engines. Optional runtime imports occur only in the
child process. Model cards: [Laya MLX](https://huggingface.co/aac6fef/laya-multilingual-mlx),
[xDecision](https://huggingface.co/mccoysc/xDecision).
