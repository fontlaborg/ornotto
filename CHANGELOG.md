<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

- First release of the `ornotto` package: one System One API (choice, yes/no, score) over the dohnuts and
  pcdServer engines, a registry of dedicated, fine-tuned and vanilla models downloaded from Hugging Face,
  `extract`, `classify` and `@decision` for typed decisions, and `ornotto.pydantic_ai.model()` for
  pydantic-ai agents.
- Platform wheels bundle both engines, built statically from the `engines/` submodules. dohnuts.cpp comes
  from the fontlaborg fork, which reuses the state prefix across the rows of a request
  ([DreamBlooms/dohnuts.cpp#1](https://github.com/DreamBlooms/dohnuts.cpp/pull/1)).
- `build.sh`, `test.sh` and `publish.sh` (gitnextver tag, CI wheels, `uv publish`).
