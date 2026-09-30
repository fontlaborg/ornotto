<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

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
- Book: the benchmark grows from 208 to 258 methods with the decision models published since the first
  round: rune, winnow, NeoHorse-Jev, Jev-Omni, APUS-OpenJev, jeb, lev, leo, imajev, JevK5, semif, CLM, and
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
