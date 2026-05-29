from app.db.models import Conversation
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.persistence import (
    create_conversation,
    get_conversation_transcript,
    store_conversation_record,
)
from app.schemas import ConversationRecordStoreRequest


def test_store_conversation_record_updates_conversation_history_text() -> None:
    init_db()
    created = create_conversation()

    user_store_result = store_conversation_record(
        ConversationRecordStoreRequest(
            conversation_id=created.conversation_id,
            turn_id=None,
            type="user",
            content="我要規劃這週的 API 串接工作",
        )
    )
    store_conversation_record(
        ConversationRecordStoreRequest(
            conversation_id=created.conversation_id,
            turn_id=user_store_result.turn_id,
            type="ai",
            content="你目前完成到哪裡？",
        )
    )

    history_text = get_conversation_transcript(created.conversation_id)

    assert history_text == (
        "user: 我要規劃這週的 API 串接工作\n"
        "ai: 你目前完成到哪裡？"
    )

    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == created.conversation_id
        ).one()
        assert conversation.conversation_history_text == history_text
    finally:
        db.close()
