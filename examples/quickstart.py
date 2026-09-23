# this_file: examples/quickstart.py
"""Three kinds of question, one model: route a FontLab request, check it, and rate it."""

import ornotto

TASKS = {
    "docs": "a question about how FontLab works, answered from the documentation",
    "python": "a Python script that automates FontLab",
    "fea": "OpenType feature code (kern, liga, ss01, …)",
}

request = "Rename every selected glyph that ends in .sc to .smcp, in all open fonts"

decision = ornotto.decide(
    request,
    {
        "task": ornotto.choice("What does the user want?", TASKS),
        "wants_code": ornotto.yes_no("Does the user want code they can run?"),
        "scope": ornotto.choice(
            "Which glyphs should the action touch?",
            {
                "selection": "the selected glyphs",
                "font": "every glyph in the current font",
                "all_fonts": "every open font",
            },
        ),
        "risk": ornotto.score(
            "How much existing data could this change?", ["none", "some glyphs", "whole fonts"]
        ),
    },
)

for name, answer in decision.items():
    print(f"{name:10} {answer.value!s:10} p={answer.probability:.2f}")
print(f"{decision.model} on {decision.engine}: {decision.ms:.0f} ms")
