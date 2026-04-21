from app.schemas.architecture_contracts import FlowStageData


def test_flow_stage_data_contract_accepts_multiple_next_nodes() -> None:
    flow_stage = FlowStageData(
        system_id="F005",
        processing_unit="後端流程控制層 -> `Response Module` 或規劃相關處理",
        previous=["F004"],
        next=["F006", "F008"],
    )

    assert flow_stage.system_id == "F005"
    assert flow_stage.next == ["F006", "F008"]
