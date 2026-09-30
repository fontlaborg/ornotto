---
this_file: src_docs/md/index.md
title: ornotto
---

<section class="fl-hero ornotto-hero" markdown="1">

ornotto
{ .ornotto-hero__eyebrow }

# Ask a local model to pick an answer, not to write one { .fl-hero__title data-toc-label="Overview" }

Give it a message and a closed set of answers. It returns the choice and a probability for every alternative, with no generated text to parse, repair or retry.

[Read the book](01-deciding.md){ .md-button .md-button--primary }
[Install the package](10-package.md){ .md-button }

![A row of tokens reaches a fork of five channels and passes into the one marked in red](img/landing-hero.png){ .ornotto-hero__img width="1376" height="768" }

</section>

<div class="ornotto-stats">
<div class="fl-card ornotto-stat">
<div class="ornotto-stat__title">Methods measured</div>
<div class="ornotto-stat__value">258</div>
<div class="ornotto-stat__desc">A model file, read one way on one engine</div>
</div>
<div class="fl-card ornotto-stat">
<div class="ornotto-stat__title">Queries</div>
<div class="ornotto-stat__value">67</div>
<div class="ornotto-stat__desc">In 30 languages, each asking for one of five tasks</div>
</div>
<div class="fl-card ornotto-stat">
<div class="ornotto-stat__title">Best local score, translated</div>
<div class="ornotto-stat__value">65/67</div>
<div class="ornotto-stat__desc">rune-26b-a4b q3, level with hosted jev</div>
</div>
<div class="fl-card ornotto-stat">
<div class="ornotto-stat__title">Fastest at 60/67 or better</div>
<div class="ornotto-stat__value">26.9 ms</div>
<div class="ornotto-stat__desc">gliner25-decide on Core AI, 61/67 translated</div>
</div>
</div>

## Three ways to decide

The package runs two open-source C++ engines on llama.cpp behind one Python API, and drives a third if you install it. [Chapter 3](03-engines.md) explains how each one reads an answer.

<div class="ornotto-grid" markdown="1">

<section class="fl-card" markdown="1">

### dohnuts

Runs models trained for this job and reads their answer at the slot they were trained to fill. decider-0.8b scores 62/67 in about 51 ms.

[How dohnuts reads an answer](03-engines.md#dohnuts)

</section>

<section class="fl-card" markdown="1">

### pcdServer

Runs any chat GGUF and scores only the tokens of the answers you allow. Qwen3.5-4B-Hmm scores 65/67 on the original text in 88 ms.

[How pcdServer constrains the answer](03-engines.md#pcdserver)

</section>

<section class="fl-card" markdown="1">

### ollaya

A separate binary with its own model registry; ornotto drives it when it is installed. Ten of its models were measured, and winnow-12b scores 65/67 on the original text.

[Setting up ollaya](10-package.md#ollaya)

</section>

</div>

## The best 15 of 258

Each row is one method, asked which of five tasks a FontLab user wants, over 67 queries in 30 languages. Click a column header to sort. [Chapter 6](06-results.md) has all 258 rows.

--8<-- "tables/top.html"

## Install and decide

```sh
uv add ornotto                      # or: pip install ornotto
uv add "ornotto[pydantic-ai]"       # with the pydantic-ai integration
```

```python
import ornotto

ornotto.choose("Build a kern feature for A V W T", ["docs", "python", "fea"]).value   # 'fea'

answer = ornotto.check("Write me a script that renames glyphs", "Does the user want code?")
answer.value, answer.probability                                                       # (True, 0.6)
```

The first call downloads decider-0.8b (0.81 GB) from Hugging Face and starts dohnuts on a loopback port. Later calls reuse both.

## What is in this book

<div class="ornotto-grid" markdown="1">

<section class="fl-card" markdown="1">

### Concepts

What a System One decision is, what you ask and what you get back, the readouts that get an answer out of a model, and how dedicated, fine-tuned and vanilla models differ.

[Chapters 1–4](01-deciding.md)

</section>

<section class="fl-card" markdown="1">

### Benchmarks

The method, the full sortable results against TypeSafe's hosted jev, and what quantization, speed, caching, confidence and fallback change.

[Chapters 5–9](05-method.md)

</section>

<section class="fl-card" markdown="1">

### The package

The API reference, typed decisions and pydantic-ai agents, and how to choose an engine and model, build from source and contribute.

[Chapters 10–12](10-package.md)

</section>

</div>
