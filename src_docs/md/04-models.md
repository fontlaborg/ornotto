---
this_file: src_docs/md/04-models.md
---

# 4. Dedicated, fine-tuned and vanilla models

A model's size tells you less about how it will decide than the place its answer is read from. This book sorts every model into one of three families by that place. A **dedicated** model was trained to answer System One questions and has its own readout: a letter at a trained answer slot, a pointer head, or a decision head on an encoder. A **fine-tuned** model is a chat model that someone tuned for a task, sometimes this task, sometimes a neighbouring one. A **vanilla** model is a stock chat model as its publisher released it.

The family decides which engines can run the model. It also decides how much prompt work you have to do before its answers are worth reading.

| family | where the answer comes from | engines in `ornotto` | engines and runtimes in the benchmark |
|---|---|---|---|
| dedicated | the model's own trained readout | dohnuts (decider, kev, Dohnuts), ollaya (its registry's models), pcdServer (as chat models) | jev, dohnuts, slot, pcdServer, ollaya, the authors' System One servers, llama.cpp embeddings, MLX, Core ML, Core AI, ONNX Runtime, PyTorch, ExecuTorch |
| fine-tuned | the first token of each allowed value, under a chat template | pcdServer | pcdServer, slot (Hmm readout) |
| vanilla | the first token of each allowed value, under a chat template | pcdServer | pcdServer |

The best row of every model in the benchmark, grouped by family:

--8<-- "tables/families.html"

## Dedicated models

### decider

