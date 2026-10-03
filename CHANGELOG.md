<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

- Add the optional native macOS 27 Core AI bridge for pinned Clef-Flash FP16/int8mix joint-schema decisions and GLiNER2 PII entity spans/redaction. Preserve native heads and confidence, serialize persistent requests, bound pipe waits and reject PII word/token overflow.
- Publish the separate 20-text PII smoke benchmark: 20 exact entity sets, 27 true positives, no false positives/negatives, 12.5 ms mean warm latency. Retain all 329 router configurations and the full cache unchanged. Clef Core AI inference remains unmeasured: FP16/int8mix preflight requires 36/30 GiB available against 22 GiB at check.

- Add fourteen pinned Clef, Clef-Flash and CLM GGUF/MLX configurations with native joint-schema or contrastive heads, managed lifecycle, full-input rejection and optional runtime installs. Attach official Clef heads to backbone-only GGUFs without changing quantized tensor bytes; keep joint questions in one prefill.
- Publish nine complete new configurations (329 total), preserving all 320 earlier rows. Clef-Flash Q3 scores 62/64 translated/direct; Q4/Q5/Q6 each 63/64; MLX 4-bit 63/63. The four CLM variants score 36/38/38/39 translated. Five larger configurations have support and pinned downloads but no measurement after the unchanged RAM preflight refused them.
- Remove failed-only downloads and downloaded weights whose best completed score is below 50/67, including the four newly measured CLM variants. Retain low-scoring benchmark rows, cached probabilities, translations and shared weights used by stronger configurations; keep failed/refused executions out of rankings.

- Register all fifteen requested System One repositories with pinned artifacts and compatible readouts. Add native Rune llama-server, Raz NLI, Lite, Bosun/OOMU, mpuig MLX, Gemma letter-slot and ONNX scalar adapters, plus an experimental external CoreAIKit integration. Gold/Distilled/ZeroShot explicitly use standard Transformers NLI without the unavailable author calibration; FluidInference's missing weights and Nev Lite's missing runtime fail before downloading.
- Publish eleven complete new configurations (320 total), retaining all 309 historical rows exactly. MiniCPM5 Q8 scores 62/59 translated/direct at 141.8/147.2 ms; CPU ONNX Q4 scores 53/67 at 1410.8 ms. CoreAI startup tripped the memory watchdog and Rune v3's native run was deferred; neither receives an invented score. Preserve the earlier Rune Q3 slot measurement and the single Jev model identity.

- Correct the two Jev runs to one TypeSafe model identity and OpenRouter engine. Retain both original measurements in the 309-run archive and ten-run remote table; show Jev once in homepage rankings. The earlier resolved build remains unlogged.

- Add the complete Weidows Q8/MPS-head comparison (309 configurations): 52/49 at 45.9/75.9 ms, identical saved probabilities to the retained CPU head but slower measured means. Preserve all 308 prior rows and the direct-mode outlier; record pinned encoder/head storage provenance only for the new row.

- Add three GPU provider/head comparisons (308 configurations), retaining all 305 earlier rows: GLiNER Core ML CPU/GPU 61/67 at 21.9 ms; Jev-Omni pooled MLX 64/64 at 908.4/904.4 ms; Neutron MPS 54/51 at 50.3/49.4 ms, a measured slowdown. Failed ONNX/CoreML attempts are excluded and explained.

- Add optional native Laya MLX and xDecision engines, three registered models, managed loopback lifecycle, CPU/GPU selection, sync/async and typed/pydantic-ai consumers. Preserve native heads, action and usage, reject invalid probabilities and reported truncation, and keep calibration unverified. xDecision uses a separately installed pinned runtime; its Q8 MLX weights expand to FP16 at load.
- Measure three complete native encoder configurations (318 distinct-input records): Laya MLX 52/49 at 11.4/11.2 ms, xDecision F16 44/43 at 14.9/15.1 ms, Q8 45/43 at 14.3/14.2 ms translated/direct. Export 305 configurations, preserving all 302 earlier rows and translations, with separate native engine filters, GPU evidence and pinned weight provenance.

