from sqlalchemy import select

from app.db.models import Conversation
from app.db.session import SessionLocal


def get_follow_up_round_count(conversation_id: str) -> int:
    """讀取指定對話目前累積的追問次數。"""

    db = SessionLocal()
    try:
        conversation = db.scalar(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        return conversation.follow_up_round_count
    finally:
        db.close()


def increment_follow_up_round_count(conversation_id: str) -> int:
    """在實際進入追問分支時累加追問次數。"""

    return _update_follow_up_round_count(conversation_id, action="increment")


def reset_follow_up_round_count(conversation_id: str) -> int:
    """在流程進入規劃分支時重置追問次數。"""

    return _update_follow_up_round_count(conversation_id, action="reset")


def _update_follow_up_round_count(
    conversation_id: str,
    action: str,
) -> int:
    db = SessionLocal()
    try:
        conversation = db.scalar(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        if action == "increment":
            conversation.follow_up_round_count += 1
        elif action == "reset":
            conversation.follow_up_round_count = 0
        else:
            raise ValueError(f"Unsupported follow_up_round_count action: {action}")

        db.commit()
        db.refresh(conversation)
        return conversation.follow_up_round_count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
