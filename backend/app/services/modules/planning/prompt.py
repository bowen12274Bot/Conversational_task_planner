from typing import Any

from app.schemas import ModuleToAIRequest
from app.services.modules.shared.requirement_labels import ALLOWED_REQUIREMENT_LABELS


TASK_TYPE = "structured_output"
GROUP_NAME = "planning_create"
CAPABILITY_LEVEL = "strong"


def build_planning_create_ai_request(
    *,
    requirement_context: str,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
    conversation_history_text: str | None,
) -> ModuleToAIRequest:
    prompt_spec = build_planning_create_prompt_spec(
        requirement_context=requirement_context,
        known_information=known_information,
        pending_confirmation=pending_confirmation,
        conversation_history_text=conversation_history_text,
    )

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_planning_create_prompt_spec(
    *,
    requirement_context: str,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
    conversation_history_text: str | None,
) -> dict[str, Any]:
    normalized_context = requirement_context.strip()
    if not normalized_context:
        raise ValueError("requirement_context 不可為空白。")

    return {
        "input_data": {
            "rules": _build_rules_text(),
            "task": _build_task_text(),
            "context": {
                "requirement_context": normalized_context,
                "known_information": known_information,
                "pending_confirmation": pending_confirmation,
                "conversation_history_text": conversation_history_text,
            },
            "examples": _build_examples(),
            "output_target": _build_output_target(),
        },
        "format_requirements": _build_format_requirements(),
    }


def _build_rules_text() -> str:
    return (
        "You are an initial task-planning assistant. "
        "Your job is to produce an initial structured plan from the current requirement context, known information, pending confirmation items, and optional conversation history. "
        "Your response must be one raw JSON object only. "
        "Do not output analysis, reasoning steps, bullet points, markdown, code fences, labels, or any text before or after the JSON object. "
        "Do not restate the input. "
        "Prioritize known_information as confirmed planning facts. "
        "Treat pending_confirmation only as unresolved gaps and not as confirmed facts. "
        "If the plan still requires assumptions, keep them conservative and list them explicitly in assumptions_used. "
        "If deadline_hint and time_budget are both available, estimate the user's available work capacity and keep the total schedule within that capacity. "
        "Do not produce a plan whose total estimated effort clearly exceeds the user's available time. "
        "If the available time appears insufficient, reduce scope conservatively and explain that limitation in design_rationale or assumptions_used. "
        "Do not invent deadlines, progress, constraints, or task details that are not reasonably supported by the input."
    )


def _build_task_text() -> str:
    return (
        "Generate an initial plan. "
        "Return plan_summary, design_rationale, assumptions_used, and schedule. "
        "schedule must contain main_tasks, and each main task must contain subtasks. "
        "Prefer a feasible plan over an over-complete plan when time is limited. "
        "Use Traditional Chinese for all user-facing text fields. "
        "Return the final answer directly as one valid JSON object without any additional commentary."
    )


def _build_output_target() -> str:
    return (
        "Return one JSON object containing plan_summary, design_rationale, assumptions_used, and schedule. "
        "The output must start with '{' and end with '}'."
    )


