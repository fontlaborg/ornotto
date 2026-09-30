# this_file: tests/test_ollaya.py
"""The ollaya engine. Unit tests never run ollaya; `test_engine_*` needs it (run with `pytest -m engine`)."""

import os
import subprocess
from pathlib import Path

import httpx
import pytest

import ornotto
from ornotto.__main__ import Cli
from ornotto._decider import Decider, DecisionError
from ornotto._engines import (
    Adapter,
    EngineNotFound,
    Server,
    command,
    environment,
    find_binary,
)
from ornotto._models import MODELS, ResolvedModel, resolve
from ornotto._protocol import choice

KEV = ResolvedModel("ollaya-kev-0.8b", None, ("ollaya",), tag="kev:0.8b")


class FakeProcess:
    """Stands in for the `ollaya serve` process."""

    def __init__(self, *args, **kwargs):
        self.args, self.env, self.alive = args[0], kwargs.get("env"), True

    def poll(self):
        return None if self.alive else 0

    def wait(self, timeout=None):
        self.alive = False
        return 0

    def terminate(self):
        self.alive = False

    kill = terminate


@pytest.fixture
def fake_ollaya(monkeypatch):
    """Record every `ollaya` CLI call and HTTP request a Server makes; serve `kev:0.8b` from the store."""
    calls: dict[str, list] = {"run": [], "get": [], "post": []}
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/ollaya"))
    monkeypatch.setattr("ornotto._engines.subprocess.Popen", FakeProcess)

    def run(cmd, **kwargs):
        calls["run"].append((cmd[1:], kwargs["env"]))
        return subprocess.CompletedProcess(cmd, 0)

    def get(url, **kwargs):
        calls["get"].append(url)
        if url.endswith("/api/tags"):
            return httpx.Response(200, json={"models": [{"name": "kev:0.8b", "model": "kev:0.8b"}]})
        return httpx.Response(200, text="Ollaya is running")

    def post(url, json=None, **kwargs):
        calls["post"].append((url, json))
        return httpx.Response(200, json={"model": json["model"], "done_reason": "load"})

    monkeypatch.setattr("ornotto._engines.subprocess.run", run)
    monkeypatch.setattr("ornotto._engines.httpx.get", get)
    monkeypatch.setattr("ornotto._engines.httpx.post", post)
    return calls


# -- models ------------------------------------------------------------------------------------------------


def test_registry_when_any_model_then_default_engine_listed_and_source_consistent(monkeypatch):
    monkeypatch.setattr("ornotto._models._download", lambda repo, file: Path(file))  # no network
    for spec in MODELS.values():
        assert spec.engines and resolve(spec.name).engines[0] == spec.engines[0], spec.name
        assert spec.size_gb > 0, f"{spec.name} has no size"
        assert spec.file.endswith(".gguf") != bool(spec.tag), (
            f"{spec.name} needs exactly one of a GGUF or a tag"
        )
        assert (spec.tag is not None) == (spec.engines == ("ollaya",)), (
            f"{spec.name}: tags run on ollaya only"
        )


def test_resolve_when_registered_ollaya_model_then_tag_and_no_download(monkeypatch):
    monkeypatch.setattr("ornotto._models._download", lambda *a: pytest.fail("ollaya models never download"))
    r = resolve("ollaya-kev-0.8b")
    assert (r.tag, r.gguf, r.engines) == ("kev:0.8b", None, ("ollaya",))


def test_resolve_when_ollaya_prefix_then_any_tag():
    assert resolve("ollaya:winnow:e4b").tag == "winnow:e4b"


def test_decider_when_bare_tag_and_ollaya_engine_then_tag_on_the_wire():
    d = Decider("kev:4b", engine="ollaya")
    assert d.engine == "ollaya" and d.adapter.model_name == "kev:4b"


def test_decider_when_registered_ollaya_model_then_registry_name_and_wire_tag():
    d = Decider("ollaya-decider-0.8b")
    assert (d.model_name, d.engine, d.adapter.model_name) == ("ollaya-decider-0.8b", "ollaya", "decider:0.8b")


def test_decider_when_url_and_ollaya_name_then_tag_on_the_wire():
    url = "http://127.0.0.1:11435"
    assert Decider("ollaya-kev-0.8b", engine="ollaya", url=url).adapter.model_name == "kev:0.8b"
    assert Decider("ollaya:laya:en", engine="ollaya", url=url).adapter.model_name == "laya:en"
    assert Decider("decider", url=url).adapter.model_name == "decider"


def test_decider_when_ollaya_model_on_pcd_then_refused():
    with pytest.raises(ValueError, match="runs on ollaya"):
        Decider("ollaya-kev-0.8b", engine="pcd")


