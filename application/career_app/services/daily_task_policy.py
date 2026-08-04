from __future__ import annotations

"""Day-assigned planner policy for Career Accelerator v10.44.0.

The active dashboard must reflect the roadmap day rather than a five-item ready
queue:

* every incomplete task assigned to today is visible;
* prerequisite-blocked tasks remain visible and grey;
* completed tasks are excluded from active queues immediately;
* catch-up work enters Today's Focus only after today's assignments are clear;
* Next Tasks orders today's work first and catch-up work second;
* weekly checks exclude weekend DataCamp projects from coursework; and
* retrospectives and weekend projects require the matching weekly check.
"""

from datetime import date
import sqlite3
from typing import Any, Callable

_INSTALLED = False
_GROUP_CACHE: dict[int, tuple[tuple[Any, ...], list[dict[str, Any]]]] = {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _task_id(task: dict[str, Any]) -> int:
    return _safe_int(task.get("id") or task.get("task_id"), 0)


def _dedupe(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from career_app.services import unified_tasks

    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for task in tasks:
        identity = unified_tasks._semantic_task_identity(task)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(task)
    return result


def _display_sort(task: dict[str, Any], current_week: int) -> tuple[Any, ...]:
    from career_app.services import sprint_day_planner

    return sprint_day_planner.task_display_sort(task, int(current_week))


def _cache_key(conn: sqlite3.Connection, current_week: int) -> tuple[Any, ...]:
    return (
        id(conn),
        int(current_week),
        date.today().isoformat(),
        int(getattr(conn, "total_changes", 0)),
    )


def _day_groups(conn: sqlite3.Connection, current_week: int) -> list[dict[str, Any]]:
    from career_app.services import sprint_day_planner

    key = _cache_key(conn, current_week)
    cached = _GROUP_CACHE.get(id(conn))
    if cached is not None and cached[0] == key:
        return cached[1]
    groups = list(sprint_day_planner.current_sprint_day_groups(conn, int(current_week)))
    # Schema/bootstrap helpers can write while constructing the first snapshot.
    # Store the post-call total_changes value so repeated dashboard reads reuse it.
    _GROUP_CACHE[id(conn)] = (_cache_key(conn, current_week), groups)
    return groups


def _is_current_week_assignment(task: dict[str, Any], current_week: int) -> bool:
    scheduled_week = _safe_int(
        task.get("scheduled_week"),
        _safe_int(task.get("week"), current_week),
    )
    return not bool(task.get("is_catch_up")) and scheduled_week == int(current_week)


def _normalize_scheduled_task(
    task: dict[str, Any],
    *,
    current_week: int,
    queue_section: str,
) -> dict[str, Any]:
    item = dict(task)
    item["id"] = _task_id(item)
    item["task_id"] = item["id"]
    item["completed"] = bool(item.get("completed"))
    # Day groups deliberately strip calendar timing from prerequisite readiness.
    # Use that result for the scheduled day instead of a stale canonical `ready`
    # value that may still reflect yesterday's timing lock.
    if "prerequisites_ready" in item:
        item["ready"] = bool(item.get("prerequisites_ready"))
    elif "ready" not in item:
        item["ready"] = False
    item["queue_section"] = queue_section
    item["focus_kind"] = queue_section
    item["is_catch_up"] = queue_section == "catch_up"
    if not bool(item.get("ready")) and not str(item.get("prerequisite_reason") or "").strip():
        item["prerequisite_reason"] = "Complete the prerequisite first."
    return item


def _today_group(conn: sqlite3.Connection, current_week: int) -> dict[str, Any] | None:
    today_text = date.today().isoformat()
    return next(
        (group for group in _day_groups(conn, current_week) if str(group.get("date")) == today_text),
        None,
    )


def _today_assignments(
    conn: sqlite3.Connection,
    current_week: int,
    *,
    include_completed: bool = False,
) -> list[dict[str, Any]]:
    group = _today_group(conn, current_week)
    if group is None:
        return []
    result: list[dict[str, Any]] = []
    for raw in group.get("tasks") or []:
        if not _is_current_week_assignment(raw, current_week):
            continue
        item = _normalize_scheduled_task(
            raw,
            current_week=current_week,
            queue_section="today",
        )
        if not include_completed and bool(item.get("completed")):
            continue
        result.append(item)
    return result


def _promoted_assignments(
    conn: sqlite3.Connection,
    current_week: int,
) -> list[dict[str, Any]]:
    from career_app.services import sprint_day_planner

    result: list[dict[str, Any]] = []
    for raw in sprint_day_planner.promoted_tasks(conn, int(current_week)):
        if bool(raw.get("completed")):
            continue
        item = _normalize_scheduled_task(
            raw,
            current_week=current_week,
            queue_section="promoted",
        )
        item["is_promoted"] = True
        result.append(item)
    return result


def _catch_up_assignments(
    conn: sqlite3.Connection,
    current_week: int,
) -> list[dict[str, Any]]:
    from career_app.services import unified_tasks

    result: list[dict[str, Any]] = []
    today_text = date.today().isoformat()

    # An incomplete assignment from an earlier day in the current sprint is
    # catch-up work too. Older builds only checked the task's week number, which
    # made Monday work disappear from Next Tasks on Tuesday.
    for group in _day_groups(conn, int(current_week)):
        if str(group.get("date") or "") >= today_text:
            continue
        for raw in group.get("tasks") or []:
            if bool(raw.get("completed")) or not _is_current_week_assignment(raw, current_week):
                continue
            item = _normalize_scheduled_task(
                raw,
                current_week=current_week,
                queue_section="catch_up",
            )
            item["is_catch_up"] = True
            result.append(item)

    # Retain the existing cross-week catch-up behavior.
    for raw in unified_tasks.all_tasks(conn, int(current_week)):
        task_week = _safe_int(raw.get("week"), current_week)
        if bool(raw.get("completed")):
            continue
        if not (bool(raw.get("is_catch_up")) or task_week < int(current_week)):
            continue
        item = _normalize_scheduled_task(
            raw,
            current_week=current_week,
            queue_section="catch_up",
        )
        item["is_catch_up"] = True
        result.append(item)
    result.sort(key=lambda item: _display_sort(item, int(current_week)))
    return _dedupe(result)


def _scheduled_day_label(value: Any) -> str:
    try:
        scheduled = date.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return "later this week"
    return scheduled.strftime("%A")


def _upcoming_current_week(
    conn: sqlite3.Connection,
    current_week: int,
) -> list[dict[str, Any]]:
    """Return future-day assignments as grey Coming Soon previews.

    Content readiness is deliberately retained in ``prerequisites_ready`` for
    diagnostics, but a task assigned to a later day is never actionable in
    Next Tasks before that day arrives.
    """
    today_text = date.today().isoformat()
    result: list[dict[str, Any]] = []
    for group in _day_groups(conn, current_week):
        scheduled_date = str(group.get("date") or "")
        if scheduled_date <= today_text:
            continue
        for raw in group.get("tasks") or []:
            if bool(raw.get("completed")) or not _is_current_week_assignment(raw, current_week):
                continue
            item = _normalize_scheduled_task(
                raw,
                current_week=current_week,
                queue_section="upcoming",
            )
            content_ready = bool(item.get("ready"))
            item["prerequisites_ready"] = content_ready
            item["ready"] = False
            item["scheduled_date"] = scheduled_date
            item["scheduled_day"] = _scheduled_day_label(scheduled_date)
            if content_ready:
                item["prerequisite_reason"] = (
                    f"Scheduled for {item['scheduled_day']}."
                )
            elif not str(item.get("prerequisite_reason") or "").strip():
                item["prerequisite_reason"] = "Complete the prerequisite first."
            result.append(item)
    return _dedupe(result)


def _project_task_ids(conn: sqlite3.Connection) -> set[int]:
    result: set[int] = set()
    try:
        rows = conn.execute(
            "SELECT task_id FROM datacamp_project_tasks WHERE task_id IS NOT NULL"
        ).fetchall()
        result.update(_safe_int(row[0], 0) for row in rows)
    except Exception:
        pass
    try:
        rows = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key LIKE 'datacamp_project:%'"
        ).fetchall()
        result.update(_safe_int(row[0], 0) for row in rows)
    except Exception:
        pass
    result.discard(0)
    return result


def _install_weekly_check_contract() -> None:
    from career_app.services import task_workspace, weekly_checks

    original_incomplete: Callable[..., Any] = weekly_checks.incomplete_required_tasks
    if not getattr(original_incomplete, "_weekday_coursework_only", False):
        def incomplete_required_tasks(conn: sqlite3.Connection, week: int) -> list[dict[str, Any]]:
            project_ids = _project_task_ids(conn)
            return [
                item
                for item in original_incomplete(conn, int(week))
                if _safe_int(item.get("week"), int(week)) == int(week)
                and _safe_int(item.get("task_id"), 0) not in project_ids
            ]

        incomplete_required_tasks._weekday_coursework_only = True  # type: ignore[attr-defined]
        weekly_checks.incomplete_required_tasks = incomplete_required_tasks

    original_readiness: Callable[..., Any] = weekly_checks.readiness
    if not getattr(original_readiness, "_weekday_coursework_reason_wrapped", False):
        def readiness(conn: sqlite3.Connection, week: int):
            result = original_readiness(conn, int(week))
            if result.ready or not result.missing:
                return result
            return weekly_checks.GateResult(
                False,
                result.missing,
                f"Complete the listed required Monday–Friday Week {int(week)} coursework before taking this check.",
            )

        readiness._weekday_coursework_reason_wrapped = True  # type: ignore[attr-defined]
        weekly_checks.readiness = readiness

    original_reconcile: Callable[..., Any] = weekly_checks.reconcile
    if not getattr(original_reconcile, "_retrospective_task_wrapped", False):
        def reconcile(conn: sqlite3.Connection) -> dict[str, int]:
            result = dict(original_reconcile(conn))
            row = conn.execute(
                "SELECT current_week FROM program_state WHERE id=1"
            ).fetchone()
            current_week = max(1, _safe_int(row[0] if row else 1, 1))
            ensured = 0
            for week in range(1, current_week + 1):
                existing = conn.execute(
                    """SELECT 1 FROM sprint_tasks
                       WHERE week=? AND LOWER(label) LIKE '%retrospective%'
                       LIMIT 1""",
                    (week,),
                ).fetchone()
                if week == current_week or existing is None:
                    task_workspace.ensure_weekly_workspace_task(conn, week, "retrospective")
                    ensured += 1
            result["retrospectives_ensured"] = ensured
            return result

        reconcile._retrospective_task_wrapped = True  # type: ignore[attr-defined]
        weekly_checks.reconcile = reconcile


def _resolve_project(conn: sqlite3.Connection, task_id: Any, project_key: Any) -> dict[str, Any] | None:
    from career_app.services import datacamp_projects

    resolver = getattr(datacamp_projects, "_weekend_project_from_identity", None)
    if callable(resolver):
        try:
            return resolver(conn, task_id=task_id, project_key=project_key)
        except Exception:
            pass
    if task_id is not None:
        try:
            return datacamp_projects.project_for_task(conn, int(task_id))
        except Exception:
            pass
    project_map = getattr(datacamp_projects, "PROJECT_BY_KEY", {})
    return dict(project_map.get(str(project_key or ""), {})) or None


def _install_project_check_gate() -> None:
    from career_app.services import datacamp_projects, weekly_checks

    original: Callable[..., Any] = datacamp_projects.project_readiness
    if getattr(original, "_weekly_check_gate_wrapped", False):
        return

    def project_readiness(conn, task_id=None, project_key=None, today=None):
        ready, reason = original(
            conn,
            task_id=task_id,
            project_key=project_key,
            today=today,
        )
        if str(reason or "").casefold().startswith("already completed"):
            return ready, reason
        project = _resolve_project(conn, task_id, project_key)
        if project is None:
            return ready, reason
        project_week = max(1, _safe_int(project.get("week"), 1))
        if not weekly_checks.passed(conn, project_week):
            return (
                False,
                f"Pass Week {project_week} Knowledge Check to unlock this weekend project.",
            )
        return ready, reason

    project_readiness._weekly_check_gate_wrapped = True  # type: ignore[attr-defined]
    datacamp_projects.project_readiness = project_readiness


def _install_planner_policy() -> None:
    from career_app.services import unified_tasks

    if getattr(unified_tasks, "_day_assigned_policy_installed", False):
        return

    def daily_plan(
        conn: sqlite3.Connection,
        current_week: int,
        max_items: int = 5,
    ) -> list[dict[str, Any]]:
        # max_items is intentionally ignored. Today's Focus is the complete set
        # of incomplete assignments for the day, not a five-task recommendation.
        del max_items
        today_items = _dedupe(
            [
                *_today_assignments(conn, int(current_week)),
                *_promoted_assignments(conn, int(current_week)),
            ]
        )
        if today_items:
            return sorted(
                today_items,
                key=lambda item: _display_sort(item, int(current_week)),
            )
        return sorted(
            _catch_up_assignments(conn, int(current_week)),
            key=lambda item: _display_sort(item, int(current_week)),
        )

    def next_tasks(
        conn: sqlite3.Connection,
        current_week: int,
        limit: int = 4,
    ) -> list[dict[str, Any]]:
        """Return only actionable today/promoted and catch-up work.

        Current-day work stays ahead of backlog work. Future-day assignments
        and any task with an unmet prerequisite belong in ``coming_up``.
        """
        today = _dedupe(
            [
                *_today_assignments(conn, int(current_week)),
                *_promoted_assignments(conn, int(current_week)),
            ]
        )
        catch_up = _catch_up_assignments(conn, int(current_week))
        ready_today = sorted(
            [item for item in today if bool(item.get("ready"))],
            key=lambda item: _display_sort(item, int(current_week)),
        )
        ready_catch_up = sorted(
            [item for item in catch_up if bool(item.get("ready"))],
            key=lambda item: _display_sort(item, int(current_week)),
        )
        queue = _dedupe([*ready_today, *ready_catch_up])
        requested = int(limit or 0)
        return queue if requested <= 0 else queue[: max(1, requested)]

    def coming_up(
        conn: sqlite3.Connection,
        current_week: int,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Return locked work and future-day previews below Coming Soon."""
        today = _dedupe(
            [
                *_today_assignments(conn, int(current_week)),
                *_promoted_assignments(conn, int(current_week)),
            ]
        )
        catch_up = _catch_up_assignments(conn, int(current_week))
        locked_today = sorted(
            [item for item in today if not bool(item.get("ready"))],
            key=lambda item: _display_sort(item, int(current_week)),
        )
        locked_catch_up = sorted(
            [item for item in catch_up if not bool(item.get("ready"))],
            key=lambda item: _display_sort(item, int(current_week)),
        )
        future = _upcoming_current_week(conn, int(current_week))
        queue = _dedupe([*locked_today, *locked_catch_up, *future])
        requested = int(limit or 0)
        return queue if requested <= 0 else queue[: max(1, requested)]

    def completion_summary(
        conn: sqlite3.Connection,
        active_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        from career_app.services import sprint_day_planner

        today_all = _today_assignments(
            conn,
            int(
                (conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone() or [1])[0]
            ),
            include_completed=True,
        )
        current_week = max(
            1,
            _safe_int(
                (conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone() or [1])[0],
                1,
            ),
        )
        promoted = sprint_day_planner.promotion_summary(conn)
        completed_today = [item for item in today_all if bool(item.get("completed"))]
        catchup_remaining = _catch_up_assignments(conn, current_week)
        planned_minutes = sum(
            max(5, _safe_int(item.get("estimated_minutes"), 30))
            for item in active_items
        )
        session_count = 0
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM study_sessions WHERE session_date=?",
                (date.today().isoformat(),),
            ).fetchone()
            session_count = _safe_int(row[0] if row else 0, 0)
        except Exception:
            pass
        new_total = len(today_all) + int(promoted.get("total") or 0)
        new_completed = len(completed_today) + int(promoted.get("completed") or 0)
        all_complete = not bool(active_items)
        return {
            "total_count": new_total,
            "completed_count": min(new_completed, new_total),
            "new_total_count": new_total,
            "new_completed_count": min(new_completed, new_total),
            "catchup_completed_count": 0,
            "catchup_remaining_count": len(catchup_remaining),
            "planned_minutes": planned_minutes,
            "completed_titles": [str(item.get("label") or "Completed task") for item in completed_today],
            "session_count": session_count,
            "active_extra": None,
            "all_base_complete": all_complete,
            "inferred_empty_complete": all_complete,
        }

    unified_tasks.daily_plan = daily_plan
    unified_tasks.next_tasks = next_tasks
    unified_tasks.coming_up = coming_up
    unified_tasks.completion_summary = completion_summary
    unified_tasks._day_assigned_policy_installed = True


def install(CareerAccelerator: type | None = None) -> None:
    """Install the final planner and gate policy after prior runtime wrappers."""

    del CareerAccelerator
    global _INSTALLED
    if _INSTALLED:
        return
    _install_weekly_check_contract()
    _install_project_check_gate()
    _install_planner_policy()
    _GROUP_CACHE.clear()
    _INSTALLED = True
