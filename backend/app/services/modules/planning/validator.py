from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanningCreateValidationResult:
    is_valid: bool
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def validate_planning_create_output(
    value: dict[str, Any],
) -> PlanningCreateValidationResult:
    required_keys = {
        "plan_summary",
        "design_rationale",
        "assumptions_used",
        "schedule",
    }
    missing_keys = sorted(required_keys - set(value.keys()))
    if missing_keys:
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="missing_required_keys",
            details={"missing_keys": missing_keys},
        )

    if not _is_non_empty_string(value.get("plan_summary")):
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="invalid_plan_summary",
        )

    if not _is_non_empty_string(value.get("design_rationale")):
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="invalid_design_rationale",
        )

    assumptions_used = value.get("assumptions_used")
    if not isinstance(assumptions_used, list) or not all(
        isinstance(item, str) for item in assumptions_used
    ):
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="invalid_assumptions_used",
        )

    schedule = value.get("schedule")
    if not isinstance(schedule, dict):
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="invalid_schedule",
            details={"type": type(schedule).__name__},
        )

    main_tasks = schedule.get("main_tasks")
    if not isinstance(main_tasks, list):
        return PlanningCreateValidationResult(
            is_valid=False,
            reason="invalid_main_tasks",
        )

    for main_task in main_tasks:
        if not isinstance(main_task, dict):
            return PlanningCreateValidationResult(
                is_valid=False,
                reason="invalid_main_task_item",
            )
        if not all(
            key in main_task
            for key in ("title", "description", "estimated_time", "order", "subtasks")
        ):
            return PlanningCreateValidationResult(
                is_valid=False,
                reason="missing_main_task_fields",
            )
        if not isinstance(main_task.get("subtasks"), list):
            return PlanningCreateValidationResult(
                is_valid=False,
                reason="invalid_subtasks",
            )
        for subtask in main_task["subtasks"]:
            if not isinstance(subtask, dict):
                return PlanningCreateValidationResult(
                    is_valid=False,
                    reason="invalid_subtask_item",
                )
            if not all(
                key in subtask
                for key in (
                    "title",
                    "description",
                    "priority",
                    "estimated_time",
                    "order",
                )
            ):
                return PlanningCreateValidationResult(
                    is_valid=False,
                    reason="missing_subtask_fields",
                )
            if subtask.get("priority") not in {"high", "medium", "low"}:
                return PlanningCreateValidationResult(
                    is_valid=False,
                    reason="invalid_subtask_priority",
                )

    return PlanningCreateValidationResult(is_valid=True)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
