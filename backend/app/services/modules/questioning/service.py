import json
from typing import Any, Literal, cast

from app.schemas import AIToModuleResult, ContextEngineeringOutput, QuestioningDecision
from app.services.ai_service.service import run_ai_flow
from app.services.modules.questioning.prompt import build_questioning_ai_request
from app.services.modules.questioning.validator import (
    validate_questioning_decision_output,
)


MAX_QUESTIONING_RETRY_COUNT = 3


def evaluate_questioning_need(
    context_output: ContextEngineeringOutput,
    follow_up_round_count: int,
    *,
    has_existing_plan: bool = False,
    existing_plan_outline: list[dict[str, Any]] | None = None,
) -> QuestioningDecision:
    """根據整理後需求狀態判斷下一步應追問或進入規劃。"""

    requirement_context = context_output.requirement_context.strip()
    if not requirement_context:
        raise ValueError("requirement_context 不可為空白。")

    guarded_decision = _build_guarded_questioning_decision(
        context_output=context_output,
        follow_up_round_count=follow_up_round_count,
        has_existing_plan=has_existing_plan,
    )
    if guarded_decision is not None:
        return guarded_decision

    ai_request = build_questioning_ai_request(
        requirement_context=requirement_context,
        known_information=context_output.known_information,
        pending_confirmation=context_output.pending_confirmation,
        follow_up_round_count=follow_up_round_count,
        planning_intent=(
            context_output.planning_intent.model_dump()
            if context_output.planning_intent is not None
            else None
        ),
        has_existing_plan=has_existing_plan,
        existing_plan_outline=existing_plan_outline,
    )

    retry_count = 0
    last_failure_reason = "unknown_error"
    last_failure_details: dict[str, Any] = {}

    while retry_count < MAX_QUESTIONING_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        parse_result, failure_reason, failure_details = _parse_questioning_result(
            ai_result=ai_result,
            fallback_known_information=context_output.known_information,
            fallback_pending_confirmation=context_output.pending_confirmation,
        )

        if parse_result is None:
            last_failure_reason = failure_reason
            last_failure_details = failure_details
            retry_count += 1
            continue

        return parse_result

    raise ValueError(
        "Questioning output validation failed after "
        f"{MAX_QUESTIONING_RETRY_COUNT} attempts. "
        f"reason={last_failure_reason}, details={last_failure_details}"
    )


