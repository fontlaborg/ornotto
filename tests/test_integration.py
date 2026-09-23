# this_file: tests/test_integration.py
"""Real engines on decider-0.8b. Run with `pytest -m engine`; downloads ~0.8 GB on first use.

Each engine runs alone: the fixture starts it for its tests and stops it after, and the test checks that
nothing is left running.
"""

from typing import Literal

import pytest
from pydantic import BaseModel, Field

import ornotto
from ornotto._engines import Server

pytestmark = pytest.mark.engine

TASKS = {
    "docs": "a question about how FontLab works",
    "python": "a Python script for FontLab",
    "fea": "OpenType feature code",
}


@pytest.fixture(scope="module", params=["dohnuts", "pcd"])
def decider(request):
    d = ornotto.Decider("decider-0.8b", engine=request.param)
    yield d
    ornotto.shutdown()
    assert not Server._running, "every engine is stopped after its tests"


def test_choose_when_router_question_then_expected_task(decider):
    answer = decider.choose("Build a kern feature for A V W T", TASKS, "What does the user want?")
    assert answer.value == "fea", answer.probabilities
    assert answer.calibrated == (decider.engine == "dohnuts")
    assert sum(answer.probabilities.values()) == pytest.approx(1.0, abs=1e-3)


def test_decide_when_three_kinds_then_all_answered(decider):
    d = decider.decide(
        "Write a Python script that renames every .sc glyph, I need it today",
        {
            "task": ornotto.choice("What does the user want?", TASKS),
            "code": ornotto.yes_no("Does the user want code they can run?"),
            "urgency": ornotto.score("How urgent is it?", ["can wait", "this week", "today"]),
        },
    )
    assert d.task.value == "python" and d.code.value is True
    assert 0 <= d.urgency.value <= 2 and d.urgency.level in (0, 1, 2)
    assert d.engine == decider.engine and d.ms > 0


def test_decide_when_json_state_then_answered(decider):
    state = {"message": "Why does this pair look too tight?", "selection": ["A", "V"]}
    answer = decider.choose(state, ["kerning", "drawing"], "Which area is this about?")
    assert answer.value == "kerning"


async def test_adecide_when_async_then_same_answer(decider):
    d = await decider.adecide(
        "Build a kern feature for A V", {"t": ornotto.choice("What does the user want?", TASKS)}
    )
    assert d.t.value == "fea"


class Triage(BaseModel):
    """A FontLab user's request."""

    task: Literal["docs", "python", "fea"] = Field(description="What does the user want?")
    wants_code: bool = Field(description="Does the user want code they can run?")


def test_extract_when_model_then_typed(decider):
    t = ornotto.extract(Triage, "Write a Python script that renames glyphs", decider=decider)
    assert t.task == "python" and isinstance(t.wants_code, bool)


def test_pydantic_ai_agent_when_output_type_then_filled(decider):
    from pydantic_ai import Agent

    from ornotto.pydantic_ai import model

    agent = Agent(model(decider), output_type=Triage, instructions="Classify a FontLab user's request.")
    result = agent.run_sync("Write a Python script that renames every .sc glyph to .smcp")
    assert isinstance(result.output, Triage)
    if decider.engine == "dohnuts":  # decider's own readout; on pcdServer the same weights are less accurate
        assert result.output.task == "python"
