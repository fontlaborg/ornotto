# this_file: tests/test_remote.py
"""Exercise authenticated remote requests without credentials or billable inference."""

import json

import httpx
import pytest

from ornotto import OPENROUTER_MODELS, Decider, DecisionError, choice, score, yes_no
from ornotto.__main__ import Cli


@pytest.fixture
def remote_http(monkeypatch):
    calls = []
    reply = {
        "model": "typesafe/jev-1.13-dated",
        "provider": "TypeSafe",
        "id": "gen-test",
        "usage": {"input_tokens": 30, "output_tokens": 0, "cost": 0.0001},
        "answers": {"q": {"type": "choice", "choice": "b", "probabilities": {"a": 0.2, "b": 0.8}}},
    }

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json=reply)

    sync, async_ = httpx.Client, httpx.AsyncClient
    transport = httpx.MockTransport(handle)
    monkeypatch.setattr(httpx, "Client", lambda **kw: sync(transport=transport, **kw))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: async_(transport=transport, **kw))
    monkeypatch.setattr("ornotto._decider.resolve", lambda *a, **kw: pytest.fail("No remote download"))
    monkeypatch.setattr("ornotto._decider.Server.shared", lambda *a: pytest.fail("No remote server"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-test-key")
    return calls, reply


@pytest.mark.parametrize("model", OPENROUTER_MODELS)
def test_remote_when_registered_then_native_authenticated_call(remote_http, model):
    calls, reply = remote_http
    decider = Decider(model)
    question = choice("Which?", ["a", "b"])
    if model.startswith("respan/"):
        question = yes_no("Code?")
        reply["answers"] = {"q": {"type": "noul", "noul": 0.9}}
    result = decider.decide({"text": "hi"}, {"q": question})
    request = calls[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/systemone"
    assert request.headers["Authorization"] == "Bearer secret-test-key"
    assert json.loads(request.content)["model"] == model
    assert result.q.value == (True if model.startswith("respan/") else "b") and not result.q.calibrated
    assert result.usage["cost"] == 0.0001 and result.provider == "TypeSafe"
    assert result.resolved_model == "typesafe/jev-1.13-dated" and result.response_id == "gen-test"
    assert "secret-test-key" not in repr(decider)


@pytest.mark.parametrize("model", [m for m in OPENROUTER_MODELS if m.startswith("respan/")])
def test_respan_when_unsupported_question_then_no_billable_call(remote_http, model):
    d = Decider(model)
    for question in (choice("Which?", ["a", "b"]), score("Rank?", ["low", "high"])):
        with pytest.raises(ValueError, match="only noul"):
            d.decide("hi", {"q": question})
    assert not remote_http[0], "Capability errors must be detected before HTTP"


async def test_remote_when_async_mixed_questions_then_native_answers(remote_http):
    calls, reply = remote_http
    reply["answers"].update(
        {
            "yes": {"type": "noul", "noul": 0.9},
            "rank": {"type": "score", "score": 0.8, "probabilities": {"0": 0.2, "1": 0.8}},
        }
    )
    result = await Decider("openrouter:liquid/d1").adecide(
        "hi", {"q": choice(None, ["a", "b"]), "yes": yes_no("Yes?"), "rank": score(None, ["low", "high"])}
    )
    assert result.yes.value is True and result.rank.value == 0.8
    assert len(json.loads(calls[0].content)["questions"]) == 3


def test_remote_when_key_missing_then_actionable_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        Decider("liquid/d1")


@pytest.mark.parametrize("status", [401, 402, 429, 503])
def test_remote_when_api_error_then_no_retry_and_no_key_leak(remote_http, status):
    d = Decider("liquid/d1")
    with pytest.raises(DecisionError, match=str(status)) as error:
        d._check(httpx.Response(status, text="secret-test-key"), {"q": choice(None, ["a", "b"])})
    assert "secret-test-key" not in str(error.value)


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"answers": {}},
        {"answers": {"q": {"type": "noul", "noul": 2}}},
        {"answers": {"q": {"type": "choice", "choice": "b", "probabilities": {"a": 0.2, "b": float("nan")}}}},
    ],
)
def test_remote_when_malformed_response_then_decision_error(remote_http, bad):
    with pytest.raises(DecisionError, match="response"):
        Decider("liquid/d1")._check(
            httpx.Response(200, text=json.dumps(bad)), {"q": choice(None, ["a", "b"])}
        )


def test_remote_when_cli_list_then_all_models_visible():
    text = Cli().models()
    assert all(m in text for m in OPENROUTER_MODELS), "All requested remote IDs must be discoverable"


def test_remote_when_explicit_engine_and_key_then_custom_model(remote_http):
    d = Decider("vendor/custom:free", engine="openrouter", api_key="explicit")
    d.decide("hi", {"q": choice(None, ["a", "b"])})
    assert remote_http[0][0].headers["Authorization"] == "Bearer explicit"
    with pytest.raises(ValueError, match="remote"):
        Decider("liquid/d1", gpu=False)


