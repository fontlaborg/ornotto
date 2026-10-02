# this_file: src/ornotto/pydantic_ai.py
"""pydantic-ai integration: run an `Agent` whose job is to decide on a local engine.

pydantic-ai's `TypeSafeModel` turns an agent's `output_type` into System One questions (one per field:
`bool`, `Literal`/`Enum`, rubrics, lists of options, nested models). dohnuts answers those requests
natively, so the model talks to it directly. For pcdServer, an in-process transport routes each request
through ornotto's translator.

    from pydantic_ai import Agent
    from ornotto.pydantic_ai import model

    agent = Agent(model("decider-0.8b"), output_type=Triage)
    agent.run_sync("Rename every .sc glyph to .smcp").output

Needs `pip install "ornotto[pydantic-ai]"`.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx2
from pydantic_ai.models.typesafe import TypeSafeModel
from pydantic_ai.providers.typesafe import TypeSafeProvider
from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

from ._decider import Decider
from ._models import DEFAULT_MODEL, Engine
from ._protocol import as_question
from ._remote import OPENROUTER_KINDS

__all__ = ["model", "provider"]

# The local engines need no key, but the TypeSafe client insists on one.
LOCAL_KEY = "ornotto-local"


def provider(decider: Decider) -> TypeSafeProvider:
    """A TypeSafe provider whose requests go to `decider`'s engine."""
    binary_remote = decider.engine == "openrouter" and OPENROUTER_KINDS.get(decider.model_name) == ("noul",)
    if decider.engine == "openrouter" and not binary_remote:
        client = AsyncTypeSafeClient(
            api_key=decider._api_key,
            base_url=decider.url,
            timeout=decider.timeout,
            retry=RetryPolicy(max_retries=0),
        )
        return TypeSafeProvider(typesafe_client=client)
    if decider.adapter.native and not binary_remote:  # local native engines
        return TypeSafeProvider(api_key=decider._api_key or LOCAL_KEY, base_url=decider.url)

    async def handle(request: httpx2.Request) -> httpx2.Response:
        if request.method == "GET" and request.url.path.endswith("/v1/models"):
            return httpx2.Response(
                200, json={"models": [{"name": decider.model_name, "description": "", "release_date": ""}]}
            )
        body: dict[str, Any] = json.loads(request.content)
        questions = {name: as_question(q) for name, q in body["questions"].items()}
        raw = await decider._araw(body["state"], questions)
        answers = {name: answer for r in raw for name, answer in r["answers"].items()}
        return httpx2.Response(
            200,
            json={
                "model": decider.model_name,
                "answers": answers,
                "usage": decider._decision(raw, time.perf_counter()).usage,
            },
        )

    client = AsyncTypeSafeClient(
        api_key=LOCAL_KEY,
        base_url="http://ornotto.local",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handle)),
    )
    return TypeSafeProvider(typesafe_client=client)


def model(
    model: str | Decider = DEFAULT_MODEL, *, engine: Engine | None = None, **kwargs: Any
) -> TypeSafeModel:
    """A pydantic-ai model on a local engine: pass a model name (with `Decider` options) or a Decider."""
    decider = model if isinstance(model, Decider) else Decider(model, engine=engine, **kwargs)
    return TypeSafeModel(decider.adapter.model_name, provider=provider(decider))
