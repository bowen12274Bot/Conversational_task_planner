from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /api/conversations
# ---------------------------------------------------------------------------


class CreateConversationResponse(BaseModel):
    """建立新對話 API 的成功回應資料。"""

    # 新建立對話的識別值。
    conversation_id: str = Field(..., min_length=1)


class ConversationMessage(BaseModel):
    """單一對話訊息的基本資料結構。"""

    # 訊息角色，例如 user、ai 或 system。
    type: str = Field(..., min_length=1)
    # 訊息內容。
    content: str = Field(..., min_length=1)


class ConversationTurn(BaseModel):
    """一個互動回合的基本資料結構，包含該回合中所有訊息。"""

    # 回合識別值。
    turn_id: str = Field(..., min_length=1)
    # 該回合所含的訊息列表。
    messages: list[ConversationMessage] = Field(default_factory=list)


class ConversationHistoryRequest(BaseModel):
    """查詢指定對話歷史資料時使用的請求資料。"""

    # 要查詢的對話識別值。
    conversation_id: str = Field(..., min_length=1)


class ConversationRecordStoreRequest(BaseModel):
    """送入持久化層的單筆對話紀錄資料。"""

    # 對話識別值。
    conversation_id: str = Field(..., min_length=1)
    # 回合識別值。使用者訊息初次存入時可為空，由持久化層建立。
    turn_id: str | None = Field(default=None, min_length=1)
    # 訊息類型，例如 user、ai 或 system。
    type: str = Field(..., min_length=1)
    # 訊息內容。
    content: str = Field(..., min_length=1)


class ConversationRecordStoreResult(BaseModel):
    """對話紀錄完成存入後回傳的最小資料。"""

    # 對話識別值。
    conversation_id: str = Field(..., min_length=1)
    # 本次訊息所屬的回合識別值。
    turn_id: str = Field(..., min_length=1)


class ConversationHistoryResponse(BaseModel):
    """後端回傳對話歷史資料的結構，供前端重建對話畫面使用。"""

    # 查詢的對話識別值。
    conversation_id: str = Field(..., min_length=1)
    # 歷史回合資料列表。
    turns: list[ConversationTurn] = Field(default_factory=list)

