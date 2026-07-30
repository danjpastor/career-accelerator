from __future__ import annotations

"""Planner integration for the weekday-learning / weekend-project rhythm.

Required DataCamp chapters are eligible for planner placement Monday through
Friday. DataCamp project tasks are eligible only on their assigned weekend day.
The policy is applied at the unified task layer so stale daily snapshots cannot
keep an item on the wrong day after an upgrade or prerequisite change.
"""

from datetime import date
import json
from typing import Any, Callable

from career_app.services import datacamp_projects

_INSTALLED = False


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _project_for_task(conn: Any, task: dict[str, Any]) -> dict[str, Any] | None:
    task_id = _safe_int(task.get("id") or task.get("task_id"), 0)
    if not task_id:
        return None
    try:
        return datacamp_projects.project_for_task(conn, task_id)
    except Exception:
        return None


def _is_project_task(conn: Any, task: dict[str, Any]) -> bool:
    managed_key = str(task.get("managed_key") or "").casefold()
    if managed_key.startswith("datacamp_project:"):
        return True
    return _project_for_task(conn, task) is not None


def _allowed_today(conn: Any, task: dict[str, Any], today: date | None = None) -> bool:
    today = today or date.today()
    kind = str(task.get("kind") or "")
    if kind == "datacamp_chapter":
        return today.weekday() <= 4
    if kind != "datacamp_project" and not _is_project_task(conn, task):
        return True

    # Projects never consume weekday learning slots.
    if today.weekday() <= 4:
        return False

    project = _project_for_task(conn, task)
    if not project:
        return False
    scheduled_weekday = _safe_int(project.get("scheduled_weekday"), 5)
    # Saturday projects may remain available Sunday if unfinished. Sunday-only
    # supplemental work does not move forward to Saturday.
    return today.weekday() >= scheduled_weekday


