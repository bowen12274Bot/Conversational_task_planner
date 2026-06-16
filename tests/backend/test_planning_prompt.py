from app.services.modules.planning.prompt import (
    build_planning_create_ai_request,
    build_planning_create_prompt_spec,
    build_planning_revision_ai_request,
    build_planning_revision_prompt_spec,
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
    assert "keep the total schedule within that capacity" in request.input_data["rules"]
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
    assert any(
        "total estimated effort should remain feasible" in requirement
        for requirement in request.format_requirements["requirements"]
    )


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


def test_build_planning_revision_ai_request_contains_expected_sections() -> None:
    request = build_planning_revision_ai_request(
        requirement_context="使用者希望細化既有規劃中的第一階段。",
        known_information=[{"label": "task_type", "value": "多益學習計畫"}],
        pending_confirmation=[],
        conversation_history_text=None,
        existing_plan_outline=[
            {"order": 1, "title": "第一階段情境重點規劃"},
            {"order": 2, "title": "學習管道與工具建議"},
        ],
        target_main_task={
            "title": "第一階段情境重點規劃",
            "description": "整理常見情境。",
            "estimated_time": "1 小時",
            "order": 1,
            "subtasks": [],
        },
        target_main_task_order=1,
        revision_request="請把第一階段補得更詳細。",
    )

    assert request.group_name == "planning_revision"
    assert request.input_data["rules"]
    assert "revise exactly one target main task" in request.input_data["rules"]
    assert request.input_data["context"]["target_main_task_order"] == 1
    assert request.input_data["examples"]
    assert "updated_main_task" in request.input_data["output_target"]


def test_build_planning_revision_ai_request_contains_format_requirements() -> None:
    request = build_planning_revision_ai_request(
        requirement_context="使用者希望細化既有規劃中的第一階段。",
        known_information=[],
        pending_confirmation=[],
        conversation_history_text=None,
        existing_plan_outline=[],
        target_main_task={
            "title": "第一階段情境重點規劃",
            "description": "整理常見情境。",
            "estimated_time": "1 小時",
            "order": 1,
            "subtasks": [],
        },
        target_main_task_order=1,
        revision_request="請把第一階段補得更詳細。",
    )

    assert request.format_requirements is not None
    assert request.format_requirements["required_fields"] == [
        "revision_summary",
        "design_rationale",
        "assumptions_used",
        "target_main_task_order",
        "updated_main_task",
    ]
    assert "Do not return the full plan or non-target main tasks." in request.format_requirements["requirements"]


def test_build_planning_revision_prompt_spec_rejects_blank_revision_request() -> None:
    try:
        build_planning_revision_prompt_spec(
            requirement_context="使用者希望細化既有規劃。",
            known_information=[],
            pending_confirmation=[],
            conversation_history_text=None,
            existing_plan_outline=[],
            target_main_task={
                "title": "第一階段",
                "description": "整理內容。",
                "estimated_time": "1 小時",
                "order": 1,
                "subtasks": [],
            },
            target_main_task_order=1,
            revision_request="   ",
        )
    except ValueError as exc:
        assert "revision_request 不可為空白" in str(exc)
        return

    raise AssertionError("Expected ValueError for blank revision_request")
