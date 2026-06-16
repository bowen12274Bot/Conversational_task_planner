from app.services.modules.context_engineering.prompt import (
    build_context_engineering_ai_request,
    build_context_engineering_prompt_spec,
)


def test_build_context_engineering_ai_request_contains_sectioned_input_data() -> None:
    request = build_context_engineering_ai_request("我要整理下週的 API 串接工作")

    assert request.task_type == "context_engineering"
    assert request.input_data["rules"]
    assert request.input_data["task"]
    assert "explicitly keep them in known_information" in request.input_data["task"]
    assert "Current raw requirement:" in request.input_data["context"]
    assert "我要整理下週的 API 串接工作" in request.input_data["context"]
    assert request.input_data["examples"]
    assert request.input_data["output_target"]


def test_build_context_engineering_ai_request_includes_conversation_history_when_provided() -> None:
    request = build_context_engineering_ai_request(
        "我要整理下週的 API 串接工作",
        conversation_history_text="user: 舊需求\nai: 舊回覆",
    )

    assert "Conversation history:" in request.input_data["context"]
    assert "User: 舊需求" in request.input_data["context"]
    assert "AI: 舊回覆" in request.input_data["context"]


def test_build_context_engineering_ai_request_contains_format_requirements() -> None:
    request = build_context_engineering_ai_request("我要整理下週的 API 串接工作")

    assert request.format_requirements is not None
    assert request.format_requirements["required_fields"] == [
        "requirement_context",
        "known_information",
        "pending_confirmation",
        "planning_intent",
    ]
    assert any(
        "create, revise, chat, or other" in requirement
        for requirement in request.format_requirements["requirements"]
    )
    assert request.format_requirements["allowed_labels"]["values"]


def test_build_context_engineering_ai_request_includes_existing_plan_outline() -> None:
    request = build_context_engineering_ai_request(
        "請問第一階段可以再詳細一點嗎？",
        existing_plan_outline=[
            {
                "order": 1,
                "title": "第一階段情境重點規劃",
                "description": "整理高頻情境。",
            }
        ],
    )

    assert "Existing plan outline:" in request.input_data["context"]
    assert "1. 第一階段情境重點規劃" in request.input_data["context"]


def test_build_context_engineering_prompt_spec_rejects_blank_input() -> None:
    try:
        build_context_engineering_prompt_spec("   ")
    except ValueError as exc:
        assert "user_input 不可為空白" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank input")