def _clear_stale_today_rows(
    conn: Any,
    current_week: int,
    tasks: list[dict[str, Any]],
    today: date | None = None,
) -> None:
    today = today or date.today()
    focus_date = today.isoformat()
    by_id = {_safe_int(task.get("id"), 0): task for task in tasks}
    disallowed_ids = {
        task_id
        for task_id, task in by_id.items()
        if task_id and not _allowed_today(conn, task, today)
    }
    if not disallowed_ids:
        return

    placeholders = ",".join("?" for _ in disallowed_ids)
    table_exists = getattr(datacamp_projects, "_table_exists", None)
    has_daily_focus = bool(
        callable(table_exists) and table_exists(conn, "daily_focus")
    )
    if has_daily_focus:
        conn.execute(
            f"DELETE FROM daily_focus WHERE focus_date=? AND task_id IN ({placeholders})",
            (focus_date, *sorted(disallowed_ids)),
        )

    if not (callable(table_exists) and table_exists(conn, "settings")):
        return
    key = f"daily_focus_snapshot_v2:{focus_date}"
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if row is None:
        return
    try:
        raw = row["value"] if hasattr(row, "keys") else row[0]
        payload = json.loads(str(raw or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        conn.execute("DELETE FROM settings WHERE key=?", (key,))
        return
    assignments = payload.get("new_assignments") or []
    stale = any(
        _safe_int(item.get("task_id"), 0) in disallowed_ids
        for item in assignments
        if isinstance(item, dict)
    )
    if stale or _safe_int(payload.get("week"), current_week) != int(current_week):
        conn.execute("DELETE FROM settings WHERE key=?", (key,))


def install(CareerAccelerator: type | None = None) -> None:
    """Install compatibility wrappers exactly once.

    ``CareerAccelerator`` is accepted for the same integration convention used
    by other runtime patches, but the behavior belongs to unified_tasks and does
    not depend on a particular dashboard implementation.
    """

    del CareerAccelerator
    global _INSTALLED
    if _INSTALLED:
        return

    from career_app.services import unified_tasks

    original_kind: Callable[..., Any] = unified_tasks._kind
    original_readiness: Callable[..., Any] = unified_tasks._readiness
    original_task_type_label: Callable[..., Any] = unified_tasks.task_type_label
    original_focus_context: Callable[..., Any] = unified_tasks.focus_context
    original_source: Callable[..., Any] = unified_tasks._source
    original_display_title: Callable[..., Any] = unified_tasks._display_title
    original_roadmap_sort: Callable[..., Any] = unified_tasks._roadmap_sort
    original_ensure_snapshot: Callable[..., Any] = unified_tasks._ensure_daily_snapshot
    original_sync_catchup: Callable[..., Any] = unified_tasks._sync_active_catchup
    original_ready_tasks: Callable[..., Any] = unified_tasks.ready_tasks
    original_daily_plan: Callable[..., Any] = unified_tasks.daily_plan

    def kind(conn: Any, task: dict[str, Any]) -> str:
        if _is_project_task(conn, task):
            return "datacamp_project"
        return str(original_kind(conn, task))

    def readiness(conn: Any, task: dict[str, Any], current_week: int) -> Any:
        if str(task.get("kind") or "") == "datacamp_project" or _is_project_task(conn, task):
            ready, reason = datacamp_projects.project_readiness(
                conn,
                task_id=_safe_int(task.get("id") or task.get("task_id"), 0),
                today=date.today(),
            )
            return unified_tasks.Readiness(bool(ready), str(reason or ""))
        return original_readiness(conn, task, current_week)

    def task_type_label(task: dict[str, Any], current_week: int | None = None) -> str:
        if str(task.get("kind") or "") == "datacamp_project":
            return "DataCamp Project"
        return str(original_task_type_label(task, current_week))

    def focus_context(task: dict[str, Any], current_week: int) -> str:
        if str(task.get("kind") or "") == "datacamp_project":
            week = max(1, _safe_int(task.get("week"), current_week))
            if bool(task.get("is_catch_up")):
                return f"Catch-Up • DataCamp Project • Week {week}"
            return f"DataCamp Project • Weekend • Week {week}"
        return str(original_focus_context(task, current_week))

    def source(task: dict[str, Any]) -> str:
        if str(task.get("kind") or "") == "datacamp_project":
            stored = str(task.get("source") or task.get("source_label") or "").strip()
            return stored or "DataCamp Project"
        return str(original_source(task))

    def display_title(task: dict[str, Any]) -> str:
        if str(task.get("kind") or "") == "datacamp_project":
            return "DataCamp Project"
        return str(original_display_title(task))

    def roadmap_sort(task: dict[str, Any], current_week: int) -> tuple[Any, ...]:
        if str(task.get("kind") or "") != "datacamp_project":
            return tuple(original_roadmap_sort(task, current_week))
        scheduled_week = _safe_int(task.get("week"), current_week)
        if scheduled_week == int(current_week):
            week_rank = 0
        elif scheduled_week < int(current_week):
            week_rank = 1
        else:
            week_rank = 2
        return (
            week_rank,
            1,
            25,
            scheduled_week,
            _safe_int(task.get("sort_order"), 0),
            _safe_int(task.get("id"), 0),
        )

    def ensure_daily_snapshot(
        conn: Any,
        current_week: int,
        max_items: int,
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        _refresh_catchup_policy_cache(conn)
        _clear_stale_today_rows(conn, current_week, tasks)
        eligible = [task for task in tasks if _allowed_today(conn, task)]
        return original_ensure_snapshot(conn, current_week, max_items, eligible)

    def sync_active_catchup(
        conn: Any,
        focus_date: str,
        current_week: int,
        slots: int,
        ready: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        eligible = [task for task in ready if _allowed_today(conn, task)]
        return list(original_sync_catchup(conn, focus_date, current_week, slots, eligible))

    def ready_tasks(conn: Any, current_week: int) -> list[dict[str, Any]]:
        return [
            task
            for task in original_ready_tasks(conn, current_week)
            if _allowed_today(conn, task)
        ]

    def daily_plan(conn: Any, current_week: int, max_items: int = 5) -> list[dict[str, Any]]:
        result = list(original_daily_plan(conn, current_week, max_items))
        filtered = [task for task in result if _allowed_today(conn, task)]
        if len(filtered) != len(result):
            _clear_stale_today_rows(conn, current_week, result)
            conn.commit()
        return filtered

    unified_tasks._kind = kind
    unified_tasks._readiness = readiness
    unified_tasks.task_type_label = task_type_label
    unified_tasks.focus_context = focus_context
    unified_tasks._source = source
    unified_tasks._display_title = display_title
    unified_tasks._roadmap_sort = roadmap_sort
    unified_tasks._ensure_daily_snapshot = ensure_daily_snapshot
    unified_tasks._sync_active_catchup = sync_active_catchup
    unified_tasks.ready_tasks = ready_tasks
    unified_tasks.daily_plan = daily_plan

    _INSTALLED = True

# BEGIN DATACAMP CATCH-UP WEEKDAY ACCESS v10.41.2
# Current-week projects keep their Saturday/Sunday schedule. Projects from an
# earlier roadmap week are catch-up tasks and can use an open weekday slot.
_catchup_base_allowed_today = _allowed_today
_CATCHUP_POLICY_CACHE_KEY = "datacamp_catchup_project_access:v10.41.2"


def _catchup_policy_current_week(conn):
    try:
        row = conn.execute(
            "SELECT current_week FROM program_state WHERE id=1"
        ).fetchone()
    except Exception:
        row = None
    if row is None:
        return 1
    try:
        value = row["current_week"] if hasattr(row, "keys") else row[0]
        return max(1, int(value or 1))
    except (TypeError, ValueError, KeyError, IndexError):
        return 1


def _catchup_project_week(task, project):
    return max(
        1,
        _safe_int(
            (project or {}).get("week") or task.get("week"),
            1,
        ),
    )


def _allowed_today(conn, task, today=None):
    today = today or date.today()
    kind = str(task.get("kind") or "")
    if kind == "datacamp_project" or _is_project_task(conn, task):
        project = _project_for_task(conn, task)
        if project is not None:
            if _catchup_project_week(task, project) < _catchup_policy_current_week(conn):
                return True
    return _catchup_base_allowed_today(conn, task, today)


def _refresh_catchup_policy_cache(conn, today=None):
    """Rebuild today's auto-generated focus once after installing this policy."""

    today = today or date.today()
    table_exists = getattr(datacamp_projects, "_table_exists", None)
    if not callable(table_exists) or not table_exists(conn, "settings"):
        return
    row = conn.execute(
        "SELECT value FROM settings WHERE key=?", (_CATCHUP_POLICY_CACHE_KEY,)
    ).fetchone()
    if row is not None:
        return

    focus_date = today.isoformat()
    if table_exists(conn, "daily_focus"):
        conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (focus_date,))
    conn.execute(
        "DELETE FROM settings WHERE key=?",
        (f"daily_focus_snapshot_v2:{focus_date}",),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
        (_CATCHUP_POLICY_CACHE_KEY, "1"),
    )
    conn.commit()
# END DATACAMP CATCH-UP WEEKDAY ACCESS v10.41.2
