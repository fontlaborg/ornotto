# this_file: src/ornotto/_clef_mlx.py
"""Adapters for the pinned model authors' MLX joint-schema readouts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from ._protocol import as_question
from ._transformers_decision import answer, options


def module_at(path: Path, name: str, *, package: bool = False):
    """Import explicitly pinned checkpoint code, including relative package imports."""
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)] if package else None
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Missing native runtime: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def native_questions(questions):
    """Native Clef and CLM represent a score rubric as an ordered list."""
    native = {key: dict(value) for key, value in questions.items()}
    for key, value in native.items():
        if value["type"] == "score":
            value["criteria"] = list(as_question(questions[key]).options.values())
    return native


class Clef:
    """Run the author head, never the backbone's generative output."""

    def __init__(self, path: str, device: str):
        if sys.platform != "darwin" or device != "gpu":
            raise ValueError("Clef MLX requires Apple silicon GPU; use a Clef GGUF for CPU")
        self.module = module_at(Path(path) / "clef_mlx.py", "_ornotto_native_clef")
        self.runtime = self.module.load(path)
        self.community = hasattr(self.runtime, "systemone")
        self.limit = 4096

    def predict(self, state, questions):
        record = {"model": "clef", "state": state, "questions": native_questions(questions)}
        if self.community:
            return self.runtime.systemone(record, max_length=self.limit, truncate=False)
        # Trevor's upstream encoder silently slices state; measure the complete
        # prompt first and refuse it before any backbone/head operation.
        ids, _ = self.module.encode_record(self.runtime[1], record, max_length=sys.maxsize)
        if len(ids) > self.limit:
            raise ValueError(f"STATE_TRUNCATED: joint prompt exceeds {self.limit} tokens")
        distributions = self.module.decide(self.runtime, record, max_length=self.limit)
        answers = {}
        for key, raw in questions.items():
            question = as_question(raw)
            keys, descriptions = options(question)
            answers[key] = answer(question.kind, keys, descriptions, [distributions[key][k] for k in keys])
        return {"answers": answers, "usage": {"input_tokens": len(ids), "output_tokens": 0}}
