from typing import Any

from pydantic import BaseModel, Field


class FrontendToControllerRequest(BaseModel):
    """由前端送入後端控制層的請求資料，作為系統啟動本次互動處理流程的起點。"""

    # 使用者原始輸入內容。
    user_input: str = Field(..., min_length=1)
    # 本次請求所屬的既有對話識別值。
    conversation_id: str | None = Field(default=None, min_length=1)
    # 本次互動的基本資訊，先維持彈性結構。
    interaction_info: dict[str, Any] = Field(default_factory=dict)


class ControllerToFrontendResponse(BaseModel):
    """由後端控制層回傳前端的回應資料，用於提供前端更新畫面與顯示本次互動結果。"""

    # 顯示給使用者的回覆文字。
    reply_text: str = Field(..., min_length=1)
    # 本輪互動所屬的對話識別值。
    conversation_id: str | None = Field(default=None, min_length=1)
    # 已完成整理、可提供前端顯示的任務排版資料。
    structured_task_output: dict[str, Any] | None = None


class ControllerFlowState(BaseModel):
    """由後端控制層依據固定流程程式邏輯所產生的目前流程位置資料，用於表達系統目前位於哪一個流程階段，以及下一步應進入哪一段處理。"""

    # 系統目前所在的流程階段。
    flow_stage: str = Field(..., min_length=1)
    # 控制層決定的下一步目標。
    next_step_target: str = Field(..., min_length=1)


class ControllerTransferData(BaseModel):
    """由後端控制層整理並轉交給下一個模組或輸出路徑的資料，用於承接前一段流程結果並銜接後續處理。"""

    # 需轉交的資料內容。
    transfer_data: dict[str, Any] = Field(default_factory=dict)
    # 本次資料的轉交目標。
    transfer_target: str = Field(..., min_length=1)


class ControllerToResponseData(BaseModel):
    """由後端控制層整理並轉交給文字輸出處理的資料，用於生成對使用者顯示的文字回覆。"""

    # 目前所在流程階段。
    flow_stage: str = Field(..., min_length=1)
    # 本次文字回覆要完成的回覆目標。
    response_goal: str = Field(..., min_length=1)
    # 提供文字輸出處理承接的資料內容。
    transfer_data: dict[str, Any] = Field(default_factory=dict)


class ModuleToAIRequest(BaseModel):
    """由模組送交 `AI service layer` 的任務資料，用於表達本次 AI 任務的用途、輸入內容與輸出要求。"""

    # 本次 AI 任務的任務類型。
    task_type: str = Field(..., min_length=1)
    # 本次任務所屬的分組名稱。
    group_name: str = Field(..., min_length=1)
    # 本次任務應採用的模型能力等級。
    capability_level: str = Field(..., min_length=1)
    # 提供給 AI 任務的輸入資料。
    input_data: dict[str, Any] = Field(default_factory=dict)
    # 本次 AI 任務希望達成的輸出目標或參考模板。
    output_target: str = Field(..., min_length=1)
    # 可選的格式要求或欄位限制。
    format_requirements: dict[str, Any] | None = None


class AIToModuleResult(BaseModel):
    """由 `AI service layer` 回傳給模組的任務結果資料，用於表示本次 AI 任務是否成功完成，並提供可被模組承接的結果或錯誤資訊。"""

    # 本次 AI 任務是否成功完成。
    success: bool
    # 任務成功時可供模組承接的輸出結果。
    output_result: dict[str, Any] | str | None = None
    # 任務失敗時的最小錯誤資訊。
    error_message: str | None = None
    # 錯誤大致發生的處理階段。
    error_stage: str | None = None
