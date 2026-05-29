from dataclasses import dataclass, field

from app.schemas import (
    ContextEngineeringOutput,
    ControllerToFrontendResponse,
    ConversationRecordStoreRequest,
    FrontendToControllerRequest,
    QuestioningDecision,
    ResponseOutput,
)
from app.services.modules.context_engineering import build_context_from_raw_input
from app.services.modules.questioning import evaluate_questioning_need
from app.services.persistence import store_conversation_record
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
            "F008": self._run_stage_f008_to_f012,
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

        context.questioning_decision = evaluate_questioning_need(
            context_output=context.context_output,
        )
        self._transition(context, next_stage="F005")

    def _run_stage_f005(self, context: RawRequestFlowContext) -> None:
        if context.questioning_decision is None:
            raise ValueError("questioning_decision 尚未建立。")

        if context.questioning_decision.is_ready_for_planning:
            self._transition(context, next_stage="F008")
            return

        self._transition(context, next_stage="F006")

    def _run_stage_f006(self, context: RawRequestFlowContext) -> None:
        if context.questioning_decision is None:
            raise ValueError("questioning_decision 尚未建立。")

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

    def _run_stage_f008_to_f012(
        self,
        context: RawRequestFlowContext,
    ) -> ControllerToFrontendResponse:
        # 因規劃分支尚未細化設計，F008-F012 目前先以簡略骨架表示。
        for stage in ("F009", "F010", "F011", "F012"):
            context.traversed_history.append(stage)
        context.current_stage = "F012"
        return ControllerToFrontendResponse(
            reply_text=(
                "目前 raw_request 規劃分支流程骨架已預留，"
                "但尚未接入實際規劃與輸出模組。"
            ),
            conversation_id=context.conversation_id,
            structured_task_output=None,
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
