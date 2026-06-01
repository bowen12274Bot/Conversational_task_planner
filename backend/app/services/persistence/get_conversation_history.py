from datetime import datetime, timezone
import json

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
                    created_at=_normalize_utc_timestamp(message.created_at),
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
            structured_task_output=(
                json.loads(conversation.structured_task_output_json)
                if conversation.structured_task_output_json
                else None
            ),
        )
    finally:
        db.close()


def _normalize_utc_timestamp(value: datetime) -> datetime:
    """將資料庫讀出的 naive UTC 時間標準化為帶時區資訊的 UTC。"""

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)

    return value.replace(tzinfo=timezone.utc)
