from app.schemas import AIToModuleResult, QuestioningDecision, ResponseOutput
from app.services.ai_service.service import run_ai_flow
from app.services.modules.response.prompt import build_follow_up_response_ai_request

MAX_RESPONSE_RETRY_COUNT = 2
MIN_RESPONSE_TEXT_LENGTH = 8


def build_response_from_questioning(
    questioning_decision: QuestioningDecision,
) -> ResponseOutput:
    """根據 questioning 判斷結果生成對前端可顯示的自然語言回覆。"""

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


def _extract_response_text(ai_result: AIToModuleResult) -> str | None:
    """從 AI service 通用結果中取出可用文字。"""

    if not ai_result.success:
        return None

    output_result = ai_result.output_result
    if isinstance(output_result, dict):
        text = output_result.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    if isinstance(output_result, str) and output_result.strip():
        return output_result.strip()

    return None


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
