from app.schemas.architecture_contracts import (
    ModuleToAIRequest,
    ControllerToFrontendResponse,
    FrontendToControllerRequest,
)
from app.schemas.module_contracts import (
    QuestioningDecision,
    ResponseOutput,
)


def test_frontend_request_contract_accepts_minimal_payload() -> None:
    payload = FrontendToControllerRequest(user_input="我想完成下週的資料庫作業")

    assert payload.user_input == "我想完成下週的資料庫作業"
    assert payload.interaction_info == {}


def test_questioning_decision_contract_represents_not_ready_state() -> None:
    decision = QuestioningDecision(
        is_ready_for_planning=False,
        reasoning="目前缺少截止時間與每日可投入時間。",
    )

    assert decision.is_ready_for_planning is False
    assert decision.pending_confirmation == []


def test_controller_response_contract_keeps_minimal_output_shape() -> None:
    response = ControllerToFrontendResponse(
        reply_text="我需要先確認你的截止時間，才能進一步規劃。",
        structured_task_output=None,
    )

    assert response.structured_task_output is None
    assert response.reply_text == "我需要先確認你的截止時間，才能進一步規劃。"


def test_response_output_contract_keeps_only_documented_fields() -> None:
    response = ResponseOutput(
        reply_text="請先補充截止時間。",
        response_type="questioning_guidance",
        includes_follow_up_questions=True,
        includes_next_action=True,
    )

    assert response.includes_follow_up_questions is True
    assert response.includes_next_action is True


def test_ai_task_request_contract_supports_grouped_ai_requests() -> None:
    request = ModuleToAIRequest(
        task_type="structured_output",
        group_name="questioning_decision",
        input_data={"user_input": "我想做一個期中報告規劃"},
        output_target="產出 Questioning 判斷結果",
    )

    assert request.group_name == "questioning_decision"