def _build_examples() -> list[dict[str, Any]]:
    return [
        {
            "input": {
                "requirement_context": "使用者希望在 7 天內完成 Java 作業，目前尚未開始。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                    {"label": "current_progress", "value": "尚未開始"},
                ],
                "pending_confirmation": [
                    {
                        "label": "time_budget",
                        "question_hint": "每天大約可投入多少時間？",
                    }
                ],
                "conversation_history_text": None,
            },
            "output": {
                "plan_summary": "先確認作業要求，再完成核心功能，最後安排測試與修正。",
                "design_rationale": "由於使用者尚未開始，且期限明確，因此先將需求理解與核心實作排在前段，再預留最後的修正時間。",
                "assumptions_used": [
                    "每日可投入時間尚未明確，因此先依一般有限時段投入進行初步安排。"
                ],
                "schedule": {
                    "main_tasks": [
                        {
                            "title": "確認作業需求與交付內容",
                            "description": "整理題目要求、輸入輸出格式與評分重點。",
                            "estimated_time": "1-2h",
                            "order": 1,
                            "subtasks": [
                                {
                                    "title": "閱讀題目說明",
                                    "description": "確認題目要求與限制。",
                                    "priority": "high",
                                    "estimated_time": "30m",
                                    "order": 1,
                                }
                            ],
                        }
                    ]
                },
            },
        },
        {
            "input": {
                "requirement_context": "使用者希望在 7 天內完成 Java 作業，每天可投入 2 小時，目前尚未開始。",
                "known_information": [
                    {"label": "task_type", "value": "Java 作業"},
                    {"label": "deadline_hint", "value": "7 天內"},
                    {"label": "time_budget", "value": "每天 2 小時"},
                    {"label": "current_progress", "value": "尚未開始"},
                ],
                "pending_confirmation": [],
                "conversation_history_text": None,
            },
            "output": {
                "plan_summary": "依照 7 天內、每天 2 小時的限制，先完成必要需求確認與核心功能，再安排測試與收尾。",
                "design_rationale": "已知總可投入時間約為 14 小時，因此排程以可完成的最小可行範圍為主，避免總工時明顯超出可用時間。",
                "assumptions_used": [],
                "schedule": {
                    "main_tasks": [
                        {
                            "title": "需求確認與工作切分",
                            "description": "先釐清題目要求與交付範圍，避免後續返工。",
                            "estimated_time": "2 小時",
                            "order": 1,
                            "subtasks": [
                                {
                                    "title": "閱讀題目與整理需求",
                                    "description": "確認功能需求、輸入輸出與限制條件。",
                                    "priority": "high",
                                    "estimated_time": "1 小時",
                                    "order": 1,
                                },
                                {
                                    "title": "切分功能與完成順序",
                                    "description": "整理最小可行功能與實作先後順序。",
                                    "priority": "medium",
                                    "estimated_time": "1 小時",
                                    "order": 2,
                                },
                            ],
                        },
                        {
                            "title": "核心功能實作",
                            "description": "先完成作業最核心的程式邏輯與必要介面。",
                            "estimated_time": "8 小時",
                            "order": 2,
                            "subtasks": [
                                {
                                    "title": "完成主要邏輯",
                                    "description": "撰寫核心功能與主要流程控制。",
                                    "priority": "high",
                                    "estimated_time": "5 小時",
                                    "order": 1,
                                },
                                {
                                    "title": "整合輸入輸出與必要處理",
                                    "description": "補齊輸入輸出與必要錯誤處理。",
                                    "priority": "high",
                                    "estimated_time": "3 小時",
                                    "order": 2,
                                },
                            ],
                        },
                        {
                            "title": "測試與提交準備",
                            "description": "保留時間進行測試、修正與最終檢查。",
                            "estimated_time": "4 小時",
                            "order": 3,
                            "subtasks": [
                                {
                                    "title": "基本測試與修正",
                                    "description": "檢查主要功能是否正常，修正明顯問題。",
                                    "priority": "medium",
                                    "estimated_time": "2 小時",
                                    "order": 1,
                                },
                                {
                                    "title": "整理提交內容",
                                    "description": "確認檔案完整並完成最後檢查。",
                                    "priority": "medium",
                                    "estimated_time": "2 小時",
                                    "order": 2,
                                },
                            ],
                        },
                    ]
                },
            },
        },
    ]


def _build_format_requirements() -> dict[str, Any]:
    return {
        "output_type": "json_object",
        "required_fields": [
            "plan_summary",
            "design_rationale",
            "assumptions_used",
            "schedule",
        ],
        "requirements": [
            "plan_summary must be a non-empty Traditional Chinese string.",
            "design_rationale must be a non-empty Traditional Chinese string.",
            "assumptions_used must be a list of strings.",
            "schedule must be an object containing main_tasks.",
            "main_tasks must be a list of objects.",
            "Each main_tasks item must contain title, description, estimated_time, order, and subtasks.",
            "Each subtasks item must contain title, description, priority, estimated_time, and order.",
            "priority must be one of high, medium, or low.",
            "If deadline_hint and time_budget are both available in known_information, the total estimated effort should remain feasible for that available time.",
            "Use only requirement labels from the allowed set when referring to extracted labels conceptually.",
            "Return exactly one JSON object and nothing else.",
            "Do not output analysis, thinking process, bullet points, markdown, or code fences.",
            "Do not output any extra text outside the JSON object.",
        ],
        "allowed_labels": {
            "values": list(ALLOWED_REQUIREMENT_LABELS),
            "guidance": "Use only labels from this allowed set when reasoning about extracted information.",
        },
    }
