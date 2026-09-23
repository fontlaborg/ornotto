# this_file: src/ornotto/_protocol.py
"""Questions, answers, and the translation between System One and pcdServer.

ornotto speaks the System One vocabulary everywhere: a `state` (text or JSON) and named questions of three
kinds, `choice` (pick one option), `noul` (yes or no) and `score` (place on an ordered rubric). dohnuts
answers System One requests natively. pcdServer answers bounded JSON fields, so `to_pcd` and `from_pcd`
translate: options become enum choices, a yes/no becomes `[false, true]`, and rubric levels become the
choices "0", "1", … whose expected value is the score.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

Kind = Literal["choice", "noul", "score"]
JSON = Any

# pcdServer request limits (include/pcd/types.hpp); checked here so errors name the question.
PCD_MAX_FIELDS = 63
PCD_MAX_DESCRIPTION_BYTES = 1024
PCD_MAX_CONTEXT_BYTES = 64 * 1024


@dataclass(frozen=True)
class Question:
    """One question about a state. Build it with `choice`, `yes_no` or `score`."""

    kind: Kind
    instructions: str | None = None
    options: dict[str, str | None] = field(default_factory=dict)
    """choice: option name -> description (or None); score: level text per level, keyed "0", "1", …;
    noul: optional "true"/"false" descriptions."""

    def to_system_one(self) -> dict[str, JSON]:
        body: dict[str, JSON] = {"type": self.kind}
        if self.instructions:
            body["instructions"] = self.instructions
        if self.kind == "score":
            body["criteria"] = [self.options[str(i)] for i in range(len(self.options))]
        elif self.options:
            body["criteria"] = dict(self.options)
        return body


def choice(instructions: str | None, options: Sequence[str] | Mapping[str, str | None]) -> Question:
    """Pick one of `options`: a list of names, or a mapping of name -> description."""
    opts = dict(options) if isinstance(options, Mapping) else dict.fromkeys(options)
    if len(opts) < 2:
        raise ValueError("a choice needs at least two options")
    return Question("choice", instructions, opts)


def yes_no(instructions: str, *, yes: str | None = None, no: str | None = None) -> Question:
    """A yes/no question. `yes` and `no` optionally say what counts as each answer."""
    opts: dict[str, str | None] = {k: v for k, v in (("false", no), ("true", yes)) if v}
    return Question("noul", instructions, opts)


def score(instructions: str | None, levels: Sequence[str]) -> Question:
    """Place the state on an ordered rubric; `levels[i]` describes level i."""
    if len(levels) < 2:
        raise ValueError("a score needs at least two levels")
    return Question("score", instructions, {str(i): text for i, text in enumerate(levels)})


def as_question(value: Question | Mapping[str, JSON]) -> Question:
    """Accept a `Question` or a System One question dict.

    `question` and `options` are accepted as aliases of `instructions` and `criteria`, `bool` of `noul`.
    """
    if isinstance(value, Question):
        return value
    kind = value.get("type", "choice")
    asked = value.get("instructions", value.get("question"))
    instructions = None if asked is None else _text(asked)  # System One allows JSON instructions
    criteria = value.get("criteria", value.get("options"))
    if kind in ("noul", "bool"):
        c = criteria or {}
        return yes_no(instructions or "", yes=c.get("true"), no=c.get("false"))
    if kind == "score":
        levels = (
            [criteria[k] for k in sorted(criteria, key=float)] if isinstance(criteria, Mapping) else criteria
        )
        return score(instructions, [_text(level) for level in levels])
    if kind == "choice":
        if isinstance(criteria, Mapping):
            return choice(instructions, {k: None if v is None else _text(v) for k, v in criteria.items()})
        return choice(instructions, [_text(c) for c in criteria or []])
    raise ValueError(f"unknown question type {kind!r}")


def _text(value: JSON) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


@dataclass(frozen=True)
class Answer:
    """One answer. `value` is the option name (choice), True/False (noul) or the expected level (score)."""

    kind: Kind
    value: str | bool | float
    probabilities: dict[str, float]
    """choice: per option; score: per level ("0", "1", …); noul: {"false": p, "true": p}."""
    calibrated: bool
    """True when probabilities are temperature-scaled by the model's recipe (decider, kev, Dohnuts);
    False for pcdServer's raw softmax over the allowed tokens. Compare confidences only within one kind."""
    raw: dict[str, JSON] = field(default_factory=dict, repr=False)

    @property
    def probability(self) -> float:
        """choice and score: probability of the most likely option or level; noul: probability of yes."""
        if self.kind == "noul":
            return self.probabilities["true"]
        return max(self.probabilities.values())

    @property
    def confidence(self) -> float:
        """Probability of the answer given: the top option, the top level, or max(p(yes), p(no))."""
        return max(self.probabilities.values())

    @property
    def level(self) -> int:
        """score: the most likely level."""
        if self.kind != "score":
            raise AttributeError("level is only defined for score answers")
        return int(max(self.probabilities, key=self.probabilities.__getitem__))

    def __bool__(self) -> bool:
        return bool(self.value)