- Add two complete local configurations while preserving all 300 prior rows: Rune Q5 full Metal (64/64, 153.3/152.8 ms) and Ornith Splash (62/63, 322.4/328.5 ms translated/direct). Add the Splash Metal engine and native-choice readout, package storage provenance, updated charts and explicit failed/refused/deferred exclusions. Q5 is 6.3 times faster but loses one correct answer in each mode.

- Add full translated/direct benchmarks for all nine OpenRouter endpoints: 954 successful unique-input requests, 300 public runs, and all 291 earlier rows unchanged. Add the OpenRouter API engine filter, explicit native-choice/noul OVR readouts, resolved versions, remote timing tables and CSV fields. Generate the homepage ranking from benchmark data.

- Verify all nine remote endpoints with authenticated requests. Record and enforce Respan's noul-only capability, including its pydantic-ai boolean bridge; unsupported choice/score calls fail before HTTP.

- Add nine registered OpenRouter decision models and arbitrary decision IDs through `engine="openrouter"`. Support sync/async questions, typed extraction, CLI discovery and pydantic-ai without local weights or server processes. Authenticate with `OPENROUTER_API_KEY` or an explicit key; retain usage/cost, provider and resolved model, reject malformed answers and report network/API failures without automatic retries. Remote calibration remains unrecorded.

- Generate benchmark CSS and JavaScript filenames from content hashes during the docs build so CDN caches cannot mix old scripts with new explorer markup. Report initialization failures visibly instead of leaving the loading message. Verified the deployed charts, filters, downloads and mobile layout.

- Add a separately cached Rune Q4 Metal run: 124.8 ms/query, 63/67 translated and 64/67 direct, versus 487.1 ms with CPU weights. Retain all 290 earlier measurements; 291 runs are now published.
- Label every benchmark configuration with CPU/GPU execution and evidence, including mixed, Neural Engine, automatic and remote cases. Identify 19 CPU-only and 19 mixed CPU/GPU runs.
- Add a reproducible interactive diagram tool, speed and weight-size Pareto frontiers, adjustable accuracy floors, mode-specific timings, shared filter URLs, CSV/SVG exports and an offline HTML download.

- Complete issue 102 measurements: 32 new methods over all 24 weight variants; 290 public rows, with the original 258 unchanged. JPT 4B/9B Q8 are local conversions of pinned BF16 files with public hash manifests. mys Kev Q4/Q8 use ggmlc because dohnuts rejects their architecture.
- Register Tev1, Jet, ThisThat 1.2, JPT 4B/9B and mradermacher Rune; bundle missing native profiles and honor explicit metadata/head overrides. JPT weights are non-commercial; Tev1's release licence remains unresolved.
- Bundle dohnuts fork `dbf48c0` with verified native JPT/Jet prompts and label mappings, and pcdServer fork `1046a00` with Jinja template fallback, BOS deduplication and CPU-only execution. `gpu=False` now controls pcdServer offload. Native temperature application is documented without claiming calibration on an unseen task.
- Rune Q5 reaches 65/67 in both modes with CPU weights; update all book tables, the landing chart and recommendations from the final exported data. Preserve older runtime measurements.

## 0.1.2 (2026-09-30)

- Landing page redesigned as an editorial composition: two-column hero with a generated illustration,
  a three-step "How a decision works" strip, a typographic numbers row, a pull quote, a bar chart of the
  eight best methods with the top-15 table collapsed beneath it, alternating engine rows, a twelve-chapter
  map and a two-line install. Sidebars are hidden on the home page only.
- Book expanded from about 26,000 to 47,000 words in the FontLab neutral voice: the September 2026 context
  (jev launch, OpenAI Decision API, Liquid d1, ollaya, pydantic-ai 2.50), attributed anecdotes, third-party
  benchmark numbers in separate tables, licence warnings, 19 Mermaid diagrams (readout families, model
  family tree, method flowchart, quant chart, memory decision tree) and five generated illustrations.
