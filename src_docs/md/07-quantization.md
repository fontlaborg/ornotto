---
this_file: src_docs/md/07-quantization.md
---

# 7. Quantization and size

A GGUF file stores a model's weights at reduced precision, and the precision you pick decides the file size, the memory the engine needs, and how many answers survive. On the router set, precision matters much less than you might expect, until it suddenly matters a lot.

## What the labels mean

The suffix of a GGUF file names its quantization: how many bits each weight keeps, and how llama.cpp groups them.

| Label | llama.cpp's reference: Llama-3-8B size, perplexity cost | What it is |
|---|---|---|
| `F16`, `BF16` | about 16 GB, none | Half precision. `BF16` keeps the float32 exponent range; for inference both are the unquantized model. |
| `Q8_0` | 7.96 GB, +0.0026 | Eight bits per weight in small blocks, each with its own scale. The usual reference quant. |
| `Q6_K`, `Q5_K_M`, `Q4_K_M` | 6.14, 5.33, 4.58 GB; +0.022, +0.057, +0.175 | K-quants: nested blocks with their own scales, mixing precisions across tensors (`_M` is the medium mix). |
| `Q3_K_M`, `Q2_K` | 3.74, 2.96 GB; +0.66, +3.52 | The same scheme with fewer bits. |
| `IQ3_XXS`, `IQ2_XXS`, `IQ1_S` | 3.06, 2.06, 1.56 bits per weight | "i-quants": codebooks fitted with an importance matrix, built to hold up at very low bit rates. |
| `UD-…` | mixed | Unsloth's "dynamic" quants, which pick a precision per layer. |

The perplexity cost is the increase llama.cpp's `llama-quantize` lists for Llama-3-8B; it grows slowly to `Q4_K_M` and fast below it, which is the shape the router benchmark shows too.

In the tables below and in [chapter 6](06-results.md), the quant is shortened to its number: `q4` is `Q4_K_M` (or `Q4_0` for the ggml-org file), `iq2` is an `IQ2` variant, `f16` and `bf16` are the unquantized files.

## Q4 to Q8 is a plateau

Across every model that was measured at four or more quantizations, the score between `q4` and `q8` barely moves. Each cell below is the translated score out of 67, then the mean time per query.

--8<-- "tables/quant-sweeps.html"

Some rows that make the point:

- **decider-0.8b on dohnuts (Metal)**: 61 at `q4`, 62 at `q5`, `q6` and `q8`, 61 at `f16`. The 1.52 GB `f16` file scores no better than the 0.53 GB `q4`.
- **Qwen2.5-3B on pcdServer**: 62 at `q4`, `q6`, `q8` and `f16`, 61 at `q5`.
- **Qwen3-4B (Unsloth) on pcdServer**: 60 or 61 at every quant from `q3` to `bf16`.
- **Qwen3.5-4B (Unsloth) on pcdServer**: 60 to 63 from `q2` to `q8`.

One query is 1.5 percentage points of accuracy on a 67-query set, so a difference of one or two answers between neighbouring quants is noise. If you read the grid expecting a smooth curve, you will find bumps that do not repeat: Qwen3.5-2B scores 61 at `q3` and 57 at `q8`, which says more about three borderline queries than about 3-bit weights.

The time column is flat too. On a GPU the engines are limited by memory bandwidth and by the per-request overhead, not by the size of the weights, so a smaller file does not make a single short decision faster: decider-0.8b takes 51 to 55 ms per query on dohnuts (Metal) at every quant.

## Below Q3 it collapses

The plateau ends at three bits, and the drop below it is steep and uneven:

| Model and engine | `q4` or best | `q3` | `q2` | lowest i-quant |
|---|---|---|---|---|
| decider-0.8b, dohnuts (Metal) | 61 | 57 | **18** | |
| decider-0.8b, pcdServer | 57 | 52 | **17** | |
| Qwen3.5-0.8B, pcdServer | 57 (`q5`) | 46 | 40 | |
| Qwen3.5-0.8B (Unsloth), pcdServer | 56 (`q5`) | 48 | 43 | 26 (`iq2`) |
| Qwen3.5-2B (Unsloth), pcdServer | 57 | 57 | 53 | 44 (`iq2`) |
| Qwen2.5-3B, pcdServer | 62 | 57 | 53 | 49 (`iq2`) |
| Qwen3-4B (Unsloth), pcdServer | 61 | 60 | | **13** (`iq1`) |
| Qwen3.5-4B (Unsloth), pcdServer | 63 (`q8`) | 60 | 61 | 52 (`iq2`) |

Two patterns stand out. The smaller the model, the earlier it breaks: at 0.8B parameters `q3` already costs 4 to 11 answers, while the Qwen3.5-4B files hold their score down to `q2`. And the break is abrupt rather than gradual: decider-0.8b at `q2` falls from 62 to 18 correct, one more than you would get by always answering the most common task (the benchmark has 17 docs queries). The `IQ1_S` file of Qwen3-4B, at 1.08 GB, scores 13.

