# this_file: examples/fallback.py
"""Answer with a fast dedicated model; ask a larger chat model only when the first is unsure.

decider-0.8b on dohnuts reports temperature-scaled probabilities, so its top probability is a usable
gate. Below the threshold the question goes to Qwen3.5-4B-Hmm on pcdServer (a 2.7 GB download).
"""

import ornotto

THRESHOLD = 0.7
TASKS = ["docs", "python", "fea", "vfj", "sample"]
QUESTION = "Which kind of help does this FontLab user want?"

fast = ornotto.Decider("decider-0.8b")
careful = ornotto.Decider("qwen3.5-4b-hmm", engine="pcd")

for text in (
    "Build a kern feature for A V",
    "Jak zmienić kąt pochylenia kursywy w FontLab?",
    "Show me how a glyph is stored in a VFJ file",
):
    answer = fast.choose(text, TASKS, QUESTION)
    source = "decider"
    if answer.confidence < THRESHOLD:
        answer, source = careful.choose(text, TASKS, QUESTION), "qwen3.5-4b-hmm"
    print(f"{answer.value:7} {answer.confidence:.2f} {source:15} {text}")
