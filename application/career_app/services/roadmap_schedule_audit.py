from __future__ import annotations

"""Persistent roadmap schedule cleanup and workload audit.

This service deliberately sits *after* the existing sprint-day planner.  The
planner remains responsible for discovering the task set and enforcing calendar
locks; this module only repairs stale persisted rows and applies a small set of
audited weekday assignments where the current curriculum is otherwise badly
unbalanced.

Historical completed work is never rescheduled or deleted.
"""

from datetime import date, timedelta
import sqlite3
from typing import Any

AUDIT_SOURCE = "roadmap_audit_v104621"

# Week 5 currently contains 26 required weekday rows.  This distribution keeps
# every content gate and direct interview-problem predecessor on the same day or
# earlier while reducing the Friday pileup from 9 tasks / 260 minutes to
# 6 tasks / 165 minutes.
WEEK_5_WEEKDAY_BY_MANAGED_KEY: dict[str, int] = {
    # DataCamp: 2 / 2 / 2 / 1 / 0 chapters Monday-Friday.
    "datacamp:w05_window_sql_01": 0,
    "datacamp:w05_window_sql_02": 0,
    "datacamp:w05_window_sql_03": 1,
    "datacamp:w05_window_sql_04": 1,
    "datacamp:w05_functions_sql_01": 2,
    "datacamp:w05_functions_sql_02": 2,
    "datacamp:w05_functions_sql_03": 3,

    # SQL Challenges 15-24.  Internal exercise IDs are stable even when the
    # learner-facing challenge number differs.
    "roadmap_v1026:duckdb:25": 0,  # Challenge 15
    "roadmap_v1026:duckdb:26": 0,  # Challenge 16 (after 15)
    "roadmap_v1026:duckdb:15": 1,  # Challenge 17
    "roadmap_v1026:duckdb:11": 1,  # Challenge 18
    "roadmap_v1026:duckdb:27": 2,  # Challenge 19
    "roadmap_v1026:duckdb:28": 2,  # Challenge 20 (after Functions Ch1)
    "roadmap_v1026:duckdb:14": 3,  # Challenge 21 (after Functions Ch2)
    "roadmap_v1026:duckdb:4": 3,   # Challenge 22 (after 21)
    "roadmap_v1026:duckdb:3": 4,   # Challenge 23 (after Functions Ch3)
    "roadmap_v1026:duckdb:17": 4,  # Challenge 24 (after Functions Ch3)

    # SQL interview chain.  Same-day successors remain locked until their
    # direct predecessor is completed, so the sequence is not bypassed.
    "roadmap_v1026:sql:Second Highest Salary": 1,
    "roadmap_v1026:sql:User's Third Transaction": 2,
    "roadmap_v1026:sql:Top Three Salaries": 3,
    "roadmap_v1026:sql:Odd and Even Measurements": 3,
    "roadmap_v1026:sql:Tweets' Rolling Averages": 3,
    "roadmap_v1026:sql:User Shopping Sprees": 4,
    "roadmap_v1026:sql:Second Day Confirmation": 4,

    "weekly_check:5": 4,
    "weekly_retrospective_05": 4,
}


