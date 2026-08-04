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

    kind = str(task.get("kind") or "").casefold()
    deferred = _metadata_date(conn, task_id) if task_id else None
    # DataCamp chapters and weekend projects own exact calendar dates. Practice
    # tasks use their chapter date as an earliest boundary instead, allowing the
    # load balancer to place them later in the week when that produces a better
    # day-by-day plan.
    if (
        deferred is not None
        and week_start <= deferred <= week_end
        and kind in {"datacamp_chapter", "datacamp_project", "review", "weekly_check"}
    ):
        return deferred

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


def _program_start(conn: sqlite3.Connection) -> date:
    row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
    try:
        return date.fromisoformat(str(_row_value(row, "start_date", 0, "")))
    except (TypeError, ValueError):
        today = date.today()
        return today - timedelta(days=today.weekday())


def _chapter_date(conn: sqlite3.Connection, chapter_key: str) -> date | None:
    try:
        from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
        chapter = CHAPTER_BY_KEY.get(str(chapter_key))
        return chapter.scheduled_date(_program_start(conn)) if chapter is not None else None
    except Exception:
        return None


def _sql_problem_title(task: dict[str, Any]) -> str | None:
    haystack = " ".join(
        str(task.get(key) or "")
        for key in ("label", "target_key", "managed_key")
    ).casefold()
    try:
        from career_app.data.roadmap import SQL_COMPANION
        for entry in SQL_COMPANION:
            title = str(entry[0])
            if title.casefold() in haystack:
                return title
    except Exception:
        pass
    return None


def _task_semantic_key(task: dict[str, Any]) -> str:
    kind = str(task.get("kind") or "").casefold()
    if kind == "datacamp_chapter":
        try:
            from career_app.services import datacamp
            chapter = datacamp.chapter_for_task(task)
            if chapter is not None:
                return f"datacamp:{chapter.key}"
        except Exception:
            pass
    if kind == "duckdb":
        try:
            from career_app.services import duckdb_curriculum_policy as policy
            internal = policy._task_internal_id(task)
            if internal is not None:
                return f"duckdb:{int(internal)}"
        except Exception:
            pass
    if kind == "python_exercise":
        try:
            from career_app.data.python_exercises import exercise_number_for_label
            number = exercise_number_for_label(str(task.get("label") or ""))
            if number is not None:
                return f"python:{int(number)}"
        except Exception:
            pass
    if kind == "interview_problem":
        title = _sql_problem_title(task)
        if title:
            return "sql_problem:" + title.casefold()
    if kind == "weekly_check":
        return f"weekly_check:{_safe_int(task.get('week'), 0)}"
    return f"task:{_safe_int(task.get('task_id') or task.get('id'), 0)}"


def _prior_semantic_keys(task: dict[str, Any]) -> tuple[str, ...]:
    kind = str(task.get("kind") or "").casefold()
    if kind == "duckdb":
        try:
            from career_app.services import duckdb_curriculum_policy as policy
            internal = policy._task_internal_id(task)
            return tuple(
                f"duckdb:{int(value)}"
                for value in policy.PRIOR_EXERCISES_BY_ID.get(int(internal), ())
            ) if internal is not None else ()
        except Exception:
            return ()
    if kind == "python_exercise":
        try:
            from career_app.data.python_exercises import (
                PYTHON_EXERCISES,
                exercise_number_for_label,
            )
            number = exercise_number_for_label(str(task.get("label") or ""))
            return tuple(
                f"python:{int(value)}"
                for value in PYTHON_EXERCISES[int(number)].get("prior_exercises", ())
            ) if number is not None else ()
        except Exception:
            return ()
    if kind == "review":
        return (f"weekly_check:{_safe_int(task.get('week'), 0)}",)
    return ()