def _build_guarded_questioning_decision(
    *,
    context_output: ContextEngineeringOutput,
    follow_up_round_count: int,
    has_existing_plan: bool,
) -> QuestioningDecision | None:
    planning_intent = context_output.planning_intent
    intent_type = planning_intent.intent_type if planning_intent is not None else None
    target_main_task_order = (
        planning_intent.target_main_task_order if planning_intent is not None else None
    )

    if intent_type == "revise" and not has_existing_plan:
        return _build_follow_up_decision(
            reasoning="使用者看起來想修改既有排程，但系統目前沒有可修改的既有排程，因此需要先確認是否要建立新規劃。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            missing_items=[
                {
                    "label": "constraint",
                    "question_hint": "目前沒有可修改的既有排程，是否要改為建立一份新的規劃？",
                }
            ],
            next_step_guidance=["目前沒有可修改的既有排程，是否要改為建立一份新的規劃？"],
        )

    if intent_type == "revise" and has_existing_plan and target_main_task_order is None:
        return _build_follow_up_decision(
            reasoning="使用者看起來想修改既有排程，但目前無法確認要修改哪一個階段或任務，因此需要先追問修改範圍。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            missing_items=[
                {
                    "label": "constraint",
                    "question_hint": "想修改哪一個階段或任務？",
                }
            ],
            next_step_guidance=["想修改哪一個階段或任務？"],
        )

    if intent_type == "chat" and not has_existing_plan:
        return _build_follow_up_decision(
            reasoning="使用者看起來想針對既有規劃提問，但系統目前沒有可參考的既有排程，因此需要先確認要詢問的任務或是否建立規劃。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            missing_items=[
                {
                    "label": "constraint",
                    "question_hint": "目前沒有既有排程可以參考，想先建立一份規劃，還是補充你想詢問的任務內容？",
                }
            ],
            next_step_guidance=[
                "目前沒有既有排程可以參考，想先建立一份規劃，還是補充你想詢問的任務內容？"
            ],
        )

    if intent_type == "chat" and has_existing_plan:
        return QuestioningDecision(
            decision="planning",
            reasoning="使用者正在針對既有規劃提問，且系統已有可參考的排程內容，因此可進入 Chat Module 回答。",
            known_information=list(context_output.known_information),
            pending_confirmation=list(context_output.pending_confirmation),
            next_step_guidance=["進入 Chat Module 回答規劃相關問題。"],
        )

    if intent_type == "other" and has_existing_plan:
        return _build_follow_up_decision(
            reasoning="系統已有既有排程，但本輪目的不是明確的建立、修改或規劃相關提問，因此需要先確認使用者想做什麼。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            missing_items=[
                {
                    "label": "constraint",
                    "question_hint": "你是想修改目前排程、詢問排程內容，還是建立新的規劃？",
                }
            ],
            next_step_guidance=["你是想修改目前排程、詢問排程內容，還是建立新的規劃？"],
        )

    if has_existing_plan or intent_type == "revise":
        return None

    missing_minimum_basis = _collect_missing_minimum_basis(
        context_output.known_information,
        context_output.pending_confirmation,
    )
    if missing_minimum_basis:
        return _build_follow_up_decision(
            reasoning="目前尚未具備任務內容與期限這兩項最小規劃基礎，因此需要先補齊關鍵資訊。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            missing_items=missing_minimum_basis,
            next_step_guidance=[
                item["question_hint"] for item in missing_minimum_basis
            ],
        )

    if (
        follow_up_round_count == 0
        and _looks_like_learning_or_exam_plan(context_output)
    ):
        missing_learning_items = _collect_missing_learning_planning_context(
            context_output.known_information,
            context_output.pending_confirmation,
        )
        if missing_learning_items:
            return _build_follow_up_decision(
                reasoning="這是學習或考試準備類規劃，初次規劃前若缺少可投入時間或目前程度，會明顯影響排程密度與安排方向，因此應先追問。",
                known_information=context_output.known_information,
                pending_confirmation=context_output.pending_confirmation,
                missing_items=missing_learning_items,
                next_step_guidance=[
                    item["question_hint"] for item in missing_learning_items
                ],
            )

    return None


def _collect_missing_minimum_basis(
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
) -> list[dict[str, str]]:
    missing_items: list[dict[str, str]] = []
    if not _has_known_label(known_information, "task_type"):
        missing_items.append(
            {
                "label": "task_type",
                "question_hint": "想規劃的任務或目標是什麼？",
            }
        )
    if not _has_known_label(known_information, "deadline_hint"):
        missing_items.append(
            {
                "label": "deadline_hint",
                "question_hint": "預計什麼時候要完成？",
            }
        )

    return missing_items


def _collect_missing_learning_planning_context(
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
) -> list[dict[str, str]]:
    missing_items: list[dict[str, str]] = []
    if not _has_known_label(known_information, "time_budget"):
        missing_items.append(
            {
                "label": "time_budget",
                "question_hint": "每天或每週大約可以投入多少時間？",
            }
        )
    if not _has_known_label(known_information, "current_progress"):
        missing_items.append(
            {
                "label": "current_progress",
                "question_hint": "目前程度或準備進度大約到哪裡？",
            }
        )

    return missing_items


def _build_follow_up_decision(
    *,
    reasoning: str,
    known_information: list[dict[str, Any]],
    pending_confirmation: list[dict[str, Any]],
    missing_items: list[dict[str, str]],
    next_step_guidance: list[str],
) -> QuestioningDecision:
    merged_pending_confirmation = list(pending_confirmation)
    existing_pending_labels = {
        item.get("label") for item in merged_pending_confirmation if isinstance(item, dict)
    }
    for item in missing_items:
        if item["label"] not in existing_pending_labels:
            merged_pending_confirmation.append(dict(item))

    return QuestioningDecision(
        decision="follow_up",
        reasoning=reasoning,
        known_information=list(known_information),
        pending_confirmation=merged_pending_confirmation,
        next_step_guidance=[guidance for guidance in next_step_guidance if guidance],
    )


def _has_known_label(
    known_information: list[dict[str, Any]],
    label: str,
) -> bool:
    for item in known_information:
        if item.get("label") != label:
            continue
        value = item.get("value")
        if isinstance(value, str) and value.strip():
            return True
    return False


