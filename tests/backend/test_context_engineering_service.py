import pytest

from app.schemas import AIToModuleResult
from app.services.modules.context_engineering import service as context_service
from app.services.ai_service.env_loader import load_provider_api_key


AI_STUDIO_API_KEY = load_provider_api_key("ai_studio")
OPENROUTER_API_KEY = load_provider_api_key("openrouter")


def test_build_context_from_raw_input_returns_structured_output_when_ai_returns_valid_json_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: "user: 之前需求\nai: 之前回覆",
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    '{"requirement_context":"整理後摘要","known_information":'
                    '[{"label":"task_type","value":"API 串接"}],'
                    '"pending_confirmation":'
                    '[{"label":"time_budget","question_hint":"每天能投入多久？"}]}'
                ),
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    result = context_service.build_context_from_raw_input(
        "我想把這週的 API 串接工作排出來",
        conversation_id="conv-001",
    )

    assert result.requirement_context == "整理後摘要"
    assert result.known_information == [
        {"label": "task_type", "value": "API 串接"}
    ]
    assert result.pending_confirmation == [
        {"label": "time_budget", "question_hint": "每天能投入多久？"}
    ]
    assert result.conversation_history_text == "user: 之前需求\nai: 之前回覆"


def test_build_context_from_raw_input_can_extract_last_json_object_after_analysis_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    "*   Analysis before final answer.\n"
                    "*   The model is thinking aloud.\n"
                    "{\n"
                    '  "requirement_context": "整理後摘要",\n'
                    '  "known_information": [{"label":"task_type","value":"API 串接"}],\n'
                    '  "pending_confirmation": [{"label":"time_budget","question_hint":"每天能投入多久？"}]\n'
                    "}"
                ),
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    result = context_service.build_context_from_raw_input(
        "我想把這週的 API 串接工作排出來",
        conversation_id="conv-001",
    )

    assert result.requirement_context == "整理後摘要"
    assert result.known_information == [
        {"label": "task_type", "value": "API 串接"}
    ]
    assert result.pending_confirmation == [
        {"label": "time_budget", "question_hint": "每天能投入多久？"}
    ]


def test_build_context_from_raw_input_raises_after_three_attempts_when_ai_returns_invalid_json_text(
    monkeypatch,
) -> None:
    user_input = "我想把這週的 API 串接工作排出來"
    call_count = {"value": 0}

    def fake_run_ai_flow(request):
        call_count["value"] += 1
        return AIToModuleResult(
            success=True,
            output_result={
                "text": "not-json",
                "provider": "mock",
                "model_name": "mock-model",
            },
        )

    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        fake_run_ai_flow,
    )
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )

    try:
        context_service.build_context_from_raw_input(
            user_input,
            conversation_id="conv-001",
        )
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        assert call_count["value"] == 3
        return

    raise AssertionError("Expected ValueError for invalid JSON text")


def test_build_context_from_raw_input_raises_when_required_fields_are_missing(
    monkeypatch,
) -> None:
    user_input = "我要整理資料庫報告"
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": '{"requirement_context":"缺欄位"}',
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    try:
        context_service.build_context_from_raw_input(
            user_input,
            conversation_id="conv-001",
        )
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        return

    raise AssertionError("Expected ValueError for missing required fields")


def test_build_context_from_raw_input_raises_when_requirement_context_is_blank(
    monkeypatch,
) -> None:
    user_input = "我要整理資料庫報告"
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    '{"requirement_context":"   ","known_information":[],"pending_confirmation":[]}'
                ),
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    try:
        context_service.build_context_from_raw_input(
            user_input,
            conversation_id="conv-001",
        )
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank requirement_context")


def test_build_context_from_raw_input_raises_when_information_fields_are_not_lists(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    '{"requirement_context":"整理後摘要","known_information":"bad",'
                    '"pending_confirmation":null}'
                ),
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    try:
        context_service.build_context_from_raw_input(
            "我要整理資料庫報告",
            conversation_id="conv-001",
        )
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        return

    raise AssertionError("Expected ValueError for invalid information field types")


def test_build_context_from_raw_input_raises_when_ai_flow_fails_after_three_attempts(
    monkeypatch,
) -> None:
    user_input = "我要整理資料庫報告"
    call_count = {"value": 0}

    def fake_run_ai_flow(request):
        call_count["value"] += 1
        return AIToModuleResult(
            success=False,
            error_message="ai failed",
            error_stage="ai_service_layer",
        )

    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        fake_run_ai_flow,
    )
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: None,
    )

    try:
        context_service.build_context_from_raw_input(
            user_input,
            conversation_id="conv-001",
        )
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        assert call_count["value"] == 3
        return

    raise AssertionError("Expected ValueError when ai flow keeps failing")