[Mapika/decider](https://github.com/Mapika/decider) is a family of full fine-tunes of Qwen3.5 trained to answer System One questions. The prompt is fixed by training: `Context:` and the state, then the question, the options lettered `(A)`, `(B)`, …, and `Answer: (`. The model is read at that last token, and only the logits of the option letters count. They are divided by a temperature from the checkpoint's `decider.json` (1.03 for the 0.8B model) before the softmax, so the probabilities are calibrated by the recipe.

The benchmark ran four sizes, from several converters:

| model | GGUF source | licence | best result (translated / direct) |
|---|---|---|---|
| decider-0.8b | [DreamBlooms/decider-0.8b-GGUF](https://huggingface.co/DreamBlooms/decider-0.8b-GGUF), [mradermacher/decider-0.8b-GGUF](https://huggingface.co/mradermacher/decider-0.8b-GGUF) | Apache-2.0 | 62/67 and 62/67 on dohnuts (Metal), mradermacher `Q6_K`, 54 ms; the DreamBlooms `Q8_0` file `ornotto` registers: 62/67 and 61/67, 52 ms |
| decider-2b | [DreamBlooms/decider-2b-GGUF](https://huggingface.co/DreamBlooms/decider-2b-GGUF), [cosetoenor/decider-2b-GGUF](https://huggingface.co/cosetoenor/decider-2b-GGUF) | Apache-2.0 | 59/67 and 62/67 on dohnuts (Metal); 60/60 on pcdServer |
| decider-4b | [Mapika/decider-4b](https://huggingface.co/Mapika/decider-4b), in Mapika's PyTorch package | Apache-2.0 | 63/67 and 65/67, 348 ms |
| decider-35b-a3b | [mradermacher/decider-35b-a3b-GGUF](https://huggingface.co/mradermacher/decider-35b-a3b-GGUF) | Apache-2.0 | 64/67 and 64/67 on dohnuts (Metal), 266 ms, 21 GB |

The DreamBlooms 2B build is a newer checkpoint with calibration-aware reinforcement learning and a temperature of 1.3. On this set it scores the same as the older 2B builds: calibration work shows up in the confidences, which the accuracy column does not see.

ollaya's `decider:0.8b` runs the 0.8B weights as a float32 ONNX graph on the CPU: 61/67 and 60/67, at 285 ms per query.

decider runs on dohnuts with its own readout, and on pcdServer as an ordinary chat model. The two are not the same measurement. [Chapter 6](06-results.md#one-set-of-weights-three-scores) shows the 0.8B model scoring 62 through its readout and 55 through pcdServer.

In `ornotto`, `decider-0.8b` and `decider-2b` are registered and default to dohnuts:

```python
import ornotto

fast = ornotto.Decider("decider-0.8b")                        # dohnuts, the trained readout
same_weights = ornotto.Decider("decider-0.8b", engine="pcd")  # pcdServer, as a chat model
```

### kev

[jaredpalmer/kev](https://github.com/jaredpalmer/kev) is a LoRA over Qwen3.5 plus a bilinear pointer head. The prompt marks the decision point and the end of every option with special tokens, and the head scores each option by the dot product of two projected hidden states. The benchmark ran the [mys/kev-0.8b-GGUF](https://huggingface.co/mys/kev-0.8b-GGUF) and kev-4b conversions through laya.cpp's `laya serve`. kev-4b reached 62/67 translated but 55/67 direct, and took 1,103 ms per query. kev-0.8b dropped to 45/67 on untranslated text.

ollaya's `kev:0.8b` reads the same LoRA and pointer head over Qwen3.5-0.8B-Base as a float32 ONNX graph and scored 60/67 translated and 62/67 direct, at 268 ms.

`ornotto` registers `kev-0.8b` from [DreamBlooms/kev-0.8b-GGUF](https://huggingface.co/DreamBlooms/kev-0.8b-GGUF) (Apache-2.0) on dohnuts, which reads the same pointer head. That build was not part of the benchmark run.

### Dohnuts

[PsiACE/Dohnuts](https://huggingface.co/PsiACE/Dohnuts-0.1.0-0.8B) is the model dohnuts.cpp was first written for: Qwen3.5-0.8B with language LoRA adapters and one scalar head read at each candidate marker. It also takes images through an `mmproj` projector. `ornotto` registers it as `dohnuts-0.8b`.

!!! warning "Non-commercial weights"
    The Dohnuts weights are licensed CC-BY-NC-SA-4.0. The engine is Apache-2.0, the weights are not. Dohnuts was not benchmarked here and is not the `ornotto` default.

### laya-multilingual

[convaiinnovations/laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) (Apache-2.0) is an encoder with a decision head, not a chat model; [chapter 3](03-engines.md#laya) describes its readout and its token budget.

The same checkpoint ran on eight engines and runtimes. Every method at 8-bit precision or better with the full prompt scored 52/67 translated and 49/67 direct, except an MXFP8 conversion on MLX at 53/67, so the engine or runtime changed only the speed: 6.9 ms per query on MLX, 12.3 ms in ollaya, 57.6 ms on laya.cpp. The compact prompt of the Neural Engine exports cost four to five answers. The 4-bit conversions spread widely: one lost an answer, one lost 16, the MXFP4 conversion lost 8, and the Q4_0 encoder from laya-neutron, read with its head converted to GGUF, gained two, to 54/67. `ornotto` runs laya only through ollaya (`ollaya-laya-multilingual`, `ollaya-laya-en`).

### jev

jev is TypeSafe's hosted System One model and the best result in the benchmark ([chapter 3](03-engines.md#jev)). Its internals are not public, so the benchmark treats it as the reference, not as a design to copy. dohnuts answers the same request shape, which is why pydantic-ai's TypeSafe model can drive a local engine ([chapter 11](11-typed.md)).

### Later dedicated models

A second benchmark round added the decision models published after the first one. Several were published as open alternatives to jev, and some say so in their names. They use the readouts described in [chapter 3](03-engines.md#a-linear-head-on-a-hidden-state-jev-omni), from letter logits to contrastive heads, and each ran on the runtime its authors provide. The licences are taken from the model cards.

| model | what it is | source | licence | best result (translated / direct, ms/query) |
|---|---|---|---|---|
| rune-26b-a4b | Gemma 4 26B-A4B mixture of experts, option-letter readout | [surogate/rune-26b-a4b-GGUF](https://huggingface.co/surogate/rune-26b-a4b-GGUF), version 1 (gated) | Apache-2.0 | 65/67 and 57/67, Q3_K_M on slot, 367 ms |
| winnow-12b | Gemma 4 12B, option-label logits | EldanRing, through ollaya's `winnow:12b` | Apache-2.0 | 64/67 and 65/67, Q8_0 in ollaya, 891 ms |
| neohorse-4b | NeoHorse-1-4B, packed prefill with a pointer head | [TokenRhythm/NeoHorse-Jev-4B-GGUF](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B-GGUF) | Apache-2.0 | 64/67 and 64/67, Q8_0, 273 ms |
| jev-omni | Gemma 4 12B-class, 256-way head on the last hidden state | [akhilaaa3/Jev-Omni](https://huggingface.co/akhilaaa3/Jev-Omni), as [GGUF](https://huggingface.co/ngquocvinh/Jev-Omni-GGUF) and [MLX](https://huggingface.co/Ruiruiz30/Jev-Omni-MLX-4bit) | Apache-2.0 | 64/67 and 64/67, Q3_K_M, 1,222 ms |
| openjev-35b-a3b | Qwen3.5-35B-A3B, option-letter readout, uncalibrated | [apus-ailab/APUS-OpenJev-v1-35B-A3B-GGUF](https://huggingface.co/apus-ailab/APUS-OpenJev-v1-35B-A3B-GGUF), and an MLX 4-bit build | Apache-2.0 | 63/67 and 64/67 on pcdServer, 297 ms |
| jeb-35b-a3b | Qwen3.6-35B-A3B, softmax restricted to the answer tokens | [szybkie-ai/jeb-35b-a3b](https://huggingface.co/szybkie-ai/jeb-35b-a3b), GGUF by mradermacher | Apache-2.0 weights, MIT code | 63/67 and 63/67, Q3_K_M, 333 ms |
| lev-4b | LoRA on Qwen3.5-4B, one-token option codes | [interfaze-ai/lev](https://huggingface.co/interfaze-ai/lev) | Apache-2.0 | 63/67 and 64/67, 2,204 ms |
| jevk5-4b | Qwen3.5-4B, option-letter readout | [alibiserikbay/JevK5-GGUF](https://huggingface.co/alibiserikbay/JevK5-GGUF) | Apache-2.0 | 62/67 and 63/67, Q4_K_M on slot, 351 ms |
| imajev-4b | LoRA on Qwen3.5-4B, 256-code readout | [mohit67890/imajev-4b](https://huggingface.co/mohit67890/imajev-4b) | Apache-2.0 | 62/67 and 64/67, 363 ms |
| gliner25-decide | DeBERTa-v3-large with a label head, English only | [fastino/GLiNER2.5-Decide](https://huggingface.co/fastino/GLiNER2.5-Decide), as Core AI, ONNX and Core ML builds | Apache-2.0 (DeBERTa-v3: MIT) | 61/67, Core AI, 27 ms |
| leo-1.7b | LoRA on Qwen3-1.7B-Base, listwise pointer head | [Suparva/leo-1.7b](https://huggingface.co/Suparva/leo-1.7b) | Apache-2.0 | 57/67 and 62/67, 136 ms |
| von | ModernBERT-large, order-invariant option markers, English only | [wfzyx/von](https://huggingface.co/wfzyx/von): 1.2 as ONNX, 1.1 in ollaya | Apache-2.0 | 57/67, ONNX, 53 ms |
| decision-eos | Qwen3.5-0.8B with an endpoint head | vLLM Semantic Router, through ollaya's `decision:eos` | Apache-2.0 | 57/67 and 56/67, 323 ms |
| semif-4b-nli | Qwen3.5-4B entailment cross-encoder | [jacksodj/semif-4b-nli-v5-mlx](https://huggingface.co/jacksodj/semif-4b-nli-v5-mlx) | MIT | 51/67 and 49/67, 121 ms |
| clm-8b | Qwen3-8B encoder with contrastive heads | [czl/CLM-v0.1-8B-GGUF](https://huggingface.co/czl/CLM-v0.1-8B-GGUF), MLX builds, ollaya's `clm:8b` | Apache-2.0 | 39/67 and 28/67, Q8_0, 108 ms |
| decima-small | multilingual late-interaction encoder | [amyrmahdy/decima-small](https://huggingface.co/amyrmahdy/decima-small) | Apache-2.0 | 37/67 and 38/67, int8, 12 ms |
| pulse-decide-150m | ModernBERT-base pair cross-encoder, English only | [RouterML/pulse-decide-150m](https://huggingface.co/RouterML/pulse-decide-150m) | Pulse Research Preview Licence | 34/67, 18 ms |
| lumma-fev-0.6b | 0.6B decoder trained from scratch, pointer head | [FrontiersMind/Lumma-fev-0.6b](https://huggingface.co/FrontiersMind/Lumma-fev-0.6b) | Apache-2.0 | 33/67 and 28/67, 70 ms |
| julia-1 | mmBERT-small with a laya-style head | [SupersonicLabs/Julia-1](https://huggingface.co/SupersonicLabs/Julia-1) | Apache-2.0 | 31/67 and 31/67, MLX, 6.8 ms |
| gliclass-large | DeBERTa-v3-large zero-shot classifier, Knowledgator | through ollaya's `gliclass:large` | Apache-2.0 | 26/67, 60 ms |
| nli-modernbert-large | ModernBERT-large zero-shot NLI, Moritz Laurer | through ollaya's `nli:modernbert-large` | Apache-2.0 | 20/67, 23 ms |

An empty direct score means the model was trained on English only, so only the translated text was sent to it.

Three licence notes travel with the rows. Pulse Decide 150M is a research preview whose training data carries non-commercial and terms-of-service restrictions; it is in the tables with that note and is not cleared for use in a product. The MXFP8 and MXFP4 conversions of laya declare no licence, and the MLX library that runs them, mlx-embeddings, is GPL-3.0. And two models were left out on purpose: Launchables' Myles encoders are gated, and their evaluation licence does not allow benchmark results to be published without the publisher's review.

Some of these models are in `ornotto` without any extra runtime: JevK5 and APUS-OpenJev as pcdServer models, and winnow, von, decision-eos, CLM, GLiClass and the ModernBERT NLI model as ollaya models ([chapter 10](10-package.md#registered-models)). The rest need the runtimes their authors publish.

## Fine-tuned models

These are chat models tuned by third parties. None of them has a trained answer slot, so every one ran on pcdServer, which scores the first token of each allowed value under the model's chat template.

[n4ze3m/Qwen3.5-4B-Hmm](https://huggingface.co/n4ze3m/Qwen3.5-4B-Hmm) (Apache-2.0) is the exception worth knowing: it was tuned for this kind of pick-one decision. On pcdServer it scored 64/67 translated and 65/67 direct at every quantization from Q4 to BF16, the best local result in the benchmark, at 88 to 95 ms per query. Read through its own letter readout on llama-server (the `slot` rows), the same weights scored 62/67 and 63/67 and took three times as long.

The rest spread from close to the top to the bottom of the table:

- The empero-ai Qwen3.8 distills reached 62/67 at 4B and 9B, and 49/67 at 2B.
- The coding models ([Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) 3B and 7B, jica98's Qwen3.5-4B super-coder) scored 60 to 61.
- Small models tuned for routing, deciding or retrieval scored worse than a vanilla model of the same size: pulse-0.6b 54, lq-decide-1.7b 50, lq-decide-0.6b 11, lyco-router-0.6b 35, Qwen3-Reranker-0.6B 40.
- DavidAU's Qwen3 Zero-Coder 0.8B scored 18 to 42 across seven quantizations, with no order by bit count, well below vanilla Qwen3.5-0.8B's best of 57.
- Qwen2.5-0.5B-PCb reached 27 at best, one answer below vanilla Qwen2.5-0.5B's 28, and EUAIAct-Qwen2.5-0.5B reached 20.

A tune for a nearby task does not carry over to this one. If you pick a fine-tuned model, check it on your own questions first.

`ornotto` registers `qwen3.5-4b-hmm` (the Q4_K_M file, 2.7 GB) on pcdServer:

```python
careful = ornotto.Decider("qwen3.5-4b-hmm")
```

## Vanilla models

Vanilla chat models need nothing but a chat template that llama.cpp understands, so any GGUF works on pcdServer. The benchmark ran Qwen3.5 (0.8B, 2B, 4B, 9B), Qwen3 (0.6B, 1.7B, 4B, 8B), Qwen2.5 (0.5B, 3B), Qwen1.5 (0.5B, 1.8B, 4B) and PrismML's Bonsai (1.7B, 27B), most of them at several quantizations.

- Qwen3.5-4B reached 62/67 and 63/67 at Q4; unsloth's Q8 build reached 63/67 and 64/67, one answer below the Hmm tune.
- Qwen3.5-2B at Q3_K_M reached 61/67 translated and 62/67 direct at 43 ms per query from a 1.2 GB file.
- Qwen3.5-0.8B reached 57/67 at Q5 and 55/67 at Q8, at about 30 ms.
- Qwen2.5-3B reached 62/67 on translated text but only 57 to 60 on direct text: it handles English well and other languages less well.
- Qwen1.5 scored 42/67 at best, at 4B. An older generation is no substitute for a smaller new one.
- Bonsai-27B at 1 bit (3.8 GB) reached 62/67 and 63/67, but took 514 ms per query.

Licences vary within the Qwen family. Qwen3 and Qwen3.5 are Apache-2.0. Qwen2.5-3B and Qwen2.5-Coder-3B use the Qwen Research licence, and Qwen1.5 the Tongyi Qianwen research licence. Read the model card before you ship one.

`ornotto` registers `qwen3.5-0.8b`, `qwen3.5-2b` and `qwen3.5-4b` on pcdServer. Any other GGUF works by path or by Hugging Face file:

```python
mine = ornotto.Decider("~/models/Qwen_Qwen3.5-2B-Q3_K_M.gguf")                            # a local file
hub = ornotto.Decider("hf:bartowski/Qwen_Qwen3.5-2B-GGUF/Qwen_Qwen3.5-2B-Q3_K_M.gguf")    # downloaded on first use
```

An unregistered GGUF runs on pcdServer only. To run one on dohnuts, pass the profile JSON as `metadata=` (and the scorer head as `head=` for kev or Dohnuts): dohnuts needs to know which readout the weights were trained for.

## Which family for which job

- If you want calibrated probabilities you can threshold, use a dedicated model on dohnuts. Only the dedicated readouts divide by a fitted temperature.
- If you want the most accurate local answer and can spend about 90 ms and 2.7 GB, use Qwen3.5-4B-Hmm on pcdServer.
- If you want the best local score and have the memory, rune-26b-a4b at Q3_K_M (13.5 GB) matched jev on translated text. NeoHorse-Jev-4B at Q8_0 (5.2 GB) scored 64/67 in both modes.
- If you have a model already, or need one that no one has tuned, a vanilla Qwen3.5 on pcdServer works with no training at all. Qwen3.5-2B at Q3 is the smallest vanilla model that stays within one answer of the dedicated 0.8B model.

[Chapter 7](07-quantization.md) shows how far each family can be quantized, and [chapter 12](12-choosing.md) turns these results into a choice.
