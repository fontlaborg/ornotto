# this_file: src/ornotto/_remote.py
"""OpenRouter decision model IDs and native response checks; no SDK dependency."""

from __future__ import annotations

import math
from collections.abc import Mapping

from ._protocol import JSON, Question, parse_answer

OPENROUTER_URL = "https://openrouter.ai/api"
OPENROUTER_MODELS = (
    "liquid/d1",
    "togethercomputer/tev1-4b-experimental",
    "inception/mercury-decide:free",
    "upstage/solar-decide",
    "respan/span-01",
    "respan/span-01-lite",
    "respan/span-01-lite:free",
    "jaredpalmer/kev-4b",
    "typesafe/jev-1.13",
)
OPENROUTER_KINDS = {
    model: ("noul",) if model.startswith("respan/") else ("choice", "noul", "score")
    for model in OPENROUTER_MODELS
}


def check_questions(model: str, questions: Mapping[str, Question]) -> None:
    """Enforce observed provider capabilities before a billable request."""
    allowed = OPENROUTER_KINDS.get(model, ("choice", "noul", "score"))
    for question in questions.values():
        if question.kind not in allowed:
            raise ValueError(f"{model} supports only {', '.join(allowed)} questions; use check()/yes_no()")


def validate_response(body: dict[str, JSON], questions: Mapping[str, Question]) -> dict[str, JSON]:
    """Reject incomplete or nonfinite provider results instead of treating them as decisions."""
    if not isinstance(body, dict) or not isinstance(body.get("model"), str):
        raise ValueError("missing response model")
    if not isinstance(body.get("usage"), dict) or set(body.get("answers", {})) != set(questions):
        raise ValueError("missing usage or answers")
    for name, question in questions.items():
        raw = body["answers"][name]
        if raw["type"] != question.kind:
            raise ValueError(f"wrong answer type for {name}")
        answer = parse_answer(raw, False)
        probs = answer.probabilities
        if not all(math.isfinite(p) and 0 <= p <= 1 for p in probs.values()):
            raise ValueError(f"invalid probabilities for {name}")
        if question.kind != "noul" and set(probs) != set(question.options):
            raise ValueError(f"missing alternatives for {name}")
        if not math.isclose(sum(probs.values()), 1, abs_tol=0.01):
            raise ValueError(f"unnormalized probabilities for {name}")
        if question.kind == "choice" and answer.value not in question.options:
            raise ValueError(f"unknown choice for {name}")
        if question.kind == "score" and not 0 <= answer.value <= len(question.options) - 1:
            raise ValueError(f"invalid score for {name}")
    for value in body["usage"].values():
        if isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
            raise ValueError("invalid usage")
    return body
