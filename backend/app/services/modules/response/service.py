from app.schemas import (
    AIToModuleResult,
    ChatResponseInput,
    PlanningRevisionResponseInput,
    PlanningResponseInput,
    QuestioningDecision,
    ResponseOutput,
)
from app.services.ai_service.service import run_ai_flow
from app.services.modules.response.prompt import (
    build_follow_up_response_ai_request,
    build_planning_response_ai_request,
)

MAX_RESPONSE_RETRY_COUNT = 2
MIN_RESPONSE_TEXT_LENGTH = 8


def build_response_from_questioning(
    questioning_decision: QuestioningDecision,
) -> ResponseOutput:
    """根據 questioning 判斷結果生成對前端可顯示的自然語言回覆。"""

    if questioning_decision.decision != "follow_up":
        raise ValueError("僅能對 follow_up decision 生成追問回覆。")

    reasoning = questioning_decision.reasoning.strip()
    if not reasoning:
        raise ValueError("questioning_decision.reasoning 不可為空白。")

    if not questioning_decision.pending_confirmation:
        return _build_fallback_follow_up_response(questioning_decision)

    ai_request = build_follow_up_response_ai_request(questioning_decision)

    retry_count = 0
    while retry_count < MAX_RESPONSE_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        reply_text = _extract_response_text(ai_result)

        if _is_usable_response_text(reply_text):
            assert reply_text is not None
            return ResponseOutput(
                reply_text=reply_text.strip(),
                response_type="follow_up_question",
            )

        retry_count += 1

    return _build_fallback_follow_up_response(questioning_decision)


def build_response_from_planning(
    planning_response_input: PlanningResponseInput,
) -> ResponseOutput:
    """根據 planning 結果生成對前端可顯示的自然語言規劃完成回覆。"""

    plan_summary = planning_response_input.plan_summary.strip()
    design_rationale = planning_response_input.design_rationale.strip()
    if not plan_summary:
        raise ValueError("planning_response_input.plan_summary 不可為空白。")
    if not design_rationale:
        raise ValueError("planning_response_input.design_rationale 不可為空白。")

    ai_request = build_planning_response_ai_request(planning_response_input)

    retry_count = 0
    while retry_count < MAX_RESPONSE_RETRY_COUNT:
        ai_result = run_ai_flow(ai_request)
        reply_text = _extract_response_text(ai_result)

        if _is_usable_response_text(reply_text):
            assert reply_text is not None
            return ResponseOutput(
                reply_text=reply_text.strip(),
                response_type="planning_summary",
            )

        retry_count += 1

    return _build_fallback_planning_response(planning_response_input)


def build_response_from_planning_revision(
    revision_response_input: PlanningRevisionResponseInput,
) -> ResponseOutput:
    """根據 planning revision 結果生成對前端可顯示的修改完成回覆。"""

    target_title = revision_response_input.target_main_task_title.strip()
    revision_summary = revision_response_input.revision_summary.strip().rstrip("。")
    if not target_title:
        raise ValueError("revision_response_input.target_main_task_title 不可為空白。")
    if not revision_summary:
        raise ValueError("revision_response_input.revision_summary 不可為空白。")

    return ResponseOutput(
        reply_text=f"已更新「{target_title}」，右側規劃面板已同步調整。{revision_summary}。",
        response_type="planning_revision_summary",
    )


def build_response_from_chat(
    chat_response_input: ChatResponseInput,
) -> ResponseOutput:
    """根據 Chat Module 結果建立對前端可顯示的自然語言回覆。"""

    answer = chat_response_input.chat_output.answer.strip()
    if not answer:
        raise ValueError("chat_response_input.chat_output.answer 不可為空白。")

    return ResponseOutput(
        reply_text=answer,
        response_type="chat_answer",
    )


def _extract_response_text(ai_result: AIToModuleResult) -> str | None:
    """從 AI service 通用結果中取出可用文字。"""

    if not ai_result.success:
        return None

    output_result = ai_result.output_result
    if isinstance(output_result, dict):
        text = output_result.get("text")
        if isinstance(text, str) and text.strip():
            return _extract_final_reply_text(text)

    if isinstance(output_result, str) and output_result.strip():
        return _extract_final_reply_text(output_result)

    return None


