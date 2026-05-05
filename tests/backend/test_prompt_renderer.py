from app.schemas import ModuleToAIRequest
from app.services.ai_service.prompt.renderer import render_prompt_text


def test_render_prompt_text_renders_sectioned_prompt_for_context_engineering_input() -> None:
    request = ModuleToAIRequest(
        task_type="context_engineering",
        group_name="conversation_flow",
        capability_level="fast",
        input_data={
            "rules": "Follow rules.",
            "task": "Analyze the requirement.",
            "context": {"raw_requirement": "我要整理報告"},
            "examples": [{"input": "A", "output": "B"}],
            "output_target": "Return structured output.",
        },
        format_requirements={"required_fields": ["requirement_context"]},
    )

    prompt_text = render_prompt_text(request)

    assert "[rules]" in prompt_text
    assert "[task]" in prompt_text
    assert "[context]" in prompt_text
    assert "[examples]" in prompt_text
    assert "[output_target]" in prompt_text
    assert "[format_requirements]" in prompt_text


def test_render_prompt_text_does_not_render_meta_section() -> None:
    request = ModuleToAIRequest(
        task_type="context_engineering",
        group_name="conversation_flow",
        capability_level="fast",
        input_data={
            "rules": "Follow rules.",
            "task": "Analyze the requirement.",
            "context": {"raw_requirement": "我要整理報告"},
            "examples": [{"input": "A", "output": "B"}],
            "output_target": "Return structured output.",
        },
        format_requirements={"required_fields": ["requirement_context"]},
    )

    prompt_text = render_prompt_text(request)

    assert "[meta]" not in prompt_text
    assert "context_engineering" not in prompt_text


def test_render_prompt_text_falls_back_to_json_dump_for_non_sectioned_input() -> None:
    request = ModuleToAIRequest(
        task_type="text_output",
        group_name="questioning_response",
        capability_level="fast",
        input_data={"user_input": "hello"},
        format_requirements=None,
    )

    prompt_text = render_prompt_text(request)

    assert prompt_text.startswith("{")
    assert '"task_type": "text_output"' in prompt_text
