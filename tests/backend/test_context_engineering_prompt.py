from app.services.modules.context_engineering.prompt import (
    build_context_engineering_ai_request,
    build_context_engineering_prompt_spec,
)


def test_build_context_engineering_ai_request_contains_sectioned_input_data() -> None:
    request = build_context_engineering_ai_request("我要整理下週的 API 串接工作")

    assert request.task_type == "context_engineering"
    assert request.input_data["rules"]
    assert request.input_data["task"]
    assert request.input_data["context"]["raw_requirement"] == "我要整理下週的 API 串接工作"
    assert request.input_data["examples"]
    assert request.input_data["output_target"]


def test_build_context_engineering_ai_request_contains_format_requirements() -> None:
    request = build_context_engineering_ai_request("我要整理下週的 API 串接工作")

    assert request.format_requirements is not None
    assert request.format_requirements["required_fields"] == [
        "requirement_context",
        "known_information",
        "pending_confirmation",
    ]
    assert request.format_requirements["allowed_labels"]["recommended"]


def test_build_context_engineering_prompt_spec_rejects_blank_input() -> None:
    try:
        build_context_engineering_prompt_spec("   ")
    except ValueError as exc:
        assert "user_input 不可為空白" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank input")
