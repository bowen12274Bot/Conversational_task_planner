import json
from typing import Any

from sqlalchemy import select

from app.db.models import Conversation
from app.db.session import SessionLocal


def get_structured_task_output(conversation_id: str) -> dict[str, Any] | None:
    db = SessionLocal()

    try:
        conversation = db.scalar(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        raw_json = conversation.structured_task_output_json
        if raw_json is None or not raw_json.strip():
            return None

        payload = json.loads(raw_json)
        if not isinstance(payload, dict):
            raise ValueError("structured_task_output_json 不是合法的物件格式。")

        return payload
    finally:
        db.close()


def save_structured_task_output(
    conversation_id: str, structured_task_output: dict[str, Any] | None
) -> None:
    db = SessionLocal()

    try:
        conversation = db.scalar(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        if conversation is None:
            raise ValueError("找不到對應的 conversation_id。")

        conversation.structured_task_output_json = (
            json.dumps(structured_task_output, ensure_ascii=False)
            if structured_task_output is not None
            else None
        )
        db.commit()
    finally:
        db.close()
