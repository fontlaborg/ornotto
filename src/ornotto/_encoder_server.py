# this_file: src/ornotto/_encoder_server.py
"""One native decision encoder in a managed, loopback-only System One process.

The existing Server lifecycle starts/stops this process. Requests run serially;
model weights and upstream action/temperature fields stay in the native runtime.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from ._models import PYTHON_ENGINES
from ._protocol import as_question
from ._remote import validate_response

MAX_BODY_BYTES = 1024 * 1024
DEFAULT_INSTRUCTIONS = {
    "choice": "Choose the option that best matches the supplied state.",
    "noul": "Is the supplied statement true?",
    "score": "Place the supplied state on the ordered scale.",
}
XDECISION_INSTALL = "uv pip install 'xdecision[apple] @ git+https://github.com/xnetsc/xDecision.git@4082689a093393358534fda26a945699080eb572'"


def load(engine: str, path: str, device: str, adapter: str | None = None) -> Any:
    """Load the upstream implementation, never interpret its weights as llama.cpp."""
    if sys.version_info < (3, 11):
        raise RuntimeError("Native encoder runtimes require Python 3.11 or newer")
    if engine not in PYTHON_ENGINES:
        raise ValueError(f"Unknown encoder engine {engine!r}")
    try:
        if engine in ("raz-nli", "transformers-nli", "transformers-slot"):
            from ._transformers_decision import TorchDecision

            return TorchDecision(path, engine, device)
        if engine == "systemone-lite":
            from ._upstream_decision import Lite

            return Lite(path, device)
        if engine == "system-one-mlx":
            from ._upstream_decision import Mpuig

            return Mpuig(path, device, adapter)
        if engine == "onnx-scorer":
            from ._onnx_scorer import OnnxScorer

            return OnnxScorer(path, device)
        if engine == "bosun-gguf":
            from ._bosun_gguf import Bosun

            return Bosun(path, device)
    except ModuleNotFoundError as error:
        raise RuntimeError(
            f"{engine} dependency missing ({error.name}); see https://fontlab.org/ornotto/10-package/#additional-system-one-models"
        ) from error
    module = "laya_mlx" if engine == "laya-mlx" else "xdecision"
    try:
        runtime = importlib.import_module(module)
    except ModuleNotFoundError as error:
        install = 'uv pip install "ornotto[laya-mlx]"' if engine == "laya-mlx" else XDECISION_INSTALL
        raise RuntimeError(
            f"{engine} runtime/dependency missing ({error.name}). Install with: {install}"
        ) from error
    if engine == "laya-mlx":
        return runtime.load(path, device=device, dtype="float16")
    if device == "gpu":
        if sys.platform != "darwin":
            raise ValueError(
                "xDecision GPU adapter currently requires Apple silicon MLX; use gpu=False for CPU"
            )
        return runtime.load(path, backend="mlx", device="gpu", dtype="float16", batch_size=8)
    return runtime.load(path, backend="torch", device="cpu")


def predict(runtime: Any, name: str, body: dict[str, Any]) -> dict[str, Any]:
    """Preserve native answers; reject reported state truncation and invalid distributions."""
    questions = {key: as_question(value) for key, value in body["questions"].items()}
    if not questions:
        raise ValueError("ask at least one question")
    native = {key: q.to_system_one() for key, q in questions.items()}
    for key, question in questions.items():
        native[key].setdefault("instructions", DEFAULT_INSTRUCTIONS[question.kind])
    result = runtime.predict(body["state"], native)
    if result.get("usage", {}).get("state_tokens_dropped", 0) or result.get("usage", {}).get("truncated"):
        raise ValueError("STATE_TRUNCATED: state exceeds the encoder context; shorten it")
    result = {**result, "model": name}
    return validate_response(result, questions)


def make_server(runtime: Any, name: str, port: int) -> HTTPServer:
    """Bind only loopback and serialize inference through the standard HTTP server."""

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status: int, body: dict[str, Any]) -> None:
            data = json.dumps(body, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.reply(200, {"ready": True})
            elif self.path == "/v1/models":
                self.reply(
                    200, {"models": [{"name": name, "description": "Native encoder", "release_date": ""}]}
                )
            else:
                self.reply(404, {"error": "Unknown endpoint"})

        def do_POST(self) -> None:
            if self.path != "/v1/systemone":
                self.reply(404, {"error": "Unknown endpoint"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY_BYTES:
                    raise ValueError("request body must be between 1 byte and 1 MiB")
                body = json.loads(self.rfile.read(length))
                if body.get("model", name) != name:
                    raise ValueError(f"This process serves {name}")
                result = predict(runtime, name, body)
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                self.reply(400, {"error": str(error)})
                return
            except (RuntimeError, FloatingPointError) as error:
                self.reply(500, {"error": str(error)})
                return
            self.reply(200, result)

    return HTTPServer(("127.0.0.1", port), Handler)


def main() -> None:
    """CLI used by Server.command; heavy imports occur only in the child process."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=PYTHON_ENGINES, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--device", choices=("cpu", "gpu"), required=True)
    args = parser.parse_args()
    runtime = load(args.engine, args.model, args.device, args.adapter)
    try:
        with make_server(runtime, args.name, args.port) as server:
            server.serve_forever()
    finally:
        if hasattr(runtime, "close"):
            runtime.close()


if __name__ == "__main__":
    main()
