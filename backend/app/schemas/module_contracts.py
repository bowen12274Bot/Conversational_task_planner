from typing import Any, Literal

from pydantic import BaseModel, Field


class RequirementInput(BaseModel):
    """使用者提交的原始自然語言需求，作為整個流程的起點。"""

    # 保留使用者最原始的需求表達。
    user_input: str = Field(..., min_length=1)


class PlanningIntent(BaseModel):
    """由 Context Engineering 整理出的規劃意圖線索。"""

    intent_type: Literal["create", "revise", "chat", "other"]
    target_main_task_order: int | None = Field(default=None, ge=1)
    confidence: Literal["high", "medium", "low"]


class ContextEngineeringOutput(BaseModel):
    """由 `Context Engineering Module` 根據原始需求與歷史脈絡整理出的可用資訊基礎。"""

    # 由原始需求整理出的需求脈絡。
    requirement_context: str = Field(..., min_length=1)
    # 目前已知、可直接使用的資訊集合。
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    # 仍待確認、暫不直接採用的資訊集合。
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    # 與目前需求相關的完整歷史對話內容。
    conversation_history_text: str | None = None
    # 本輪輸入中可觀察到的規劃意圖線索；僅供後續模組判斷，不代表流程決策。
    planning_intent: PlanningIntent | None = None


class QuestioningDecision(BaseModel):
    """由 `Questioning Module` 根據 `Context Engineering` 整理結果所產出的判斷資料。"""

    # 本輪下一步應採取的方向。
    decision: Literal["follow_up", "planning"]
    # 對此判斷的原因說明。
    reasoning: str = Field(..., min_length=1)
    # 延用目前已知資訊集合。
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    # 延用目前待確認資訊集合。
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    # 下一步建議內容，依 decision 語意解讀。
    next_step_guidance: list[str] = Field(default_factory=list)


class PlanningSubtask(BaseModel):
    """排程核心結構中的子任務資料。"""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    priority: Literal["high", "medium", "low"]
    estimated_time: str = Field(..., min_length=1)
    order: int = Field(..., ge=1)


class PlanningMainTask(BaseModel):
    """排程核心結構中的主任務資料。"""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    estimated_time: str = Field(..., min_length=1)
    order: int = Field(..., ge=1)
    subtasks: list[PlanningSubtask] = Field(default_factory=list)


class PlanningSchedule(BaseModel):
    """Planning Module 排程結果的核心結構。"""

    main_tasks: list[PlanningMainTask] = Field(default_factory=list)


class PlanningCreateInput(BaseModel):
    """提供 `Planning Module` 建立初步規劃時使用的輸入資料。"""

    requirement_context: str = Field(..., min_length=1)
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history_text: str | None = None


class PlanningCreateOutput(BaseModel):
    """由 `Planning Module` 建立介面產出的初步規劃結果。"""

    plan_summary: str = Field(..., min_length=1)
    design_rationale: str = Field(..., min_length=1)
    assumptions_used: list[str] = Field(default_factory=list)
    schedule: PlanningSchedule


class PlanningRevisionInput(BaseModel):
    """提供 `Planning Module` 修改既有規劃時使用的輸入資料。"""

    requirement_context: str = Field(..., min_length=1)
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history_text: str | None = None
    existing_plan_outline: list[dict[str, Any]] = Field(default_factory=list)
    target_main_task: PlanningMainTask
    target_main_task_order: int = Field(..., ge=1)
    revision_request: str = Field(..., min_length=1)


class PlanningRevisionOutput(BaseModel):
    """由 `Planning Module` 修改介面產出的局部規劃修改結果。"""

    revision_summary: str = Field(..., min_length=1)
    design_rationale: str = Field(..., min_length=1)
    assumptions_used: list[str] = Field(default_factory=list)
    target_main_task_order: int = Field(..., ge=1)
    updated_main_task: PlanningMainTask