def _extract_final_reply_text(reply_text: str) -> str | None:
    normalized_text = reply_text.strip()
    if not normalized_text:
        return None

    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    if not lines:
        return None

    for line in reversed(lines):
        candidate = _normalize_reply_candidate(line)
        if _looks_like_final_reply(candidate):
            return candidate

    candidate = _normalize_reply_candidate(lines[-1])
    return candidate or None


def _normalize_reply_candidate(value: str) -> str:
    normalized = value.strip().strip('"').strip("'").strip()
    if normalized.startswith("*"):
        normalized = normalized.lstrip("*").strip()
    return normalized


def _looks_like_final_reply(value: str) -> bool:
    if not value:
        return False

    lowered = value.lower()
    blocked_prefixes = (
        "helpful planning assistant",
        "natural traditional chinese",
        "generate a short follow-up reply",
        "final polish",
        "draft",
        "constraint",
        "reasoning",
        "next_step_guidance",
        "input",
        "output",
        "wait,",
        "applying this style",
        "example style",
        "this looks perfect",
    )
    if lowered.startswith(blocked_prefixes):
        return False

    if "`" in value or "{" in value or "}" in value:
        return False

    if ":" in value and all(ord(ch) < 128 for ch in value[: min(len(value), 24)]):
        return False

    question_marks = value.count("？") + value.count("?")
    if question_marks == 0:
        return False

    return True


def _is_usable_response_text(reply_text: str | None) -> bool:
    """判斷 AI 回覆文字是否達到最小可用標準。"""

    if reply_text is None:
        return False

    normalized_text = reply_text.strip()
    if not normalized_text:
        return False

    return len(normalized_text) >= MIN_RESPONSE_TEXT_LENGTH


def _build_fallback_follow_up_response(
    questioning_decision: QuestioningDecision,
) -> ResponseOutput:
    """當 AI 回覆不可用時，建立最小追問回覆。"""

    question_hints: list[str] = []
    for guidance in questioning_decision.next_step_guidance:
        normalized_guidance = guidance.strip()
        if normalized_guidance:
            question_hints.append(normalized_guidance)
        if len(question_hints) >= 2:
            break

    if question_hints:
        reply_text = (
            "為了幫你安排得更準確，我想先確認兩件事："
            + "？".join(question_hints).rstrip("？")
            + "？"
        )
        return ResponseOutput(
            reply_text=reply_text,
            response_type="follow_up_question",
        )

    for item in questioning_decision.pending_confirmation:
        question_hint = item.get("question_hint")
        if isinstance(question_hint, str) and question_hint.strip():
            question_hints.append(question_hint.strip())
        if len(question_hints) >= 2:
            break

    if question_hints:
        reply_text = (
            "為了幫你安排得更準確，我想先確認兩件事："
            + "？".join(question_hints).rstrip("？")
            + "？"
        )
    else:
        reply_text = "目前還需要再補充一些資訊，我先整理幾個關鍵問題來確認。"

    return ResponseOutput(
        reply_text=reply_text,
        response_type="follow_up_question",
    )


def _build_fallback_planning_response(
    planning_response_input: PlanningResponseInput,
) -> ResponseOutput:
    """當 planning 路徑 AI 回覆不可用時，建立最小規劃完成回覆。"""

    plan_summary = planning_response_input.plan_summary.strip().rstrip("。")
    design_rationale = planning_response_input.design_rationale.strip().rstrip("。")
    if design_rationale:
        reply_text = (
            f"我先根據目前資訊整理出一版初步規劃，已經放在右側規劃面板。"
            f"{plan_summary}。"
        )
    else:
        reply_text = (
            "我先根據目前資訊整理出一版初步規劃，已經放在右側規劃面板。"
            f"{plan_summary}。"
        )

    return ResponseOutput(
        reply_text=reply_text,
        response_type="planning_summary",
    )
