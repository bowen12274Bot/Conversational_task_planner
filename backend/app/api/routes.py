from fastapi import APIRouter

from app.schemas.architecture_contracts import (
    ControllerToFrontendResponse,
    FrontendToControllerRequest,
)

router = APIRouter(prefix="/api")


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "backend connected"}


@router.get("/db-check")
def db_check() -> dict[str, str]:
    return {"status": "ok", "database": "configured"}


@router.post("/raw-request", response_model=ControllerToFrontendResponse)
def raw_request(payload: FrontendToControllerRequest) -> ControllerToFrontendResponse:
    return ControllerToFrontendResponse(
        reply_text=(
            "已收到需求。MVP1 目前先回傳控制層基本回應資料，後續再串接 "
            "Context Engineering、Questioning 與 AI service layer。"
        ),
        structured_task_output=None,
    )
