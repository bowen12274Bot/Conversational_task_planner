from fastapi.testclient import TestClient
from datetime import datetime
from types import SimpleNamespace

from app.controllers import raw_request_controller as raw_request_module
from app.schemas import (
    ContextEngineeringOutput,
    PlanningCreateOutput,
    PlanningMainTask,
    PlanningRevisionOutput,
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
                message_created_at=datetime(2026, 6, 2, 10, 30, 0),
            )

        return SimpleNamespace(
            conversation_id=record.conversation_id,
            turn_id=record.turn_id,
            message_created_at=datetime(2026, 6, 2, 10, 30, 30),
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
        "get_structured_task_output",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, conversation_id=None, existing_plan_outline=None: ContextEngineeringOutput(
            requirement_context="整理後摘要",
            known_information=[],
            pending_confirmation=[{"label": "time_budget", "question_hint": "每天能投入多久？"}],
            conversation_history_text=None,
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "evaluate_questioning_need",
        lambda context_output, follow_up_round_count, has_existing_plan=False, existing_plan_outline=None: QuestioningDecision(
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
    assert body["reply_created_at"].endswith("Z") or body["reply_created_at"].endswith("+00:00")
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
    saved_structured_outputs: list[tuple[str, dict[str, object] | None]] = []
    stored_records: list[dict[str, str | None]] = []

    monkeypatch.setattr(
        raw_request_module,
        "store_conversation_record",
        lambda record: (
            stored_records.append(
                {
                    "conversation_id": record.conversation_id,
                    "turn_id": record.turn_id,
                    "type": record.type,
                    "content": record.content,
                }
            )
            or SimpleNamespace(
                conversation_id=record.conversation_id,
                turn_id="turn-001",
                message_created_at=datetime(2026, 6, 2, 11, 0, 0),
            )
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_follow_up_round_count",
        lambda conversation_id: 1,
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_structured_task_output",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, conversation_id=None, existing_plan_outline=None: ContextEngineeringOutput(
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
        lambda context_output, follow_up_round_count, has_existing_plan=False, existing_plan_outline=None: QuestioningDecision(
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
        "save_structured_task_output",
        lambda conversation_id, structured_task_output: saved_structured_outputs.append(
            (conversation_id, structured_task_output)
        ),
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
    monkeypatch.setattr(
        raw_request_module,
        "build_response_from_planning",
        lambda planning_response_input: ResponseOutput(
            reply_text="我先整理出一版初步規劃，已經放在右側規劃面板。",
            response_type="planning_summary",
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
    assert body["reply_text"] == "我先整理出一版初步規劃，已經放在右側規劃面板。"
    assert body["reply_created_at"].endswith("Z") or body["reply_created_at"].endswith("+00:00")
    assert body["structured_task_output"]["plan_summary"] == "先確認需求，再完成核心功能與測試。"
    assert body["structured_task_output"]["summary_metrics"]["daily_time_budget_text"] == "待確認"
    assert "estimated_completion_text" in body["structured_task_output"]["summary_metrics"]
    assert body["structured_task_output"]["main_tasks"][0]["title"] == "確認需求"
    assert reset_calls == ["conv-002"]
    assert saved_structured_outputs == [("conv-002", body["structured_task_output"])]
    assert stored_records == [
        {
            "conversation_id": "conv-002",
            "turn_id": None,
            "type": "user",
            "content": "我想把 Java 作業在 7 天內做完",
        },
        {
            "conversation_id": "conv-002",
            "turn_id": "turn-001",
            "type": "ai",
            "content": "我先整理出一版初步規劃，已經放在右側規劃面板。",
        },
    ]


def test_raw_request_revises_existing_plan_without_rebuilding_other_main_tasks(
    client: TestClient,
    monkeypatch,
) -> None:
    existing_structured_output = {
        "plan_summary": "針對三個階段建立多益準備路線。",
        "summary_metrics": {
            "total_estimated_time_text": "約 3 小時",
            "daily_time_budget_text": "一天2小時",
            "estimated_completion_text": "待確認",
        },
        "main_tasks": [
            {
                "title": "第一階段情境重點規劃",
                "description": "鎖定多益常見生活與商務情境。",
                "estimated_time": "1 小時",
                "order": 1,
                "subtasks": [
                    {
                        "title": "核心情境分類",
                        "description": "整理常見情境。",
                        "priority": "high",
                        "estimated_time": "30 分鐘",
                        "order": 1,
                    },
                    {
                        "title": "基礎文法對應",
                        "description": "將文法重點與情境結合。",
                        "priority": "medium",
                        "estimated_time": "30 分鐘",
                        "order": 2,
                    },
                ],
            },
            {
                "title": "學習管道與工具建議",
                "description": "提供適合每日 2 小時利用的有效學習途徑。",
                "estimated_time": "1 小時",
                "order": 2,
                "subtasks": [
                    {
                        "title": "數位學習工具",
                        "description": "整理 APP 與網站。",
                        "priority": "high",
                        "estimated_time": "30 分鐘",
                        "order": 1,
                    }
                ],
            },
            {
                "title": "題型突破與模擬練習",
                "description": "安排考題訓練。",
                "estimated_time": "1 小時",
                "order": 3,
                "subtasks": [
                    {
                        "title": "模擬測驗",
                        "description": "完成一回模擬題。",
                        "priority": "medium",
                        "estimated_time": "1 小時",
                        "order": 1,
                    }
                ],
            },
        ],
    }
    saved_structured_outputs: list[tuple[str, dict[str, object] | None]] = []
    initial_planning_calls: list[object] = []
    revision_inputs: list[object] = []

    monkeypatch.setattr(
        raw_request_module,
        "store_conversation_record",
        lambda record: SimpleNamespace(
            conversation_id=record.conversation_id,
            turn_id=record.turn_id or "turn-003",
            message_created_at=datetime(2026, 6, 2, 12, 0, 0),
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_structured_task_output",
        lambda conversation_id: existing_structured_output,
    )
    monkeypatch.setattr(
        raw_request_module,
        "get_follow_up_round_count",
        lambda conversation_id: 0,
    )
    monkeypatch.setattr(
        raw_request_module,
        "reset_follow_up_round_count",
        lambda conversation_id: None,
    )
    monkeypatch.setattr(
        raw_request_module,
        "save_structured_task_output",
        lambda conversation_id, structured_task_output: saved_structured_outputs.append(
            (conversation_id, structured_task_output)
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_context_from_raw_input",
        lambda user_input, conversation_id=None, existing_plan_outline=None: ContextEngineeringOutput(
            requirement_context="使用者希望細化既有規劃中的第一階段，補充練習情境與學習管道。",
            known_information=[
                {"label": "task_type", "value": "多益學習計畫"},
                {"label": "time_budget", "value": "一天2小時"},
            ],
            pending_confirmation=[],
            conversation_history_text=None,
            planning_intent={
                "intent_type": "revise",
                "target_main_task_order": 1,
                "confidence": "high",
            },
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "evaluate_questioning_need",
        lambda context_output, follow_up_round_count, has_existing_plan=False, existing_plan_outline=None: QuestioningDecision(
            decision="planning",
            reasoning="修改目標清楚，可進入規劃修改。",
            known_information=context_output.known_information,
            pending_confirmation=context_output.pending_confirmation,
            next_step_guidance=["可針對第一階段進行局部修改。"],
        ),
    )
    monkeypatch.setattr(
        raw_request_module,
        "build_initial_planning",
        lambda planning_input: initial_planning_calls.append(planning_input),
    )

    def fake_build_revised_planning(planning_input):
        revision_inputs.append(planning_input)
        return PlanningRevisionOutput(
            revision_summary="已將第一階段補上更具體的情境練習與學習管道。",
            design_rationale="使用者要求細化第一階段，因此只更新該階段內容。",
            assumptions_used=[],
            target_main_task_order=1,
            updated_main_task=PlanningMainTask(
                title="第一階段情境重點規劃",
                description="針對多益常見生活與商務情境建立具體練習安排。",
                estimated_time="1 小時",
                order=1,
                subtasks=[
                    PlanningSubtask(
                        title="生活情境練習",
                        description="練習交通、餐廳、購物與住宿情境。",
                        priority="high",
                        estimated_time="30 分鐘",
                        order=1,
                    ),
                    PlanningSubtask(
                        title="學習管道整理",
                        description="搭配 APP、影片與題庫練習情境字彙。",
                        priority="medium",
                        estimated_time="30 分鐘",
                        order=2,
                    ),
                ],
            ),
        )

    monkeypatch.setattr(
        raw_request_module,
        "build_revised_planning",
        fake_build_revised_planning,
    )

    response = client.post(
        "/api/raw-request",
        json={
            "conversation_id": "conv-003",
            "user_input": "請問第一階段時可以針對哪些情境練習，以及有沒有甚麼管道能學習",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert initial_planning_calls == []
    assert len(revision_inputs) == 1
    assert revision_inputs[0].target_main_task_order == 1
    assert body["structured_task_output"]["main_tasks"][0]["description"] == (
        "針對多益常見生活與商務情境建立具體練習安排。"
    )
    assert body["structured_task_output"]["main_tasks"][1] == existing_structured_output["main_tasks"][1]
    assert body["structured_task_output"]["main_tasks"][2] == existing_structured_output["main_tasks"][2]
    assert body["reply_text"].startswith("已更新「第一階段情境重點規劃」")
    assert saved_structured_outputs == [("conv-003", body["structured_task_output"])]
