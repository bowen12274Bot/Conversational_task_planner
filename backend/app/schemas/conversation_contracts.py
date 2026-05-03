from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /api/conversations
# ---------------------------------------------------------------------------


class ConversationCreateResponse(BaseModel):
    """後端建立新對話後回傳前端的資料，包含可供後續請求使用的對話識別值。"""

    # 新建立對話的識別值，供前端後續互動與歷史查詢使用。
    conversation_id: str = Field(..., min_length=1)


class ConversationMessage(BaseModel):
    """單一對話訊息的基本資料結構。"""

    # 訊息角色，例如 user 或 assistant。
    role: str = Field(..., min_length=1)
    # 訊息內容。
    content: str = Field(..., min_length=1)


class ConversationTurn(BaseModel):
    """一個互動回合的基本資料結構，包含該回合中所有訊息。"""

    # 回合序號（從 1 開始）。
    turn_index: int = Field(..., ge=1)
    # 該回合所含的訊息列表。
    messages: list[ConversationMessage] = Field(default_factory=list)


class ConversationHistoryResponse(BaseModel):
    """後端回傳對話歷史資料的結構，供前端重建對話畫面使用。"""

    # 查詢的對話識別值。
    conversation_id: str = Field(..., min_length=1)
    # 歷史回合資料列表。
    turns: list[ConversationTurn] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 通用錯誤回應
# ---------------------------------------------------------------------------


class ConversationErrorResponse(BaseModel):
    """對話相關 API 在錯誤情境下回傳的最小錯誤資訊。"""

    # 本次錯誤的簡短描述。
    error_message: str = Field(..., min_length=1)
    # 錯誤發生的處理位置。
    error_stage: str = Field(..., min_length=1)
