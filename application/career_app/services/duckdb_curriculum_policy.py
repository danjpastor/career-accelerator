from __future__ import annotations

"""Scheduling and prerequisite policy for the compact SQL challenge track.

The native DuckDB workspace remains unchanged. Stable internal IDs preserve
existing progress and managed task keys, while learner-facing SQL Challenge
numbers follow the audited curriculum order stored in the catalog.
"""

from datetime import date, timedelta
from typing import Any
import re

from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES,
    ordered_exercise_numbers,
    roadmap_number,
)

_INSTALLED = False
ROADMAP_INTERNAL_ORDER = tuple(ordered_exercise_numbers())
TITLE_BY_ID = {
    internal_id: str(DUCKDB_EXERCISES[internal_id]["title"])
    for internal_id in ROADMAP_INTERNAL_ORDER
}
TERMINAL_CHAPTER_BY_ID = {
    internal_id: str(DUCKDB_EXERCISES[internal_id]["terminal_chapter"])
    for internal_id in ROADMAP_INTERNAL_ORDER
}
PRIOR_EXERCISES_BY_ID = {
    internal_id: tuple(
        int(value)
        for value in dict(
            DUCKDB_EXERCISES[internal_id].get("prerequisites") or {}
        ).get("prior_exercises", ())
    )
    for internal_id in ROADMAP_INTERNAL_ORDER
}
_DISPLAY_BY_ID = {
    internal_id: roadmap_number(internal_id)
    for internal_id in ROADMAP_INTERNAL_ORDER
}
_ID_BY_DISPLAY = {display: internal for internal, display in _DISPLAY_BY_ID.items()}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _row_value(row: Any, key: str, index: int = 0, default: Any = None) -> Any:
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        try:
            return row[index]
        except Exception:
            return default


def _table_exists(conn: Any, name: str) -> bool:
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (str(name),),
        ).fetchone() is not None
    except Exception:
        return False


def _apply_catalog_overlay() -> None:
    """Validate the static catalog and synchronize the shared chapter gate map."""
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
    from career_app.services import content_gates

    if set(DUCKDB_EXERCISES) != set(ROADMAP_INTERNAL_ORDER):
        missing = sorted(set(ROADMAP_INTERNAL_ORDER) - set(DUCKDB_EXERCISES))
        extra = sorted(set(DUCKDB_EXERCISES) - set(ROADMAP_INTERNAL_ORDER))
        raise RuntimeError(f"SQL challenge catalog mismatch; missing={missing}, extra={extra}")
    unknown = sorted(set(TERMINAL_CHAPTER_BY_ID.values()) - set(CHAPTER_BY_KEY))
    if unknown:
        raise RuntimeError(f"Unknown DataCamp terminal chapters: {unknown}")

    content_gates.DUCKDB_TERMINAL_CHAPTER.clear()
    content_gates.DUCKDB_TERMINAL_CHAPTER.update(TERMINAL_CHAPTER_BY_ID)


def _program_start(conn: Any) -> date:
    if _table_exists(conn, "program_state"):
        row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
        raw = _row_value(row, "start_date", 0, None)
        try:
            return date.fromisoformat(str(raw))
        except (TypeError, ValueError):
            pass
    today = date.today()
    return today - timedelta(days=today.weekday())


def scheduled_date(conn: Any, internal_id: int) -> date:
    """Return the terminal DataCamp chapter's own scheduled date."""
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY

    chapter = CHAPTER_BY_KEY[TERMINAL_CHAPTER_BY_ID[int(internal_id)]]
    return chapter.scheduled_date(_program_start(conn))


def _display_prerequisite_name(internal_id: int) -> str:
    internal_id = int(internal_id)
    return (
        f"SQL Challenge {_DISPLAY_BY_ID[internal_id]:02d}: "
        f"{DUCKDB_EXERCISES[internal_id]['title']}"
    )


def _rewrite_readiness_result(result: dict[str, Any]) -> dict[str, Any]:
    rewritten = dict(result)
    missing: list[str] = []
    for value in list(result.get("missing") or []):
        text = str(value)
        match = re.fullmatch(r"DuckDB Exercise\s+(\d+)(?::.*)?", text, re.I)
        if match:
            internal = int(match.group(1))
            if internal in _DISPLAY_BY_ID:
                text = _display_prerequisite_name(internal)
        missing.append(text)
    missing = list(dict.fromkeys(missing))
    rewritten["missing"] = missing
    rewritten["ready"] = not missing
    rewritten["reason"] = "" if not missing else "Complete " + ", ".join(missing) + " first."
    return rewritten


