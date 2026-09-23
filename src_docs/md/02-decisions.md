---
this_file: src_docs/md/02-decisions.md
---

# 2. The shape of a decision

A decision request carries a state and a set of named questions. Both engines in the `ornotto` package accept the same three question kinds, but they build different prompts from them and return different fields. This chapter describes the request and the answer in System One terms, then shows what changes on pcdServer. The `ornotto` package hides most of the difference ([chapter 10](10-package.md)); the parts it cannot hide, such as calibration and limits, are here.

## The state

The state is what the model judges. It can be a string or any JSON value, and every question in the request refers to the same state.

On dohnuts the state shapes the prompt directly:

- A string is used as it is.
- Any other JSON value is printed Python-style, `{"k": v, ...}`, with `", "` and `": "` separators, the way the decider model saw data in training.
- Every array of 8 or more items is rewritten as `[{"_index": 0, ...}, {"_index": 1, ...}, ...]`, so the model can refer to an item by its position.

That makes application state a first-class input. If your assistant knows the open font, the selection and the active window, you can pass them as an object rather than describing them in prose:

```json
{"message": "Why does this pair look too tight?", "window": "Metrics window",
 "selection": ["A", "V"], "font": "Garamond Pro Italic"}
```

pcdServer takes a `context` string of at most 64 KiB. Structured state has to be serialised first; `ornotto` does it with `json.dumps`, so pcdServer sees JSON text where dohnuts sees a Python-style dict.

## The three question kinds

### Choice

A choice picks one option. In System One, `criteria` is either a list of names or an object mapping each name to a description of when it applies:

```json
{"type": "choice", "instructions": "Which team should handle this?",
 "criteria": {"billing": "Charges and invoices", "shipping": "Delivery status", "other": null}}
```

A name without a description is read by its name alone. dohnuts accepts 2 to 255 options per question. Up to 10 options are labelled with the letters A to J; longer lists use single-token labels A to Z, then AA, AB and so on.

pcdServer has no per-option descriptions. A field is a name, one `description` of up to 1,024 bytes, and `choices`, a list of 2 to 256 distinct strings of up to 256 bytes each:

```json
{"name": "team", "description": "Which team should handle this? billing: Charges and invoices; shipping: Delivery status",
 "choices": ["billing", "shipping", "other"]}
```

When `ornotto` translates a choice for pcdServer, it folds the option descriptions into the field description, one `name: description` line per option, and clips the result at 1,024 bytes.

### Yes/no

A yes/no question (`noul`, with `bool` accepted as an alias) returns the probability that the answer is yes. The optional `criteria` object says what counts as each answer:

```json
{"type": "noul", "instructions": "Is this message spam?",
 "criteria": {"true": "Unsolicited advertising", "false": "A legitimate conversation"}}
```

Without criteria, dohnuts shows the options as `no` and `yes`. On pcdServer a yes/no is a field whose choices are exactly `[false, true]`.

### Score

A score places the state on an ordered rubric. `criteria` is a list whose position is the level, starting at zero, or an object keyed by numbers, which dohnuts sorts numerically:

```json
{"type": "score", "instructions": "How frustrated is the customer?",
 "criteria": ["calm", "frustrated", "very frustrated"]}
```

The answer is the expected level, the probability-weighted average of the levels, so a score of 1.44 sits between "frustrated" and "very frustrated". pcdServer has no graded type. `ornotto` sends the levels as the choices `"0"`, `"1"`, `"2"`, lists the level texts in the field description, and computes the expected level from the probabilities pcdServer returns.

## The answer

Each answer carries a `type` matching its question. Beyond that, the fields depend on the kind and the engine.

| Kind | System One fields | What the value means |
|---|---|---|
| choice | `choice`, `probabilities`, `confidence` | the option with the highest probability |
| yes/no | `noul` | the probability of yes, from 0 to 1 |
| score | `score`, `probabilities`, `confidence`, `legend` | the expected level; `legend` maps each level to its text |

`probabilities` covers every option or level and sums to 1. dohnuts adds a `native` block with profile-specific statistics, and `usage.input_tokens`, the tokens it read across every row of the request. pcdServer returns its own shape: `values` with the assembled object, one entry per field in `fields` with `value`, `probability`, `probabilities` and `levels`, and a `metrics` block with timings and cache status.

