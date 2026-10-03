# this_file: src/ornotto/_coreai.py
"""Persistent JSON-line bridge to the pinned native macOS 27 implementations."""

from __future__ import annotations

import asyncio
import json
import math
import os
import select
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

PII_REPO = "mlboydaisuke/GLiNER2-PII-CoreAI"
PII_REVISION = "74fb5c19e7eba2d4ebad95f90eeb6d996432575d"


class NativeBridge:
    """One resident native process, serialized requests and bounded pipe waits."""

    def __init__(self, args: list[str], timeout: float = 180.0):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.pending = b""
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            if self.read() != {"ready": True}:
                raise RuntimeError("Core AI bridge did not become ready")
        except BaseException:
            self.close()
            raise

    def read(self) -> dict[str, Any]:
        assert self.process.stdout is not None
        deadline = time.monotonic() + self.timeout
        while b"\n" not in self.pending:
            remaining = max(0, deadline - time.monotonic())
            if not select.select([self.process.stdout], [], [], remaining)[0]:
                self.close()
                raise TimeoutError("Core AI bridge timed out")
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                self.close()
                raise RuntimeError("Core AI bridge exited before replying")
            self.pending += chunk
            if len(self.pending) > 1024 * 1024:
                self.close()
                raise RuntimeError("Core AI bridge response exceeds 1 MiB")
        line, self.pending = self.pending.split(b"\n", 1)
        result = json.loads(line)
        if not isinstance(result, dict):
            raise RuntimeError("Core AI bridge returned a non-object")
        if "error" in result:
            raise ValueError(result["error"])
        return result

    def request(self, body: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            assert self.process.stdin is not None
            try:
                self.process.stdin.write(
                    (json.dumps(body, ensure_ascii=False, allow_nan=False) + "\n").encode()
                )
                self.process.stdin.flush()
                return self.read()
            except (BrokenPipeError, json.JSONDecodeError):
                self.close()
                raise RuntimeError("Core AI bridge failed") from None

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()


def bridge_args(mode: str, path: str, variant: str) -> list[str]:
    if sys.platform != "darwin":
        raise RuntimeError("Native Core AI requires macOS 27 and Apple silicon")
    binary = os.environ.get("ORNOTTO_COREAI_BRIDGE_BIN") or shutil.which("ornotto-coreai")
    if not binary or not Path(binary).is_file():
        raise RuntimeError(
            "Build runtimes/coreai/build.py and set ORNOTTO_COREAI_BRIDGE_BIN "
            "to the ornotto-coreai executable"
        )
    return [binary, mode, path, variant]


class CoreAIDecider:
    """Use the author's native joint-schema readout for text/JSON states."""

    def __init__(self, path: str, device: str, variant: str):
        if device != "gpu":
            raise ValueError("Clef Core AI requires the Mac GPU runtime")
        self.bridge = NativeBridge(bridge_args("clef", path, variant))

    def predict(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        return self.bridge.request({"model": "clef-flash", "state": state, "questions": questions})

    def close(self) -> None:
        self.bridge.close()


class CoreAIExtractor:
    """Native GLiNER2 PII spans and redaction, kept separate from typed decisions.

    Use as a context manager. Downloads only the pinned macOS bundle into the
    configured Hugging Face cache. Confidence is a native span score.
    """

    def __init__(self, path: str | Path | None = None):
        args = bridge_args("pii", str(path or ""), "fp16")
        if path is None:
            from huggingface_hub import snapshot_download

            path = snapshot_download(PII_REPO, revision=PII_REVISION, allow_patterns=["macos/*", "LICENSE"])
        args[2] = str(path)
        self.bridge = NativeBridge(args)

    def extract(self, text: str, labels: list[str], *, threshold: float = 0.5) -> dict[str, Any]:
        if not isinstance(text, str) or not 1 <= len(labels) <= 16:
            raise ValueError("text must be a string and labels must contain 1...16 entries")
        if any(not isinstance(label, str) or not label.strip() for label in labels) or len(
            set(labels)
        ) != len(labels):
            raise ValueError("labels must be unique nonempty strings")
        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("threshold must be finite and between 0 and 1")
        result = self.bridge.request({"text": text, "labels": labels, "threshold": threshold})
        entities: dict[str, list[str]] = {}
        for span in result["spans"]:
            confidence = span["confidence"]
            if not math.isfinite(confidence) or not 0 <= confidence <= 1 or span["label"] not in labels:
                raise RuntimeError("Invalid native entity span")
            if span["text"] not in text:
                raise RuntimeError("Native entity does not occur in the input")
            entities.setdefault(span["label"], []).append(span["text"])
        return {**result, "entities": entities}

    async def aextract(self, text: str, labels: list[str], *, threshold: float = 0.5) -> dict[str, Any]:
        return await asyncio.to_thread(self.extract, text, labels, threshold=threshold)

    def close(self) -> None:
        self.bridge.close()

    def __enter__(self) -> CoreAIExtractor:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
