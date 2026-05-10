from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.controllers import raw_request_controller as raw_request_module
from app.schemas import ContextEngineeringOutput, QuestioningDecision, ResponseOutput


def test_raw_request_requires_conversation_id(client: TestClient) -> None:
    response = client.post(
        "/api/raw-request",
        json={"user_input": "我想把這週的 API 串接工作排出來"},
    )

    assert response.status_code == 400

    body = response.json()
    assert body["error_stage"] == "controller"
    assert "conversation_id" in body["error_message"]


def test_raw_request_runs_follow_up_branch_and_returns_reply_text(
    client: TestClient,
    monkeypatch,
) -> None:
    stored_records: list[dict[str, str | None]] = []

    def fake_store(record):
        stored_records.append(
            {
                "conversation_id": record.conversation_id,
                "turn_id": record.turn_id,
                "type": record.type,
                "content": record.content,
            }
        )
        if record.type == "user":
            return SimpleNamespace(
                conversation_id=record.conversation_id,
                turn_id="turn-001",
            )

        return SimpleNamespace(
            conversation_id=record.conversation_id,
            turn_id=record.turn_id,
        )

    monkeypatch.setattr(raw_request_module, "store_conversation_record", fake_store)
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, history_context_summary=None: ContextEngineeringOutput(
            requirement_context="整理後摘要",
            known_information=[],
            pending_confirmation=[{"label": "time_budget", "question_hint": "每天能投入多久？"}],
            history_context_summary=history_context_summary,
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "evaluate_questioning_need",
        lambda context_output: QuestioningDecision(
            is_ready_for_planning=False,
            reasoning="資訊不足，需要追問。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_response_from_questioning",
        lambda questioning_decision: ResponseOutput(
            reply_text="請先補充每天可投入的時間。",
            response_type="follow_up_question",
        ),
    )

    response = client.post(
        "/api/raw-request",
        json={
            "conversation_id": "conv-001",
            "user_input": "我想把這週的 API 串接工作排出來",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == "conv-001"
    assert body["reply_text"] == "請先補充每天可投入的時間。"
    assert body["structured_task_output"] is None
    assert stored_records == [
        {
            "conversation_id": "conv-001",
            "turn_id": None,
            "type": "user",
            "content": "我想把這週的 API 串接工作排出來",
        },
        {
            "conversation_id": "conv-001",
            "turn_id": "turn-001",
            "type": "ai",
            "content": "請先補充每天可投入的時間。",
        },
    ]
