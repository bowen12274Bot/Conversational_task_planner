from app.schemas import AIToModuleResult, PlanningCreateInput
from app.services.modules.planning import service as planning_service


def test_build_initial_planning_can_extract_last_json_object_after_analysis_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        planning_service,
        "run_ai_flow",
        lambda request: AIToModuleResult(
            success=True,
            output_result={
                "text": (
                    "* analysis before final answer\n"
                    "{\n"
                    '  "plan_summary": "先確認需求，再安排實作與測試。",\n'
                    '  "design_rationale": "期限明確且尚未開始，因此先安排需求理解與核心實作。",\n'
                    '  "assumptions_used": ["每日可投入時間尚未明確，因此先依一般有限時段投入安排。"],\n'
                    '  "schedule": {\n'
                    '    "main_tasks": [\n'
                    '      {\n'
                    '        "title": "確認作業需求",\n'
                    '        "description": "整理作業要求與交付內容。",\n'
                    '        "estimated_time": "1-2h",\n'
                    '        "order": 1,\n'
                    '        "subtasks": [\n'
                    '          {\n'
                    '            "title": "閱讀題目說明",\n'
                    '            "description": "確認題目要求與限制。",\n'
                    '            "priority": "high",\n'
                    '            "estimated_time": "30m",\n'
                    '            "order": 1\n'
                    '          }\n'
                    "        ]\n"
                    "      }\n"
                    "    ]\n"
                    "  }\n"
                    "}"
                ),
                "provider": "mock",
                "model_name": "mock-model",
            },
        ),
    )

    result = planning_service.build_initial_planning(
        PlanningCreateInput(
            requirement_context="使用者希望在 7 天內完成 Java 作業，目前尚未開始。",
            known_information=[
                {"label": "task_type", "value": "Java 作業"},
                {"label": "deadline_hint", "value": "7 天內"},
            ],
            pending_confirmation=[],
            conversation_history_text=None,
        )
    )

    assert result.plan_summary == "先確認需求，再安排實作與測試。"
    assert result.schedule.main_tasks[0].title == "確認作業需求"
    assert result.schedule.main_tasks[0].subtasks[0].priority == "high"
