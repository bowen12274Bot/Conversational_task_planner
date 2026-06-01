from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.models import (
    Conversation,
    ConversationTurn as ConversationTurnModel,
    TurnMessage as TurnMessageModel,
)
from app.db.session import SessionLocal
from app.schemas import (
    ConversationRecordStoreRequest,
    ConversationRecordStoreResult,
)


def store_conversation_record(
    request: ConversationRecordStoreRequest,
) -> ConversationRecordStoreResult:
    """對話紀錄存入窗口，依 user/ai 規則寫入對話回合與訊息。"""

    if request.type == "ai" and not request.turn_id:
        raise ValueError(
            "AI 訊息存入持久化層時必須提供既有 turn_id。"
        )

    db = SessionLocal()

    try:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.conversation_id == request.conversation_id
            )
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        if request.type == "user" and not request.turn_id:
            turn_id = str(uuid4())
            turn = ConversationTurnModel(
                conversation_pk=conversation.conversation_pk,
                turn_id=turn_id,
            )
            db.add(turn)
            db.flush()
            message_index = 0
        elif request.turn_id:
            turn_id = request.turn_id or ""
            turn = db.scalar(
                select(ConversationTurnModel).where(
                    ConversationTurnModel.turn_id == turn_id,
                    ConversationTurnModel.conversation_pk
                    == conversation.conversation_pk,
                )
            )
            if turn is None:
                raise ValueError("找不到對應的 turn_id。")

            message_index = len(turn.messages)
        else:
            raise ValueError("寫入既有 turn 時必須提供 turn_id。")

        message = TurnMessageModel(
            turn_pk=turn.turn_pk,
            message_index=message_index,
            type=request.type,
            content=request.content,
        )
        db.add(message)
        db.flush()

        conversation.conversation_history_text = _build_conversation_history_text(
            db=db,
            conversation_pk=conversation.conversation_pk,
        )
        db.commit()

        return ConversationRecordStoreResult(
            conversation_id=request.conversation_id,
            turn_id=turn_id,
            message_created_at=_normalize_utc_timestamp(message.created_at),
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _normalize_utc_timestamp(value: datetime) -> datetime:
    """將資料庫讀出的 naive UTC 時間標準化為帶時區資訊的 UTC。"""

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)

    return value.replace(tzinfo=timezone.utc)


def _build_conversation_history_text(db, conversation_pk: int) -> str | None:
    """依現有 turn/message 順序重建完整對話歷史文字。"""

    rows = db.execute(
        select(
            TurnMessageModel.type,
            TurnMessageModel.content,
        )
        .join(
            ConversationTurnModel,
            TurnMessageModel.turn_pk == ConversationTurnModel.turn_pk,
        )
        .where(ConversationTurnModel.conversation_pk == conversation_pk)
        .order_by(
            ConversationTurnModel.created_at,
            TurnMessageModel.message_index,
            TurnMessageModel.created_at,
        )
    ).all()

    history_lines = [
        f"{message_type}: {content}"
        for message_type, content in rows
    ]
    if not history_lines:
        return None

    return "\n".join(history_lines)
