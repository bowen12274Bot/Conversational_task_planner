from typing import Any

from pydantic import BaseModel, Field
from app.services.modules.shared.requirement_labels import (
    ALLOWED_REQUIREMENT_LABELS,
)


class ContextEngineeringValidationResult(BaseModel):
    """Context Engineering 輸出驗證結果。"""

    is_valid: bool
    action: str = Field(..., min_length=1)  # "accept" | "regenerate"
    reason: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


def validate_context_engineering_output(
    output_data: dict[str, Any],
) -> ContextEngineeringValidationResult:
    """驗證 AI 產出的 CE 結果是否符合目前系統契約。"""

    missing_fields = _collect_missing_required_fields(output_data)
    if missing_fields:
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="missing_required_field",
            details={"missing_fields": missing_fields},
        )

    requirement_context = output_data.get("requirement_context")
    if not isinstance(requirement_context, str) or not requirement_context.strip():
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_requirement_context",
            details={},
        )

    known_information = output_data.get("known_information")
    known_information_error = _validate_information_items(
        field_name="known_information",
        items=known_information,
        required_value_key="value",
    )
    if known_information_error is not None:
        return known_information_error

    pending_confirmation = output_data.get("pending_confirmation")
    pending_confirmation_error = _validate_information_items(
        field_name="pending_confirmation",
        items=pending_confirmation,
        required_value_key="question_hint",
    )
    if pending_confirmation_error is not None:
        return pending_confirmation_error

    if "planning_intent" in output_data:
        planning_intent_error = _validate_planning_intent(
            output_data.get("planning_intent")
        )
        if planning_intent_error is not None:
            return planning_intent_error

    return ContextEngineeringValidationResult(
        is_valid=True,
        action="accept",
    )


def _collect_missing_required_fields(output_data: dict[str, Any]) -> list[str]:
    """收集 CE 必要欄位中缺漏的欄位名稱。"""

    required_fields = (
        "requirement_context",
        "known_information",
        "pending_confirmation",
    )
    return [field_name for field_name in required_fields if field_name not in output_data]


def _validate_planning_intent(
    value: Any,
) -> ContextEngineeringValidationResult | None:
    if not isinstance(value, dict):
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_planning_intent",
            details={"expected_type": "object"},
        )

    intent_type = value.get("intent_type")
    if intent_type not in {"create", "revise", "chat", "other"}:
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_planning_intent_type",
            details={"intent_type": intent_type},
        )

    target_main_task_order = value.get("target_main_task_order")
    if target_main_task_order is not None:
        if not isinstance(target_main_task_order, int) or target_main_task_order < 1:
            return ContextEngineeringValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_target_main_task_order",
                details={"target_main_task_order": target_main_task_order},
            )

    confidence = value.get("confidence")
    if confidence not in {"high", "medium", "low"}:
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_planning_intent_confidence",
            details={"confidence": confidence},
        )

    return None


def _validate_information_items(
    field_name: str,
    items: Any,
    required_value_key: str,
) -> ContextEngineeringValidationResult | None:
    """驗證 known_information / pending_confirmation 的項目契約。"""

    if not isinstance(items, list):
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_field_type",
            details={"field": field_name, "expected_type": "list"},
        )

    invalid_labels: list[str] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return ContextEngineeringValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_item_shape",
                details={"field": field_name, "index": index},
            )

        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            return ContextEngineeringValidationResult(
                is_valid=False,
                action="regenerate",
                reason="missing_label",
                details={"field": field_name, "index": index},
            )

        if label not in ALLOWED_REQUIREMENT_LABELS:
            invalid_labels.append(label)

        value = item.get(required_value_key)
        if not isinstance(value, str) or not value.strip():
            return ContextEngineeringValidationResult(
                is_valid=False,
                action="regenerate",
                reason="missing_required_item_value",
                details={
                    "field": field_name,
                    "index": index,
                    "required_key": required_value_key,
                },
            )

    if invalid_labels:
        return ContextEngineeringValidationResult(
            is_valid=False,
            action="regenerate",
            reason="unknown_label",
            details={"field": field_name, "invalid_labels": invalid_labels},
        )

    return None
