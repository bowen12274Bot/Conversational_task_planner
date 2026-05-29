from typing import Any

from app.schemas import ModuleToAIRequest
from app.services.modules.shared.requirement_labels import (
    ALLOWED_REQUIREMENT_LABELS,
)


TASK_TYPE = "context_engineering"
GROUP_NAME = "conversation_flow"
CAPABILITY_LEVEL = "default"


def build_context_engineering_ai_request(
    user_input: str,
    conversation_history_text: str | None = None,
) -> ModuleToAIRequest:
    """建立 Context Engineering 專用的 AI 請求資料。"""

    prompt_spec = build_context_engineering_prompt_spec(
        user_input=user_input,
        conversation_history_text=conversation_history_text,
    )

    return ModuleToAIRequest(
        task_type=TASK_TYPE,
        group_name=GROUP_NAME,
        capability_level=CAPABILITY_LEVEL,
        input_data=prompt_spec["input_data"],
        format_requirements=prompt_spec["format_requirements"],
    )


def build_context_engineering_prompt_spec(
    user_input: str,
    conversation_history_text: str | None = None,
) -> dict[str, Any]:
    """整理 Context Engineering 任務的 prompt 規格。"""

    normalized_input = user_input.strip()
    if not normalized_input:
        raise ValueError("user_input 不可為空白。")

    rules = _build_rules_text()
    task = _build_task_description()
    context = _build_context_data(
        user_input=normalized_input,
        conversation_history_text=conversation_history_text,
    )
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
    context: str,
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
        "requirement_context, known_information, and pending_confirmation "
        "for the current turn."
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
            "requirement_context must be a concise string summary of the current requirement and current situation.",
            "known_information must be a list of objects containing only information clearly supported by the current raw requirement or prior user messages that are still relevant.",
            "pending_confirmation must be a list of objects for important missing, unclear, or conflicting information that should be clarified later.",
            "If prior user-provided information is still relevant and not contradicted, carry it forward into the refreshed result.",
            "If the current raw requirement clearly corrects or updates prior information, update known_information accordingly.",
            "If the current raw requirement conflicts with prior history but the correction is unclear, place the conflicting item in pending_confirmation instead of treating it as confirmed.",
            "If a previously missing or uncertain item is now clearly supported by the current raw requirement or prior user messages, move it into known_information.",
            "Use label and value for each known_information item.",
            "Use label and question_hint for each pending_confirmation item.",
            "Do not treat prior AI replies as confirmed facts unless they are clearly supported by user messages.",
            "Do not invent deadlines, progress, constraints, or difficulties that were not stated by the user.",
            "Return an empty list when there is no suitable item for known_information or pending_confirmation.",
        ],
        "allowed_labels": {
            "values": list(ALLOWED_REQUIREMENT_LABELS),
            "guidance": (
                "You must use only labels from this allowed set. "
                "Do not create new labels."
            ),
        },
    }


def _build_rules_text() -> str:
    """建立規則層文字。"""

    return (
        "You are a requirement analysis assistant. "
        "Use the current raw requirement as the primary input for this turn. "
        "Use prior conversation history as supporting context only. "
        "Only extract information supported by user-provided content. "
        "Do not treat prior AI replies as confirmed facts unless they are clearly supported by user messages. "
        "Do not invent deadlines, progress, or constraints that were not stated."
    )


def _build_task_description() -> str:
    """建立任務層文字。"""

    return (
        "Read the current raw requirement together with the prior conversation history, "
        "then build a refreshed requirement_context, known_information, and pending_confirmation for this turn. "
        "If prior user-provided facts are still relevant and not contradicted, carry them forward. "
        "If the current raw requirement clearly corrects or updates prior information, use the current raw requirement as the new source of truth. "
        "If the current raw requirement conflicts with prior history but the correction is unclear, do not force a resolution; "
        "move the conflicting item into pending_confirmation instead."
    )


def _build_context_data(
    user_input: str,
    conversation_history_text: str | None = None,
) -> str:
    """建立上下文層資料。"""

    sections = [
        "Current raw requirement:",
        user_input,
    ]
    if conversation_history_text is not None and conversation_history_text.strip():
        sections.extend(
            [
                "",
                "Conversation history:",
                _normalize_conversation_history_text(conversation_history_text),
            ]
        )

    return "\n".join(sections)


def _normalize_conversation_history_text(conversation_history_text: str) -> str:
    """將 transcript 角色前綴整理為較自然的 prompt 顯示格式。"""

    normalized_lines: list[str] = []
    for raw_line in conversation_history_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("user:"):
            normalized_lines.append(f"User:{line[5:]}")
            continue

        if line.startswith("ai:"):
            normalized_lines.append(f"AI:{line[3:]}")
            continue

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


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
        },
        {
            "input": (
                "Current raw requirement:\n"
                "我剩一天。\n\n"
                "Conversation history:\n"
                "User: 我要準備下週的資料庫期末報告。"
            ),
            "output": {
                "requirement_context": (
                    "使用者需要準備資料庫期末報告，但目前期限資訊存在不明確衝突。"
                ),
                "known_information": [
                    {
                        "label": "task_type",
                        "value": "資料庫期末報告",
                    }
                ],
                "pending_confirmation": [
                    {
                        "label": "deadline_hint",
                        "question_hint": "實際期限是下週，還是只剩一天",
                    }
                ],
            },
        },
    ]
