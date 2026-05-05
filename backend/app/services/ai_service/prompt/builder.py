from app.schemas import ModuleToAIRequest, PromptBuilderOutput
from app.services.ai_service.prompt.renderer import render_prompt_text


def build_ai_studio_request_payload(request: ModuleToAIRequest) -> PromptBuilderOutput:
    """Build AI Studio prompt output from the normalized module request."""

    prompt_text = render_prompt_text(request)

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


def build_openrouter_request_payload(
    request: ModuleToAIRequest,
) -> PromptBuilderOutput:
    """Build OpenRouter prompt output from the normalized module request."""

    prompt_text = render_prompt_text(request)

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
