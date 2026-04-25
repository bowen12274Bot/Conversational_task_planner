import json

from app.schemas import ModuleToAIRequest


def build_text_prompt(request: ModuleToAIRequest) -> str:
    """Build the minimal prompt text passed from AI service layer to provider clients."""

    payload = {
        "task_type": request.task_type,
        "group_name": request.group_name,
        "capability_level": request.capability_level,
        "input_data": request.input_data,
        "output_target": request.output_target,
        "format_requirements": request.format_requirements,
    }
    return json.dumps(payload, ensure_ascii=False)


def build_ai_studio_request_payload(request: ModuleToAIRequest) -> dict[str, object]:
    """Build AI Studio request payload from the normalized module request."""

    return {
        "contents": [
            {
                "parts": [
                    {
                        "text": build_text_prompt(request),
                    }
                ]
            }
        ]
    }


def build_openrouter_request_payload(request: ModuleToAIRequest) -> dict[str, object]:
    """Build OpenRouter chat completion payload from the normalized module request."""

    return {
        "messages": [
            {
                "role": "user",
                "content": build_text_prompt(request),
            }
        ]
    }