### The confidence trap

dohnuts reports two numbers with confusing names:

| JSON path | What it is |
|---|---|
| `answers.<name>.confidence` | 1 − H/ln K: one minus the entropy of the distribution over its maximum. 0 means uniform, 1 means certain. `native.certainty` repeats it. |
| `answers.<name>.native.confidence` | the top probability, after temperature scaling |

The two disagree most on yes/no questions. A yes probability of 0.72 has a top probability of 0.72 but an entropy-based `confidence` of 0.14, because 0.72 is not far from the uniform 0.5. If you want to know how likely the answer is to be right, read the top probability. On our router set it also separated right from wrong answers slightly better at low fallback rates ([chapter 9](09-confidence.md)).

`ornotto` sidesteps the names: `Answer.probability` is the top probability for a choice or score and the probability of yes for a yes/no, and `Answer.confidence` is the probability of the answer given, `max(p(yes), p(no))` for a yes/no.

### Isolated score levels

The decider model's recipe scores a rubric one level at a time by default (`isolated_levels: true` in its metadata). Each level becomes its own yes/no row: the question, then `Proposed answer: <level>`, then `Does the proposed answer fit?`. dohnuts reports the yes probabilities as `native.level_fit` and their sum as `native.fit_mass`; normalised, they give `probabilities`, and `score` is their expected value.

A low `fit_mass` is a warning in its own right: no level describes the state well. In one of our FontLab examples, "Loop through masters and print their names" scored 0.63 on a rubric of general type design, the FontLab UI and the FontLab Python API. Every level fitted poorly (fit_mass 0.50) and "general type design" fitted least badly, so the score was wrong and the fit mass said so. Send `"isolated": false` on the question to score all levels in one lettered row instead.

## Calibration

A probability is *calibrated* when answers given with probability 0.8 are right about 80 percent of the time. The dedicated decision models are trained and then tuned for this: decider, kev and laya divide their logits by a fitted temperature before the softmax. decider-0.8b uses T = 1.03 and decider-2b T = 1.3, both read from the model's metadata. jev's probabilities are calibrated by its provider.

pcdServer's probabilities are not calibrated. It computes a softmax over the first tokens of the allowed values only, with no temperature, and reports the model's raw preference among them. A chat model can put 0.998 on an answer that a calibrated model would give 0.9, which is exactly what happened on the router's kern example: decider on dohnuts said `fea` with 0.90, a 4B model on pcdServer said `fea` with 0.998.

!!! warning "Compare confidences only within one kind"
    A 0.9 from dohnuts and a 0.9 from pcdServer are different measurements. Thresholds tuned on one engine do not transfer to the other. Accuracy comparisons are safe, because they use only the winning option. `ornotto` marks every answer with `calibrated`: true for dohnuts, false for pcdServer.

Calibration is a property of the recipe, not a guarantee. On the 67 router queries, decider-0.8b's top probabilities between 0.6 and 0.8 were right 13 times out of 13, while those of 0.95 and above were right 31 times out of 33 ([chapter 9](09-confidence.md)).

## Limits

| | dohnuts (decider profile) | pcdServer |
|---|---|---|
| Endpoint | `POST /v1/systemone` (one request), `POST /predict` (one or an array) | `POST /v1/pcd/decode` |
| State | a string or any JSON value | `context`: a string, up to 64 KiB |
| Questions per request | up to `--max-questions`, 8 by default (`ornotto` starts it with 64) | 1 to 63 fields |
| Options per question | 2 to 255 | 2 to 256 strings, each up to 256 bytes, or exactly `[false, true]` |
| Option descriptions | yes, in `criteria` | no; one field description of up to 1,024 bytes |
| Field names | any question key | up to 128 bytes, unique |
| Graded answers | `score`, with `level_fit` and `fit_mass` | none; use an ordered enum |
| Token budget | 4,096 tokens per question row | the whole rendered request must fit the model context (8,192 for pcdServer's default model); at most 4,096 candidate tokens in all |
| Request body | | 1 MiB |
| Images | no (only the Dohnuts profile reads `state.image`) | no |