def _dependency_earliest_date(
    conn: sqlite3.Connection,
    task: dict[str, Any],
    week_start: date,
) -> date:
    """Return the earliest day on which the task may be listed.

    The date is based on the final assigned DataCamp chapter required by the
    task. Direct exercise prerequisites are applied later using the actual date
    chosen for the preceding exercise.
    """
    kind = str(task.get("kind") or "").casefold()
    chapter_keys: tuple[str, ...] = ()
    try:
        if kind == "duckdb":
            from career_app.services import duckdb_curriculum_policy as policy
            internal = policy._task_internal_id(task)
            if internal is not None:
                chapter_keys = (policy.TERMINAL_CHAPTER_BY_ID[int(internal)],)
        elif kind == "python_exercise":
            from career_app.data.python_exercises import (
                PYTHON_EXERCISES,
                exercise_number_for_label,
            )
            number = exercise_number_for_label(str(task.get("label") or ""))
            if number is not None:
                chapter_keys = (str(PYTHON_EXERCISES[int(number)]["terminal_chapter"]),)
        elif kind == "interview_problem":
            from career_app.services import content_gates, tracks
            title = _sql_problem_title(task)
            if title:
                groups = tracks.SQL_PROBLEM_REQUIREMENTS.get(title, {})
                required = set(groups.get("all_of", ())) | set(groups.get("any_of", ()))
                chapter_keys = content_gates.requirements_for_sql_problem(
                    required,
                    roadmap_week=tracks.SQL_PROBLEM_WEEK.get(title),
                )
        elif kind == "applied_lab":
            from career_app.data.applied_exercises import exercise_number_for_label
            from career_app.services import content_gates
            number = exercise_number_for_label(str(task.get("label") or ""))
            if number is not None:
                chapter_keys = content_gates.requirements_for_applied_lab(int(number))
    except Exception:
        chapter_keys = ()

    dates = [value for key in chapter_keys if (value := _chapter_date(conn, key)) is not None]
    return max([week_start, *dates])


def _sequence_rank(task: dict[str, Any]) -> int:
    kind = str(task.get("kind") or "").casefold()
    if kind == "datacamp_chapter":
        try:
            from career_app.data.datacamp_curriculum import DATACAMP_CHAPTERS
            from career_app.services import datacamp
            chapter = datacamp.chapter_for_task(task)
            if chapter is not None:
                return next(
                    index for index, value in enumerate(DATACAMP_CHAPTERS)
                    if value.key == chapter.key
                )
        except Exception:
            pass
    if kind == "duckdb":
        try:
            from career_app.services import duckdb_curriculum_policy as policy
            internal = policy._task_internal_id(task)
            if internal is not None:
                return 1000 + int(policy._DISPLAY_BY_ID[int(internal)])
        except Exception:
            pass
    if kind == "interview_problem":
        title = _sql_problem_title(task)
        try:
            from career_app.data.roadmap import SQL_COMPANION
            if title:
                return 2000 + next(
                    index for index, value in enumerate(SQL_COMPANION)
                    if str(value[0]) == title
                )
        except Exception:
            pass
    if kind == "python_exercise":
        try:
            from career_app.data.python_exercises import exercise_number_for_label
            number = exercise_number_for_label(str(task.get("label") or ""))
            if number is not None:
                return 3000 + int(number)
        except Exception:
            pass
    if kind == "applied_lab":
        try:
            from career_app.data.applied_exercises import exercise_number_for_label
            number = exercise_number_for_label(str(task.get("label") or ""))
            if number is not None:
                return 4000 + int(number)
        except Exception:
            pass
    return 9000 + _safe_int(task.get("sort_order"), 0)


def _kind_priority(task: dict[str, Any]) -> int:
    return {
        "google": 0,
        "datacamp_chapter": 1,
        "duckdb": 10,
        "interview_problem": 11,
        "sql_practice": 12,
        "python_exercise": 13,
        "applied_lab": 20,
        "portfolio_preparation": 30,
        "portfolio_execution": 31,
        "weekly_check": 40,
        "review": 41,
        "career_readiness": 50,
        "general": 60,
    }.get(str(task.get("kind") or "").casefold(), 60)


