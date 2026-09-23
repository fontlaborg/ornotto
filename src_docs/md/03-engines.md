---
this_file: src_docs/md/03-engines.md
---

# 3. Five ways to read an answer

A decision engine turns a state and a question into a prompt, runs the model once, and reads a probability for each allowed answer out of the result. The engines in this book differ in all three steps: what the prompt looks like, where in the model they read, and what they return. Those differences decide which models an engine can run, how fast it answers, and whether its probabilities mean what they say.

Five engines ran in our benchmark. Two of them, dohnuts and pcdServer, are the engines the `ornotto` package bundles. jev is the hosted reference. slot is a readout our benchmark harness builds on top of a stock llama-server, and laya is a different kind of model altogether.

## jev

jev is TypeSafe's hosted System One model. You send the request shape from [chapter 2](02-decisions.md) to `/v1/systemone` and get answers with `choice`, `confidence` and `probabilities`, plus `usage.billing_units`. Our harness reaches it through OpenRouter's System One API as `jev-latest`.

What jev does inside is not public: we know its inputs and outputs, not its prompt or its readout. Its answers are calibrated by its provider. On the router set it scores 65 of 67, translated or direct, at 466 ms per query measured from our client, network included.

jev matters to the local engines in two ways. It sets the accuracy to beat, and it defined the API that dohnuts and pydantic-ai's `TypeSafeModel` speak.

## dohnuts

