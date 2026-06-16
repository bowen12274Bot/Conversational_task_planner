from app.schemas import (
    AIToModuleResult,
    ChatModuleOutput,
    ChatResponseInput,
    PlanningResponseInput,
    StructuredSummaryMetricsOutput,
    StructuredTaskOutput,
)
from app.services.modules.response import service as response_service


def test_extract_response_text_keeps_only_final_follow_up_reply() -> None:
    ai_result = AIToModuleResult(
        success=True,
        output_result={
            "text": (
                "Helpful planning assistant.\n"
                "Natural Traditional Chinese (Taiwan).\n"
                "* Draft 1: 為了幫你規劃得更準確，我想先確認目前進度。\n"
                "Final Polish:\n"
                "為了幫你做出更準確的規劃，我想先確認兩件事：目前作業進行到哪裡了？難度大約是什麼程度呢？"
            ),
            "provider": "mock",
            "model_name": "mock-model",
        },
    )

    reply_text = response_service._extract_response_text(ai_result)

    assert (
        reply_text
        == "為了幫你做出更準確的規劃，我想先確認兩件事：目前作業進行到哪裡了？難度大約是什麼程度呢？"
    )


def test_extract_response_text_unwraps_final_quoted_reply() -> None:
    ai_result = AIToModuleResult(
        success=True,
        output_result={
            "text": (
                "* Constraint check\n"
                "\"為了幫你安排得更準確，我想先確認兩件事：這份作業預計什麼時候完成？目前進度如何？\""
            ),
            "provider": "mock",
            "model_name": "mock-model",
        },
    )

    reply_text = response_service._extract_response_text(ai_result)

    assert (
        reply_text
        == "為了幫你安排得更準確，我想先確認兩件事：這份作業預計什麼時候完成？目前進度如何？"
    )


def test_build_fallback_planning_response_returns_plain_text_summary() -> None:
    result = response_service._build_fallback_planning_response(
        PlanningResponseInput(
            plan_summary="先完成需求確認，再安排核心實作與測試。",
            design_rationale="期限明確，因此先排需求確認與核心實作。",
            structured_task_output=StructuredTaskOutput(
                plan_summary="先完成需求確認，再安排核心實作與測試。",
                summary_metrics=StructuredSummaryMetricsOutput(
                    total_estimated_time_text="待確認",
                    daily_time_budget_text="待確認",
                    estimated_completion_text="待確認",
                ),
                main_tasks=[],
            ),
        )
    )

    assert result.response_type == "planning_summary"
    assert "右側規劃面板" in result.reply_text
    assert "先完成需求確認，再安排核心實作與測試" in result.reply_text


def test_build_response_from_chat_returns_chat_answer_without_ai_call() -> None:
    result = response_service.build_response_from_chat(
        ChatResponseInput(
            chat_output=ChatModuleOutput(
                answer_types=["execution_advice", "resource_suggestion"],
                answer="第三階段可以用限時模考搭配錯題分類。",
                referenced_plan=None,
                suggested_follow_up_actions=[],
            )
        )
    )

    assert result.response_type == "chat_answer"
    assert result.reply_text == "第三階段可以用限時模考搭配錯題分類。"
