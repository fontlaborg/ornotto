---
this_file: src_docs/md/01-deciding.md
---

# 1. Deciding, not generating

A System One decision asks a language model to pick, not to write. You hand it a *state* (a message, a ticket, a slice of application data) and a set of named *questions*, each with a closed set of answers. The model returns one probability for every allowed answer. It never produces free text, so there is nothing to parse, repair or retry: the answer is always one of the values you listed.

This book is about running those decisions on your own machine. It compares five ways of reading a decision out of a model, 208 benchmark methods, and the Python package, `ornotto`, that puts the two local engines behind one API.

## What a decision looks like

A decision request has two parts. The state is whatever the model should judge. The questions say what to judge about it:

```json
{
  "state": "Rename every selected glyph that ends in .sc to .smcp, in all open fonts",
  "questions": {
    "task":       {"type": "choice", "instructions": "What does the user want?",
                   "criteria": {"docs": "an explanation", "python": "a script", "fea": "feature code"}},
    "wants_code": {"type": "noul",   "instructions": "Does the user want code they can run?"},
    "risk":       {"type": "score",  "instructions": "How much existing data could this change?",
                   "criteria": ["none", "some glyphs", "whole fonts"]}
  }
}
```

There are three kinds of question:

- A **choice** picks one option from a list. Each option can carry a description of when it applies.
- A **yes/no** question (System One calls it `noul`) returns the probability of yes.
- A **score** places the state on an ordered rubric and returns the expected level, which can fall between two levels.

The reply has one answer per question name. A choice comes back with the winning option and a probability for every option; a yes/no comes back as a single number between 0 and 1; a score comes back as an expected level plus the distribution over the levels. [Chapter 2](02-decisions.md) goes through every field.

Because the answer set is closed, the output is valid by construction. A model that generates JSON can forget a brace, invent a field, or answer "probably billing" when the schema wanted `billing`. A model that only assigns probabilities to `billing`, `shipping` and `other` cannot. None of the readouts in this book lets the model write its answer: each reads probabilities at one position. (slot asks llama-server for a single token only to see the log-probabilities of the candidates.)

## Where decisions fit

Decisions are small, frequent and cheap to check. That makes them useful wherever software has to branch on the meaning of text:

- **Routing.** Send a request to the right handler, team, model or prompt.
- **Triage.** Flag a ticket as urgent, a transfer as suspicious, a message as spam.
- **Tagging.** Attach a language, a topic, a product area, a sentiment.
- **Gating an agent.** Before a large model runs a tool, ask a small one whether the tool call is safe, whether the user asked for it, or whether a human should look first.

In each case the question is fixed at development time and only the state changes at run time. That lets you test the question like code: collect labelled examples, measure how often the answer is right, and move the threshold on the probability until the mistakes you care about are rare enough.

If the decision needs free-form output, such as a summary, a translation or code, a decision engine is the wrong tool. It can still sit in front of the generator and decide whether to call it.

## The running example: the FontLab assistant router

Every benchmark in this book asks the same question. FontLab, the font editor, has a built-in assistant. A message typed into it must go to one of five handlers, and the router has to pick the right one before anything else happens. The five tasks, as our benchmark harness defines them:

- **docs**: answer a question from the FontLab documentation. The user wants to know how a feature, tool, panel, dialog, setting or workflow works, what something means, where to find something, or why FontLab behaves a certain way. They want an explanation, not code.
- **python**: write, fix or explain a Python script that automates FontLab, through the FontLab Python API or FontTools and DrawBot style scripting: batch operations, renaming glyphs, generating files, processing fonts programmatically.
- **fea**: write or fix OpenType feature code in the Adobe FDK (`.fea`) syntax: feature blocks such as `liga`, `kern`, `calt`, `smcp` or `ss01`, lookups, substitutions, positioning, classes and `languagesystem` statements.
- **vfj**: write a glyph definition in VFJ, FontLab's JSON glyph format: one JSON object with the glyph's name, Unicode value, advance width, contours, nodes, components, anchors and guides.
- **sample**: write a sample text (a pangram, a test string, a word list, a paragraph or a set of glyph sequences) to show in the FontLab Glyph window so the user can examine the font with it.

The categories overlap on purpose. "How do I write a liga feature?" is a documentation question about feature code. "Show me how a glyph is stored in a VFJ file" asks for an explanation, not a glyph. The router set has 67 queries in 30 languages, and ten of them were written to sit on these boundaries. [Chapter 5](05-method.md) describes the set and how it was scored.

A router is a good test because it is a real decision with a known right answer, it runs on every message, and a wrong answer is expensive: the user gets a script when they asked how a menu works.

## jev, the hosted reference

TypeSafe's **jev** is a hosted System One model. You send a state and questions to an API and get calibrated probabilities back; our benchmark harness reaches it through OpenRouter's System One API as `jev-latest`. It is the reference point in this book because it is the model the local engines have to match. On the router set jev scores 65 of 67, both on translated queries and on the original text.

jev also defined the vocabulary. The request and answer shapes shown above are its API, and pydantic-ai's `TypeSafeModel` speaks it. dohnuts, one of the two local engines, answers the same requests at the same `/v1/systemone` path, which is why an agent written for jev can run locally with a changed base URL ([chapter 11](11-typed.md)).

## Why run decisions locally

jev answers the router question in 466 ms on average, measured from our client, network included. The local methods that come within three answers of it take 52 to 95 ms on the same machine ([chapter 6](06-results.md)).

Latency is the first reason to run locally. A router that sits in front of every message adds its delay to every message, and a gate in front of every tool call adds it to every step of an agent. At 50 ms the decision disappears into the time the interface needs to redraw; at 500 ms the user waits for it.

Cost per call is the second reason. A decision is small, but a router or a gate runs on every request, so the number of calls grows with the product rather than with the difficulty of the question. A local model costs the same whether you ask once or a million times.

Privacy is the third. The state is often exactly the data you would rather not send anywhere: a customer's message, the contents of a document, the file a user has open. A local engine reads it on the machine where it already is.

The fourth is that a local engine keeps working offline and does not change under you. A hosted alias such as `jev-latest` moves when a new release ships, and a threshold tuned against one release may not hold for the next. A GGUF file on disk answers the same way until you replace it.

The price is accuracy on the hardest queries and the work of choosing, downloading and running a model. This book is about paying that price well.

## How this book is organised

The **concepts** part (chapters 1 to 4) defines a decision, explains how each engine reads one out of a model, and sorts the models into dedicated, fine-tuned and vanilla families.

The **benchmarks** part (chapters 5 to 9) describes how the router set was measured and reports accuracy, quantization, speed, caching and confidence for every model and engine we ran.

The **package** part (chapters 10 to 12) documents `ornotto`, shows how to use it from plain Python and from pydantic-ai, and ends with a guide to choosing an engine and model, and to building and contributing.
