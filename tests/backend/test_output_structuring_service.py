from app.schemas import (
    PlanningCreateOutput,
    PlanningMainTask,
    PlanningSchedule,
    PlanningSubtask,
)
from app.services.modules.output_structuring.service import (
    build_structured_task_output,
)


def test_build_structured_task_output_sorts_main_tasks_and_subtasks() -> None:
    planning_output = PlanningCreateOutput(
        plan_summary="先確認需求，再完成核心功能與測試。",
        design_rationale="目前期限與任務目標已明確，因此可直接建立初步規劃。",
        assumptions_used=[],
        schedule=PlanningSchedule(
            main_tasks=[
                PlanningMainTask(
                    title="核心功能實作",
                    description="完成主要功能。",
                    estimated_time="4-6h",
                    order=2,
                    subtasks=[
                        PlanningSubtask(
                            title="整合測試",
                            description="確認主要流程可運作。",
                            priority="medium",
                            estimated_time="1h",
                            order=2,
                        ),
                        PlanningSubtask(
                            title="完成主要功能程式碼",
                            description="依題目要求完成核心實作。",
                            priority="high",
                            estimated_time="3-4h",
                            order=1,
                        ),
                    ],
                ),
                PlanningMainTask(
                    title="確認作業需求",
                    description="整理作業要求。",
                    estimated_time="1h",
                    order=1,
                    subtasks=[],
                ),
            ]
        ),
    )

    result = build_structured_task_output(planning_output)

    assert result.plan_summary == "先確認需求，再完成核心功能與測試。"
    assert result.main_tasks[0].title == "確認作業需求"
    assert result.main_tasks[1].title == "核心功能實作"
    assert result.main_tasks[1].subtasks[0].title == "完成主要功能程式碼"
    assert result.main_tasks[1].subtasks[1].title == "整合測試"
