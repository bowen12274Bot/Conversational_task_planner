from app.schemas import ContextEngineeringOutput


def build_context_from_raw_input(
    user_input: str,
    history_context_summary: str | None = None,
) -> ContextEngineeringOutput:
    """將使用者原始輸入整理為後續流程可用的基礎上下文。"""

    normalized_input = user_input.strip()
    if not normalized_input:
        raise ValueError("user_input 不可為空白。")

    return ContextEngineeringOutput(
        requirement_context=normalized_input,
        known_information=[],
        pending_confirmation=[],
        history_context_summary=history_context_summary,
    )
