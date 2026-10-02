---
this_file: src_docs/md/06-results.md
---

# 6. Results

jev, the hosted reference, answered 65 of the 67 router queries correctly in both modes, at 466 ms per query. In September, one local method matched it on translated text: rune-26b-a4b at Q3_K_M on llama-server scored 65/67 at 367 ms from a 13.5 GB file, but only 57/67 on the original text. Rune Q5 on pcdServer now matches jev in both modes (65/67 each), using CPU weights at 962 ms/query from 19.13 GB. The best local model near 90 ms remains Qwen3.5-4B-Hmm on pcdServer: 64/67 on translated text and 65/67 on direct text, at 88 ms per query from a 4.5 GB file, or 93 ms from the 2.7 GB Q4_K_M file. The dedicated decider-0.8b on dohnuts (Metal) scored 62/67 and 61/67 at 52 ms from the 0.81 GB DreamBlooms `Q8_0` file that `ornotto` registers. Among encoders, GLiNER2.5-Decide scored 61/67 on translated text in 27 ms on Core AI, and laya 52/67 in 7 ms. 300 methods finished; five failed and are left out.

The jev row measures `jev-1.13.0`. TypeSafe's model page listed no other version in September 2026, and both public aliases, `jev-latest` and `jev-preview`, pointed to it when we checked on 30 September.[^ts-models] [Chapter 1](01-deciding.md#jev-the-hosted-reference) explains why the version behind an alias matters. Every benchmark number in this chapter comes from our own 67-query routing test. Local inference ran on one Mac; remote calls used that Mac as the client, with provider hardware undisclosed. Numbers that other people published about the same models are collected separately, in [Numbers others report](#numbers-others-report), and are never mixed into our tables.

## OpenRouter: nine remote models

The fresh `typesafe/jev-1.13` run scored **65/67 in both modes**, at **364.4 ms translated and 375.1 ms direct**. Together Tev1 scored **64/67 translated at 339.3 ms** and **65/67 direct at 335.1 ms**. Kev 4B also scored **65/67 in both**, at **1,653.0 ms translated and 1,525.0 ms direct**. The earlier hosted Jev measurement is retained; differences in end-to-end timing across dates are not a controlled model-speed comparison.

All nine requested endpoints were measured on the same 67 queries, in translated and direct modes, on 3 October 2026. Translations and local results are retained from the earlier runs. Each endpoint received 106 distinct inputs, sequentially, with duplicate inputs reused across modes. Latency includes the network trip and provider processing; **R** means the provider did not disclose CPU/GPU placement or weight precision.

Six endpoints use a native five-way **choice**. Respan's three endpoints support **noul** only: each request contains five independent yes/no questions using the same task descriptions. We choose the largest P(true), then normalize the five values for the routing report. This **noul OVR** readout is labelled separately; its values are not calibrated exclusive-choice probabilities. Choose **OpenRouter API** in the explorer's engine filter to select all nine endpoints. Its table shows the readout for each run.

--8<-- "tables/remote.html"

## Issue 102: October additions

The 32 additions were measured on 2 October 2026. They use the same 67 queries and recorded translation choices as the earlier round. Each model ran alone. The 258 earlier result rows are unchanged.

