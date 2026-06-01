from dataclasses import dataclass, field
from typing import Any

from app.schemas import (
    ContextEngineeringOutput,
    ControllerToFrontendResponse,
    ConversationRecordStoreRequest,
    FrontendToControllerRequest,
    PlanningCreateInput,
    PlanningCreateOutput,
    QuestioningDecision,
    ResponseOutput,
)
from app.services.modules.context_engineering import build_context_from_raw_input
from app.services.modules.planning import build_initial_planning
from app.services.modules.questioning import evaluate_questioning_need
from app.services.persistence import (
    get_follow_up_round_count,
    increment_follow_up_round_count,
    reset_follow_up_round_count,
    store_conversation_record,
)
from app.services.modules.response import build_response_from_questioning


RAW_REQUEST_START_STAGE = "F001"
RAW_REQUEST_ALLOWED_END_STAGES = {"F007", "F012"}


@dataclass
class RawRequestFlowContext:
    """`raw_request` 主流程在控制層內部使用的最小執行上下文。"""

    request: FrontendToControllerRequest
    conversation_id: str
    turn_id: str | None = None
    context_output: ContextEngineeringOutput | None = None
    questioning_decision: QuestioningDecision | None = None
    response_output: ResponseOutput | None = None
    planning_input: PlanningCreateInput | None = None
    planning_output: PlanningCreateOutput | None = None
    structured_task_output: dict[str, Any] | None = None
    current_stage: str = RAW_REQUEST_START_STAGE
    traversed_history: list[str] = field(
        default_factory=lambda: [RAW_REQUEST_START_STAGE]
    )


class RawRequestController:
    """承接 `raw_request` 這條窗口流程的控制器骨架。"""

    def handle_raw_request(
        self,
        payload: FrontendToControllerRequest,
    ) -> ControllerToFrontendResponse:
        conversation_id = payload.conversation_id
        if conversation_id is None:
            raise ValueError("raw_request 流程缺少 conversation_id。")

        context = RawRequestFlowContext(
            request=payload,
            conversation_id=conversation_id,
        )
        final_response = self._run_flow(context)
        self._ensure_valid_end_stage(context.current_stage)
        return final_response

    def _run_flow(self, context: RawRequestFlowContext) -> ControllerToFrontendResponse:
        stage_handlers = {
            "F001": self._run_stage_f001,
            "F002": self._run_stage_f002,
            "F003": self._run_stage_f003,
            "F004": self._run_stage_f004,
            "F005": self._run_stage_f005,
            "F006": self._run_stage_f006,
            "F007": self._run_stage_f007,
            "F008": self._run_stage_f008,
            "F009": self._run_stage_f009,
            "F010": self._run_stage_f010,
            "F011": self._run_stage_f011,
            "F012": self._run_stage_f012,
        }

        while True:
            handler = stage_handlers.get(context.current_stage)
            if handler is None:
                raise ValueError(f"Unsupported raw_request stage: {context.current_stage}")

            result = handler(context)
            if isinstance(result, ControllerToFrontendResponse):
                return result

    def _run_stage_f001(self, context: RawRequestFlowContext) -> None:
        self._transition(context, next_stage="F002")

    def _run_stage_f002(self, context: RawRequestFlowContext) -> None:
        store_result = store_conversation_record(
            ConversationRecordStoreRequest(
                conversation_id=context.conversation_id,
                turn_id=None,
                type="user",
                content=context.request.user_input,
            )
        )
        context.turn_id = store_result.turn_id
        self._transition(context, next_stage="F003")

    def _run_stage_f003(self, context: RawRequestFlowContext) -> None:
        context.context_output = build_context_from_raw_input(
            user_input=context.request.user_input,
            conversation_id=context.conversation_id,
        )
        self._transition(context, next_stage="F004")

    def _run_stage_f004(self, context: RawRequestFlowContext) -> None:
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")

        follow_up_round_count = get_follow_up_round_count(context.conversation_id)
        context.questioning_decision = evaluate_questioning_need(
            context_output=context.context_output,
            follow_up_round_count=follow_up_round_count,
        )
        self._transition(context, next_stage="F005")

    def _run_stage_f005(self, context: RawRequestFlowContext) -> None:
        if context.questioning_decision is None:
            raise ValueError("questioning_decision 尚未建立。")

        if context.questioning_decision.decision == "planning":
            self._transition(context, next_stage="F008")
            return

        self._transition(context, next_stage="F006")

    def _run_stage_f006(self, context: RawRequestFlowContext) -> None:
        if context.questioning_decision is None:
            raise ValueError("questioning_decision 尚未建立。")

        increment_follow_up_round_count(context.conversation_id)
        context.response_output = build_response_from_questioning(
            questioning_decision=context.questioning_decision,
        )
        store_conversation_record(
            ConversationRecordStoreRequest(
                conversation_id=context.conversation_id,
                turn_id=context.turn_id,
                type="ai",
                content=context.response_output.reply_text,
            )
        )
        self._transition(context, next_stage="F007")

    def _run_stage_f007(
        self,
        context: RawRequestFlowContext,
    ) -> ControllerToFrontendResponse:
        if context.response_output is None:
            raise ValueError("response_output 尚未建立。")

        return ControllerToFrontendResponse(
            reply_text=context.response_output.reply_text,
            conversation_id=context.conversation_id,
            structured_task_output=None,
        )

    def _run_stage_f008(self, context: RawRequestFlowContext) -> None:
        reset_follow_up_round_count(context.conversation_id)
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")

        context.planning_input = PlanningCreateInput(
            requirement_context=context.context_output.requirement_context,
            known_information=context.context_output.known_information,
            pending_confirmation=context.context_output.pending_confirmation,
            conversation_history_text=context.context_output.conversation_history_text,
        )
        self._transition(context, next_stage="F009")

    def _run_stage_f009(self, context: RawRequestFlowContext) -> None:
        if context.planning_input is None:
            raise ValueError("planning_input 尚未建立。")

        context.planning_output = build_initial_planning(context.planning_input)
        self._transition(context, next_stage="F010")

    def _run_stage_f010(self, context: RawRequestFlowContext) -> None:
        if context.planning_output is None:
            raise ValueError("planning_output 尚未建立。")

        # Output Structuring Module 尚未正式實作，現階段先承接 planning output，
        # 後續再由獨立模組負責最終整理。
        context.structured_task_output = context.planning_output.schedule.model_dump()
        self._transition(context, next_stage="F011")

    def _run_stage_f011(self, context: RawRequestFlowContext) -> None:
        if context.structured_task_output is None:
            raise ValueError("structured_task_output 尚未建立。")

        # Output Structuring Module 尚未正式接入，F011 目前先保留為最小占位節點。
        self._transition(context, next_stage="F012")

    def _run_stage_f012(
        self,
        context: RawRequestFlowContext,
    ) -> ControllerToFrontendResponse:
        if context.planning_output is None:
            raise ValueError("planning_output 尚未建立。")

        return ControllerToFrontendResponse(
            reply_text=context.planning_output.plan_summary,
            conversation_id=context.conversation_id,
            structured_task_output=context.structured_task_output,
        )

    def _transition(
        self,
        context: RawRequestFlowContext,
        next_stage: str,
    ) -> None:
        context.current_stage = next_stage
        context.traversed_history.append(next_stage)

    def _ensure_valid_end_stage(self, stage: str) -> None:
        """確保流程是停在 raw_request 這條路線允許的合法終點。"""

        if stage not in RAW_REQUEST_ALLOWED_END_STAGES:
            raise ValueError(f"raw_request flow ended at invalid stage: {stage}")
