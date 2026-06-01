from app.schemas.module_contracts import (
    PlanningCreateOutput,
    StructuredMainTaskOutput,
    StructuredSubtaskOutput,
    StructuredTaskOutput,
)


def build_structured_task_output(
    planning_output: PlanningCreateOutput,
) -> StructuredTaskOutput:
    """將 Planning Module 結果整理為前端可穩定渲染的排程顯示資料。"""

    sorted_main_tasks = sorted(
        planning_output.schedule.main_tasks,
        key=lambda task: task.order,
    )

    structured_main_tasks = []
    for main_task in sorted_main_tasks:
        sorted_subtasks = sorted(
            main_task.subtasks,
            key=lambda subtask: subtask.order,
        )
        structured_subtasks = [
            StructuredSubtaskOutput(
                title=subtask.title,
                description=subtask.description,
                priority=subtask.priority,
                estimated_time=subtask.estimated_time,
                order=subtask.order,
            )
            for subtask in sorted_subtasks
        ]

        structured_main_tasks.append(
            StructuredMainTaskOutput(
                title=main_task.title,
                description=main_task.description,
                estimated_time=main_task.estimated_time,
                order=main_task.order,
                subtasks=structured_subtasks,
            )
        )

    return StructuredTaskOutput(
        plan_summary=planning_output.plan_summary,
        main_tasks=structured_main_tasks,
    )
