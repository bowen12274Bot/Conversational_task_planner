import json
from typing import Any

from app.schemas import (
    AIToModuleResult,
    PlanningCreateInput,
    PlanningCreateOutput,
    PlanningRevisionInput,
    PlanningRevisionOutput,
)
from app.services.ai_service.service import run_ai_flow
from app.services.modules.planning.prompt import (
    build_planning_create_ai_request,
    build_planning_revision_ai_request,
)
from app.services.modules.planning.validator import (
    validate_planning_create_output,
    validate_planning_revision_output,
)


MAX_PLANNING_CREATE_RETRY_COUNT = 3
MAX_PLANNING_REVISION_RETRY_COUNT = 2


def build_initial_planning(
    planning_input: PlanningCreateInput,
) -> PlanningCreateOutput:
    ai_request = build_planning_create_ai_request(
        requirement_context=planning_input.requirement_context,
        known_information=planning_input.known_information,
        pending_confirmation=planning_input.pending_confirmation,
        conversation_history_text=planning_input.conversation_history_text,
    )

    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_PLANNING_CREATE_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_planning_create_result(
            ai_result=ai_result,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Planning create output validation failed after "
        f"{MAX_PLANNING_CREATE_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def build_revised_planning(
    planning_input: PlanningRevisionInput,
) -> PlanningRevisionOutput:
    ai_request = build_planning_revision_ai_request(
        requirement_context=planning_input.requirement_context,
        known_information=planning_input.known_information,
        pending_confirmation=planning_input.pending_confirmation,
        conversation_history_text=planning_input.conversation_history_text,
        existing_plan_outline=planning_input.existing_plan_outline,
        target_main_task=planning_input.target_main_task.model_dump(),
        target_main_task_order=planning_input.target_main_task_order,
        revision_request=planning_input.revision_request,
    )

    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_PLANNING_REVISION_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_planning_revision_result(
            ai_result=ai_result,
            expected_target_main_task_order=planning_input.target_main_task_order,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Planning revision output validation failed after "
        f"{MAX_PLANNING_REVISION_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def _parse_planning_create_result(
    *,
    ai_result: AIToModuleResult,
) -> tuple[PlanningCreateOutput | None, str, dict[str, Any]]:
    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    parsed_output = _extract_planning_create_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_planning_create_output(parsed_output)
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    try:
        return PlanningCreateOutput.model_validate(parsed_output), "accept", {}
    except Exception as exc:  # pragma: no cover - defensive
        return None, "schema_validation_failed", {"error_message": str(exc)}


def _parse_planning_revision_result(
    *,
    ai_result: AIToModuleResult,
    expected_target_main_task_order: int,
) -> tuple[PlanningRevisionOutput | None, str, dict[str, Any]]:
    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    parsed_output = _extract_planning_revision_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_planning_revision_output(
        parsed_output,
        expected_target_main_task_order=expected_target_main_task_order,
    )
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    try:
        return PlanningRevisionOutput.model_validate(parsed_output), "accept", {}
    except Exception as exc:  # pragma: no cover - defensive
        return None, "schema_validation_failed", {"error_message": str(exc)}


def _extract_planning_create_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    if isinstance(output_result, dict):
        if _looks_like_planning_create_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_planning_create_text(text_output)

    if isinstance(output_result, str):
        return _parse_planning_create_text(output_result)

    return None


def _extract_planning_revision_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    if isinstance(output_result, dict):
        if _looks_like_planning_revision_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_planning_revision_text(text_output)

    if isinstance(output_result, str):
        return _parse_planning_revision_text(output_result)

    return None


def _parse_planning_create_text(text_output: str) -> dict[str, Any] | None:
    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    return _extract_last_planning_create_json_object(normalized_text)


def _parse_planning_revision_text(text_output: str) -> dict[str, Any] | None:
    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    return _extract_last_planning_revision_json_object(normalized_text)


def _strip_markdown_code_fence(text_output: str) -> str:
    if not text_output.startswith("```"):
        return text_output

    lines = text_output.splitlines()
    if not lines:
        return text_output

    if lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def _looks_like_planning_create_output(value: dict[str, Any]) -> bool:
    required_keys = {
        "plan_summary",
        "design_rationale",
        "assumptions_used",
        "schedule",
    }
    return required_keys.issubset(value.keys())


def _looks_like_planning_revision_output(value: dict[str, Any]) -> bool:
    required_keys = {
        "revision_summary",
        "design_rationale",
        "assumptions_used",
        "target_main_task_order",
        "updated_main_task",
    }
    return required_keys.issubset(value.keys())


def _extract_last_planning_create_json_object(
    text_output: str,
) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
    else:
        if isinstance(parsed_output, dict) and _looks_like_planning_create_output(
            parsed_output
        ):
            return parsed_output

    for start_index in range(len(text_output) - 1, -1, -1):
        if text_output[start_index] != "{":
            continue

        try:
            candidate, _ = decoder.raw_decode(text_output[start_index:])
        except json.JSONDecodeError:
            continue

        if isinstance(candidate, dict):
            candidates.append(candidate)

    for candidate in candidates:
        if _looks_like_planning_create_output(candidate):
            return candidate

    return None


def _extract_last_planning_revision_json_object(
    text_output: str,
) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
    else:
        if isinstance(parsed_output, dict) and _looks_like_planning_revision_output(
            parsed_output
        ):
            return parsed_output

    for start_index in range(len(text_output) - 1, -1, -1):
        if text_output[start_index] != "{":
            continue

        try:
            candidate, _ = decoder.raw_decode(text_output[start_index:])
        except json.JSONDecodeError:
            continue

        if isinstance(candidate, dict):
            candidates.append(candidate)

    for candidate in candidates:
        if _looks_like_planning_revision_output(candidate):
            return candidate

    return None
