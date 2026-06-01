from sqlalchemy import select

from app.db.models import Conversation
from app.db.session import SessionLocal


def get_conversation_transcript(conversation_id: str) -> str | None:
    """取得指定對話目前聚合後的完整對話逐字內容。"""

    db = SessionLocal()

    try:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id
            )
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        return conversation.conversation_history_text
    finally:
        db.close()
