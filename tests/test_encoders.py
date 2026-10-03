# this_file: tests/test_encoders.py
"""Native encoder integration without loading weights."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from ornotto import Decider, choice, score, yes_no
from ornotto._engines import Adapter, command
from ornotto._models import MODELS, ResolvedModel, resolve


@pytest.mark.parametrize(
    "name,engine",
    [("laya-multilingual-mlx", "laya-mlx"), ("xdecision-f16", "xdecision"), ("xdecision-q8", "xdecision")],
)
def test_resolve_when_encoder_registered_then_native_runtime_and_expected_artifact(
    name, engine, monkeypatch, tmp_path
):
    monkeypatch.setattr("ornotto._models._download", lambda repo, file: tmp_path / file)
    monkeypatch.setattr("huggingface_hub.snapshot_download", lambda **kwargs: str(tmp_path))
    resolved = resolve(name)
    assert resolved.engines == (engine,), "Custom encoder architecture must not be sent to llama.cpp"
    assert resolved.gguf == (tmp_path if engine == "laya-mlx" else tmp_path / MODELS[name].file)


@pytest.mark.parametrize("engine", ["laya-mlx", "xdecision"])
@pytest.mark.parametrize("gpu", [True, False])
def test_command_when_encoder_then_python_server_uses_requested_device(engine, gpu, tmp_path):
    args = command(engine, ResolvedModel("encoder", tmp_path, (engine,)), 9010, gpu)
    assert args[:3] == [sys.executable, "-m", "ornotto._encoder_server"]
    assert args[args.index("--device") + 1] == ("gpu" if gpu else "cpu")
    adapter = Adapter(engine, "encoder")
    assert adapter.native and not adapter.calibrated, (
        "Temperature recipes are not verified calibration on this task"
    )
    path, body = adapter.request("state", {"a": choice(None, ["a", "b"])})
    assert path == "/v1/systemone" and body["questions"]["a"]["type"] == "choice"


def test_predict_when_native_encoder_then_defaults_types_and_action_are_preserved():
    from ornotto._encoder_server import predict

    runtime = SimpleNamespace(
        predict=Mock(
            return_value={
                "model": "native",
                "usage": {"input_tokens": 3, "output_tokens": 0},
                "answers": {
                    "a": {
                        "type": "choice",
                        "choice": "b",
                        "probabilities": {"a": 0.2, "b": 0.8},
                        "action": {"act_probability": 0.6},
                    },
                    "n": {"type": "noul", "noul": 0.7},
                    "s": {
                        "type": "score",
                        "score": 1.4,
                        "probabilities": {"0": 0.1, "1": 0.4, "2": 0.5},
                        "legend": {"0": "low", "1": "medium", "2": "high"},
                    },
                },
            }
        )
    )
    questions = {
        "a": choice(None, ["a", "b"]).to_system_one(),
        "n": yes_no("Is it?").to_system_one(),
        "s": score(None, ["low", "medium", "high"]).to_system_one(),
    }
    body = predict(runtime, "encoder", {"state": {"text": "state"}, "questions": questions})
    assert runtime.predict.call_args.args[0] == {"text": "state"}
    assert all(q.get("instructions") for q in runtime.predict.call_args.args[1].values()), (
        "Encoder needs explicit instructions"
    )
    assert body["model"] == "encoder" and body["answers"]["a"]["action"] == {"act_probability": 0.6}
    assert body["answers"]["s"]["score"] == 1.4


@pytest.mark.parametrize("bad", [float("nan"), -1, 2])
def test_predict_when_invalid_probability_then_response_is_rejected(bad):
    from ornotto._encoder_server import predict

    runtime = SimpleNamespace(
        predict=lambda *args: {
            "model": "native",
            "usage": {},
            "answers": {"a": {"type": "noul", "noul": bad}},
        }
    )
    with pytest.raises(ValueError, match="probabilit"):
        predict(runtime, "encoder", {"state": "s", "questions": {"a": yes_no("Is it?").to_system_one()}})


def test_predict_when_state_truncated_then_request_fails_instead_of_silent_cut():
    from ornotto._encoder_server import predict

    runtime = SimpleNamespace(
        predict=lambda *args: {
            "model": "native",
            "usage": {"state_tokens_dropped": 4},
            "answers": {"a": {"type": "noul", "noul": 0.7}},
        }
    )
    with pytest.raises(ValueError, match="STATE_TRUNCATED"):
        predict(runtime, "encoder", {"state": "s", "questions": {"a": yes_no("Is it?").to_system_one()}})


@pytest.mark.parametrize("engine,module", [("laya-mlx", "laya_mlx"), ("xdecision", "xdecision")])
def test_load_when_runtime_available_then_native_api_and_cpu_setting(engine, module, monkeypatch, tmp_path):
    from ornotto._encoder_server import load

    native = SimpleNamespace(load=Mock(return_value="agent"))
    monkeypatch.setitem(sys.modules, module, native)
    assert load(engine, str(tmp_path), "cpu") == "agent"
    assert native.load.call_args.kwargs["device"] == "cpu"


@pytest.mark.parametrize("engine", ["laya-mlx", "xdecision"])
async def test_decider_when_native_encoder_http_then_sync_async_answers_match(engine):
    import threading

    from ornotto._encoder_server import make_server

    runtime = SimpleNamespace(
        predict=lambda state, qs: {
            "model": "native",
            "usage": {"input_tokens": 2, "output_tokens": 0},
            "answers": {k: {"type": "noul", "noul": 0.8} for k in qs},
        }
    )
    server = make_server(runtime, "encoder", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        decider = Decider("encoder", engine=engine, url=url)
        assert decider.check("text", "Is it?").value is True
        result = await decider.adecide("text", {"answer": yes_no("Is it?")})
        assert result.answer.value is True and result.usage["output_tokens"] == 0
        assert httpx.get(url + "/health").json()["ready"]
        assert httpx.get(url + "/v1/models").json()["models"][0]["name"] == "encoder"
        assert httpx.post(url + "/v1/systemone", content="malformed").status_code == 400
        assert httpx.post(url + "/v1/systemone", json={"state": "s", "questions": {}}).status_code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    assert not thread.is_alive(), "Test server must release its listener"


@pytest.mark.parametrize("engine", ["laya-mlx", "xdecision"])
async def test_encoder_when_pydantic_ai_agent_then_typed_output_from_real_http(engine):
    import threading
    from typing import Literal

    from pydantic import BaseModel, Field
    from pydantic_ai import Agent

    from ornotto._encoder_server import make_server
    from ornotto.pydantic_ai import model

    class Triage(BaseModel):
        task: Literal["docs", "python"] = Field(description="What task?")
        code: bool = Field(description="Does it ask for code?")

    def native_predict(state, questions):
        answers = {}
        for key, q in questions.items():
            if q["type"] == "noul":
                answers[key] = {"type": "noul", "noul": 0.9, "confidence": 0.9}
            else:
                labels = list(q["criteria"])
                answers[key] = {
                    "type": "choice",
                    "choice": labels[1],
                    "confidence": 0.8,
                    "probabilities": {labels[0]: 0.2, labels[1]: 0.8},
                }
        return {"model": "native", "answers": answers, "usage": {"input_tokens": 8, "output_tokens": 0}}

    server = make_server(SimpleNamespace(predict=native_predict), "encoder", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        decider = Decider("encoder", engine=engine, url=f"http://127.0.0.1:{server.server_port}")
        result = await Agent(model(decider), output_type=Triage).run("Write a Python script")
        assert result.output == Triage(task="python", code=True), (
            "Actual SDK must read native choice and noul"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("engine", ["laya-mlx", "xdecision"])
def test_native_runtime_when_process_shared_then_shutdown_releases_port(engine, tmp_path, monkeypatch):
    import socket

    from ornotto import shutdown
    from ornotto._engines import Server

    source = """def load(*args, **kwargs):
    class Runtime:
        def predict(self, state, questions):
            return {'model':'native','usage':{},'answers':{k:{'type':'noul','noul':.8} for k in questions}}
    return Runtime()
