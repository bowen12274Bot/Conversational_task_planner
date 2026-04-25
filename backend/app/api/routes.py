from fastapi import APIRouter

from app.schemas import (
    AIToModuleResult,
    ControllerToFrontendResponse,
    FrontendToControllerRequest,
    ModuleToAIRequest,
)
from app.services.ai_service.service import run_ai_flow

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
            "目前這是 MVP1 測試用回應。後續會由後端流程控制層串接 "
            "Context Engineering、Questioning 與 AI service layer。"
        ),
        structured_task_output=None,
    )


@router.post("/ai-test", response_model=AIToModuleResult)
def ai_test(payload: ModuleToAIRequest) -> AIToModuleResult:
    return run_ai_flow(payload)
