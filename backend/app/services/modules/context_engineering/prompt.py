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
    existing_plan_outline: list[dict[str, Any]] | None = None,
) -> ModuleToAIRequest:
    """建立 Context Engineering 專用的 AI 請求資料。"""

    prompt_spec = build_context_engineering_prompt_spec(
        user_input=user_input,
        conversation_history_text=conversation_history_text,
        existing_plan_outline=existing_plan_outline,
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
    existing_plan_outline: list[dict[str, Any]] | None = None,
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
        existing_plan_outline=existing_plan_outline,
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
            "planning_intent",
        ],
        "requirements": [
            "requirement_context must be a concise string summary of the current requirement and current situation.",
            "known_information must be a list of objects containing only information clearly supported by the current raw requirement or prior user messages that are still relevant.",
            "pending_confirmation must be a list of objects for important missing, unclear, or conflicting information that should be clarified later.",
            "planning_intent must be an object containing intent_type, target_main_task_order, and confidence.",
            "planning_intent.intent_type must be one of create, revise, or other.",
            "planning_intent.target_main_task_order must be a positive integer when the current request clearly targets one existing main task; otherwise use null.",
            "planning_intent.confidence must be one of high, medium, or low.",
            "Use label and value for each known_information item.",
            "Use label and question_hint for each pending_confirmation item.",
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
        "Use prior conversation history to help interpret the current turn and preserve relevant known_information and pending_confirmation continuity. "
        "If an existing plan outline is provided, use it only to identify whether the current turn appears to create a new plan, revise an existing plan, or do something else. "
        "When deciding confirmed information, prioritize content clearly supported by user messages, "
        "and treat prior AI replies as contextual references rather than independent confirmed facts. "
        "Do not decide whether to ask follow-up questions; only organize the observable information and planning intent. "
        "Do not invent deadlines, progress, or constraints that were not stated."
    )


def _build_task_description() -> str:
    """建立任務層文字。"""

    return (
        "Read the current raw requirement together with the prior conversation history, "
        "then build a refreshed requirement_context, known_information, pending_confirmation, and planning_intent for this turn. "
        "If prior user-provided facts are still relevant and not contradicted, explicitly keep them in known_information for the current turn instead of dropping them. "
        "When a previous user message has already established task type, deadline, time budget, progress, difficulty, or constraint information and the current turn does not replace or conflict with it, preserve that information in known_information while adding the new details from the current turn. "
        "Set planning_intent.intent_type to create when the user appears to request a new plan, revise when the user appears to refine or change an existing plan, and other when the current turn is not a planning creation or revision request. "
        "When intent_type is revise, set target_main_task_order only if the current turn clearly points to one item from existing_plan_outline. "
        "If the current raw requirement clearly corrects or updates prior information, use the current raw requirement as the new source of truth. "
        "If the current raw requirement conflicts with prior history but the correction is unclear, do not force a resolution; "
        "move the conflicting item into pending_confirmation instead."
    )


def _build_context_data(
    user_input: str,
    conversation_history_text: str | None = None,
    existing_plan_outline: list[dict[str, Any]] | None = None,
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

    if existing_plan_outline:
        sections.extend(
            [
                "",
                "Existing plan outline:",
                _format_existing_plan_outline(existing_plan_outline),
            ]
        )

    return "\n".join(sections)


def _format_existing_plan_outline(existing_plan_outline: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in existing_plan_outline:
        order = item.get("order")
        title = item.get("title")
        description = item.get("description")
        if not isinstance(order, int) or not isinstance(title, str) or not title.strip():
            continue
        line = f"{order}. {title.strip()}"
        if isinstance(description, str) and description.strip():
            line = f"{line} - {description.strip()}"
        lines.append(line)

    return "\n".join(lines)


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
                "planning_intent": {
                    "intent_type": "create",
                    "target_main_task_order": None,
                    "confidence": "high",
                },
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
                "planning_intent": {
                    "intent_type": "create",
                    "target_main_task_order": None,
                    "confidence": "medium",
                },
            },
        },
        {
            "input": (
                "Current raw requirement:\n"
                "已經完成系統架構了，但是模組間的API清單和資料契約還沒決定好。\n\n"
                "Conversation history:\n"
                "User: 我要在7天內完成Java作業，我一天只能做2小時。\n"
                "AI: 為了幫你規劃合適的安排，我想先了解一下目前這份 Java 作業已經完成到哪裡了呢？\n"
                "User: 已經完成系統架構了，但是模組間的API清單和資料契約還沒決定好。"
            ),
            "output": {
                "requirement_context": (
                    "使用者想在7天內完成Java作業，每天可投入2小時；"
                    "目前已完成系統架構，但模組間的API清單與資料契約仍未決定。"
                ),
                "known_information": [
                    {
                        "label": "task_type",
                        "value": "Java作業",
                    },
                    {
                        "label": "deadline_hint",
                        "value": "7天內",
                    },
                    {
                        "label": "time_budget",
                        "value": "一天2小時",
                    },
                    {
                        "label": "current_progress",
                        "value": "已完成系統架構",
                    },
                    {
                        "label": "constraint",
                        "value": "模組間的API清單和資料契約還沒決定好",
                    },
                ],
                "pending_confirmation": [],
                "planning_intent": {
                    "intent_type": "create",
                    "target_main_task_order": None,
                    "confidence": "high",
                },
            },
        },
        {
            "input": (
                "Current raw requirement:\n"
                "請問第一階段時可以針對哪些情境練習，以及有沒有甚麼管道能學習\n\n"
                "Existing plan outline:\n"
                "1. 第一階段情境重點規劃 - 鎖定多益高頻生活與商務情境。\n"
                "2. 學習管道與工具建議 - 提供每日可用的學習管道。\n"
                "3. 題型突破與模擬練習 - 安排考題訓練。"
            ),
            "output": {
                "requirement_context": (
                    "使用者希望細化既有規劃中的第一階段，補充可練習的情境與學習管道。"
                ),
                "known_information": [
                    {
                        "label": "constraint",
                        "value": "修改目標為既有規劃的第一階段",
                    }
                ],
                "pending_confirmation": [],
                "planning_intent": {
                    "intent_type": "revise",
                    "target_main_task_order": 1,
                    "confidence": "high",
                },
            },
        },
    ]
