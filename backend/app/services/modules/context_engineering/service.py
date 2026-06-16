import json
import re
from typing import Any

from app.schemas import AIToModuleResult, ContextEngineeringOutput, PlanningIntent
from app.services.persistence import get_conversation_transcript
from app.services.ai_service.service import run_ai_flow
from app.services.modules.context_engineering.prompt import (
    build_context_engineering_ai_request,
)
from app.services.modules.context_engineering.validator import (
    validate_context_engineering_output,
)


MAX_CONTEXT_ENGINEERING_RETRY_COUNT = 3


def build_context_from_raw_input(
    user_input: str,
    conversation_id: str | None = None,
    existing_plan_outline: list[dict[str, Any]] | None = None,
) -> ContextEngineeringOutput:
    """將使用者原始輸入整理為後續流程可用的基礎上下文。"""

    normalized_input = user_input.strip()
    if not normalized_input:
        raise ValueError("user_input 不可為空白。")

    conversation_history_text = _load_conversation_history_text(conversation_id)
    ai_request = build_context_engineering_ai_request(
        normalized_input,
        conversation_history_text=conversation_history_text,
        existing_plan_outline=existing_plan_outline,
    )
    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_CONTEXT_ENGINEERING_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_context_engineering_result(
            ai_result=ai_result,
            user_input=normalized_input,
            conversation_history_text=conversation_history_text,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Context engineering output validation failed after "
        f"{MAX_CONTEXT_ENGINEERING_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def _load_conversation_history_text(conversation_id: str | None) -> str | None:
    """依 conversation_id 載入聚合後的完整歷史文字內容。"""

    if conversation_id is None or not conversation_id.strip():
        return None

    return get_conversation_transcript(conversation_id.strip())


def _parse_context_engineering_result(
    ai_result: AIToModuleResult,
    user_input: str,
    conversation_history_text: str | None = None,
) -> tuple[ContextEngineeringOutput | None, str, dict[str, Any]]:
    """將 AI 回傳結果整理為 ContextEngineeringOutput。"""

    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    # AI service layer 先回傳通用結果，模組層再將其中內容轉成自己的業務資料形狀。
    parsed_output = _extract_context_engineering_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_context_engineering_output(parsed_output)
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    requirement_context = parsed_output.get("requirement_context")
    known_information = _collect_information_list(
        parsed_output.get("known_information")
    )
    pending_confirmation = _collect_information_list(
        parsed_output.get("pending_confirmation")
    )
    known_information, pending_confirmation = _preserve_explicit_user_facts(
        user_input=user_input,
        conversation_history_text=conversation_history_text,
        known_information=known_information,
        pending_confirmation=pending_confirmation,
    )
    planning_intent = _collect_planning_intent(parsed_output.get("planning_intent"))

    if not isinstance(requirement_context, str) or not requirement_context.strip():
        requirement_context = user_input

    return ContextEngineeringOutput(
        requirement_context=requirement_context.strip(),
        known_information=known_information,
        pending_confirmation=pending_confirmation,
        conversation_history_text=conversation_history_text,
        planning_intent=planning_intent,
    ), "accept", {}


def _extract_context_engineering_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    """從 AI service 的通用輸出中取出 Context Engineering 可承接的資料。"""

    if isinstance(output_result, dict):
        if _looks_like_context_engineering_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_context_engineering_text(text_output)

    if isinstance(output_result, str):
        return _parse_context_engineering_text(output_result)

    return None


def _parse_context_engineering_text(text_output: str) -> dict[str, Any] | None:
    """將模型文字輸出解析為 Context Engineering 所需的結構。"""

    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    return _extract_last_context_engineering_json_object(normalized_text)


def _strip_markdown_code_fence(text_output: str) -> str:
    """移除模型常見的 markdown code fence，保留內部 JSON 內容。"""

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


def _looks_like_context_engineering_output(value: dict[str, Any]) -> bool:
    """判斷 dict 是否至少具有 Context Engineering 預期的核心欄位。"""

    required_keys = {
        "requirement_context",
        "known_information",
        "pending_confirmation",
    }
    return required_keys.issubset(value.keys())


def _collect_planning_intent(value: Any) -> PlanningIntent:
    if not isinstance(value, dict):
        return PlanningIntent(
            intent_type="other",
            target_main_task_order=None,
            confidence="low",
        )

    try:
        return PlanningIntent.model_validate(value)
    except Exception:
        return PlanningIntent(
            intent_type="other",
            target_main_task_order=None,
            confidence="low",
        )


def _preserve_explicit_user_facts(
    *,
    user_input: str,
    conversation_history_text: str | None,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    user_text = _build_user_fact_source_text(
        user_input=user_input,
        conversation_history_text=conversation_history_text,
    )
    explicit_facts = {
        "deadline_hint": _extract_explicit_deadline_hint(user_text),
        "time_budget": _extract_explicit_time_budget(user_text),
    }

    updated_known_information = list(known_information)
    updated_pending_confirmation = list(pending_confirmation)
    for label, value in explicit_facts.items():
        if value is None:
            continue
        if not _has_information_label(
            updated_known_information,
            label,
            value_key="value",
        ):
            updated_known_information.append(
                {
                    "label": label,
                    "value": value,
                }
            )
        updated_pending_confirmation = [
            item
            for item in updated_pending_confirmation
            if item.get("label") != label
        ]

    return updated_known_information, updated_pending_confirmation


def _build_user_fact_source_text(
    *,
    user_input: str,
    conversation_history_text: str | None,
) -> str:
    user_lines: list[str] = []
    if conversation_history_text is not None:
        for raw_line in conversation_history_text.splitlines():
            line = raw_line.strip()
            lowered = line.lower()
            if lowered.startswith("user:"):
                user_lines.append(line[5:].strip())

    user_lines.append(user_input.strip())
    return "\n".join(line for line in user_lines if line)


def _extract_explicit_deadline_hint(user_input: str) -> str | None:
    normalized_input = user_input.strip().replace(" ", "")
    if not normalized_input:
        return None

    days_match = re.search(r"(\d+)天內", normalized_input)
    if days_match:
        return f"{days_match.group(1)}天內"

    week_match = re.search(r"([0-9一二兩三四五六七八九十]+)(?:個)?(?:週|周|星期)(後|內)", normalized_input)
    if week_match:
        return f"{week_match.group(1)}週{week_match.group(2)}"

    if "後天" in normalized_input:
        return "後天"
    if "明天" in normalized_input:
        return "明天"
    if "今天" in normalized_input:
        return "今天"
    if "下週" in normalized_input or "下周" in normalized_input:
        return "下週"

    return None


def _extract_explicit_time_budget(user_input: str) -> str | None:
    normalized_input = user_input.strip().replace(" ", "")
    if not normalized_input:
        return None

    daily_match = re.search(
        r"(?:每天|每日|一天|平均一天)(?:可|可以|能|大約|大概|約|平均|投入|可投入)*([0-9一二兩三四五六七八九十]+)(?:個)?小時",
        normalized_input,
    )
    if daily_match:
        return f"一天{daily_match.group(1)}小時"

    weekly_match = re.search(
        r"(?:每週|每周|一週|一周)(?:可|可以|能|大約|大概|約|平均|投入|可投入)*([0-9一二兩三四五六七八九十]+)(?:個)?小時",
        normalized_input,
    )
    if weekly_match:
        return f"每週{weekly_match.group(1)}小時"

    return None


def _has_information_label(
    items: list[dict[str, Any]],
    label: str,
    *,
    value_key: str,
) -> bool:
    for item in items:
        if item.get("label") != label:
            continue
        value = item.get(value_key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _collect_information_list(value: Any) -> list[dict[str, Any]]:
    """收集 AI 回傳列表中可直接承接的 dict 項目。"""

    if not isinstance(value, list):
        return []

    collected_items: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            collected_items.append(item)

    return collected_items


def _extract_last_context_engineering_json_object(
    text_output: str,
) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
    else:
        if isinstance(parsed_output, dict) and _looks_like_context_engineering_output(
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
        if _looks_like_context_engineering_output(candidate):
            return candidate

    return None
