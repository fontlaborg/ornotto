# this_file: src/ornotto/_engines.py
"""Finding, starting and talking to the inference engines.

Every engine is a local HTTP server. `Server` starts one on a free loopback port, waits until it answers
(`/health`, or `/` for ollaya), and stops it when the interpreter exits. One server per (engine, model,
options) is shared by every `Decider` in the process, so opening the same model twice costs nothing. An
`Adapter` turns a System One request into the engine's HTTP call and its reply back into a System One
response.
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

BINARIES: dict[Engine, str] = {"dohnuts": "dohnuts-cli", "pcd": "pcd_server", "ollaya": "ollaya"}
ENV: dict[Engine, str] = {
    "dohnuts": "ORNOTTO_DOHNUTS_BIN",
    "pcd": "ORNOTTO_PCD_BIN",
    "ollaya": "ORNOTTO_OLLAYA_BIN",
}
START_TIMEOUT = 180.0  # seconds for a server to load its model
DOHNUTS_MAX_QUESTIONS = 64  # per request; the server default is 8
OLLAYA_MAX_QUESTIONS = 256  # ollaya's limit per request
OLLAYA_LOAD_TIMEOUT = 600.0  # seconds for the preload; ollaya's own load timeout defaults to 5 minutes
OLLAYA_INSTALL = "curl -fsSL https://ollaya.dev/install.sh | OLLAYA_INSTALL_DIR=$HOME/.local sh"
PCD_CACHE_BYTES = 512 * 1024 * 1024


class EngineNotFound(RuntimeError):
    pass


def find_binary(engine: Engine) -> Path:
    """The engine executable: $ORNOTTO_<ENGINE>_BIN, the copy bundled in the wheel, or PATH.

    ollaya is never bundled; it is looked up on PATH and then in ~/.local/bin, where its installer puts it.
    """
    name = BINARIES[engine] + (".exe" if sys.platform == "win32" else "")
    candidates: list[str | Path | None] = [os.environ.get(ENV[engine])]
    if engine == "ollaya":
        candidates += [shutil.which(name), Path.home() / ".local" / "bin" / name]
    else:
        candidates += [Path(__file__).parent / "_bin" / name, shutil.which(name)]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    if engine == "ollaya":
        raise EngineNotFound(f"ollaya not found. Install it with `{OLLAYA_INSTALL}` or set {ENV[engine]}.")
    raise EngineNotFound(
        f"{name} not found. Install a platform wheel of ornotto, put {name} on PATH, or set {ENV[engine]}."
    )


def gpu_available() -> bool:
    """The bundled macOS build uses Metal; elsewhere the bundled builds are CPU only."""
    return sys.platform == "darwin"


def command(engine: Engine, model: ResolvedModel, port: int, gpu: bool) -> list[str]:
    """The command line that serves `model` with `engine` on `port`; ollaya reads the port from env."""
    binary = str(find_binary(engine))
    if engine == "ollaya":
        if model.tag is None:
            raise ValueError(f"{model.name} is a GGUF file; ollaya runs ollaya models (see `ornotto models`)")
        return [binary, "serve"]
    if model.gguf is None:
        raise ValueError(f"{model.name} is an ollaya model; use engine='ollaya'")
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
        "--gpu-layers",
        "-1" if gpu else "0",
    ] + ([] if gpu else ["--cpu"])


def environment(engine: Engine, port: int) -> dict[str, str] | None:
    """The engine's environment: None (inherit) except for ollaya, which takes its settings from env vars.

    ollaya listens on our port, holds one model and keeps it loaded until the server stops, overriding any
    OLLAYA_* setting the caller has. It logs to our log file and needs no key. `OLLAYA_MODELS`, the model
    store (default ~/.ollaya/models), and `OLLAYA_DEVICE` are inherited.
    """
    if engine != "ollaya":
        return None
    env = {k: v for k, v in os.environ.items() if k not in ("OLLAYA_API_KEY", "OLLAYA_LOG_DIR")}
    env.update(OLLAYA_HOST=f"127.0.0.1:{port}", OLLAYA_MAX_LOADED_MODELS="1", OLLAYA_KEEP_ALIVE="-1")
    return env


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Server:
    """One engine process serving one model on a loopback port."""

    _running: dict[tuple[Any, ...], Server] = {}
    _lock = threading.Lock()

    def __init__(self, engine: Engine, model: ResolvedModel, gpu: bool, *, preload: bool = True):
        self.engine, self.model = engine, model
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.env = environment(engine, self.port)
        # The engines log to stderr freely; a file never blocks them the way a full pipe would.
        self.log = Path(tempfile.gettempdir()) / f"ornotto-{engine}-{self.port}.log"
        with self.log.open("wb") as log:
            self.process = subprocess.Popen(
                command(engine, model, self.port, gpu),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=self.env,
            )
        try:
            self._wait_ready()
            if engine == "ollaya":
                self._ollaya_load(preload)
        except BaseException:
            self.stop()  # not registered yet, so nothing else would stop it
            raise

    @classmethod
    def shared(cls, engine: Engine, model: ResolvedModel, gpu: bool) -> Server:
        """The running server for this engine, model and device, started on first use.

        ollaya picks its own device (OLLAYA_DEVICE) and ignores `gpu`, so the flag is left out of its key:
        Deciders that differ only in `gpu` share one server, keeping one model resident.
        """
        key = (engine, model.gguf, model.metadata, model.head, model.tag, None if engine == "ollaya" else gpu)
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
                if self._ready():
                    return
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(0.2)
        self.stop()
        raise TimeoutError(
            f"{self.engine} did not load {self.model.name} within {START_TIMEOUT:.0f} s (log {self.log})"
        )

    def _ready(self) -> bool:
        if self.engine == "ollaya":  # no /health; `/` answers "Ollaya is running"
            return httpx.get(self.url + "/", timeout=2.0).status_code == 200
        health = httpx.get(self.url + "/health", timeout=2.0).json()
        return bool(health.get("ready", health.get("status") == "ok"))

    def _ollaya(self, *args: str, timeout: float | None = None) -> None:
        """Run the ollaya CLI against this server (never against a daemon on the default port)."""
        with self.log.open("ab") as log:
            subprocess.run(
                [str(find_binary("ollaya")), *args],
                env=self.env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=timeout,
            )

    def _ollaya_load(self, preload: bool) -> None:
        """Pull the tag if the store lacks it, then load it, so the first question does not wait for it."""
        tag = self.model.tag
        if tag is None:  # command() refuses this too, but asserts vanish under -O
            raise ValueError(f"{self.model.name} has no ollaya tag")
        full = tag if ":" in tag else tag + ":latest"
        tags = httpx.get(self.url + "/api/tags", timeout=10.0).json().get("models", [])
        if not any(full in (m.get("name"), m.get("model")) for m in tags):
            self._ollaya("pull", tag)
        if preload:
            r = httpx.post(
                self.url + "/api/decide", json={"model": tag, "keep_alive": -1}, timeout=OLLAYA_LOAD_TIMEOUT
            )
            if r.status_code != 200:
                raise RuntimeError(f"ollaya could not load {tag}: {r.status_code} {r.text[:500]}")

    def stop(self) -> None:
        if self.engine == "ollaya" and self.process.poll() is None:
            try:  # `ollaya stop` unloads the models and ends the server, runners included
                self._ollaya("stop", timeout=30)
                self.process.wait(timeout=10)
            except (OSError, EngineNotFound, subprocess.SubprocessError):
                pass
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
    """The name the engine knows the model by: an ollaya tag, or ornotto's name."""

    @property
    def native(self) -> bool:
        """dohnuts and ollaya speak System One (`/v1/systemone`) themselves; pcdServer needs translating."""
        return self.engine in ("dohnuts", "ollaya")

    @property
    def calibrated(self) -> bool:
        return self.native  # dohnuts scales by temperature; ollaya ships a calibration per model

    @property
    def max_questions(self) -> int:
        return {"dohnuts": DOHNUTS_MAX_QUESTIONS, "ollaya": OLLAYA_MAX_QUESTIONS}.get(self.engine, 63)

    def request(self, state: Any, questions: Mapping[str, Question]) -> tuple[str, dict[str, Any]]:
        """(path, JSON body) for one request."""
        if self.native:
            body = {
                "state": state,
                "model": self.model_name,
                "questions": {name: q.to_system_one() for name, q in questions.items()},
            }
            return "/v1/systemone", body
        return "/v1/pcd/decode", to_pcd(state, questions)

    def response(self, body: dict[str, Any], questions: Mapping[str, Question]) -> dict[str, Any]:
        """The engine's reply -> a System One response."""
        return body if self.native else from_pcd(body, questions)
