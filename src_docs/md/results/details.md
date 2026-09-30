---
this_file: src_docs/md/results/details.md
---

# Results: every table

This page collects every table the benchmark produced, with enough context to read each one on its own. The chapters that discuss them carry the same tables beside the argument. Every number comes from one run on one 48 GB Mac, on one 67-query router question; [chapter 5](../05-method.md) describes the run. For the headline figures, start at [Results: the short version](tldr.md).

Scores count correct answers out of 67. **Translated** means the 39 non-English queries were first translated into English; **direct** means the classifier got the original text. **ms/query** is the mean wall-clock time per query, without model loading. [Chapter 5](../05-method.md#what-the-numbers-mean) defines every column.

Most tables sort when you click a column header; click again to reverse the order.

## All 258 methods

A method is one model file, read one way, on one engine or runtime. This is every method that finished, best first. Five more failed and are left out; [chapter 6](../06-results.md#every-method) says why.

Type in the box to keep only the rows that contain every word you type: `pcdServer hmm` keeps the Hmm model on pcdServer, and `dedicated Metal` keeps the dedicated models on dohnuts (Metal).

!!! note "How to read this table"
    - **An empty direct cell** means the model was trained on English only and received the translated text alone. An empty GB or load cell means the value was not measured or does not apply, for example the size of a hosted model.
    - **†** after a method marks a licence note. Hover over the method to read it.
    - **English** counts the 28 English queries in translated mode. **Other, translated** and **other, direct** count the 39 non-English queries in each mode.

--8<-- "tables/classifiers.html"

## One set of weights on several engines

An engine is not a neutral container. This table puts the same model file side by side on every engine that ran it. decider-0.8b scores 61 or 62 through its own trained readout on dohnuts and llama-server, but 55 on pcdServer, which reads it as a chat model. [Chapter 6](../06-results.md#one-set-of-weights-three-scores) explains the difference.

--8<-- "tables/engines-same-model.html"

## Best model per family

The best row of every model, grouped by family. A **dedicated** model was trained for this kind of question and has its own readout; a **fine-tuned** model is a chat model tuned by someone for a task; a **vanilla** model is a stock chat model. **Best method** names the row the other columns come from. [Chapter 4](../04-models.md) describes the families.

--8<-- "tables/families.html"

## Quantization sweeps

Each row is one model on one engine, measured at several quantizations. Each cell is the translated score out of 67, then the mean time per query; an empty cell was not measured. Between Q4 and Q8 the scores barely move, and below Q3 they collapse. [Chapter 7](../07-quantization.md#q4-to-q8-is-a-plateau) reads the grid.

--8<-- "tables/quant-sweeps.html"

## Every query

Every one of the 67 queries, hardest first. **Right, translated** and **right, direct** are the share of all methods that answered it correctly in each mode. **jev** is jev's answer on the translated text, which you can compare with the labelled **task**. [Chapter 9](../09-confidence.md#the-hardest-queries) discusses the three hardest.

--8<-- "tables/queries.html"

## The translator

The translated mode runs Hy-MT2-1.8B at Q4_K_M on llama-server in front of the classifier, with a short glossary of font-editing terms. The table lists the 39 non-English queries, their English translations and the time each took. Each query was translated once, so every classifier saw the same English. [Chapter 5](../05-method.md#translation) describes the prompt.

--8<-- "tables/translator.html"

## Language detection

Before it translates, the pipeline has to know whether a query is English. Two detectors, and a majority vote that breaks ties in lingua's favour, were measured over 100 passes of the 67 queries, single-threaded. [Chapter 5](../05-method.md#language-detection) lists lingua's four misses.

--8<-- "tables/detectors.html"

## Calibration

These tables group the answers of decider-0.8b (DreamBlooms' `Q8_0` file, the one `ornotto` registers) on dohnuts (Metal) by their top probability. **Share right** is the fraction of answers in that band that were correct; a calibrated model is right about as often as its probability says. [Chapter 9](../09-confidence.md#decider-08b-on-the-router-set) reads the bands.

With translation:

--8<-- "tables/calibration-translated.html"

On the original text:

--8<-- "tables/calibration-direct.html"

## A fallback gate

A gate asks decider-0.8b on dohnuts first and sends the query to Qwen3.5-4B-Hmm on pcdServer only when decider's top probability is below the threshold. The rows replay the benchmark's cached answers at each threshold. **Fallbacks** counts the queries sent on; **mean ms** is the cost per query averaged over all 67, where a query that falls back pays for both calls. The thresholds were chosen on the same queries they are scored on, so this is not a held-out test. [Chapter 9](../09-confidence.md#a-fallback-gate) explains why the gate pays only on the original text.

With translation:

--8<-- "tables/cascade-translated.html"

On the original text:

--8<-- "tables/cascade-direct.html"
