# this_file: tests/test_clef_clm.py
"""Native head contracts and all requested quantizations, without loading weights."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ornotto._engines import command
from ornotto._models import MODELS, ResolvedModel, resolve

NAMES = [
    *(f"clef-q{n}" for n in (3, 4, 5)),
    "clef-mlx4",
    *(f"clm-8b-q{n}-" + ("km" if n < 6 else "k") for n in (4, 5, 6)),
    "clm-8b-mlx6",
    *(f"clef-flash-q{n}" for n in (3, 4, 5, 6)),
    "clef-flash-mlx8",
    "clef-flash-mlx4",
]


def test_requested_variants_have_pinned_native_readouts():
    for name in NAMES:
        spec = MODELS[name]
        assert len(spec.revision) == 40, name
        assert spec.engines[0] in ("llama", "clef-mlx", "clm-gguf", "clm-mlx"), name
        assert not spec.unavailable, name
        if name.startswith("clm-"):
            assert spec.head_repo == "Contrastive-LM/CLM-v0.1-8B", name
            assert len(spec.head_revision) == 40, name


@pytest.mark.parametrize("name", ["clm-8b-q4-km", "clm-8b-mlx6"])
def test_clm_resolve_downloads_pinned_projection_head(monkeypatch, tmp_path, name):
    import huggingface_hub

    download = Mock(return_value=str(tmp_path / "checkpoint"))
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", download)
    monkeypatch.setattr(huggingface_hub, "snapshot_download", Mock(return_value=str(tmp_path)))
    model = resolve(name)
    assert model.head == tmp_path / "checkpoint"
    assert any(call.kwargs.get("revision") == MODELS[name].head_revision for call in download.call_args_list)


def test_clef_requires_whole_prompt_prefill(monkeypatch):
    monkeypatch.setattr("ornotto._engines.find_binary", lambda _: Path("/bin/llama-server"))
    args = command("llama", ResolvedModel("clef-q3", Path("m.gguf"), ("llama",)), 8123, True)
    assert args[args.index("--ubatch-size") + 1] == "4096"
    assert args[args.index("--batch-size") + 1] == "4096"


def test_clm_managed_command_carries_head():
    args = command(
        "clm-gguf",
        ResolvedModel("clm-8b-q4-km", Path("m.gguf"), ("clm-gguf",), head=Path("h.pt")),
        8123,
        True,
    )
    assert args[args.index("--head") + 1] == "h.pt"


def test_clef_trevor_rejects_full_prompt_overflow_before_inference():
    from ornotto._clef_mlx import Clef

    runtime = Clef.__new__(Clef)
    runtime.community = False
    runtime.limit = 4096
    runtime.runtime = (None, None, None, None)
    runtime.module = Mock()
    runtime.module.encode_record.return_value = ([0] * 4097, [])
    with pytest.raises(ValueError, match="STATE_TRUNCATED"):
        runtime.predict("state", {"x": {"type": "choice", "criteria": {"a": "A", "b": "B"}}})
    runtime.module.decide.assert_not_called()


def test_clef_trevor_keeps_native_distribution_and_score_levels():
    from ornotto._clef_mlx import Clef

    runtime = Clef.__new__(Clef)
    runtime.community = False
    runtime.limit = 4096
    runtime.runtime = (None, None, None, None)
    runtime.module = Mock()
    runtime.module.encode_record.return_value = ([1, 2], [])
    runtime.module.decide.return_value = {"x": {"0": 0.2, "1": 0.8}}
    result = runtime.predict("state", {"x": {"type": "score", "criteria": ["low", "high"]}})
    assert result["answers"]["x"]["score"] == 0.8
    assert result["answers"]["x"]["probabilities"] == {"0": 0.2, "1": 0.8}
    assert result["usage"] == {"input_tokens": 2, "output_tokens": 0}
    record = runtime.module.decide.call_args.args[1]
    assert record["questions"]["x"]["criteria"] == ["low", "high"]


def test_clm_mlx_refuses_truncation_and_returns_float32(monkeypatch):
    import sys

    from ornotto._clm_decision import MLXEmbedder

    np = pytest.importorskip("numpy")
    monkeypatch.setitem(sys.modules, "numpy", np)
    encoder = Mock()
    encoder.tok.side_effect = lambda text: {"input_ids": list(range(len(text)))}
    encoder.embed.return_value = (np.ones((1, 4096)), 3)
    runtime = MLXEmbedder.__new__(MLXEmbedder)
    runtime.encoder = encoder
    runtime.limit = 4
    with pytest.raises(ValueError, match="STATE_TRUNCATED"):
        runtime.embed(["longtext"])
    encoder.embed.assert_not_called()
    output, count = runtime.embed(["yes"])
    assert output.dtype == np.float32 and count == 3


def test_clef_conversion_preserves_quantized_backbone_and_attaches_head(tmp_path):
    import json

    np = pytest.importorskip("numpy")
    gguf = pytest.importorskip("gguf")
    pytest.importorskip("torch")
    safetensors = pytest.importorskip("safetensors.numpy")
    from ornotto._clef_gguf import prepare

    source = tmp_path / "backbone.gguf"
    writer = gguf.GGUFWriter(str(source), "qwen35")
    writer.add_uint32("qwen35.block_count", 1)
    original = gguf.quants.quantize(
        np.arange(256, dtype=np.float32).reshape(1, 256), gguf.GGMLQuantizationType.Q4_0
    )
    writer.add_tensor("token_embd.weight", original, raw_dtype=gguf.GGMLQuantizationType.Q4_0)
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_tensors_to_file()
    writer.close()
    checkpoint = tmp_path / "head"
    checkpoint.mkdir()
    (checkpoint / "joint_head_config.json").write_text(
        json.dumps({"routing_layers": 2, "layers": 4, "heads": 16})
    )
    safetensors.save_file(
        {
            "prior_logit_scale": np.array(0, dtype=np.float32),
            "joint_logit_scale": np.array(1, dtype=np.float32),
            "residual_gate": np.array(0, dtype=np.float32),
            "hidden_norm.weight": np.ones(256, dtype=np.float32),
        },
        str(checkpoint / "joint_head.safetensors"),
    )
    before = source.read_bytes()
    result = prepare(source, checkpoint)
    reader = gguf.GGUFReader(str(result))
    assert reader.fields["general.architecture"].contents() == "clef"
    assert reader.fields["clef.block_count"].contents() == 1
    assert reader.fields["clef.decision.type"].contents() == "clef"
    backbone = next(t for t in reader.tensors if t.name == "token_embd.weight")
    assert backbone.tensor_type == gguf.GGMLQuantizationType.Q4_0
    assert backbone.data.tobytes() == original.tobytes(), "No requantization or backbone changes"
    assert {"decision.scales", "decision.hidden_norm.weight"} <= {t.name for t in reader.tensors}
    assert source.read_bytes() == before, "Original artifact must remain intact"
    assert prepare(source, checkpoint) == result


def test_community_clef_supplies_model_and_disables_truncation():
    from ornotto._clef_mlx import Clef

    runtime = Clef.__new__(Clef)
    runtime.community = True
    runtime.limit = 4096
    runtime.runtime = Mock()
    expected = {
        "answers": {"x": {"type": "noul", "noul": 0.7}},
        "usage": {"input_tokens": 4, "output_tokens": 0},
    }
    runtime.runtime.systemone.return_value = expected
    assert runtime.predict("state", {"x": {"type": "noul"}}) == expected
    call = runtime.runtime.systemone.call_args
    assert isinstance(call.args[0]["model"], str)
    assert call.kwargs == {"max_length": 4096, "truncate": False}


def test_native_clm_questions_preserve_reference_rendering_and_list_rubric():
    from ornotto._clef_mlx import native_questions

    original = {
        "route": {"type": "choice", "instructions": "Exact task", "criteria": {"z": "Last", "a": "First"}},
        "level": {"type": "score", "criteria": {"1": "high", "0": "low"}},
    }
    result = native_questions(original)
    assert result["route"] == original["route"]
    assert result["level"]["criteria"] == ["low", "high"]
    assert isinstance(original["level"]["criteria"], dict)


def test_clef_joint_schema_is_not_split_at_the_independent_question_limit():
    from ornotto import Decider, yes_no

    decider = Decider("clef-flash-q4", engine="llama", url="http://127.0.0.1:8123")
    questions = {str(i): yes_no("True?") for i in range(80)}
    assert decider._chunks(questions) == [questions], "Joint fields cannot be answered in separate requests"
