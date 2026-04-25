from typing import Any

import httpx

from app.schemas import AIToModuleResult


def _parse_openrouter_text_response(payload: dict[str, Any]) -> str:
    """Extract plain text from the normalized OpenRouter chat completion payload."""

    choices = payload.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message", {})
    if not isinstance(message, dict):
        return ""

    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()

    return ""


def run_openrouter_task(
    model_config: dict[str, object],
    request_payload: dict[str, object] | None,
    api_key: str | None,
    base_url: str | None,
    timeout_seconds: float,
) -> AIToModuleResult:
    """OpenRouter provider client."""

    if not api_key:
        return AIToModuleResult(
            success=False,
            error_message="Missing OPENROUTER_API_KEY.",
            error_stage="ai_service_layer",
        )

    model_name = str(model_config.get("model_name", "")).strip()
    if not model_name:
        return AIToModuleResult(
            success=False,
            error_message="Model config is missing 'model_name'.",
            error_stage="ai_service_layer",
        )
    if not base_url:
        return AIToModuleResult(
            success=False,
            error_message="Missing OpenRouter base URL.",
            error_stage="ai_service_layer",
        )
    if not request_payload:
        return AIToModuleResult(
            success=False,
            error_message="Missing OpenRouter request payload.",
            error_stage="ai_service_layer",
        )

    payload = {"model": model_name, **request_payload}

    try:
        response = httpx.post(
            url=f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        response_payload = response.json()
    except httpx.HTTPError as exc:
        return AIToModuleResult(
            success=False,
            error_message=str(exc),
            error_stage="ai_service_layer",
        )
    except ValueError as exc:
        return AIToModuleResult(
            success=False,
            error_message=f"Invalid OpenRouter response: {exc}",
            error_stage="ai_service_layer",
        )

    text_output = _parse_openrouter_text_response(response_payload)
    if not text_output:
        return AIToModuleResult(
            success=False,
            error_message="OpenRouter response did not contain text output.",
            error_stage="ai_service_layer",
        )

    return AIToModuleResult(
        success=True,
        output_result={
            "text": text_output,
            "provider": "openrouter",
            "model_name": model_name,
        },
    )
