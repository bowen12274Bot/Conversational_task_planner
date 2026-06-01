from typing import Any

from app.schemas import ModuleToAIRequest, PlanningResponseInput, QuestioningDecision


TASK_TYPE = "response_generation"
GROUP_NAME = "questioning_follow_up"
CAPABILITY_LEVEL = "default"
PLANNING_GROUP_NAME = "planning_summary"


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


def build_planning_response_ai_request(
    planning_response_input: PlanningResponseInput,
) -> ModuleToAIRequest:
    """建立規劃完成回覆專用的 AI 請求資料。"""

    prompt_spec = build_planning_response_prompt_spec(planning_response_input)

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=PLANNING_GROUP_NAME,
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
                "decision": questioning_decision.decision,
                "reasoning": reasoning,
                "known_information": questioning_decision.known_information,
                "pending_confirmation": questioning_decision.pending_confirmation,
                "next_step_guidance": questioning_decision.next_step_guidance,
            },
            "examples": _build_examples(),
            "output_target": _build_output_target(),
        },
        "format_requirements": _build_format_requirements(),
    }


def build_planning_response_prompt_spec(
    planning_response_input: PlanningResponseInput,
) -> dict[str, Any]:
    """整理規劃完成回覆任務的 prompt 規格。"""

    plan_summary = planning_response_input.plan_summary.strip()
    design_rationale = planning_response_input.design_rationale.strip()
    if not plan_summary:
        raise ValueError("planning_response_input.plan_summary 不可為空白。")
    if not design_rationale:
        raise ValueError("planning_response_input.design_rationale 不可為空白。")

    return {
        "input_data": {
            "rules": _build_planning_rules_text(),
            "task": _build_planning_task_text(),
            "context": {
                "plan_summary": plan_summary,
                "design_rationale": design_rationale,
                "structured_task_output": planning_response_input.structured_task_output.model_dump(),
            },
            "examples": _build_planning_examples(),
            "output_target": _build_planning_output_target(),
        },
        "format_requirements": _build_planning_format_requirements(),
    }


def _build_rules_text() -> str:
    return (
        "You are a helpful planning assistant. "
        "Write in natural Traditional Chinese used in Taiwan. "
        "Do not invent new missing-information questions beyond the provided pending_confirmation list. "
        "Output only the final user-facing follow-up reply. "
        "Do not output analysis, draft notes, bullet points, markdown, or quotation wrappers."
    )


def _build_task_text() -> str:
    return (
        "Generate a short follow-up reply for the user. "
        "First explain briefly why more information is needed, then ask one or two key follow-up questions. "
        "Return only the final reply sentence block in Traditional Chinese."
    )


def _build_output_target() -> str:
    return "Return one short natural-language follow-up reply in Traditional Chinese."


def _build_examples() -> list[dict[str, str]]:
    return [
        {
            "input_summary": (
                "reasoning: 目前需求是希望在7天內完成Java作業。"
                "但目前仍缺少目前進度、可投入時間。 "
                "next_step_guidance: 目前作業已經完成到哪裡？ 每天大約可以投入多少時間？"
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
            "Do not output analysis, drafts, bullet points, or any extra text before the final reply.",
        ],
    }


def _build_planning_rules_text() -> str:
    return (
        "You are a helpful planning assistant. "
        "Write in natural Traditional Chinese used in Taiwan. "
        "The detailed schedule is already shown in the planning panel, so do not restate the full task list. "
        "Use plan_summary as the main source of the reply, and use design_rationale only to add a brief explanation when needed. "
        "Treat structured_task_output as supporting context so that the reply stays aligned with the planning panel. "
        "Output only the final user-facing reply. "
        "Do not output JSON, markdown, bullet points, analysis, draft notes, or quotation wrappers."
    )


def _build_planning_task_text() -> str:
    return (
        "Generate one short planning-completion reply for the chat area. "
        "Briefly tell the user that an initial plan has been prepared and guide them to review the planning panel. "
        "If appropriate, add one brief sentence explaining the overall arrangement direction. "
        "Return only the final reply in Traditional Chinese."
    )


def _build_planning_output_target() -> str:
    return "Return one short natural-language planning summary reply in Traditional Chinese."


def _build_planning_examples() -> list[dict[str, str]]:
    return [
        {
            "input_summary": (
                "plan_summary: 已完成一版初步規劃，內容包含需求確認、核心功能實作與最後測試收尾。 "
                "design_rationale: 由於期限明確且目前尚未開始，因此先安排需求確認與核心功能，再保留最後測試時間。"
            ),
            "output_example": (
                "我先根據目前資訊整理出一版初步規劃，已經放在右側規劃面板。這版安排會先從需求確認與核心功能開始，並保留最後的測試與整理時間。"
            ),
        }
    ]


def _build_planning_format_requirements() -> dict[str, Any]:
    return {
        "output_type": "plain_text",
        "requirements": [
            "Use Traditional Chinese.",
            "Keep the reply concise and natural.",
            "Output plain text only.",
            "Do not output JSON or markdown.",
            "Do not output analysis, drafts, bullet points, or any extra text before the final reply.",
            "Do not restate the full task list already shown in the planning panel.",
        ],
    }
