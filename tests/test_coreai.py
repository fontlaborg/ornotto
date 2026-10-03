# this_file: tests/test_coreai.py
"""Native CoreAI contracts without loading weights in the unit-test process."""

import sys

import pytest

from ornotto._coreai import CoreAIDecider, CoreAIExtractor, NativeBridge
from ornotto._models import MODELS


def test_clef_when_registered_then_both_variants_pin_complete_native_assets():
    for variant in ("fp16", "int8mix"):
        spec = MODELS["clef-flash-coreai-" + variant]
        assert spec.engines == ("clef-coreai",)
        assert len(spec.revision) == 40
        assert "host/*" in spec.snapshot
        assert any("head_bucket" in p for p in spec.snapshot)
        assert any(variant + "_pf64" in p for p in spec.snapshot)


def test_native_bridge_when_child_answers_then_persistent_and_closed(tmp_path):
    script = tmp_path / "bridge.py"
    script.write_text(
        'import sys,json\nprint(json.dumps({"ready":True}),flush=True)\n'
        'for line in sys.stdin: print(json.dumps({"echo":json.loads(line)}),flush=True)\n'
    )
    bridge = NativeBridge([sys.executable, str(script)], timeout=2)
    pid = bridge.process.pid
    assert bridge.request({"text": "é"}) == {"echo": {"text": "é"}}
    assert bridge.request({"text": "two"}) == {"echo": {"text": "two"}}
    assert bridge.process.pid == pid
    bridge.close()
    assert bridge.process.poll() is not None


def test_native_bridge_when_child_stalls_then_timeout_kills_it(tmp_path):
    script = tmp_path / "stall.py"
    script.write_text("import time\ntime.sleep(10)\n")
    with pytest.raises(TimeoutError, match="Core AI"):
        NativeBridge([sys.executable, str(script)], timeout=0.05)


def test_clef_when_cpu_requested_then_rejects_before_native_start():
    with pytest.raises(ValueError, match="GPU"):
        CoreAIDecider("unused", "cpu", "fp16")


def test_pii_when_invalid_labels_or_threshold_then_rejects_before_inference():
    runtime = object.__new__(CoreAIExtractor)
    for labels in ([], ["email"] * 2, [""]):
        with pytest.raises(ValueError):
            runtime.extract("hello", labels)
    with pytest.raises(ValueError):
        runtime.extract("hello", ["email"], threshold=float("nan"))


def test_pii_when_native_spans_then_preserves_redaction_and_confidence():
    runtime = object.__new__(CoreAIExtractor)

    class Bridge:
        def request(self, body):
            assert body == {"text": "Mail a@b.com", "labels": ["email"], "threshold": 0.5}
            return {
                "spans": [{"label": "email", "text": "a@b.com", "start": 5, "end": 12, "confidence": 0.9}],
                "redacted": "Mail [EMAIL]",
            }

    runtime.bridge = Bridge()
    result = runtime.extract("Mail a@b.com", ["email"])
    assert result["entities"] == {"email": ["a@b.com"]}
    assert result["redacted"] == "Mail [EMAIL]"
    assert result["spans"][0]["confidence"] == 0.9


def test_native_bridge_when_partial_line_stalls_then_deadline_still_applies(tmp_path):
    script = tmp_path / "partial.py"
    script.write_text('import sys,time\nsys.stdout.write("{");sys.stdout.flush();time.sleep(10)\n')
    with pytest.raises(TimeoutError, match="Core AI"):
        NativeBridge([sys.executable, str(script)], timeout=0.05)


def test_pii_when_native_rejects_long_input_then_preserves_error():
    runtime = object.__new__(CoreAIExtractor)

    class Bridge:
        def request(self, body):
            raise ValueError("STATE_TRUNCATED: text exceeds token budget")

    runtime.bridge = Bridge()
    with pytest.raises(ValueError, match="STATE_TRUNCATED"):
        runtime.extract("too long", ["email"])


def test_clef_when_predicting_then_supplies_required_native_model_and_joint_schema():
    runtime = object.__new__(CoreAIDecider)

    class Bridge:
        def request(self, body):
            assert body["model"] == "clef-flash"
            assert set(body["questions"]) == {"one", "two"}
            return {"answers": {}}

    runtime.bridge = Bridge()
    assert runtime.predict("state", {"one": {}, "two": {}}) == {"answers": {}}


def test_clef_when_many_fields_then_client_never_splits_joint_schema():
    from ornotto._engines import Adapter

    assert Adapter("clef-coreai", "clef-flash-coreai-int8mix").max_questions == sys.maxsize
