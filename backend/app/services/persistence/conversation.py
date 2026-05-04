from app.schemas import (
    ConversationHistoryRequest,
    ConversationHistoryResponse,
    ConversationRecordStoreRequest,
    ConversationRecordStoreResult,
    CreateConversationResponse,
)


class PersistenceService:
    """持久化層三個窗口的最小骨架。"""

    def create_conversation(self) -> CreateConversationResponse:
        """建立新對話窗口，後續再接上實際 DB 建立流程。"""

        return CreateConversationResponse(
            conversation_id="conversation_id_placeholder"
        )

    def store_conversation_record(
        self, request: ConversationRecordStoreRequest
    ) -> ConversationRecordStoreResult:
        """對話紀錄存入窗口，依 user/ai 規則回傳對應 turn。"""

        if request.type == "ai" and not request.turn_id:
            raise ValueError(
                "AI 訊息存入持久化層時必須提供既有 turn_id。"
            )

        if request.type == "user":
            turn_id = request.turn_id or "turn_id_placeholder"
        else:
            turn_id = request.turn_id or ""

        return ConversationRecordStoreResult(
            conversation_id=request.conversation_id,
            turn_id=turn_id,
        )

    def get_conversation_history(
        self, request: ConversationHistoryRequest
    ) -> ConversationHistoryResponse:
        """歷史查詢窗口，後續再接上實際 DB 查詢流程。"""

        return ConversationHistoryResponse(
            conversation_id=request.conversation_id,
            turns=[],
        )
