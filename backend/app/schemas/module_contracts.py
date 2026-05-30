from typing import Any, Literal

from pydantic import BaseModel, Field


class RequirementInput(BaseModel):
    """使用者提交的原始自然語言需求，作為整個流程的起點。"""

    # 保留使用者最原始的需求表達。
    user_input: str = Field(..., min_length=1)


class ContextEngineeringOutput(BaseModel):
    """由 `Context Engineering Module` 根據原始需求與歷史脈絡整理出的可用資訊基礎。"""

    # 由原始需求整理出的需求脈絡。
    requirement_context: str = Field(..., min_length=1)
    # 目前已知、可直接使用的資訊集合。
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    # 仍待確認、暫不直接採用的資訊集合。
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    # 與目前需求相關的歷史脈絡摘要。
    history_context_summary: str | None = None


class QuestioningDecision(BaseModel):
    """由 `Questioning Module` 根據 `Context Engineering` 整理結果所產出的判斷資料。"""

    # 本輪下一步應採取的方向。
    decision: Literal["follow_up", "planning"]
    # 對此判斷的原因說明。
    reasoning: str = Field(..., min_length=1)
    # 延用目前已知資訊集合。
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    # 延用目前待確認資訊集合。
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    # 下一步建議內容，依 decision 語意解讀。
    next_step_guidance: list[str] = Field(default_factory=list)


class ResponseOutput(BaseModel):
    """由 `Response Module` 根據 `Questioning 判斷結果` 所生成的、適合提供前端顯示的最終回覆內容。"""

    # 適合直接顯示給使用者的回覆文字。
    reply_text: str = Field(..., min_length=1)
    # 回覆在互動流程中的類型。現階段僅明確支援追問引導回覆。
    response_type: Literal["follow_up_question"]
