from dataclasses import dataclass, field


CONVERSATION_HISTORY_START_STAGE = "F015"
CONVERSATION_HISTORY_ALLOWED_END_STAGES = {"F018"}


@dataclass
class ConversationHistoryFlowContext:
    """`conversation_history` 主流程在控制層內部使用的最小執行上下文。"""

    conversation_id: str
    current_stage: str = CONVERSATION_HISTORY_START_STAGE
    traversed_history: list[str] = field(
        default_factory=lambda: [CONVERSATION_HISTORY_START_STAGE]
    )


class ConversationHistoryController:
    """承接 `conversation_history` 這條窗口流程的控制器骨架。"""

    def handle_conversation_history(self, conversation_id: str) -> dict[str, object]:
        context = ConversationHistoryFlowContext(conversation_id=conversation_id)
        final_response = self._run_flow(context)
        self._ensure_valid_end_stage(context.current_stage)
        return final_response

    def _run_flow(self, context: ConversationHistoryFlowContext) -> dict[str, object]:
        stage_handlers = {
            "F015": self._run_stage_f015,
            "F016": self._run_stage_f016,
            "F017": self._run_stage_f017,
            "F018": self._run_stage_f018,
        }

        while True:
            handler = stage_handlers.get(context.current_stage)
            if handler is None:
                raise ValueError(
                    f"Unsupported conversation_history stage: {context.current_stage}"
                )

            result = handler(context)
            if isinstance(result, dict):
                return result

    def _run_stage_f015(self, context: ConversationHistoryFlowContext) -> None:
        self._transition(context, next_stage="F016")

    def _run_stage_f016(self, context: ConversationHistoryFlowContext) -> None:
        self._transition(context, next_stage="F017")

    def _run_stage_f017(self, context: ConversationHistoryFlowContext) -> None:
        self._transition(context, next_stage="F018")

    def _run_stage_f018(
        self,
        context: ConversationHistoryFlowContext,
    ) -> dict[str, object]:
        return {
            "conversation_id": context.conversation_id,
        }

    def _transition(
        self,
        context: ConversationHistoryFlowContext,
        next_stage: str,
    ) -> None:
        context.current_stage = next_stage
        context.traversed_history.append(next_stage)

    def _ensure_valid_end_stage(self, stage: str) -> None:
        """確保流程是停在 conversation_history 這條路線允許的合法終點。"""

        if stage not in CONVERSATION_HISTORY_ALLOWED_END_STAGES:
            raise ValueError(
                f"conversation_history flow ended at invalid stage: {stage}"
            )
