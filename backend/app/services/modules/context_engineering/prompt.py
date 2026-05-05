from typing import Any

from app.schemas import ModuleToAIRequest


TASK_TYPE = "context_engineering"
GROUP_NAME = "conversation_flow"
CAPABILITY_LEVEL = "default"


def build_context_engineering_ai_request(user_input: str) -> ModuleToAIRequest:
    """建立 Context Engineering 專用的 AI 請求資料。"""

    prompt_spec = build_context_engineering_prompt_spec(user_input)

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_context_engineering_prompt_spec(user_input: str) -> dict[str, Any]:
    """整理 Context Engineering 任務的 prompt 規格。"""

    normalized_input = user_input.strip()
    if not normalized_input:
        raise ValueError("user_input 不可為空白。")

    rules = _build_rules_text()
    task = _build_task_description()
    context = _build_context_data(normalized_input)
    examples = _build_examples()
    output_target = _build_output_target()

    return {
        "input_data": _build_input_data(
            rules=rules,
            task=task,
            context=context,
            examples=examples,
            output_target=output_target,
        ),
        "format_requirements": _build_format_requirements(),
    }


def _build_input_data(
    rules: str,
    task: str,
    context: dict[str, Any],
    examples: list[dict[str, Any]],
    output_target: str,
) -> dict[str, Any]:
    """建立 Context Engineering 任務使用的輸入資料。"""

    return {
        "rules": rules,
        "task": task,
        "context": context,
        "examples": examples,
        "output_target": output_target,
    }


def _build_output_target() -> str:
    """建立本任務的輸出目標描述。"""

    return (
        "Analyze the user's raw requirement and organize it into "
        "requirement_context, known_information, and pending_confirmation."
    )


def _build_format_requirements() -> dict[str, Any]:
    """建立本任務的格式要求。"""

    return {
        "output_type": "json_object",
        "required_fields": [
            "requirement_context",
            "known_information",
            "pending_confirmation",
        ],
        "requirements": [
            "requirement_context must be a concise string summary of the user's requirement.",
            "known_information must be a list of objects containing only information clearly supported by the user's input.",
            "pending_confirmation must be a list of objects for important missing or unclear information that should be clarified later.",
            "Use label and value for each known_information item.",
            "Use label and question_hint for each pending_confirmation item.",
            "Do not invent deadlines, progress, constraints, or difficulties that were not stated by the user.",
            "Return an empty list when there is no suitable item for known_information or pending_confirmation.",
        ],
        "allowed_labels": {
            "recommended": [
                "task_type",
                "deadline_hint",
                "current_progress",
                "time_budget",
                "difficulty",
                "constraint",
            ],
            "guidance": (
                "Use these labels when they fit the user's input. "
                "If none fit well, you may create a short snake_case label "
                "that clearly describes the information."
            ),
        },
    }


def _build_rules_text() -> str:
    """建立規則層文字。"""

    return (
        "You are a requirement analysis assistant. "
        "Only extract information that is supported by the user's input. "
        "Do not invent deadlines, progress, or constraints that were not stated."
    )


def _build_task_description() -> str:
    """建立任務層文字。"""

    return (
        "Read the user's raw requirement and organize it into a concise "
        "requirement_context, a list of known_information, and a list of "
        "pending_confirmation items that matter for later questioning and planning."
    )


def _build_context_data(user_input: str) -> dict[str, Any]:
    """建立上下文層資料。"""

    return {
        "raw_requirement": user_input,
    }


def _build_examples() -> list[dict[str, Any]]:
    """建立範例層資料。"""

    return [
        {
            "input": {
                "raw_requirement": "我要準備下週的資料庫期末報告，但還不知道怎麼拆工作。"
            },
            "output": {
                "requirement_context": "使用者需要準備下週的資料庫期末報告，且目前尚未完成工作拆解。",
                "known_information": [
                    {
                        "label": "task_type",
                        "value": "資料庫期末報告",
                    },
                    {
                        "label": "deadline_hint",
                        "value": "下週",
                    },
                ],
                "pending_confirmation": [
                    {
                        "label": "current_progress",
                        "question_hint": "目前已經完成到哪裡",
                    },
                    {
                        "label": "time_budget",
                        "question_hint": "每天大約可投入多少時間",
                    },
                ],
            },
        }
    ]
