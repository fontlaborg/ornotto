<!-- this_file: README.md -->

# ornotto

ornotto asks a language model to decide, not to write. You describe a decision (pick one of these options, answer yes or no, place this on a rubric) and get back an answer with a probability for every alternative. Nothing is generated, so nothing has to be parsed, repaired or retried.

It gives local engines and hosted decision models one Python API:

- **dohnuts** ([dohnuts.cpp](https://github.com/DreamBlooms/dohnuts.cpp)) runs models trained for this job (decider, kev, Dohnuts, Tev1, Jet, JPT and ThisThat) and reads their answer at a trained slot. Its probabilities follow each model's temperature recipe.
- **pcdServer** ([pcdServer](https://github.com/stephanj/pcdServer)) runs any chat GGUF and scores only the tokens of the answers you allow. It needs no special model.
- **ollaya** ([ollaya](https://github.com/ollaya-dev/ollaya)) is a separate install that runs decision models from its own registry (kev, decider, laya, winnow and others) on ONNX Runtime, llama.cpp or MLX. Each model ships its own calibration.
- **Laya MLX and xDecision** use their native encoder heads through optional Python runtimes. They support choice, yes/no and score without generated text.
- **OpenRouter** serves native choice, yes/no and score questions remotely, using the same `Decider` methods.

The book at **[fontlab.org/ornotto](https://fontlab.org/ornotto/)** explains how the engines work and which model to pick, and has the benchmarks: 309 methods over 67 queries in 30 languages, twelve chapters with diagrams, and a landing page that summarises the best results.

The [interactive explorer](https://fontlab.org/ornotto/results/explorer/) filters by accuracy floor, engine and CPU/GPU execution, with speed and weight-size Pareto frontiers. Run `python3 src_docs/gen_diagrams.py --out explorer.html` to produce an offline report from the public JSON. Rune Q5 full Metal adds 64/64 at 153.3 ms, versus 65/65 at 962.3 ms mixed; Ornith Splash is benchmark-only at 62/63 and 322.4/328.5 ms. Rune Q4 has a separate Metal run: 63/64 at 124.8 ms, against 487.1 ms with CPU weights.

## Install

```sh
uv add ornotto                      # or: pip install ornotto
uv add "ornotto[pydantic-ai]"       # with the pydantic-ai integration
```

Wheels bundle both engines for macOS 14+ on Apple silicon (Metal) and for Linux x86_64 and aarch64 (manylinux_2_28, CPU only: no CUDA or Vulkan). Windows x64 wheels carry dohnuts only: pcdServer does not build on Windows yet. Elsewhere pip installs the Python code without engines: clone with `--recursive` and run `./build.sh`, or put `dohnuts-cli` and `pcd_server` on your `PATH` (or point `ORNOTTO_DOHNUTS_BIN` and `ORNOTTO_PCD_BIN` at them).

Current `main` also supports `laya-multilingual-mlx`, `xdecision-f16` and `xdecision-q8`. Install their optional runtimes in the same Python environment (Python 3.11+):

```sh
uv pip install "ornotto[laya-mlx]"  # Apple silicon macOS
uv pip install 'xdecision[apple] @ git+https://github.com/xnetsc/xDecision.git@4082689a093393358534fda26a945699080eb572'
```

For xDecision CPU, omit `[apple]` and use `gpu=False`. These runtimes are not bundled. xDecision Q8 is smaller on disk, but MLX expands it to FP16 in memory. See the [native encoder reference](src_docs/md/10-package.md#native-encoders) for source installation and limits.

Models download from Hugging Face on first use into the usual Hugging Face cache. `HF_HUB_CACHE` moves it.

ornotto never bundles ollaya. Install it with `curl -fsSL https://ollaya.dev/install.sh | OLLAYA_INSTALL_DIR=$HOME/.local sh`; ornotto looks on `PATH`, then in `~/.local/bin`, or at `ORNOTTO_OLLAYA_BIN`. ollaya pulls its models into its own store, `OLLAYA_MODELS` (default `~/.ollaya/models`), not the Hugging Face cache.

## Decide

```python
import ornotto

ornotto.choose("Build a kern feature for A V W T", ["docs", "python", "fea"]).value
# 'fea'

answer = ornotto.check("Write me a script that renames glyphs", "Does the user want code?")
answer.value, answer.probability
# (True, 0.6)
```

Several questions about one state go in one call. The state can be text or any JSON value:

```python
decision = ornotto.decide(
    {"message": "Why does this pair look too tight?", "selection": ["A", "V"]},
    {
        "area": ornotto.choice("Which area is this about?", {
            "kerning": "space between a specific pair of glyphs",
            "sidebearings": "space built into each glyph",
        }),
        "urgent": ornotto.yes_no("Is the user blocked?"),
        "skill": ornotto.score("How experienced is the user?", ["beginner", "intermediate", "expert"]),
    },
)
decision.area.value, decision.area.probabilities, decision.skill.value
```

Each `Answer` has `value`, `probabilities`, `probability`, `confidence` and `calibrated`. `calibrated` identifies the native readout on dohnuts and ollaya; it is false for pcdServer and the new native encoders, whose task calibration is unverified. Native profiles apply their recorded temperature, which can be 1.0; the flag does not prove calibration on your task. Compare confidences only between answers of the same kind.

## Pick a model and engine

```python
fast = ornotto.Decider("decider-0.8b")                    # dohnuts, the default
same_weights = ornotto.Decider("decider-0.8b", engine="pcd")
careful = ornotto.Decider("qwen3.5-4b-hmm")               # a fine-tuned chat model; pcdServer only
mine = ornotto.Decider("~/models/my-model.gguf")          # any chat GGUF, on pcdServer
encoder = ornotto.Decider("laya-multilingual-mlx")           # optional native MLX runtime
xdecision = ornotto.Decider("xdecision-q8")                  # optional native xDecision runtime
laya = ornotto.Decider("ollaya-laya-en")                   # a registered ollaya model
any_tag = ornotto.Decider("kev:4b", engine="ollaya")       # any ollaya tag, pulled on first use
remote = ornotto.Decider("decider", url="http://127.0.0.1:8298")   # an engine you started yourself
```

`ornotto models` lists the registered models:

| name | engines | family | GB | licence |
|---|---|---|---:|---|
| `decider-0.8b` | dohnuts, pcd | dedicated | 0.8 | apache-2.0 |
| `decider-2b` | dohnuts, pcd | dedicated | 2.0 | apache-2.0 |
| `kev-0.8b` | dohnuts | dedicated | 0.8 | apache-2.0 |
| `tev1-0.8b` | dohnuts | dedicated | 0.8 | unresolved |
| `jet-4b` | dohnuts | dedicated | 4.5 | apache-2.0 |
| `this-that-1.2` | dohnuts | dedicated | 1.3 | mit |
| `jpt-4b`, `jpt-9b` | dohnuts, pcd | dedicated | 2.7, 5.6 | cc-by-nc-4.0 |
| `rune-26b-a4b` | pcd | dedicated | 13.3 | apache-2.0 |
| `dohnuts-0.8b` | dohnuts | dedicated | 0.8 | cc-by-nc-sa-4.0 |
| `qwen3.5-0.8b`, `qwen3.5-2b`, `qwen3.5-4b` | pcd | vanilla | 0.8, 1.4, 3.0 | apache-2.0 |
| `qwen3.5-4b-hmm` | pcd | fine-tuned | 2.7 | apache-2.0 |
| `jevk5-4b`, `openjev-35b-a3b` | pcd | fine-tuned | 2.7, 21.2 | apache-2.0 |
| `ollaya-kev-0.8b`, `ollaya-decider-0.8b`, `ollaya-laya-en`, `ollaya-laya-multilingual`, `ollaya-nli-modernbert-large`, `ollaya-gliclass-large`, `ollaya-von-1.1`, `ollaya-decision-eos` | ollaya | dedicated | 0.7–1.8 | apache-2.0 |
| `laya-multilingual-mlx` | laya-mlx | dedicated | 0.64 | apache-2.0 |
| `xdecision-f16`, `xdecision-q8` | xdecision | dedicated | 0.70, 0.40 | apache-2.0 |
| `ollaya-winnow-12b`, `ollaya-clm-8b` | ollaya | dedicated | 12.7, 16.5 | apache-2.0 |

JPT and ThisThat registry entries use Q4_K_M; Rune uses Q3_K_M. JPT's
non-commercial weights require their own licence review. Its Q8_0 benchmark
files were converted locally from pinned BF16 files because the requested
repositories publish no Q8. The book records their provenance. Other GGUF
quantizations can be used as local paths. On dohnuts, supply a profile JSON
such as `{"profile": "jpt", "temperature": 1.036}` for JPT 4B, or temperature
`1.087` for JPT 9B; ThisThat uses `{"profile": "thisthat", "temperature": 1.0}`.
`gpu=False` disables pcdServer GPU weights, computation and KV offload.
Build current `main` with `./build.sh` for the October registry and engine updates.

`openjev-35b-a3b` needs about 23 GB of memory, so run it with nothing else loaded. The book also benchmarks models that need their own runtimes: Bosun, NeoHorse-Jev, Jev-Omni's decision head, lev, leo, imajev, jeb, CLM, semif, and GLiNER2.5-Decide, Julia-1, von and other encoders on MLX, ONNX Runtime, Core ML and Core AI. ornotto does not run those. Of the 309 methods in the book, the mradermacher Rune Q5 on pcdServer matches hosted jev at 65/67 in both modes, with CPU weights at 962 ms/query; the registered Q3 scores 64/67 in both modes at 146 ms.

The engine starts on the first question, on a free loopback port, and stops when Python exits. Every `Decider` in a process that names the same model, engine and device shares one engine process. `ornotto.shutdown()` stops them all now.

An ollaya engine is a private `ollaya serve` on its own port. It holds one model, pulls the tag if the store lacks it, and loads it before the first question. It never touches a daemon you run on ollaya's default port. A state longer than the model's context raises `DecisionError` instead of being cut; `ollaya-laya-en` reads only 512 tokens.

## Remote decision models

Use current `main` for remote support. Set `OPENROUTER_API_KEY`, then call `ornotto.Decider("liquid/d1").choose(state, options)`.
All nine requested IDs appear in `ornotto models` and `ornotto.OPENROUTER_MODELS`; other decision IDs use `engine="openrouter"` or the `openrouter:owner/model` prefix.
Sync/async calls, typed extraction and pydantic-ai work without local models; the three Respan variants accept yes/no only. See [remote configuration, usage/cost and execution labels](src_docs/md/10-package.md#remote-openrouter-models).

## Typed decisions

A pydantic model becomes one question per field: a `Literal` or `Enum` of strings is a choice, `bool` is yes or no, and a `float` with `ge=0, le=1` is the probability of yes. The field description is the question.

```python
from typing import Literal
from pydantic import BaseModel, Field

class Triage(BaseModel):
    task: Literal["docs", "python", "fea"] = Field(description="What does the user want?")
    wants_code: bool = Field(description="Does the user want code they can run?")

ornotto.extract(Triage, "Write a Python script that renames every .sc glyph")
# Triage(task='python', wants_code=True)
```

A typed function with a docstring becomes a decision through `@ornotto.decision`; see the [typed examples](src_docs/md/10-package.md#typed-decisions).

`ornotto.classify(text, labels)` follows marvin's `classify`. These are idioms, not integrations: marvin 3 does not currently import against pydantic-ai 2.

## pydantic-ai

pydantic-ai's `TypeSafeModel` turns an agent's `output_type` into System One questions, the protocol dohnuts speaks. `ornotto.pydantic_ai.model()` points it at a local engine. For pcdServer, an in-process transport translates each request.

```python
from pydantic_ai import Agent
from ornotto.pydantic_ai import model

agent = Agent(model("decider-0.8b"), output_type=Triage, instructions="Classify a FontLab user's request.")
agent.run_sync("Build a kern feature for A V W T").output
```

Rubrics (`int` fields with a description per level), lists of options and nested models work as pydantic-ai documents them for `TypeSafeModel`.

## Command line

```sh
ornotto models
ornotto pull decider-0.8b
ornotto choose "Build a kern feature" docs python fea
ornotto check "Rename all .sc glyphs" "Does the user want code?"
```

## Develop

```sh
git clone --recursive https://github.com/fontlaborg/ornotto
cd ornotto
./build.sh                # lint, unit tests, sdist and a wheel with both engines compiled in
./docs.sh                 # build the book with the shared FontLab documentation theme
ENGINES=1 ./test.sh       # also the real-engine tests and examples/, one engine at a time (ollaya if installed)
./publish.sh              # tag the next version, let CI build every wheel, upload with uv publish
```

The engines are git submodules in `engines/`; hatch-vcs derives versions from tags.
The book sources live in `src_docs/`; Pages publishes `docs/` with the shared FontLab theme.

## Licence

ornotto is Apache-2.0. The wheels contain dohnuts.cpp (Apache-2.0), pcdServer, llama.cpp, cpp-httplib and nlohmann/json (MIT). Their notices are in `licenses/`. ollaya (Apache-2.0) is installed separately. Model weights keep their own licences, listed above.

<!-- shared-theme-integration:start -->
## Shared FontLab theme integration

This repository is part of the FontLab theme 2026 rollout: ornotto documentation with fontlab editorial chrome.
[THEME.md](THEME.md) documents its source/output boundaries, configuration,
publication route, control ownership, shared visual changes and verification.
Use the [public setup guide](https://i.fontlab.com/fltheme26/) and
[MaterialX starter](https://i.fontlab.com/fltheme26/starter.zip) for new sites.
<!-- shared-theme-integration:end -->
