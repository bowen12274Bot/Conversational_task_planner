from sqlalchemy import select

from app.db.models import Conversation
from app.db.session import SessionLocal
from app.schemas import (
    ConversationHistoryRequest,
    ConversationHistoryResponse,
    ConversationMessage,
    ConversationTurn,
)


def get_conversation_history(
    request: ConversationHistoryRequest,
) -> ConversationHistoryResponse:
    """歷史查詢窗口，回傳指定對話的完整回合與訊息資料。"""

    db = SessionLocal()

    try:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.conversation_id == request.conversation_id
            )
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        turns: list[ConversationTurn] = []
        for turn in conversation.turns:
            messages = [
                ConversationMessage(
                    type=message.type,
                    content=message.content,
                )
                for message in turn.messages
            ]
            turns.append(
                ConversationTurn(
                    turn_id=turn.turn_id,
                    messages=messages,
                )
            )

        return ConversationHistoryResponse(
            conversation_id=request.conversation_id,
            turns=turns,
        )
    finally:
        db.close()
