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


def test_build_context_from_raw_input_falls_back_when_ai_returns_invalid_json_text(
    monkeypatch,
) -> None:
    user_input = "我想把這週的 API 串接工作排出來"
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": "not-json",
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    result = context_service.build_context_from_raw_input(user_input)

    assert result.requirement_context == user_input
    assert result.known_information == []
    assert result.pending_confirmation == []


def test_build_context_from_raw_input_falls_back_when_required_fields_are_missing(
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

    result = context_service.build_context_from_raw_input(user_input)

    assert result.requirement_context == user_input
    assert result.known_information == []
    assert result.pending_confirmation == []


def test_build_context_from_raw_input_uses_user_input_when_requirement_context_is_blank(
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

    result = context_service.build_context_from_raw_input(user_input)

    assert result.requirement_context == user_input


def test_build_context_from_raw_input_normalizes_non_list_information_fields_to_empty_lists(
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

    result = context_service.build_context_from_raw_input("我要整理資料庫報告")

    assert result.requirement_context == "整理後摘要"
    assert result.known_information == []
    assert result.pending_confirmation == []


def test_build_context_from_raw_input_falls_back_when_ai_flow_fails(
    monkeypatch,
) -> None:
    user_input = "我要整理資料庫報告"
    monkeypatch.setattr(
        context_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=False,
            error_message="ai failed",
            error_stage="ai_service_layer",
        ),
    )

    result = context_service.build_context_from_raw_input(user_input)

    assert result.requirement_context == user_input
    assert result.known_information == []
    assert result.pending_confirmation == []
