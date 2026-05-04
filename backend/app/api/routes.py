from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.schemas import (
    AIToModuleResult,
    ControllerToFrontendResponse,
    FrontendToControllerRequest,
    ModuleToAIRequest,
)
from app.services.ai_service.service import run_ai_flow

router = APIRouter(prefix="/api")

# MVP Phase 2: Conversation API Models
class CreateConversationResponse(BaseModel):
    conversation_id: str

class ConversationMessage(BaseModel):
    id: str
    type: str  # 'system' | 'user' | 'ai'
    content: str
    timestamp: str

class PlanTask(BaseModel):
    id: str
    title: str
    due: Optional[str] = None
    created_at: str
    subtasks: List[dict]  # Simplified for MVP

class ConversationHistoryResponse(BaseModel):
    messages: List[ConversationMessage]
    plan_tasks: Optional[List[PlanTask]] = None

# MVP Phase 2: In-memory conversation storage (for testing)
conversations = {}  # conversation_id -> {messages: [], plan_tasks: []}

# MVP Phase 2: Conversation API Models
class CreateConversationResponse(BaseModel):
    conversation_id: str

class ConversationMessage(BaseModel):
    id: str
    type: str  # 'system' | 'user' | 'ai'
    content: str
    timestamp: str

class PlanTask(BaseModel):
    id: str
    title: str
    due: Optional[str] = None
    created_at: str
    subtasks: List[dict]  # Simplified for MVP

class ConversationHistoryResponse(BaseModel):
    messages: List[ConversationMessage]
    plan_tasks: Optional[List[PlanTask]] = None


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "backend connected"}


@router.get("/db-check")
def db_check() -> dict[str, str]:
    return {"status": "ok", "database": "configured"}


@router.post("/raw-request", response_model=ControllerToFrontendResponse)
def raw_request(payload: FrontendToControllerRequest) -> ControllerToFrontendResponse:
    # MVP Phase 2: For now, create a simple conversation if none exists
    # In full implementation, conversation_id should come from frontend
    conversation_id = "temp-conversation"
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            'messages': [],
            'plan_tasks': []
        }

    # Add user message to conversation history
    user_message = ConversationMessage(
        id=str(uuid.uuid4()),
        type="user",
        content=payload.user_input,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]['messages'].append(user_message)

    # Generate AI response
    ai_response = (
        "目前這是 MVP1 測試用回應。後續會由後端流程控制層串接 "
        "Context Engineering、Questioning 與 AI service layer。"
    )

    # Add AI message to conversation history
    ai_message = ConversationMessage(
        id=str(uuid.uuid4()),
        type="ai",
        content=ai_response,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]['messages'].append(ai_message)

    return ControllerToFrontendResponse(
        reply_text=ai_response,
        structured_task_output=None,
    )


@router.post("/ai-test", response_model=AIToModuleResult)
def ai_test(payload: ModuleToAIRequest) -> AIToModuleResult:
    return run_ai_flow(payload)


# MVP Phase 2: Conversation APIs
@router.post("/conversations", response_model=CreateConversationResponse)
def create_conversation() -> CreateConversationResponse:
    """Create a new conversation and return conversation ID"""
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = {
        'messages': [],
        'plan_tasks': []
    }
    return CreateConversationResponse(conversation_id=conversation_id)


@router.get("/conversations/{conversation_id}/history", response_model=ConversationHistoryResponse)
def get_conversation_history(conversation_id: str) -> ConversationHistoryResponse:
    """Get conversation history including messages and plan tasks"""
    if conversation_id not in conversations:
        # Return empty history for new conversations
        return ConversationHistoryResponse(
            messages=[],
            plan_tasks=[]
        )

    conversation = conversations[conversation_id]
    return ConversationHistoryResponse(
        messages=conversation['messages'],
        plan_tasks=conversation['plan_tasks']
    )
