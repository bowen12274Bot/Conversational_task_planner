from app.schemas import ContextEngineeringOutput, QuestioningDecision


def evaluate_questioning_need(
    context_output: ContextEngineeringOutput,
) -> QuestioningDecision:
    """判斷目前資訊是否足以進入規劃，或需要先追問。"""

    requirement_context = context_output.requirement_context.strip()
    if not requirement_context:
        raise ValueError("requirement_context 不可為空白。")

    pending_confirmation = context_output.pending_confirmation
    known_information = context_output.known_information

    if pending_confirmation:
        return QuestioningDecision(
            is_ready_for_planning=False,
            reasoning=_build_reasoning_text(
                requirement_context=requirement_context,
                pending_confirmation=pending_confirmation,
            ),
            known_information=known_information,
            pending_confirmation=pending_confirmation,
        )

    return QuestioningDecision(
        is_ready_for_planning=True,
        reasoning="目前已具備基本資訊，可進入下一步規劃處理。",
        known_information=known_information,
        pending_confirmation=pending_confirmation,
    )


def _build_reasoning_text(
    requirement_context: str,
    pending_confirmation: list[dict[str, object]],
) -> str:
    """建立帶背景的追問理由說明。"""

    missing_information_names: list[str] = []
    for item in pending_confirmation:
        label = item.get("label")
        if isinstance(label, str) and label.strip():
            missing_information_names.append(_map_label_to_display_text(label))

    if not missing_information_names:
        return (
            f"目前需求是：{requirement_context}。"
            "仍有一些關鍵資訊不足，先補充後會比較適合後續規劃。"
        )

    missing_information_text = "、".join(missing_information_names)
    return (
        f"目前需求是：{requirement_context}。"
        f"但目前仍缺少 {missing_information_text}，"
        "先補這些資訊會比較適合後續規劃。"
    )


def _map_label_to_display_text(label: str) -> str:
    """將內部 label 轉為較自然的中文描述。"""

    label_display_map = {
        "current_progress": "目前進度",
        "time_budget": "可投入時間",
        "difficulty": "困難點",
        "constraint": "限制條件",
        "deadline_hint": "期限",
        "task_type": "任務內容",
    }
    return label_display_map.get(label, label)