@dataclass(frozen=True)
class Decision(Mapping[str, Answer]):
    """All answers to one request, by question name. `decision.task` works as well as `decision["task"]`."""

    answers: dict[str, Answer]
    model: str
    engine: str
    usage: dict[str, JSON] = field(default_factory=dict)
    ms: float = 0.0

    def __getitem__(self, key: str) -> Answer:
        return self.answers[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.answers)

    def __len__(self) -> int:
        return len(self.answers)

    def __getattr__(self, name: str) -> Answer:
        try:
            return self.__dict__["answers"][name]
        except KeyError:
            raise AttributeError(name) from None

    def to_dict(self) -> dict[str, str | bool | float]:
        """Just the values, by question name."""
        return {name: answer.value for name, answer in self.answers.items()}


def parse_answer(raw: Mapping[str, JSON], calibrated: bool) -> Answer:
    """A System One answer dict -> `Answer`."""
    kind = raw["type"]
    if kind == "noul":
        p = float(raw["noul"])
        return Answer("noul", p >= 0.5, {"false": 1.0 - p, "true": p}, calibrated, dict(raw))
    probs = {str(k): float(v) for k, v in raw["probabilities"].items()}
    value = raw["choice"] if kind == "choice" else float(raw["score"])
    return Answer(kind, value, probs, calibrated, dict(raw))


def entropy_confidence(p: Sequence[float]) -> float:
    """1 - H/ln K, the System One `confidence` of a distribution (0 = uniform, 1 = certain)."""
    if len(p) <= 1:
        return 1.0
    h = -sum(x * math.log(max(x, 1e-12)) for x in p)
    return max(0.0, min(1.0, 1.0 - h / math.log(len(p))))


def _clip_bytes(text: str, limit: int) -> str:
    data = text.encode()
    return text if len(data) <= limit else data[: limit - 3].decode(errors="ignore") + "..."


def to_pcd(state: JSON, questions: Mapping[str, Question]) -> dict[str, JSON]:
    """A System One request -> a pcdServer `/v1/pcd/decode` body."""
    if len(questions) > PCD_MAX_FIELDS:
        raise ValueError(f"pcdServer takes at most {PCD_MAX_FIELDS} questions per request")
    context = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    if len(context.encode()) > PCD_MAX_CONTEXT_BYTES:
        raise ValueError("pcdServer takes at most 64 KiB of state")
    fields = []
    for name, q in questions.items():
        lines = [q.instructions or ""]
        if q.kind == "noul":
            choices: list[JSON] = [False, True]
            lines += [f"{k}: {v}" for k, v in q.options.items() if v]
        elif q.kind == "score":
            choices = list(q.options)
            lines += [f"{k}: {v}" for k, v in q.options.items()]
        else:
            choices = list(q.options)
            lines += [f"{k}: {v}" for k, v in q.options.items() if v]
        description = _clip_bytes("\n".join(line for line in lines if line), PCD_MAX_DESCRIPTION_BYTES)
        fields.append({"name": name, "description": description, "choices": choices})
    return {"context": context, "fields": fields}


def from_pcd(body: Mapping[str, JSON], questions: Mapping[str, Question]) -> dict[str, JSON]:
    """A pcdServer decode response -> a System One response (`model`, `answers`, `usage`)."""
    answers: dict[str, JSON] = {}
    for item in body["fields"]:
        q = questions[item["name"]]
        probs = {str(k): float(v) for k, v in item["probabilities"].items()}
        if q.kind == "noul":
            answers[item["name"]] = {"type": "noul", "noul": probs.get("true", 0.0)}
            continue
        ordered = [probs.get(k, 0.0) for k in q.options]
        answer = {"type": q.kind, "confidence": entropy_confidence(ordered), "probabilities": probs}
        if q.kind == "choice":
            answer["choice"] = str(item["value"])
        else:
            answer["score"] = sum(i * p for i, p in enumerate(ordered))
            answer["legend"] = dict(q.options)
        answers[item["name"]] = answer
    metrics = body.get("metrics", {})
    return {
        "model": body.get("model", ""),
        "answers": answers,
        "usage": {"input_tokens": 0, "output_tokens": 0, "elapsed_ms": metrics.get("elapsedMs")},
    }
