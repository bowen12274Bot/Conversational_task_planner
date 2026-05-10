REQUIREMENT_LABEL_DISPLAY_TEXT = {
    "task_type": "任務內容",
    "deadline_hint": "期限",
    "current_progress": "目前進度",
    "time_budget": "可投入時間",
    "difficulty": "困難點",
    "constraint": "限制條件",
}

ALLOWED_REQUIREMENT_LABELS = tuple(REQUIREMENT_LABEL_DISPLAY_TEXT.keys())


def get_requirement_label_display_text(label: str) -> str:
    """將系統內部 requirement label 轉為較自然的中文描述。"""

    return REQUIREMENT_LABEL_DISPLAY_TEXT.get(label, label)