class ChatReferencedPlan(BaseModel):
    """Chat Module 回答中引用的既有規劃位置。"""

    main_task_order: int | None = Field(default=None, ge=1)
    subtask_orders: list[str] = Field(default_factory=list)


class ChatSuggestedFollowUpAction(BaseModel):
    """Chat Module 回答後可提供的後續操作提示。"""

    action_type: Literal["revise_plan", "ask_more"]
    label: str = Field(..., min_length=1)


class ChatModuleInput(BaseModel):
    """提供 `Chat Module` 回答規劃相關問題時使用的輸入資料。"""

    raw_requirement: str = Field(..., min_length=1)
    requirement_context: str = Field(..., min_length=1)
    planning_intent: PlanningIntent
    known_information: list[dict[str, Any]] = Field(default_factory=list)
    pending_confirmation: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history_text: str | None = None
    existing_plan_outline: list[dict[str, Any]] = Field(default_factory=list)
    structured_task_output: dict[str, Any] | None = None


class ChatModuleOutput(BaseModel):
    """由 `Chat Module` 產出的規劃相關問答結果。"""

    answer_types: list[
        Literal[
            "plan_explanation",
            "execution_advice",
            "resource_suggestion",
            "risk_analysis",
            "general_answer",
        ]
    ] = Field(..., min_length=1, max_length=3)
    answer: str = Field(..., min_length=1)
    referenced_plan: ChatReferencedPlan | None = None
    suggested_follow_up_actions: list[ChatSuggestedFollowUpAction] = Field(
        default_factory=list
    )


class ChatResponseInput(BaseModel):
    """提供 `Response Module` 包裝 Chat Module 回答時使用的輸入資料。"""

    chat_output: ChatModuleOutput


class StructuredSubtaskOutput(BaseModel):
    """供前端規劃面板顯示的子任務資料。"""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    priority: Literal["high", "medium", "low"]
    estimated_time: str = Field(..., min_length=1)
    order: int = Field(..., ge=1)


class StructuredMainTaskOutput(BaseModel):
    """供前端規劃面板顯示的主任務資料。"""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    estimated_time: str = Field(..., min_length=1)
    order: int = Field(..., ge=1)
    subtasks: list[StructuredSubtaskOutput] = Field(default_factory=list)


class StructuredSummaryMetricsOutput(BaseModel):
    """供前端規劃面板 footer 顯示的摘要指標資料。"""

    total_estimated_time_text: str = Field(..., min_length=1)
    daily_time_budget_text: str = Field(..., min_length=1)
    estimated_completion_text: str = Field(..., min_length=1)


class StructuredTaskOutput(BaseModel):
    """由 Output Structuring Module 產出的前端排程顯示資料。"""

    plan_summary: str = Field(..., min_length=1)
    summary_metrics: StructuredSummaryMetricsOutput
    main_tasks: list[StructuredMainTaskOutput] = Field(default_factory=list)


class PlanningResponseInput(BaseModel):
    """提供 `Response Module` 在 planning 路徑生成最終回覆時使用的輸入資料。"""

    plan_summary: str = Field(..., min_length=1)
    design_rationale: str = Field(..., min_length=1)
    structured_task_output: StructuredTaskOutput


class PlanningRevisionResponseInput(BaseModel):
    """提供 `Response Module` 在 planning revision 路徑生成最終回覆時使用的輸入資料。"""

    revision_summary: str = Field(..., min_length=1)
    design_rationale: str = Field(..., min_length=1)
    target_main_task_title: str = Field(..., min_length=1)
    structured_task_output: StructuredTaskOutput


class ResponseOutput(BaseModel):
    """由 `Response Module` 根據 `Questioning 判斷結果` 所生成的、適合提供前端顯示的最終回覆內容。"""

    # 適合直接顯示給使用者的回覆文字。
    reply_text: str = Field(..., min_length=1)
    # 回覆在互動流程中的類型。
    response_type: Literal[
        "follow_up_question",
        "planning_summary",
        "planning_revision_summary",
        "chat_answer",
    ]
