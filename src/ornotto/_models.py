# this_file: src/ornotto/_models.py
"""Known models and how to fetch them.

A model is a GGUF file plus, for dohnuts, the metadata JSON that selects its profile and temperature (and,
for kev and Dohnuts, a scorer head). Registered models download from Hugging Face on first use into the
normal Hugging Face cache. Anything else can be given as a local path or as `hf:owner/repo/file.gguf`.

An ollaya model is a tag in ollaya's own registry (`kev:0.8b`) instead of a file: ollaya pulls it into its
store (`OLLAYA_MODELS`, default `~/.ollaya/models`) the first time a managed server needs it. Any tag can
be given as `ollaya:<tag>`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Engine = Literal[
    "dohnuts",
    "pcd",
    "ollaya",
    "openrouter",
    "laya-mlx",
    "xdecision",
    "llama",
    "raz-nli",
    "transformers-nli",
    "transformers-slot",
    "systemone-lite",
    "system-one-mlx",
    "onnx-scorer",
    "coreai",
    "bosun-gguf",
    "clef-mlx",
    "clm-gguf",
    "clm-mlx",
]
PYTHON_ENGINES = (
    "laya-mlx",
    "xdecision",
    "raz-nli",
    "transformers-nli",
    "transformers-slot",
    "systemone-lite",
    "system-one-mlx",
    "onnx-scorer",
    "bosun-gguf",
    "clef-mlx",
    "clm-gguf",
    "clm-mlx",
)
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
    tag: str | None = None
    """ollaya or external CoreAI catalog tag, replacing downloaded files."""
    bundled_metadata: str | None = None
    """Profile JSON shipped with the package when the weight repository has none."""
    revision: str | None = None
    snapshot: tuple[str, ...] = ()
    base_repo: str | None = None
    base_revision: str | None = None
    unavailable: str | None = None
    decision_repo: str | None = None
    decision_revision: str | None = None
    head_repo: str | None = None
    head_revision: str | None = None


def _ollaya(name: str, tag: str, size_gb: float, note: str) -> ModelSpec:
    """A model that ollaya pulls from its own registry. Every one of them is Apache-2.0."""
    return ModelSpec(
        name,
        f"ollaya-dev/{tag.split(':')[0]}",
        "",
        ("ollaya",),
        "dedicated",
        "apache-2.0",
        size_gb,
        note=note,
        tag=tag,
    )


MODELS: dict[str, ModelSpec] = {
    m.name: m
    for m in (
        ModelSpec(
            "laya-multilingual-mlx",
            "aac6fef/laya-multilingual-mlx",
            "",
            ("laya-mlx",),
            "dedicated",
            "apache-2.0",
            0.64,
            note="Native MLX FP16 encoder; optional laya-mlx runtime, Apple silicon, Python 3.11+.",
        ),
        ModelSpec(
            "xdecision-f16",
            "mccoysc/xDecision",
            "models/gguf/xDecision-F16.gguf",
            ("xdecision",),
            "dedicated",
            "apache-2.0",
            0.7041,
            note="Custom xdecision GGUF; native MLX or PyTorch CPU. Install upstream runtime separately.",
        ),
        ModelSpec(
            "xdecision-q8",
            "mccoysc/xDecision",
            "models/gguf/xDecision-Q8_0.gguf",
            ("xdecision",),
            "dedicated",
            "apache-2.0",
            0.40255,
            note="Q8_0 is dequantized to dense weights at load; requires the upstream xdecision runtime.",
        ),
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
            "tev1-0.8b",
            "DreamBlooms/Tev1-0.8B-experimental-GGUF",
            "tev1-Q8_0.gguf",
            ("dohnuts",),
            "dedicated",
            "other",
            0.81,
            metadata="tev1.json",
            note="Together Tev1 experimental, Q8_0 label logits. Release licence is unresolved; "
            "temperature 1.0 does not establish calibration.",
        ),
        ModelSpec(
            "jet-4b",
            "DreamBlooms/jet-GGUF",
            "jet-4b-Q8_0.gguf",
            ("dohnuts",),
            "dedicated",
            "apache-2.0",
            4.48,
            metadata="jet.json",
            note="Jet v6.2 Q8_0, per-question-type temperatures inherited from v6.1.",
        ),
        ModelSpec(
            "this-that-1.2",
            "mradermacher/this-that-model-1.2-GGUF",
            "this-that-model-1.2.Q4_K_M.gguf",
            ("dohnuts",),
            "dedicated",
            "mit",
            1.27,
            bundled_metadata="thisthat.json",
            note="ThisThat 1.2 Q4_K_M; probability temperature 1.0.",
        ),
        ModelSpec(
            "jpt-4b",
            "prithivMLmods/jpt-4b-GGUF",
            "jpt-4b.Q4_K_M.gguf",
            ("dohnuts", "pcd"),
            "dedicated",
            "cc-by-nc-4.0",
            2.71,
            bundled_metadata="jpt-4b.json",
            note="JPT 4B Q4_K_M, author temperature 1.036 on dohnuts. Non-commercial weights.",
        ),
        ModelSpec(
            "jpt-9b",
            "prithivMLmods/jpt-9b-GGUF",
            "jpt-9b.Q4_K_M.gguf",
            ("dohnuts", "pcd"),
            "dedicated",
            "cc-by-nc-4.0",
            5.63,
            bundled_metadata="jpt-9b.json",
            note="JPT 9B Q4_K_M, author temperature 1.087 on dohnuts. Non-commercial weights.",
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
            "rune-26b-a4b",
            "mradermacher/rune-26b-a4b-GGUF",
            "rune-26b-a4b.Q3_K_M.gguf",
            ("pcd",),
            "dedicated",
            "apache-2.0",
            13.29,
            note="mradermacher Rune Q3_K_M. Requires pcdServer's Jinja fallback for Gemma 4.",
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
        ModelSpec(
            "jevk5-4b",
            "alibiserikbay/JevK5-GGUF",
            "jevk5-4b-v0.3-Q4_K_M.gguf",
            ("pcd",),
            "fine-tuned",
            "apache-2.0",
            2.7,
            note="JevK5 v0.3, a Qwen3.5-4B decision fine-tune, Q4_K_M. 62/67 with its own letter readout, "
            "61/67 on pcdServer.",
        ),
        ModelSpec(
            "openjev-35b-a3b",
            "apus-ailab/APUS-OpenJev-v1-35B-A3B-GGUF",
            "APUS-OpenJev-v1-35B-A3B-Q4_K_M.gguf",
            ("pcd",),
            "fine-tuned",
            "apache-2.0",
            21.2,
            note="APUS-OpenJev v1, a Qwen3.5-35B-A3B decision fine-tune, Q4_K_M. "
            "Needs the machine to itself.",
        ),
        _ollaya("ollaya-kev-0.8b", "kev:0.8b", 1.8, "Kev 0.8B (Jared Palmer): LoRA and pointer head, ONNX."),
        _ollaya("ollaya-decider-0.8b", "decider:0.8b", 1.5, "decider-0.8b (Mapika), slot readout, ONNX."),
        _ollaya("ollaya-laya-en", "laya:en", 0.9, "Laya (Convai Innovations), ModernBERT-large, 512 tokens."),
        _ollaya("ollaya-laya-multilingual", "laya:multilingual", 0.7, "Laya multilingual, mmBERT-base."),
        _ollaya("ollaya-nli-modernbert-large", "nli:modernbert-large", 0.8, "Zero-shot NLI (Moritz Laurer)."),
        _ollaya("ollaya-gliclass-large", "gliclass:large", 1.8, "GLiClass instruct large (Knowledgator)."),
        _ollaya("ollaya-von-1.1", "von:1.1", 1.6, "Von 1.1 (Victor Hugo Panisa), ModernBERT-large."),
        _ollaya("ollaya-decision-eos", "decision:eos", 1.5, "Decision 1.0 Eos (vLLM Semantic Router)."),
        _ollaya("ollaya-winnow-12b", "winnow:12b", 12.7, "Winnow 12B (EldanRing), Gemma 4, Q8_0 GGUF."),
        _ollaya("ollaya-clm-8b", "clm:8b", 16.5, "CLM v0.1 8B (Contrastive-LM), Qwen3-8B encoder."),
    )
}

DEFAULT_MODEL = "decider-0.8b"

for entry in json.loads((Path(__file__).parent / "data" / "systemone-models.json").read_text())["models"]:
    entry["engines"] = tuple(entry["engines"])
    entry["snapshot"] = tuple(entry.get("snapshot", ()))
    MODELS[entry["name"]] = ModelSpec(**entry)


@dataclass(frozen=True)
class ResolvedModel:
    """A GGUF file or native encoder checkpoint directory on disk, or an ollaya tag."""

    name: str
    gguf: Path | None
    """None for an ollaya model, which is a `tag` instead."""
    engines: tuple[Engine, ...]
    metadata: Path | None = None
    head: Path | None = None
    tag: str | None = None
    adapter: Path | None = None


def _download(repo: str, file: str) -> Path:
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download(repo, file))


def resolve(
    model: str,
    *,
    metadata: str | Path | None = None,
    head: str | Path | None = None,
    engine: Engine | None = None,
) -> ResolvedModel:
    """Turn a registered name, a local .gguf path or `hf:owner/repo/file.gguf` into files on disk.

    Registered models download on first use. For an unregistered model on dohnuts, pass `metadata` (the
    profile JSON) and, for kev or Dohnuts, `head`. `ollaya:<tag>` and registered ollaya models resolve to a
    tag with no file; the ollaya server pulls it.
    """
    if (
        engine in (*PYTHON_ENGINES, "llama", "coreai")
        or model in MODELS
        and MODELS[model].engines
        and MODELS[model].engines[0] in (*PYTHON_ENGINES, "llama", "coreai")
    ) and (metadata is not None or head is not None):
        raise ValueError(
            "Native encoders carry their own profile/head; metadata and head are dohnuts settings"
        )
    if model.startswith("ollaya:"):
        return ResolvedModel(model, None, ("ollaya",), tag=model.removeprefix("ollaya:"))
    if spec := MODELS.get(model):
        if spec.unavailable:
            raise RuntimeError(f"{spec.name} unavailable: {spec.unavailable}")
        if engine is not None and engine not in spec.engines:
            raise ValueError(f"{spec.name} runs on {' or '.join(spec.engines)}, not {engine}")
        if spec.tag:
            return ResolvedModel(spec.name, None, spec.engines, tag=spec.tag)
        native_head = None
        if spec.head_repo:
            from huggingface_hub import hf_hub_download

            native_head = Path(hf_hub_download(spec.head_repo, spec.head, revision=spec.head_revision))
        if spec.snapshot:
            from huggingface_hub import snapshot_download

            options = {}
            if spec.engines == ("onnx-scorer",):
                from huggingface_hub.constants import HF_HUB_CACHE

                # External ONNX data must be beside the graph, not cache blob symlinks.
                options["local_dir"] = str(Path(HF_HUB_CACHE) / "ornotto-local" / spec.name / spec.revision)
            checkpoint = Path(
                snapshot_download(
                    repo_id=spec.repo,
                    revision=spec.revision,
                    allow_patterns=list(spec.snapshot),
                    max_workers=2,
                    **options,
                )
            )
            if spec.base_repo:
                base = Path(
                    snapshot_download(
                        repo_id=spec.base_repo,
                        revision=spec.base_revision,
                        allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja"],
                        max_workers=2,
                    )
                )
                return ResolvedModel(spec.name, base, spec.engines, adapter=checkpoint)
            return ResolvedModel(spec.name, checkpoint, spec.engines, head=native_head)
        if spec.engines == ("laya-mlx",):
            from huggingface_hub import snapshot_download

            snapshot = snapshot_download(
                repo_id=spec.repo, allow_patterns=["*.json", "*.safetensors", "tokenizer/*"]
            )
            return ResolvedModel(spec.name, Path(snapshot), spec.engines)
        if spec.revision:
            from huggingface_hub import hf_hub_download

            gguf = Path(hf_hub_download(spec.repo, spec.file, revision=spec.revision))
        else:
            gguf = _download(spec.repo, spec.file)
        if spec.decision_repo:
            from huggingface_hub import snapshot_download

            from ._clef_gguf import prepare

            checkpoint = Path(
                snapshot_download(
                    repo_id=spec.decision_repo,
                    revision=spec.decision_revision,
                    allow_patterns=["joint_head.safetensors", "joint_head_config.json"],
                    max_workers=2,
                )
            )
            gguf = prepare(gguf, checkpoint)
        profile = (
            Path(metadata).expanduser()
            if metadata
            else (
                Path(__file__).parent / "data" / spec.bundled_metadata
                if spec.bundled_metadata
                else _download(spec.repo, spec.metadata)
                if spec.metadata
                else None
            )
        )
        return ResolvedModel(
            spec.name,
            gguf,
            spec.engines,
            profile,
            Path(head).expanduser()
            if head
            else native_head or (_download(spec.repo, spec.head) if spec.head else None),
        )
    if model.startswith("hf:"):
        owner, repo, file = model[3:].split("/", 2)
        gguf = _download(f"{owner}/{repo}", file)
    else:
        gguf = Path(model).expanduser()
        if not (gguf.is_file() or engine in PYTHON_ENGINES and gguf.is_dir()):
            known = ", ".join(MODELS)
            raise FileNotFoundError(f"{model!r} is neither a registered model ({known}) nor a file")
    engines: tuple[Engine, ...] = (
        (engine,) if engine in (*PYTHON_ENGINES, "llama") else ("dohnuts", "pcd") if metadata else ("pcd",)
    )
    return ResolvedModel(
        gguf.stem,
        gguf,
        engines,
        Path(metadata).expanduser() if metadata else None,
        Path(head).expanduser() if head else None,
    )
