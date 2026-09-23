---
this_file: src_docs/md/index.md
---

# ornotto

ornotto asks a local language model to pick an answer, not to write one. You give it a state (a message, or any JSON value) and a question with a closed set of answers: one of these options, yes or no, or a level on a rubric. It returns the answer and a probability for every alternative. Because nothing is generated, there is no output to parse, repair or retry, and decider-0.8b answers in about 52 ms on an Apple M4 Max.

The package runs two open-source C++ engines on llama.cpp behind one Python API. [dohnuts.cpp](https://github.com/DreamBlooms/dohnuts.cpp) runs models trained for this job and reads their answer at a trained slot. [pcdServer](https://github.com/stephanj/pcdServer) runs any chat GGUF and scores only the tokens of the answers you allow. This book explains how both work, compares them with TypeSafe's hosted jev model and with other local engines and runtimes on 67 real queries, and documents the package.

## Install

```sh
uv add ornotto                      # or: pip install ornotto
uv add "ornotto[pydantic-ai]"       # with the pydantic-ai integration
```

## Decide

```python
import ornotto

ornotto.choose("Build a kern feature for A V W T", ["docs", "python", "fea"]).value   # 'fea'

answer = ornotto.check("Write me a script that renames glyphs", "Does the user want code?")
answer.value, answer.probability                                                       # (True, 0.6)
```

The first call downloads decider-0.8b (0.81 GB) from Hugging Face and starts dohnuts on a loopback port. Later calls reuse both.

## The best 15 of 208

Each row is one method, a model file read one way, asked which of five tasks a FontLab user wants, over 67 queries in 30 languages. Click a column header to sort. [Chapter 6](06-results.md) has all 208 rows.

--8<-- "tables/top.html"

## What is in this book

- **Concepts.** [Chapter 1](01-deciding.md) says what a System One decision is. [Chapter 2](02-decisions.md) covers what you ask and what you get back. [Chapter 3](03-engines.md) shows the five readouts that get an answer out of a model, and defines the terms the rest of the book uses. [Chapter 4](04-models.md) covers dedicated, fine-tuned and vanilla models.
- **Benchmarks.** [Chapter 5](05-method.md) is the method. [Chapter 6](06-results.md) has the full sortable results. [Chapter 7](07-quantization.md) covers quantization, [chapter 8](08-speed.md) speed and caching, and [chapter 9](09-confidence.md) confidence and fallback.
- **The package.** [Chapter 10](10-package.md) is the API reference. [Chapter 11](11-typed.md) covers typed decisions and pydantic-ai agents. [Chapter 12](12-choosing.md) is about choosing an engine and model, building from source and contributing.
