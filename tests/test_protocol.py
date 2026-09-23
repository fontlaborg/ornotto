# this_file: tests/test_protocol.py
import pytest

from ornotto._protocol import (
    Decision,
    as_question,
    choice,
    entropy_confidence,
    from_pcd,
    parse_answer,
    score,
    to_pcd,
    yes_no,
)


def test_choice_when_list_then_options_without_descriptions():
    q = choice("Which task?", ["docs", "fea"])
    assert q.to_system_one() == {
        "type": "choice",
        "instructions": "Which task?",
        "criteria": {"docs": None, "fea": None},
    }


def test_choice_when_one_option_then_error():
    with pytest.raises(ValueError, match="two options"):
        choice("?", ["only"])


def test_score_when_levels_then_ordered_criteria_list():
    assert score("How urgent?", ["low", "high"]).to_system_one()["criteria"] == ["low", "high"]


def test_as_question_when_system_one_aliases_then_same_question():
    q = as_question({"type": "bool", "question": "Spam?", "options": {"true": "an ad"}})
    assert q == yes_no("Spam?", yes="an ad"), (
        "bool/question/options are aliases of noul/instructions/criteria"
    )


def test_as_question_when_score_keyed_by_numbers_then_sorted_numerically():
    q = as_question({"type": "score", "criteria": {"10": "c", "2": "b", "0": "a"}})
    assert list(q.options.values()) == ["a", "b", "c"]


def test_to_pcd_when_mixed_questions_then_bounded_fields():
    qs = {
        "task": choice("Which?", {"docs": "the manual", "fea": None}),
        "code": yes_no("Code?", yes="runnable"),
        "urgency": score("Urgent?", ["no", "yes"]),
    }
    body = to_pcd({"text": "hi"}, qs)
    assert body["context"] == '{"text": "hi"}', "non-string state is serialised"
    fields = {f["name"]: f for f in body["fields"]}
    assert fields["task"]["choices"] == ["docs", "fea"]
    assert "docs: the manual" in fields["task"]["description"], (
        "option descriptions fold into the field description"
    )
    assert fields["code"]["choices"] == [False, True]
    assert fields["urgency"]["choices"] == ["0", "1"]


def test_to_pcd_when_description_too_long_then_clipped_to_limit():
    body = to_pcd("x", {"q": choice("?" * 2000, ["a", "b"])})
    assert len(body["fields"][0]["description"].encode()) <= 1024


def test_to_pcd_when_too_many_questions_then_error():
    with pytest.raises(ValueError, match="63"):
        to_pcd("x", {str(i): yes_no("?") for i in range(64)})


def test_from_pcd_when_fields_then_system_one_answers():
    qs = {"task": choice(None, ["docs", "fea"]), "code": yes_no("?"), "u": score(None, ["a", "b", "c"])}
    body = {
        "model": "m.gguf",
        "fields": [
            {"name": "task", "value": "fea", "probabilities": {"docs": 0.2, "fea": 0.8}},
            {"name": "code", "value": True, "probabilities": {"false": 0.3, "true": 0.7}},
            {"name": "u", "value": "2", "probabilities": {"0": 0.0, "1": 0.5, "2": 0.5}},
        ],
        "metrics": {"elapsedMs": 5},
    }
    out = from_pcd(body, qs)
    assert out["answers"]["task"]["choice"] == "fea"
    assert out["answers"]["code"] == {"type": "noul", "noul": 0.7}
    assert out["answers"]["u"]["score"] == pytest.approx(1.5), "score is the expected level"


def test_parse_answer_when_noul_then_bool_value_and_probability():
    a = parse_answer({"type": "noul", "noul": 0.25}, calibrated=True)
    assert a.value is False and a.probability == 0.25 and a.confidence == 0.75


def test_parse_answer_when_score_then_level_is_argmax():
    a = parse_answer(
        {"type": "score", "score": 1.2, "confidence": 0.5, "probabilities": {"0": 0.1, "1": 0.6, "2": 0.3}},
        calibrated=False,
    )
    assert a.value == 1.2 and a.level == 1 and not a.calibrated


def test_decision_when_attribute_access_then_answer():
    a = parse_answer({"type": "noul", "noul": 0.9}, True)
    d = Decision({"spam": a}, "m", "dohnuts")
    assert d.spam is a and d["spam"] is a and d.to_dict() == {"spam": True} and len(d) == 1
    with pytest.raises(AttributeError):
        _ = d.missing


def test_entropy_confidence_when_uniform_then_zero_and_certain_then_one():
    assert entropy_confidence([0.5, 0.5]) == pytest.approx(0.0)
    assert entropy_confidence([1.0, 0.0]) == pytest.approx(1.0)


def test_as_question_when_json_instructions_then_text():
    q = as_question({"type": "noul", "instructions": {"task": "Is this spam?"}})
    assert q.instructions == '{"task": "Is this spam?"}', "pydantic-ai may send instructions as a JSON object"
