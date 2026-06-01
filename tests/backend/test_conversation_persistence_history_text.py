from app.db.models import Conversation
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.persistence import (
    create_conversation,
    get_conversation_history,
    get_structured_task_output,
    save_structured_task_output,
    get_conversation_transcript,
    store_conversation_record,
)
from app.schemas import ConversationHistoryRequest, ConversationRecordStoreRequest


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


def test_conversation_history_returns_persisted_structured_task_output() -> None:
    init_db()
    created = create_conversation()

    user_store_result = store_conversation_record(
        ConversationRecordStoreRequest(
            conversation_id=created.conversation_id,
            turn_id=None,
            type="user",
            content="我要在 7 天內完成 Java 作業",
        )
    )
    store_conversation_record(
        ConversationRecordStoreRequest(
            conversation_id=created.conversation_id,
            turn_id=user_store_result.turn_id,
            type="ai",
            content="目前這份 Java 作業已經完成到什麼程度了呢？",
        )
    )

    structured_task_output = {
        "plan_summary": "先確認需求，再完成核心功能與測試。",
        "main_tasks": [
            {
                "title": "確認需求",
                "description": "整理作業要求。",
                "estimated_time": "1 小時",
                "order": 1,
                "subtasks": [
                    {
                        "title": "閱讀題目說明",
                        "description": "確認題目與限制。",
                        "priority": "high",
                        "estimated_time": "30 分鐘",
                        "order": 1,
                    }
                ],
            }
        ],
    }
    save_structured_task_output(created.conversation_id, structured_task_output)

    assert get_structured_task_output(created.conversation_id) == structured_task_output

    history = get_conversation_history(
        ConversationHistoryRequest(conversation_id=created.conversation_id)
    )

    assert history.conversation_id == created.conversation_id
    assert history.structured_task_output == structured_task_output
    assert history.turns[0].messages[0].content == "我要在 7 天內完成 Java 作業"
