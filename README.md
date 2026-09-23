<!-- this_file: README.md -->

# ornotto

ornotto asks a local language model to decide, not to write. You describe a decision (pick one of these options, answer yes or no, place this on a rubric) and get back an answer with a probability for every alternative. Nothing is generated, so nothing has to be parsed, repaired or retried.

It runs two open-source C++ engines on llama.cpp and gives them one Python API:

- **dohnuts** ([dohnuts.cpp](https://github.com/DreamBlooms/dohnuts.cpp)) runs models trained for this job (decider, kev, Dohnuts) and reads their answer at a trained slot. Its probabilities are temperature-calibrated.
- **pcdServer** ([pcdServer](https://github.com/stephanj/pcdServer)) runs any chat GGUF and scores only the tokens of the answers you allow. It needs no special model.

The book at **[fontlab.org/ornotto](https://fontlab.org/ornotto/)** explains how the engines work and which model to pick, and has the benchmarks.

## Install

```sh
uv add ornotto                      # or: pip install ornotto
uv add "ornotto[pydantic-ai]"       # with the pydantic-ai integration
```

Wheels bundle both engines for macOS 14+ on Apple silicon (Metal) and for Linux x86_64 and aarch64 (manylinux_2_28, CPU only: no CUDA or Vulkan). Windows x64 wheels carry dohnuts only: pcdServer does not build on Windows yet. Elsewhere pip installs the Python code without engines: clone with `--recursive` and run `./build.sh`, or put `dohnuts-cli` and `pcd_server` on your `PATH` (or point `ORNOTTO_DOHNUTS_BIN` and `ORNOTTO_PCD_BIN` at them).

Models download from Hugging Face on first use into the usual Hugging Face cache. `HF_HUB_CACHE` moves it.

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

Each `Answer` has `value`, `probabilities`, `probability`, `confidence` and `calibrated`. `calibrated` is true for dohnuts, whose probabilities are temperature-scaled, and false for pcdServer, whose probabilities are a raw softmax over the allowed tokens. Compare confidences only between answers of the same kind.

## Pick a model and engine

```python
fast = ornotto.Decider("decider-0.8b")                    # dohnuts, the default
same_weights = ornotto.Decider("decider-0.8b", engine="pcd")
careful = ornotto.Decider("qwen3.5-4b-hmm")               # a fine-tuned chat model; pcdServer only
mine = ornotto.Decider("~/models/my-model.gguf")          # any chat GGUF, on pcdServer
remote = ornotto.Decider("decider", url="http://127.0.0.1:8298")   # an engine you started yourself
```

`ornotto models` lists the registered models:

| name | engines | family | GB | licence |
|---|---|---|---:|---|
| `decider-0.8b` | dohnuts, pcd | dedicated | 0.8 | apache-2.0 |
| `decider-2b` | dohnuts, pcd | dedicated | 2.0 | apache-2.0 |
| `kev-0.8b` | dohnuts | dedicated | 0.8 | apache-2.0 |
| `dohnuts-0.8b` | dohnuts | dedicated | 0.8 | cc-by-nc-sa-4.0 |
| `qwen3.5-0.8b`, `qwen3.5-2b`, `qwen3.5-4b` | pcd | vanilla | 0.8, 1.4, 3.0 | apache-2.0 |
| `qwen3.5-4b-hmm` | pcd | fine-tuned | 2.7 | apache-2.0 |

The engine starts on the first question, on a free loopback port, and stops when Python exits. Every `Decider` in a process that names the same model, engine and device shares one engine process. `ornotto.shutdown()` stops them all now.

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

A typed function with only a docstring becomes a decision, in the style of magentic and promptic. Its docstring is the question, and several arguments become one JSON state:

```python
@ornotto.decision
def route(request: str) -> Literal["docs", "python", "fea"]:
    """Which kind of help does this FontLab user want?"""

route("How do I open the Glyph window?")   # 'docs'
```

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
ornotto serve qwen3.5-4b-hmm --engine=pcd
```

## Develop

```sh
git clone --recursive https://github.com/fontlaborg/ornotto
cd ornotto
./build.sh                # lint, unit tests, sdist and a wheel with both engines compiled in
ENGINES=1 ./test.sh       # also the real-engine tests and examples/, one engine at a time
./publish.sh              # tag the next version, let CI build every wheel, upload with uv publish
```

The engines are git submodules in `engines/`. The version comes from git tags via hatch-vcs.

## Licence

ornotto is Apache-2.0. The wheels contain dohnuts.cpp (Apache-2.0), pcdServer, llama.cpp, cpp-httplib and nlohmann/json (MIT). Their notices are in `licenses/`. Model weights keep their own licences, listed above.
