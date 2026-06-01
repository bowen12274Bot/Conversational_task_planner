from app.schemas import (
    PlanningResponseInput,
    StructuredMainTaskOutput,
    StructuredTaskOutput,
)
from app.services.modules.response.prompt import (
    build_planning_response_ai_request,
)


def test_build_planning_response_ai_request_contains_expected_sections() -> None:
    request = build_planning_response_ai_request(
        PlanningResponseInput(
            plan_summary="先完成需求確認，再安排核心實作與測試。",
            design_rationale="期限明確且任務尚未開始，因此先排需求確認與核心功能。",
            structured_task_output=StructuredTaskOutput(
                plan_summary="先完成需求確認，再安排核心實作與測試。",
                main_tasks=[
                    StructuredMainTaskOutput(
                        title="需求確認",
                        description="整理題目要求。",
                        estimated_time="1-2 小時",
                        order=1,
                        subtasks=[],
                    )
                ],
            ),
        )
    )

    assert request.group_name == "planning_summary"
    assert request.input_data["rules"]
    assert request.input_data["task"]
    assert request.input_data["context"]["plan_summary"] == "先完成需求確認，再安排核心實作與測試。"
    assert request.input_data["examples"]
    assert request.input_data["output_target"]
    assert request.format_requirements is not None
    assert request.format_requirements["output_type"] == "plain_text"
