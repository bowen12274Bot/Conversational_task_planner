from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.controllers.conversation_create_controller import (
    ConversationCreateController,
)
from app.controllers.conversation_history_controller import (
    ConversationHistoryController,
)
from app.controllers.raw_request_controller import RawRequestController
from app.schemas import (
    AIToModuleResult,
    CreateConversationResponse,
    ConversationHistoryResponse,
    ControllerToFrontendResponse,
    ErrorResponse,
    FrontendToControllerRequest,
    ModuleToAIRequest,
)
from app.services.ai_service.service import run_ai_flow

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------


def _error_response(status_code: int, error_message: str, error_stage: str) -> JSONResponse:
    """建立符合 API 規格的最小錯誤回應。"""
    error = ErrorResponse(
        error_message=error_message,
        error_stage=error_stage,
    )
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
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


@router.post(
    "/conversations",
    response_model=CreateConversationResponse,
)
def create_conversation() -> Any:
    """建立新的對話，由後端生成並回傳 conversation_id。

    成功：200 OK，回傳 conversation_id。
    失敗：500 Internal Server Error，回傳 error_message 與 error_stage。
    """
    try:
        controller = ConversationCreateController()
        return controller.handle_create_conversation()
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"建立對話時發生錯誤：{exc}",
            error_stage="controller",
        )


# ---------------------------------------------------------------------------
# POST /api/raw-request  —  對話送出（Phase 2：含 conversation_id）
# ---------------------------------------------------------------------------


@router.post("/raw-request", response_model=ControllerToFrontendResponse)
def raw_request(payload: FrontendToControllerRequest) -> Any:
    """承接前端送出的對話輸入，啟動後端主流程並回傳結果。

    成功：200 OK，回傳 reply_text、conversation_id 與 structured_task_output。
    失敗：
      - 400 Bad Request：缺少必要欄位或格式不正確。
      - 404 Not Found：conversation_id 查無對應對話。
      - 500 Internal Server Error：主流程處理失敗。
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
        controller = RawRequestController()
        return controller.handle_raw_request(payload)
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
    """
    # --- 基本格式驗證 ---
    if not conversation_id or not conversation_id.strip():
        return _error_response(
            status_code=400,
            error_message="conversation_id 格式不正確或為空白。",
            error_stage="controller",
        )

    # --- 查詢歷史 ---
    try:
        controller = ConversationHistoryController()
        return controller.handle_conversation_history(conversation_id)
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

