from uuid import uuid4

from app.db.models import Conversation
from app.db.session import SessionLocal
from app.schemas import CreateConversationResponse


def create_conversation() -> CreateConversationResponse:
    """建立新對話窗口並回傳新生成的 conversation_id。"""

    conversation_id = str(uuid4())
    db = SessionLocal()

    try:
        conversation = Conversation(
            conversation_id=conversation_id,
            title=None,
        )
        db.add(conversation)
        db.commit()

        return CreateConversationResponse(
            conversation_id=conversation_id
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
