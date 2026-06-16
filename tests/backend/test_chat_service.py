import pytest

from app.schemas import AIToModuleResult, ChatModuleInput, PlanningIntent
from app.services.modules.chat import service as chat_service
from app.services.modules.chat.validator import validate_chat_output


def _build_chat_input() -> ChatModuleInput:
    return ChatModuleInput(
        raw_requirement="第三階段的模擬試題有沒有什麼練習方向，或是學習管道可以參考？",
        requirement_context="使用者詢問第三階段的模擬試題練習方向與學習管道。",
        planning_intent=PlanningIntent(
            intent_type="chat",
            target_main_task_order=3,
            confidence="high",
        ),
        existing_plan_outline=[
            {"order": 1, "title": "第一階段：基礎建立期"},
            {"order": 2, "title": "第二階段：題型強化期"},
            {"order": 3, "title": "第三階段：實戰衝刺期"},
        ],
    )


def test_validate_chat_output_accepts_multiple_answer_types() -> None:
    result = validate_chat_output(
        {
            "answer_types": ["execution_advice", "resource_suggestion"],
            "answer": "可以先做限時模考，再整理錯題與補強弱點。",
            "referenced_plan": {
                "main_task_order": 3,
                "subtask_orders": [],
            },
            "suggested_follow_up_actions": [
                {
                    "action_type": "revise_plan",
                    "label": "將建議加入第三階段",
                }
            ],
        },
        expected_main_task_order=3,
    )

    assert result.is_valid


def test_validate_chat_output_rejects_unexpected_referenced_plan() -> None:
    result = validate_chat_output(
        {
            "answer_types": ["execution_advice"],
            "answer": "可以先做限時模考。",
            "referenced_plan": {
                "main_task_order": 2,
                "subtask_orders": [],
            },
            "suggested_follow_up_actions": [],
        },
        expected_main_task_order=3,
    )

    assert not result.is_valid
    assert result.reason == "unexpected_referenced_main_task_order"


def test_build_chat_answer_parses_ai_json_text(monkeypatch) -> None:
    monkeypatch.setattr(
        chat_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    '{"answer_types":["execution_advice","resource_suggestion"],'
                    '"answer":"可以先做限時模考，再整理錯題與補強弱點。",'
                    '"referenced_plan":{"main_task_order":3,"subtask_orders":[]},'
                    '"suggested_follow_up_actions":[]}'
                ),
            },
        ),
    )

    result = chat_service.build_chat_answer(_build_chat_input())

    assert result.answer_types == ["execution_advice", "resource_suggestion"]
    assert result.referenced_plan is not None
    assert result.referenced_plan.main_task_order == 3
    assert "限時模考" in result.answer


def test_build_chat_answer_raises_after_retry_when_output_is_invalid(monkeypatch) -> None:
    monkeypatch.setattr(
        chat_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={"text": '{"answer":"缺欄位"}'},
        ),
    )

    with pytest.raises(ValueError, match="Chat output validation failed"):
        chat_service.build_chat_answer(_build_chat_input())
