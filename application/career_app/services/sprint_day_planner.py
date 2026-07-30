from __future__ import annotations

"""Day-by-day sprint planning and temporary Today’s Focus promotion.

The original roadmap schedule is never rewritten. A promotion is a date-scoped
overlay that expires automatically when the local date changes, so unfinished
work returns to its original sprint day at midnight.
"""

from datetime import date, datetime, timedelta
import sqlite3
from typing import Any

PROMOTION_TABLE = "task_day_promotions"

_TIMING_REASON_PREFIXES = (
    "scheduled for ",
    "weekend project",
    "datacamp projects are scheduled",
    "current-week datacamp projects",
    "duckdb practice is scheduled",
    "available on ",
    "available during ",
    "reserved for ",
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (str(table),)
    ).fetchone() is not None


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


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PROMOTION_TABLE} (
            promotion_date TEXT NOT NULL,
            task_id INTEGER NOT NULL,
            original_date TEXT NOT NULL,
            sprint_week INTEGER NOT NULL,
            promoted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (promotion_date, task_id)
        )
        """
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{PROMOTION_TABLE}_date "
        f"ON {PROMOTION_TABLE}(promotion_date)"
    )
    conn.commit()


def week_bounds(conn: sqlite3.Connection, week: int) -> tuple[date, date]:
    week = max(1, int(week))
    row = None
    if _table_exists(conn, "program_state"):
        row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
    try:
        start = date.fromisoformat(str(_row_value(row, "start_date", 0, "")))
    except (TypeError, ValueError):
        today = date.today()
        start = today - timedelta(days=today.weekday())
    week_start = start + timedelta(days=(week - 1) * 7)
    return week_start, week_start + timedelta(days=6)


def _metadata_date(conn: sqlite3.Connection, task_id: int) -> date | None:
    if not _table_exists(conn, "task_metadata"):
        return None
    row = conn.execute(
        "SELECT deferred_until FROM task_metadata WHERE task_id=?", (int(task_id),)
    ).fetchone()
    raw = str(_row_value(row, "deferred_until", 0, "") or "").strip()
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def _datacamp_project(conn: sqlite3.Connection, task_id: int) -> dict[str, Any] | None:
    try:
        from career_app.services import datacamp_projects
        return datacamp_projects.project_for_task(conn, int(task_id))
    except Exception:
        return None


def _duckdb_date(conn: sqlite3.Connection, task: dict[str, Any]) -> date | None:
    try:
        from career_app.services import duckdb_curriculum_policy as policy
        internal = policy._task_internal_id(task)
        if internal is None:
            return None
        return policy.scheduled_date(conn, int(internal))
    except Exception:
        return None


def _known_scheduled_date(
    conn: sqlite3.Connection,
    task: dict[str, Any],
    week_start: date,
    week_end: date,
) -> date | None:
    task_id = _safe_int(task.get("task_id") or task.get("id"), 0)
    project = _datacamp_project(conn, task_id) if task_id else None
    if project is not None:
        role = str(project.get("role") or "primary").casefold()
        weekday = _safe_int(project.get("scheduled_weekday"), 5 if role == "primary" else 6)
        weekday = min(6, max(0, weekday))
        return week_start + timedelta(days=weekday)

    deferred = _metadata_date(conn, task_id) if task_id else None
    if deferred is not None and week_start <= deferred <= week_end:
        return deferred

    duckdb_day = _duckdb_date(conn, task)
    if duckdb_day is not None and week_start <= duckdb_day <= week_end:
        return duckdb_day

    kind = str(task.get("kind") or "").casefold()
    label = str(task.get("label") or "").casefold()
    category = str(task.get("category") or "").casefold()
    if kind in {"weekly_check", "review"} or "retrospective" in label or "knowledge check" in label:
        return week_start + timedelta(days=4)
    if kind == "datacamp_project":
        return week_start + timedelta(days=5)
    if category == "portfolio" and "project" in label:
        return week_start + timedelta(days=5)
    return None


def _timing_only(reason: str) -> bool:
    text = str(reason or "").strip().casefold()
    return bool(text) and text.startswith(_TIMING_REASON_PREFIXES)


def prerequisite_readiness(
    conn: sqlite3.Connection,
    current_week: int,
    task: dict[str, Any],
) -> tuple[bool, str]:
    """Return content/prerequisite readiness while deliberately ignoring its day."""
    if bool(task.get("completed")) or str(task.get("status") or "") == "Completed":
        return True, "Completed."

    task_id = _safe_int(task.get("task_id") or task.get("id"), 0)
    project = _datacamp_project(conn, task_id) if task_id else None
    if project is not None:
        try:
            from career_app.services import datacamp_projects
            ready, reason = datacamp_projects.project_readiness(
                conn, task_id=task_id, today=date.today()
            )
            if ready or _timing_only(str(reason or "")):
                return True, "All project prerequisites are complete."
            return False, str(reason or project.get("prerequisite") or "Complete the prerequisite first.")
        except Exception:
            pass

    try:
        from career_app.services import duckdb_curriculum_policy as duckdb_policy
        internal = duckdb_policy._task_internal_id(task)
    except Exception:
        internal = None
    if internal is not None:
        try:
            from career_app.services import roadmap_mastery
            result = roadmap_mastery.duckdb_readiness(conn, int(internal))
            return bool(result.get("ready")), str(result.get("reason") or "")
        except Exception as exc:
            return False, f"Could not verify DuckDB prerequisites: {exc}"

    try:
        from career_app.services import unified_tasks
        canonical = unified_tasks.task_by_id(conn, int(current_week), task_id) if task_id else None
        if canonical is None:
            canonical = task
        if bool(canonical.get("ready")):
            return True, "All prerequisites are complete."
        reason = str(canonical.get("prerequisite_reason") or "Complete the prerequisite first.")
        if _timing_only(reason):
            return True, "All prerequisites are complete."
        return False, reason
    except Exception as exc:
        return False, f"Could not verify prerequisites: {exc}"


def _enrich_row(
    conn: sqlite3.Connection,
    current_week: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    result = dict(row)
    task_id = _safe_int(result.get("task_id") or result.get("id"), 0)
    try:
        from career_app.services import unified_tasks
        canonical = unified_tasks.task_by_id(conn, int(current_week), task_id) if task_id else None
    except Exception:
        canonical = None
    if canonical:
        merged = dict(canonical)
        merged.update({key: value for key, value in result.items() if value is not None})
        result = merged
    result["task_id"] = task_id
    result["id"] = task_id
    ready, reason = prerequisite_readiness(conn, current_week, result)
    result["prerequisites_ready"] = bool(ready)
    result["prerequisite_reason"] = "" if ready else reason
    return result


def current_sprint_day_groups(
    conn: sqlite3.Connection,
    current_week: int,
) -> list[dict[str, Any]]:
    """Return the current sprint as seven ordered day buckets."""
    ensure_schema(conn)
    from career_app.services import task_workspace

    week_start, week_end = week_bounds(conn, current_week)
    raw_rows = [dict(item) for item in task_workspace.current_sprint_items(conn, current_week)]
    rows = [_enrich_row(conn, current_week, row) for row in raw_rows]

    known: dict[int, date] = {}
    unscheduled: list[dict[str, Any]] = []
    for row in rows:
        scheduled = _known_scheduled_date(conn, row, week_start, week_end)
        task_id = _safe_int(row.get("task_id"), 0)
        if scheduled is not None and task_id:
            known[task_id] = scheduled
        else:
            unscheduled.append(row)

    # Stable fallback for legacy tasks without explicit dates. Learning work is
    # spread Monday-Friday in roadmap order; explicit project/review dates above
    # are never overwritten.
    unscheduled.sort(
        key=lambda item: (
            _safe_int(item.get("sort_order"), 0),
            _safe_int(item.get("task_id"), 0),
        )
    )
    weekday_loads = [0, 0, 0, 0, 0]
    for row in unscheduled:
        task_id = _safe_int(row.get("task_id"), 0)
        if not task_id:
            continue
        weekday = min(range(5), key=lambda index: (weekday_loads[index], index))
        known[task_id] = week_start + timedelta(days=weekday)
        weekday_loads[weekday] += 1

    promoted = {
        int(_row_value(row, "task_id", 0, 0))
        for row in conn.execute(
            f"SELECT task_id FROM {PROMOTION_TABLE} WHERE promotion_date=?",
            (date.today().isoformat(),),
        ).fetchall()
    }

    groups: list[dict[str, Any]] = []
    for offset in range(7):
        scheduled = week_start + timedelta(days=offset)
        day_rows = []
        for row in rows:
            task_id = _safe_int(row.get("task_id"), 0)
            if known.get(task_id) != scheduled:
                continue
            item = dict(row)
            item["scheduled_date"] = scheduled.isoformat()
            item["scheduled_day"] = scheduled.strftime("%A")
            item["promoted_today"] = task_id in promoted
            day_rows.append(item)
        day_rows.sort(
            key=lambda item: (
                bool(item.get("completed")),
                _safe_int(item.get("sort_order"), 0),
                _safe_int(item.get("task_id"), 0),
            )
        )
        incomplete = [item for item in day_rows if not bool(item.get("completed"))]
        blockers = [item for item in incomplete if not bool(item.get("prerequisites_ready"))]
        groups.append(
            {
                "date": scheduled.isoformat(),
                "day": scheduled.strftime("%A"),
                "label": scheduled.strftime("%A, %B %d"),
                "is_today": scheduled == date.today(),
                "tasks": day_rows,
                "incomplete_count": len(incomplete),
                "blocked_count": len(blockers),
                "all_prerequisites_ready": bool(incomplete) and not blockers,
                "all_promoted": bool(incomplete) and all(bool(item.get("promoted_today")) for item in incomplete),
            }
        )
    return groups


def cleanup_expired_promotions(conn: sqlite3.Connection, today: date | None = None) -> int:
    ensure_schema(conn)
    today = today or date.today()
    cursor = conn.execute(
        f"DELETE FROM {PROMOTION_TABLE} WHERE promotion_date<>?",
        (today.isoformat(),),
    )
    conn.commit()
    return int(cursor.rowcount or 0)


def promote_day(
    conn: sqlite3.Connection,
    current_week: int,
    scheduled_date: str | date,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    ensure_schema(conn)
    today = today or date.today()
    target = scheduled_date if isinstance(scheduled_date, date) else date.fromisoformat(str(scheduled_date))
    week_start, week_end = week_bounds(conn, current_week)
    if target < week_start or target > week_end:
        return {"ok": False, "added": 0, "reason": "That day is outside the current sprint."}
    if target == today:
        return {"ok": False, "added": 0, "reason": "Those tasks are already scheduled for today."}

    group = next(
        (item for item in current_sprint_day_groups(conn, current_week) if item["date"] == target.isoformat()),
        None,
    )
    if group is None:
        return {"ok": False, "added": 0, "reason": "That sprint day could not be found."}
    incomplete = [item for item in group["tasks"] if not bool(item.get("completed")) and _safe_int(item.get("task_id"), 0)]
    if not incomplete:
        return {"ok": False, "added": 0, "reason": "Every task assigned to that day is already complete."}
    blockers = [item for item in incomplete if not bool(item.get("prerequisites_ready"))]
    if blockers:
        details = [
            f"{item.get('label') or 'Task'} — {item.get('prerequisite_reason') or 'Complete its prerequisite first.'}"
            for item in blockers
        ]
        return {
            "ok": False,
            "added": 0,
            "reason": "All incomplete tasks for that day must have finished prerequisites.",
            "blockers": details,
        }

    added = 0
    for item in incomplete:
        task_id = _safe_int(item.get("task_id"), 0)
        cursor = conn.execute(
            f"""
            INSERT OR IGNORE INTO {PROMOTION_TABLE}
                (promotion_date,task_id,original_date,sprint_week,promoted_at)
            VALUES(?,?,?,?,?)
            """,
            (
                today.isoformat(),
                task_id,
                target.isoformat(),
                int(current_week),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        added += int(cursor.rowcount or 0)
    conn.commit()
    return {
        "ok": True,
        "added": added,
        "day": target.strftime("%A"),
        "original_date": target.isoformat(),
        "reason": (
            f"Added {added} task{'s' if added != 1 else ''} from {target.strftime('%A')} to Today’s Focus. "
            "The temporary placement expires at midnight."
        ),
    }


def promotion_summary(
    conn: sqlite3.Connection,
    *,
    today: date | None = None,
) -> dict[str, int]:
    ensure_schema(conn)
    today = today or date.today()
    cleanup_expired_promotions(conn, today)
    if not _table_exists(conn, "sprint_tasks"):
        return {"total": 0, "completed": 0, "minutes": 0}
    has_metadata = _table_exists(conn, "task_metadata")
    if has_metadata:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN COALESCE(s.completed,0)=1 THEN 1 ELSE 0 END) AS completed,
                   COALESCE(SUM(COALESCE(m.estimated_minutes,30)),0) AS minutes
            FROM {PROMOTION_TABLE} p
            JOIN sprint_tasks s ON s.id=p.task_id
            LEFT JOIN task_metadata m ON m.task_id=s.id
            WHERE p.promotion_date=?
            """,
            (today.isoformat(),),
        ).fetchone()
    else:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN COALESCE(s.completed,0)=1 THEN 1 ELSE 0 END) AS completed,
                   COUNT(*) * 30 AS minutes
            FROM {PROMOTION_TABLE} p
            JOIN sprint_tasks s ON s.id=p.task_id
            WHERE p.promotion_date=?
            """,
            (today.isoformat(),),
        ).fetchone()
    return {
        "total": _safe_int(_row_value(row, "total", 0, 0), 0),
        "completed": _safe_int(_row_value(row, "completed", 1, 0), 0),
        "minutes": _safe_int(_row_value(row, "minutes", 2, 0), 0),
    }


def promoted_tasks(
    conn: sqlite3.Connection,
    current_week: int,
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    ensure_schema(conn)
    today = today or date.today()
    cleanup_expired_promotions(conn, today)
    rows = conn.execute(
        f"""
        SELECT task_id,original_date
        FROM {PROMOTION_TABLE}
        WHERE promotion_date=?
        ORDER BY promoted_at,task_id
        """,
        (today.isoformat(),),
    ).fetchall()
    result: list[dict[str, Any]] = []
    try:
        from career_app.services import unified_tasks
    except Exception:
        return result
    for row in rows:
        task_id = _safe_int(_row_value(row, "task_id", 0, 0), 0)
        task = unified_tasks.task_by_id(conn, int(current_week), task_id)
        if task is None or bool(task.get("completed")):
            continue
        ready, reason = prerequisite_readiness(conn, current_week, task)
        if not ready:
            continue
        item = dict(task)
        original = str(_row_value(row, "original_date", 1, ""))
        try:
            day_name = date.fromisoformat(original).strftime("%A")
        except ValueError:
            day_name = "another day"
        item.update(
            {
                "ready": True,
                "prerequisite_state": "Ready",
                "prerequisite_reason": None,
                "focus_kind": "promoted",
                "is_promoted": True,
                "original_scheduled_date": original,
                "detail": f"Added from {day_name} • Returns there at midnight",
            }
        )
        result.append(item)
    return result
