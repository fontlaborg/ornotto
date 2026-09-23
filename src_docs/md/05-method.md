---
this_file: src_docs/md/05-method.md
---

# 5. How we measured

The benchmark asks one question 67 times: which of five things does this FontLab user want the built-in assistant to do? It is the router in front of the FontLab assistant, and it is the decision this book was written to get right. Every engine and model got the same 67 queries, and every answer was scored against a label we assigned before the run.

## The router question

The assistant can do five kinds of work, and each query belongs to exactly one:

| task | what the user wants |
|---|---|
| `docs` | an explanation of how a FontLab feature, tool, panel or setting works, from the documentation, not code |
| `python` | a Python script that automates FontLab: batch operations, renaming glyphs, generating files |
| `fea` | OpenType feature code in FEA syntax: `liga`, `kern`, `calt`, `ss01`, lookups, classes |
| `vfj` | a glyph definition in VFJ, FontLab's JSON glyph format: contours, nodes, components, anchors |
| `sample` | a sample text to type in the Glyph window: a pangram, test strings, glyph sequences |

The labels split 17 `docs`, 14 `fea`, 14 `sample`, 13 `python` and 9 `vfj`.

System One engines received the question as the instruction *"This message was sent to the assistant built into FontLab, the font editor. What is the user asking the assistant to do? Pick the single best match."* and each task as an option with a description of one to three sentences. Other engines needed shorter prompts, which the section on [prompts](#what-each-engine-was-asked) lists.

## The 67 queries

28 queries are in English and 39 are in 29 other languages, 30 languages in all: Polish (3); German, French, Spanish, Italian, Russian, Japanese, Chinese and Korean (2 each); and Czech, Portuguese, Dutch, Turkish, Hungarian, Finnish, Swedish, Ukrainian, Bulgarian, Greek, Armenian, Georgian, Arabic, Persian, Hebrew, Urdu, Hindi, Bengali, Thai and Vietnamese (1 each). They cover Latin with diacritics, Cyrillic, Greek, Arabic, Hebrew, Devanagari, Bengali, Thai, Georgian, Armenian, Han, Hangul and Kana.

Ten of the queries were written to be hard. They sit on the border between two tasks, and a reasonable person could hesitate over each:

- "How do I write a liga feature?" asks for an explanation (`docs`) but names FEA.
- "Give me the code that makes ff become a ligature" is `fea`, and "Script the kerning for A V" is `fea` phrased like `python`.
- "What would the JSON for a glyph look like?" is `vfj`, while "Show me how a glyph is stored in a VFJ file" is `docs`.
- "Text with lots of kerning pairs" and "Something to type in the Glyph window that shows off my ligatures" are `sample`, and so is one Polish variant.
- "Can FontLab batch rename glyphs?" is `docs`, while "Rename all glyphs in every open font, I don't want to click" is `python`.

These ten carry most of the differences between the stronger models. On "How do I write a liga feature?", 9% of all runs answered `docs`, and jev answered `fea`. [Chapter 9](09-confidence.md) lists every query with the share of runs that got it right.

## Translated and direct

Every model was scored twice.

- **Direct**: the original query goes to the classifier, in whatever language it was written.
- **Translated**: the 39 non-English queries are first translated into English, and the 28 English ones pass through unchanged.

The translated mode models a pipeline in which a small translator runs before the decision. It costs one more model and about 88 ms per non-English query. It helps weaker multilingual models most and helps the strongest ones not at all: jev scored 65/67 either way.

### Language detection

The pipeline has to know whether a query is English before it can decide to translate it. Two detectors were measured over 100 passes of the 67 queries, single-threaded, after a warm-up:

--8<-- "tables/detectors.html"

[lingua](https://github.com/pemistahl/lingua-rs) was right on 63 of 67 queries and handles 1,650 calls per second. papagan is 50 times faster and was right on 43. The majority vote, which breaks ties in lingua's favour, adds nothing to lingua alone. Its four misses: a Spanish and an English query read as Latin, a Bulgarian one as Russian, and a Hindi query full of English terms as Sotho.

### Translation

The translator is Hy-MT2-1.8B at Q4_K_M on llama-server, at temperature 0, with a prompt that names the source language and carries a short glossary. The glossary pins font-editing terms that the model otherwise paraphrased in early tests: without it, the Polish *kursywy* came back as "curve", and the German *kern-Feature* as "core feature". Terms such as `glyph`, `kerning`, `feature`, `italic`, `VFJ`, `FEA` and `Glyph window` map to themselves.

The 39 translations, with the time each took:

--8<-- "tables/translator.html"

Each query was translated once and the English text was cached, so every classifier in translated mode saw the same English.

## What each engine was asked

Engines take different request shapes, so the same decision was phrased in the shape each engine was built for:

| engine | prompt |
|---|---|
| jev, dohnuts, laya.cpp (kev), PyTorch, ExecuTorch | a System One request: the query as `state`, one `choice` question with the long instruction and the five long task descriptions as `criteria` |
| slot, decider readout | decider's trained layout, tokenized as upstream does it: `Context:` and the query, then the question, the options lettered `(A)` to `(E)` with their long descriptions, then `Answer: (` |
| slot, Hmm readout | the Qwen chat template with thinking off, options as `A: name — description` lines, and "Return only the option letter." |
| pcdServer | one enum field `task` with the choices `docs`, `python`, `fea`, `vfj`, `sample`, and a field description made of a short instruction and one short description per task |
| laya runtimes | a System One request with the short instruction and short descriptions, because the encoder shares a 1,024-token budget; the Neural Engine exports hold 96 tokens and got a compact prompt |

pcdServer cannot attach a description to each allowed value, which is why its task descriptions live in the field description. [Chapter 3](03-engines.md) explains what each engine does with its prompt.

## One model at a time

Every model was loaded alone, measured, and unloaded before the next one started. The rule comes from an accident. An early run loaded several GGUFs in one batch, next to the translator. The machine, an Apple M4 Max with 48 GB of memory, swapped its boot disk full and macOS stopped responding.

Since then the harness checks that no model process is running before it loads one. A watchdog polls every two seconds and aborts a model's run if swap grows by more than 4 GB, free space on the boot disk falls below 30 GB, available memory falls below 4 GB, or the run passes 30 minutes. With those guards in place, swap stayed flat for every model, the 35B mixture-of-experts model included.

One model at a time also makes the timings fair: no model competes with another for the GPU or for memory bandwidth.

## What the numbers mean

- **Translated** and **direct** count correct answers out of 67. A correct answer is one whose most likely option is the labelled task.
- The **English** column counts the 28 English queries in translated mode. **Other, translated** and **other, direct** count the 39 non-English queries in each mode.
- **ms/query** is the mean wall-clock time from the moment the harness sends a query to the moment it has the probabilities. For server engines it includes the HTTP round trip and JSON parsing on loopback. For jev it includes the network trip to OpenRouter. It excludes model loading and a warm-up call made before timing starts.
- **Load ms** is the time to load the model and answer the warm-up call, for runtimes that load in-process or that the harness started itself. It is blank where a server was started outside the timed step.
- **GB** is the size of the GGUF file as published on Hugging Face.

In-process runtimes (MLX, Core ML, ONNX Runtime) have no HTTP in their times, so compare their milliseconds with a server's only loosely.

## Limits

- **67 queries is a small set.** One query is 1.5 points of accuracy. Differences of one or two queries between models are within what a different set of 67 would change.
- **The labels are ours.** For the ten ambiguous queries another person could label a few differently. jev's two errors are both on ambiguous queries.
- **Thresholds are in-sample.** The confidence gates in [chapter 9](09-confidence.md) were tuned on the same 67 queries they are scored on. Expect them to do somewhat worse on new traffic.
- **One machine.** All timings come from one Apple M4 Max, on Metal where the engine supports it. CPU-only machines are several times slower: dohnuts on the CPU with eight threads took 275 ms per query against 52 ms on Metal.
- **One task.** A five-way router is one decision. Yes/no questions, rubrics and long option lists behave differently, and [chapter 2](02-decisions.md) shows examples of each.
- **Only the winner is scored.** Accuracy looks at the most likely option. It ignores how confident the model was, which matters as soon as you gate on confidence ([chapter 9](09-confidence.md)).