"""
    module = "laya_mlx" if engine == "laya-mlx" else "xdecision"
    (tmp_path / (module + ".py")).write_text(source)
    package_src = Path(__file__).resolve().parents[1] / "src"
    monkeypatch.setenv("PYTHONPATH", str(tmp_path) + ":" + str(package_src))
    resolved = ResolvedModel("native", tmp_path, (engine,))
    try:
        a = Server.shared(engine, resolved, False)
        assert a is Server.shared(engine, resolved, False), "Identical models must share one child process"
        port = a.port
        assert Decider("native", engine=engine, url=a.url).check("state", "Is it?").value is True
    finally:
        shutdown()
    assert a.process.poll() is not None
    with socket.socket() as sock:
        assert sock.connect_ex(("127.0.0.1", port)) != 0, "Shutdown must release the listener"


@pytest.mark.parametrize("name", ["laya-multilingual-mlx", "xdecision-f16", "xdecision-q8"])
@pytest.mark.parametrize("override", ["metadata", "head"])
def test_resolve_when_native_override_then_rejected_before_download(name, override, monkeypatch):
    monkeypatch.setattr("ornotto._models._download", Mock(side_effect=AssertionError("must not download")))
    with pytest.raises(ValueError, match="own profile/head"):
        resolve(name, **{override: "custom.json"})


@pytest.mark.parametrize("engine", ["laya-mlx", "xdecision"])
def test_load_when_optional_runtime_missing_then_actionable_install_message(engine, monkeypatch):
    from ornotto._encoder_server import load

    def missing(name):
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr("ornotto._encoder_server.importlib.import_module", missing)
    with pytest.raises(RuntimeError, match="Install with: uv pip install"):
        load(engine, "native", "cpu")
