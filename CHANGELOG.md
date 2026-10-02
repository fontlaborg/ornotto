<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

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