def task_display_sort(task: dict[str, Any], current_week: int) -> tuple[Any, ...]:
    """Shared ready-first ordering for Focus, Next Tasks, and sprint days."""
    ready = bool(task.get("ready", task.get("prerequisites_ready", False)))
    return (
        0 if ready else 1,
        _kind_priority(task),
        _sequence_rank(task),
        _safe_int(task.get("week"), current_week),
        _safe_int(task.get("sort_order"), 0),
        _safe_int(task.get("task_id") or task.get("id"), 0),
    )


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
    canonical_by_id: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Merge one sprint row with a precomputed canonical task.

    Earlier builds called ``unified_tasks.task_by_id`` for every row. That
    function rebuilds the full task pool, turning one dialog click into
    thousands of database queries. The caller now supplies a one-pass lookup.
    """
    result = dict(row)
    task_id = _safe_int(result.get("task_id") or result.get("id"), 0)
    canonical = (canonical_by_id or {}).get(task_id) if task_id else None
    if canonical:
        merged = dict(canonical)
        merged.update({key: value for key, value in result.items() if value is not None})
        result = merged
    result["task_id"] = task_id
    result["id"] = task_id

    if bool(result.get("completed")) or str(result.get("status") or "") == "Completed":
        ready, reason = True, "Completed."
    elif canonical is not None:
        reason = str(canonical.get("prerequisite_reason") or "")
        ready = bool(canonical.get("ready")) or _timing_only(reason)
        if ready:
            reason = "All prerequisites are complete."
    else:
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
    from career_app.services import unified_tasks

    canonical_tasks = list(unified_tasks.all_tasks(conn, current_week))
    canonical_by_id = {
        _safe_int(task.get("id") or task.get("task_id"), 0): task
        for task in canonical_tasks
        if _safe_int(task.get("id") or task.get("task_id"), 0)
    }
    raw_rows = [
        dict(item)
        for item in task_workspace.current_sprint_items(
            conn, current_week, canonical_tasks=canonical_tasks
        )
    ]
    rows = [
        _enrich_row(conn, current_week, row, canonical_by_id)
        for row in raw_rows
    ]

    known: dict[int, date] = {}
    scheduled_by_key: dict[str, date] = {}
    unscheduled: list[dict[str, Any]] = []
    weekday_minutes = [0, 0, 0, 0, 0]
    weekday_counts = [0, 0, 0, 0, 0]

    for row in rows:
        scheduled = _known_scheduled_date(conn, row, week_start, week_end)
        task_id = _safe_int(row.get("task_id"), 0)
        if scheduled is not None and task_id:
            known[task_id] = scheduled
            scheduled_by_key[_task_semantic_key(row)] = scheduled
            offset = (scheduled - week_start).days
            if 0 <= offset <= 4:
                weekday_minutes[offset] += max(5, _safe_int(row.get("estimated_minutes"), 30))
                weekday_counts[offset] += 1
        else:
            unscheduled.append(row)

    # Schedule prerequisite-dependent practice only after the content that
    # unlocks it. Within the allowed date range, choose the lightest remaining
    # weekday so the roadmap is distributed by estimated effort rather than by
    # an unrelated task ID round-robin.
    unscheduled.sort(
        key=lambda item: (
            _dependency_earliest_date(conn, item, week_start),
            _sequence_rank(item),
            _kind_priority(item),
            _safe_int(item.get("sort_order"), 0),
            _safe_int(item.get("task_id"), 0),
        )
    )
    for row in unscheduled:
        task_id = _safe_int(row.get("task_id"), 0)
        if not task_id:
            continue
        kind = str(row.get("kind") or "").casefold()
        earliest = _dependency_earliest_date(conn, row, week_start)
        for dependency_key in _prior_semantic_keys(row):
            dependency_date = scheduled_by_key.get(dependency_key)
            if dependency_date is not None:
                earliest = max(earliest, dependency_date)

        if kind == "google":
            selected_day = 0
        else:
            earliest_offset = max(0, (earliest - week_start).days)
            candidate_days = list(range(min(4, earliest_offset), 5))
            task_minutes = max(5, _safe_int(row.get("estimated_minutes"), 30))
            # Keep a normal weekday near three hours of assigned work. Moving a
            # task one day later carries roughly one chapter of delay cost, so
            # the planner fills the earliest reasonable day instead of blindly
            # pushing every flexible practice item onto Friday.
            daily_target_minutes = 180
            selected_day = min(
                candidate_days,
                key=lambda index: (
                    max(
                        0,
                        weekday_minutes[index] + task_minutes - daily_target_minutes,
                    )
                    * 100,
                    weekday_minutes[index]
                    + task_minutes
                    + (index - earliest_offset) * 45,
                    weekday_counts[index],
                    index,
                ),
            )

        scheduled = week_start + timedelta(days=selected_day)
        known[task_id] = scheduled
        scheduled_by_key[_task_semantic_key(row)] = scheduled
        weekday_minutes[selected_day] += max(5, _safe_int(row.get("estimated_minutes"), 30))
        weekday_counts[selected_day] += 1

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
                task_display_sort(item, int(current_week)),
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