def _looks_like_learning_or_exam_plan(
    context_output: ContextEngineeringOutput,
) -> bool:
    text_parts = [context_output.requirement_context]
    for item in context_output.known_information:
        value = item.get("value")
        if isinstance(value, str):
            text_parts.append(value)

    normalized_text = "".join(text_parts).lower()
    keywords = (
        "學習",
        "考試",
        "備考",
        "準備",
        "多益",
        "toeic",
        "托福",
        "toefl",
        "雅思",
        "ielts",
        "英文",
        "英語",
        "證照",
        "檢定",
    )
    return any(keyword in normalized_text for keyword in keywords)


def _parse_questioning_result(
    *,
    ai_result: AIToModuleResult,
    fallback_known_information: list[dict[str, Any]],
    fallback_pending_confirmation: list[dict[str, Any]],
) -> tuple[QuestioningDecision | None, str, dict[str, Any]]:
    if not ai_result.success:
        return None, "ai_service_error", {
            "error_message": ai_result.error_message,
            "error_stage": ai_result.error_stage,
        }

    parsed_output = _extract_questioning_output(ai_result.output_result)
    if parsed_output is None:
        return None, "unparseable_output", {}

    validation_result = validate_questioning_decision_output(parsed_output)
    if not validation_result.is_valid:
        return None, validation_result.reason or "validation_failed", dict(
            validation_result.details
        )

    return QuestioningDecision(
        decision=_normalize_questioning_decision(parsed_output["decision"]),
        reasoning=str(parsed_output["reasoning"]).strip(),
        known_information=_collect_information_list(
            parsed_output.get("known_information"),
            fallback_known_information,
        ),
        pending_confirmation=_collect_information_list(
            parsed_output.get("pending_confirmation"),
            fallback_pending_confirmation,
        ),
        next_step_guidance=_collect_guidance_list(
            parsed_output.get("next_step_guidance")
        ),
    ), "accept", {}


def _extract_questioning_output(
    output_result: dict[str, Any] | str | None,
) -> dict[str, Any] | None:
    if isinstance(output_result, dict):
        if _looks_like_questioning_output(output_result):
            return output_result

        text_output = output_result.get("text")
        if isinstance(text_output, str):
            return _parse_questioning_text(text_output)

    if isinstance(output_result, str):
        return _parse_questioning_text(output_result)

    return None


def _parse_questioning_text(text_output: str) -> dict[str, Any] | None:
    normalized_text = _strip_markdown_code_fence(text_output.strip())
    if not normalized_text:
        return None

    return _extract_last_questioning_json_object(normalized_text)


def _load_json_object(text_output: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
        for start_index in range(len(text_output) - 1, -1, -1):
            if text_output[start_index] != "{":
                continue

            try:
                candidate, _ = decoder.raw_decode(text_output[start_index:])
            except json.JSONDecodeError:
                continue

            if isinstance(candidate, dict):
                parsed_output = candidate
                break

    if not isinstance(parsed_output, dict):
        return None

    return parsed_output


def _extract_last_questioning_json_object(text_output: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []

    try:
        parsed_output = json.loads(text_output)
    except json.JSONDecodeError:
        parsed_output = None
    else:
        if isinstance(parsed_output, dict) and _looks_like_questioning_output(parsed_output):
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
        if _looks_like_questioning_output(candidate):
            return candidate

    return None


def _strip_markdown_code_fence(text_output: str) -> str:
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


def _looks_like_questioning_output(value: dict[str, Any]) -> bool:
    required_keys = {
        "decision",
        "reasoning",
        "known_information",
        "pending_confirmation",
        "next_step_guidance",
    }
    return required_keys.issubset(value.keys())


def _normalize_questioning_decision(value: Any) -> Literal["follow_up", "planning"]:
    if value == "follow_up":
        return cast(Literal["follow_up", "planning"], "follow_up")
    if value == "planning":
        return cast(Literal["follow_up", "planning"], "planning")

    raise ValueError(f"Unsupported questioning decision: {value!r}")


def _collect_information_list(
    value: Any,
    fallback_value: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return list(fallback_value)

    collected_items: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            collected_items.append(item)

    return collected_items


def _collect_guidance_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    guidance_items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            guidance_items.append(item.strip())

    return guidance_items