dohnuts ([dohnuts.cpp](https://github.com/DreamBlooms/dohnuts.cpp)) is a C++ server on llama.cpp that runs models trained for System One decisions, each through its own *profile*. The metadata JSON that ships with a model names the profile:

- **decider** ([Mapika/decider](https://huggingface.co/Mapika/decider-0.8b)): a full fine-tune of Qwen3.5 read at an answer slot.
- **kev** ([jaredpalmer/kev](https://huggingface.co/jaredpalmer/kev-0.8b)): a LoRA plus a bilinear pointer head over the hidden states at a decide marker and at the end of each option.
- **Dohnuts** ([PsiACE/Dohnuts](https://huggingface.co/PsiACE/Dohnuts-0.1.0-0.8B)): one scalar head over the hidden state at each candidate marker, with image input.

The decider profile is the one most of this book measures. For each question it builds one row in the layout the model was trained on:

```text
Context:
<state>

Question: <instructions>
Options:
(A) docs: answer a question about how FontLab works, from the documentation
(B) python: …
Answer: (
```

The model reads the row once. dohnuts takes the logits of the option-letter tokens at the position after `Answer: (`, divides them by the model's temperature (1.03 for decider-0.8b), and applies a softmax. Nothing is generated: the letter the model would write next is scored, never written.

Every question is its own row, and an isolated score is one row per level. Upstream dohnuts cleared the model's memory before each row and decoded it from scratch, so a request with four questions paid for its state four times. Our fork reuses the decoded state across the rows of a request; [chapter 8](08-speed.md) has the measurements and the pull request.

dohnuts batches concurrent requests at its queue and says which batch served a call in the `X-Dohnuts-Batch-Id` and `X-Dohnuts-Batch-Offset` headers. Its replies carry no timings.

The same binary runs on the CPU or, built with `-DDOHNUTS_METAL=ON` and started with `--gpu-layers -1`, on Apple's GPU. With decider-0.8b at Q8_0, the Metal build answers a router query in 52 ms and the CPU build (8 threads) in 275 ms, with the same 62 of 67. Qwen3.5 is a hybrid of 18 gated delta-net layers and 6 attention layers, and the delta-net layers dominate CPU time.

## pcdServer

pcdServer ([stephanj/pcdServer](https://github.com/stephanj/pcdServer)) implements Parallel Constrained Decoding. It runs any chat GGUF that llama.cpp supports and needs no special training, because it asks the model to write a JSON object and then scores only the tokens that could legally come next.

The prompt uses the model's own chat template. The system turn is fixed text followed by the fields:

```text
You are a precise structured-data extraction engine. Read the user's text and decide the value of
every field below. Each field must be set to exactly one of its allowed values. Respond only with a
JSON object containing every field.

Fields:
- "task": <description>. Allowed values: "docs", "python", "fea", "vfj", "sample"

Output format:
{
  "task": <value>
}
```

The user turn is the context. The assistant turn opens the JSON object, after Qwen3.5's empty `<think></think>` block.

A decode then runs in phases:

1. **Schema prefix.** The system prompt depends only on the fields, so pcdServer decodes it once and saves a full checkpoint of the model's state. A later request with the same fields restores the checkpoint instead of decoding again.
2. **Dynamic context.** The context, the end of the user turn and the start of the assistant turn are decoded after the prefix.
3. **Broadcast.** The finished sequence is copied into one sequence per field.
4. **Field suffixes.** Each field's sequence gets its own member prefix, `  "task": "`, and all of them are decoded in one batch, with logits only on the last token of each.
5. **Scoring.** pcdServer applies a softmax over the first tokens of the allowed values only. A boolean field ends at the colon, so the scored tokens are ` true` and ` false`.

The expensive part, the context, is decoded once however many fields a request has. Each extra field adds only a short suffix to one batch.

### The collision tree

Two allowed values can start with the same token, such as `kern pair` and `kern class`. pcdServer then resolves them level by level: the winning group of the first token stays live and is expanded with its next token, until every live candidate differs. `levels` in the reply reports how many levels were needed, and each level costs another forward pass. In one of our FontLab examples, the choices `kern pair`, `kern class`, `kerning panel settings` and `class definition` needed 3 levels and 5 forward passes.

Only the winning group is expanded. A losing group's probability is split **equally** among its members, so two losing options that share a first token always report the same probability, whatever the model thought of them. In a 14-option panel example, "Font Info" and "Font Audit" both came back at 0.0105. If the probability of an alternative matters to you, give it a distinct first word.

### What pcdServer returns

`values` holds the assembled object and `fields[]` holds `value`, `probability`, `probabilities` and `levels` for each field. `metrics` reports `elapsedMs`, `forwardPasses`, `schemaCacheStatus` (`miss`, `hit` or `fallback`), `checkpointBytes` and the milliseconds of each phase. The probabilities are a raw softmax, not temperature-scaled ([chapter 2](02-decisions.md#calibration)).

With the same decider-0.8b Q8_0 file that dohnuts reads at its answer slot, pcdServer answers a router query in 28 ms, the fastest accurate path in this book. It scores 55 of 67 translated, against 62 for the answer-slot readout: the decider model was trained to answer at `Answer: (`, not inside a JSON object. With a model trained for chat, Qwen3.5-4B-Hmm at Q8_0, pcdServer scores 64 of 67 at 88 ms.

## slot

slot is how our benchmark harness reads a decision model through a stock `llama-server`, with no decision-specific server at all. It asks for one token and the log-probabilities of the top candidates:

```json
{"prompt": "...", "n_predict": 1, "n_probs": 100, "temperature": 0, "cache_prompt": false}
```

and then does the readout on the client, in one of two ways:

- **decider readout.** The prompt is the tokens of `Context:\n<state>` followed by the tokens of the question and options, tokenized separately as the decider package does. The harness looks up the log-probabilities of the option-letter token ids, divides them by the model's temperature and applies a softmax.
- **Hmm readout.** For [n4ze3m/hmm](https://github.com/n4ze3m/hmm) models, the prompt is a Qwen chat turn with thinking turned off: the state, the question, one `A: name — description` line per option, and `Return only the option letter.` The harness sums the probabilities of every top token whose trimmed text is a single option letter, then renormalises over the options.

A letter that falls outside the top 100 tokens gets probability 0, and the harness counts it as a miss.

slot is the control for dohnuts. On every decider GGUF we ran, dohnuts's Metal build picked the same task as the decider readout on slot for 106 of 106 texts, with probabilities at most 0.0004 apart: dohnuts reproduces decider's own readout. slot pays for its generality with a round trip to tokenize and one to complete, and answers the router question in 65 ms with decider-0.8b Q8_0, against 52 ms for dohnuts.

## laya

laya ([convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya-multilingual)) is not a language model. It is a multilingual encoder, mmBERT-base, with a decision head trained for System One questions. Its input is one sequence:

```text
[CLS] choice question: <instructions> [SEP] [MASK] <option 1> [MASK] <option 2> … [SEP] <state> [SEP]
```

The head reads the encoder's hidden states at the `[MASK]` in front of each option and scores them. Probabilities are calibrated with a temperature chosen by bucket, first by the number of options and then by question type. A second head, the *act head*, returns `action.act_probability`: the probability that the question should be answered directly rather than escalated. It is the only built-in abstain signal among the engines here, and our benchmark does not use it yet.

An encoder reads its whole input in one pass and never decodes, so laya is fast: on MLX it answers a router query in 6.9 ms, and a compact Core ML export on the Neural Engine in 4.2 ms. The price is accuracy and length. laya-multilingual scores 52 of 67 translated and 49 direct, and its encoders share a budget of 1,024 tokens between the question, the options and the state. The Neural Engine exports hold 96 tokens in all, so they get a compact prompt, and their load time runs to about 20 seconds.

The same checkpoint ran on six runtimes in our benchmark: MLX, Core ML on the Neural Engine, Core AI, ONNX Runtime, llama.cpp as an embedding server with the head on the client, and laya.cpp, which also serves the kev GGUFs. [Chapter 6](06-results.md) lists them all.

## Side by side

| | jev | dohnuts | pcdServer | slot | laya |
|---|---|---|---|---|---|
| Runs | hosted | local, llama.cpp | local, llama.cpp | local, stock llama-server | local, MLX, Core ML, ONNX, llama.cpp |
| Models | jev | decider, kev, Dohnuts | any chat GGUF | decider, Hmm | laya checkpoints |
| Prompt | not public | the model's trained layout | chat template and JSON schema | the model's trained layout | encoder sequence with `[MASK]` markers |
| Scored | not public | option letters at `Answer: (` | first tokens of allowed values | option letters in the top 100 | hidden state at each `[MASK]` |
| Calibrated | yes | yes, temperature from metadata | no | yes, temperature applied by the client | yes, by bucket |
| Extra questions cost | not public | a full row each | a short suffix each | a full request each | a full pass each |
| Reuse across requests | not public | the state prefix of multi-row requests (our fork) | schema prefix checkpoints (LRU) | none (`cache_prompt: false`) | none |
| Router accuracy, best row | 65/67 | 64/67 (decider-35b-a3b) | 64/67 (Qwen3.5-4B-Hmm) | 64/67 (decider-35b-a3b) | 52/67 |
| ms per query, 0.8B decider | | 52 (Metal), 275 (CPU) | 28 | 65 | 7 (laya on MLX) |

The best dohnuts row, decider-35b-a3b at Q4, answers in 266 ms; pcdServer's best, Qwen3.5-4B-Hmm at Q8_0, in 88 ms.
