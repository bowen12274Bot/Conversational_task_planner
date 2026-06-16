from typing import Any

from app.schemas import ChatModuleInput, ModuleToAIRequest


TASK_TYPE = "structured_output"
GROUP_NAME = "chat"
CAPABILITY_LEVEL = "default"


def build_chat_ai_request(chat_input: ChatModuleInput) -> ModuleToAIRequest:
    """建立 Chat Module 專用的 AI 請求資料。"""

    prompt_spec = build_chat_prompt_spec(chat_input)

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_chat_prompt_spec(chat_input: ChatModuleInput) -> dict[str, Any]:
    """整理 Chat Module 任務的 prompt 規格。"""

    raw_requirement = chat_input.raw_requirement.strip()
    requirement_context = chat_input.requirement_context.strip()
    if not raw_requirement:
        raise ValueError("raw_requirement 不可為空白。")
    if not requirement_context:
        raise ValueError("requirement_context 不可為空白。")

    return {
        "input_data": {
            "role": _build_role_text(),
            "task": _build_task_text(),
            "context": {
                "raw_requirement": raw_requirement,
                "requirement_context": requirement_context,
                "planning_intent": chat_input.planning_intent.model_dump(),
                "known_information": chat_input.known_information,
                "pending_confirmation": chat_input.pending_confirmation,
                "conversation_history_text": chat_input.conversation_history_text,
                "existing_plan_outline": chat_input.existing_plan_outline,
                "structured_task_output": chat_input.structured_task_output,
            },
            "examples": _build_examples(),
            "output_target": _build_output_target(),
        },
        "format_requirements": _build_format_requirements(),
    }


def _build_role_text() -> str:
    return (
        "You are a planning chat assistant. "
        "Answer the user's planning-related question based on the provided context and existing plan."
    )


def _build_task_text() -> str:
    return (
        "Use the current raw_requirement as the main question. "
        "Use existing plan data as context when it is relevant. "
        "If the user asks how to execute, understand, evaluate, or find resources for a plan item, answer directly. "
        "If you mention possible next actions, present them as suggestions only. "
        "Do not claim that an action was performed in the system. "
        "Use Traditional Chinese for user-facing text. "
        "Return one valid JSON object only."
    )


def _build_output_target() -> str:
    return (
        "Return one JSON object containing answer_types, answer, referenced_plan, "
        "and suggested_follow_up_actions."
    )


def _build_examples() -> list[dict[str, Any]]:
    return [
        {
            "input": {
                "raw_requirement": "第三階段的模擬試題有沒有什麼練習方向呢，或是有沒有什麼學習管道可以參考呢",
                "planning_intent": {
                    "intent_type": "chat",
                    "target_main_task_order": 3,
                    "confidence": "high",
                },
                "existing_plan_outline": [
                    {"order": 1, "title": "第一階段：基礎建立期"},
                    {"order": 2, "title": "第二階段：題型強化期"},
                    {"order": 3, "title": "第三階段：實戰衝刺期"},
                ],
            },
            "output": {
                "answer_types": ["execution_advice", "resource_suggestion"],
                "answer": (
                    "第三階段的模擬試題練習可以先以限時完整模考為主，"
                    "再把錯題分成聽力理解、閱讀速度、單字文法與時間分配幾類，"
                    "最後針對最高頻錯誤安排回補練習。學習管道可先找官方範例題、"
                    "模擬試題書與可計時的線上題庫。"
                ),
                "referenced_plan": {
                    "main_task_order": 3,
                    "subtask_orders": [],
                },
                "suggested_follow_up_actions": [
                    {
                        "action_type": "revise_plan",
                        "label": "將這些練習方向加入第三階段",
                    }
                ],
            },
        }
    ]


def _build_format_requirements() -> dict[str, Any]:
    return {
        "output_type": "json_object",
        "required_fields": [
            "answer_types",
            "answer",
            "referenced_plan",
            "suggested_follow_up_actions",
        ],
        "requirements": [
            "answer_types must be a list containing 1 to 3 values.",
            "Each answer_types item must be one of plan_explanation, execution_advice, resource_suggestion, risk_analysis, or general_answer.",
            "answer must be a non-empty Traditional Chinese string.",
            "referenced_plan must be an object or null.",
            "referenced_plan.main_task_order must match the target main task when the question clearly references one.",
            "referenced_plan.subtask_orders must be a list of strings.",
            "suggested_follow_up_actions must be a list of objects.",
            "Each suggested_follow_up_actions item must contain action_type and label.",
            "action_type must be revise_plan or ask_more.",
            "Return exactly one JSON object and nothing else.",
        ],
    }
