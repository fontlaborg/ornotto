---
this_file: src_docs/md/10-package.md
---

# 10. The ornotto package

`ornotto` is the Python side of this book. It speaks System One (a state, plus named questions of three kinds) to the local engines, starts and stops them for you, and downloads the models they need. Two engines, dohnuts and pcdServer, ship inside the wheel; a third, ollaya, is a separate install that `ornotto` drives when it finds it. This chapter is the reference: what each object takes, what it returns, and what happens underneath.

## Install

```sh
uv add ornotto                      # or: pip install ornotto
uv add "ornotto[pydantic-ai]"       # adds pydantic-ai-slim[typesafe] for chapter 11
```

Every wheel on PyPI contains `dohnuts-cli`, built from [dohnuts.cpp](https://github.com/DreamBlooms/dohnuts.cpp), and all but the Windows wheel also contain `pcd_server`, built from [pcdServer](https://github.com/stephanj/pcdServer). Both are compiled statically from the `engines/` submodules. On Windows, the pcd-only models (`qwen3.5-0.8b`, `qwen3.5-2b`, `qwen3.5-4b`, `qwen3.5-4b-hmm`) and any `engine="pcd"` raise `EngineNotFound` unless `ORNOTTO_PCD_BIN` points at a `pcd_server` you built yourself.

| Platform | Wheel tag | Backend |
|---|---|---|
| macOS 14 or later, Apple silicon | `macosx_14_0_arm64` | Metal |
| Linux x86_64, glibc 2.28 or later | `manylinux_2_28_x86_64` | CPU only (no CUDA or Vulkan) |
| Linux aarch64, glibc 2.28 or later | `manylinux_2_28_aarch64` | CPU only |
| Windows x64 | `win_amd64` | CPU; dohnuts only, because pcdServer's sources do not build on Windows yet |

You need Python 3.10 or later. The Python code is the same on every platform. Only the executables differ, so each wheel is tagged `py3-none-<platform>`.

If no wheel fits your platform, pip falls back to the source distribution, which carries no engine sources and installs the Python code alone. ornotto then looks for each engine in three places, in this order:

1. The path in `ORNOTTO_DOHNUTS_BIN` or `ORNOTTO_PCD_BIN`.
2. The copy bundled in the wheel, under `ornotto/_bin/`.
3. `dohnuts-cli` or `pcd_server` on your `PATH`.

If none of them exists, the first question raises `EngineNotFound` with the name of the variable to set. [Chapter 12](12-choosing.md#building-from-source) shows how to build both engines yourself.

### ollaya

ollaya is not in the wheel and not on PyPI: it is one Rust binary that fetches its models from its own registry. Install it without `sudo` into `~/.local`:

```sh
curl -fsSL https://ollaya.dev/install.sh | OLLAYA_INSTALL_DIR=$HOME/.local sh
```

ornotto looks for it at the path in `ORNOTTO_OLLAYA_BIN`, then on your `PATH`, then in `~/.local/bin`. If none has it, a question for an ollaya model raises `EngineNotFound` with the install command. ollaya keeps its models in its own store, `OLLAYA_MODELS` (default `~/.ollaya/models`), not in the Hugging Face cache; set that variable if your home volume has no room.

Models download from Hugging Face on first use, through `huggingface_hub`, into the ordinary Hugging Face cache. Set `HF_HUB_CACHE` (or `HF_HOME`) if your home volume has no room: decider-0.8b needs 0.81 GB, and Qwen3.5-4B-Hmm needs 2.7 GB.

## Decider

A `Decider` is one model on one engine. Creating one resolves the model (downloading it if needed) but does not start the engine. The engine starts on the first question.

```python
import ornotto

fast = ornotto.Decider("decider-0.8b")                        # dohnuts, the default engine for this model
same = ornotto.Decider("decider-0.8b", engine="pcd")          # the same weights on pcdServer
mine = ornotto.Decider("~/models/my-model.gguf")              # any chat GGUF, on pcdServer
hf   = ornotto.Decider("hf:bartowski/Qwen_Qwen3.5-2B-GGUF/Qwen_Qwen3.5-2B-Q4_K_M.gguf")
up   = ornotto.Decider("decider", url="http://127.0.0.1:8298") # an engine you started yourself
laya = ornotto.Decider("ollaya-laya-multilingual")             # a registered ollaya model
tag  = ornotto.Decider("ollaya:kev:4b")                        # any ollaya tag; same as Decider("kev:4b", engine="ollaya")
```

| Argument | Default | Meaning |
|---|---|---|
| `model` | `"decider-0.8b"` | A registered name, a local `.gguf` path (`~` expands), `hf:owner/repo/file.gguf`, or an ollaya tag as `ollaya:<tag>`. |
| `engine` | first engine the model supports | `"dohnuts"`, `"pcd"` or `"ollaya"`. With `"ollaya"`, a plain tag such as `kev:4b` also works. Asking a model for an engine it cannot run raises `ValueError`. |
| `url` | `None` | Talk to a running engine at this base URL instead of starting one. `engine` then defaults to `"dohnuts"`, and `model` is only a label. |
| `gpu` | `True` on macOS, `False` elsewhere | Offload all layers to the GPU. The bundled macOS build has Metal; the Linux and Windows builds are CPU only. Affects dohnuts; pcdServer offloads to Metal by itself. |
| `metadata` | `None` | The dohnuts profile JSON (`decider.json`, `kev.json`, `dohnuts.json`) for a model that is not registered. Without it, an unregistered GGUF runs on pcdServer only. |
| `head` | `None` | The scorer head for kev or Dohnuts, when the model is not registered. |
| `timeout` | `60.0` | Seconds to wait for one answer. |

A `Decider` has four methods, plus an async one. Each takes the `state` you ask about: a string, or any JSON value (a dict, a list, numbers).

| Method | Asks | Returns |
|---|---|---|
| `decide(state, questions)` | named questions, in one call | `Decision` |
| `choose(state, options, question=None)` | pick one of `options` | `Answer` |
| `check(state, question, *, yes=None, no=None)` | yes or no | `Answer` |
| `rate(state, question, levels)` | a level on a rubric | `Answer` |
| `adecide(state, questions)` | `decide`, for asyncio | `Decision` |

`options` is a list of names or a mapping of name to description. `levels[i]` describes level `i`. `yes` and `no` optionally say what counts as each answer.

The `url` property returns the engine's base URL, starting the engine if needed. Use it when you want to call the engine's HTTP API directly.

## Module functions

The module functions use one shared `Decider`, created on first use from the arguments of the last `ornotto.use()` call.

| Function | Same as |
|---|---|
| `ornotto.decide(state, questions)` | `Decider.decide` |
| `ornotto.choose(state, options, question=None)` | `Decider.choose` |
| `ornotto.check(state, question, *, yes=None, no=None)` | `Decider.check` |
| `ornotto.rate(state, question, levels)` | `Decider.rate` |
| `ornotto.use(model="decider-0.8b", *, engine=None, **kwargs)` | sets the shared Decider's arguments; the next call creates it again |
| `ornotto.default()` | returns the shared Decider |
| `ornotto.shutdown()` | stops every engine this process started |

```python
ornotto.use("qwen3.5-4b-hmm")        # every module function now runs Qwen3.5-4B-Hmm on pcdServer
ornotto.choose("Kern the class of round lowercase letters against the period",
               ["kern pair", "kern class", "class definition"])
```

## Questions

`decide` takes a mapping from question name to question. The name you choose comes back as the key of the answer. Build questions with three functions:

```python
ornotto.choice("What does the user want?", {"docs": "an explanation from the manual",
                                             "python": "a script", "fea": "feature code"})
ornotto.yes_no("Does the user want code they can run?", yes="runnable code", no="an explanation")
ornotto.score("How urgent is it?", ["can wait", "this week", "today"])
```

| Builder | System One type | Rules |
|---|---|---|
| `choice(instructions, options)` | `choice` | at least two options; `options` is a list of names or a name → description mapping |
| `yes_no(instructions, *, yes=None, no=None)` | `noul` | `yes` and `no` are optional descriptions |
| `score(instructions, levels)` | `score` | at least two levels, in order from level 0 |

You can also pass a System One question as a plain dict, as the jev API and dohnuts accept it: `{"type": "choice", "instructions": "...", "criteria": {...}}`. `question` is accepted for `instructions`, `options` for `criteria`, and `bool` for `noul`. A `score` whose criteria are keyed by numbers (`{"0": ..., "1": ...}`) is sorted numerically. Instructions and criteria may be JSON values; ornotto turns them into text.

### Limits per request

dohnuts takes at most 64 questions per request (ornotto starts it with `--max-questions 64`; the server default is 8), ollaya 256, and pcdServer at most 63 fields. If you ask more, your `Decider` splits them into several requests and merges the answers into one `Decision`. For pcdServer, ornotto also checks the 64 KiB state limit before it sends anything and clips each question's text, option descriptions included, to 1,024 bytes. [Chapter 2](02-decisions.md#limits) lists every limit of both engines.

## Answers

An `Answer` is one answer. Its fields mean slightly different things for the three kinds of question you can ask.

| Field | choice | yes/no | score |
|---|---|---|---|
| `kind` | `"choice"` | `"noul"` | `"score"` |
| `value` | the option name | `True` when p(yes) ≥ 0.5 | the expected level, a float |
| `probabilities` | per option | `{"false": p, "true": p}` | per level, keyed `"0"`, `"1"`, … |
| `probability` | of the chosen option | of yes | of the most likely level |
| `confidence` | of the chosen option | max(p(yes), p(no)) | of the most likely level |
| `level` | raises `AttributeError` | raises `AttributeError` | the most likely level, an int |
| `raw` | the engine's answer as a dict | same | same |

`bool(answer)` is `bool(answer.value)`, so `if ornotto.check(text, "Is it spam?"):` reads as it should.

`calibrated` says what kind of number the probabilities are. It is `True` for dohnuts, whose models divide their logits by a temperature fitted during training before the softmax, so a 0.8 should be right about 80 percent of the time, and for ollaya, which ships a calibration with every model. It is `False` for pcdServer, whose probabilities are a plain softmax over the first tokens of the allowed answers. Both are fine for picking the winner. They are not interchangeable as confidences: compare a dohnuts 0.8 only with another dohnuts 0.8. [Chapter 9](09-confidence.md) shows how well the calibration held up on our benchmark.

`raw` keeps everything the engine sent, including fields ornotto does not model. From dohnuts that includes `native.confidence` (the top probability) and `native.certainty` (1 − H/ln K); for isolated scores it adds `native.level_fit` and `native.fit_mass`.

A `Decision` holds all answers to one request. It is a read-only mapping from question name to `Answer`, and it also answers attribute access:

```python
d = ornotto.decide("Rename every .sc glyph to .smcp in all open fonts", {
    "task": ornotto.choice("What does the user want?", ["docs", "python", "fea"]),
    "code": ornotto.yes_no("Does the user want code they can run?"),
})
d.task.value, d["code"].probability, d.to_dict()
```

| Field | Meaning |
|---|---|
| `answers` | the dict of answers |
| `model` | the model name |
| `engine` | `"dohnuts"`, `"pcd"` or `"ollaya"` |
| `usage` | numeric usage fields summed over the requests, for example `input_tokens` from dohnuts or `elapsed_ms` from pcdServer |
| `ms` | client wall-clock time for the whole call, engine start excluded |
| `to_dict()` | just the values, by question name |

## Async

`adecide` is `decide` for asyncio. It uses `httpx.AsyncClient`, so many decisions can be in flight at once. The first call may block briefly while the engine starts: starting a process and waiting for it to load a model is not asynchronous.

```python
import asyncio

async def main():
    d = ornotto.Decider("decider-0.8b")
    texts = ["How do I open the Glyph window?", "Build a kern feature for A V"]
    q = {"task": ornotto.choice("What does the user want?", ["docs", "python", "fea"])}
    return await asyncio.gather(*(d.adecide(t, q) for t in texts))

asyncio.run(main())
```

`ornotto.aextract` is the async form of `extract` ([chapter 11](11-typed.md)).

## Engine lifecycle

The engine is a local HTTP server that ornotto runs as a child process. You never start it by hand unless you want to.

1. The first question asks `Decider.url`, which calls `Server.shared(engine, model, gpu)`.
2. ornotto binds a socket to `127.0.0.1` on port 0 to get a free port, and starts the engine on that port, loopback only.
3. The engine's stdout and stderr go to a log file in the temp directory, named `ornotto-<engine>-<port>.log`. A file never fills up and blocks the engine the way a full pipe would.
4. ornotto polls `/health` every 0.2 s until the model is loaded, for up to 180 s. If the process exits first, the error includes the last 2,000 characters of its log.
5. At interpreter exit, an `atexit` handler stops every engine: terminate, wait 10 s, then kill.

An ollaya engine is a private `ollaya serve` on its own loopback port, so it never touches an ollaya daemon you run yourself on ollaya's default port. ornotto starts it holding one model and keeping it loaded, waits until `/` answers, pulls the tag if the store lacks it, and loads the model through `/api/decide` before the first question, allowing up to 600 s for that load. At exit it stops the server with `ollaya stop`. Your `OLLAYA_*` settings, such as `OLLAYA_MODELS` and `OLLAYA_DEVICE`, pass through, except that ornotto sets the address, the one-model limit and the keep-alive itself and leaves out `OLLAYA_API_KEY` and `OLLAYA_LOG_DIR`.

Every `Decider` in the process that names the same engine, model files and GPU setting shares one engine process. Opening `Decider("decider-0.8b")` twice costs one load. If the process died, the next question starts a new one.

!!! warning "Memory"
    Each engine holds its model in memory for as long as it runs. Two Deciders on different models are two processes, both resident. `ornotto.shutdown()` stops them all at once.

## Registered models

`ornotto.MODELS` maps names to `ModelSpec` records. `ornotto models` prints the same list, with sizes rounded to one decimal and licence ids in lowercase.

| Name | Engines | Family | GB | Licence | Source |
|---|---|---|---:|---|---|
| `decider-0.8b` | dohnuts, pcd | dedicated | 0.81 | Apache-2.0 | [DreamBlooms/decider-0.8b-GGUF](https://huggingface.co/DreamBlooms/decider-0.8b-GGUF) |
| `decider-2b` | dohnuts, pcd | dedicated | 2.0 | Apache-2.0 | [DreamBlooms/decider-2b-GGUF](https://huggingface.co/DreamBlooms/decider-2b-GGUF) |
| `kev-0.8b` | dohnuts | dedicated | 0.81 | Apache-2.0 | [DreamBlooms/kev-0.8b-GGUF](https://huggingface.co/DreamBlooms/kev-0.8b-GGUF) |
| `dohnuts-0.8b` | dohnuts | dedicated | 0.81 | CC-BY-NC-SA-4.0 | [DreamBlooms/Dohnuts-0.1.0-0.8B-GGUF](https://huggingface.co/DreamBlooms/Dohnuts-0.1.0-0.8B-GGUF) |
| `qwen3.5-0.8b` | pcd | vanilla | 0.83 | Apache-2.0 | [ggml-org/Qwen3.5-0.8B-GGUF](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF) |
| `qwen3.5-2b` | pcd | vanilla | 1.4 | Apache-2.0 | [bartowski/Qwen_Qwen3.5-2B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-2B-GGUF) |
| `qwen3.5-4b` | pcd | vanilla | 3.0 | Apache-2.0 | [bartowski/Qwen_Qwen3.5-4B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3.5-4B-GGUF) |
| `qwen3.5-4b-hmm` | pcd | fine-tuned | 2.7 | Apache-2.0 | [n4ze3m/Qwen3.5-4B-Hmm](https://huggingface.co/n4ze3m/Qwen3.5-4B-Hmm) |
| `jevk5-4b` | pcd | fine-tuned | 2.7 | Apache-2.0 | [alibiserikbay/JevK5-GGUF](https://huggingface.co/alibiserikbay/JevK5-GGUF) |
| `openjev-35b-a3b` | pcd | fine-tuned | 21.2 | Apache-2.0 | [apus-ailab/APUS-OpenJev-v1-35B-A3B-GGUF](https://huggingface.co/apus-ailab/APUS-OpenJev-v1-35B-A3B-GGUF) |
| `ollaya-kev-0.8b` | ollaya | dedicated | 1.8 | Apache-2.0 | ollaya `kev:0.8b` |
| `ollaya-decider-0.8b` | ollaya | dedicated | 1.5 | Apache-2.0 | ollaya `decider:0.8b` |
| `ollaya-laya-en` | ollaya | dedicated | 0.9 | Apache-2.0 | ollaya `laya:en` |
| `ollaya-laya-multilingual` | ollaya | dedicated | 0.7 | Apache-2.0 | ollaya `laya:multilingual` |
| `ollaya-nli-modernbert-large` | ollaya | dedicated | 0.8 | Apache-2.0 | ollaya `nli:modernbert-large` |
| `ollaya-gliclass-large` | ollaya | dedicated | 1.8 | Apache-2.0 | ollaya `gliclass:large` |
| `ollaya-von-1.1` | ollaya | dedicated | 1.6 | Apache-2.0 | ollaya `von:1.1` |
| `ollaya-decision-eos` | ollaya | dedicated | 1.5 | Apache-2.0 | ollaya `decision:eos` |
| `ollaya-winnow-12b` | ollaya | dedicated | 12.7 | Apache-2.0 | ollaya `winnow:12b` |
| `ollaya-clm-8b` | ollaya | dedicated | 16.5 | Apache-2.0 | ollaya `clm:8b` |

The registry files `jevk5-4b` and `openjev-35b-a3b` as fine-tuned pcdServer models; the benchmark tables count them as dedicated, because each has a trained letter readout of its own ([chapter 4](04-models.md#later-dedicated-models)). The dedicated GGUF models are Q8_0; the Qwen chat models, JevK5 and APUS-OpenJev are Q4_K_M, except the 0.8B, which is Q8_0. `openjev-35b-a3b` needs about 23 GB of memory, so run it with nothing else loaded. An ollaya model is its registry tag, and its size is ollaya's download; ollaya picks the runtime and precision for each tag. On the router benchmark, `ollaya-winnow-12b` scored 64/67 and `ollaya-decider-0.8b` 61/67, while `ollaya-clm-8b`, `ollaya-gliclass-large` and `ollaya-nli-modernbert-large` scored 39, 26 and 20 ([chapter 6](06-results.md)). Every other tag in ollaya's registry works as `ollaya:<tag>`. For dohnuts, a dedicated model also downloads its profile JSON, and kev and Dohnuts download a scorer head. The Dohnuts weights are for non-commercial use only. [Chapter 4](04-models.md) explains the three families, and [chapter 12](12-choosing.md) which to pick.

`ornotto.DEFAULT_MODEL` is `"decider-0.8b"`.

## Errors

| Exception | Raised when |
|---|---|
| `EngineNotFound` | the engine executable is not in the environment variable, the wheel or `PATH` (for ollaya: the variable, `PATH` or `~/.local/bin`) |
| `DecisionError` | the engine answered with an HTTP status other than 200; the message carries the status and the first 500 characters of the body. ollaya's `422 STATE_TRUNCATED` says that the state is longer than the model's context; `ollaya-laya-en` reads only 512 tokens |
| `ValueError` | a question has fewer than two options or levels; a model does not run on the requested engine; an unregistered GGUF asks for dohnuts without `metadata`; the state for pcdServer exceeds 64 KiB |
| `FileNotFoundError` | the model is neither a registered name nor a file; the message lists the registered names |
| `RuntimeError`, `TimeoutError` | the engine exited while loading, or did not load within 180 s; the message names the log file |
| `httpx.HTTPError` | the connection to the engine failed |

## Command line

The `ornotto` command wraps the same API. Each command prints its result, as JSON where it returns an answer.

| Command | Does |
|---|---|
| `ornotto models` | list the registered models |
| `ornotto pull NAME` | download a model and its metadata and print the GGUF path; for an ollaya model, pull the tag into `OLLAYA_MODELS` |
| `ornotto choose STATE OPTION... [--model=] [--engine=] [--question=]` | pick one option |
| `ornotto check STATE QUESTION [--model=] [--engine=]` | answer yes or no |
| `ornotto serve [NAME] [--engine=]` | start an engine, print its URL, run until ++ctrl+c++ |
| `ornotto version` | print the package version |

```sh
ornotto choose "Build a kern feature for A V W T" docs python fea
ornotto serve qwen3.5-4b-hmm --engine=pcd
ornotto pull ollaya-kev-0.8b
ornotto choose "Build a kern feature for A V W T" docs python fea --model=kev:4b --engine=ollaya
```

`ornotto serve` is the easy way to get a server that another process can reach. Pass its URL to `Decider(url=...)`, or point any System One client at it if the engine is dohnuts or ollaya.
