# this_file: src/ornotto/_bosun_prompt.py
"""Public Bosun prompt compiler (Apache-2.0).

Hanno-Labs/bosun-v3.1-0.6b, revision 1d8b6f9611f9b64b514ce8b57cd86398fbc31a3b,
modeling_bosun.py. Preserves the author's stable-slot permutation and JSON bytes.
"""

import hashlib
import json
import random
from collections.abc import Mapping, Sequence
from typing import Any

_DECISION_TYPES = {"choice", "score", "noul"}


def render_decision_prompt(
    *,
    state: Any,
    instructions: str,
    candidates: Sequence[Mapping[str, Any]],
    decision_type: str,
    decision_tokens: Sequence[str],
    seed: int,
    row_id: str,
    prompt_schema: str = "bosun-decision-prompt-v3-stable-slots",
) -> tuple[str, list[int], dict[str, int]]:
    """Compile a request into Bosun's stable presented-slot JSON contract."""

    candidate_count = len(candidates)
    if not 2 <= candidate_count <= 255:
        raise ValueError("Bosun supports 2 to 255 candidates")
    if decision_type not in _DECISION_TYPES:
        raise ValueError("decision_type must be one of: choice, score, noul")
    if len(decision_tokens) < candidate_count:
        raise ValueError("model does not expose enough decision tokens")

    presentation_order = list(range(candidate_count))
    digest = hashlib.sha256(f"{seed}:{row_id}:candidate-order".encode()).digest()
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(presentation_order)
    candidate_to_slot: dict[str, int] = {}
    mapped_criteria: list[dict[str, Any]] = []
    for slot, candidate_index in enumerate(presentation_order):
        candidate = candidates[candidate_index]
        candidate_id = str(candidate["id"])
        candidate_to_slot[candidate_id] = slot
        mapped_criteria.append(
            {
                "t": decision_tokens[slot],
                "o": candidate_index,
                "n": str(candidate["label"]),
                "d": candidate.get("description") or "",
            }
        )
    criteria_fields, criteria = _compact_criteria(mapped_criteria)
    content = _canonical_json(
        {
            "schema": prompt_schema,
            "state": state,
            "question": {
                "instructions": instructions,
                "type": decision_type,
                "criteria_fields": criteria_fields,
                "criteria": criteria,
            },
        }
    )
    return content, presentation_order, candidate_to_slot


def _compact_criteria(
    mapped_criteria: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[list[Any]]]:
    parsed_descriptions: list[dict[str, Any]] = []
    description_fields: list[str] | None = None
    for criterion in mapped_criteria:
        try:
            parsed = json.loads(str(criterion["d"]))
        except json.JSONDecodeError:
            parsed = None
        if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
            description_fields = None
            break
        fields = sorted(parsed)
        if description_fields is None:
            description_fields = fields
        elif fields != description_fields:
            description_fields = None
            break
        parsed_descriptions.append(parsed)
    if description_fields is not None and len(parsed_descriptions) == len(mapped_criteria):
        rows = [
            [
                criterion["t"],
                criterion["o"],
                criterion["n"],
                *(parsed[field] for field in description_fields),
            ]
            for criterion, parsed in zip(mapped_criteria, parsed_descriptions, strict=True)
        ]
        return ["t", "o", "n", *description_fields], rows
    return ["t", "o", "n", "d"], [
        [criterion["t"], criterion["o"], criterion["n"], criterion["d"]] for criterion in mapped_criteria
    ]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