# Explicit schedule dependencies used as a safety net for audited weekday
# overrides. A dependent may share a day with its prerequisite (it stays locked
# until completion), but it may never be assigned to an earlier day.
WEEK_5_SCHEDULE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "datacamp:w05_window_sql_02": ("datacamp:w05_window_sql_01",),
    "datacamp:w05_window_sql_03": ("datacamp:w05_window_sql_02",),
    "datacamp:w05_window_sql_04": ("datacamp:w05_window_sql_03",),
    "datacamp:w05_functions_sql_02": ("datacamp:w05_functions_sql_01",),
    "datacamp:w05_functions_sql_03": ("datacamp:w05_functions_sql_02",),
    "roadmap_v1026:duckdb:25": ("datacamp:w05_window_sql_01",),
    "roadmap_v1026:duckdb:26": (
        "roadmap_v1026:duckdb:25",
        "datacamp:w05_window_sql_02",
    ),
    "roadmap_v1026:duckdb:15": ("datacamp:w05_window_sql_03",),
    "roadmap_v1026:duckdb:11": ("datacamp:w05_window_sql_03",),
    "roadmap_v1026:duckdb:27": ("datacamp:w05_window_sql_04",),
    "roadmap_v1026:duckdb:28": ("datacamp:w05_functions_sql_01",),
    "roadmap_v1026:duckdb:14": ("datacamp:w05_functions_sql_02",),
    "roadmap_v1026:duckdb:4": (
        "roadmap_v1026:duckdb:14",
        "datacamp:w05_functions_sql_02",
    ),
    "roadmap_v1026:duckdb:3": ("datacamp:w05_functions_sql_03",),
    "roadmap_v1026:duckdb:17": ("datacamp:w05_functions_sql_03",),
    "roadmap_v1026:sql:Second Highest Salary": (
        "datacamp:w05_window_sql_03",
    ),
    "roadmap_v1026:sql:User's Third Transaction": (
        "roadmap_v1026:sql:Second Highest Salary",
        "datacamp:w05_window_sql_03",
    ),
    "roadmap_v1026:sql:Top Three Salaries": (
        "roadmap_v1026:sql:User's Third Transaction",
    ),
    "roadmap_v1026:sql:Odd and Even Measurements": (
        "roadmap_v1026:sql:Top Three Salaries",
        "datacamp:w05_functions_sql_02",
    ),
    "roadmap_v1026:sql:Tweets' Rolling Averages": (
        "roadmap_v1026:sql:Odd and Even Measurements",
    ),
    "roadmap_v1026:sql:User Shopping Sprees": (
        "roadmap_v1026:sql:Tweets' Rolling Averages",
        "datacamp:w05_functions_sql_02",
    ),
    "roadmap_v1026:sql:Second Day Confirmation": (
        "roadmap_v1026:sql:User Shopping Sprees",
        "datacamp:w05_functions_sql_02",
    ),
}

# Week 7 already has a sensible 5/5/4/4/4 DataCamp chapter distribution, but
# the Friday knowledge check + retrospective turn Friday into six rows.  Moving
# the final visualization chapter to Thursday preserves course order and yields
# 5/5/4/5/5 weekday rows.
WEEK_7_WEEKDAY_BY_MANAGED_KEY: dict[str, int] = {
    "datacamp:w07_visual_powerbi_04": 3,
    "weekly_check:7": 4,
    "weekly_retrospective_07": 4,
}

