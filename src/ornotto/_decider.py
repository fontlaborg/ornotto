# this_file: src/ornotto/_decider.py
"""`Decider`: one model on one engine, asked System One questions."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx

from ._engines import Adapter, Server, gpu_available
from ._models import DEFAULT_MODEL, MODELS, Engine, resolve
from ._protocol import JSON, Answer, Decision, Question, as_question, choice, parse_answer, score, yes_no
from ._remote import OPENROUTER_MODELS, OPENROUTER_URL

QuestionLike = Question | Mapping[str, JSON]


class DecisionError(RuntimeError):
    """The engine rejected a request or failed to answer it."""


# The ollaya error code that deserves a plainer message than the raw 422 body.
STATE_TRUNCATED = "STATE_TRUNCATED"


class Decider:
    """A model on an engine, ready to answer questions about a state.

    >>> d = Decider()                                    # decider-0.8b on dohnuts, downloaded on first use
    >>> d.choose("Build a kern feature for A V", ["docs", "python", "fea"]).value
    'fea'

    Args:
        model: a registered name (see `ornotto.MODELS`), a local .gguf path, `hf:owner/repo/file.gguf`, or an
            ollaya tag (`ollaya:kev:4b`, or plain `kev:4b` with engine="ollaya").
        engine: "dohnuts", "pcd", "ollaya", "openrouter", "laya-mlx" or "xdecision".
            Registered models infer their native engine.
        url: talk to an engine that is already running instead of starting one.
        gpu: offload to the GPU (Metal on macOS). Defaults to on where the bundled build has a GPU backend.
        metadata, head: dohnuts profile JSON and scorer head, for a model that is not registered.
        timeout: seconds to wait for one answer.
        api_key: OpenRouter key; defaults to OPENROUTER_API_KEY. Only sent to remote models.

    The engine starts on the first question, not here, and is shared by every Decider in the process
    that uses the same model, engine and device.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        engine: Engine | None = None,
        url: str | None = None,
        gpu: bool | None = None,
        metadata: str | Path | None = None,
        head: str | Path | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
    ):
        self.gpu = gpu_available() if gpu is None else gpu
        self.timeout = timeout
        self._url = url.rstrip("/") if url else None
        wire = model
        self._api_key = None
        remote = engine == "openrouter" or model in OPENROUTER_MODELS or model.startswith("openrouter:")
        if remote:
            if (
                engine not in (None, "openrouter")
                or gpu is not None
                or metadata is not None
                or head is not None
            ):
                raise ValueError(
                    "remote models use engine='openrouter' and have no local GPU/metadata/head settings"
                )
            wire = model.removeprefix("openrouter:")
            if not wire or "/" not in wire:
                raise ValueError("remote model must be an OpenRouter owner/model ID")
            self._api_key = (
                api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
            ).strip()
            if not self._api_key:
                raise ValueError("Set OPENROUTER_API_KEY or pass api_key=... for remote models")
            self.model_name, self.engine, self._resolved = wire, "openrouter", None
            self._url = (url or OPENROUTER_URL).rstrip("/")
        elif api_key is not None:
            raise ValueError("api_key is only supported for remote OpenRouter models")
        elif url:
            self.model_name, self.engine, self._resolved = model, engine or "dohnuts", None
            spec = MODELS.get(model)
            wire = spec.tag if spec and spec.tag else model.removeprefix("ollaya:")
        else:
            if engine == "ollaya" and model not in MODELS and not model.startswith("ollaya:"):
                model = "ollaya:" + model
            resolved = resolve(model, metadata=metadata, head=head, engine=engine)
            chosen = engine or resolved.engines[0]
            if chosen not in resolved.engines:
                raise ValueError(f"{resolved.name} runs on {' or '.join(resolved.engines)}, not {chosen}")
            self.model_name, self.engine, self._resolved = resolved.name, chosen, resolved
            wire = resolved.tag or resolved.name
        self.adapter = Adapter(self.engine, wire)

    def __repr__(self) -> str:
        return f"Decider({self.model_name!r}, engine={self.engine!r})"

    @property
    def url(self) -> str:
        """The engine's base URL, starting the engine if needed."""
        if self._url:
            return self._url
        assert self._resolved is not None
        return Server.shared(self.engine, self._resolved, self.gpu).url

    # -- the general call ------------------------------------------------------------------------------------

    def decide(self, state: JSON, questions: Mapping[str, QuestionLike]) -> Decision:
        """Answer named questions about `state` (text, or any JSON value) in one call."""
        qs = {name: as_question(q) for name, q in questions.items()}
        _ = self.url  # start the engine before the clock does
        start = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            raw = [self._post(client.post, state, chunk) for chunk in self._chunks(qs)]
        return self._decision(raw, start)

    async def adecide(self, state: JSON, questions: Mapping[str, QuestionLike]) -> Decision:
        """`decide`, for asyncio. The first call may block briefly while the engine starts."""
        _ = self.url
        start = time.perf_counter()
        raw = await self._araw(state, {name: as_question(q) for name, q in questions.items()})
        return self._decision(raw, start)

    async def _araw(self, state: JSON, qs: Mapping[str, Question]) -> list[dict[str, JSON]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return [await self._apost(client.post, state, chunk) for chunk in self._chunks(qs)]

    def _chunks(self, qs: Mapping[str, Question]) -> list[dict[str, Question]]:
        if not qs:
            raise ValueError("ask at least one question")
        items, size = list(qs.items()), self.adapter.max_questions
        return [dict(items[i : i + size]) for i in range(0, len(items), size)]

    def _post(self, post: Any, state: JSON, qs: Mapping[str, Question]) -> dict[str, JSON]:
        path, body = self.adapter.request(state, qs)
        try:
            return self._check(post(self.url + path, json=body, **self._auth()), qs)
        except httpx.RequestError as error:
            if self.engine != "openrouter":
                raise
            raise DecisionError(
                f"openrouter request failed ({type(error).__name__}); no retry sent"
            ) from None

    async def _apost(self, post: Any, state: JSON, qs: Mapping[str, Question]) -> dict[str, JSON]:
        path, body = self.adapter.request(state, qs)
        try:
            return self._check(await post(self.url + path, json=body, **self._auth()), qs)
        except httpx.RequestError as error:
            if self.engine != "openrouter":
                raise
            raise DecisionError(
                f"openrouter request failed ({type(error).__name__}); no retry sent"
            ) from None

    def _auth(self) -> dict[str, Any]:
        return {"headers": {"Authorization": f"Bearer {self._api_key}"}} if self._api_key else {}

    def _check(self, response: httpx.Response, qs: Mapping[str, Question]) -> dict[str, JSON]:
        if response.status_code != 200:
            text = response.text.replace(self._api_key, "[redacted]") if self._api_key else response.text
            reply = f"{self.engine} answered {response.status_code}: {text[:500]}"
            if STATE_TRUNCATED in response.text:
                hint = (
                    f"the state is longer than {self.adapter.model_name}'s context; "
                    "shorten it or use a model with more"
                )
                raise DecisionError(f"{hint} ({reply})")
            raise DecisionError(reply)
        try:
            return self.adapter.response(response.json(), qs)
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            if self.engine != "openrouter":
                raise
            raise DecisionError("openrouter returned an invalid decision response") from error

    def _decision(self, raw: list[dict[str, JSON]], start: float) -> Decision:
        answers = {
            name: parse_answer(a, self.adapter.calibrated) for r in raw for name, a in r["answers"].items()
        }
        usage: dict[str, JSON] = {}
        for r in raw:
            for key, value in (r.get("usage") or {}).items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
        return Decision(
            answers,
            self.model_name,
            self.engine,
            usage,
            (time.perf_counter() - start) * 1000,
            resolved_model=raw[0].get("model"),
            provider=raw[0].get("provider"),
            response_id=raw[0].get("id"),
        )

    # -- one question at a time ------------------------------------------------------------------------------

    def choose(
        self, state: JSON, options: Sequence[str] | Mapping[str, str | None], question: str | None = None
    ) -> Answer:
        """Pick one of `options` (names, or name -> description). `.value` is the option name."""
        return self.decide(state, {"answer": choice(question, options)})["answer"]

    def check(self, state: JSON, question: str, *, yes: str | None = None, no: str | None = None) -> Answer:
        """Answer yes or no. `.value` is True or False, `.probability` the probability of yes."""
        return self.decide(state, {"answer": yes_no(question, yes=yes, no=no)})["answer"]

    def rate(self, state: JSON, question: str | None, levels: Sequence[str]) -> Answer:
        """Place `state` on a rubric; `levels[i]` describes level i. `.value` is the expected level."""
        return self.decide(state, {"answer": score(question, levels)})["answer"]