| method | translated | direct | ms/query | weights GB | C/G |
|---|---:|---:|---:|---:|---|
| `pcdserver@rune-mradermacher-26b-a4b-q5` | 65/67 | 65/67 | 962.3 | 19.13 | C+G |
| `pcdserver@rune-mradermacher-26b-a4b-q3` | 64/67 | 64/67 | 146.1 | 13.29 | G |
| `dohnuts-metal@jpt-4b-q8` | 64/67 | 64/67 | 335.6 | 4.48 | G |
| `pcdserver@rune-mradermacher-26b-a4b-q8` | 64/67 | 64/67 | 758.1 | 26.86 | C |
| `pcdserver@jpt-4b-q8` | 63/67 | 64/67 | 86.3 | 4.48 | G |
| `pcdserver@jpt-4b-q4` | 63/67 | 64/67 | 93.0 | 2.71 | G |
| `pcdserver@jpt-9b-q5` | 63/67 | 64/67 | 155.2 | 6.47 | G |
| `dohnuts-metal@jpt-4b-q5` | 63/67 | 64/67 | 367.0 | 3.07 | G |
| `pcdserver@rune-mradermacher-26b-a4b-q4-metal` | 63/67 | 64/67 | 124.8 | 16.80 | G |
| `pcdserver@rune-mradermacher-26b-a4b-q4` | 63/67 | 64/67 | 487.1 | 16.80 | C+G |
| `dohnuts-metal@jpt-9b-q5` | 63/67 | 64/67 | 619.6 | 6.47 | G |
| `dohnuts-metal@jpt-9b-q4` | 63/67 | 64/67 | 619.8 | 5.63 | G |
| `dohnuts-metal@jpt-9b-q8` | 63/67 | 64/67 | 624.7 | 9.53 | G |
| `pcdserver@jpt-4b-q5` | 62/67 | 63/67 | 99.4 | 3.07 | G |
| `dohnuts-metal@jet-4b-q8` | 62/67 | 63/67 | 281.4 | 4.48 | G |
| `dohnuts-metal@jpt-4b-q4` | 62/67 | 62/67 | 290.6 | 2.71 | G |
| `dohnuts-metal@jpt-9b-q3` | 61/67 | 64/67 | 636.7 | 4.62 | G |
| `pcdserver@jpt-9b-q4` | 61/67 | 63/67 | 137.3 | 5.63 | G |
| `pcdserver@jpt-9b-q8` | 61/67 | 63/67 | 141.8 | 9.53 | G |
| `dohnuts-metal@jpt-4b-q3` | 61/67 | 63/67 | 315.0 | 2.26 | G |
| `coreml@kev-0.8b-fp16-l512` | 60/67 | 62/67 | 121.3 | 1.51 | C+G |
| `pcdserver@jpt-9b-q3` | 60/67 | 62/67 | 139.2 | 4.62 | G |
| `pcdserver@jpt-4b-q3` | 60/67 | 60/67 | 93.7 | 2.26 | G |
| `mlx@tev1-0.8b-4bit` | 60/67 | 59/67 | 64.8 | 0.42 | G |
| `dohnuts-metal@tev1-0.8b-q8` | 59/67 | 62/67 | 61.5 | 0.81 | G |
| `dohnuts-metal@this-that-model-1.2-q3` | 57/67 | 56/67 | 113.1 | 1.10 | G |
| `systemone@kev-ggmlc-0.8b-q8` | 57/67 | 45/67 | 199.8 | 0.83 | G |
| `systemone@bosun-1.7b-q5` | 55/67 | 55/67 | 130.8 | 1.26 | G |
| `dohnuts-metal@this-that-model-1.2-q5` | 54/67 | 57/67 | 117.4 | 1.41 | G |
| `systemone@kev-ggmlc-0.8b-q4` | 54/67 | 43/67 | 207.2 | 0.96 | G |
| `dohnuts-metal@this-that-model-1.2-q8` | 53/67 | 57/67 | 107.8 | 2.01 | G |
| `dohnuts-metal@this-that-model-1.2-q4` | 51/67 | 51/67 | 110.5 | 1.27 | G |
| `dohnuts-metal@this-that-model-1.2-q2` | 21/67 | 18/67 | 112.2 | 0.97 | G |

