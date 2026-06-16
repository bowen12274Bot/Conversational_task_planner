from typing import Any

from pydantic import BaseModel, Field


ALLOWED_ANSWER_TYPES = {
    "plan_explanation",
    "execution_advice",
    "resource_suggestion",
    "risk_analysis",
    "general_answer",
}
ALLOWED_FOLLOW_UP_ACTION_TYPES = {"revise_plan", "ask_more"}


class ChatValidationResult(BaseModel):
    """Chat Module 輸出驗證結果。"""

    is_valid: bool
    action: str = Field(..., min_length=1)
    reason: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


def validate_chat_output(
    output_data: dict[str, Any],
    *,
    expected_main_task_order: int | None = None,
) -> ChatValidationResult:
    """驗證 AI 產出的 Chat 結果是否符合目前系統契約。"""

    missing_fields = _collect_missing_required_fields(output_data)
    if missing_fields:
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="missing_required_field",
            details={"missing_fields": missing_fields},
        )

    answer_types_error = _validate_answer_types(output_data.get("answer_types"))
    if answer_types_error is not None:
        return answer_types_error

    answer = output_data.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_answer",
            details={},
        )

    referenced_plan_error = _validate_referenced_plan(
        output_data.get("referenced_plan"),
        expected_main_task_order=expected_main_task_order,
    )
    if referenced_plan_error is not None:
        return referenced_plan_error

    follow_up_error = _validate_suggested_follow_up_actions(
        output_data.get("suggested_follow_up_actions")
    )
    if follow_up_error is not None:
        return follow_up_error

    return ChatValidationResult(is_valid=True, action="accept")


def _collect_missing_required_fields(output_data: dict[str, Any]) -> list[str]:
    required_fields = (
        "answer_types",
        "answer",
        "referenced_plan",
        "suggested_follow_up_actions",
    )
    return [field_name for field_name in required_fields if field_name not in output_data]


def _validate_answer_types(value: Any) -> ChatValidationResult | None:
    if not isinstance(value, list):
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_answer_types",
            details={"expected_type": "list"},
        )

    if not 1 <= len(value) <= 3:
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_answer_types_count",
            details={"count": len(value)},
        )

    invalid_values = [
        item for item in value if not isinstance(item, str) or item not in ALLOWED_ANSWER_TYPES
    ]
    if invalid_values:
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_answer_type_value",
            details={"invalid_values": invalid_values},
        )

    if len(set(value)) != len(value):
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="duplicated_answer_type",
            details={"answer_types": value},
        )

    return None


def _validate_referenced_plan(
    value: Any,
    *,
    expected_main_task_order: int | None,
) -> ChatValidationResult | None:
    if value is None:
        return None

    if not isinstance(value, dict):
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_referenced_plan",
            details={"expected_type": "object_or_null"},
        )

    main_task_order = value.get("main_task_order")
    if main_task_order is not None:
        if not isinstance(main_task_order, int) or main_task_order < 1:
            return ChatValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_referenced_main_task_order",
                details={"main_task_order": main_task_order},
            )
        if (
            expected_main_task_order is not None
            and main_task_order != expected_main_task_order
        ):
            return ChatValidationResult(
                is_valid=False,
                action="regenerate",
                reason="unexpected_referenced_main_task_order",
                details={
                    "expected": expected_main_task_order,
                    "actual": main_task_order,
                },
            )

    subtask_orders = value.get("subtask_orders", [])
    if not isinstance(subtask_orders, list) or any(
        not isinstance(item, str) for item in subtask_orders
    ):
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_referenced_subtask_orders",
            details={"subtask_orders": subtask_orders},
        )

    return None


def _validate_suggested_follow_up_actions(
    value: Any,
) -> ChatValidationResult | None:
    if not isinstance(value, list):
        return ChatValidationResult(
            is_valid=False,
            action="regenerate",
            reason="invalid_suggested_follow_up_actions",
            details={"expected_type": "list"},
        )

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            return ChatValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_follow_up_action_shape",
                details={"index": index},
            )

        action_type = item.get("action_type")
        if action_type not in ALLOWED_FOLLOW_UP_ACTION_TYPES:
            return ChatValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_follow_up_action_type",
                details={"index": index, "action_type": action_type},
            )

        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            return ChatValidationResult(
                is_valid=False,
                action="regenerate",
                reason="invalid_follow_up_action_label",
                details={"index": index},
            )

    return None
