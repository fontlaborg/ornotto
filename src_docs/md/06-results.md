---
this_file: src_docs/md/06-results.md
---

# 6. Results

jev, the hosted reference, answered 65 of the 67 router queries correctly in both modes, at 466 ms per query. The best local model came within one query of it: Qwen3.5-4B-Hmm on pcdServer scored 64/67 on translated text and 65/67 on direct text, at 88 ms per query from a 4.5 GB file, or 93 ms from the 2.7 GB Q4_K_M file. The dedicated decider-0.8b on dohnuts (Metal) scored 62/67 and 61/67 at 52 ms from the 0.81 GB DreamBlooms `Q8_0` file that `ornotto` registers, and the laya encoder scored 52/67 in 7 ms. 208 methods finished; two failed and are left out.

## The top of the table

The fifteen best methods, ordered by translated accuracy, then direct accuracy, then speed:

--8<-- "tables/top.html"

Five findings stand out.

- **A small, dedicated model gets within three queries of jev.** decider-0.8b answers 62 of 67 through its own readout, from a file a fifth the size of the Hmm model's Q8 build. It is the fastest method to score 62 or more (51 ms for mradermacher's `Q8_0` conversion of the same weights), and its probabilities are calibrated.
- **A tuned 4B chat model on pcdServer matches the 35B decider.** Qwen3.5-4B-Hmm ties decider-35b-a3b on dohnuts on translated text (64 each) and beats it by one answer on direct text (65 against 64). Its 2.7 GB Q4 build is an eighth the size of the 35B file and runs three times faster. Its accuracy does not move from Q4 to BF16.
- **Vanilla chat models are close behind.** unsloth's Qwen3.5-4B at Q8 scored 63/64 at 85 ms, one query behind the Hmm tune, with no task-specific training. Qwen3.5-2B at Q3_K_M scored 61/62 at 43 ms from 1.2 GB.
- **Size does not rescue an old model.** The best Qwen1.5 method, at 4B, scored 42/67 in 248 ms. Qwen3.5 at 0.8B scored 57.
- **Speed and accuracy separate at the extremes.** laya runs in 4 to 7 ms on Apple silicon but tops out at 52. kev-4b reaches 62 on translated text but takes 1.1 seconds per query.

## Every method