Kev uses the [FluidInference Core ML export](https://huggingface.co/FluidInference/kev-0.8b-coreml), the L512/K16 single-question row on CPU and GPU. This is not the fused multi-question path. Its fitted temperature is already in the graph. Tev1 uses the native decision prompt with thinking disabled and a single forward pass over option-letter logits, on [dohnuts Q8](https://huggingface.co/DreamBlooms/Tev1-0.8B-experimental-GGUF) and [MLX 4-bit](https://huggingface.co/SirSahOl/Tev1-0.8B-experimental-chat-mlx-4bit). Its release licence is unresolved, and temperature 1.0 does not establish calibration.

[Bosun Q5_K_M](https://huggingface.co/Hanno-Labs/bosun-v3.1-1.7b-GGUF) runs on llama-cpp-python with Metal. Its native prompt shuffles candidates into stable slots. We verified the prompt against the pinned source renderer and tokenizer ChatML template, checked all 256 decision-token IDs, read final-position logits for the valid slots and restored the caller's order. Temperature is 1.0; these measurements do not establish calibration. [Hanno's server](https://github.com/Hanno-Labs/jev-compatible-server) implements native Bosun through Transformers; its generic llama backend does not implement this GGUF readout.

The [mys Kev Q4 and Q8 files](https://huggingface.co/mys/kev-0.8b-GGUF) ran on ggmlc with Metal. Both fail to load in current dohnuts with `unknown model architecture: 'ggmlc'`. This is an observed runtime incompatibility, so the two measurements use the compiler's own runtime. The Q4 file is larger than Q8 because its dynamic quantization preserves additional tensors at higher precision.

[Rune's mradermacher conversions](https://huggingface.co/mradermacher/rune-26b-a4b-GGUF) now run on pcdServer through the fork's Jinja chat-template fallback. Q5_K_M scores 65/67 in both modes at 962 ms/query from 19.13 GB. Q3_K_M scores 64/67 in both modes at 146 ms from 13.29 GB. These are separate conversions and a separate readout from the earlier surogate Rune rows. The original Q4 and Q5 runs keep weights on CPU with Metal computation enabled; Q8 runs entirely on CPU after device-offload attempts exceeded the guards. The fresh Q4 full-Metal rerun scores 63/64 at 124.8 ms (3.9× faster than the earlier Q4 at 487.1 ms), and is retained as a separate row. Q5 and Q8 latency is not a fair comparison with the Q3 or new Q4 GPU runs. Swap grew during the larger-model attempts; each run remained guarded and each completed measurement ran alone.

[JPT 4B](https://huggingface.co/prithivMLmods/jpt-4b-GGUF) and [JPT 9B](https://huggingface.co/prithivMLmods/jpt-9b-GGUF) ran at Q3, Q4, Q5 and Q8 on both requested engines. The repositories publish no Q8: we converted their pinned BF16 files locally with llama-quantize Q8_0. The [conversion manifests](https://github.com/fontlaborg/ornotto/blob/main/src_docs/data/local_conversions.json) record source revisions, input/output hashes, converter hash, sizes and tensor types. JPT is CC BY-NC 4.0. Native dohnuts uses source-matched chat prompts, contextual answer tokens and the affirmative yes/no label; its temperatures are 1.036 (4B) and 1.087 (9B). The 4B Q8 native readout scores 64/67 in both modes; pcdServer is faster but scores 63/64.

[Jet Q8](https://huggingface.co/DreamBlooms/jet-GGUF) scores 62/67 translated and 63/67 direct on dohnuts, in 281 ms. Its score questions read digit logits and yes/no questions read the corresponding word logits. [ThisThat 1.2](https://huggingface.co/mradermacher/this-that-model-1.2-GGUF) ran on dohnuts at every requested precision. Q3 scores 57/56, while Q2 falls to 21/18. Their native prompts and label mappings are part of the updated bundled engine, and response checks cover choice, yes/no and score in addition to the router benchmark.

All 24 requested weight variants are covered by these 32 measurements. The two mys Kev measurements use the documented ggmlc alternative, and the four JPT Q8 engine measurements use the documented local conversions. The earlier 258 exported rows remain field-identical.

## The top of the table

The fifteen best methods, ordered by translated accuracy, then direct accuracy, then speed:

--8<-- "tables/top.html"

Five findings stand out from the first round of 208 methods, three more from the next 50, and the October additions bring Rune Q5 to 65/67 in both modes.

- **A small, dedicated model gets within three queries of jev.** decider-0.8b answers 62 of 67 through its own readout, from a file a fifth the size of the Hmm model's Q8 build. decider-0.8b's `Q8_0` conversions are the fastest methods to score 62 or more (51 ms for mradermacher's, 52 ms for DreamBlooms'), and its probabilities are calibrated.
- **A tuned 4B chat model on pcdServer matches the 35B decider.** Qwen3.5-4B-Hmm ties decider-35b-a3b on dohnuts on translated text (64 each) and beats it by one answer on direct text (65 against 64). Its 2.7 GB Q4 build is an eighth the size of the 35B file and runs three times faster. Its accuracy does not move from Q4 to BF16.
- **Vanilla chat models are close behind.** unsloth's Qwen3.5-4B at Q8 scored 63/64 at 85 ms, one query behind the Hmm tune, with no task-specific training. Qwen3.5-2B at Q3_K_M scored 61/62 at 43 ms from 1.2 GB.
- **Size does not rescue an old model.** The best Qwen1.5 method, at 4B, scored 42/67 in 248 ms. Qwen3.5 at 0.8B scored 57.
- **Speed and accuracy separate at the extremes.** laya runs in 4 to 7 ms on Apple silicon but tops out at 52. kev-4b reaches 62 on translated text but takes 1.1 seconds per query.
- **The later dedicated models join the top, at a price in latency or memory.** rune (65/67 translated, 13.5 GB), winnow in ollaya (64/67 and 65/67, 891 ms), Jev-Omni (64/67 in both modes, 1.2 seconds) and NeoHorse-Jev-4B (64/67 in both modes, 273 ms from 5.2 GB) all reach the top fifteen. None of them answers as fast as Qwen3.5-4B-Hmm on pcdServer, which scores 64/67 and 65/67 in 88 ms.
- **An English-only encoder gets within four answers of jev on translated text.** GLiNER2.5-Decide scored 61/67 on Core AI, ONNX Runtime and Core ML alike, nine answers above laya, in 27 ms on Core AI. It cannot read the original text of a non-English query, so it needs the translator.
- **A new readout is no guarantee.** The contrastive CLM scored 33 to 39, the entailment readouts 20 (ModernBERT NLI) and 51 (semif), GLiClass 26, and the small encoders Julia-1, Pulse Decide and decima-small 31 to 37. Apart from semif, they score no better than the old Qwen1.5 models, whose best was 42.

## Every method

All 300 methods are in the table below. Click a column header to sort by it, and click again to reverse the order. Type in the box to keep only the rows that contain every word you type: `pcdServer hmm` keeps the Hmm model on pcdServer, and `dedicated Metal` keeps the dedicated models on dohnuts (Metal). [Chapter 5](05-method.md#what-the-numbers-mean) defines every column. An empty direct cell means the model was trained on English only and was sent the translated text alone. A method marked † carries a licence note, which its tooltip shows.

--8<-- "tables/classifiers.html"

Some reading notes:

- **English is the hard part.** The ten deliberately ambiguous queries are nine English and one Polish, so most models lose more of the 28 English queries than of the 39 others. jev got 26 of 28 English and 39 of 39 others.
- **Translation helps weak multilingual models and costs strong ones nothing.** kev-0.8b scored 57 translated and 45 direct, Qwen2.5-3B at Q8 62 and 57, laya 52 and 49. The Hmm model scored one answer better without translation, 65 against 64, and so did the Qwen3.5-4B builds.
- **Load times differ by three orders of magnitude.** A GGUF on pcdServer or llama-server loaded in 40 ms to 1.8 seconds. Core ML models compiled for the Neural Engine took 20 seconds, decider-4b in PyTorch 17 seconds, and the fixed-shape Core ML package of GLiNER2.5-Decide 82 seconds. The authors' System One servers were started before the timed run, so their load is not measured.
- **Quantization is flat until it falls off a cliff.** Q4 to Q8 barely changes a score. Below Q3 scores drop fast: decider-0.8b at Q2 answered 17 or 18 of 67 on every engine, and Qwen3-4B at IQ1_S answered 13. [Chapter 7](07-quantization.md) has the full sweeps.
- **Five methods failed.** A Core ML laya export fixed at 64 tokens and four options could not take a five-way question. The BF16 build of unsloth's Qwen3.5-4B was not on disk when its turn came. The earlier pcdServer build answered every request for the two surogate Rune files with HTTP 422; the October fork separately measures mradermacher Rune through its Jinja fallback. The Q5_K_M file of jeb-35b-a3b took the machine's free memory below the benchmark's safety limit while it loaded, and the run was stopped. None of the five appears in the tables.

## Best method per engine and runtime

Most methods run on pcdServer, because it takes any chat GGUF: 172 of the 300. The other engines and runtimes ran only the models they were built for. The best method on each:

| engine or runtime | methods | best method | translated / direct | ms/query | C/G |
|---|---:|---|---|---:|---|
| jev (hosted) | 1 | `jev` | 65 / 65 | 466 | R |
| slot (llama-server) | 20 | `slot@rune-26b-a4b-q3` | 65 / 57 | 367 | G |
| pcdServer | 172 | `pcdserver@rune-mradermacher-26b-a4b-q5` | 65 / 65 | 962 | C+G |
| ollaya | 10 | `ollaya@winnow-12b` | 64 / 65 | 891 | G |
| dohnuts (Metal) | 27 | `dohnuts-metal@decider-35b-a3b-q4` | 64 / 64 | 266 | G |
| System One server | 11 | `systemone@neohorse-4b-q8` | 64 / 64 | 273 | G |
| llama.cpp embeddings + head | 5 | `gguf-head@jev-omni-q3` | 64 / 64 | 1,222 | C+G |
| PyTorch | 4 | `torch@decider-4b-bf16` | 63 / 65 | 348 | G |
| MLX | 9 | `mlx@openjev-35b-a3b-4bit` | 63 / 62 | 250 | G |
| dohnuts (CPU) | 1 | `dohnuts@decider-0.8b-dreamblooms-q8` | 62 / 60 | 275 | C |
| laya.cpp | 5 | `kev-4b-gguf` | 62 / 55 | 1,103 | G |
| ExecuTorch (MLX) | 2 | `executorch@decider-0.8b-fp16` | 61 / 60 | 90 | G |
| Core AI | 3 | `coreai@gliner25-decide` | 61 / – | 27 | A |
| ONNX Runtime | 8 | `onnx@gliner25-decide-fp32` | 61 / – | 67 | C |
| Core ML | 2 | `coreml@gliner25-decide-fp16-l256` | 61 / – | 349 | A |
| ggmlc (Metal) | 2 | `systemone@kev-ggmlc-0.8b-q8` | 57 / 45 | 200 | G |
| llama-cpp-python (Metal) | 1 | `systemone@bosun-1.7b-q5` | 55 / 55 | 131 | G |
| llama.cpp embeddings | 6 | `laya-wd-gguf-q8` | 52 / 49 | 44 | C+G |
| Core ML, Neural Engine | 2 | `laya-coreml-ane-w8-compact` | 48 / 49 | 5 | C+N |

A dash is a direct score that does not apply: GLiNER2.5-Decide was trained on English only.

If you need an answer in under 10 ms on a Mac, only laya delivers it at a useful score, 52/67; Julia-1 on MLX answers in 6.8 ms but scores 31. Between 10 and 30 ms, laya in ollaya answers in 12 ms (52/67), and GLiNER2.5-Decide on Core AI in 27 ms (61/67, translated text only). If you can spend 40 to 55 ms, pcdServer with a 2B chat model or dohnuts with decider-0.8b reaches 61 or 62. Every method above 62 took at least 85 ms; Rune Q5 reaches 65 in both modes at 962 ms with CPU weights.

The table also shows where the choice of engine is a choice of model. pcdServer ran 171 methods, including the October mradermacher Rune conversions through the new Jinja fallback. The earlier failed surogate Rune runs remain excluded. ollaya and the authors' System One servers ran the models they ship, and nothing else. The hosted jev and the five fastest local engines answer the same five-way question, but they do not compete for the same models. [Chapter 3](03-engines.md#side-by-side) lists which readout each engine uses, and [chapter 12](12-choosing.md#which-engine-and-model) turns this table into a choice.

## The second round, model by model

The 50 methods added in the second round were mostly dedicated decision models that appeared on Hugging Face in the second half of September 2026. Their authors describe them against jev and against each other. Our numbers put them on one question and one machine, which is a narrower test than the authors' own, and a more even one.

**rune-26b-a4b** is the only local model that matched jev on translated text: 65/67 at `Q3_K_M` on slot, in 367 ms from 13.52 GB. On the original, untranslated text it scored 57/67, the largest gap between the two modes among the top methods. The `Q4_K_M` file scored 64/67 and 55/67 in 335 ms from 17.03 GB. The file we measured is version 1 of the model, from a gated revision of the repository. The later v3, which leads the Decision Index board, was not published as GGUF when we ran the benchmark, so the two are not the same weights.

**winnow-12b** in ollaya scored 64/67 translated and 65/67 direct, the same as the Hmm model on direct text, but at 891 ms per query from 12.67 GB. Its authors compare it to jev on a 231-item public subset of JevBench, where the `Q8_0` build and jev both scored 85.71%.[^winnow] ollaya's own measurement on typed-decisions put `winnow:12b` at 0.702 and the smaller `winnow:e4b` at 0.722.[^ollaya-rel] On our set the 12B model is among the most accurate and among the slowest.

**NeoHorse-Jev-4B** scored 64/67 in both modes at `Q8_0`, in 273 ms from 5.17 GB, and 63/67 in both modes at `Q3_K_M`, in 296 ms from 2.95 GB. It is the smallest file in the benchmark to score 63 or more in both modes on its own server. We found no accuracy figure from its authors to set beside ours. The name also needs care: NeoHorse-1 is a general agentic and coding model, and only NeoHorse-Jev-4B is the decision model ([chapter 4](04-models.md#later-dedicated-models)).

**Jev-Omni** scored 64/67 in both modes from its 6.09 GB `Q3_K_M` file, read through llama.cpp embeddings and its own head, but took 1,222 ms per query. The `Q5_K_M` and `Q8_0` files each scored 63/67 in both modes. On MLX, the 4-bit build scored 61/67 in both modes in 780 ms. Its card reports 86.15% on 231 matched JevBench decisions.[^jevomni]

**GLiNER2.5-Decide** is the surprise among the encoders. It scored 61/67 on translated text on Core AI (27 ms), ONNX Runtime (67 ms) and Core ML (349 ms), nine answers above laya and within four of jev. Its card reports 60.2% exact match on the publisher's own 17-domain decision set.[^gliner] The two figures measure different things and cannot be compared, but they point the same way: a 340M English encoder with a label head can hold its own on a clean English question. It cannot read the original text of the 39 non-English queries, so it needs the translator in front of it.

**Julia-1** runs the other way. Its card reports 73.15% on typed-decisions (1,463 of 2,000), above the 72.70% it quotes for jev.[^julia] On our router set it scored 31/67 in both modes, on MLX in 6.8 ms and on ONNX Runtime in 12.2 ms. A model that does well on one public board can still do badly on a question it was not trained near, which is the reason this book measures on a fixed question of its own ([chapter 5](05-method.md#limits)).

**CLM**, the contrastive readout, scored 33 to 39 translated across five builds, and 39/67 in ollaya at 1,678 ms. Its heads were trained on the states and actions of agents rather than on routing, and ollaya's own typed-decisions run scored it at 0.357, which ollaya's release notes call "close to chance there".[^ollaya-rel] [Chapter 7](07-quantization.md#the-later-decision-models) shows that no quantization rescues it.

## Numbers others report

The same decision models are ranked on several public boards, and by their own publishers. None of these numbers comes from our run, and none of them can be compared with a score out of 67. They are here so that you can see where our result agrees with the outside view and where it does not.

!!! note "Reported by others, not measured by us"
    The tables in this section copy published figures. Each names its board, its version where it has one, and the date the figure was measured or read. Numbers from different boards use different questions, different metrics and different clients, so a row in one table says nothing about a row in another.

### typed-decisions

The Hugging Face dataset `LocalLLaMA/typed-decisions` was created on 16 September 2026. Its test split has 400 cases and 2,000 decisions from four workflows: agent-trace observability, customer service, invoice processing and security incidents. Its leaderboard, read on 30 September 2026:[^td]

| # | Model | Accuracy ↑ | KL from gold ↓ | Brier ↓ | ECE ↓ | p50 latency |
|---|---|---|---|---|---|---|
| 1 | meraGPT Decider 1 (`sd-1`), hosted | 0.768 | 0.096 | 0.052 | 0.180 | 526 ms |
| 2 | Liquid AI d1 (`d1:free`), hosted, measured 2026-09-30 | 0.742 | 0.475 | 0.155 | 0.124 | 525 ms |
| 3 | TypeSafe jev 1.13.0, hosted, measured 2026-09-18 | 0.727 | 1.442 | 0.148 | 0.144 | 710 ms |
| 4 | Featherless Simple Jev, hosted | 0.716 | 0.488 | 0.176 | – | – |
| – | Prior (always the most common answer) | 0.470 | 0.347 | 0.189 | 0.088 | – |

The card's own comment on jev: "Its accuracy is near the 0.735 ceiling, but it puts nearly all its probability on one answer, which is where the KL gap comes from." [Chapter 9](09-confidence.md#what-calibration-means) returns to that gap. The latency column is the card's client against each hosted API, not a local measurement, and it is not the 466 ms we measured for jev from our own client.

jev's accuracy on this set is quoted three ways in September 2026: 0.727 on the card, 0.738 on ollaya's site (which cites Winnow's benchmark report for it), and 72.70% on the Julia-1 card.[^ollaya-site][^julia] The differences come from different runs and dates. This book uses the card's 0.727 with its measurement date.

ollaya publishes its own runs on the same set, "measured by Ollaya", in its release notes between 24 and 28 September 2026:[^ollaya-rel]

| ollaya tag | Accuracy on typed-decisions |
|---|---|
| `kev:9b` | 0.722 |
| `winnow:e4b` | 0.722 |
| `winnow:12b` | 0.702 |
| `kev:4b` | 0.669 |
| JevK5 | 0.625 |
| `decider:2b` | 0.591 |
| `nli` | 0.548 |
| `decider:0.8b` | 0.506 |
| `gliclass` | 0.477 |
| `kev:0.8b` | 0.460 |
| `laya:en` | 0.361 |
| CLM | 0.357 |

ollaya leaves out laya's own figure of 0.766, because laya "was fine-tuned on this dataset".[^ollaya-site] The two lists agree with ours on some points and not on others. Both put winnow near the top and CLM near the bottom. On typed-decisions, `decider:0.8b` sits well below `kev:4b`; on our router set, decider-0.8b through its own readout (62/67) scored the same as kev-4b on translated text and above it on direct text. A board with four business workflows and a five-way router over FontLab tasks reward different things.

### Decision 1.0

The vLLM Semantic Router project published its Decision 1.0 family on 21 and 22 September 2026, with its own benchmark of 54 tasks and 3,766 questions. Its card reports:[^d1]

| Model | Overall, Decision 1.0 benchmark |
|---|---|
| Decision-1.0-Eos-0.8B | 61.89 |
| Kev 0.8B | 58.28 |
| Qwen3.5-2B, letter readout | 57.24 |
| Laya English | 51.03 |

We ran Eos through ollaya as `decision:eos`: 57/67 translated and 56/67 direct, in 323 ms. That is below kev-0.8b in ollaya (60/67 and 62/67) and below vanilla Qwen3.5-2B on pcdServer (61/67 and 62/67), the opposite order from the card. The board is the publisher's own, and so is the set of tasks it chose.

!!! quote "How it looked from the outside"
    On 26 September 2026 Lijuan Tang and Yuemeng Zheng posted an audit of 28 papers on typed decision models, all posted between 19 and 24 September, in the ten days after jev's launch. Their abstract concludes that "the typed readout itself has not shown an independent accuracy advantage over comparable label-probability readouts. Jev's clearest gains are in latency and cost".[^audit]

    Our table points the same way from a different direction. The best local rows read label probabilities: letter logits on slot and dohnuts, first-token probabilities on pcdServer. A vanilla Qwen3.5-4B read that way scored 63/67 and 64/67 without any decision training.

## What changed in September 2026

The first round of this benchmark had 208 methods, most of them vanilla and fine-tuned chat models on pcdServer. By the time the second round ran, at the end of September 2026, the field had changed shape. Nearly every decision model in the second round first appeared on Hugging Face between 16 and 29 September, and several public boards had appeared alongside them. Three things follow for this chapter.

- **The top of the table is more crowded, not higher.** rune reached jev's 65 on translated text, and four other second-round models reached 64. None of them beat jev in both modes, and none beat Qwen3.5-4B-Hmm on direct text.
- **Hosted alternatives to jev appeared.** meraGPT Decider 1 and Liquid AI d1 rank above jev on typed-decisions, and OpenAI announced a Decision API on 29 September.[^openai] None of them is in our benchmark. Neither of the first two states its weights or licence.
- **Board numbers moved during the month.** JevBench changed its scale more than once in two weeks, and jev's own typed-decisions figure is quoted three ways. [Chapter 5](05-method.md#limits) explains why this book reports one question on one date instead.

## One set of weights, three scores

An engine is not a neutral container. The same GGUF file, read two ways, gives different answers:

--8<-- "tables/engines-same-model.html"

decider-0.8b scores 62/67 on dohnuts and 62/67 on slot. Both read the model where it was trained to answer: the logits of the option letters after `Answer: (`, divided by the checkpoint's temperature. The agreement is exact: on all 106 benchmark texts the two picked the same task, and their probabilities differed by at most 0.0004. They differ only in speed. dohnuts (Metal) took 52 ms per query, slot on llama-server 65 ms, and dohnuts on the CPU with eight threads 275 ms.

pcdServer scored the same file 55/67 translated and 57/67 direct, at 28 ms. pcdServer does not know the decider layout. It wraps the query in the model's chat template, lists the fields in a system prompt, and scores the first token of each allowed value. decider was never trained to answer that way, so seven answers go missing, although pcdServer is the fastest engine on this model.

The larger deciders narrow the gap. decider-2b's `Q8_0` and `F16` files scored 59 or 60 translated on every engine that ran them (the `IQ4_NL` file 56 or 57). On direct text they scored 62 through the readout and 60 through pcdServer. The 35B model scored 64/64 through its readout and 63/63 through pcdServer.

The same weights also ran in Mapika's own runtimes: ExecuTorch on MLX scored decider-0.8b at 61/60 in 90 ms, and decider-2b at 59/62 in 251 ms. ollaya runs decider-0.8b as a float32 ONNX graph on the CPU, with decider's own slot readout: 61/60 in 285 ms.

A runtime can also leave the score alone entirely. GLiNER2.5-Decide scored 61/67 on Core AI, ONNX Runtime and Core ML, and its three builds differ only in speed: 27 ms, 67 ms and 349 ms per query.

Reading a dedicated model through its own readout is worth several answers on small models. For a fine-tuned or vanilla chat model, pcdServer's chat-template readout is the one that works: the Hmm model scored 64/65 there and 62/63 through its letter readout on llama-server, and in a third of the time.

## What the results do not say

A five-way router over 67 queries decides nothing about your task. A model that is one query behind another here is not measurably worse, and the ranking between models within two or three queries of each other would change with a different set of 67. The results are clear about the large gaps: dedicated or modern models against old ones, sensible quantizations against 1- and 2-bit ones, and a trained readout against a foreign one. [Chapter 12](12-choosing.md) turns those gaps into recommendations. [Chapter 8](08-speed.md) explains where the milliseconds go.

The same caution applies to the public boards in [Numbers others report](#numbers-others-report). Each measures its own question, and a model's rank moves from one board to the next. If a board and this chapter disagree about a model, the disagreement is information about the two questions, not an error in either. The only way to know how a model will do on your decision is to run it on your own labelled examples, which is what [chapter 5](05-method.md) describes and [chapter 9](09-confidence.md#a-fallback-gate) builds on.

[^ts-models]: TypeSafe, "Models", documentation page, read 2026-09-30. <https://docs.typesafe.ai/models>
[^winnow]: EldanRing, "Winnow-12B" model card, created 2026-09-20, read 2026-09-30. <https://huggingface.co/EldanRing/Winnow-12B>
[^ollaya-rel]: ollaya-dev, "ollaya" release notes v0.3.0 to v0.7.4, 2026-09-24 to 2026-09-28. <https://github.com/ollaya-dev/ollaya/releases>
[^ollaya-site]: ollaya, "ollaya.dev", project site, read 2026-09-30. <https://ollaya.dev>
[^jevomni]: akhilaaa3, "Jev-Omni" model card, created 2026-09-20, read 2026-09-30. <https://huggingface.co/akhilaaa3/Jev-Omni>
[^gliner]: fastino, "GLiNER2.5-Decide" model card, created 2026-09-23, read 2026-09-30. <https://huggingface.co/fastino/GLiNER2.5-Decide>
[^julia]: SupersonicLabs, "Julia-1" model card, measured 2026-09-24, read 2026-09-30. <https://huggingface.co/SupersonicLabs/Julia-1>
[^td]: LocalLLaMA, "typed-decisions" dataset card and leaderboard, created 2026-09-16, read 2026-09-30. <https://huggingface.co/datasets/LocalLLaMA/typed-decisions>
[^d1]: vLLM Semantic Router, "Decision-1.0-Eos-0.8B" model card, created 2026-09-21, read 2026-09-30. <https://huggingface.co/llm-semantic-router/Decision-1.0-Eos-0.8B>
[^audit]: Lijuan Tang and Yuemeng Zheng, "Typed Decision Models: An Early Evidence Audit and Evaluation Checklist", arXiv 2609.32160, 2026-09-26. <https://arxiv.org/abs/2609.32160>
[^openai]: The New Stack, "OpenAI Decision API on Luna", 2026-09-29. <https://thenewstack.io/openai-decision-api-luna/>
