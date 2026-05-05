from app.schemas import QuestioningDecision, ResponseOutput


def build_response_from_questioning(
    questioning_decision: QuestioningDecision,
) -> ResponseOutput:
    """根據 questioning 判斷結果生成對前端可顯示的自然語言回覆。"""

    reasoning = questioning_decision.reasoning.strip()
    if not reasoning:
        raise ValueError("questioning_decision.reasoning 不可為空白。")

    if questioning_decision.is_ready_for_planning:
        return ResponseOutput(
            reply_text="目前資訊已足以進入下一步規劃處理。",
            response_type="planning_ready",
            includes_follow_up_questions=False,
            includes_next_action=True,
        )

    return ResponseOutput(
        reply_text="目前需要再補充一些資訊，我會先根據已知內容整理後續追問。",
        response_type="follow_up_question",
        includes_follow_up_questions=True,
        includes_next_action=True,
    )
