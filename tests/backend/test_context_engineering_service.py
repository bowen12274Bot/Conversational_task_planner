from app.schemas import AIToModuleResult
from app.services.modules.context_engineering import service as context_service


def test_build_context_from_raw_input_returns_structured_output_when_ai_returns_valid_json_text(
    monkeypatch,
) -> None:
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
        "我想把這週的 API 串接工作排出來"
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

    try:
        context_service.build_context_from_raw_input(user_input)
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
        context_service.build_context_from_raw_input(user_input)
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
        context_service.build_context_from_raw_input(user_input)
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank requirement_context")


def test_build_context_from_raw_input_raises_when_information_fields_are_not_lists(
    monkeypatch,
) -> None:
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
        context_service.build_context_from_raw_input("我要整理資料庫報告")
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

    try:
        context_service.build_context_from_raw_input(user_input)
    except ValueError as exc:
        assert "validation failed after 3 attempts" in str(exc)
        assert call_count["value"] == 3
        return

    raise AssertionError("Expected ValueError when ai flow keeps failing")