All 208 methods are in the table below. Click a column header to sort by it, and click again to reverse the order. Type in the box to keep only the rows that contain every word you type: `pcdServer hmm` keeps the Hmm model on pcdServer, and `dedicated Metal` keeps the dedicated models on dohnuts (Metal). [Chapter 5](05-method.md#what-the-numbers-mean) defines every column.

--8<-- "tables/classifiers.html"

Some reading notes:

- **English is the hard part.** The ten deliberately ambiguous queries are nine English and one Polish, so most models lose more of the 28 English queries than of the 39 others. jev got 26 of 28 English and 39 of 39 others.
- **Translation helps weak multilingual models and costs strong ones nothing.** kev-0.8b scored 57 translated and 45 direct, Qwen2.5-3B at Q8 62 and 57, laya 52 and 49. The Hmm model scored one answer better without translation, 65 against 64, and so did the Qwen3.5-4B builds.
- **Load times differ by three orders of magnitude.** A GGUF on pcdServer or llama-server loaded in 40 ms to 1.8 seconds. Core ML models compiled for the Neural Engine took 20 seconds, and decider-4b in PyTorch 17 seconds.
- **Quantization is flat until it falls off a cliff.** Q4 to Q8 barely changes a score. Below Q3 scores drop fast: decider-0.8b at Q2 answered 17 or 18 of 67 on every engine, and Qwen3-4B at IQ1_S answered 13. [Chapter 7](07-quantization.md) has the full sweeps.
- **Two methods failed.** A Core ML laya export fixed at 64 tokens and four options could not take a five-way question. The BF16 build of unsloth's Qwen3.5-4B was not on disk when its turn came. Neither appears in the tables.

## Best method per engine and runtime

Most methods run on pcdServer, because it takes any chat GGUF: 156 of the 208. The other engines and runtimes ran only the models they were built for. The best method on each:

| engine or runtime | methods | best method | translated / direct | ms/query |
|---|---:|---|---|---:|
| jev (hosted) | 1 | `jev` | 65 / 65 | 466 |
| pcdServer | 156 | `pcdserver@qwen3.5-4b-hmm-q8` | 64 / 65 | 88 |
| dohnuts (Metal) | 12 | `dohnuts-metal@decider-35b-a3b-q4` | 64 / 64 | 266 |
| slot (llama-server) | 15 | `slot@decider-35b-a3b-q4` | 64 / 64 | 299 |
| PyTorch | 2 | `torch@decider-4b-bf16` | 63 / 65 | 348 |
| dohnuts (CPU) | 1 | `dohnuts@decider-0.8b-dreamblooms-q8` | 62 / 60 | 275 |
| laya.cpp | 5 | `kev-4b-gguf` | 62 / 55 | 1,103 |
| ExecuTorch (MLX) | 2 | `executorch@decider-0.8b-fp16` | 61 / 60 | 90 |
| MLX | 2 | `laya-mlx` | 52 / 49 | 7 |
| Core AI | 2 | `laya-coreai` | 52 / 49 | 10 |
| ONNX Runtime | 2 | `laya-ml-onnx-fp32` | 52 / 49 | 23 |
| llama.cpp embeddings | 6 | `laya-wd-gguf-q8` | 52 / 49 | 44 |
| Core ML, Neural Engine | 2 | `laya-coreml-ane-w8-compact` | 48 / 49 | 5 |

If you need an answer in under 10 ms on a Mac, only laya delivers it, at 52/67. If you can spend 40 to 55 ms, pcdServer with a 2B chat model or dohnuts with decider-0.8b reaches 61 or 62. Every method above 62 took at least 85 ms.

## One set of weights, three scores

An engine is not a neutral container. The same GGUF file, read two ways, gives different answers:

--8<-- "tables/engines-same-model.html"

decider-0.8b scores 62/67 on dohnuts and 62/67 on slot. Both read the model where it was trained to answer: the logits of the option letters after `Answer: (`, divided by the checkpoint's temperature. The agreement is exact: on all 106 benchmark texts the two picked the same task, and their probabilities differed by at most 0.0004. They differ only in speed. dohnuts (Metal) took 52 ms per query, slot on llama-server 65 ms, and dohnuts on the CPU with eight threads 275 ms.

pcdServer scored the same file 55/67 translated and 57/67 direct, at 28 ms. pcdServer does not know the decider layout. It wraps the query in the model's chat template, lists the fields in a system prompt, and scores the first token of each allowed value. decider was never trained to answer that way, so seven answers go missing, although pcdServer is the fastest engine on this model.

The larger deciders narrow the gap. decider-2b's `Q8_0` and `F16` files scored 59 or 60 translated on every engine that ran them (the `IQ4_NL` file 56 or 57). On direct text they scored 62 through the readout and 60 through pcdServer. The 35B model scored 64/64 through its readout and 63/63 through pcdServer.

The same weights also ran in Mapika's own runtimes: ExecuTorch on MLX scored decider-0.8b at 61/60 in 90 ms, and decider-2b at 59/62 in 251 ms.

Reading a dedicated model through its own readout is worth several answers on small models. For a fine-tuned or vanilla chat model, pcdServer's chat-template readout is the one that works: the Hmm model scored 64/65 there and 62/63 through its letter readout on llama-server, and in a third of the time.

## What the results do not say

A five-way router over 67 queries decides nothing about your task. A model that is one query behind another here is not measurably worse, and the ranking between models within two or three queries of each other would change with a different set of 67. The results are clear about the large gaps: dedicated or modern models against old ones, sensible quantizations against 1- and 2-bit ones, and a trained readout against a foreign one. [Chapter 12](12-choosing.md) turns those gaps into recommendations. [Chapter 8](08-speed.md) explains where the milliseconds go.
