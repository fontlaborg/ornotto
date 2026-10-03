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

## Additional System One adapters

The optional `transformers` extra uses Torch (tested 2.14.1) and Transformers
(tested 5.18.0) for explicit CPU/MPS NLI and letter-slot scoring. The `onnx`
extra adds ONNX Runtime >=1.26 (tested 1.30.0 CPU Q4) and NumPy; physical
sidecar downloads preserve the graph's external-data layout. Both require
Python 3.11+. The `bosun` extra uses llama-cpp-python >=0.3.36 (tested Metal)
and NumPy, with Bosun's Apache-2.0 prompt compiler attributed in
`licenses/bosun-NOTICE`. No downloaded weights are bundled.

Native Lite and mpuig runtimes are separate source installs pinned to
[fritzprix/systemone-lite fc6fbe3](https://github.com/fritzprix/systemone-lite/tree/fc6fbe3e9a3976d5c2976589f0f7176cfdcfb110)
and [mpuig/system-one ed076ed](https://github.com/mpuig/system-one/tree/ed076ed47d5e09187b66697982f6aa65263387dc).
The latter uses MLX/MLX-LM on Apple silicon and preserves the upstream
calibration identity check. CoreAIKit's `systemone` CLI (tested 0.7.3) and
current llama.cpp's `llama-server` are external executables. Their discovery
overrides are `ORNOTTO_COREAI_BIN` and `ORNOTTO_LLAMA_BIN`. CoreAI's catalog
controls its model revision; tested scorer pin is f27dcd3124cb3aa53e46b6707d3edb976f55c5f3.

Model licences and availability are recorded per pinned repository in
`src/ornotto/data/systemone-models.json`. Shreyan's standard Transformers
NLI fallback does not apply the unavailable author's runtime/calibration.
FluidInference's source-only toolkit and Nev Lite's missing custom runtime
remain explicitly unavailable. See the package chapter for all fifteen aliases.

## Clef and CLM

Optional `clef` uses gguf >=0.18, safetensors, NumPy, Torch and filelock to
stream quantized tensors into an atomic native decision GGUF; the original
Hub download is preserved. The tensor map and schema template are extracted
from [llama.cpp 99b95488c](https://github.com/ggml-org/llama.cpp/tree/99b95488c),
with MIT attribution in `licenses/clef-NOTICE`. The external server is b11371.
The `clef-mlx` extra uses mlx-lm 0.32 and mlx-vlm 0.7.4, on Apple silicon.
Model-local runtime code is imported only from pinned Hub snapshots.

Optional `clm` supplies Torch, NumPy, requests and llama-cpp-python >=0.3.36.
The official [contrastive-lm 0.1.0](https://github.com/Contrastive-LM/CLM) is
installed separately with `--no-deps`, avoiding its unused vLLM server. Its
Engine handles exact reference rendering, projection and probability recipes;
the adapter supplies a local GGUF or the pinned author MLX encoder. The
reference projection checkpoint is pinned to e939398d4556fcd9400c76fa8c5a513202f42b0a.
These CLM heads explicitly run on CPU; the model encoder uses Metal or MLX.

## Optional native Core AI bridge

`runtimes/coreai/build.py` fetches ClefFlash from
[john-rocky/coreai-model-zoo 2d214b3](https://github.com/john-rocky/coreai-model-zoo/tree/2d214b3d20cdd66c9a45b57e591df407b8a0147d/apps/ClefFlash)
and InformationExtractor from
[coreai-kit 7bdcc46](https://github.com/john-rocky/coreai-kit/tree/7bdcc466204bf45fc4e994994215b2c317fb5672).
SwiftPM resolves their tokenizer/graph dependencies; `Package.resolved` records
exact versions. CoreAI is the system framework on macOS 27. The only local
upstream modification makes the PII collator throw at its word/token limits.
The bridge and Python subprocess adapter retain native readouts; no extra
Python inference package is required. Source downloads stay in ignored
`.upstream/`; the bridge is built separately from the wheels.
