from typing import Any

from app.schemas import ModuleToAIRequest
from app.services.modules.shared.requirement_labels import ALLOWED_REQUIREMENT_LABELS


TASK_TYPE = "structured_output"
GROUP_NAME = "questioning_decision"
CAPABILITY_LEVEL = "strong"


def build_questioning_ai_request(
    *,
    requirement_context: str,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
    follow_up_round_count: int,
) -> ModuleToAIRequest:
    """建立 Questioning Module 專用的 AI 請求資料。"""

    prompt_spec = build_questioning_prompt_spec(
        requirement_context=requirement_context,
        known_information=known_information,
        pending_confirmation=pending_confirmation,
        follow_up_round_count=follow_up_round_count,
    )

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_questioning_prompt_spec(
    *,
    requirement_context: str,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
    follow_up_round_count: int,
) -> dict[str, Any]:
    normalized_context = requirement_context.strip()
    if not normalized_context:
        raise ValueError("requirement_context 不可為空白。")

    if follow_up_round_count < 0:
        raise ValueError("follow_up_round_count 不可為負數。")

    return {
        "input_data": {
            "rules": _build_rules_text(),
            "task": _build_task_text(),
            "context": {
                "requirement_context": normalized_context,
                "known_information": known_information,
                "pending_confirmation": pending_confirmation,
                "follow_up_round_count": follow_up_round_count,
            },
            "examples": _build_examples(),
            "output_target": _build_output_target(),
        },
        "format_requirements": _build_format_requirements(),
    }


def _build_rules_text() -> str:
    return (
        "You are a pre-planning decision assistant. "
        "Your job is to decide whether the next step should be follow_up or planning. "
        "Your response must be one raw JSON object only. "
        "Do not output analysis, reasoning steps, bullet points, markdown, code fences, labels, or any text before or after the JSON object. "
        "Do not restate the input. "
        "Share the same requirement labels as the Context Engineering Module. "
        "Treat task_type and deadline_hint as the minimum planning basis. "
        "Treat current_progress, time_budget, difficulty, and constraint as contextual signals rather than always-required items. "
        "Do not ask follow-up questions just to maximize completeness. "
        "Ask follow-up questions only when the missing information would significantly affect planning direction or planning quality. "
        "If the current information is sufficient for a reasonable initial plan, allow planning and explain the remaining uncertainty in reasoning. "
        "If follow_up_round_count is already greater than 2, avoid continued follow-up unless the unresolved issue would make planning direction clearly unreliable."
    )


def _build_task_text() -> str:
    return (
        "Read requirement_context, known_information, pending_confirmation, and follow_up_round_count. "
        "Decide whether the next action should be follow_up or planning. "
        "If follow_up is needed, provide a small number of high-value next-step questions. "
        "If planning is appropriate, explain why the current information is sufficient for initial planning and describe how the remaining uncertainty may be handled conservatively. "
        "Return the final answer directly as one valid JSON object without any additional commentary."
    )


def _build_output_target() -> str:
    return (
        "Return one JSON object containing decision, reasoning, known_information, "
        "pending_confirmation, and next_step_guidance. "
        "The output must start with '{' and end with '}'."
    )


def _build_examples() -> list[dict[str, Any]]:
    return [
        {
            "input": {
                "requirement_context": "使用者希望系統協助安排任務，但目前尚未提供明確期限。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"}
                ],
                "pending_confirmation": [
                    {
                        "label": "deadline_hint",
                        "question_hint": "預計什麼時候要完成？",
                    }
                ],
                "follow_up_round_count": 0,
            },
            "output": {
                "decision": "follow_up",
                "reasoning": "目前任務內容已知，但期限尚未明確，最小規劃基礎尚未成立，因此應先追問。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"}
                ],
                "pending_confirmation": [
                    {
                        "label": "deadline_hint",
                        "question_hint": "預計什麼時候要完成？",
                    }
                ],
                "next_step_guidance": [
                    "預計什麼時候要完成這份 Java 作業？"
                ],
            },
        },
        {
            "input": {
                "requirement_context": "使用者希望在 7 天內完成 Java 作業，目前主任務與期限已明確。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                ],
                "pending_confirmation": [
                    {
                        "label": "time_budget",
                        "question_hint": "每天大約可投入多少時間？",
                    }
                ],
                "follow_up_round_count": 1,
            },
            "output": {
                "decision": "planning",
                "reasoning": "目前任務內容與期限已足以形成初步規劃，剩餘缺口主要影響規劃精度，因此可先進入規劃。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                ],
                "pending_confirmation": [
                    {
                        "label": "time_budget",
                        "question_hint": "每天大約可投入多少時間？",
                    }
                ],
                "next_step_guidance": [
                    "可先依保守投入時間進行初步規劃，後續若補充每日可投入時間，再調整安排。"
                ],
            },
        },
        {
            "input": {
                "requirement_context": "使用者希望在 3 天內完成資料庫期末報告，但目前尚不清楚已完成到哪個階段。",
                "known_information": [
                    {"label": "task_type", "value": "資料庫期末報告"},
                    {"label": "deadline_hint", "value": "3 天內"},
                ],
                "pending_confirmation": [
                    {
                        "label": "current_progress",
                        "question_hint": "目前已經完成到哪裡？",
                    }
                ],
                "follow_up_round_count": 0,
            },
            "output": {
                "decision": "follow_up",
                "reasoning": "雖然任務內容與期限已知，但目前進度會明顯影響接下來的安排方式，因此應先追問。",
                "known_information": [
                    {"label": "task_type", "value": "資料庫期末報告"},
                    {"label": "deadline_hint", "value": "3 天內"},
                ],
                "pending_confirmation": [
                    {
                        "label": "current_progress",
                        "question_hint": "目前已經完成到哪裡？",
                    }
                ],
                "next_step_guidance": [
                    "目前這份資料庫期末報告已經完成到哪個階段？"
                ],
            },
        },
        {
            "input": {
                "requirement_context": "使用者希望在 7 天內完成 Java 作業，但目前需求描述仍偏粗略，尚不清楚作業是剛開始還是已進行一部分。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                ],
                "pending_confirmation": [],
                "follow_up_round_count": 0,
            },
            "output": {
                "decision": "follow_up",
                "reasoning": "雖然目前沒有顯式待確認項目，但現有情境下進度資訊很可能明顯影響規劃安排，因此仍值得先追問。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                ],
                "pending_confirmation": [],
                "next_step_guidance": [
                    "目前這份 Java 作業已經完成到哪裡？"
                ],
            },
        },
    ]


def _build_format_requirements() -> dict[str, Any]:
    return {
        "output_type": "json_object",
        "required_fields": [
            "decision",
            "reasoning",
            "known_information",
            "pending_confirmation",
            "next_step_guidance",
        ],
        "requirements": [
            "decision must be either 'follow_up' or 'planning'.",
            "reasoning must be a concise Traditional Chinese explanation.",
            "known_information must be a list of objects.",
            "pending_confirmation must be a list of objects.",
            "next_step_guidance must be a list of Traditional Chinese strings.",
            "Use only requirement labels from the allowed set.",
            "Return exactly one JSON object and nothing else.",
            "Do not output analysis, thinking process, bullet points, markdown, or code fences.",
            "Do not output any extra text outside the JSON object.",
        ],
        "allowed_labels": {
            "values": list(ALLOWED_REQUIREMENT_LABELS),
            "guidance": "Use only labels from this allowed set.",
        },
    }
