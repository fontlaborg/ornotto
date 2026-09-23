---
this_file: src_docs/md/12-choosing.md
---

# 12. Choosing, building and contributing

The first eleven chapters describe how the engines read an answer, how the models compare, and what the package does. This one turns them into choices you make on day one: which engine and model for which job, how to build the engines if no wheel fits, how a release is made, and how to send a change upstream.

## Which engine and model

Start from what your decision needs, not from the model list. The numbers in the right-hand column are from the FontLab router benchmark ([chapter 6](06-results.md)), translated set, on an Apple M4 Max; your task will score differently, but the order tends to hold.

| If you need | Use | Why, and what it costs |
|---|---|---|
| A good default | `decider-0.8b` on dohnuts | 62/67 at 52 ms per query on Metal, 0.81 GB, calibrated probabilities. On CPU the same model takes 275 ms. |
| The most accurate local answer | `qwen3.5-4b-hmm` on pcdServer | 64/67 translated and 65/67 direct, at 88 to 93 ms, 2.7 GB at Q4_K_M. |
| The lowest latency for one model | pcdServer | Same decider-0.8b GGUF: 28 ms on pcdServer against 52 ms on dohnuts (Metal). pcdServer reads it as a chat model, though, and scores 55/67 instead of 62. |
| Non-English text without a translator | `qwen3.5-4b-hmm` on pcdServer | 65/67 on the original text. decider-0.8b drops from 62 to 61 without translation ([chapter 5](05-method.md)). |
| Several questions about one message | either | pcdServer decodes the message once and adds a short suffix per field. dohnuts reuses the state across the questions of one request since our [prefix cache](08-speed.md#prefix-caching-in-dohnuts) (1.9× on Metal, 3.2× on CPU for three questions). |
| Options that need explaining | dohnuts | Each option carries a description (`choice(..., {"name": "description"})`). pcdServer only has the field description, so ornotto folds option descriptions into it, clipped to 1,024 bytes. |
| A graded answer, and whether any level fits | dohnuts with a decider model | `score` returns the expected level; `raw["native"]` has `level_fit` and `fit_mass` per level. pcdServer has no graded type; ornotto emulates one with the choices "0", "1", … and returns their expected value. |
| Application state as JSON | dohnuts | It prints the JSON into the prompt and indexes long arrays (`_index`), so the model can refer to items by position. pcdServer gets the JSON serialized as text. |
| Any chat GGUF | pcdServer | dohnuts runs only the decider, kev and Dohnuts profiles. pcdServer scores the allowed tokens of any model with a chat template. |
| A confidence to gate on | dohnuts | Temperature-scaled probabilities. [Chapter 9](09-confidence.md) shows how a gate at 0.7 to Qwen3.5-4B-Hmm moved 60/67 to 63/67 on untranslated text. |
| Many different question sets in rotation | dohnuts, or pcdServer with a larger cache | pcdServer caches one checkpoint per question set: about 22 MB on a 0.8B model and 56 to 63 MB on a 4B one. ornotto starts it with a 512 MiB cache. |
| The best accuracy, cost no object | jev (hosted) | 65/67 at 466 ms, over the network, per call. ornotto does not call it; pydantic-ai's `TypeSafeModel` does. |

Two catches in the registry. `qwen3.5-2b` in ornotto is the Q4_K_M file, which scored 57/67; the Q3_K_M file of the same model scored 61/67 at 43 ms ([chapter 7](07-quantization.md)). If a small vanilla model is what you want, pass that file as `hf:bartowski/Qwen_Qwen3.5-2B-GGUF/Qwen_Qwen3.5-2B-Q3_K_M.gguf`. And the fastest stack in the benchmark, laya-multilingual on MLX at 7 ms and 52/67, is not in ornotto at all: it runs a different kind of model on runtimes the package does not bundle ([chapter 3](03-engines.md)).

## Building from source

You build from source to change an engine, to get a platform the wheels do not cover, or to work on ornotto itself. You need Git, CMake 3.25 or later (pcdServer's minimum), a C++20 compiler, `uv`, and network access for the first configure, when pcdServer fetches its pinned dependencies.

```sh
git clone --recursive https://github.com/fontlaborg/ornotto
cd ornotto
./build.sh
```

`build.sh` initializes the submodules, runs `ruff` and the unit tests, and builds an sdist and a wheel for your platform into `dist/`. It builds the wheel from the source tree, not from the sdist, because the sdist does not carry the engine sources. It then copies the two executables into `src/ornotto/_bin/`, where an editable install (`uv sync`) finds them.

The engines come from two git submodules:

| Submodule | Repository | Brings its own llama.cpp |
|---|---|---|
| `engines/dohnuts.cpp` | [fontlaborg/dohnuts.cpp](https://github.com/fontlaborg/dohnuts.cpp), branch `side-prefix-cache` | as a nested submodule |
| `engines/pcdServer` | [stephanj/pcdServer](https://github.com/stephanj/pcdServer) | fetched by CMake at configure time |

So a build compiles llama.cpp twice, once per engine, each at the version its engine pins. The CMake build directories live in `build-engines/` and are reused, so a second build recompiles only what changed.

### What the build hook passes to CMake

`hatch_build.py` is a hatchling build hook. It builds both engines, adds them to the wheel as `ornotto/_bin/dohnuts-cli` and `ornotto/_bin/pcd_server`, and tags the wheel `py3-none-<platform>`. Every flag it adds answers one portability problem:

| Flag | Engine | Why |
|---|---|---|
| `-DBUILD_SHARED_LIBS=OFF`, `-DDOHNUTS_STATIC=ON` | both | One self-contained executable, no llama.cpp shared libraries to ship or find at run time. |
| `-DGGML_NATIVE=OFF` | both | No `-march=native`, so the binary runs on CPUs other than the one that built it. |
| `-DGGML_OPENMP=OFF` | both | No OpenMP runtime to bundle; ggml uses its own thread pool. |
| `-DLLAMA_CURL=OFF` | both | No libcurl; ornotto downloads models itself. |
| `-DHTTPLIB_USE_<LIB>_IF_AVAILABLE=OFF` for OpenSSL, zlib, Brotli, zstd, mbedTLS and wolfSSL | pcdServer | cpp-httplib links any of these it finds on the build machine. A macOS build linked Homebrew's OpenSSL, Brotli and zstd, and would not start on a Mac without them. |
| `-DHTTPLIB_USE_NON_BLOCKING_GETADDRINFO=OFF` | pcdServer | cpp-httplib's non-blocking name lookup calls `getaddrinfo_a`, which needs libanl on the glibc 2.28 of manylinux_2_28. The server only binds a loopback port and never resolves a name. |
| `-DDOHNUTS_METAL=ON` | dohnuts, macOS | The Metal backend. pcdServer turns Metal on by itself. |
| `-DCMAKE_OSX_DEPLOYMENT_TARGET=14.0` | both, macOS | The wheel tag says `macosx_14_0`, so the binary must load on macOS 14. |
| `-DCMAKE_CXX_FLAGS=-fexperimental-library` | dohnuts, macOS | dohnuts uses `std::jthread`, which Apple's libc++ before LLVM 20 keeps behind this flag. Without it, the macOS 14 CI runner fails with `no member named 'jthread' in namespace 'std'`. |
| `-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded` | both, Windows | Static MSVC runtime, no redistributable DLLs to ship. |
| `-DCMAKE_CXX_FLAGS=/Zc:char8_t- /utf-8 /EHsc` | dohnuts, Windows | dohnuts builds llama.cpp as C++20, where `u8""` literals are `char8_t`, which llama.cpp's sources reject under MSVC. pcdServer gets `/utf-8 /EHsc` only: its nlohmann/json needs `char8_t` in C++20. |

Four environment variables steer the hook:

| Variable | Effect |
|---|---|
| `ORNOTTO_ENGINES=skip` | build a pure wheel without engines |
| `ORNOTTO_PLATFORM_TAG` | wheel platform tag; CI sets `manylinux_2_28_x86_64` and `manylinux_2_28_aarch64` |
| `ORNOTTO_BUILD_DIR` | the CMake build directory, default `build-engines/` |
| `ORNOTTO_JOBS` | parallel compile jobs, default the CPU count |

If you build the engines some other way, skip the hook and point ornotto at them with `ORNOTTO_DOHNUTS_BIN` and `ORNOTTO_PCD_BIN` ([chapter 10](10-package.md#install)).

## Tests

```sh
./test.sh                 # ruff check and format check, then the unit tests
ENGINES=1 ./test.sh       # also the real-engine tests, then every script in examples/
```

The unit tests need no engine and no model: they cover the System One and pcdServer translation, the typed helpers against a fake `Decider`, and the engine command lines. The engine tests carry the pytest marker `engine`, which the default run deselects. They load decider-0.8b on dohnuts, then on pcdServer, one engine at a time, and check that no engine is left running afterwards. They download 0.81 GB on the first run; `examples/fallback.py` adds 2.7 GB for Qwen3.5-4B-Hmm.

!!! note
    The engine tests assert the answers, not just their shape, so a model that behaves differently fails them. Two checks are looser on pcdServer: `extract` and the pydantic-ai agent assert only the type there, because decider-0.8b read as a chat model gets the short Python request in those tests wrong ([chapter 11](11-typed.md#which-model-to-put-behind-an-agent)).

## Wheels and releases

The workflow in `.github/workflows/wheels.yml` builds one wheel per platform, plus the sdist:

| Job | Runner | Output |
|---|---|---|
| Linux x86_64 | `ubuntu-24.04` in the `manylinux_2_28_x86_64` container | `manylinux_2_28_x86_64` wheel |
| Linux aarch64 | `ubuntu-24.04-arm` in the `manylinux_2_28_aarch64` container | `manylinux_2_28_aarch64` wheel |
| macOS | `macos-15` | `macosx_14_0_arm64` wheel |
| Windows | `windows-2022`, allowed to fail | `win_amd64` wheel |
| sdist | `ubuntu-24.04` | source distribution without engines |

Each wheel job installs its wheel into a fresh virtual environment and checks that both engines are found before it uploads the artifact. Building in the manylinux 2.28 containers makes the Linux wheels load on glibc 2.28 and later. Windows is best effort, because pcdServer does not document Windows support; when that job fails, a release ships without a Windows wheel.

A release runs from `./publish.sh`, which needs `UV_PUBLISH_TOKEN` (a PyPI token) and an authenticated `gh`:

1. `./build.sh` checks and builds locally.
2. `uvx gitnextver` commits any changes, tags the next version `vX.Y.Z`, and pushes the commit and the tag.
3. The tag starts the wheels workflow, whose last job attaches every wheel and the sdist to a GitHub release.
4. `publish.sh` waits for that run, downloads its artifacts and uploads them with `uv publish`.

The version comes from the tag, through hatch-vcs, so nothing in the source holds a version number. Every file in the working tree that git does not ignore goes into the release commit, because gitnextver adds them all.

## The book

This book is built from `src_docs/` with ProperDocs and the MaterialX theme, into `docs/`, which GitHub Pages serves at <https://fontlab.org/ornotto/>.

```sh
./docs.sh           # regenerate tables, build into docs/
./docs.sh serve     # live preview
```

The benchmark tables are not written by hand. The results live as JSON in `src_docs/data/`, exported from our benchmark harness: `classifiers.json` (one row per model and engine), `queries.json`, `translator.json`, `detectors.json` and `cascade.json`. `src_docs/gen_tables.py` renders them into the sortable HTML snippets in `src_docs/md/tables/`, and the chapters include those snippets. To correct a number, change the JSON and run `./docs.sh`; the build runs in strict mode and fails on a broken link or a missing snippet.

## Contributing upstream

The engines are other people's projects, and changes to them belong upstream. The dohnuts prefix cache is the worked example ([chapter 8](08-speed.md#prefix-caching-in-dohnuts)):

1. Read how the project takes changes. dohnuts.cpp had no contribution guide, template or CI when we started; its history was short imperative commit subjects, and it keeps its English and Chinese READMEs in sync.
2. Make the change in a fork, on a topic branch: [fontlaborg/dohnuts.cpp](https://github.com/fontlaborg/dohnuts.cpp), branch `side-prefix-cache`. Keep it to the code the change needs: six files, and no README edit, which would have needed a matching Chinese one.
3. Measure before and after, on both backends, and check accuracy against the project's own reference: here the upstream `scripts/compare/compare.sh` (8/8) and the f32 PyTorch decider on longer states.
4. Open the pull request with the numbers: [DreamBlooms/dohnuts.cpp#1](https://github.com/DreamBlooms/dohnuts.cpp/pull/1).

ornotto's `engines/dohnuts.cpp` submodule follows the fork's branch until the change is merged, then goes back to upstream. pcdServer is used unmodified.

The licences travel with the wheel, in its `dist-info/licenses/`:

| Component | Licence |
|---|---|
| ornotto | Apache-2.0 |
| dohnuts.cpp | Apache-2.0, with a NOTICE file |
| laya.cpp HTTP transport, inside dohnuts.cpp | MIT |
| pcdServer | MIT |
| llama.cpp and ggml | MIT |
| cpp-httplib, nlohmann/json | MIT |

Model weights are not in the wheel and keep their own licences: Apache-2.0 for every registered model except Dohnuts, which is CC-BY-NC-SA-4.0.

Changes to ornotto itself go to [fontlaborg/ornotto](https://github.com/fontlaborg/ornotto) as issues or pull requests. `./test.sh` must pass; the code style is `ruff` with a line length of 110, and every source file names its own path in a `this_file` comment.
