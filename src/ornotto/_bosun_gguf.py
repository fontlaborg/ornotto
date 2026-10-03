# this_file: src/ornotto/_bosun_gguf.py
"""Bosun stable-slot GGUF inference, using the upstream public prompt compiler."""

from __future__ import annotations

from ._bosun_prompt import render_decision_prompt
from ._protocol import as_question
from ._transformers_decision import answer


class Bosun:
    def __init__(self, path: str, device: str):
        from llama_cpp import Llama

        self.model = Llama(
            model_path=path,
            n_gpu_layers=-1 if device == "gpu" else 0,
            n_ctx=4096,
            n_batch=512,
            logits_all=True,
            verbose=False,
        )
        self.labels = [f"<|decision_{i:03d}|>" for i in range(256)]
        encoded = [self.model.tokenize(token.encode(), add_bos=False, special=True) for token in self.labels]
        if any(ids != [151669 + i] for i, ids in enumerate(encoded)):
            self.model.close()
            raise ValueError("GGUF does not carry the Bosun v3.1 stable decision vocabulary")
        self.ids = [ids[0] for ids in encoded]

    def predict(self, state, questions):
        import numpy as np

        answers, count = {}, 0
        for key, raw in questions.items():
            question = as_question(raw)
            criteria = dict(question.options)
            if question.kind == "noul":
                criteria = {"true": criteria.get("true") or "yes", "false": criteria.get("false") or "no"}
            candidates = [
                {
                    "id": name,
                    "label": description if question.kind == "score" else name,
                    "description": "" if question.kind == "score" else description,
                }
                for name, description in criteria.items()
            ]
            content, order, _ = render_decision_prompt(
                state=state,
                instructions=question.instructions,
                candidates=candidates,
                decision_type=question.kind,
                decision_tokens=self.labels,
                seed=0,
                row_id="0",
            )
            prompt = (
                "<|im_start|>system\nChoose exactly one supplied decision token. Return only that token. "
                "Do not explain the answer.<|im_end|>\n<|im_start|>user\n"
                + content
                + "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            )
            tokens = self.model.tokenize(prompt.encode(), add_bos=False, special=True)
            if len(tokens) > self.model.n_ctx():
                raise ValueError("STATE_TRUNCATED: Bosun prompt exceeds 4096 tokens")
            self.model.reset()
            self.model.eval(tokens)
            scores = np.asarray(self.model.scores[-1, self.ids[: len(criteria)]], dtype=np.float64)
            if not np.isfinite(scores).all():
                raise FloatingPointError("Bosun returned nonfinite decision logits")
            probabilities = np.exp(scores - scores.max())
            probabilities /= probabilities.sum()
            aligned = np.empty_like(probabilities)
            aligned[order] = probabilities
            answers[key] = answer(
                question.kind, list(criteria), [v or k for k, v in criteria.items()], aligned.tolist()
            )
            count += len(tokens)
        return {"answers": answers, "usage": {"input_tokens": count, "output_tokens": 0}}

    def close(self):
        self.model.close()
