from datetime import datetime, timedelta, timezone
import re

from app.schemas.module_contracts import (
    PlanningCreateOutput,
    StructuredMainTaskOutput,
    StructuredSubtaskOutput,
    StructuredSummaryMetricsOutput,
    StructuredTaskOutput,
)

TAIPEI_TZ = timezone(timedelta(hours=8))
WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


def build_structured_task_output(
    planning_output: PlanningCreateOutput,
    *,
    known_information: list[dict[str, object]] | None = None,
    current_datetime: datetime | None = None,
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

    summary_metrics = StructuredSummaryMetricsOutput(
        total_estimated_time_text=_build_total_estimated_time_text(
            structured_main_tasks
        ),
        daily_time_budget_text=_extract_known_information_text(
            known_information,
            label="time_budget",
        )
        or "待確認",
        estimated_completion_text=_build_estimated_completion_text(
            known_information=known_information,
            current_datetime=current_datetime,
        ),
    )

    return StructuredTaskOutput(
        plan_summary=planning_output.plan_summary,
        summary_metrics=summary_metrics,
        main_tasks=structured_main_tasks,
    )


def _extract_known_information_text(
    known_information: list[dict[str, object]] | None,
    *,
    label: str,
) -> str | None:
    if not known_information:
        return None

    for item in known_information:
        if item.get("label") != label:
            continue

        value = item.get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _parse_estimated_time_to_minutes(value: str) -> int | None:
    normalized = value.strip().lower()
    if not normalized:
        return None

    if not _looks_like_total_effort_time(normalized):
        return None

    range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", normalized)
    range_average = (
        (float(range_match.group(1)) + float(range_match.group(2))) / 2
        if range_match
        else None
    )

    number_match = re.search(r"\d+(?:\.\d+)?", normalized)
    base_value = range_average if range_average is not None else (
        float(number_match.group(0)) if number_match else None
    )
    if base_value is None:
        return None

    if _has_minute_unit(normalized):
        return round(base_value)

    if _has_hour_unit(normalized):
        return round(base_value * 60)

    return None


def _has_minute_unit(value: str) -> bool:
    return (
        "分鐘" in value
        or "分" in value
        or "min" in value
        or value.endswith("m")
    )


def _has_hour_unit(value: str) -> bool:
    return (
        "小時" in value
        or "hour" in value
        or "hr" in value
        or value.endswith("h")
    )


def _looks_like_total_effort_time(value: str) -> bool:
    if not (_has_minute_unit(value) or _has_hour_unit(value)):
        return False

    unit_pattern = r"(?:小時|hours?|hrs?|h|分鐘|分|min|m)"
    total_effort_pattern = (
        rf"^(?:約\s*)?"
        rf"\d+(?:\.\d+)?"
        rf"(?:\s*-\s*\d+(?:\.\d+)?)?"
        rf"\s*{unit_pattern}$"
    )
    if not re.fullmatch(total_effort_pattern, value):
        return False

    cadence_markers = (
        "/",
        "每日",
        "每天",
        "一天",
        "每週",
        "每周",
        "一週",
        "一周",
        "每月",
        "每次",
        "一次",
        "per ",
    )
    return not any(marker in value for marker in cadence_markers)


def _format_minutes_label(minutes: int) -> str:
    if minutes < 60:
        return f"約 {minutes} 分鐘"

    hours = minutes / 60
    rounded = round(hours * 10) / 10
    display = f"{rounded:.0f}" if rounded.is_integer() else f"{rounded:.1f}"
    return f"約 {display} 小時"


def _build_total_estimated_time_text(
    structured_main_tasks: list[StructuredMainTaskOutput],
) -> str:
    if not structured_main_tasks:
        return "待確認"

    total_minutes = 0

    for task in structured_main_tasks:
        parsed_task_time = _parse_estimated_time_to_minutes(task.estimated_time)
        if parsed_task_time is None:
            return "待確認"

        total_minutes += parsed_task_time

    return _format_minutes_label(total_minutes)


def _build_estimated_completion_text(
    *,
    known_information: list[dict[str, object]] | None,
    current_datetime: datetime | None,
) -> str:
    deadline_hint = _extract_known_information_text(
        known_information,
        label="deadline_hint",
    )
    if not deadline_hint:
        return "待確認"

    reference = current_datetime or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    local_reference = reference.astimezone(TAIPEI_TZ)

    normalized_hint = deadline_hint.replace(" ", "")

    days_match = re.search(r"(\d+)天內", normalized_hint)
    if days_match:
        offset_days = int(days_match.group(1))
        target_date = local_reference.date() + timedelta(days=offset_days)
        return _format_date_with_weekday(target_date.year, target_date.month, target_date.day)

    if "明天" in normalized_hint:
        target_date = local_reference.date() + timedelta(days=1)
        return _format_date_with_weekday(target_date.year, target_date.month, target_date.day)

    if "今天" in normalized_hint:
        target_date = local_reference.date()
        return _format_date_with_weekday(target_date.year, target_date.month, target_date.day)

    return "待確認"


def _format_date_with_weekday(year: int, month: int, day: int) -> str:
    target = datetime(year, month, day, tzinfo=TAIPEI_TZ)
    weekday = WEEKDAY_LABELS[target.weekday()]
    return f"{year:04d}/{month:02d}/{day:02d}（週{weekday}）"
