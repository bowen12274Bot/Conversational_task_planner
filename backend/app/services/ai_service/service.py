from typing import Any

from app.schemas import (
    AIToModuleResult,
    ModuleToAIRequest,
    ProviderExecutionConfig,
    ProviderRequestData,
)
from app.services.ai_service.clients import run_ai_studio_task, run_openrouter_task
from app.services.ai_service.config_loader import (
    get_provider_base_url,
    get_provider_timeout_seconds,
    load_model_config,
)
from app.services.ai_service.env_loader import load_provider_api_key
from app.services.ai_service.prompt import (
    build_ai_studio_request_payload,
    build_openrouter_request_payload,
)

DEFAULT_PROVIDER_ORDER = ("ai_studio", "openrouter")


def select_capability_level_model_config(
    ai_service_config: dict[str, Any],
    capability_level: str,
    provider_order: tuple[str, ...] = DEFAULT_PROVIDER_ORDER,
) -> dict[str, Any]:
    """Select the first enabled model config matching one capability level."""

    models = ai_service_config.get("models", [])
    # 這裡預期 model_config.yaml 讀出來的 models 應該是一個清單。
    # 先擋掉錯誤格式，避免後面的選模邏輯在異常資料上繼續運作。
    if not isinstance(models, list):
        raise ValueError("AI model configuration field 'models' must be a list.")

    for provider in provider_order:
        for model in models:
            if not isinstance(model, dict):
                continue
            if not model.get("enabled", False):
                continue
            if model.get("provider") != provider:
                continue
            if model.get("capability_level") != capability_level:
                continue
            return model

    raise ValueError(
        f"No enabled model matches capability_level '{capability_level}'."
    )


def build_model_chain(
    ai_service_config: dict[str, Any],
    model_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Expand one model config into an ordered fallback chain."""

    models = ai_service_config.get("models", [])
    # fallback 鏈會從整份 models 設定中往下展開。
    # 先確認資料型態正確，避免這個函式默默接受錯誤設定。
    if not isinstance(models, list):
        raise ValueError("AI model configuration field 'models' must be a list.")

    models_by_id: dict[str, dict[str, Any]] = {}
    # 先建立 id -> model 的對照表，之後 fallback_to 就能直接找到下一個模型，
    # 不需要每往下一層都重新掃一次整份 models。
    for model in models:
        if not isinstance(model, dict):
            continue
        model_id = str(model.get("id", "")).strip()
        if not model_id:
            continue
        models_by_id[model_id] = model

    model_chain: list[dict[str, Any]] = []
    visited_model_ids: set[str] = set()
    current_model: dict[str, Any] | None = model_config

    while current_model is not None:
        model_id = str(current_model.get("id", "")).strip()
        # fallback 鏈是靠內部 id 串接的，沒有 id 就無法安全地接到下一個模型。
        if not model_id:
            raise ValueError("Selected model config is missing 'id'.")
        # 防止設定出現 A -> B -> A 這種 fallback 迴圈。
        if model_id in visited_model_ids:
            raise ValueError(f"Detected fallback loop at model '{model_id}'.")
        # 即使某個模型被 fallback_to 指到，只要它已停用，就不應該進入可執行鏈。
        if not current_model.get("enabled", False):
            raise ValueError(f"Model '{model_id}' is disabled.")

        visited_model_ids.add(model_id)
        model_chain.append(current_model)

        fallback_model_id = current_model.get("fallback_to")
        if not isinstance(fallback_model_id, str) or not fallback_model_id.strip():
            break

        next_model = models_by_id.get(fallback_model_id)
        # 若 fallback 指到不存在的模型，直接在這裡報錯，
        # 比等到真正執行時才出問題更容易定位設定錯誤。
        if next_model is None:
            raise ValueError(f"Model '{fallback_model_id}' was not found.")
        current_model = next_model

    return model_chain


def run_single_model(
    provider_request_data: ProviderRequestData,
) -> AIToModuleResult:
    """Dispatch one request to the provider defined by the selected model config."""

    provider = provider_request_data.execution_config.provider_id
    if provider == "ai_studio":
        return run_ai_studio_task(
            model_config=provider_request_data.selected_model_config,
            request_payload=provider_request_data.request_payload,
            api_key=provider_request_data.execution_config.api_key,
            base_url=provider_request_data.execution_config.base_url,
            timeout_seconds=provider_request_data.execution_config.timeout_seconds,
        )
    if provider == "openrouter":
        return run_openrouter_task(
            model_config=provider_request_data.selected_model_config,
            request_payload=provider_request_data.request_payload,
            api_key=provider_request_data.execution_config.api_key,
            base_url=provider_request_data.execution_config.base_url,
            timeout_seconds=provider_request_data.execution_config.timeout_seconds,
        )

    return AIToModuleResult(
        success=False,
        error_message=f"Unsupported provider '{provider}'.",
        error_stage="ai_service_layer",
    )


def run_ai_flow(
    request: ModuleToAIRequest,
    config_path=None,
) -> AIToModuleResult:
    """AI service layer entry point."""

    try:
        ai_service_config = load_model_config(config_path)
        selected_model_config = select_capability_level_model_config(
            ai_service_config=ai_service_config,
            capability_level=request.capability_level,
        )
        model_chain = build_model_chain(
            ai_service_config=ai_service_config,
            model_config=selected_model_config,
        )
    except Exception as exc:
        return AIToModuleResult(
            success=False,
            error_message=str(exc),
            error_stage="ai_service_layer",
        )

    last_result: AIToModuleResult | None = None

    for current_model in model_chain:
        provider_id = str(current_model.get("provider", "")).strip()
        execution_config = ProviderExecutionConfig(
            provider_id=provider_id,
            base_url=get_provider_base_url(
                ai_service_config=ai_service_config,
                provider_id=provider_id,
            ),
            timeout_seconds=get_provider_timeout_seconds(
                ai_service_config=ai_service_config,
                provider_id=provider_id,
            ),
            api_key=load_provider_api_key(provider_id) or "",
        )

        if provider_id == "ai_studio":
            prompt_output = build_ai_studio_request_payload(request)
        elif provider_id == "openrouter":
            prompt_output = build_openrouter_request_payload(request)
        else:
            last_result = AIToModuleResult(
                success=False,
                error_message=f"Unsupported provider '{provider_id}'.",
                error_stage="ai_service_layer",
            )
            continue

        provider_request_data = ProviderRequestData(
            selected_model_config=current_model,
            request_payload=prompt_output.request_payload,
            execution_config=execution_config,
        )

        last_result = run_single_model(
            provider_request_data=provider_request_data,
        )
        if last_result.success:
            return last_result

    if last_result is not None:
        return last_result

    return AIToModuleResult(
        success=False,
        error_message="No model was executed.",
        error_stage="ai_service_layer",
    )
