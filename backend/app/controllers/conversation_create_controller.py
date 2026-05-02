from dataclasses import dataclass, field


CONVERSATION_CREATE_START_STAGE = "F013"
CONVERSATION_CREATE_ALLOWED_END_STAGES = {"F014"}


@dataclass
class ConversationCreateFlowContext:
    """`conversation_create` 主流程在控制層內部使用的最小執行上下文。"""

    current_stage: str = CONVERSATION_CREATE_START_STAGE
    traversed_history: list[str] = field(
        default_factory=lambda: [CONVERSATION_CREATE_START_STAGE]
    )


class ConversationCreateController:
    """承接 `conversation_create` 這條窗口流程的控制器骨架。"""

    def handle_create_conversation(self) -> dict[str, str]:
        context = ConversationCreateFlowContext()
        final_response = self._run_flow(context)
        self._ensure_valid_end_stage(context.current_stage)
        return final_response

    def _run_flow(self, context: ConversationCreateFlowContext) -> dict[str, str]:
        stage_handlers = {
            "F013": self._run_stage_f013,
            "F014": self._run_stage_f014,
        }

        while True:
            handler = stage_handlers.get(context.current_stage)
            if handler is None:
                raise ValueError(
                    f"Unsupported conversation_create stage: {context.current_stage}"
                )

            result = handler(context)
            if isinstance(result, dict):
                return result

    def _run_stage_f013(self, context: ConversationCreateFlowContext) -> None:
        self._transition(context, next_stage="F014")

    def _run_stage_f014(
        self,
        context: ConversationCreateFlowContext,
    ) -> dict[str, str]:
        return {
            "conversation_id": "conversation_id_placeholder",
        }

    def _transition(
        self,
        context: ConversationCreateFlowContext,
        next_stage: str,
    ) -> None:
        context.current_stage = next_stage
        context.traversed_history.append(next_stage)

    def _ensure_valid_end_stage(self, stage: str) -> None:
        """確保流程是停在 conversation_create 這條路線允許的合法終點。"""

        if stage not in CONVERSATION_CREATE_ALLOWED_END_STAGES:
            raise ValueError(
                f"conversation_create flow ended at invalid stage: {stage}"
            )
