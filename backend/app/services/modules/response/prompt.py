from typing import Any

from app.schemas import ModuleToAIRequest, QuestioningDecision


TASK_TYPE = "response_generation"
GROUP_NAME = "questioning_follow_up"
CAPABILITY_LEVEL = "default"


def build_follow_up_response_ai_request(
    questioning_decision: QuestioningDecision,
) -> ModuleToAIRequest:
    """建立追問回覆專用的 AI 請求資料。"""

    prompt_spec = build_follow_up_response_prompt_spec(questioning_decision)

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_follow_up_response_prompt_spec(
    questioning_decision: QuestioningDecision,
) -> dict[str, Any]:
    """整理追問回覆任務的 prompt 規格。"""

    reasoning = questioning_decision.reasoning.strip()
    if not reasoning:
        raise ValueError("questioning_decision.reasoning 不可為空白。")

    return {
        "input_data": {
            "rules": _build_rules_text(),
            "task": _build_task_text(),
            "context": {
                "reasoning": reasoning,
                "known_information": questioning_decision.known_information,
                "pending_confirmation": questioning_decision.pending_confirmation,
            },
            "examples": _build_examples(),
            "output_target": _build_output_target(),
        },
        "format_requirements": _build_format_requirements(),
    }


def _build_rules_text() -> str:
    return (
        "You are a helpful planning assistant. "
        "Write in natural Traditional Chinese used in Taiwan. "
        "Do not invent new missing-information questions beyond the provided pending_confirmation list."
    )


def _build_task_text() -> str:
    return (
        "Generate a short follow-up reply for the user. "
        "First explain briefly why more information is needed, then ask one or two key follow-up questions."
    )


def _build_output_target() -> str:
    return "Return one short natural-language follow-up reply in Traditional Chinese."


def _build_examples() -> list[dict[str, str]]:
    return [
        {
            "input_summary": (
                "reasoning: 目前需求是希望在7天內完成Java作業。"
                "但目前仍缺少目前進度、可投入時間。"
            ),
            "output_example": (
                "為了幫你排出比較可行的進度，我想先確認兩件事："
                "目前作業已經完成到哪裡？每天大約可以投入多少時間？"
            ),
        }
    ]


def _build_format_requirements() -> dict[str, Any]:
    return {
        "output_type": "plain_text",
        "requirements": [
            "Use Traditional Chinese.",
            "Keep the reply concise and natural.",
            "Ask at most two follow-up questions.",
            "Questions must be based on pending_confirmation.question_hint.",
            "Do not output JSON or markdown.",
        ],
    }
