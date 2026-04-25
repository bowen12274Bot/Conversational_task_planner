from typing import Any

import httpx

from app.schemas import AIToModuleResult


def _parse_ai_studio_text_response(payload: dict[str, Any]) -> str:
    """Extract plain text from the nested AI Studio response payload."""

    # AI Studio wraps generated text under candidates -> content -> parts -> text.
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return ""

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        return ""

    content = first_candidate.get("content", {})
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts", [])
    if not isinstance(parts, list):
        return ""

    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])

    return "\n".join(texts).strip()


def run_ai_studio_task(
    model_config: dict[str, object],
    request_payload: dict[str, object],
    api_key: str | None,
    base_url: str | None,
    timeout_seconds: float,
) -> AIToModuleResult:
    """AI Studio provider client."""

    if not api_key:
        return AIToModuleResult(
            success=False,
            error_message="Missing AI_STUDIO_API_KEY.",
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
            error_message="Missing AI Studio base URL.",
            error_stage="ai_service_layer",
        )

    try:
        response = httpx.post(
            url=f"{base_url}/{model_name}:generateContent",
            params={"key": api_key},
            json=request_payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        return AIToModuleResult(
            success=False,
            error_message=str(exc),
            error_stage="ai_service_layer",
        )
    except ValueError as exc:
        return AIToModuleResult(
            success=False,
            error_message=f"Invalid AI Studio response: {exc}",
            error_stage="ai_service_layer",
        )

    text_output = _parse_ai_studio_text_response(payload)
    if not text_output:
        return AIToModuleResult(
            success=False,
            error_message="AI Studio response did not contain text output.",
            error_stage="ai_service_layer",
        )

    return AIToModuleResult(
        success=True,
        output_result={
            "text": text_output,
            "provider": "ai_studio",
            "model_name": model_name,
        },
    )