- Diagrams render at full size with `useMaxWidth: false`, wide ones scroll inside their own box, and their
  colours follow the site theme in light and dark mode through the `--md-mermaid-*` variables.
- ollaya review follow-ups: Deciders that differ only in `gpu` share one ollaya server, a missing tag raises
  instead of asserting, and the `pull` and `models` commands have tests.
- New engine `ollaya`: ornotto starts a private `ollaya serve` on a free loopback port (one model, kept
  loaded, `OLLAYA_MODELS` inherited), pulls the tag if the store lacks it, preloads it through
  `/api/decide`, and stops it with `ollaya stop`. Requests go to `/v1/systemone` unchanged; answers are
  calibrated. ollaya is found on `PATH`, in `~/.local/bin` or at `ORNOTTO_OLLAYA_BIN`, and is never bundled.
- Ten registered ollaya models (`ollaya-kev-0.8b`, `ollaya-decider-0.8b`, `ollaya-laya-en`,
  `ollaya-laya-multilingual`, `ollaya-nli-modernbert-large`, `ollaya-gliclass-large`, `ollaya-von-1.1`,
  `ollaya-decision-eos`, `ollaya-winnow-12b`, `ollaya-clm-8b`). Any other tag works as `ollaya:<tag>`, or as
  a plain tag with `engine="ollaya"`.
- Two new pcdServer models: `jevk5-4b` (JevK5 v0.3 Q4_K_M) and `openjev-35b-a3b` (APUS-OpenJev v1 Q4_K_M).
- A `422 STATE_TRUNCATED` reply becomes a `DecisionError` that says the state is longer than the model's
  context.
- The pydantic-ai provider talks to ollaya directly and sends the tag as the model name.
- CLI: `--engine=ollaya`, `ornotto pull` for ollaya models, and a wider `ornotto models` table.
- Book: the benchmark grows from 208 to 258 methods with decision models the first round did not
  cover: rune, winnow, NeoHorse-Jev, Jev-Omni, APUS-OpenJev, jeb, lev, leo, imajev, JevK5, semif, CLM, and
  the encoders GLiNER2.5-Decide, Julia-1, von, decima-small, Pulse Decide, Lumma and new laya builds, on
  ollaya, the authors' System One servers, llama.cpp embeddings with a head, MLX, ONNX Runtime, Core ML
  and Core AI. Chapters 3 (new readouts), 4 (the later dedicated models and their licences), 5, 6, 7, 8,
  9, 10 (ollaya), 12 (new recommendations) and the index are updated from the exported data.
- Book tables: rows with a licence note show a dagger and a tooltip; an empty direct cell marks a model
  trained on English only; the caption counts the rows; the quantization grid knows the MLX, MXFP and
  exact GGUF labels.
- Match the shared FontLab documentation design: global menu/footer, section
  tabs, five visual themes, collapsible contents and local search at every width.
- Preserve chapter links and book licence text above the global footer.

## 0.1.1 (2026-09-24)

- First release of the `ornotto` package: one System One API (choice, yes/no, score) over the dohnuts and
  pcdServer engines, a registry of dedicated, fine-tuned and vanilla models downloaded from Hugging Face,
  `extract`, `classify` and `@decision` for typed decisions, and `ornotto.pydantic_ai.model()` for
  pydantic-ai agents.
- Platform wheels bundle both engines, built statically from the `engines/` submodules. dohnuts.cpp comes
  from the fontlaborg fork, which reuses the state prefix across the rows of a request
  ([DreamBlooms/dohnuts.cpp#1](https://github.com/DreamBlooms/dohnuts.cpp/pull/1)).
- `build.sh`, `test.sh` and `publish.sh` (gitnextver tag, CI wheels, `uv publish`).
- Wheels: macOS 14+ arm64 (Metal), manylinux_2_28 x86_64 and aarch64 (CPU). Windows x64 wheels carry
  dohnuts only, because pcdServer does not build with MSVC yet.