def _task_internal_id(task: dict[str, Any]) -> int | None:
    for value in (
        task.get("starter_path"),
        task.get("managed_key"),
        task.get("target_key"),
        task.get("source_key"),
    ):
        match = re.search(r"(?:roadmap_v1026:)?duckdb:(\d+)", str(value or ""), re.I)
        if match:
            candidate = int(match.group(1))
            if candidate in _DISPLAY_BY_ID:
                return candidate
    try:
        from career_app.data.duckdb_exercises import exercise_number_for_label
        candidate = exercise_number_for_label(str(task.get("label") or ""))
    except Exception:
        candidate = None
    return int(candidate) if candidate in _DISPLAY_BY_ID else None


def _weekday_schedule_ready(
    conn: Any, internal_id: int, *, today: date | None = None
) -> tuple[bool, str]:
    today = today or date.today()
    scheduled = scheduled_date(conn, internal_id)
    if today < scheduled:
        return False, "Scheduled for " + scheduled.strftime("%A, %B %d") + "."
    if today.weekday() > 4:
        return False, (
            "SQL challenge practice is scheduled Monday through Friday; "
            "weekends are reserved for projects."
        )
    return True, "Available for weekday SQL challenge practice."


def _clear_stale_focus(conn: Any, internal_ids: set[int] | None = None) -> None:
    if not _table_exists(conn, "daily_focus") or not _table_exists(conn, "task_metadata"):
        return
    rows = conn.execute(
        """SELECT s.id,s.label,m.managed_key,m.starter_path
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=0"""
    ).fetchall()
    stale_ids: list[int] = []
    for row in rows:
        task = {
            "label": _row_value(row, "label", 1, ""),
            "managed_key": _row_value(row, "managed_key", 2, ""),
            "starter_path": _row_value(row, "starter_path", 3, ""),
        }
        internal = _task_internal_id(task)
        if internal is None or (internal_ids is not None and internal not in internal_ids):
            continue
        calendar_ready, _ = _weekday_schedule_ready(conn, internal)
        if not calendar_ready:
            stale_ids.append(_safe_int(_row_value(row, "id", 0, 0)))
    if stale_ids:
        placeholders = ",".join("?" for _ in stale_ids)
        conn.execute(
            f"DELETE FROM daily_focus WHERE task_id IN ({placeholders}) AND completed_at IS NULL",
            tuple(stale_ids),
        )
        if _table_exists(conn, "settings"):
            conn.execute("DELETE FROM settings WHERE key LIKE 'daily_focus_snapshot_v2:%'")


