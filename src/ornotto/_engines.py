# this_file: src/ornotto/_engines.py
"""Finding, starting and talking to the inference engines.

Both engines are local HTTP servers. `Server` starts one on a free loopback port, waits until it answers
`/health`, and stops it when the interpreter exits. One server per (engine, model, options) is shared by
every `Decider` in the process, so opening the same model twice costs nothing. An `Adapter` turns a System
One request into the engine's HTTP call and its reply back into a System One response.
"""

from __future__ import annotations

import atexit
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from ._models import Engine, ResolvedModel
from ._protocol import Question, from_pcd, to_pcd

BINARIES: dict[Engine, str] = {"dohnuts": "dohnuts-cli", "pcd": "pcd_server"}
ENV: dict[Engine, str] = {"dohnuts": "ORNOTTO_DOHNUTS_BIN", "pcd": "ORNOTTO_PCD_BIN"}
START_TIMEOUT = 180.0  # seconds for a server to load its model
DOHNUTS_MAX_QUESTIONS = 64  # per request; the server default is 8
PCD_CACHE_BYTES = 512 * 1024 * 1024


class EngineNotFound(RuntimeError):
    pass


def find_binary(engine: Engine) -> Path:
    """The engine executable: $ORNOTTO_<ENGINE>_BIN, the copy bundled in the wheel, or PATH."""
    name = BINARIES[engine] + (".exe" if sys.platform == "win32" else "")
    candidates = [os.environ.get(ENV[engine]), Path(__file__).parent / "_bin" / name, shutil.which(name)]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise EngineNotFound(
        f"{name} not found. Install a platform wheel of ornotto, put {name} on PATH, or set {ENV[engine]}."
    )


def gpu_available() -> bool:
    """The bundled macOS build uses Metal; elsewhere the bundled builds are CPU only."""
    return sys.platform == "darwin"


def command(engine: Engine, model: ResolvedModel, port: int, gpu: bool) -> list[str]:
    """The command line that serves `model` with `engine` on `port`."""
    binary = str(find_binary(engine))
    if engine == "dohnuts":
        if model.metadata is None:
            raise ValueError(
                f"{model.name} has no dohnuts metadata JSON; pass metadata=... or use engine='pcd'"
            )
        cmd = [
            binary,
            "--server",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--model",
            str(model.gguf),
            "--metadata",
            str(model.metadata),
            "--max-questions",
            str(DOHNUTS_MAX_QUESTIONS),
            "--gpu-layers",
            "-1" if gpu else "0",
        ]
        return cmd + (["--head", str(model.head)] if model.head else [])
    return [
        binary,
        "--bind",
        "127.0.0.1",
        "--port",
        str(port),
        "--model",
        str(model.gguf),
        "--models-dir",
        str(model.gguf.parent),
        "--cache-bytes",
        str(PCD_CACHE_BYTES),
    ]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    """One engine process serving one model on a loopback port."""

    _running: dict[tuple[Any, ...], Server] = {}
    _lock = threading.Lock()

    def __init__(self, engine: Engine, model: ResolvedModel, gpu: bool):
        self.engine, self.model = engine, model
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        # The engines log to stderr freely; a file never blocks them the way a full pipe would.
        self.log = Path(tempfile.gettempdir()) / f"ornotto-{engine}-{self.port}.log"
        with self.log.open("wb") as log:
            self.process = subprocess.Popen(
                command(engine, model, self.port, gpu),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        self._wait_ready()

    @classmethod
    def shared(cls, engine: Engine, model: ResolvedModel, gpu: bool) -> Server:
        """The running server for this engine, model and device, started on first use."""
        key = (engine, model.gguf, model.metadata, model.head, gpu)
        with cls._lock:
            server = cls._running.get(key)
            if server is None or server.process.poll() is not None:
                server = cls._running[key] = cls(engine, model, gpu)
            return server

    def _wait_ready(self) -> None:
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                tail = self.log.read_text(errors="replace")[-2000:]
                raise RuntimeError(
                    f"{self.engine} exited while loading {self.model.name} (log {self.log}):\n{tail}"
                )
            try:
                health = httpx.get(self.url + "/health", timeout=2.0).json()
                if health.get("ready", health.get("status") == "ok"):
                    return
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(0.2)
        self.stop()
        raise TimeoutError(
            f"{self.engine} did not load {self.model.name} within {START_TIMEOUT:.0f} s (log {self.log})"
        )

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    @classmethod
    def stop_all(cls) -> None:
        """Stop every server this process started."""
        with cls._lock:
            for server in cls._running.values():
                server.stop()
            cls._running.clear()


atexit.register(Server.stop_all)


@dataclass(frozen=True)
class Adapter:
    """How to ask one engine a System One request."""

    engine: Engine
    model_name: str

    @property
    def calibrated(self) -> bool:
        return self.engine == "dohnuts"

    @property
    def max_questions(self) -> int:
        return DOHNUTS_MAX_QUESTIONS if self.engine == "dohnuts" else 63

    def request(self, state: Any, questions: Mapping[str, Question]) -> tuple[str, dict[str, Any]]:
        """(path, JSON body) for one request."""
        if self.engine == "dohnuts":
            body = {
                "state": state,
                "model": self.model_name,
                "questions": {name: q.to_system_one() for name, q in questions.items()},
            }
            return "/v1/systemone", body
        return "/v1/pcd/decode", to_pcd(state, questions)

    def response(self, body: dict[str, Any], questions: Mapping[str, Question]) -> dict[str, Any]:
        """The engine's reply -> a System One response."""
        return body if self.engine == "dohnuts" else from_pcd(body, questions)
