# this_file: tests/test_typed.py
import enum
from typing import Literal

import pytest
from pydantic import BaseModel, Field

import ornotto
from ornotto._protocol import Decision, parse_answer
from ornotto._typed import questions_for


class Tone(enum.Enum):
    CALM = "calm"
    ANGRY = "angry"


class Ticket(BaseModel):
    """A support ticket."""

    team: Literal["billing", "shipping"] = Field(description="Which team handles it?")
    refund: bool = Field(description="Does it need a refund?")
    tone: Tone
    spam: float = Field(ge=0, le=1, description="Is it spam?")


class FakeDecider(ornotto.Decider):
    """A real Decider whose `decide` answers with fixed probabilities and records what it was asked."""

    def __init__(self):
        self.calls = []

    def decide(self, state, questions):
        self.calls.append((state, dict(questions)))
        answers = {}
        for name, q in questions.items():
            if q.kind == "noul":
                answers[name] = parse_answer({"type": "noul", "noul": 0.8}, True)
            else:
                first = next(iter(q.options))
                probs = {k: (0.9 if k == first else 0.1 / (len(q.options) - 1)) for k in q.options}
                answers[name] = parse_answer(
                    {"type": "choice", "choice": first, "confidence": 0.5, "probabilities": probs}, True
                )
        return Decision(answers, "fake", "dohnuts")


def test_questions_for_when_supported_fields_then_one_question_each():
    qs = questions_for(Ticket)
    assert {n: q.kind for n, q in qs.items()} == {
        "team": "choice",
        "refund": "noul",
        "tone": "choice",
        "spam": "noul",
    }
    assert qs["team"].instructions == "Which team handles it?"
    assert qs["tone"].instructions == "Tone?", "without a description the field name is the question"


def test_questions_for_when_unsupported_field_then_type_error():
    class Bad(BaseModel):
        count: int

    with pytest.raises(TypeError, match="count"):
        questions_for(Bad)


def test_extract_when_answers_then_typed_instance():
    t = ornotto.extract(Ticket, "I was charged twice", decider=FakeDecider())
    assert t == Ticket(team="billing", refund=True, tone=Tone.CALM, spam=0.8)


def test_classify_when_enum_then_member():
    assert ornotto.classify("hello", Tone, decider=FakeDecider()) is Tone.CALM


def test_decision_decorator_when_two_args_then_json_state_and_docstring_question():
    fake = FakeDecider()

    @ornotto.decision(decider=fake)
    def route(request: str, app: str) -> Literal["docs", "python"]:
        """Which kind of help is wanted?"""

    assert route("rename glyphs", app="FontLab") == "docs"
    state, questions = fake.calls[-1]
    assert state == {"request": "rename glyphs", "app": "FontLab"}
    assert questions["answer"].instructions == "Which kind of help is wanted?"


def test_decision_decorator_when_float_then_probability():
    @ornotto.decision(decider=FakeDecider())
    def is_spam(text: str) -> float:
        """Is this spam?"""

    assert is_spam("buy now") == 0.8
