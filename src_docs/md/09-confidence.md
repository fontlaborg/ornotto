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

These are the 67 router queries answered by decider-0.8b (mradermacher `q5`) on dohnuts (Metal), grouped by top probability. First with translation:

--8<-- "tables/calibration-translated.html"

And on the original text:

--8<-- "tables/calibration-direct.html"

Pooled over both runs, answers with a top probability from 0.6 to 0.8 were right 96 percent of the time (26 answers), answers at 0.95 and above were right 94 percent of the time (69 answers), and answers below 0.6 were right 75 percent of the time (16 answers). The ordering is loose: the middle band is more reliable than its probability says, and the most confident band is less reliable than its 0.95 promises. With 67 queries per run the bands hold 8 to 36 answers each, so one answer moves a band by several percentage points. The signal is usable for separating very unsure answers from the rest, and weak above that.

The bands use the top probability, which dohnuts reports as `native.confidence`; its plain `confidence` field is an entropy measure ([chapter 2](02-decisions.md#the-confidence-trap)).

## A fallback gate

The fastest accurate local model and the most accurate local model are different models:

- decider-0.8b (mradermacher `q5`) on dohnuts (Metal): 62 of 67 translated, 60 of 67 direct, 55 ms per query.
- Qwen3.5-4B-Hmm (`q8`, 4.48 GB) on pcdServer: 64 of 67 translated, 65 of 67 direct, 88 ms per query. The `q4` file that `ornotto` registers scores the same at 93 ms from 2.7 GB.

A gate asks the fast model first and sends the query to the slow one only when the fast model's top probability is below a threshold. The tables replay the benchmark's cached answers through such a gate at several thresholds. "Mean ms" is the cost per query averaged over all 67, where a query that falls back pays for both calls.

With translation:

--8<-- "tables/cascade-translated.html"

On the original text:

--8<-- "tables/cascade-direct.html"

The two runs lead to different decisions.

**With translation, the gate does not pay.** The best gate, below 0.85, scores 63 of 67 at 85.8 ms with 24 fallbacks. Qwen3.5-4B-Hmm alone scores 64 at 87.6 ms. The one answer the gate gains over decider alone comes from a single query, the Urdu request for a Python script, where decider's top probability was 0.84. Thresholds of 0.5 to 0.8 score 62, the same as decider alone.

**Without translation, the gate helps.** Below 0.7, it scores 63 of 67 at 73.2 ms with 14 fallbacks, three answers better than decider alone and 15 ms faster than Qwen3.5-4B-Hmm alone. It catches decider's errors on the Persian, Czech and German queries, which had top probabilities from 0.38 to 0.63. Qwen3.5-4B-Hmm alone still scores higher, 65 of 67, at 88 ms.

Some of decider's errors no threshold catches, because decider is sure of them. "Can FontLab batch rename glyphs?" (a docs question) got python at 0.97, and "Show me how a glyph is stored in a VFJ file" (also docs) got vfj at 0.99. Both are questions about FontLab, worded with the vocabulary of the task they are not. Qwen3.5-4B-Hmm answers both correctly.

!!! warning "Read these gains with care"
    The gate and the calibration bands were replayed with decider-0.8b's `q5` file. The `ornotto` package registers the DreamBlooms `q8` file, which scores the same 62/67 translated but was not replayed through the gate, so its thresholds may sit elsewhere.

    The thresholds were chosen on the same 67 queries they are scored on, and the direct run uses the same queries as the translated run, so neither is a held-out test. A gate also needs both models loaded at once (about 0.6 GB plus 4.5 GB here), and no benchmark run has measured the two servers running side by side.

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

`ornotto` registers the `q8` file of decider-0.8b, not the `q5` file of the benchmark, and it sends a shorter question than the benchmark's router prompt, so the confidences differ from the tables above. In our test run of this script the kern request stayed on decider (fea, 0.79), the Polish question stayed on decider (docs, 0.99), and the VFJ question fell below 0.7 and went to Qwen3.5-4B-Hmm, which answered vfj. The thresholds you pick belong to your own prompts and your own labelled examples, not to this benchmark.

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