def _stage_duckdb_task_orders(conn: Any) -> int:
    """Move SQL challenge task rows to collision-free temporary sort slots."""
    if not (_table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata")):
        return 0
    rows = conn.execute(
        """SELECT s.id,s.week
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:duckdb:%'
              OR m.starter_path LIKE 'duckdb:%'
           ORDER BY s.week,s.id"""
    ).fetchall()
    by_week: dict[int, list[int]] = {}
    for row in rows:
        task_id = _safe_int(_row_value(row, "id", 0, 0))
        week = _safe_int(_row_value(row, "week", 1, 1), 1)
        if task_id > 0:
            by_week.setdefault(week, []).append(task_id)
    staged = 0
    for week, task_ids in by_week.items():
        row = conn.execute(
            "SELECT MIN(sort_order) AS minimum_order FROM sprint_tasks WHERE week=?",
            (int(week),),
        ).fetchone()
        current_minimum = _safe_int(_row_value(row, "minimum_order", 0, 0), 0)
        base = min(current_minimum, -1000000) - len(task_ids) - 1000
        for offset, task_id in enumerate(task_ids, start=1):
            conn.execute(
                "UPDATE sprint_tasks SET sort_order=? WHERE id=?",
                (int(base - offset), int(task_id)),
            )
            staged += 1
    return staged


def _available_task_sort_order(
    conn: Any, *, week: int, preferred: int, task_id: int, after: int | None = None
) -> int:
    candidate = max(int(preferred), int(after) + 1 if after is not None else int(preferred))
    while True:
        occupied = conn.execute(
            "SELECT id FROM sprint_tasks WHERE week=? AND sort_order=? AND id<>? LIMIT 1",
            (int(week), int(candidate), int(task_id)),
        ).fetchone()
        if occupied is None:
            return candidate
        candidate += 1


def _sync_task_metadata(conn: Any) -> None:
    from career_app.services import roadmap_mastery

    if not (_table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata")):
        return
    _stage_duckdb_task_orders(conn)
    last_sort_by_week: dict[int, int] = {}
    for internal_id in ROADMAP_INTERNAL_ORDER:
        item = DUCKDB_EXERCISES[internal_id]
        managed = f"roadmap_v1026:duckdb:{internal_id}"
        row = conn.execute(
            """SELECT s.id,s.completed FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               WHERE m.managed_key=? LIMIT 1""",
            (managed,),
        ).fetchone()
        if row is None:
            continue
        task_id = _safe_int(_row_value(row, "id", 0, 0))
        completed = bool(_safe_int(_row_value(row, "completed", 1, 0)))
        readiness = roadmap_mastery.duckdb_readiness(conn, internal_id)
        schedule_day = scheduled_date(conn, internal_id)
        schedule_ready, schedule_reason = _weekday_schedule_ready(conn, internal_id)
        ready = completed or (bool(readiness.get("ready")) and schedule_ready)
        reason = None if ready else (
            schedule_reason if not schedule_ready else readiness.get("reason") or schedule_reason
        )
        target_week = int(item["week"])
        target_sort = _available_task_sort_order(
            conn,
            week=target_week,
            preferred=-760000 + _DISPLAY_BY_ID[internal_id] * 10,
            task_id=task_id,
            after=last_sort_by_week.get(target_week),
        )
        last_sort_by_week[target_week] = target_sort
        conn.execute(
            "UPDATE sprint_tasks SET week=?,sort_order=?,label=? WHERE id=?",
            (target_week, target_sort, str(item["label"]), task_id),
        )
        conn.execute(
            """UPDATE task_metadata
               SET prerequisite_state=?,prerequisite_reason=?,deferred_until=?,
                   description=?,definition_of_done=?,starter_path=?,category='SQL',
                   estimated_minutes=?
               WHERE task_id=?""",
            (
                "Ready" if ready else "Blocked",
                reason,
                None if completed or date.today() >= schedule_day else schedule_day.isoformat(),
                (
                    f"Focused SQL challenge aligned to {TERMINAL_CHAPTER_BY_ID[internal_id]}. "
                    "Complete the terminal DataCamp chapter and only the listed dependent challenges."
                ),
                "Pass the single task check and submit the saved SQL answer.",
                f"duckdb:{internal_id}",
                int(item.get("minutes", 25)),
                task_id,
            ),
        )
        if _table_exists(conn, "roadmap_requirement_state"):
            conn.execute(
                """UPDATE roadmap_requirement_state
                   SET title=?,due_week=?,reason=?,updated_at=CURRENT_TIMESTAMP
                   WHERE requirement_key=?""",
                (item["title"], target_week, reason, f"duckdb:{internal_id}"),
            )
    _clear_stale_focus(conn)


def audit_contract(root=None) -> list[str]:
    del root
    errors: list[str] = []
    if len(ROADMAP_INTERNAL_ORDER) != 33 or set(ROADMAP_INTERNAL_ORDER) != set(range(1, 34)):
        errors.append("SQL challenge order must contain every stable internal ID exactly once.")
    if set(TERMINAL_CHAPTER_BY_ID) != set(ROADMAP_INTERNAL_ORDER):
        errors.append("Terminal chapter map does not cover every SQL challenge.")
    if set(PRIOR_EXERCISES_BY_ID) != set(ROADMAP_INTERNAL_ORDER):
        errors.append("Prerequisite map does not cover every SQL challenge.")
    for internal_id in ROADMAP_INTERNAL_ORDER:
        item = DUCKDB_EXERCISES[internal_id]
        if int(item.get("roadmap_number", 0)) != _DISPLAY_BY_ID[internal_id]:
            errors.append(f"Internal challenge {internal_id} has the wrong display number.")
        for prior in PRIOR_EXERCISES_BY_ID[internal_id]:
            if prior not in _DISPLAY_BY_ID:
                errors.append(f"Challenge {internal_id} references unknown prerequisite {prior}.")
            elif _DISPLAY_BY_ID[prior] >= _DISPLAY_BY_ID[internal_id]:
                errors.append(
                    f"SQL Challenge {_DISPLAY_BY_ID[internal_id]:02d} has a forward prerequisite."
                )
    try:
        from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
        for internal_id, chapter_key in TERMINAL_CHAPTER_BY_ID.items():
            if chapter_key not in CHAPTER_BY_KEY:
                errors.append(f"Challenge {internal_id} uses unknown chapter {chapter_key}.")
            elif int(DUCKDB_EXERCISES[internal_id]["week"]) != int(CHAPTER_BY_KEY[chapter_key].week):
                errors.append(f"Challenge {internal_id} is assigned to the wrong roadmap week.")
    except Exception as exc:
        errors.append(f"Could not validate DataCamp chapter alignment: {exc}")
    return errors


def _install_readiness_and_sync() -> None:
    from career_app.services import roadmap_mastery

    if getattr(roadmap_mastery, "_duckdb_curriculum_audit_installed", False):
        return
    original_readiness = roadmap_mastery.duckdb_readiness
    original_reconcile = roadmap_mastery.reconcile

    def duckdb_readiness(conn: Any, number: int) -> dict[str, Any]:
        return _rewrite_readiness_result(original_readiness(conn, int(number)))

    def reconcile(conn: Any, root: Any = None) -> dict[str, Any]:
        result = original_reconcile(conn, root)
        _sync_task_metadata(conn)
        conn.commit()
        return result

    roadmap_mastery.duckdb_readiness = duckdb_readiness
    roadmap_mastery.reconcile = reconcile
    roadmap_mastery._duckdb_curriculum_audit_installed = True


def _install_unified_task_policy() -> None:
    from career_app.services import roadmap_mastery, unified_tasks

    if getattr(unified_tasks, "_duckdb_curriculum_policy_installed", False):
        return
    original_readiness = unified_tasks._readiness
    original_ready_tasks = unified_tasks.ready_tasks
    original_daily_plan = unified_tasks.daily_plan
    original_snapshot = unified_tasks._ensure_daily_snapshot

    def readiness(conn: Any, task: dict[str, Any], current_week: int):
        internal = _task_internal_id(task)
        if internal is None:
            return original_readiness(conn, task, current_week)
        result = roadmap_mastery.duckdb_readiness(conn, internal)
        schedule_ready, schedule_reason = _weekday_schedule_ready(conn, internal)
        ready = bool(result.get("ready")) and schedule_ready
        reason = "" if ready else (result.get("reason") or schedule_reason)
        return unified_tasks.Readiness(ready, str(reason))

    def ready_tasks(conn: Any, current_week: int) -> list[dict[str, Any]]:
        rows = list(original_ready_tasks(conn, current_week))
        return [
            task for task in rows
            if _task_internal_id(task) is None or readiness(conn, task, current_week).ready
        ]

    def ensure_snapshot(conn: Any, current_week: int, max_items: int, tasks: list[dict[str, Any]]):
        eligible: list[dict[str, Any]] = []
        for task in tasks:
            internal = _task_internal_id(task)
            if internal is None or _weekday_schedule_ready(conn, internal)[0]:
                eligible.append(task)
        _clear_stale_focus(conn)
        return original_snapshot(conn, current_week, max_items, eligible)

    def daily_plan(conn: Any, current_week: int, max_items: int = 5) -> list[dict[str, Any]]:
        rows = list(original_daily_plan(conn, current_week, max_items))
        filtered = [
            task for task in rows
            if _task_internal_id(task) is None
            or _weekday_schedule_ready(conn, int(_task_internal_id(task)))[0]
        ]
        if len(filtered) != len(rows):
            _clear_stale_focus(conn)
            conn.commit()
        return filtered

    unified_tasks._readiness = readiness
    unified_tasks.ready_tasks = ready_tasks
    unified_tasks._ensure_daily_snapshot = ensure_snapshot
    unified_tasks.daily_plan = daily_plan
    unified_tasks._duckdb_curriculum_policy_installed = True


def install(CareerAccelerator: type | None = None) -> None:
    del CareerAccelerator
    global _INSTALLED
    if _INSTALLED:
        return
    _apply_catalog_overlay()
    _install_readiness_and_sync()
    _install_unified_task_policy()
    _INSTALLED = True
