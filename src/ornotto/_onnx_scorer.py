# this_file: src/ornotto/_onnx_scorer.py
"""The published Qwen scalar ONNX contract: right padding, T=1.75, no truncation."""

from __future__ import annotations

from pathlib import Path

from ._protocol import as_question
from ._transformers_decision import answer, options, state_text


class OnnxScorer:
    def __init__(self, path: str, device: str):
        import onnxruntime as ort
        from transformers import AutoTokenizer

        if device != "cpu":
            raise ValueError("ONNX scalar adapter uses CPUExecutionProvider; pass gpu=False")
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.session = ort.InferenceSession(
            str(Path(path) / "onnx" / "model_q4.onnx"), providers=["CPUExecutionProvider"]
        )

    def sequences(self, state, question, descriptions):
        head = self.tokenizer.encode("State:\n" + state_text(state), add_special_tokens=False)
        rows = []
        for description in descriptions:
            tail = self.tokenizer.encode(
                f"\n\nQuestion:\n{question.instructions}\n\nOption:\n{description}", add_special_tokens=False
            )
            if len(head) + len(tail) > 384:
                raise ValueError("STATE_TRUNCATED: scalar scorer requires at most 384 tokens per option")
            rows.append(head + tail)
        return rows

    def predict(self, state, questions):
        import numpy as np

        answers, count = {}, 0
        for key, raw in questions.items():
            question = as_question(raw)
            keys, descriptions = options(question)
            rows = self.sequences(state, question, descriptions)
            # One row at a time bounds transient attention allocations on CPU.
            logits = []
            for row in rows:
                inputs = {
                    "input_ids": np.asarray([row], dtype=np.int64),
                    "attention_mask": np.ones((1, len(row)), dtype=np.int64),
                }
                scalar = self.session.run(["logits"], inputs)[0]
                if scalar.shape != (1, 1):
                    raise ValueError(f"Unexpected scalar scorer output shape: {scalar.shape}")
                logits.append(float(scalar[0, 0]))
            values = np.asarray(logits) / 1.75
            probabilities = np.exp(values - values.max())
            probabilities /= probabilities.sum()
            answers[key] = answer(question.kind, keys, descriptions, probabilities.tolist())
            count += sum(map(len, rows))
        return {"answers": answers, "usage": {"input_tokens": count, "output_tokens": 0}}
