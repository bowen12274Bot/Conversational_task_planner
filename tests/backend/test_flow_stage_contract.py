from app.schemas.flow_contracts import (
    FlowRunState,
    FlowStageData,
    FlowStageExecutionState,
)


def test_flow_stage_data_contract_accepts_multiple_next_nodes() -> None:
    flow_stage = FlowStageData(
        system_id="F005",
        processing_unit="後端流程控制層 -> `Response Module` 或規劃相關處理",
        previous=["F004"],
        next=["F006", "F008"],
    )

    assert flow_stage.system_id == "F005"
    assert flow_stage.next == ["F006", "F008"]


def test_flow_stage_execution_state_contract_accepts_runtime_fields() -> None:
    execution_state = FlowStageExecutionState(
        current_stage_system_id="F005",
        step_status="fallback_to_stage",
        stage_retry_count=1,
    )

    assert execution_state.current_stage_system_id == "F005"
    assert execution_state.step_status == "fallback_to_stage"
    assert execution_state.stage_retry_count == 1


def test_flow_run_state_contract_accepts_flow_level_fields() -> None:
    run_state = FlowRunState(
        flow_status="running",
        total_error_count=2,
        traversed_history=["F001", "F002", "F003", "F004", "F005"],
    )

    assert run_state.flow_status == "running"
    assert run_state.total_error_count == 2
    assert run_state.traversed_history == ["F001", "F002", "F003", "F004", "F005"]
