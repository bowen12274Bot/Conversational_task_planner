from app.schemas import ContextEngineeringOutput, QuestioningDecision


def evaluate_questioning_need(
    context_output: ContextEngineeringOutput,
) -> QuestioningDecision:
    """判斷目前資訊是否足以進入規劃，或需要先追問。"""

    requirement_context = context_output.requirement_context.strip()
    if not requirement_context:
        raise ValueError("requirement_context 不可為空白。")

    return QuestioningDecision(
        is_ready_for_planning=False,
        reasoning="questioning service 骨架已建立，後續將補上實際判斷規則。",
        known_information=context_output.known_information,
        pending_confirmation=context_output.pending_confirmation,
    )