# -- finding and starting ollaya ---------------------------------------------------------------------------


def test_find_binary_when_ollaya_only_in_local_bin_then_found(tmp_path, monkeypatch):
    exe = tmp_path / ".local" / "bin" / "ollaya"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    monkeypatch.delenv("ORNOTTO_OLLAYA_BIN", raising=False)
    monkeypatch.setattr("ornotto._engines.shutil.which", lambda name: None)
    monkeypatch.setattr("ornotto._engines.Path.home", lambda: tmp_path)
    assert find_binary("ollaya") == exe


def test_find_binary_when_ollaya_missing_then_install_line(tmp_path, monkeypatch):
    monkeypatch.delenv("ORNOTTO_OLLAYA_BIN", raising=False)
    monkeypatch.setattr("ornotto._engines.shutil.which", lambda name: None)
    monkeypatch.setattr("ornotto._engines.Path.home", lambda: tmp_path)
    with pytest.raises(EngineNotFound, match="ollaya.dev/install.sh"):
        find_binary("ollaya")


def test_command_when_ollaya_then_serve_only(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/ollaya"))
    assert command("ollaya", KEV, 9002, gpu=True) == ["/bin/ollaya", "serve"]


def test_command_when_gguf_engine_gets_ollaya_model_then_error(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/" + engine))
    with pytest.raises(ValueError, match="engine='ollaya'"):
        command("pcd", KEV, 9002, gpu=False)


def test_environment_when_ollaya_then_private_port_one_model_kept_loaded(monkeypatch):
    monkeypatch.setenv("OLLAYA_HOST", "127.0.0.1:11435")  # a user's daemon must not be touched
    monkeypatch.setenv("OLLAYA_KEEP_ALIVE", "0")
    monkeypatch.setenv("OLLAYA_API_KEY", "secret")  # would make our unauthenticated requests fail
    monkeypatch.setenv("OLLAYA_LOG_DIR", "/logs")  # would leave our log file empty
    monkeypatch.setenv("OLLAYA_MODELS", "/store")
    env = environment("ollaya", 9002)
    assert env is not None
    assert env["OLLAYA_HOST"] == "127.0.0.1:9002", "each server gets its own port"
    assert env["OLLAYA_MAX_LOADED_MODELS"] == "1" and env["OLLAYA_KEEP_ALIVE"] == "-1"
    assert "OLLAYA_API_KEY" not in env and "OLLAYA_LOG_DIR" not in env
    assert env["OLLAYA_MODELS"] == "/store", "the store location is the caller's choice"
    assert environment("pcd", 9002) is None


def test_server_when_tag_in_store_then_preloaded_not_pulled(fake_ollaya):
    server = Server("ollaya", KEV, gpu=True)
    assert server.process.args == ["/bin/ollaya", "serve"]
    assert server.process.env["OLLAYA_HOST"] == f"127.0.0.1:{server.port}"
    assert fake_ollaya["get"][0] == server.url + "/", "readiness is GET / (ollaya has no /health)"
    assert fake_ollaya["run"] == [], "nothing to pull"
    assert fake_ollaya["post"] == [(server.url + "/api/decide", {"model": "kev:0.8b", "keep_alive": -1})]


def test_server_when_tag_missing_then_pulled_through_this_server(fake_ollaya):
    von = ResolvedModel("ollaya-von-1.1", None, ("ollaya",), tag="von:1.1")
    server = Server("ollaya", von, gpu=True, preload=False)
    (args, env), *_ = fake_ollaya["run"]
    assert args == ["pull", "von:1.1"] and env["OLLAYA_HOST"] == f"127.0.0.1:{server.port}"
    assert fake_ollaya["post"] == [], "preload=False only pulls"


def test_server_when_stopped_then_ollaya_stop_on_its_own_host(fake_ollaya):
    server = Server("ollaya", KEV, gpu=True)
    server.stop()
    (args, env), *_ = fake_ollaya["run"]
    assert args == ["stop"] and env["OLLAYA_HOST"] == f"127.0.0.1:{server.port}"
    assert server.process.poll() == 0


def test_server_when_preload_fails_then_server_stopped_and_error(fake_ollaya, monkeypatch):
    monkeypatch.setattr(
        "ornotto._engines.httpx.post", lambda url, **kw: httpx.Response(404, json={"code": "MODEL_NOT_FOUND"})
    )
    started = []
    monkeypatch.setattr(
        "ornotto._engines.subprocess.Popen",
        lambda *a, **kw: started.append(FakeProcess(*a, **kw)) or started[-1],
    )
    with pytest.raises(RuntimeError, match="could not load kev:0.8b: 404"):
        Server("ollaya", KEV, gpu=True)
    assert started[0].poll() == 0, "a server that failed to load is not left running"
    assert [args for args, _ in fake_ollaya["run"]] == [["stop"]]


# -- asking ----------------------------------------------------------------------------------------------


def test_adapter_when_ollaya_then_system_one_calibrated():
    a = Adapter("ollaya", "kev:0.8b")
    path, body = a.request("Build a kern feature", {"t": choice("What?", ["docs", "fea"])})
    assert path == "/v1/systemone" and body["model"] == "kev:0.8b"
    assert body["questions"]["t"] == {
        "type": "choice",
        "instructions": "What?",
        "criteria": {"docs": None, "fea": None},
    }
    assert a.calibrated and a.max_questions == 256
    reply = {
        "answers": {"t": {"type": "choice", "choice": "fea", "probabilities": {"docs": 0.1, "fea": 0.9}}}
    }
    assert a.response(reply, {}) is reply


def _decider_answering(status: int, body: dict) -> Decider:
    d = Decider("laya:en", engine="ollaya", url="http://127.0.0.1:1")
    d._post = lambda post, state, qs: d._check(httpx.Response(status, json=body), qs)  # type: ignore[method-assign]
    return d


def test_decide_when_state_truncated_then_plain_error():
    d = _decider_answering(
        422, {"error": "state has 900 tokens, laya:en takes 512", "code": "STATE_TRUNCATED"}
    )
    with pytest.raises(DecisionError, match="longer than laya:en's context.*STATE_TRUNCATED"):
        d.choose("x" * 5000, ["docs", "fea"])


def test_decide_when_ollaya_answers_then_calibrated_answer():
    probs = {"docs": 0.2, "fea": 0.8}
    d = _decider_answering(
        200, {"answers": {"answer": {"type": "choice", "choice": "fea", "probabilities": probs}}}
    )
    answer = d.choose("Build a kern feature", ["docs", "fea"])
    assert answer.value == "fea" and answer.calibrated


# -- a real ollaya ---------------------------------------------------------------------------------------


def _kev_in_store() -> bool:
    store = Path(os.environ.get("OLLAYA_MODELS", Path.home() / ".ollaya" / "models"))
    return (store / "manifests" / "ollaya.dev" / "library" / "kev" / "0.8b").is_file()


@pytest.mark.engine
def test_engine_ollaya_when_kev_then_one_decision():
    """Start ollaya with kev:0.8b (about 5 GB resident). Skips unless kev:0.8b is in OLLAYA_MODELS."""
    try:
        find_binary("ollaya")
    except EngineNotFound as e:
        pytest.skip(str(e))
    if not _kev_in_store():
        pytest.skip("kev:0.8b is not in OLLAYA_MODELS; run `ornotto pull ollaya-kev-0.8b` first")
    try:
        answer = Decider("ollaya-kev-0.8b").choose(
            "Build a kern feature for A V W T", ["docs", "python", "fea"], "What does the user want?"
        )
        assert answer.value in ("docs", "python", "fea"), answer.probabilities
        assert answer.calibrated and sum(answer.probabilities.values()) == pytest.approx(1.0, abs=1e-3)
    finally:
        ornotto.shutdown()
    assert not Server._running, "ollaya is stopped after the test"


def test_shared_when_ollaya_deciders_differ_only_in_gpu_then_one_server(fake_ollaya, monkeypatch):
    monkeypatch.setattr(Server, "_running", {})
    on, off = Decider("ollaya:kev:0.8b", gpu=True), Decider("ollaya:kev:0.8b", gpu=False)
    assert on.url == off.url, "ollaya ignores gpu, so a second resident server would waste memory"
    assert len(Server._running) == 1


def test_cli_pull_when_ollaya_model_then_private_server_started_without_preload_and_stopped(fake_ollaya):
    assert Cli().pull("ollaya:von:1.1") == "ollaya von:1.1"
    assert [args for args, _ in fake_ollaya["run"]] == [["pull", "von:1.1"], ["stop"]]
    assert fake_ollaya["post"] == [], "pull must not load the model"


def test_cli_models_when_listed_then_column_fits_longest_name():
    rows = Cli().models().splitlines()
    width = max(map(len, MODELS))
    assert len(rows) == len(MODELS) + 1
    assert rows[0].startswith("name".ljust(width) + " engines"), "header aligns with the longest name"
    assert all(row.startswith(name.ljust(width) + " ") for row, name in zip(rows[1:], MODELS, strict=True)), (
        "every name is padded to the same width"
    )
