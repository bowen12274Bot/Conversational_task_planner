import json
from typing import Any

from app.schemas import AIToModuleResult, ChatModuleInput, ChatModuleOutput
from app.services.ai_service.service import run_ai_flow
from app.services.modules.chat.prompt import build_chat_ai_request
from app.services.modules.chat.validator import validate_chat_output


MAX_CHAT_RETRY_COUNT = 2


def build_chat_answer(chat_input: ChatModuleInput) -> ChatModuleOutput:
    """根據既有規劃與本輪問題產生 Chat 回答。"""

    ai_request = build_chat_ai_request(chat_input)
    expected_main_task_order = chat_input.planning_intent.target_main_task_order

    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_CHAT_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_chat_result(
            ai_result=ai_result,
            expected_main_task_order=expected_main_task_order,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Chat output validation failed after "
        f"{MAX_CHAT_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def _parse_chat_result(
    *,
    ai_result: AIToModuleResult,
    expected_main_task_order: int | None,
) -> tuple[ChatModuleOutput | None, str, dict[str, Any]]:
    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    parsed_output = _extract_chat_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_chat_output(
        parsed_output,
        expected_main_task_order=expected_main_task_order,
    )
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    try:
        return ChatModuleOutput.model_validate(parsed_output), "accept", {}
    except Exception as exc:  # pragma: no cover - defensive
        return None, "schema_validation_failed", {"error_message": str(exc)}


def _extract_chat_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    if isinstance(output_result, dict):
        if _looks_like_chat_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_chat_text(text_output)

    if isinstance(output_result, str):
        return _parse_chat_text(output_result)

    return None


def _parse_chat_text(text_output: str) -> dict[str, Any] | None:
    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    return _extract_last_chat_json_object(normalized_text)


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


def _looks_like_chat_output(value: dict[str, Any]) -> bool:
    required_keys = {
        "answer_types",
        "answer",
        "referenced_plan",
        "suggested_follow_up_actions",
    }
    return required_keys.issubset(value.keys())


def _extract_last_chat_json_object(text_output: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
    else:
        if isinstance(parsed_output, dict) and _looks_like_chat_output(parsed_output):
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
        if _looks_like_chat_output(candidate):
            return candidate

    return None
