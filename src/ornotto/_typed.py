# this_file: src/ornotto/_typed.py
"""Typed conveniences: fill a pydantic model, classify, and turn a typed function into a decision.

A pydantic model becomes one question per field:
    Literal[...] or Enum of strings -> choice    bool -> yes/no    float with ge=0, le=1 -> probability of yes
The field description is the question; without one, the field name is.
"""

from __future__ import annotations

import enum
import functools
import inspect
import typing
from collections.abc import Callable, Sequence
from typing import Any, Literal, TypeVar, get_args, get_origin

from pydantic import BaseModel

from ._decider import Decider
from ._models import DEFAULT_MODEL, Engine
from ._protocol import JSON, Question, choice, yes_no

M = TypeVar("M", bound=BaseModel)
F = TypeVar("F", bound=Callable[..., Any])

_default: Decider | None = None
_default_args: dict[str, Any] = {"model": DEFAULT_MODEL}


def use(model: str = DEFAULT_MODEL, *, engine: Engine | None = None, **kwargs: Any) -> None:
    """Set the model the module-level functions (`choose`, `extract`, `@decision`, …) use."""
    global _default
    _default = None
    _default_args.clear()
    _default_args.update(model=model, engine=engine, **kwargs)


def default() -> Decider:
    """The shared Decider behind the module-level functions."""
    global _default
    if _default is None:
        _default = Decider(**_default_args)
    return _default


def _options(annotation: Any) -> list[str] | None:
    """String options of a Literal or Enum annotation, else None."""
    if get_origin(annotation) is Literal and all(isinstance(a, str) for a in get_args(annotation)):
        return list(get_args(annotation))
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return [str(member.value) for member in annotation]
    return None


def _question(name: str, annotation: Any, description: str | None, metadata: Sequence[Any] = ()) -> Question:
    asked = description or name.replace("_", " ").capitalize() + "?"
    if (opts := _options(annotation)) is not None:
        return choice(asked, opts)
    if annotation is bool:
        return yes_no(asked)
    if annotation is float and _unit_interval(metadata):
        return yes_no(asked)
    raise TypeError(f"field {name!r}: use a Literal or Enum of strings, bool, or a float with ge=0 and le=1")


def _unit_interval(metadata: Sequence[Any]) -> bool:
    bounds = {k: getattr(m, k) for m in metadata for k in ("ge", "le") if getattr(m, k, None) is not None}
    return bounds.get("ge") == 0 and bounds.get("le") == 1


def questions_for(schema: type[BaseModel]) -> dict[str, Question]:
    """One question per field of `schema`."""
    return {
        name: _question(name, f.annotation, f.description, f.metadata)
        for name, f in schema.model_fields.items()
    }


def _value(annotation: Any, answer: Any) -> Any:
    if annotation is float:
        return answer.probability
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return annotation(answer.value)
    return answer.value


def extract(schema: type[M], state: JSON, *, decider: Decider | None = None) -> M:
    """Fill `schema` from `state`: every field is answered by the model, in one request."""
    decision = (decider or default()).decide(state, questions_for(schema))
    return schema(**{name: _value(f.annotation, decision[name]) for name, f in schema.model_fields.items()})


async def aextract(schema: type[M], state: JSON, *, decider: Decider | None = None) -> M:
    """`extract`, for asyncio."""
    decision = await (decider or default()).adecide(state, questions_for(schema))
    return schema(**{name: _value(f.annotation, decision[name]) for name, f in schema.model_fields.items()})


def classify(
    data: JSON,
    labels: Sequence[str] | type[enum.Enum],
    instructions: str | None = None,
    *,
    decider: Decider | None = None,
) -> Any:
    """Pick the label that fits `data` (marvin-style). An Enum class returns an Enum member."""
    opts = _options(labels) if isinstance(labels, type) else list(labels)
    answer = (decider or default()).choose(data, opts or [], instructions)
    return labels(answer.value) if isinstance(labels, type) else answer.value


def decision(fn: F | None = None, *, decider: Decider | None = None) -> Any:
    """Turn a typed, docstring-only function into a decision (magentic and promptic style).

        @ornotto.decision
        def route(request: str) -> Literal["docs", "python", "fea"]:
            '''Which kind of help does this FontLab user want?'''

    The docstring is the question. One argument is the state; several become a JSON state keyed by
    argument name. The return type picks the question: Literal/Enum -> choice, bool -> yes/no,
    float -> probability of yes, a pydantic model -> `extract`.
    """
    if fn is None:
        return functools.partial(decision, decider=decider)
    signature = inspect.signature(fn)
    returns = typing.get_type_hints(fn).get("return")
    asked = inspect.getdoc(fn)

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        state = next(iter(bound.arguments.values())) if len(bound.arguments) == 1 else dict(bound.arguments)
        d = decider or default()
        if isinstance(returns, type) and issubclass(returns, BaseModel):
            return extract(returns, state, decider=d)
        if returns is float:
            return d.check(state, asked or fn.__name__).probability
        answer = d.decide(state, {"answer": _question(fn.__name__, returns, asked)})["answer"]
        return _value(returns, answer)

    return wrapper
