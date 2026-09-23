---
this_file: src_docs/md/09-confidence.md
---

# 9. Confidence and fallback

Every engine in this book returns a probability for each option, not just a winner. If those probabilities mean what they say, you can act on the confident answers and send the doubtful ones somewhere slower and better. This chapter measures whether they do, on the router benchmark, and what a fallback buys.

## What calibration means

A model is calibrated when its stated probability matches its hit rate: of all the answers it gives with a top probability near 0.8, about 80 percent are right. Calibration is a property of the probabilities, separate from accuracy. A model can be accurate and badly calibrated (always 0.99, sometimes wrong), or calibrated and mediocre.

The dedicated models get calibrated during training. decider divides the letter logits by a fitted temperature before the softmax (T 1.03 for decider-0.8b, 1.3 for DreamBlooms' decider-2b), and laya picks a temperature per bucket of option count and question type. pcdServer applies no temperature: its probabilities are the model's raw softmax over the first tokens of the allowed values, which says how strongly the model prefers one value, not how often it is right. The `ornotto` package marks the difference on every answer with `Answer.calibrated`, `True` on dohnuts and `False` on pcdServer, so that you do not compare the two as if they were one scale.

To check calibration you need labelled examples: group the answers by their top probability, and count how many in each group were right.

## decider-0.8b on the router set

These are the 67 router queries answered by decider-0.8b on dohnuts (Metal), grouped by top probability. The file is DreamBlooms' `Q8_0` conversion, the one `ornotto` registers. First with translation:

--8<-- "tables/calibration-translated.html"

And on the original text:

--8<-- "tables/calibration-direct.html"

Pooled over both runs, answers at 0.95 and above were right 97 percent of the time (61 of 63), answers from 0.8 to 0.95 were right 85 percent of the time (28 of 33), answers from 0.6 to 0.8 were right 95 percent of the time (19 of 20), and answers below 0.6 were right 83 percent of the time (15 of 18). The top band keeps its promise, but the order below it is loose: the 0.6 to 0.8 band is more reliable than its probability says, and more reliable than the band above it. With 67 queries per run the bands hold 8 to 32 answers each, so one answer moves a band by several percentage points. The signal separates the very confident answers from the rest, and says little about which of the others are wrong.

The bands use the top probability, which dohnuts reports as `native.confidence`; its plain `confidence` field is an entropy measure ([chapter 2](02-decisions.md#the-confidence-trap)).

## A fallback gate

The fastest accurate local model and the most accurate local model are different models:

- decider-0.8b (DreamBlooms `Q8_0`, the file `ornotto` registers) on dohnuts (Metal): 62 of 67 translated at 52.2 ms per query, 61 of 67 direct at 52.4 ms.
- Qwen3.5-4B-Hmm (`Q8_0`, 4.48 GB) on pcdServer: 64 of 67 translated at 87.6 ms, 65 of 67 direct at 88.0 ms. The `Q4_K_M` file that `ornotto` registers scores the same at 93 ms from 2.7 GB ([chapter 6](06-results.md)).

A gate asks the fast model first and sends the query to the slow one only when the fast model's top probability is below a threshold. The tables replay the benchmark's cached answers through such a gate at several thresholds. "Mean ms" is the cost per query averaged over all 67, where a query that falls back pays for both calls.

With translation:

--8<-- "tables/cascade-translated.html"

On the original text:

--8<-- "tables/cascade-direct.html"

The two runs lead to different decisions.

**With translation, the gate does not pay.** Thresholds from 0.5 to 0.85 score 62 of 67, the same as decider alone: at 0.5 the gate fixes one error (the sidebearings script, top probability 0.49) and makes one ("Which words should I look at to judge the spacing of round letters?", 0.49, where Qwen3.5-4B-Hmm says docs). The gate first gains an answer at 0.9, when the Urdu request for a Python script (0.86) falls back, and then scores 63 at 89.2 ms with 29 fallbacks. Qwen3.5-4B-Hmm alone scores 64 at 87.6 ms.

**Without translation, the gate helps.** Below 0.7, it scores 63 of 67 at 71.5 ms with 15 fallbacks: two answers better than decider alone and 16 ms faster than Qwen3.5-4B-Hmm alone. It catches decider's errors on the Persian, German and sidebearings queries, which had top probabilities from 0.37 to 0.68, and loses the round-letters query. Below 0.95 it reaches 64 of 67 at 97.2 ms with 35 fallbacks, which is slower than Qwen3.5-4B-Hmm alone, and Qwen3.5-4B-Hmm alone still scores higher, 65 of 67.

Some of decider's errors sit where a useful threshold cannot reach them, because decider is sure of them. "Show me how a glyph is stored in a VFJ file" (a docs question) got vfj at 0.99, above every threshold in the tables. "Can FontLab batch rename glyphs?" (also docs) got python at 0.94, and falls back only below 0.95, where the gate is already slower than Qwen3.5-4B-Hmm alone. Both are questions about FontLab, worded with the vocabulary of the task they are not, and Qwen3.5-4B-Hmm answers both correctly. "How do I write a liga feature?" (docs) got fea at 0.86, and falling back does not help: Qwen3.5-4B-Hmm answers fea too.

!!! warning "Read these gains with care"
    The thresholds were chosen on the same 67 queries they are scored on, and the direct run uses the same queries as the translated run, so neither is a held-out test. A gate also needs both models loaded at once (about 0.8 GB plus 4.5 GB here), and no benchmark run has measured the two servers running side by side.

## A gate in ornotto

The `ornotto` repository ships the gate as `examples/fallback.py`:

```python
import ornotto

THRESHOLD = 0.7
TASKS = ["docs", "python", "fea", "vfj", "sample"]
QUESTION = "Which kind of help does this FontLab user want?"

fast = ornotto.Decider("decider-0.8b")
careful = ornotto.Decider("qwen3.5-4b-hmm", engine="pcd")

for text in ("Build a kern feature for A V", "Jak zmienić kąt pochylenia kursywy w FontLab?",
             "Show me how a glyph is stored in a VFJ file"):
    answer = fast.choose(text, TASKS, QUESTION)
    source = "decider"
    if answer.confidence < THRESHOLD:
        answer, source = careful.choose(text, TASKS, QUESTION), "qwen3.5-4b-hmm"
    print(f"{answer.value:7} {answer.confidence:.2f} {source:15} {text}")
```

The script sends a shorter question than the benchmark's router prompt, so its confidences differ from the tables above even though the model file is the same. In our test run of this script the kern request stayed on decider (fea, 0.79), the Polish question stayed on decider (docs, 0.99), and the VFJ question fell below 0.7 and went to Qwen3.5-4B-Hmm, which answered vfj. The thresholds you pick belong to your own prompts and your own labelled examples, not to this benchmark.

If you run the two models as a pydantic-ai chain instead, [chapter 11](11-typed.md) shows the same pattern with an `Agent`.

## The hardest queries

Some queries defeat most of the 208 classifiers, and they are worth reading because they show where the task definition, not the model, is weak. The table lists every query with the share of classifiers that got it right, translated and direct, and jev's answer on the translated text. It opens with the hardest.

--8<-- "tables/queries.html"

The three hardest:

- **"How do I write a liga feature?"** is labelled docs: the user asks how, not for code. 9 percent of the classifiers agree, and jev answers fea. The words "write" and "feature" pull every model towards the feature-code task. Whether the label or the models are right is a question about what the assistant should do, which a router cannot settle.
- **"Which words should I look at to judge the spacing of round letters?"** is labelled sample: the user wants test text. 22 percent get it right, jev among them. The question is about spacing, and the request for text to look at is implied rather than stated.
- **"Show me how a glyph is stored in a VFJ file"** is labelled docs, and 26 percent agree. It is the same trap as the liga query: the format's name pulls the answer to vfj, the task of writing VFJ, and jev answers vfj too.

One query shows what translation costs. The Korean request for a VFJ glyph named hyphen with a width of 300 is right for 90 percent of the classifiers on the original text and for 32 percent after translation, because the translator turned it into "The FontLab file has a hyphen name and a glyph definition with a width of 300." Most classifiers read the Korean better than the English they were given.

## The abstain signal nobody used

laya returns one more number that the other engines do not: `action.act_probability`, the output of a separate act head that estimates whether the model should answer directly or escalate. It is the only built-in abstain signal among the engines benchmarked here. Our benchmark harness never read it; it compared only the probability maps. A gate on `act_probability` instead of on top probability is the obvious next experiment for laya, whose 4 to 7 ms answers ([chapter 8](08-speed.md#load-time-and-the-latency-floor)) would make a cheap first stage if it knew when to step aside.
