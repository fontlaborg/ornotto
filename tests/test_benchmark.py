# this_file: tests/test_benchmark.py
"""Check diagram inputs, portable output, and the actual browser-side Pareto math."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "src_docs/gen_diagrams.py").exists():
    pytest.skip("Documentation tools are tested in the repository checkout", allow_module_level=True)
spec = importlib.util.spec_from_file_location("gen_diagrams", ROOT / "src_docs/gen_diagrams.py")
diagrams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagrams)


@pytest.mark.parametrize("field,value", [("device", ""), ("ms", float("nan")), ("direct", 68)])
def test_diagram_input_when_invalid_then_rejected(tmp_path, field, value):
    row = json.loads((ROOT / "src_docs/data/classifiers.json").read_text())[0]
    row[field] = value
    path = tmp_path / "runs.json"
    path.write_text(json.dumps([row]))
    with pytest.raises(ValueError):
        diagrams.read_runs(path)


def test_diagram_when_generated_then_offline_assets_and_safe_payload_are_embedded(tmp_path):
    row = json.loads((ROOT / "src_docs/data/classifiers.json").read_text())[0]
    row["method"] = "</script><script>alert(1)</script>"
    path, out = tmp_path / "runs.json", tmp_path / "explorer.html"
    path.write_text(json.dumps([row]))
    diagrams.generate(path, out)
    text = out.read_text()
    assert "plotly.js (basic - minified) v3.1.0" in text, "Offline report must embed Plotly"
    assert "\\u003c/script>" in text, "JSON must not terminate the script tag"
    assert "<script>alert(1)</script>" not in text, "Method IDs are data, never script"
    assert 'name="benchSearch"' in diagrams.widget([row]), "Explorer search needs its own field name"
    assert 'name="search"' not in diagrams.widget([row]), "Native site search owns this reserved name"


def test_frontier_and_filters_when_node_available_then_browser_math_passes():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is needed to verify the browser math")
    subprocess.run([node, "--test", "tests/benchmark.test.cjs"], cwd=ROOT, check=True, capture_output=True)


def test_book_assets_when_versioned_then_urls_match_content_and_are_idempotent(tmp_path):
    config = tmp_path / "properdocs.yml"
    config.write_text((ROOT / "src_docs/properdocs.yml").read_text())
    for asset in ("css/benchmark.css", "js/benchmark-math.js", "js/benchmark.js"):
        target = tmp_path / asset
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((diagrams.MD / asset).read_bytes())
    diagrams.version_assets(config, tmp_path)
    first = config.read_text()
    for asset in ("css/benchmark.css", "js/benchmark-math.js", "js/benchmark.js"):
        digest = hashlib.sha256((diagrams.MD / asset).read_bytes()).hexdigest()[:12]
        stem, suffix = asset.rsplit(".", 1)
        versioned = f"{stem}.{digest}.{suffix}"
        assert f"  - {versioned}" in first, "Every benchmark asset needs its matching content version"
        assert (tmp_path / versioned).read_bytes() == (tmp_path / asset).read_bytes()
    diagrams.version_assets(config, tmp_path)
    assert config.read_text() == first, "Repeated builds must retain identical asset URLs"
