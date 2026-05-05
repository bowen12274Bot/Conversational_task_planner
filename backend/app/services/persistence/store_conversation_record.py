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
        db.commit()

        return ConversationRecordStoreResult(
            conversation_id=request.conversation_id,
            turn_id=turn_id,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
