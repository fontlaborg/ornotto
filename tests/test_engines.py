# this_file: tests/test_engines.py
from pathlib import Path

import pytest

from ornotto._engines import EngineNotFound, command, find_binary
from ornotto._models import MODELS, ResolvedModel, resolve


def test_find_binary_when_env_points_to_file_then_used(tmp_path, monkeypatch):
    exe = tmp_path / "pcd_server"
    exe.write_text("")
    monkeypatch.setenv("ORNOTTO_PCD_BIN", str(exe))
    assert find_binary("pcd") == exe


def test_find_binary_when_nothing_found_then_helpful_error(monkeypatch):
    monkeypatch.setenv("ORNOTTO_DOHNUTS_BIN", "/nonexistent")
    monkeypatch.setattr("ornotto._engines.Path.is_file", lambda self: False)
    with pytest.raises(EngineNotFound, match="ORNOTTO_DOHNUTS_BIN"):
        find_binary("dohnuts")


def test_command_when_dohnuts_then_metadata_head_and_gpu(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/" + engine))
    m = ResolvedModel("kev", Path("/m/kev.gguf"), ("dohnuts",), Path("/m/kev.json"), Path("/m/head.f32"))
    cmd = command("dohnuts", m, 9000, gpu=True)
    assert cmd[:2] == ["/bin/dohnuts", "--server"]
    assert "--metadata" in cmd and "--head" in cmd and cmd[cmd.index("--gpu-layers") + 1] == "-1"


def test_command_when_dohnuts_without_metadata_then_error(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/" + engine))
    with pytest.raises(ValueError, match="metadata"):
        command("dohnuts", ResolvedModel("x", Path("/m/x.gguf"), ("pcd",)), 9000, gpu=False)


def test_command_when_pcd_then_loopback_and_model(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/" + engine))
    cmd = command("pcd", ResolvedModel("q", Path("/m/q.gguf"), ("pcd",)), 9001, gpu=False)
    assert cmd[cmd.index("--bind") + 1] == "127.0.0.1" and cmd[cmd.index("--model") + 1] == "/m/q.gguf"


def test_registry_when_default_then_dedicated_apache_model():
    spec = MODELS["decider-0.8b"]
    assert spec.engines[0] == "dohnuts" and spec.license == "apache-2.0" and spec.metadata


def test_resolve_when_unknown_name_then_lists_registered_models():
    with pytest.raises(FileNotFoundError, match="decider-0.8b"):
        resolve("no-such-model")


def test_resolve_when_local_file_then_pcd_only(tmp_path):
    gguf = tmp_path / "mine.gguf"
    gguf.write_bytes(b"GGUF")
    assert resolve(str(gguf)).engines == ("pcd",)
    assert resolve(str(gguf), metadata=tmp_path / "m.json").engines == ("dohnuts", "pcd")