AUDITED_WEEKDAY_OVERRIDES: dict[int, dict[str, int]] = {
    5: WEEK_5_WEEKDAY_BY_MANAGED_KEY,
    7: WEEK_7_WEEKDAY_BY_MANAGED_KEY,
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _program_start(conn: sqlite3.Connection) -> date | None:
    try:
        row = conn.execute(
            "SELECT start_date FROM program_state WHERE id=1"
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    try:
        return date.fromisoformat(str(row[0]))
    except (TypeError, ValueError):
        return None


def _week_start(conn: sqlite3.Connection, week: int) -> date | None:
    start = _program_start(conn)
    if start is None:
        return None
    # The program start is expected to be Monday.  Keep the persisted program
    # anchor authoritative instead of deriving dates from the machine clock.
    return start + timedelta(days=(max(1, int(week)) - 1) * 7)


def _ensure_schedule_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS task_sprint_schedule (
               task_id INTEGER NOT NULL,
               sprint_week INTEGER NOT NULL,
               scheduled_date TEXT NOT NULL,
               source TEXT NOT NULL DEFAULT 'planner',
               updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
               PRIMARY KEY(task_id,sprint_week)
           )"""
    )


def cleanup_orphan_schedule_rows(conn: sqlite3.Connection) -> int:
    """Delete schedule rows whose sprint task was retired/archived already."""
    if "task_sprint_schedule" not in _tables(conn):
        return 0
    cursor = conn.execute(
        """DELETE FROM task_sprint_schedule
           WHERE task_id NOT IN (SELECT id FROM sprint_tasks)"""
    )
    return max(0, _safe_int(cursor.rowcount, 0))


def _set_task_date(
    conn: sqlite3.Connection,
    *,
    task_id: int,
    week: int,
    scheduled: date,
    managed_key: str,
) -> bool:
    scheduled_text = scheduled.isoformat()
    current = conn.execute(
        """SELECT scheduled_date,source
           FROM task_sprint_schedule
           WHERE task_id=? AND sprint_week=?""",
        (int(task_id), int(week)),
    ).fetchone()
    changed = (
        current is None
        or str(current[0]) != scheduled_text
        or str(current[1]) != AUDIT_SOURCE
    )

    conn.execute(
        """INSERT INTO task_sprint_schedule
           (task_id,sprint_week,scheduled_date,source,updated_at)
           VALUES(?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(task_id,sprint_week) DO UPDATE SET
               scheduled_date=excluded.scheduled_date,
               source=excluded.source,
               updated_at=CURRENT_TIMESTAMP""",
        (int(task_id), int(week), scheduled_text, AUDIT_SOURCE),
    )
    conn.execute(
        """UPDATE task_metadata
           SET deferred_until=?
           WHERE task_id=?""",
        (scheduled_text, int(task_id)),
    )

    if managed_key.startswith("datacamp:"):
        chapter_key = managed_key.split(":", 1)[1]
        try:
            conn.execute(
                """UPDATE datacamp_chapter_progress
                   SET scheduled_date=?,updated_at=CURRENT_TIMESTAMP
                   WHERE chapter_key=?""",
                (scheduled_text, chapter_key),
            )
        except sqlite3.Error:
            pass
    return changed


def _schedule_friday_reviews(
    conn: sqlite3.Connection,
    *,
    current_week: int,
) -> int:
    """Keep checks/retrospectives on Friday for every current/future week."""
    changed = 0
    rows = conn.execute(
        """SELECT s.id,s.week,s.completed,m.managed_key
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.week>=?
             AND s.completed=0
             AND (
                 m.managed_key LIKE 'weekly_check:%'
                 OR m.managed_key LIKE 'weekly_retrospective_%'
             )""",
        (max(1, int(current_week)),),
    ).fetchall()
    for row in rows:
        week = int(row["week"])
        week_start = _week_start(conn, week)
        if week_start is None:
            continue
        if _set_task_date(
            conn,
            task_id=int(row["id"]),
            week=week,
            scheduled=week_start + timedelta(days=4),
            managed_key=str(row["managed_key"] or ""),
        ):
            changed += 1
    return changed


def reconcile_supplemental_capacity(
    conn: sqlite3.Connection,
    *,
    current_week: int,
) -> int:
    """Return overloaded supplemental DataCamp projects to reserve practice.

    The existing project contract only selects a supplemental project when the
    required week plus its primary project remains below the 18-hour (1,080
    minute) planned-work target.  Preserve historical completed projects, but
    repair a future/current selection that violates that rule.
    """
    if "datacamp_project_tasks" not in _tables(conn):
        return 0

    changed = 0
    supplemental_rows = conn.execute(
        """SELECT d.project_key,d.task_id,d.project_week,d.capacity_selected,
                  m.status,m.prerequisite_state,m.prerequisite_reason
           FROM datacamp_project_tasks d
           JOIN sprint_tasks s ON s.id=d.task_id
           JOIN task_metadata m ON m.task_id=s.id
           WHERE d.role='supplemental'
             AND d.project_week>=?
             AND s.completed=0""",
        (max(1, int(current_week)),),
    ).fetchall()

    for row in supplemental_rows:
        week = int(row["project_week"])
        planned_without_supplemental = conn.execute(
            """SELECT COALESCE(SUM(m.estimated_minutes),0)
               FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               LEFT JOIN datacamp_project_tasks d ON d.task_id=s.id
               WHERE s.week=?
                 AND COALESCE(d.role,'')<>'supplemental'""",
            (week,),
        ).fetchone()[0]
        if _safe_int(planned_without_supplemental, 0) < 1080:
            continue
        if bool(row["capacity_selected"]):
            conn.execute(
                """UPDATE datacamp_project_tasks
                   SET capacity_selected=0,updated_at=CURRENT_TIMESTAMP
                   WHERE project_key=?""",
                (str(row["project_key"]),),
            )
            changed += 1

        # Keep the task record for the Optional Practice surface, but make its
        # reserve status explicit for any service that reads task metadata.
        reason = (
            f"Reserve optional practice — required Week {week} work already "
            "reaches the 18-hour workload target."
        )
        if (
            str(row["status"] or "") != "Blocked"
            or str(row["prerequisite_state"] or "") != "Blocked"
            or str(row["prerequisite_reason"] or "") != reason
        ):
            conn.execute(
                """UPDATE task_metadata
                   SET status='Blocked',
                       prerequisite_state='Blocked',
                       prerequisite_reason=?
                   WHERE task_id=?""",
                (reason, int(row["task_id"])),
            )
            changed += 1
    return changed



def _dependency_safe_mapping(
    mapping: dict[str, int],
    dependencies: dict[str, tuple[str, ...]],
) -> dict[str, int]:
    """Clamp audited assignments so no task precedes a scheduled prerequisite."""
    resolved = {str(key): int(value) for key, value in mapping.items()}
    # Weekday values only move later, so this converges quickly even for chains.
    for _ in range(max(1, len(resolved))):
        changed = False
        for task_key, prerequisite_keys in dependencies.items():
            if task_key not in resolved:
                continue
            prerequisite_days = [
                resolved[key]
                for key in prerequisite_keys
                if key in resolved
            ]
            if not prerequisite_days:
                continue
            minimum_day = max(prerequisite_days)
            if resolved[task_key] < minimum_day:
                resolved[task_key] = minimum_day
                changed = True
        if not changed:
            break
    return resolved


def apply_audited_weekdays(
    conn: sqlite3.Connection,
    *,
    current_week: int,
) -> int:
    """Apply only current/future audited dates; historical work is untouched."""
    changed = 0
    for week, mapping in AUDITED_WEEKDAY_OVERRIDES.items():
        if int(week) < int(current_week):
            continue
        if int(week) == 5:
            mapping = _dependency_safe_mapping(
                mapping,
                WEEK_5_SCHEDULE_DEPENDENCIES,
            )
        week_start = _week_start(conn, int(week))
        if week_start is None:
            continue
        placeholders = ",".join("?" for _ in mapping)
        rows = conn.execute(
            f"""SELECT s.id,s.week,s.completed,m.managed_key
                FROM sprint_tasks s
                JOIN task_metadata m ON m.task_id=s.id
                WHERE s.week=?
                  AND s.completed=0
                  AND m.managed_key IN ({placeholders})""",
            (int(week), *mapping.keys()),
        ).fetchall()
        for row in rows:
            managed_key = str(row["managed_key"] or "")
            weekday = mapping.get(managed_key)
            if weekday is None:
                continue
            if _set_task_date(
                conn,
                task_id=int(row["id"]),
                week=int(week),
                scheduled=week_start + timedelta(days=int(weekday)),
                managed_key=managed_key,
            ):
                changed += 1
    return changed


def reconcile(conn: sqlite3.Connection, current_week: int) -> dict[str, int] | bool:
    """Clean stale persisted rows and apply audited current/future weekdays.

    The return value is truthy when anything changed so callers can rebuild a
    day-group snapshot immediately.
    """
    try:
        _ensure_schedule_table(conn)
        orphan_rows_removed = cleanup_orphan_schedule_rows(conn)
        audited_dates_updated = apply_audited_weekdays(
            conn,
            current_week=max(1, int(current_week)),
        )
        review_dates_updated = _schedule_friday_reviews(
            conn,
            current_week=max(1, int(current_week)),
        )
        supplemental_projects_reserved = reconcile_supplemental_capacity(
            conn,
            current_week=max(1, int(current_week)),
        )
        total = (
            orphan_rows_removed
            + audited_dates_updated
            + review_dates_updated
            + supplemental_projects_reserved
        )
        if total:
            conn.commit()
        return {
            "orphan_schedule_rows_removed": orphan_rows_removed,
            "audited_dates_updated": audited_dates_updated,
            "review_dates_updated": review_dates_updated,
            "supplemental_projects_reserved": supplemental_projects_reserved,
            "changed": total,
        }
    except sqlite3.Error:
        # Scheduling cleanup must never prevent the application from opening.
        return False


def workload_snapshot(conn: sqlite3.Connection) -> dict[int, dict[int, dict[str, int]]]:
    """Return scheduled task counts/minutes by sprint week and weekday."""
    result: dict[int, dict[int, dict[str, int]]] = {}
    if "task_sprint_schedule" not in _tables(conn):
        return result
    rows = conn.execute(
        """SELECT ts.sprint_week,ts.scheduled_date,
                  COUNT(*) AS task_count,
                  COALESCE(SUM(m.estimated_minutes),0) AS minutes
           FROM task_sprint_schedule ts
           JOIN sprint_tasks s ON s.id=ts.task_id
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=0
           GROUP BY ts.sprint_week,ts.scheduled_date
           ORDER BY ts.sprint_week,ts.scheduled_date"""
    ).fetchall()
    for row in rows:
        try:
            weekday = date.fromisoformat(str(row["scheduled_date"])).weekday()
        except (TypeError, ValueError):
            continue
        week = int(row["sprint_week"])
        result.setdefault(week, {})[weekday] = {
            "task_count": int(row["task_count"]),
            "minutes": int(row["minutes"]),
        }
    return result
