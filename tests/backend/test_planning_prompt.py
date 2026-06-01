from app.services.modules.planning.prompt import (
    build_planning_create_ai_request,
    build_planning_create_prompt_spec,
)


def test_build_planning_create_ai_request_contains_expected_sections() -> None:
    request = build_planning_create_ai_request(
        requirement_context="使用者希望在 7 天內完成 Java 作業，目前尚未開始。",
        known_information=[
            {"label": "task_type", "value": "Java 作業"},
            {"label": "deadline_hint", "value": "7 天內"},
        ],
        pending_confirmation=[],
        conversation_history_text=None,
    )

    assert request.group_name == "planning_create"
    assert request.input_data["rules"]
    assert request.input_data["task"]
    assert request.input_data["context"]["requirement_context"] == (
        "使用者希望在 7 天內完成 Java 作業，目前尚未開始。"
    )
    assert request.input_data["examples"]
    assert request.input_data["output_target"]
    assert "one raw JSON object only" in request.input_data["rules"]
    assert "without any additional commentary" in request.input_data["task"]


def test_build_planning_create_ai_request_contains_format_requirements() -> None:
    request = build_planning_create_ai_request(
        requirement_context="使用者希望在 7 天內完成 Java 作業，目前尚未開始。",
        known_information=[],
        pending_confirmation=[],
        conversation_history_text=None,
    )

    assert request.format_requirements is not None
    assert request.format_requirements["required_fields"] == [
        "plan_summary",
        "design_rationale",
        "assumptions_used",
        "schedule",
    ]
    assert "Return exactly one JSON object and nothing else." in request.format_requirements["requirements"]


def test_build_planning_create_prompt_spec_rejects_blank_requirement_context() -> None:
    try:
        build_planning_create_prompt_spec(
            requirement_context="   ",
            known_information=[],
            pending_confirmation=[],
            conversation_history_text=None,
        )
    except ValueError as exc:
        assert "requirement_context 不可為空白" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank requirement_context")
