import pytest

from app.schemas import ContextEngineeringOutput
from app.services.ai_service.env_loader import load_provider_api_key
from app.services.modules.questioning import service as questioning_service


AI_STUDIO_API_KEY = load_provider_api_key("ai_studio")
OPENROUTER_API_KEY = load_provider_api_key("openrouter")


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
@pytest.mark.xfail(
    reason=(
        "The current Questioning model can reach the correct follow_up conclusion, "
        "but its strong-model output format is still unstable across runs."
    ),
    strict=False,
)
def test_evaluate_questioning_need_returns_follow_up_when_minimum_basis_is_missing_with_real_ai() -> None:
    context_output = ContextEngineeringOutput(
        requirement_context="使用者希望系統協助安排任務，但目前尚未提供明確期限。",
        known_information=[
            {"label": "task_type", "value": "Java 作業"},
        ],
        pending_confirmation=[
            {
                "label": "deadline_hint",
                "question_hint": "預計什麼時候要完成？",
            }
        ],
        conversation_history_text=None,
    )

    result = questioning_service.evaluate_questioning_need(
        context_output=context_output,
        follow_up_round_count=0,
    )

    assert result.decision == "follow_up"
    assert result.next_step_guidance


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
@pytest.mark.xfail(
    reason=(
        "The current Questioning prompt is still conservative in the "
        "precision-only pending case and may choose follow_up instead of planning."
    ),
    strict=False,
)
def test_evaluate_questioning_need_returns_planning_when_pending_only_affects_precision_with_real_ai() -> None:
    context_output = ContextEngineeringOutput(
        requirement_context="使用者希望在 7 天內完成 Java 作業，目前主任務與期限已明確。",
        known_information=[
            {"label": "task_type", "value": "Java 作業"},
            {"label": "deadline_hint", "value": "7 天內"},
        ],
        pending_confirmation=[
            {
                "label": "time_budget",
                "question_hint": "每天大約可投入多少時間？",
            }
        ],
        conversation_history_text=None,
    )

    result = questioning_service.evaluate_questioning_need(
        context_output=context_output,
        follow_up_round_count=1,
    )

    assert result.decision == "planning"
    assert result.next_step_guidance


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
@pytest.mark.xfail(
    reason=(
        "The current Questioning model can reach the correct follow_up conclusion, "
        "but its strong-model output format is still unstable across runs."
    ),
    strict=False,
)
def test_evaluate_questioning_need_returns_follow_up_when_pending_is_high_value_with_real_ai() -> None:
    context_output = ContextEngineeringOutput(
        requirement_context="使用者希望在 3 天內完成資料庫期末報告，但目前尚不清楚已完成到哪個階段。",
        known_information=[
            {"label": "task_type", "value": "資料庫期末報告"},
            {"label": "deadline_hint", "value": "3 天內"},
        ],
        pending_confirmation=[
            {
                "label": "current_progress",
                "question_hint": "目前已經完成到哪裡？",
            }
        ],
        conversation_history_text=None,
    )

    result = questioning_service.evaluate_questioning_need(
        context_output=context_output,
        follow_up_round_count=0,
    )

    assert result.decision == "follow_up"
    assert result.next_step_guidance


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
def test_evaluate_questioning_need_can_still_follow_up_when_pending_is_empty_with_real_ai() -> None:
    context_output = ContextEngineeringOutput(
        requirement_context=(
            "使用者希望在 7 天內完成 Java 作業，但目前需求描述仍偏粗略，"
            "尚不清楚作業是剛開始還是已進行一部分。"
        ),
        known_information=[
            {"label": "task_type", "value": "Java 作業"},
            {"label": "deadline_hint", "value": "7 天內"},
        ],
        pending_confirmation=[],
        conversation_history_text=None,
    )

    result = questioning_service.evaluate_questioning_need(
        context_output=context_output,
        follow_up_round_count=0,
    )

    assert result.decision == "follow_up"
    assert result.next_step_guidance


def test_parse_questioning_text_can_extract_last_json_object_after_analysis() -> None:
    raw_output = """
*   Role: Pre-planning decision assistant.
*   This model is thinking aloud before the final answer.
*   JSON only? Yes.
{
  "decision": "follow_up",
  "reasoning": "目前任務內容已知，但期限尚未明確，未達到最小規劃基礎，因此應先追問期限以確保規劃方向正確。",
  "known_information": [
    {
      "label": "task_type",
      "value": "Java 作業"
    }
  ],
  "pending_confirmation": [
    {
      "label": "deadline_hint",
      "question_hint": "預計什麼時候要完成？"
    }
  ],
  "next_step_guidance": [
    "預計什麼時候要完成這份 Java 作業？"
  ]
}
""".strip()

    parsed = questioning_service._parse_questioning_text(raw_output)

    assert parsed is not None
    assert parsed["decision"] == "follow_up"
    assert parsed["known_information"][0]["label"] == "task_type"
    assert parsed["pending_confirmation"][0]["label"] == "deadline_hint"
