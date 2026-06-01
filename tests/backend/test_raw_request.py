from fastapi.testclient import TestClient
from types import SimpleNamespace

from app.controllers import raw_request_controller as raw_request_module
from app.schemas import (
    ContextEngineeringOutput,
    PlanningCreateOutput,
    PlanningMainTask,
    PlanningSchedule,
    PlanningSubtask,
    QuestioningDecision,
    ResponseOutput,
)


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
    follow_up_counter_calls: list[str] = []

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
        "increment_follow_up_round_count",
        lambda conversation_id: follow_up_counter_calls.append(conversation_id),
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_follow_up_round_count",
        lambda conversation_id: 0,
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, conversation_id=None: ContextEngineeringOutput(
            requirement_context="整理後摘要",
            known_information=[],
            pending_confirmation=[{"label": "time_budget", "question_hint": "每天能投入多久？"}],
            conversation_history_text=None,
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "evaluate_questioning_need",
        lambda context_output, follow_up_round_count: QuestioningDecision(
            decision="follow_up",
            reasoning="資訊不足，需要追問。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            next_step_guidance=["每天大約可以投入多少時間？"],
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
    assert follow_up_counter_calls == ["conv-001"]


def test_raw_request_resets_follow_up_round_count_when_entering_planning(
    client: TestClient,
    monkeypatch,
) -> None:
    reset_calls: list[str] = []

    monkeypatch.setattr(
        raw_request_module,
        "store_conversation_record",
        lambda record: SimpleNamespace(
            conversation_id=record.conversation_id,
            turn_id="turn-001",
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_follow_up_round_count",
        lambda conversation_id: 1,
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, conversation_id=None: ContextEngineeringOutput(
            requirement_context="整理後摘要",
            known_information=[
                {"label": "task_type", "value": "Java 作業"},
                {"label": "deadline_hint", "value": "7 天內"},
            ],
            pending_confirmation=[],
            conversation_history_text=None,
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "evaluate_questioning_need",
        lambda context_output, follow_up_round_count: QuestioningDecision(
            decision="planning",
            reasoning="資訊足夠，可進入規劃。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            next_step_guidance=["可先進行初步規劃。"],
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "reset_follow_up_round_count",
        lambda conversation_id: reset_calls.append(conversation_id),
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_initial_planning",
        lambda planning_input: PlanningCreateOutput(
            plan_summary="先確認需求，再完成核心功能與測試。",
            design_rationale="目前期限與任務目標已明確，因此可直接建立初步規劃。",
            assumptions_used=[],
            schedule=PlanningSchedule(
                main_tasks=[
                    PlanningMainTask(
                        title="確認需求",
                        description="整理作業要求。",
                        estimated_time="1h",
                        order=1,
                        subtasks=[
                            PlanningSubtask(
                                title="閱讀題目說明",
                                description="確認題目與限制。",
                                priority="high",
                                estimated_time="30m",
                                order=1,
                            )
                        ],
                    )
                ]
            ),
        ),
    )

    response = client.post(
        "/api/raw-request",
        json={
            "conversation_id": "conv-002",
            "user_input": "我想把 Java 作業在 7 天內做完",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == "conv-002"
    assert body["reply_text"] == "先確認需求，再完成核心功能與測試。"
    assert body["structured_task_output"]["plan_summary"] == "先確認需求，再完成核心功能與測試。"
    assert body["structured_task_output"]["main_tasks"][0]["title"] == "確認需求"
    assert reset_calls == ["conv-002"]
