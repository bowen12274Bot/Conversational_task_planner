from dataclasses import dataclass, field
from typing import Any


@dataclass
class QuestioningValidationResult:
    is_valid: bool
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def validate_questioning_decision_output(
    value: dict[str, Any],
) -> QuestioningValidationResult:
    required_keys = {
        "decision",
        "reasoning",
        "known_information",
        "pending_confirmation",
        "next_step_guidance",
    }
    missing_keys = sorted(required_keys - set(value.keys()))
    if missing_keys:
        return QuestioningValidationResult(
            is_valid=False,
            reason="missing_required_keys",
            details={"missing_keys": missing_keys},
        )

    decision = value.get("decision")
    if decision not in {"follow_up", "planning"}:
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_decision",
            details={"decision": decision},
        )

    reasoning = value.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_reasoning",
        )

    known_information = value.get("known_information")
    if not _is_list_of_dicts(known_information):
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_known_information",
        )

    pending_confirmation = value.get("pending_confirmation")
    if not _is_list_of_dicts(pending_confirmation):
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_pending_confirmation",
        )

    next_step_guidance = value.get("next_step_guidance")
    if not isinstance(next_step_guidance, list):
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_next_step_guidance",
            details={"type": type(next_step_guidance).__name__},
        )

    if not all(isinstance(item, str) and item.strip() for item in next_step_guidance):
        return QuestioningValidationResult(
            is_valid=False,
            reason="invalid_next_step_guidance_item",
        )

    return QuestioningValidationResult(is_valid=True)


def _is_list_of_dicts(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)
