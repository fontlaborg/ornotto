# this_file: src/ornotto/_clm_decision.py
"""Native CLM reference Engine over local last-token GGUF or MLX embeddings.

The separately installed contrastive-lm 0.1.0 package supplies the exact
state/action rendering, trained projection heads and probability recipe.
"""

from __future__ import annotations

from pathlib import Path

from ._clef_mlx import module_at, native_questions

CONTEXT = 2048


class GGUFEmbedder:
    """Reference last-token pooling, L2 normalization and full-input checks."""

    def __init__(self, path: str, device: str):
        from llama_cpp import LLAMA_POOLING_TYPE_LAST, Llama

        self.model = Llama(
            model_path=path,
            embedding=True,
            pooling_type=LLAMA_POOLING_TYPE_LAST,
            n_ctx=CONTEXT,
            n_batch=CONTEXT,
            n_ubatch=CONTEXT,
            n_gpu_layers=-1 if device == "gpu" else 0,
            verbose=False,
        )

    def embed(self, texts):
        import numpy as np

        if any(len(self.model.tokenize(text.encode("utf-8"))) > CONTEXT for text in texts):
            raise ValueError(f"STATE_TRUNCATED: CLM input exceeds {CONTEXT} tokens")
        values, tokens = self.model.embed(texts, normalize=True, truncate=False, return_count=True)
        return np.asarray(values, dtype=np.float32), tokens

    def close(self):
        self.model.close()


class MLXEmbedder:
    """Pinned author encoder; reject its otherwise silent first-2048 slicing."""

    def __init__(self, path: str):
        module = module_at(Path(path) / "clm_mlx" / "__init__.py", "_ornotto_native_clm", package=True)
        self.encoder = module.Encoder(path, max_tokens=CONTEXT, batch_tokens=CONTEXT)
        self.limit = CONTEXT

    def embed(self, texts):
        import numpy as np

        if any(len(self.encoder.tok(text)["input_ids"]) > self.limit for text in texts):
            raise ValueError(f"STATE_TRUNCATED: CLM input exceeds {self.limit} tokens")
        values, tokens = self.encoder.embed(texts)
        return np.asarray(values, dtype=np.float32), tokens


class CLM:
    """The official contrastive Engine and its pinned reference checkpoint."""

    def __init__(self, path: str, mode: str, device: str, head: str | None):
        import sys

        from clm import Engine

        if not head or not Path(head).is_file():
            raise ValueError("CLM requires its trained projection-head checkpoint")
        if mode == "clm-mlx" and (sys.platform != "darwin" or device != "gpu"):
            raise ValueError("CLM MLX requires Apple silicon GPU; use CLM GGUF for CPU")
        self.embedder = MLXEmbedder(path) if mode == "clm-mlx" else GGUFEmbedder(path, device)
        # The small FP32 reference heads run on CPU; encoder placement remains
        # explicit. No action-cache allocation or second resident model.
        self.engine = Engine(embedder=self.embedder, checkpoint=head, device="cpu", action_cache=0)

    def predict(self, state, questions):
        return self.engine.answer(state, native_questions(questions))

    def close(self):
        if hasattr(self.embedder, "close"):
            self.embedder.close()