def test_remote_when_typed_schema_then_extraction_uses_same_backend(remote_http):
    from typing import Literal

    from pydantic import BaseModel

    from ornotto import extract

    class Result(BaseModel):
        q: Literal["a", "b"]

    assert extract(Result, "hi", decider=Decider("liquid/d1")).q == "b"


@pytest.mark.parametrize("async_mode", [False, True])
async def test_remote_when_timeout_then_single_request_and_clear_error(remote_http, async_mode):
    d = Decider("liquid/d1")
    calls = []

    def fail(*args, **kwargs):
        calls.append(args)
        raise httpx.ReadTimeout("timeout")

    async def afail(*args, **kwargs):
        return fail(*args, **kwargs)

    with pytest.raises(DecisionError, match="ReadTimeout"):
        if async_mode:
            await d._apost(afail, "hi", {"q": choice(None, ["a", "b"])})
        else:
            d._post(fail, "hi", {"q": choice(None, ["a", "b"])})
    assert len(calls) == 1, "Timeouts must not multiply billable calls"


def test_remote_when_empty_questions_or_local_operations_then_rejected(remote_http):
    with pytest.raises(ValueError, match="at least one"):
        Decider("liquid/d1").decide("hi", {})
    assert not remote_http[0], "Empty requests never reach the provider"
    with pytest.raises(ValueError, match="local weights"):
        Cli().pull("liquid/d1")
    with pytest.raises(ValueError, match="hosted"):
        Cli().serve("liquid/d1")


def test_local_when_remote_key_in_environment_then_key_is_not_sent(remote_http):
    d = Decider("local", url="http://127.0.0.1:12345")
    d.decide("hi", {"q": choice(None, ["a", "b"])})
    assert "Authorization" not in remote_http[0][0].headers, "A remote key never goes to local engines"


@pytest.mark.parametrize("state", [None, True, -1, float("inf")])
def test_remote_when_state_outside_api_contract_then_no_request(remote_http, state):
    with pytest.raises(ValueError, match="state"):
        Decider("liquid/d1").decide(state, {"q": choice(None, ["a", "b"])})
    assert not remote_http[0], "Invalid states must be rejected before remote inference"


async def test_remote_when_pydantic_ai_provider_then_real_sdk_targets_openrouter(monkeypatch):
    import httpx2
    from typesafe_sdk import Choice

    from ornotto.pydantic_ai import provider

    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-test-key")
    client = provider(Decider("liquid/d1")).client
    calls = []

    async def handle(request):
        calls.append(request)
        return httpx2.Response(
            200,
            json={
                "model": "liquid/d1",
                "usage": {"input_tokens": 10, "output_tokens": 0},
                "answers": {
                    "q": {
                        "type": "choice",
                        "choice": "b",
                        "confidence": 0.5,
                        "probabilities": {"a": 0.2, "b": 0.8},
                    }
                },
            },
        )

    await client._http_client.aclose()
    client._http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    async with client:
        result = await client.system_one(
            "hi", {"q": Choice(criteria={"a": None, "b": None})}, model="liquid/d1"
        )
    assert result.choices["q"].choice == "b"
    assert str(calls[0].url) == "https://openrouter.ai/api/v1/systemone"
    assert calls[0].headers["Authorization"] == "Bearer secret-test-key"


async def test_remote_when_pydantic_ai_agent_then_typed_output(monkeypatch):
    from typing import Literal

    import httpx2
    from pydantic import BaseModel
    from pydantic_ai import Agent

    import ornotto.pydantic_ai as integration

    class Output(BaseModel):
        q: Literal["a", "b"]

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    d = Decider("liquid/d1")
    configured = integration.provider(d)
    calls = []

    async def handle(request):
        calls.append(request)
        return httpx2.Response(
            200,
            json={
                "model": "liquid/d1",
                "usage": {"input_tokens": 10, "output_tokens": 0},
                "answers": {
                    "q": {
                        "type": "choice",
                        "choice": "b",
                        "confidence": 0.5,
                        "probabilities": {"a": 0.2, "b": 0.8},
                    }
                },
            },
        )

    await configured.client._http_client.aclose()
    configured.client._http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    monkeypatch.setattr(integration, "provider", lambda _: configured)
    async with configured.client:
        result = await Agent(integration.model(d), output_type=Output).run("hi")
    assert result.output.q == "b"
    assert json.loads(calls[0].content)["model"] == "liquid/d1"


async def test_respan_when_pydantic_ai_bool_then_plain_native_questions(remote_http):
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent

    from ornotto.pydantic_ai import model

    class Output(BaseModel):
        q: bool = Field(description="Does the user ask for runnable code?")

    calls, reply = remote_http
    reply["answers"] = {"q": {"type": "noul", "noul": 0.9}}
    result = await Agent(model("respan/span-01-lite"), output_type=Output).run("Write code")
    assert result.output.q is True
    body = json.loads(calls[0].content)
    assert body["model"] == "respan/span-01-lite"
    assert isinstance(body["questions"]["q"]["instructions"], str)
