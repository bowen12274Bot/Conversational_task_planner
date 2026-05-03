import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import (
    AIToModuleResult,
    ConversationCreateResponse,
    ConversationHistoryResponse,
    FrontendToControllerRequest,
    ModuleToAIRequest,
    RawRequestPayload,
    RawRequestResponse,
)
from app.services.ai_service.service import run_ai_flow

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------


def _error_response(status_code: int, error_message: str, error_stage: str) -> JSONResponse:
    """建立符合 API 規格的最小錯誤回應。"""
    return JSONResponse(
        status_code=status_code,
        content={"error_message": error_message, "error_stage": error_stage},
    )


# ---------------------------------------------------------------------------
# 維運端點
# ---------------------------------------------------------------------------


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "backend connected"}


@router.get("/db-check")
def db_check() -> dict[str, str]:
    return {"status": "ok", "database": "configured"}


# ---------------------------------------------------------------------------
# POST /api/conversations  —  建立對話
# ---------------------------------------------------------------------------


@router.post("/conversations", response_model=ConversationCreateResponse)
def create_conversation() -> ConversationCreateResponse:
    """建立新的對話，由後端生成並回傳 conversation_id。

    成功：200 OK，回傳 conversation_id。
    失敗：500 Internal Server Error，回傳 error_message 與 error_stage。

    Notes
    -----
    目前 Persistence Layer 尚未串接，conversation_id 暫由後端以 UUID4 生成。
    後續串接 Persistence Layer 後，應改由 Persistence Layer 負責生成與保存。
    """
    try:
        conversation_id = str(uuid.uuid4())
        return ConversationCreateResponse(conversation_id=conversation_id)
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"建立對話時發生錯誤：{exc}",
            error_stage="controller",
        )


# ---------------------------------------------------------------------------
# POST /api/raw-request  —  對話送出（Phase 2：含 conversation_id）
# ---------------------------------------------------------------------------


@router.post("/raw-request", response_model=RawRequestResponse)
def raw_request(payload: RawRequestPayload) -> Any:
    """承接前端送出的對話輸入，啟動後端主流程並回傳結果。

    成功：200 OK，回傳 reply_text、conversation_id 與 structured_task_output。
    失敗：
      - 400 Bad Request：缺少必要欄位或格式不正確。
      - 404 Not Found：conversation_id 查無對應對話。
      - 500 Internal Server Error：主流程處理失敗。

    Notes
    -----
    目前 conversation_id 驗證與 Persistence Layer 尚未串接，
    後續應在此處驗證 conversation_id 是否存在，以及將對話紀錄送入 Persistence Layer。
    """
    # --- 基本輸入驗證 ---
    if not payload.conversation_id or not payload.conversation_id.strip():
        return _error_response(
            status_code=400,
            error_message="conversation_id 為必填欄位，且不可為空白。",
            error_stage="controller",
        )

    if not payload.user_input or not payload.user_input.strip():
        return _error_response(
            status_code=400,
            error_message="user_input 為必填欄位，且不可為空白。",
            error_stage="controller",
        )

    # --- 主流程（MVP2 暫以固定回應代替；後續串接控制層流程）---
    try:
        reply_text = (
            "目前這是 MVP2 測試用回應。後續會由後端流程控制層串接 "
            "Context Engineering、Questioning 與 AI service layer，"
            f"並將本輪對話紀錄保存至 Persistence Layer（conversation_id: {payload.conversation_id}）。"
        )
        return RawRequestResponse(
            reply_text=reply_text,
            conversation_id=payload.conversation_id,
            structured_task_output=None,
        )
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"主流程處理時發生錯誤：{exc}",
            error_stage="controller",
        )


# ---------------------------------------------------------------------------
# GET /api/conversations/{conversation_id}/history  —  查詢歷史
# ---------------------------------------------------------------------------


@router.get(
    "/conversations/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
)
def get_conversation_history(conversation_id: str) -> Any:
    """取得指定對話的歷史回合與訊息資料，供前端重建對話畫面。

    成功：200 OK，回傳 conversation_id 與 turns 列表。
    失敗：
      - 400 Bad Request：conversation_id 格式不正確。
      - 404 Not Found：指定對話不存在。
      - 500 Internal Server Error：查詢或整理資料時發生錯誤。

    Notes
    -----
    目前 Persistence Layer 尚未串接，暫以空 turns 列表回應代替。
    後續串接 Persistence Layer 後，應向 Persistence Layer 查詢並整理歷史資料。
    """
    # --- 基本格式驗證 ---
    if not conversation_id or not conversation_id.strip():
        return _error_response(
            status_code=400,
            error_message="conversation_id 格式不正確或為空白。",
            error_stage="controller",
        )

    # --- 查詢歷史（MVP2 暫以空 turns 代替；後續串接 Persistence Layer）---
    try:
        # TODO: 串接 Persistence Layer 以取得真實歷史資料。
        #       若 conversation_id 不存在，應回傳 404。
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            turns=[],
        )
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"查詢歷史紀錄時發生錯誤：{exc}",
            error_stage="controller",
        )


# ---------------------------------------------------------------------------
# POST /api/ai-test  —  AI 服務直測
# ---------------------------------------------------------------------------


@router.post("/ai-test", response_model=AIToModuleResult)
def ai_test(payload: ModuleToAIRequest) -> AIToModuleResult:
    return run_ai_flow(payload)

