# this_file: tests/test_systemone_models.py
"""New checkpoint routing, without downloading weights or hiding unavailable assets."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ornotto import choice, score, yes_no
from ornotto._engines import Adapter, command
from ornotto._models import MODELS, ResolvedModel, resolve
from ornotto._transformers_decision import answer, options

READY = {
    "rune-systemone-q3": "llama",
    "oomu-systemone-0.6b": "bosun-gguf",
    "raz-nli-xsmall-openjev": "raz-nli",
    "raz-nli-base": "raz-nli",
    "systemone-lite-0.5b": "systemone-lite",
    "system-one-270m": "transformers-slot",
    "system-one-scorer-onnx": "onnx-scorer",
    "system-one-minicpm5-2b-q8": "system-one-mlx",
    "system-one-qwen3-0.6b": "system-one-mlx",
    "system-one-gold": "transformers-nli",
    "system-one-distilled": "transformers-nli",
    "system-one-zeroshot": "transformers-nli",
}


@pytest.mark.parametrize("name,engine", READY.items())
def test_new_model_when_resolved_then_correct_runtime_and_pinned_artifacts(
    name, engine, monkeypatch, tmp_path
):
    calls = []

    def snapshot(**kwargs):
        calls.append(kwargs)
        return str(tmp_path)

    monkeypatch.setattr("huggingface_hub.snapshot_download", snapshot)
    monkeypatch.setattr("huggingface_hub.hf_hub_download", lambda *args, **kwargs: str(tmp_path / args[1]))
    model = resolve(name)
    assert model.engines == (engine,), "Decision heads must use their own inference contract"
    assert MODELS[name].revision and len(MODELS[name].revision) == 40
    assert all(len(c["revision"]) == 40 for c in calls), "Snapshots must be reproducible"
    assert model.adapter is not None if name == "system-one-qwen3-0.6b" else model.adapter is None


@pytest.mark.parametrize(
    "name",
    [
        "system-one-gemma-coreml",
        "nev-lite-systemone",
    ],
)
def test_unavailable_model_when_resolved_then_explains_missing_assets_before_download(name, monkeypatch):
    monkeypatch.setattr(
        "huggingface_hub.snapshot_download", lambda **kwargs: pytest.fail("No speculative download")
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        resolve(name)


@pytest.mark.parametrize("engine", set(READY.values()) - {"llama"})
def test_new_native_engine_when_command_then_loopback_python_adapter(engine, tmp_path):
    args = command(engine, ResolvedModel("test", tmp_path, (engine,)), 9001, False)
    assert args[:3] == [sys.executable, "-m", "ornotto._encoder_server"]
    assert args[-1] == "cpu"
    assert Adapter(engine, "test").native


def test_llama_when_command_then_native_decision_endpoint_and_explicit_device(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/llama-server"))
    args = command("llama", ResolvedModel("rune", Path("rune.gguf"), ("llama",)), 9001, False)
    assert args[0] == "/bin/llama-server"
    assert "--jinja" in args and args[args.index("--gpu-layers") + 1] == "0"
    assert args[args.index("--host") + 1] == "127.0.0.1"
    assert Adapter("llama", "rune").native


@pytest.mark.parametrize(
    "question,keys",
    [
        (choice("Choose", ["a", "b"]), ["a", "b"]),
        (yes_no("Is it?"), ["false", "true"]),
        (score("Rate", ["low", "high"]), ["0", "1"]),
    ],
)
def test_options_when_each_primitive_then_order_and_descriptions_are_explicit(question, keys):
    got, descriptions = options(question)
    assert got == keys and len(descriptions) == len(keys)
    result = answer(question.kind, got, descriptions, [0.2, 0.8])
    assert result["confidence"] == 0.8, "The TypeSafe SDK requires choice/score confidence"
    if question.kind == "noul":
        assert result["noul"] == 0.8
    elif question.kind == "score":
        assert result["score"] == 0.8 and result["legend"] == {"0": "low", "1": "high"}
    else:
        assert result["choice"] == "b"


def test_mpuig_when_release_contains_extra_metadata_then_only_bound_assets_reach_runtime(
    monkeypatch, tmp_path
):
    import json

    from ornotto._upstream_decision import Mpuig

    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "training.json").write_text("{}")
    (tmp_path / "temperature.json").write_text(
        json.dumps({"prediction_config": {"backbone_files": {"config.json": "bound-hash"}}})
    )
    calls = []

    def factory(path, **kwargs):
        calls.append((sorted(p.name for p in Path(path).iterdir()), kwargs))
        return SimpleNamespace(respond=Mock(return_value={"answers": {}}))

    monkeypatch.setitem(sys.modules, "jev.engine", SimpleNamespace(SystemOneEngine=factory))
    runtime = Mpuig(str(tmp_path), "gpu", None)
    try:
        assert calls[0][0] == ["config.json"], (
            "Calibration and training JSON must not pollute the bound model identity"
        )
        assert calls[0][1]["temperature_path"] == str(tmp_path / "temperature.json")
        assert runtime.predict("state", {}) == {"answers": {}}
    finally:
        runtime.close()
    assert (tmp_path / "training.json").exists(), "Source snapshots must remain intact"


def test_bosun_when_stable_slot_compiler_then_permutation_is_reproducible_and_labels_preserved():
    import json

    from ornotto._bosun_prompt import render_decision_prompt

    kwargs = dict(
        state={"message": "test"},
        instructions="Pick",
        candidates=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        decision_type="choice",
        decision_tokens=["slot0", "slot1"],
        seed=0,
        row_id="0",
    )
    content, order, slots = render_decision_prompt(**kwargs)
    assert render_decision_prompt(**kwargs) == (content, order, slots)
    assert order == [1, 0] and slots == {"b": 0, "a": 1}
    body = json.loads(content)
    assert body["question"]["criteria"] == [["slot0", 1, "B", ""], ["slot1", 0, "A", ""]]
    with pytest.raises(ValueError, match="2 to 255"):
        render_decision_prompt(**{**kwargs, "candidates": []})


def test_onnx_when_long_input_then_rejected_before_graph_execution():
    from ornotto._onnx_scorer import OnnxScorer

    runtime = object.__new__(OnnxScorer)
    runtime.tokenizer = SimpleNamespace(encode=lambda text, **kwargs: list(range(len(text))))
    with pytest.raises(ValueError, match="STATE_TRUNCATED"):
        runtime.sequences("x" * 384, choice("Choose", ["a", "b"]), ["a", "b"])


def test_coreai_when_registered_then_external_catalog_and_cpu_rejected(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda engine: Path("/bin/systemone"))
    model = resolve("system-one-scorer-coreai")
    assert model.gguf is None and model.tag == "system-one-scorer-4b"
    args = command("coreai", model, 9001, True)
    assert args == ["/bin/systemone", "serve", "--model", model.tag, "--host", "127.0.0.1", "--port", "9001"]
    with pytest.raises(ValueError, match="requires.*GPU"):
        command("coreai", model, 9001, False)
