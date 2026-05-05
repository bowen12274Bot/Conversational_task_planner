import json
from typing import Any

from app.schemas import AIToModuleResult, ContextEngineeringOutput
from app.services.ai_service.service import run_ai_flow
from app.services.modules.context_engineering.prompt import (
    build_context_engineering_ai_request,
)


def build_context_from_raw_input(
    user_input: str,
    history_context_summary: str | None = None,
) -> ContextEngineeringOutput:
    """將使用者原始輸入整理為後續流程可用的基礎上下文。"""

    normalized_input = user_input.strip()
    if not normalized_input:
        raise ValueError("user_input 不可為空白。")

    ai_request = build_context_engineering_ai_request(normalized_input)
    ai_result = run_ai_flow(ai_request)

    if not ai_result.success:
        return _build_fallback_context(
            user_input=normalized_input,
            history_context_summary=history_context_summary,
        )

    return _parse_context_engineering_result(
        ai_result=ai_result,
        user_input=normalized_input,
        history_context_summary=history_context_summary,
    )


def _parse_context_engineering_result(
    ai_result: AIToModuleResult,
    user_input: str,
    history_context_summary: str | None = None,
) -> ContextEngineeringOutput:
    """將 AI 回傳結果整理為 ContextEngineeringOutput。"""

    # AI service layer 先回傳通用結果，模組層再將其中內容轉成自己的業務資料形狀。
    parsed_output = _extract_context_engineering_output(ai_result.output_result)
    if parsed_output is None:
        return _build_fallback_context(
            user_input=user_input,
            history_context_summary=history_context_summary,
        )

    requirement_context = parsed_output.get("requirement_context")
    known_information = _collect_information_list(
        parsed_output.get("known_information")
    )
    pending_confirmation = _collect_information_list(
        parsed_output.get("pending_confirmation")
    )

    if not isinstance(requirement_context, str) or not requirement_context.strip():
        requirement_context = user_input

    return ContextEngineeringOutput(
        requirement_context=requirement_context.strip(),
        known_information=known_information,
        pending_confirmation=pending_confirmation,
        history_context_summary=history_context_summary,
    )


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

    try:
        parsed_output = json.loads(normalized_text)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed_output, dict):
        return None

    if not _looks_like_context_engineering_output(parsed_output):
        return None

    return parsed_output


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


def _collect_information_list(value: Any) -> list[dict[str, Any]]:
    """收集 AI 回傳列表中可直接承接的 dict 項目。"""

    if not isinstance(value, list):
        return []

    collected_items: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            collected_items.append(item)

    return collected_items


def _build_fallback_context(
    user_input: str,
    history_context_summary: str | None = None,
) -> ContextEngineeringOutput:
    """當 AI 回傳失敗或格式不符時，建立最小可用的 fallback context。"""

    return ContextEngineeringOutput(
        requirement_context=user_input,
        known_information=[],
        pending_confirmation=[],
        history_context_summary=history_context_summary,
    )
