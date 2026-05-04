import pytest

from app.schemas import ModuleToAIRequest
from app.services.ai_service import service as ai_service_module
from app.services.ai_service.env_loader import load_provider_api_key
from app.services.ai_service.service import run_ai_flow

AI_STUDIO_API_KEY = load_provider_api_key("ai_studio")
OPENROUTER_API_KEY = load_provider_api_key("openrouter")


@pytest.mark.skipif(
    not AI_STUDIO_API_KEY,
    reason="AI Studio API key is not configured.",
)
def test_ai_studio_connectivity_with_real_provider() -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="default",
        input_data={"user_input": "測試API連接，請只輸出成功兩字"},
        output_target="成功",
    )

    result = run_ai_flow(request=request)

    assert result.success is True
    assert result.output_result is not None


@pytest.mark.skipif(
    not OPENROUTER_API_KEY,
    reason="OpenRouter API key is not configured.",
)
def test_openrouter_connectivity_with_real_provider(monkeypatch) -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="default",
        input_data={"user_input": "測試API連接，請只輸出成功兩字"},
        output_target="成功",
    )

    monkeypatch.setattr(
        ai_service_module,
        "load_model_config",
        lambda config_path=None: {
            "providers": [
                {
                    "id": "openrouter",
                    "type": "openrouter",
                    "enabled": True,
                    "base_url": "https://openrouter.ai/api/v1",
                    "timeout_seconds": 30,
                }
            ],
            "models": [
                {
                    "id": "openrouter_default",
                    "provider": "openrouter",
                    "model_name": "google/gemma-3-12b-it",
                    "enabled": True,
                    "capability_level": "default",
                    "fallback_to": None,
                }
            ],
        },
    )

    result = run_ai_flow(request=request)

    assert result.success is True
    assert result.output_result is not None
