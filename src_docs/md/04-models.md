---
this_file: src_docs/md/04-models.md
---

# 4. Dedicated, fine-tuned and vanilla models

A model's size tells you less about how it will decide than the place its answer is read from. This book sorts every model into one of three families by that place. A **dedicated** model was trained to answer System One questions and has its own readout: a letter at a trained answer slot, a pointer head, or a decision head on an encoder. A **fine-tuned** model is a chat model that someone tuned for a task, sometimes this task, sometimes a neighbouring one. A **vanilla** model is a stock chat model as its publisher released it.

The family decides which engines can run the model. It also decides how much prompt work you have to do before its answers are worth reading.

| family | where the answer comes from | engines in `ornotto` | engines in the benchmark |
|---|---|---|---|
| dedicated | the model's own trained readout | dohnuts (decider, kev, Dohnuts), pcdServer (decider only, as a chat model) | jev, dohnuts, slot, pcdServer, laya runtimes, PyTorch, ExecuTorch |
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
| decider-0.8b | [DreamBlooms/decider-0.8b-GGUF](https://huggingface.co/DreamBlooms/decider-0.8b-GGUF), [mradermacher/decider-0.8b-GGUF](https://huggingface.co/mradermacher/decider-0.8b-GGUF) | Apache-2.0 | 62/67 and 61/67 on dohnuts (Metal), 51 ms |
| decider-2b | [DreamBlooms/decider-2b-GGUF](https://huggingface.co/DreamBlooms/decider-2b-GGUF), [cosetoenor/decider-2b-GGUF](https://huggingface.co/cosetoenor/decider-2b-GGUF) | Apache-2.0 | 59/67 and 62/67 on dohnuts (Metal); 60/60 on pcdServer |
| decider-4b | [Mapika/decider-4b](https://huggingface.co/Mapika/decider-4b), in Mapika's PyTorch package | Apache-2.0 | 63/67 and 65/67, 348 ms |
| decider-35b-a3b | [mradermacher/decider-35b-a3b-GGUF](https://huggingface.co/mradermacher/decider-35b-a3b-GGUF) | Apache-2.0 | 64/67 and 64/67 on dohnuts (Metal), 266 ms, 21 GB |

The DreamBlooms 2B build is a newer checkpoint with calibration-aware reinforcement learning and a temperature of 1.3. On this set it scores the same as the older 2B builds: calibration work shows up in the confidences, which the accuracy column does not see.

decider runs on dohnuts with its own readout, and on pcdServer as an ordinary chat model. The two are not the same measurement. [Chapter 6](06-results.md#one-set-of-weights-three-scores) shows the 0.8B model scoring 62 through its readout and 55 through pcdServer.

In `ornotto`, `decider-0.8b` and `decider-2b` are registered and default to dohnuts:

```python
import ornotto

fast = ornotto.Decider("decider-0.8b")                        # dohnuts, the trained readout
same_weights = ornotto.Decider("decider-0.8b", engine="pcd")  # pcdServer, as a chat model
```

### kev

[jaredpalmer/kev](https://github.com/jaredpalmer/kev) is a LoRA over Qwen3.5 plus a bilinear pointer head. The prompt marks the decision point and the end of every option with special tokens, and the head scores each option by the dot product of two projected hidden states. The benchmark ran the [mys/kev-0.8b-GGUF](https://huggingface.co/mys/kev-0.8b-GGUF) and kev-4b conversions through laya.cpp's `laya serve`. kev-4b reached 62/67 translated but 55/67 direct, and took 1,103 ms per query. kev-0.8b dropped to 45/67 on untranslated text.

`ornotto` registers `kev-0.8b` from [DreamBlooms/kev-0.8b-GGUF](https://huggingface.co/DreamBlooms/kev-0.8b-GGUF) (Apache-2.0) on dohnuts, which reads the same pointer head. That build was not part of the benchmark run.

### Dohnuts

[PsiACE/Dohnuts](https://huggingface.co/PsiACE/Dohnuts-0.1.0-0.8B) is the model dohnuts.cpp was first written for: Qwen3.5-0.8B with language LoRA adapters and one scalar head read at each candidate marker. It also takes images through an `mmproj` projector. `ornotto` registers it as `dohnuts-0.8b`.

!!! warning "Non-commercial weights"
    The Dohnuts weights are licensed CC-BY-NC-SA-4.0. The engine is Apache-2.0, the weights are not. Dohnuts was not benchmarked here and is not the `ornotto` default.

### laya-multilingual

[convaiinnovations/laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) (Apache-2.0) is an encoder, not a chat model: mmBERT-base with a decision head that reads a marker per option, plus an act head that says whether to answer directly or escalate. It shares a 1,024-token budget between the question, the options and the state, so the benchmark gave it short task descriptions. The Neural Engine exports hold 96 tokens and got a compact prompt of their own.

The same checkpoint ran on six runtimes (MLX, Core AI, Core ML on the Neural Engine, ONNX Runtime, laya.cpp, and llama.cpp serving embeddings with the head in Python). Every run at 8-bit precision or better with the full prompt scored 52/67 translated and 49/67 direct, so the runtime changed only the speed: 6.9 ms per query on MLX, 57.6 ms on laya.cpp. The compact prompt cost four to five points. Of the two 4-bit conversions, one lost a point and the other lost 16. `ornotto` does not run laya.

### jev

jev is TypeSafe's hosted System One model, reached through OpenRouter's System One API as `jev-latest`. It scored 65/67 in both modes, the best result in the benchmark, at 466 ms per query over the network. Its internals are not public, so the benchmark treats it as the reference, not as a design to copy. dohnuts answers the same request shape, which is why pydantic-ai's TypeSafe model can drive a local engine ([chapter 11](11-typed.md)).

## Fine-tuned models

These are chat models tuned by third parties. None of them has a trained answer slot, so every one ran on pcdServer, which scores the first token of each allowed value under the model's chat template.

[n4ze3m/Qwen3.5-4B-Hmm](https://huggingface.co/n4ze3m/Qwen3.5-4B-Hmm) (Apache-2.0) is the exception worth knowing: it was tuned for this kind of pick-one decision. On pcdServer it scored 64/67 translated and 65/67 direct at every quantization from Q4 to BF16, the best local result in the benchmark, at 88 to 95 ms per query. Read through its own letter readout on llama-server (the `slot` rows), the same weights scored 62/67 and 63/67 and took three times as long.

The rest spread from close to the top to the bottom of the table:

- The empero-ai Qwen3.8 distills reached 62/67 at 4B and 9B, and 49/67 at 2B.
- The coding models ([Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF) 3B and 7B, jica98's Qwen3.5-4B super-coder) scored 60 to 61.
- Small models tuned for routing, deciding or retrieval scored worse than a vanilla model of the same size: pulse-0.6b 54, lq-decide-1.7b 50, lq-decide-0.6b 11, lyco-router-0.6b 35, Qwen3-Reranker-0.6B 40.
- Qwen2.5-0.5B-PCb and EUAIAct-Qwen2.5-0.5B reached 27 and 20.

A tune for a nearby task does not carry over to this one. If you pick a fine-tuned model, check it on your own questions first.

`ornotto` registers `qwen3.5-4b-hmm` (the Q4_K_M file, 2.7 GB) on pcdServer:

```python
careful = ornotto.Decider("qwen3.5-4b-hmm")
```

## Vanilla models

Vanilla chat models need nothing but a chat template that llama.cpp understands, so any GGUF works on pcdServer. The benchmark ran Qwen3.5 (0.8B, 2B, 4B, 9B), Qwen3 (0.6B, 1.7B, 4B, 8B), Qwen2.5 (0.5B, 3B), Qwen1.5 (0.5B, 1.8B, 4B) and PrismML's Bonsai (1.7B, 27B), most of them at several quantizations.

- Qwen3.5-4B reached 62/67 and 63/67 at Q4; unsloth's Q8 build reached 63/67 and 64/67, one point below the Hmm tune.
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
- If you have a model already, or need one that no one has tuned, a vanilla Qwen3.5 on pcdServer works with no training at all. Qwen3.5-2B at Q3 is the smallest vanilla model that stays within one point of the dedicated 0.8B model.

[Chapter 7](07-quantization.md) shows how far each family can be quantized, and [chapter 12](12-choosing.md) turns these results into a choice.
