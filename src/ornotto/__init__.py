# this_file: src/ornotto/__init__.py
"""ornotto: typed decisions on local models, over the dohnuts and pcdServer engines.

    import ornotto

    ornotto.choose("Build a kern feature for A V", ["docs", "python", "fea"]).value   # 'fea'
    ornotto.check("Write me a script that renames glyphs", "Does the user want code?").probability

Every call answers System One questions (choice, yes/no, score) about a state. `Decider` picks the model
and engine; the module-level functions use a shared default (`ornotto.use(...)` changes it).
"""

from __future__ import annotations

from typing import Any

from ._decider import Decider, DecisionError
from ._engines import EngineNotFound, Server
from ._models import DEFAULT_MODEL, MODELS, ModelSpec
from ._protocol import Answer, Decision, Question, choice, score, yes_no
from ._typed import aextract, classify, decision, default, extract, questions_for, use

try:
    from ._version import __version__
except ImportError:  # running from a source tree without a build
    __version__ = "0.0.0"

__all__ = [
    "DEFAULT_MODEL",
    "MODELS",
    "Answer",
    "Decider",
    "Decision",
    "DecisionError",
    "EngineNotFound",
    "ModelSpec",
    "Question",
    "aextract",
    "check",
    "choice",
    "choose",
    "classify",
    "decide",
    "decision",
    "extract",
    "questions_for",
    "rate",
    "score",
    "shutdown",
    "use",
    "yes_no",
]


def decide(state: Any, questions: Any) -> Decision:
    """Answer named questions about `state` with the default Decider."""
    return default().decide(state, questions)


def choose(state: Any, options: Any, question: str | None = None) -> Answer:
    """Pick one of `options` with the default Decider."""
    return default().choose(state, options, question)


def check(state: Any, question: str, *, yes: str | None = None, no: str | None = None) -> Answer:
    """Answer a yes/no question with the default Decider."""
    return default().check(state, question, yes=yes, no=no)


def rate(state: Any, question: str | None, levels: Any) -> Answer:
    """Score `state` on a rubric with the default Decider."""
    return default().rate(state, question, levels)


def shutdown() -> None:
    """Stop every engine this process started (also done automatically at exit)."""
    Server.stop_all()
