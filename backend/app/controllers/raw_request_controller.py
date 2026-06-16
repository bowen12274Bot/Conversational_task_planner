from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.schemas import (
    ContextEngineeringOutput,
    ControllerToFrontendResponse,
    ConversationRecordStoreRequest,
    FrontendToControllerRequest,
    PlanningCreateInput,
    PlanningCreateOutput,
    PlanningMainTask,
    PlanningRevisionInput,
    PlanningRevisionOutput,
    PlanningRevisionResponseInput,
    PlanningResponseInput,
    QuestioningDecision,
    ResponseOutput,
)
from app.services.modules.context_engineering import build_context_from_raw_input
from app.services.modules.planning import build_initial_planning, build_revised_planning
from app.services.modules.questioning import evaluate_questioning_need
from app.services.modules.output_structuring.service import (
    build_structured_task_output,
)
from app.services.persistence import (
    get_follow_up_round_count,
    get_structured_task_output,
    increment_follow_up_round_count,
    reset_follow_up_round_count,
    save_structured_task_output,
    store_conversation_record,
)
from app.services.modules.response import (
    build_response_from_planning,
    build_response_from_planning_revision,
    build_response_from_questioning,
)


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
    planning_revision_input: PlanningRevisionInput | None = None
    planning_output: PlanningCreateOutput | None = None
    planning_revision_output: PlanningRevisionOutput | None = None
    existing_structured_task_output: dict[str, Any] | None = None
    structured_task_output: dict[str, Any] | None = None
    planning_mode: str = "create"
    reply_created_at: datetime | None = None
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
        context.existing_structured_task_output = get_structured_task_output(
            context.conversation_id
        )
        existing_plan_outline = self._build_existing_plan_outline(
            context.existing_structured_task_output
        )
        context.context_output = build_context_from_raw_input(
            user_input=context.request.user_input,
            conversation_id=context.conversation_id,
            existing_plan_outline=existing_plan_outline,
        )
        self._transition(context, next_stage="F004")

    def _run_stage_f004(self, context: RawRequestFlowContext) -> None:
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")

        follow_up_round_count = get_follow_up_round_count(context.conversation_id)
        existing_plan_outline = self._build_existing_plan_outline(
            context.existing_structured_task_output
        )
        context.questioning_decision = evaluate_questioning_need(
            context_output=context.context_output,
            follow_up_round_count=follow_up_round_count,
            has_existing_plan=context.existing_structured_task_output is not None,
            existing_plan_outline=existing_plan_outline,
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
        store_result = store_conversation_record(
            ConversationRecordStoreRequest(
                conversation_id=context.conversation_id,
                turn_id=context.turn_id,
                type="ai",
                content=context.response_output.reply_text,
            )
        )
        context.reply_created_at = self._normalize_utc_timestamp(
            store_result.message_created_at
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
            reply_created_at=context.reply_created_at,
            conversation_id=context.conversation_id,
            structured_task_output=None,
        )

    def _run_stage_f008(self, context: RawRequestFlowContext) -> None:
        reset_follow_up_round_count(context.conversation_id)
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")

        if self._should_run_revision(context):
            context.planning_mode = "revise"
            context.planning_revision_input = self._build_planning_revision_input(
                context
            )
        else:
            self._ensure_create_planning_is_safe(context)
            context.planning_mode = "create"
            context.planning_input = PlanningCreateInput(
                requirement_context=context.context_output.requirement_context,
                known_information=context.context_output.known_information,
                pending_confirmation=context.context_output.pending_confirmation,
                conversation_history_text=context.context_output.conversation_history_text,
            )
        self._transition(context, next_stage="F009")

    def _run_stage_f009(self, context: RawRequestFlowContext) -> None:
        if context.planning_mode == "revise":
            if context.planning_revision_input is None:
                raise ValueError("planning_revision_input 尚未建立。")
            context.planning_revision_output = build_revised_planning(
                context.planning_revision_input
            )
            context.planning_output = self._merge_revision_into_planning_output(
                context
            )
            self._transition(context, next_stage="F010")
            return

        if context.planning_input is None:
            raise ValueError("planning_input 尚未建立。")

        context.planning_output = build_initial_planning(context.planning_input)
        self._transition(context, next_stage="F010")

    def _run_stage_f010(self, context: RawRequestFlowContext) -> None:
        if context.planning_output is None:
            raise ValueError("planning_output 尚未建立。")

        self._transition(context, next_stage="F011")

    def _run_stage_f011(self, context: RawRequestFlowContext) -> None:
        if context.planning_output is None:
            raise ValueError("planning_output 尚未建立。")
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")

        structured_task_output = build_structured_task_output(
            context.planning_output,
            known_information=context.context_output.known_information,
            current_datetime=datetime.now(timezone.utc),
        )
        context.structured_task_output = structured_task_output.model_dump()
        save_structured_task_output(
            context.conversation_id, context.structured_task_output
        )
        if context.planning_mode == "revise":
            if context.planning_revision_output is None:
                raise ValueError("planning_revision_output 尚未建立。")
            context.response_output = build_response_from_planning_revision(
                PlanningRevisionResponseInput(
                    revision_summary=context.planning_revision_output.revision_summary,
                    design_rationale=context.planning_revision_output.design_rationale,
                    target_main_task_title=context.planning_revision_output.updated_main_task.title,
                    structured_task_output=structured_task_output,
                )
            )
        else:
            context.response_output = build_response_from_planning(
                PlanningResponseInput(
                    plan_summary=context.planning_output.plan_summary,
                    design_rationale=context.planning_output.design_rationale,
                    structured_task_output=structured_task_output,
                )
            )
        store_result = store_conversation_record(
            ConversationRecordStoreRequest(
                conversation_id=context.conversation_id,
                turn_id=context.turn_id,
                type="ai",
                content=context.response_output.reply_text,
            )
        )
        context.reply_created_at = self._normalize_utc_timestamp(
            store_result.message_created_at
        )
        self._transition(context, next_stage="F012")

    def _run_stage_f012(
        self,
        context: RawRequestFlowContext,
    ) -> ControllerToFrontendResponse:
        if context.response_output is None:
            raise ValueError("response_output 尚未建立。")

        return ControllerToFrontendResponse(
            reply_text=context.response_output.reply_text,
            reply_created_at=context.reply_created_at,
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

    def _normalize_utc_timestamp(self, value: datetime) -> datetime:
        """將回覆訊息時間標準化為帶時區資訊的 UTC。"""

        if value.tzinfo is not None:
            return value.astimezone(timezone.utc)

        return value.replace(tzinfo=timezone.utc)

    def _should_run_revision(self, context: RawRequestFlowContext) -> bool:
        if context.existing_structured_task_output is None:
            return False
        if context.context_output is None or context.context_output.planning_intent is None:
            return False

        planning_intent = context.context_output.planning_intent
        if planning_intent.intent_type != "revise":
            return False
        if planning_intent.target_main_task_order is None:
            raise ValueError("revision planning 缺少 target_main_task_order。")

        self._get_target_main_task(
            context.existing_structured_task_output,
            planning_intent.target_main_task_order,
        )
        return True

    def _ensure_create_planning_is_safe(self, context: RawRequestFlowContext) -> None:
        if context.existing_structured_task_output is None:
            return
        if context.context_output is None or context.context_output.planning_intent is None:
            raise ValueError("已有既有排程，但缺少 planning_intent，不能安全重新規劃。")

        planning_intent = context.context_output.planning_intent
        if planning_intent.intent_type == "create" and planning_intent.confidence != "low":
            return

        raise ValueError("已有既有排程，但本輪意圖不足以安全建立新規劃。")

    def _build_planning_revision_input(
        self,
        context: RawRequestFlowContext,
    ) -> PlanningRevisionInput:
        if context.context_output is None:
            raise ValueError("context_output 尚未建立。")
        if context.existing_structured_task_output is None:
            raise ValueError("existing_structured_task_output 尚未建立。")
        if context.context_output.planning_intent is None:
            raise ValueError("planning_intent 尚未建立。")

        target_order = context.context_output.planning_intent.target_main_task_order
        if target_order is None:
            raise ValueError("revision planning 缺少 target_main_task_order。")

        return PlanningRevisionInput(
            requirement_context=context.context_output.requirement_context,
            known_information=context.context_output.known_information,
            pending_confirmation=context.context_output.pending_confirmation,
            conversation_history_text=context.context_output.conversation_history_text,
            existing_plan_outline=self._build_existing_plan_outline(
                context.existing_structured_task_output
            ),
            target_main_task=self._get_target_main_task(
                context.existing_structured_task_output,
                target_order,
            ),
            target_main_task_order=target_order,
            revision_request=context.request.user_input,
        )

    def _merge_revision_into_planning_output(
        self,
        context: RawRequestFlowContext,
    ) -> PlanningCreateOutput:
        if context.existing_structured_task_output is None:
            raise ValueError("existing_structured_task_output 尚未建立。")
        if context.planning_revision_output is None:
            raise ValueError("planning_revision_output 尚未建立。")

        main_tasks = self._extract_planning_main_tasks(
            context.existing_structured_task_output
        )
        target_order = context.planning_revision_output.target_main_task_order
        merged_tasks: list[PlanningMainTask] = []
        replaced = False
        for main_task in main_tasks:
            if main_task.order == target_order:
                merged_tasks.append(context.planning_revision_output.updated_main_task)
                replaced = True
                continue
            merged_tasks.append(main_task)

        if not replaced:
            raise ValueError("找不到可替換的 revision target main task。")

        return PlanningCreateOutput(
            plan_summary=context.planning_revision_output.revision_summary,
            design_rationale=context.planning_revision_output.design_rationale,
            assumptions_used=context.planning_revision_output.assumptions_used,
            schedule={"main_tasks": merged_tasks},
        )

    def _build_existing_plan_outline(
        self,
        structured_task_output: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if structured_task_output is None:
            return []

        outline: list[dict[str, Any]] = []
        for main_task in structured_task_output.get("main_tasks", []):
            if not isinstance(main_task, dict):
                continue
            order = main_task.get("order")
            title = main_task.get("title")
            if not isinstance(order, int) or not isinstance(title, str):
                continue
            outline.append(
                {
                    "order": order,
                    "title": title,
                    "description": main_task.get("description"),
                }
            )

        return outline

    def _get_target_main_task(
        self,
        structured_task_output: dict[str, Any],
        target_order: int,
    ) -> PlanningMainTask:
        for main_task in self._extract_planning_main_tasks(structured_task_output):
            if main_task.order == target_order:
                return main_task

        raise ValueError(f"找不到 target_main_task_order={target_order} 的既有主任務。")

    def _extract_planning_main_tasks(
        self,
        structured_task_output: dict[str, Any],
    ) -> list[PlanningMainTask]:
        main_tasks = structured_task_output.get("main_tasks")
        if not isinstance(main_tasks, list):
            raise ValueError("existing structured_task_output 缺少 main_tasks。")

        return [PlanningMainTask.model_validate(main_task) for main_task in main_tasks]
