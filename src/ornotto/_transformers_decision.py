# this_file: src/ornotto/_transformers_decision.py
"""Documented Raz NLI and Gemma letter readouts, with full input or an error."""

from __future__ import annotations

import json
from typing import Any

from ._protocol import as_question


def state_text(state: Any) -> str:
    return state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)


def answer(kind: str, keys: list[str], descriptions: list[str], probabilities: list[float]) -> dict:
    """Encode distributions in the shared protocol; score uses its expected level."""
    distribution = dict(zip(keys, probabilities, strict=True))
    if kind == "noul":
        return {"type": kind, "noul": distribution["true"], "confidence": max(probabilities)}
    result = {"type": kind, "probabilities": distribution, "confidence": max(probabilities)}
    if kind == "choice":
        result["choice"] = max(distribution, key=distribution.__getitem__)
    else:
        result.update(
            score=sum(i * p for i, p in enumerate(probabilities)),
            legend=dict(zip(keys, descriptions, strict=True)),
        )
    return result


def options(question) -> tuple[list[str], list[str]]:
    if question.kind == "noul":
        return ["false", "true"], [
            question.options.get("false") or "no",
            question.options.get("true") or "yes",
        ]
    return list(question.options), [value or key for key, value in question.options.items()]


class TorchDecision:
    """Load published standard Transformers checkpoints without remote Python code."""

    def __init__(self, path: str, mode: str, device: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer

        self.torch, self.mode = torch, mode
        target = "cpu"
        if device == "gpu":
            target = (
                "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else ""
            )
            if not target:
                raise RuntimeError("No supported Torch GPU is available; use gpu=False")
        self.device = target
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        loader = AutoModelForSequenceClassification if mode.endswith("nli") else AutoModelForCausalLM
        self.model = (
            loader.from_pretrained(path, local_files_only=True, dtype=torch.float32).to(target).eval()
        )
        self.limit = min(512 if mode.endswith("nli") else 4096, self.model.config.max_position_embeddings)
        if mode.endswith("nli"):
            labels = {value.lower(): int(key) for key, value in self.model.config.id2label.items()}
            self.entail = labels["entailment"]
            self.contra = labels.get("contradiction", labels.get("not_entailment"))
            if self.contra is None:
                raise ValueError("NLI model must declare contradiction or not_entailment")

    def tokens(self, first, second=None):
        batch = self.tokenizer(first, second, padding=True, truncation=False, return_tensors="pt")
        if batch["input_ids"].shape[-1] > self.limit:
            raise ValueError(f"STATE_TRUNCATED: prompt exceeds {self.limit} tokens; shorten it")
        return {key: value.to(self.device) for key, value in batch.items()}

    def nli(self, state, question, descriptions):
        if question.kind == "noul":
            hypotheses = [question.instructions]
        elif question.kind == "choice":
            hypotheses = [
                f"This example is {description}."
                if self.mode == "transformers-nli"
                else f"This text is about {description}."
                for description in descriptions
            ]
        else:
            hypotheses = descriptions
        batch = self.tokens([state] * len(hypotheses), hypotheses)
        with self.torch.inference_mode():
            logits = self.model(**batch).logits
            probs = self.torch.softmax(logits.float(), dim=-1)
        if self.mode == "transformers-nli":
            if question.kind == "noul":
                p = float(self.torch.softmax(logits[0, [self.contra, self.entail]].float(), dim=-1)[1])
                result = [1 - p, p]
            else:
                result = self.torch.softmax(logits[:, self.entail].float(), dim=0).tolist()
            return result, int(batch["attention_mask"].sum())
        entail, contra = probs[:, self.entail], probs[:, self.contra]
        if question.kind != "choice":
            sums = entail + contra
            values = self.torch.where(sums < 1e-6, 0.5, entail / sums)
        else:
            values = entail
        if question.kind == "noul":
            p = float(values[0])
            result = [1 - p, p]
        else:
            total = float(values.sum())
            if total <= 0:
                raise FloatingPointError("NLI options have no entailment mass")
            result = (values / total).tolist()
        return result, int(batch["attention_mask"].sum())

    def letters(self, state, question, keys, descriptions):
        if len(keys) > 26:
            raise ValueError("Gemma 270M supports at most 26 options")
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(keys)]
        body = "\n".join(
            f"{letter}. {key} - {description}"
            for letter, key, description in zip(letters, keys, descriptions, strict=True)
        )
        prompt = (
            f"<state>\n{state}\n</state>\n\nQuestion: {question.instructions}\n"
            f"Options:\n{body}\n\nAnswer with one letter.\nAnswer:"
        )
        text = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
        )
        ids = [self.tokenizer.encode(letter, add_special_tokens=False) for letter in letters]
        if any(len(tokens) != 1 for tokens in ids) or len({tokens[0] for tokens in ids}) != len(ids):
            raise ValueError("Letter readout requires distinct single-token labels")
        batch = self.tokenizer(text, add_special_tokens=False, return_tensors="pt", truncation=False)
        if batch["input_ids"].shape[-1] > self.limit:
            raise ValueError(f"STATE_TRUNCATED: prompt exceeds {self.limit} tokens")
        with self.torch.inference_mode():
            logits = self.model(
                input_ids=batch["input_ids"].to(self.device), logits_to_keep=1, use_cache=False
            ).logits[0, -1]
            probs = self.torch.softmax(logits[[tokens[0] for tokens in ids]].float(), dim=-1).tolist()
        return probs, int(batch["input_ids"].numel())

    def predict(self, state, questions):
        answers, count = {}, 0
        for key, raw in questions.items():
            question = as_question(raw)
            keys, descriptions = options(question)
            probs, tokens = (
                self.nli(state_text(state), question, descriptions)
                if self.mode.endswith("nli")
                else self.letters(state_text(state), question, keys, descriptions)
            )
            result = answer(question.kind, keys, descriptions, probs)
            if self.mode == "raz-nli" and question.kind == "score":
                # Raz reports the modal level, not the expected value.
                result["score"] = float(max(range(len(probs)), key=probs.__getitem__))
            answers[key], count = result, count + tokens
        return {"answers": answers, "usage": {"input_tokens": count, "output_tokens": 0}}
