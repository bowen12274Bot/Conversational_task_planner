import json
from typing import Any, Literal, cast

from app.schemas import AIToModuleResult, ContextEngineeringOutput, QuestioningDecision
from app.services.ai_service.service import run_ai_flow
from app.services.modules.questioning.prompt import build_questioning_ai_request
from app.services.modules.questioning.validator import (
    validate_questioning_decision_output,
)


MAX_QUESTIONING_RETRY_COUNT = 3


def evaluate_questioning_need(
    context_output: ContextEngineeringOutput,
    follow_up_round_count: int,
) -> QuestioningDecision:
    """根據整理後需求狀態判斷下一步應追問或進入規劃。"""

    requirement_context = context_output.requirement_context.strip()
    if not requirement_context:
        raise ValueError("requirement_context 不可為空白。")

    ai_request = build_questioning_ai_request(
        requirement_context=requirement_context,
        known_information=context_output.known_information,
        pending_confirmation=context_output.pending_confirmation,
        follow_up_round_count=follow_up_round_count,
    )

    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_QUESTIONING_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_questioning_result(
            ai_result=ai_result,
            fallback_known_information=context_output.known_information,
            fallback_pending_confirmation=context_output.pending_confirmation,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Questioning output validation failed after "
        f"{MAX_QUESTIONING_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def _parse_questioning_result(
    *,
    ai_result: AIToModuleResult,
    fallback_known_information: list[dict[str, Any]],
    fallback_pending_confirmation: list[dict[str, Any]],
) -> tuple[QuestioningDecision | None, str, dict[str, Any]]:
    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    parsed_output = _extract_questioning_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_questioning_decision_output(parsed_output)
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    return QuestioningDecision(
        decision=_normalize_questioning_decision(parsed_output["decision"]),
        reasoning=str(parsed_output["reasoning"]).strip(),
        known_information=_collect_information_list(
            parsed_output.get("known_information"),
            fallback_known_information,
        ),
        pending_confirmation=_collect_information_list(
            parsed_output.get("pending_confirmation"),
            fallback_pending_confirmation,
        ),
        next_step_guidance=_collect_guidance_list(
            parsed_output.get("next_step_guidance")
        ),
    ), "accept", {}


def _extract_questioning_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    if isinstance(output_result, dict):
        if _looks_like_questioning_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_questioning_text(text_output)

    if isinstance(output_result, str):
        return _parse_questioning_text(output_result)

    return None


def _parse_questioning_text(text_output: str) -> dict[str, Any] | None:
    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    parsed_output = _load_json_object(normalized_text)
    if parsed_output is None:
        return None

    if not isinstance(parsed_output, dict):
        return None

    if not _looks_like_questioning_output(parsed_output):
        return None

    return parsed_output


def _load_json_object(text_output: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
        for start_index in range(len(text_output) - 1, -1, -1):
            if text_output[start_index] != "{":
                continue

            try:
                candidate, _ = decoder.raw_decode(text_output[start_index:])
            except json.JSONDecodeError:
                continue

            if isinstance(candidate, dict):
                parsed_output = candidate
                break

    if not isinstance(parsed_output, dict):
        return None

    return parsed_output


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


def _looks_like_questioning_output(value: dict[str, Any]) -> bool:
    required_keys = {
        "decision",
        "reasoning",
        "known_information",
        "pending_confirmation",
        "next_step_guidance",
    }
    return required_keys.issubset(value.keys())


def _normalize_questioning_decision(value: Any) -> Literal["follow_up", "planning"]:
    if value == "follow_up":
        return cast(Literal["follow_up", "planning"], "follow_up")
    if value == "planning":
        return cast(Literal["follow_up", "planning"], "planning")

    raise ValueError(f"Unsupported questioning decision: {value!r}")


def _collect_information_list(
    value: Any,
    fallback_value: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return list(fallback_value)

    collected_items: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            collected_items.append(item)

    return collected_items


def _collect_guidance_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    guidance_items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            guidance_items.append(item.strip())

    return guidance_items
