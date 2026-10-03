# this_file: src/ornotto/_clef_gguf.py
"""Attach Clef's trained head to backbone-only published GGUF quantizations.

Tensor names, scales and prompt follow llama.cpp conversion/clef.py at
99b95488c (MIT; see licenses/clef-NOTICE). Backbone bytes stay quantized.
The original Hub artifact is retained; an atomic derived GGUF is cached beside it.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

FORMAT = json.loads((Path(__file__).parent / "data/clef-format.json").read_text())


def head_tensors(path: Path, routing: int):
    """Official head layout: split attention QKV and offset decoder blocks."""
    import numpy as np
    from safetensors.torch import load_file

    tensors = {key: value.float().numpy() for key, value in load_file(str(path)).items()}
    scales = []
    for key in ("prior_logit_scale", "joint_logit_scale", "residual_gate"):
        value = float(tensors.pop(key))
        scales.append(
            1 / (1 + math.exp(-value)) if key == "residual_gate" else math.exp(min(value, math.log(100)))
        )
    yield "decision.scales", np.asarray(scales, dtype=np.float32)
    for key, tensor in tensors.items():
        parts = key.split(".")
        if parts[0] == "layers":
            parts[1] = str(int(parts[1]) + routing)
        key = ".".join(parts)
        suffix = key.rsplit(".", 1)[1]
        if suffix.startswith("in_proj_"):
            prefix = key.rsplit(".", 1)[0]
            for qkv, value in zip("qkv", np.split(tensor, 3, axis=0), strict=True):
                yield (
                    FORMAT["mapping"][prefix + "." + qkv] + "." + suffix.removeprefix("in_proj_"),
                    value.astype(np.float32),
                )
        else:
            stem, suffix = key.rsplit(".", 1)
            yield FORMAT["mapping"][stem] + "." + suffix, tensor.astype(np.float32)


def write(source: Path, checkpoint: Path, output: Path):
    """Stream unchanged quantized backbone tensors and the FP32 native head."""
    from gguf import GGUFReader, GGUFWriter

    reader = GGUFReader(str(source))
    arch = reader.fields["general.architecture"].contents()
    if arch not in ("qwen35", "qwen35moe"):
        raise ValueError(f"Unsupported Clef backbone architecture: {arch}")
    cfg = json.loads((checkpoint / "joint_head_config.json").read_text())
    writer = GGUFWriter(str(output), "clef")
    for key, field in reader.fields.items():
        if (
            key.startswith("GGUF.")
            or key == "general.architecture"
            or key.startswith("tokenizer.chat_template")
        ):
            continue
        target = "clef." + key[len(arch) + 1 :] if key.startswith(arch + ".") else key
        writer.add_key_value(
            target, field.contents(), field.types[0], field.types[1] if len(field.types) > 1 else None
        )
    writer.add_string("clef.decision.type", "clef")
    writer.add_uint32("clef.decision.routing_block_count", cfg["routing_layers"])
    writer.add_uint32("clef.decision.block_count", cfg["layers"])
    writer.add_uint32("clef.decision.head_count", cfg["heads"])
    writer.add_float32("clef.attention.layer_norm_epsilon", 1e-5)
    writer.add_string("tokenizer.chat_template.systemone", FORMAT["template"])
    writer.add_array("tokenizer.chat_templates", ["systemone"])
    head = list(head_tensors(checkpoint / "joint_head.safetensors", cfg["routing_layers"]))
    for tensor in reader.tensors:
        writer.add_tensor_info(
            tensor.name,
            tensor.data.shape,
            tensor.data.dtype,
            tensor.data.nbytes,
            raw_dtype=tensor.tensor_type,
        )
    for name, value in head:
        writer.add_tensor_info(name, value.shape, value.dtype, value.nbytes)
    try:
        writer.write_header_to_file()
        writer.write_kv_data_to_file()
        writer.write_ti_data_to_file()
        for tensor in reader.tensors:
            writer.write_tensor_data(tensor.data)
        for _, value in head:
            writer.write_tensor_data(value)
    finally:
        writer.close()


def prepare(source: Path, checkpoint: Path) -> Path:
    """Make a native decision GGUF once, without overwriting downloaded artifacts."""
    from filelock import FileLock
    from gguf import GGUFReader

    if GGUFReader(str(source)).fields["general.architecture"].contents() == "clef":
        return source
    # The immutable Hub snapshot path fixes backbone and head revisions.
    digest = hashlib.sha256(json.dumps(FORMAT, sort_keys=True).encode())
    with (checkpoint / "joint_head.safetensors").open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    target = source.parent / (source.stem + "-clef-native-" + digest.hexdigest()[:16] + ".gguf")
    with FileLock(str(target) + ".lock"):
        if target.is_file():
            return target
        required = source.stat().st_size + 2 * (checkpoint / "joint_head.safetensors").stat().st_size
        if shutil.disk_usage(source.parent).free < required + 1024**3:
            raise OSError("Insufficient disk space for the native Clef GGUF; original is retained")
        fd, temporary = tempfile.mkstemp(prefix=target.name, suffix=".partial", dir=target.parent)
        os.close(fd)
        try:
            write(source, checkpoint, Path(temporary))
            check = GGUFReader(temporary)
            if check.fields["clef.decision.type"].contents() != "clef":
                raise ValueError("Converted GGUF lacks its native decision head")
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return target
