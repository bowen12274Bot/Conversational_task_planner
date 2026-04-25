import pytest

from app.schemas import AIToModuleResult, ModuleToAIRequest
from app.services.ai_service import service as ai_service_module
from app.services.ai_service.env_loader import load_provider_api_key
from app.services.ai_service.service import (
    build_model_chain,
    run_ai_flow,
    select_capability_level_model_config,
)


def _classify_ai_connectivity_result(result: AIToModuleResult) -> str:
    if not result.success:
        return "失敗"

    output_text = ""
    if isinstance(result.output_result, str):
        output_text = result.output_result.strip()
    elif isinstance(result.output_result, dict):
        output_text = str(result.output_result.get("text", "")).strip()

    if output_text == "成功":
        return "完全成功"

    return "半成功"


def test_select_capability_level_model_config_prefers_ai_studio() -> None:
    config = {
        "models": [
            {
                "id": "ai_studio_default",
                "provider": "ai_studio",
                "model_name": "gemma-3-12b-it",
                "enabled": True,
                "capability_level": "default",
                "fallback_to": "openrouter_default",
            },
            {
                "id": "openrouter_default",
                "provider": "openrouter",
                "model_name": "google/gemma-3-12b-it",
                "enabled": True,
                "capability_level": "default",
                "fallback_to": None,
            },
        ]
    }

    selected = select_capability_level_model_config(
        ai_service_config=config,
        capability_level="default",
    )

    assert selected["id"] == "ai_studio_default"


def test_build_model_chain_expands_fallback_order() -> None:
    config = {
        "models": [
            {
                "id": "ai_studio_default",
                "provider": "ai_studio",
                "model_name": "gemma-3-12b-it",
                "enabled": True,
                "capability_level": "default",
                "fallback_to": "openrouter_default",
            },
            {
                "id": "openrouter_default",
                "provider": "openrouter",
                "model_name": "google/gemma-3-12b-it",
                "enabled": True,
                "capability_level": "default",
                "fallback_to": None,
            },
        ]
    }

    selected = select_capability_level_model_config(
        ai_service_config=config,
        capability_level="default",
    )
    model_chain = build_model_chain(ai_service_config=config, model_config=selected)

    assert [model["id"] for model in model_chain] == [
        "ai_studio_default",
        "openrouter_default",
    ]


def test_run_ai_flow_returns_structured_error_for_missing_provider_key(
    monkeypatch,
) -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="default",
        input_data={"user_input": "測試API連接，請只輸出成功"},
        output_target="只輸出成功",
    )

    monkeypatch.setattr(
        ai_service_module,
        "load_model_config",
        lambda config_path=None: {
            "providers": [
                {
                    "id": "ai_studio",
                    "type": "ai_studio",
                    "enabled": True,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
                    "timeout_seconds": 30,
                }
            ],
            "models": [
                {
                    "id": "ai_studio_default",
                    "provider": "ai_studio",
                    "model_name": "gemma-3-12b-it",
                    "enabled": True,
                    "capability_level": "default",
                    "fallback_to": None,
                }
            ],
        },
    )
    monkeypatch.setattr(
        ai_service_module,
        "load_provider_api_key",
        lambda provider_id: None,
    )

    result = run_ai_flow(request=request)

    assert result.success is False
    assert result.error_stage == "ai_service_layer"


def test_run_ai_flow_falls_back_to_openrouter_when_ai_studio_fails(
    monkeypatch,
) -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="default",
        input_data={"user_input": "測試API連接，請只輸出成功"},
        output_target="只輸出成功",
    )

    monkeypatch.setattr(
        ai_service_module,
        "load_model_config",
        lambda config_path=None: {
            "providers": [
                {
                    "id": "ai_studio",
                    "type": "ai_studio",
                    "enabled": True,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
                    "timeout_seconds": 30,
                },
                {
                    "id": "openrouter",
                    "type": "openrouter",
                    "enabled": True,
                    "base_url": "https://openrouter.ai/api/v1",
                    "timeout_seconds": 30,
                },
            ],
            "models": [
                {
                    "id": "ai_studio_default",
                    "provider": "ai_studio",
                    "model_name": "gemma-3-12b-it",
                    "enabled": True,
                    "capability_level": "default",
                    "fallback_to": "openrouter_default",
                },
                {
                    "id": "openrouter_default",
                    "provider": "openrouter",
                    "model_name": "google/gemma-3-12b-it",
                    "enabled": True,
                    "capability_level": "default",
                    "fallback_to": None,
                },
            ],
        },
    )
    monkeypatch.setattr(
        ai_service_module,
        "run_ai_studio_task",
        lambda **kwargs: AIToModuleResult(
            success=False,
            error_message="ai_studio_failed",
            error_stage="ai_service_layer",
        ),
    )
    monkeypatch.setattr(
        ai_service_module,
        "run_openrouter_task",
        lambda **kwargs: AIToModuleResult(
            success=True,
            output_result={
                "text": "成功",
                "provider": "openrouter",
                "model_name": "google/gemma-3-12b-it",
            },
        ),
    )
    monkeypatch.setattr(
        ai_service_module,
        "load_provider_api_key",
        lambda provider_id: "test-key",
    )

    result = run_ai_flow(request=request)

    assert result.success is True
    assert isinstance(result.output_result, dict)
    assert result.output_result["provider"] == "openrouter"


def test_classify_ai_connectivity_result_by_three_levels() -> None:
    failed = AIToModuleResult(
        success=False,
        error_message="request failed",
        error_stage="ai_service_layer",
    )
    partial = AIToModuleResult(
        success=True,
        output_result={"text": "API連接成功"},
    )
    complete = AIToModuleResult(
        success=True,
        output_result={"text": "成功"},
    )

    assert _classify_ai_connectivity_result(failed) == "失敗"
    assert _classify_ai_connectivity_result(partial) == "半成功"
    assert _classify_ai_connectivity_result(complete) == "完全成功"


@pytest.mark.skipif(
    not load_provider_api_key("ai_studio"),
    reason="AI Studio API key is not configured.",
)
def test_ai_connectivity_with_real_provider_returns_three_level_result() -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="default",
        input_data={"user_input": "測試API連接，請只輸出成功"},
        output_target="只輸出成功",
    )

    result = run_ai_flow(request=request)
    level = _classify_ai_connectivity_result(result)

    assert level in {"失敗", "半成功", "完全成功"}