The 1-bit Bonsai models are the exception that shows why: Bonsai-27B at `q1` (3.8 GB) scores 62, because it is built as a 1-bit model ([prism-ml/Bonsai-27B-gguf](https://huggingface.co/prism-ml/Bonsai-27B-gguf)) rather than squeezed into 1-bit weights after training. A post-training quant of an ordinary model has no such margin.

## Q5 for the small models

For the 0.8B and 1.7B models, `q5` keeps the full score everywhere, and on pcdServer it is often the best row of its model:

- decider-0.8b on pcdServer scores 57 at `q5` against 55 at `q8` and `f16`.
- Qwen3.5-0.8B on pcdServer scores 57 at `q5` against 55 at `q8` and `bf16`.
- Qwen3-1.7B scores 57 at `q5`, `q6`, `q8` and `bf16`, and drops to 54 at `q4`.

The gain of `q5` over `q8` is two answers, inside the noise, so the practical reading is that `q5` loses nothing. The `q4` files of the same models lose anything from nothing (decider-0.8b on pcdServer, 57 at both `q4` and `q5`) to five answers (Qwen3.5-0.8B, 52 against 57), and `q3` loses more.

## The same file on different engines

A quant is not a property of the model alone: the engine that reads the answer out decides how much of the model's accuracy you keep. The three rows for decider-0.8b show this most clearly, because they use the same GGUF files:

- dohnuts (Metal) and slot read decider's trained answer slot, the letter logits after `Answer: (`, and score identically at every quant: 62 at `q8`, `q6` and `q5`, 61 at `f16` and `q4`, 57 at `q3`, 18 at `q2`.
- pcdServer runs the same weights as a chat model and scores the first tokens of the task names, a readout decider was never trained for. It loses five to seven answers at every quant: 55 at `q8`, 57 at `q5`, 17 at `q2`.

The quant curve has the same shape on every engine; the engine shifts it up or down. [Chapter 3](03-engines.md) explains the readouts, and [chapter 6](06-results.md) has the full cross-engine comparison.

Laya shows a different failure: the laya-multilingual encoder run as a llama.cpp embedding model scores 52 at `q8` and `f16`, 51 at `q6`, 47 at `q5`, 36 at `q4` and 49 at `q3`. An encoder's hidden states feed a decision head that expects float precision, and the loss does not follow bit count in order. If you run laya through llama.cpp, keep `q8` or `f16`.

## Size against accuracy

Across families, parameters buy more than bits do. The best translated score of each size class on the router set:

| Size class | Best row | GB | Translated | ms/query |
|---|---|---|---|---|
| 0.5 to 0.6B | Qwen3-0.6B `q8`, pcdServer | 0.64 | 53/67 | 25.5 |
| 0.8B | decider-0.8b `q8` (DreamBlooms), dohnuts (Metal) | 0.81 | 62/67 | 52.2 |
| 1.7 to 2B | Qwen3.5-2B `q3`, pcdServer | 1.22 | 61/67 | 42.7 |
| 3B | Qwen2.5-3B `q8`, pcdServer | 3.29 | 62/67 | 53.3 |
| 4B | Qwen3.5-4B-Hmm `q8`, pcdServer | 4.48 | 64/67 | 87.6 |
| 35B (3B active) | decider-35b-a3b `q4`, dohnuts (Metal) | 21.17 | 64/67 | 266.3 |

The hosted jev scores 65 at 466 ms per query. A dedicated 0.8B model gets within three answers of it, and a fine-tuned 4B model within one, at a fifth of the latency. The 35B mixture-of-experts decider does no better than the 4B fine-tune and is three times slower. Generations matter as much as size: the Qwen1.5 models score 39 to 42 at 4B, which the newer 0.8B models beat.

## Which quant to download

- **0.5B to 1B models**: `q5`, or `q8` if the file size does not matter. Never below `q4`; at `q2` they fail.
- **1.7B to 2B models**: `q5` or `q4`. `q3` is usable on the Qwen3.5-2B files, `q2` and the i-quants are not.
- **3B to 4B models**: `q4`. It costs nothing to two answers against `q8` (Qwen3.5-4B-Hmm 64 at both, unsloth's Qwen3.5-4B 61 against 63) and cuts the download from 4.48 GB to 2.71 GB for Qwen3.5-4B-Hmm. The Qwen3.5-4B files keep their score even at `q2`; Qwen3-4B at `IQ1_S` does not.
- **Encoders run as embedding models** (laya through llama.cpp): `q8` or `f16`.
- **Anything larger**: `q4`, and check the memory arithmetic in [chapter 8](08-speed.md#memory-one-model-at-a-time) before you load it.

The registered models in the `ornotto` package follow this: `decider-0.8b`, `decider-2b`, `kev-0.8b`, `dohnuts-0.8b` and `qwen3.5-0.8b` are `q8`, the 2B and 4B chat models are `q4` ([chapter 10](10-package.md)).
