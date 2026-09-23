# this_file: src/ornotto/_models.py
"""Known models and how to fetch them.

A model is a GGUF file plus, for dohnuts, the metadata JSON that selects its profile and temperature (and,
for kev and Dohnuts, a scorer head). Registered models download from Hugging Face on first use into the
normal Hugging Face cache. Anything else can be given as a local path or as `hf:owner/repo/file.gguf`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Engine = Literal["dohnuts", "pcd"]
Family = Literal["dedicated", "fine-tuned", "vanilla"]


@dataclass(frozen=True)
class ModelSpec:
    """A registered model."""

    name: str
    repo: str
    file: str
    engines: tuple[Engine, ...]
    """Engines that can run it; the first is the default."""
    family: Family
    """dedicated: trained for System One decisions (read out at its answer slot);
    fine-tuned: a chat model tuned for this kind of task; vanilla: a stock chat model."""
    license: str
    size_gb: float
    metadata: str | None = None
    head: str | None = None
    note: str = ""


MODELS: dict[str, ModelSpec] = {
    m.name: m
    for m in (
        ModelSpec(
            "decider-0.8b",
            "DreamBlooms/decider-0.8b-GGUF",
            "decider-0.8b-q8_0.gguf",
            ("dohnuts", "pcd"),
            "dedicated",
            "apache-2.0",
            0.81,
            metadata="decider.json",
            note="Mapika/decider-0.8b, Q8_0. The default: fast, calibrated, 62/67 on the FontLab router set.",
        ),
        ModelSpec(
            "decider-2b",
            "DreamBlooms/decider-2b-GGUF",
            "decider-2b-q8_0.gguf",
            ("dohnuts", "pcd"),
            "dedicated",
            "apache-2.0",
            2.0,
            metadata="decider.json",
            note="decider-2b with calibration-aware RL (T 1.3), Q8_0.",
        ),
        ModelSpec(
            "kev-0.8b",
            "DreamBlooms/kev-0.8b-GGUF",
            "kev-0.8b-q8_0.gguf",
            ("dohnuts",),
            "dedicated",
            "apache-2.0",
            0.81,
            metadata="kev.json",
            head="kev-head.f32",
            note="jaredpalmer/kev-0.8b: a pointer head over option markers, Q8_0.",
        ),
        ModelSpec(
            "dohnuts-0.8b",
            "DreamBlooms/Dohnuts-0.1.0-0.8B-GGUF",
            "Dohnuts-0.1.0-0.8B-Q8_0.gguf",
            ("dohnuts",),
            "dedicated",
            "cc-by-nc-sa-4.0",
            0.81,
            metadata="dohnuts.json",
            head="head.f32",
            note="PsiACE/Dohnuts 0.1.0. Non-commercial licence.",
        ),
        ModelSpec(
            "qwen3.5-0.8b",
            "ggml-org/Qwen3.5-0.8B-GGUF",
            "Qwen3.5-0.8B-Q8_0.gguf",
            ("pcd",),
            "vanilla",
            "apache-2.0",
            0.83,
            note="Stock Qwen3.5-0.8B, pcdServer's default model.",
        ),
        ModelSpec(
            "qwen3.5-2b",
            "bartowski/Qwen_Qwen3.5-2B-GGUF",
            "Qwen_Qwen3.5-2B-Q4_K_M.gguf",
            ("pcd",),
            "vanilla",
            "apache-2.0",
            1.4,
        ),
        ModelSpec(
            "qwen3.5-4b",
            "bartowski/Qwen_Qwen3.5-4B-GGUF",
            "Qwen_Qwen3.5-4B-Q4_K_M.gguf",
            ("pcd",),
            "vanilla",
            "apache-2.0",
            3.0,
        ),
        ModelSpec(
            "qwen3.5-4b-hmm",
            "n4ze3m/Qwen3.5-4B-Hmm",
            "Qwen3.5-4B-Hmm-Q4_K_M.gguf",
            ("pcd",),
            "fine-tuned",
            "apache-2.0",
            2.7,
            note="The most accurate local model on the FontLab router set (64/67).",
        ),
    )
}

DEFAULT_MODEL = "decider-0.8b"


@dataclass(frozen=True)
class ResolvedModel:
    """Files on disk for one model."""

    name: str
    gguf: Path
    engines: tuple[Engine, ...]
    metadata: Path | None = None
    head: Path | None = None


def _download(repo: str, file: str) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download(repo, file))


def resolve(
    model: str, *, metadata: str | Path | None = None, head: str | Path | None = None
) -> ResolvedModel:
    """Turn a registered name, a local .gguf path or `hf:owner/repo/file.gguf` into files on disk.

    Registered models download on first use. For an unregistered model on dohnuts, pass `metadata` (the
    profile JSON) and, for kev or Dohnuts, `head`.
    """
    if spec := MODELS.get(model):
        return ResolvedModel(
            spec.name,
            _download(spec.repo, spec.file),
            spec.engines,
            _download(spec.repo, spec.metadata) if spec.metadata else None,
            _download(spec.repo, spec.head) if spec.head else None,
        )
    if model.startswith("hf:"):
        owner, repo, file = model[3:].split("/", 2)
        gguf = _download(f"{owner}/{repo}", file)
    else:
        gguf = Path(model).expanduser()
        if not gguf.is_file():
            known = ", ".join(MODELS)
            raise FileNotFoundError(f"{model!r} is neither a registered model ({known}) nor a file")
    engines: tuple[Engine, ...] = ("dohnuts", "pcd") if metadata else ("pcd",)
    return ResolvedModel(
        gguf.stem,
        gguf,
        engines,
        Path(metadata).expanduser() if metadata else None,
        Path(head).expanduser() if head else None,
    )
