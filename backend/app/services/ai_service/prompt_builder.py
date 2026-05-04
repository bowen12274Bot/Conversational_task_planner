import json

from app.schemas import ModuleToAIRequest, PromptBuilderOutput


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


def build_ai_studio_request_payload(request: ModuleToAIRequest) -> PromptBuilderOutput:
    """Build AI Studio prompt output from the normalized module request."""

    prompt_text = build_text_prompt(request)

    return PromptBuilderOutput(
        prompt_text=prompt_text,
        request_payload={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt_text,
                        }
                    ]
                }
            ]
        },
    )


def build_openrouter_request_payload(request: ModuleToAIRequest) -> PromptBuilderOutput:
    """Build OpenRouter prompt output from the normalized module request."""

    prompt_text = build_text_prompt(request)

    return PromptBuilderOutput(
        prompt_text=prompt_text,
        request_payload={
            "messages": [
                {
                    "role": "user",
                    "content": prompt_text,
                }
            ]
        },
    )
