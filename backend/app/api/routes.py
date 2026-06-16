from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

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
from app.services.progress_events import (
    publish_progress_event,
    subscribe_progress_events,
)

router = APIRouter(prefix="/api")

CONVERSATION_NOT_FOUND_MESSAGE = "找不到對應的 conversation_id。"


def _error_response(
    status_code: int, error_message: str, error_stage: str
) -> JSONResponse:
    """建立符合 API 規格的最小錯誤回應。"""
    error = ErrorResponse(
        error_message=error_message,
        error_stage=error_stage,
    )
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
    )


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "backend connected"}


@router.get("/db-check")
def db_check() -> dict[str, str]:
    return {"status": "ok", "database": "configured"}


@router.post(
    "/conversations",
    response_model=CreateConversationResponse,
)
def create_conversation() -> Any:
    """建立新的對話，由後端生成並回傳 conversation_id。"""
    try:
        controller = ConversationCreateController()
        return controller.handle_create_conversation()
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"建立對話時發生錯誤：{exc}",
            error_stage="controller",
        )


@router.post("/raw-request", response_model=ControllerToFrontendResponse)
def raw_request(payload: FrontendToControllerRequest) -> Any:
    """承接前端送出的對話輸入，啟動後端主流程並回傳結果。"""
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

    request_id = _extract_request_id(payload)
    publish_progress_event(
        conversation_id=payload.conversation_id,
        request_id=request_id,
        event_type="request_received",
        stage="F001",
    )

    try:
        controller = RawRequestController()
        result = controller.handle_raw_request(payload)
        publish_progress_event(
            conversation_id=payload.conversation_id,
            request_id=request_id,
            event_type="completed",
            stage=getattr(controller, "current_stage", None),
        )
        return result
    except ValueError as exc:
        publish_progress_event(
            conversation_id=payload.conversation_id,
            request_id=request_id,
            event_type="failed",
            stage="controller",
        )
        if str(exc) == CONVERSATION_NOT_FOUND_MESSAGE:
            return _error_response(
                status_code=404,
                error_message=str(exc),
                error_stage="controller",
            )
        return _error_response(
            status_code=500,
            error_message=f"主流程處理時發生錯誤：{exc}",
            error_stage="controller",
        )
    except Exception as exc:
        publish_progress_event(
            conversation_id=payload.conversation_id,
            request_id=request_id,
            event_type="failed",
            stage="controller",
        )
        return _error_response(
            status_code=500,
            error_message=f"主流程處理時發生錯誤：{exc}",
            error_stage="controller",
        )


@router.get("/conversations/{conversation_id}/events")
async def get_conversation_events(conversation_id: str, request_id: str) -> StreamingResponse:
    """Subscribe to progress events for one conversation request."""

    return StreamingResponse(
        subscribe_progress_events(
            conversation_id=conversation_id,
            request_id=request_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/conversations/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
)
def get_conversation_history(conversation_id: str) -> Any:
    """取得指定對話的歷史回合與訊息資料，供前端重建對話畫面。"""
    if not conversation_id or not conversation_id.strip():
        return _error_response(
            status_code=400,
            error_message="conversation_id 格式不正確或為空白。",
            error_stage="controller",
        )

    try:
        controller = ConversationHistoryController()
        return controller.handle_conversation_history(conversation_id)
    except ValueError as exc:
        if str(exc) == CONVERSATION_NOT_FOUND_MESSAGE:
            return _error_response(
                status_code=404,
                error_message=str(exc),
                error_stage="controller",
            )
        return _error_response(
            status_code=500,
            error_message=f"查詢歷史紀錄時發生錯誤：{exc}",
            error_stage="controller",
        )
    except Exception as exc:
        return _error_response(
            status_code=500,
            error_message=f"查詢歷史紀錄時發生錯誤：{exc}",
            error_stage="controller",
        )


@router.post("/ai-test", response_model=AIToModuleResult)
def ai_test(payload: ModuleToAIRequest) -> AIToModuleResult:
    return run_ai_flow(payload)


def _extract_request_id(payload: FrontendToControllerRequest) -> str | None:
    request_id = payload.interaction_info.get("request_id")
    if isinstance(request_id, str) and request_id.strip():
        return request_id.strip()
    return None
