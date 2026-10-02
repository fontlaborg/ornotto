---
this_file: src_docs/md/results/tldr.md
---

# Results: the short version

We asked 290 methods one router question: which of five tasks does a FontLab user want? There were 67 queries in 30 languages, and each method was scored twice, on English translations and on the original text. The hosted reference, jev, answered 65 of 67 either way. Rune Q5 on pcdServer matches it in both modes at 962 ms/query with CPU weights. An earlier local method matched it on translated text: rune-26b-a4b version 1 at Q3_K_M, which scored 65/67 but fell to 57/67 on the original text. Among the 4B models, Qwen3.5-4B-Hmm on pcdServer scored 64/67 and 65/67 in 88 ms, and the best small dedicated model, NeoHorse-Jev-4B, scored 64/67 in both modes in 273 ms. The fastest method at 60/67 or better is GLiNER2.5-Decide on Core AI: 61/67 on translated text in 26.9 ms.

## The top fifteen

--8<-- "tables/top.html"

## Best per engine

Scores read translated / direct, out of 67. A dash means the model reads English only.

- **dohnuts (Metal)**: decider-35b-a3b at Q4, 64 / 64 in 266 ms from 21 GB. The small decider-0.8b that `ornotto` registers scores 62 / 61 in 52 ms from 0.81 GB.
- **pcdServer**: Qwen3.5-4B-Hmm at Q8, 64 / 65 in 88 ms. The 2.7 GB Q4_K_M file scores the same in 93 ms.
- **slot (llama-server)**: rune-26b-a4b at Q3, 65 / 57 in 367 ms from 13.5 GB. pcdServer rejects its Gemma 4 files, so it runs only here.
- **ollaya**: winnow-12b, 64 / 65 in 891 ms from 12.7 GB.
- **Encoders**: GLiNER2.5-Decide on Core AI, 61 / – in 26.9 ms. laya is the only method under 10 ms with a useful score: 52/67 in 7 ms on MLX.

The full list, one row per engine and runtime, is in [chapter 6](../06-results.md#best-method-per-engine-and-runtime).

## What to pick

- **A good default**: decider-0.8b on dohnuts. It scores 62/67 in 52 ms from 0.81 GB, and its probabilities are calibrated.
- **The most accurate answer in `ornotto`**: Qwen3.5-4B-Hmm on pcdServer, 64/67 translated and 65/67 on the original text, from 2.7 GB at Q4_K_M. It needs no translator.
- **The best accuracy, if the text may leave the machine**: jev, hosted, 65/67 in 466 ms per call. `ornotto` does not call it; pydantic-ai's `TypeSafeModel` does.

[Chapter 12](../12-choosing.md#which-engine-and-model) covers the other cases, from graded answers to several questions about one message.

## Where to read more

- [Results: every table](details.md) has all 290 rows, filterable and sortable, and every other table the benchmark produced.
- [Chapter 5](../05-method.md) explains how we measured and what each column means.
- [Chapter 6](../06-results.md) reads the results model by model.
- [Chapter 7](../07-quantization.md) covers quantization and file size.
- [Chapter 8](../08-speed.md) explains where the milliseconds go.
- [Chapter 9](../09-confidence.md) tests whether the probabilities can be trusted.

Two methods within two or three queries of each other are not measurably different here. To rank models on your own decision, run them on your own labelled examples.
