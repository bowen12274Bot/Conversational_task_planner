from pydantic import BaseModel, Field


class FlowStageData(BaseModel):
    """用於表示單一 `flow_stage` 節點在資料傳輸情境下所需內容的結構化資料物件。"""

    # 系統內部穩定引用該節點的主要識別。
    system_id: str = Field(..., min_length=1)
    # 主要涉及的架構層或模組層處理單位。
    processing_unit: str = Field(..., min_length=1)
    # 目前節點的前一個節點或前一組節點。
    previous: list[str] = Field(default_factory=list)
    # 目前節點的下一個節點、下一組節點，或流程結束狀態。
    next: list[str] = Field(default_factory=list)


class FlowStageExecutionState(BaseModel):
    """用於表示單一 `flow_stage` 節點在流程執行期間之狀態資訊的結構化資料物件。"""

    # 目前正在執行或判斷中的流程節點系統識別。
    current_stage_system_id: str = Field(..., min_length=1)
    # 目前節點本次執行結果。
    step_status: str = Field(..., min_length=1)
    # 目前節點已累積的重試次數。
    stage_retry_count: int = Field(0, ge=0)


class FlowRunState(BaseModel):
    """用於表示整體流程在執行期間之狀態資訊的結構化資料物件。"""

    # 整體流程目前的執行狀態。
    flow_status: str = Field(..., min_length=1)
    # 本輪流程從開始至目前為止累積發生的錯誤次數。
    total_error_count: int = Field(0, ge=0)
    # 本輪流程目前為止實際經過的節點紀錄。
    traversed_history: list[str] = Field(default_factory=list)