def test_build_context_from_raw_input_skips_history_lookup_when_conversation_id_is_missing(
    monkeypatch,
) -> None:
    history_call_count = {"value": 0}

    def fake_get_history(conversation_id):
        history_call_count["value"] += 1
        return "should not be used"

    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        fake_get_history,
    )
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    '{"requirement_context":"整理後摘要","known_information":[],'
                    '"pending_confirmation":[]}'
                ),
            },
        ),
    )

    result = context_service.build_context_from_raw_input("我要整理資料庫報告")

    assert result.conversation_history_text is None
    assert history_call_count["value"] == 0


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
def test_build_context_from_raw_input_can_merge_multi_turn_history_with_real_ai(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: (
            "User: 我要準備下週的資料庫期末報告，但還不知道怎麼拆工作。\n"
            "AI: 你目前已經完成到哪裡？每天大約可投入多少時間？"
        ),
    )

    result = context_service.build_context_from_raw_input(
        "我目前還沒開始，每天大概可以投入 2 小時。",
        conversation_id="conv-001",
    )

    known_information = {
        item.get("label"): item.get("value")
        for item in result.known_information
        if isinstance(item, dict)
    }
    pending_labels = {
        item.get("label")
        for item in result.pending_confirmation
        if isinstance(item, dict)
    }

    assert "資料庫期末報告" in result.requirement_context
    assert known_information.get("task_type")
    assert known_information.get("current_progress")
    assert known_information.get("time_budget")
    assert "current_progress" not in pending_labels
    assert "time_budget" not in pending_labels


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
def test_build_context_from_raw_input_keeps_confirmed_deadline_and_time_budget_across_turns_with_real_ai(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: (
            "User: 我要在7天內完成java作業，我一天只能做2小時。\n"
            "AI: 為了幫你規劃合適的安排，我想先了解一下目前這份 Java 作業已經完成到哪裡了呢？\n"
            "User: 已經完成系統架構了，但是模組間的API清單和資料契約還沒決定好。"
        ),
    )

    result = context_service.build_context_from_raw_input(
        "已經完成系統架構了，但是模組間的API清單和資料契約還沒決定好。",
        conversation_id="conv-001",
    )

    known_information = {
        item.get("label"): item.get("value")
        for item in result.known_information
        if isinstance(item, dict)
    }
    pending_labels = {
        item.get("label")
        for item in result.pending_confirmation
        if isinstance(item, dict)
    }

    assert known_information.get("task_type")
    assert known_information.get("deadline_hint")
    assert "7" in str(known_information.get("deadline_hint"))
    assert known_information.get("time_budget")
    assert "2" in str(known_information.get("time_budget"))
    assert "deadline_hint" not in pending_labels
    assert "time_budget" not in pending_labels


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
def test_build_context_from_raw_input_can_apply_explicit_requirement_update_with_real_ai(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: (
            "User: 我要準備下週的資料庫期末報告。\n"
            "AI: 你目前已經完成到哪裡？"
        ),
    )

    result = context_service.build_context_from_raw_input(
        "更正一下，不是下週，是明天要交。",
        conversation_id="conv-001",
    )

    known_information = {
        item.get("label"): item.get("value")
        for item in result.known_information
        if isinstance(item, dict)
    }
    pending_labels = {
        item.get("label")
        for item in result.pending_confirmation
        if isinstance(item, dict)
    }

    assert known_information.get("task_type")
    assert known_information.get("deadline_hint")
    assert "明天" in str(known_information.get("deadline_hint"))
    assert "deadline_hint" not in pending_labels


@pytest.mark.skipif(
    not (AI_STUDIO_API_KEY or OPENROUTER_API_KEY),
    reason="No real AI provider API key is configured.",
)
@pytest.mark.xfail(
    reason=(
        "The ambiguous-conflict case improved after adding one example, "
        "but the current model response is still not stable enough across runs."
    ),
    strict=False,
)
def test_build_context_from_raw_input_can_keep_unclear_conflict_in_pending_with_real_ai(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        context_service,
        "get_conversation_transcript",
        lambda conversation_id: (
            "User: 我要準備下週的資料庫期末報告。\n"
            "AI: 你目前已經完成到哪裡？"
        ),
    )

    result = context_service.build_context_from_raw_input(
        "我剩一天。",
        conversation_id="conv-001",
    )

    pending_labels = {
        item.get("label")
        for item in result.pending_confirmation
        if isinstance(item, dict)
    }

    assert "deadline_hint" in pending_labels
