from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /api/conversations
# ---------------------------------------------------------------------------


class ConversationCreateResponse(BaseModel):
    """後端建立新對話後回傳前端的資料，包含可供後續請求使用的對話識別值。"""

    # 新建立對話的識別值，供前端後續互動與歷史查詢使用。
    conversation_id: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# POST /api/raw-request（Phase 2 擴充：加入 conversation_id）
# ---------------------------------------------------------------------------


class RawRequestPayload(BaseModel):
    """Phase 2 版本的前端送出對話請求資料，包含使用者輸入與所屬對話識別值。"""

    # 使用者原始輸入內容。
    user_input: str = Field(..., min_length=1)
    # 本次請求所屬的既有對話識別值。
    conversation_id: str = Field(..., min_length=1)


class RawRequestResponse(BaseModel):
    """後端處理對話送出後回傳前端的回應資料。"""

    # 顯示給使用者的回覆文字。
    reply_text: str = Field(..., min_length=1)
    # 所屬對話的識別值，供前端確認本輪互動歸屬。
    conversation_id: str = Field(..., min_length=1)
    # 已完成整理、可提供前端顯示的任務排版資料（選填）。
    structured_task_output: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# GET /api/conversations/{conversation_id}/history
# ---------------------------------------------------------------------------


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
