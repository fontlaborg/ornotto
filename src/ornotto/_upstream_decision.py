# this_file: src/ornotto/_upstream_decision.py
"""Small adapters around pinned upstream System One implementations."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path


class Mpuig:
    def __init__(self, path: str, device: str, adapter: str | None):
        if device != "gpu":
            raise ValueError("system-one-mlx requires Apple silicon GPU; it has no CPU backend")
        from jev.engine import SystemOneEngine

        directory = Path(adapter or path)
        temperature = directory / "temperature.json"
        expected = json.loads(temperature.read_text())["prediction_config"]["backbone_files"]
        # The upstream fingerprint includes every JSON in the directory. Hub
        # releases also contain calibration/training files, absent from the
        # fitted identity. Present only the exact bound assets, without changing
        # the source snapshot or weakening its hash check.
        self.view = tempfile.TemporaryDirectory(prefix="ornotto-mpuig-")
        view = Path(self.view.name)
        for name in expected:
            source = Path(path) / name
            if not source.is_file():
                self.view.cleanup()
                raise FileNotFoundError(f"Calibrated backbone asset missing: {name}")
            destination = view / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(source.resolve())
        self.runtime = SystemOneEngine(
            str(view),
            adapter_path=adapter,
            renderer_version="structured-v1",
            readout_version="letters-v1",
            temperature_path=str(temperature),
            mlx_cache_limit_bytes=512 * 1024 * 1024,
        )

    def predict(self, state, questions):
        return self.runtime.respond({"state": state, "questions": questions})

    def close(self):
        self.view.cleanup()


class Lite:
    """Alias arbitrary caller keys to distinct symbols before upstream slot scoring."""

    def __init__(self, path: str, device: str):
        from systemone_lite.infer import LoadedModel, SystemOneEngine

        from ._transformers_decision import TorchDecision

        loaded = TorchDecision(path, "transformers-slot", device)
        self.runtime = SystemOneEngine(
            LoadedModel(path, path, loaded.tokenizer, loaded.model, loaded.model.device),
            use_prefix_cache=False,
        )
        self.tokenizer = loaded.tokenizer

    def predict(self, state, questions):
        from systemone_lite.prompt import build_prompts
        from systemone_lite.schema import SystemOneRequest

        aliases, native = {}, {}
        for key, question in questions.items():
            native[key] = dict(question)
            if question["type"] == "choice":
                criteria = question["criteria"]
                if len(criteria) > 26:
                    raise ValueError("systemone-lite supports at most 26 distinct option symbols")
                aliases[key] = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", criteria, strict=False))
                native[key]["criteria"] = {
                    symbol: criteria[label] or label for symbol, label in aliases[key].items()
                }
        request = SystemOneRequest.model_validate({"state": state, "questions": native})
        for prompt in build_prompts(request).values():
            if len(self.tokenizer.encode(prompt)) > 4096:
                raise ValueError("STATE_TRUNCATED: systemone-lite prompt exceeds 4096 tokens")
        response = self.runtime.decide(request).model_dump()
        for key, mapping in aliases.items():
            result = response["answers"][key]
            result["choice"] = mapping[result["choice"]]
            result["probabilities"] = {
                mapping[symbol]: probability for symbol, probability in result["probabilities"].items()
            }
        return response
