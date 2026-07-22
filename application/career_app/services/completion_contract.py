from __future__ import annotations

"""Fixed-deadline pacing for the 90-day Career Accelerator program.

The adaptive planner may reorder ready work, but it may not move the program end
past Day 90. Weekly quotas are recalculated from the complete remaining workload,
including all imported portfolio projects, so missed work is redistributed across
the days that remain instead of extending the schedule.
"""

from datetime import date, timedelta
import json
import math
import sqlite3
from typing import Any


PROGRAM_DAYS = 90
PROGRAM_WEEKS = 13
SPRINT_WEEKS = 12
DEFAULT_WEEKLY_HOURS = 18.0

KEY_PREFIX = "program_contract."
KEY_START_DATE = KEY_PREFIX + "start_date"
KEY_END_DATE = KEY_PREFIX + "end_date"
KEY_DURATION_DAYS = KEY_PREFIX + "duration_days"
KEY_REQUIRED_WEEKLY_HOURS = KEY_PREFIX + "required_weekly_hours"
KEY_SNAPSHOT = KEY_PREFIX + "snapshot"
KEY_ACADEMY_CATALOG = KEY_PREFIX + "academy_catalog"

GOOGLE_MODULE_COUNTS = {1: 4, 2: 4, 3: 5, 4: 6, 5: 4, 6: 4, 7: 5, 8: 4, 9: 4}
GOOGLE_TOTAL = sum(GOOGLE_MODULE_COUNTS.values())
SQL_INTERVIEW_TOTAL_FALLBACK = 16
DUCKDB_TOTAL = 12
APPLIED_TOTAL = 36

TRACK_MINUTES = {
    "google": 90,
    "sql": 45,
    "portfolio": 120,
    "applied": 45,
    "academy": 30,
}

# The full program is deliberately scoped below the 90-day capacity of a learner
# studying 18 hours each week. Quotas use item counts; hour forecasts use these
# track budgets so large catalogs cannot silently make the plan impossible.
TRACK_BUDGET_MINUTES = {
    "google": 62 * 60,
    "sql": 28 * 60,
    "portfolio": 70 * 60,
    "applied": 26 * 60,
    "academy": 42 * 60,
}
PROGRAM_CAPACITY_MINUTES = round(PROGRAM_DAYS / 7 * DEFAULT_WEEKLY_HOURS * 60)


class CompletionContractError(RuntimeError):
    pass


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
    )


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {str(row[1]) for row in conn.execute(f'PRAGMA table_info("{table}")')}


def _row_value(row: Any, key: str, index: int = 0, default: Any = None) -> Any:
    if row is None:
        return default
    try:
        return row[key]
    except (TypeError, IndexError, KeyError):
        try:
            return row[index]
        except (TypeError, IndexError):
            return default


def _get_setting(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    if not _table_exists(conn, "settings"):
        return default
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    value = _row_value(row, "value", 0, default)
    return default if value is None else str(value)


def _set_settings(conn: sqlite3.Connection, values: dict[str, Any]) -> None:
    if not _table_exists(conn, "settings"):
        return
    conn.executemany(
        """
        INSERT INTO settings(key,value) VALUES(?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        [(key, str(value)) for key, value in values.items()],
    )
    conn.commit()


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _state_int(state: Any, key: str, default: int) -> int:
    try:
        return int(state[key])
    except (TypeError, KeyError, IndexError, ValueError):
        return int(default)


def _state_float(state: Any, key: str, default: float) -> float:
    try:
        return float(state[key])
    except (TypeError, KeyError, IndexError, ValueError):
        return float(default)


def _profile_is_ready(conn: sqlite3.Connection) -> bool:
    return bool(_get_setting(conn, "onboarding.pathway_id"))


def _derive_existing_start(today: date, state: Any) -> date:
    current_week = max(1, min(SPRINT_WEEKS, _state_int(state, "current_week", 1)))
    return today - timedelta(days=(current_week - 1) * 7)


def _program_state_columns(conn: sqlite3.Connection) -> set[str]:
    return _columns(conn, "program_state")


def _set_program_state(conn: sqlite3.Connection, **values: Any) -> None:
    columns = _program_state_columns(conn)
    assignments = [(name, value) for name, value in values.items() if name in columns]
    if not assignments:
        return
    sql = ", ".join(f'"{name}"=?' for name, _ in assignments)
    conn.execute(
        f'UPDATE program_state SET {sql} WHERE id=1',
        tuple(value for _, value in assignments),
    )
    conn.commit()


def clock(conn: sqlite3.Connection, *, today: date | None = None) -> dict[str, Any]:
    current = today or date.today()
    start = _parse_date(_get_setting(conn, KEY_START_DATE))
    end = _parse_date(_get_setting(conn, KEY_END_DATE))
    if start is None or end is None:
        return {
            "active": False,
            "program_day": 1,
            "days_remaining": PROGRAM_DAYS,
            "weeks_remaining": PROGRAM_WEEKS,
            "start_date": None,
            "end_date": None,
            "deadline_passed": False,
        }
    raw_day = (current - start).days + 1
    program_day = max(1, min(PROGRAM_DAYS, raw_day))
    days_remaining = max(0, (end - current).days + 1)
    return {
        "active": True,
        "program_day": program_day,
        "days_remaining": days_remaining,
        "weeks_remaining": max(1, math.ceil(max(1, days_remaining) / 7)),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "deadline_passed": current > end,
    }


def _google_completed(conn: sqlite3.Connection, state: Any) -> int:
    course = max(1, min(max(GOOGLE_MODULE_COUNTS), _state_int(state, "google_course", 1)))
    module = max(1, _state_int(state, "google_module", 1))
    inferred = sum(GOOGLE_MODULE_COUNTS[index] for index in range(1, course))
    inferred += min(module - 1, GOOGLE_MODULE_COUNTS[course])

    event_count = 0
    if _table_exists(conn, "track_events"):
        columns = _columns(conn, "track_events")
        if {"track_key", "event_key"}.issubset(columns):
            row = conn.execute(
                "SELECT COUNT(DISTINCT event_key) FROM track_events WHERE track_key='google'"
            ).fetchone()
            event_count = int(_row_value(row, "COUNT(DISTINCT event_key)", 0, 0) or 0)

    if _table_exists(conn, "track_state"):
        row = conn.execute(
            "SELECT status FROM track_state WHERE track_key='google'"
        ).fetchone()
        if str(_row_value(row, "status", 0, "")) == "Completed":
            return GOOGLE_TOTAL
    return max(0, min(GOOGLE_TOTAL, max(inferred, event_count)))


def _sql_counts(conn: sqlite3.Connection) -> tuple[int, int]:
    interview_total = SQL_INTERVIEW_TOTAL_FALLBACK
    interview_completed = 0
    if _table_exists(conn, "sql_practice"):
        columns = _columns(conn, "sql_practice")
        where = " WHERE platform='DataLemur'" if "platform" in columns else ""
        total_row = conn.execute(f"SELECT COUNT(*) FROM sql_practice{where}").fetchone()
        observed_total = int(_row_value(total_row, "COUNT(*)", 0, 0) or 0)
        interview_total = max(SQL_INTERVIEW_TOTAL_FALLBACK, observed_total)
        if "status" in columns:
            complete_where = (
                " WHERE platform='DataLemur' AND status='Completed'"
                if "platform" in columns
                else " WHERE status='Completed'"
            )
            complete_row = conn.execute(
                f"SELECT COUNT(*) FROM sql_practice{complete_where}"
            ).fetchone()
            interview_completed = int(_row_value(complete_row, "COUNT(*)", 0, 0) or 0)

    duck_completed = 0
    if _table_exists(conn, "duckdb_exercise_progress"):
        columns = _columns(conn, "duckdb_exercise_progress")
        if "status" in columns:
            row = conn.execute(
                "SELECT COUNT(*) FROM duckdb_exercise_progress WHERE status='Completed'"
            ).fetchone()
            duck_completed = int(_row_value(row, "COUNT(*)", 0, 0) or 0)
        elif "completed" in columns:
            row = conn.execute(
                "SELECT COUNT(*) FROM duckdb_exercise_progress WHERE completed=1"
            ).fetchone()
            duck_completed = int(_row_value(row, "COUNT(*)", 0, 0) or 0)
    total = interview_total + DUCKDB_TOTAL
    completed = min(total, interview_completed + duck_completed)
    return total, completed


def _applied_counts(conn: sqlite3.Connection) -> tuple[int, int]:
    completed = 0
    if _table_exists(conn, "applied_exercise_progress"):
        columns = _columns(conn, "applied_exercise_progress")
        if "status" in columns:
            row = conn.execute(
                "SELECT COUNT(*) FROM applied_exercise_progress WHERE status='Completed'"
            ).fetchone()
            completed = int(_row_value(row, "COUNT(*)", 0, 0) or 0)
        elif "completed" in columns:
            row = conn.execute(
                "SELECT COUNT(*) FROM applied_exercise_progress WHERE completed=1"
            ).fetchone()
            completed = int(_row_value(row, "COUNT(*)", 0, 0) or 0)
    return APPLIED_TOTAL, min(APPLIED_TOTAL, completed)


def _portfolio_counts(conn: sqlite3.Connection) -> tuple[int, int, int]:
    if not _table_exists(conn, "project_tasks"):
        return 0, 0, 0
    columns = _columns(conn, "project_tasks")
    completed_column = "completed" if "completed" in columns else None
    total_row = conn.execute("SELECT COUNT(*) FROM project_tasks").fetchone()
    total = int(_row_value(total_row, "COUNT(*)", 0, 0) or 0)
    completed = 0
    remaining_minutes = 0
    if completed_column:
        completed_row = conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE completed=1"
        ).fetchone()
        completed = int(_row_value(completed_row, "COUNT(*)", 0, 0) or 0)
        if "estimated_minutes" in columns:
            minutes_row = conn.execute(
                "SELECT COALESCE(SUM(COALESCE(estimated_minutes,120)),0) "
                "FROM project_tasks WHERE completed=0"
            ).fetchone()
            remaining_minutes = int(_row_value(minutes_row, "SUM", 0, 0) or 0)
    return total, min(total, completed), max(0, remaining_minutes)


def register_academy_catalog(conn: sqlite3.Connection, catalog: Any) -> dict[str, Any]:
    """Persist the complete Academy workload so all three learning tracks fit Day 90."""
    track_totals: dict[str, int] = {}
    required_activities = 0
    for path in getattr(getattr(catalog, "program", None), "paths", ()):
        for track in getattr(path, "tracks", ()):
            track_id = str(getattr(track, "track_id", "academy") or "academy")
            count = 0
            for course in getattr(track, "courses", ()):
                for module in getattr(course, "modules", ()):
                    for lesson in getattr(module, "lessons", ()):
                        for activity in getattr(lesson, "activities", ()):
                            if bool(getattr(activity, "required_for_completion", True)):
                                count += 1
            track_totals[track_id] = count
            required_activities += count

    try:
        assessment_count = len(tuple(catalog.assessments()))
    except Exception:
        assessment_count = 0
    try:
        skills_lab_count = len(tuple(catalog.skills_labs()))
    except Exception:
        skills_lab_count = 0

    total_items = required_activities + assessment_count + skills_lab_count
    metadata = {
        "total_items": total_items,
        "required_activities": required_activities,
        "assessment_count": assessment_count,
        "skills_lab_count": skills_lab_count,
        "track_totals": track_totals,
        "fixed_deadline": True,
    }
    _set_settings(
        conn,
        {KEY_ACADEMY_CATALOG: json.dumps(metadata, sort_keys=True, separators=(",", ":"))},
    )
    return metadata


def _academy_counts(conn: sqlite3.Connection) -> tuple[int | None, int, dict[str, Any]]:
    metadata: dict[str, Any] = {}
    raw_catalog = _get_setting(conn, KEY_ACADEMY_CATALOG, "{}")
    try:
        metadata = json.loads(raw_catalog or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        metadata = {}

    total: int | None = None
    try:
        candidate = int(metadata.get("total_items", 0) or 0)
    except (TypeError, ValueError):
        candidate = 0
    if candidate > 0:
        total = candidate

    completed_activities = 0
    if _table_exists(conn, "academy_activity_progress"):
        columns = _columns(conn, "academy_activity_progress")
        if "state" in columns:
            row = conn.execute(
                "SELECT COUNT(*) FROM academy_activity_progress "
                "WHERE state IN ('Passed','Completed')"
            ).fetchone()
            completed_activities = int(_row_value(row, "COUNT(*)", 0, 0) or 0)

    completed_assessments = 0
    if _table_exists(conn, "academy_assessment_attempts"):
        columns = _columns(conn, "academy_assessment_attempts")
        if {"assessment_id", "passed"}.issubset(columns):
            row = conn.execute(
                "SELECT COUNT(DISTINCT assessment_id) FROM academy_assessment_attempts "
                "WHERE passed=1"
            ).fetchone()
            completed_assessments = int(_row_value(row, "COUNT", 0, 0) or 0)

    completed_labs = 0
    if _table_exists(conn, "academy_submissions"):
        columns = _columns(conn, "academy_submissions")
        if {"item_type", "item_id", "validation_status"}.issubset(columns):
            row = conn.execute(
                "SELECT COUNT(DISTINCT item_id) FROM academy_submissions "
                "WHERE item_type='skills_lab' AND validation_status='Passed'"
            ).fetchone()
            completed_labs = int(_row_value(row, "COUNT", 0, 0) or 0)

    completed = completed_activities + completed_assessments + completed_labs
    if _table_exists(conn, "track_state"):
        row = conn.execute(
            "SELECT status FROM track_state WHERE track_key='academy'"
        ).fetchone()
        if str(_row_value(row, "status", 0, "")) == "Completed" and total is not None:
            completed = total
    if total is not None:
        completed = min(total, completed)
    metadata.update(
        {
            "completed_activities": completed_activities,
            "completed_assessments": completed_assessments,
            "completed_skills_labs": completed_labs,
        }
    )
    return total, completed, metadata


def _budget_remaining(track_key: str, total: int | None, completed: int) -> int:
    budget = int(TRACK_BUDGET_MINUTES[track_key])
    if total is None or total <= 0:
        return budget if completed <= 0 else 0
    fraction_remaining = max(0.0, min(1.0, (int(total) - int(completed)) / int(total)))
    return int(math.ceil(budget * fraction_remaining))


def remaining_work(conn: sqlite3.Connection, state: Any) -> dict[str, dict[str, Any]]:
    google_completed = _google_completed(conn, state)
    sql_total, sql_completed = _sql_counts(conn)
    applied_total, applied_completed = _applied_counts(conn)
    portfolio_total, portfolio_completed, portfolio_minutes = _portfolio_counts(conn)
    academy_total, academy_completed, _ = _academy_counts(conn)

    result: dict[str, dict[str, Any]] = {
        "google": {
            "total": GOOGLE_TOTAL,
            "completed": google_completed,
            "remaining": max(0, GOOGLE_TOTAL - google_completed),
            "minutes_per_item": TRACK_MINUTES["google"],
            "budget_minutes_remaining": _budget_remaining("google", GOOGLE_TOTAL, google_completed),
        },
        "sql": {
            "total": sql_total,
            "completed": sql_completed,
            "remaining": max(0, sql_total - sql_completed),
            "minutes_per_item": TRACK_MINUTES["sql"],
            "budget_minutes_remaining": _budget_remaining("sql", sql_total, sql_completed),
        },
        "portfolio": {
            "total": portfolio_total,
            "completed": portfolio_completed,
            "remaining": max(0, portfolio_total - portfolio_completed),
            "minutes_per_item": TRACK_MINUTES["portfolio"],
            "remaining_minutes": min(TRACK_BUDGET_MINUTES["portfolio"], portfolio_minutes),
            "budget_minutes_remaining": min(TRACK_BUDGET_MINUTES["portfolio"], portfolio_minutes),
        },
        "applied": {
            "total": applied_total,
            "completed": applied_completed,
            "remaining": max(0, applied_total - applied_completed),
            "minutes_per_item": TRACK_MINUTES["applied"],
            "budget_minutes_remaining": _budget_remaining("applied", applied_total, applied_completed),
        },
        "academy": {
            "total": academy_total,
            "completed": academy_completed,
            "remaining": (
                max(0, academy_total - academy_completed)
                if academy_total is not None
                else None
            ),
            "minutes_per_item": TRACK_MINUTES["academy"],
            "budget_minutes_remaining": _budget_remaining("academy", academy_total, academy_completed),
        },
    }
    return result


def _remaining_minutes(item: dict[str, Any]) -> int:
    if "budget_minutes_remaining" in item:
        return max(0, int(item.get("budget_minutes_remaining") or 0))
    if "remaining_minutes" in item and int(item.get("remaining_minutes") or 0) > 0:
        return int(item["remaining_minutes"])
    remaining = item.get("remaining")
    if remaining is None:
        return 0
    return int(remaining) * int(item.get("minutes_per_item") or 60)


def _weekly_target(remaining: int | None, weeks_remaining: int, fallback: int) -> int:
    if remaining is None:
        return max(0, int(fallback))
    if remaining <= 0:
        return 0
    return max(1, math.ceil(int(remaining) / max(1, int(weeks_remaining))))


def _sync_academy_contract(
    conn: sqlite3.Connection,
    contract_clock: dict[str, Any],
    work: dict[str, dict[str, Any]],
) -> None:
    if not _table_exists(conn, "track_state"):
        return
    columns = _columns(conn, "track_state")
    if not {"track_key", "metadata", "weekly_target"}.issubset(columns):
        return
    row = conn.execute(
        "SELECT metadata,weekly_target FROM track_state WHERE track_key='academy'"
    ).fetchone()
    if row is None:
        return
    try:
        metadata = json.loads(_row_value(row, "metadata", 0, "{}") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        metadata = {}
    existing_target = int(_row_value(row, "weekly_target", 1, 0) or 0)
    required = _weekly_target(
        work["academy"].get("remaining"),
        contract_clock["weeks_remaining"],
        existing_target,
    )
    metadata.update(
        {
            "program_day": contract_clock["program_day"],
            "program_days": PROGRAM_DAYS,
            "program_end_date": contract_clock["end_date"],
            "deadline_weekly_target": required,
            "fixed_deadline": True,
        }
    )
    assignments = "weekly_target=?,metadata=?"
    if "updated_at" in columns:
        assignments += ",updated_at=CURRENT_TIMESTAMP"
    conn.execute(
        f"UPDATE track_state SET {assignments} WHERE track_key='academy'",
        (required, json.dumps(metadata, sort_keys=True, separators=(",", ":"))),
    )
    conn.commit()


def ensure_contract(
    conn: sqlite3.Connection,
    state: Any,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Create or refresh the immutable 90-day completion contract.

    A brand-new learner receives an 18-hour weekly target. Existing learner
    preferences are preserved. The deadline never rolls forward when work is missed.
    """
    current = today or date.today()
    if not _profile_is_ready(conn):
        return {"active": False, "program_days": PROGRAM_DAYS}

    start = _parse_date(_get_setting(conn, KEY_START_DATE))
    created = start is None
    if start is None:
        origin = _get_setting(conn, "onboarding.profile_origin", "new")
        start = current if origin == "new" else _derive_existing_start(current, state)
    end = start + timedelta(days=PROGRAM_DAYS - 1)
    _set_settings(
        conn,
        {
            KEY_START_DATE: start.isoformat(),
            KEY_END_DATE: end.isoformat(),
            KEY_DURATION_DAYS: PROGRAM_DAYS,
        },
    )

    contract_clock = clock(conn, today=current)
    expected_week = min(SPRINT_WEEKS, max(1, ((contract_clock["program_day"] - 1) // 7) + 1))
    origin = _get_setting(conn, "onboarding.profile_origin", "new")
    selected_weekly_hours = max(
        DEFAULT_WEEKLY_HOURS,
        _state_float(state, "weekly_target_hours", DEFAULT_WEEKLY_HOURS),
    )
    state_values: dict[str, Any] = {
        "current_week": expected_week,
        "weekly_target_hours": selected_weekly_hours,
    }
    _set_program_state(conn, **state_values)

    work = remaining_work(conn, state)
    weekly_minutes = sum(_remaining_minutes(item) for item in work.values()) / max(
        1, contract_clock["weeks_remaining"]
    )
    required_weekly_hours = round(weekly_minutes / 60.0, 1)
    snapshot = {
        **contract_clock,
        "program_days": PROGRAM_DAYS,
        "required_weekly_hours": required_weekly_hours,
        "selected_weekly_hours": selected_weekly_hours,
        "work": work,
        "fixed_deadline": True,
        "capacity_hours": round(PROGRAM_CAPACITY_MINUTES / 60.0, 1),
        "scope_budget_hours": round(sum(TRACK_BUDGET_MINUTES.values()) / 60.0, 1),
        "scope_fits_90_days": sum(TRACK_BUDGET_MINUTES.values()) <= PROGRAM_CAPACITY_MINUTES,
    }
    _set_settings(
        conn,
        {
            KEY_REQUIRED_WEEKLY_HOURS: required_weekly_hours,
            KEY_SNAPSHOT: json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
        },
    )
    _sync_academy_contract(conn, contract_clock, work)
    return snapshot


def prepare_state(conn: sqlite3.Connection, state: Any) -> dict[str, Any]:
    """Advance completed projects and align the active sprint to the 90-day clock."""
    normalized = dict(state)
    if _table_exists(conn, "project_tasks") and _table_exists(conn, "program_state"):
        current_project = max(1, _state_int(state, "current_project", 1))
        remaining_current = conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE project_id=? AND completed=0",
            (current_project,),
        ).fetchone()
        if int(_row_value(remaining_current, "COUNT(*)", 0, 0) or 0) == 0:
            next_row = conn.execute(
                "SELECT project_id FROM project_tasks WHERE completed=0 "
                "GROUP BY project_id ORDER BY project_id LIMIT 1"
            ).fetchone()
            if next_row is not None:
                next_project = int(_row_value(next_row, "project_id", 0, current_project))
                if next_project != current_project:
                    _set_program_state(conn, current_project=next_project)
                    normalized["current_project"] = next_project

    snapshot = ensure_contract(conn, normalized)
    if snapshot.get("active"):
        expected_week = min(SPRINT_WEEKS, max(1, ((snapshot["program_day"] - 1) // 7) + 1))
        normalized["current_week"] = expected_week
        normalized["weekly_target_hours"] = max(
            DEFAULT_WEEKLY_HOURS,
            _state_float(normalized, "weekly_target_hours", DEFAULT_WEEKLY_HOURS),
        )
    return normalized


def deadline_allocations(
    conn: sqlite3.Connection,
    state: Any,
    base_allocations: dict[str, dict[str, Any]],
    *,
    portfolio_ready: bool = True,
) -> dict[str, dict[str, Any]]:
    """Replace open-ended pacing with quotas that finish by Day 90."""
    snapshot = ensure_contract(conn, state)
    if not snapshot.get("active"):
        return base_allocations
    work = snapshot["work"]
    weeks_remaining = snapshot["weeks_remaining"]
    allocations = {key: dict(value) for key, value in base_allocations.items()}

    weekly_minutes: dict[str, int] = {}
    for track_key in ("google", "sql", "portfolio", "applied"):
        if track_key not in allocations:
            continue
        remaining = work.get(track_key, {}).get("remaining")
        required_target = _weekly_target(
            remaining,
            weeks_remaining,
            int(allocations[track_key].get("weekly_target") or 0),
        )
        if track_key == "portfolio" and not portfolio_ready and remaining:
            # Keep the quota visible while prerequisites are being learned. The track
            # remains locked by the existing readiness engine, then catches up later.
            required_target = max(1, required_target)
        allocations[track_key]["weekly_target"] = required_target
        minutes = math.ceil(
            _remaining_minutes(work.get(track_key, {})) / max(1, weeks_remaining)
        )
        allocations[track_key]["allocation_minutes"] = max(0, minutes)
        weekly_minutes[track_key] = max(0, minutes)

    total_minutes = sum(weekly_minutes.values())
    for track_key, minutes in weekly_minutes.items():
        allocations[track_key]["allocation_percent"] = (
            round(minutes * 100 / total_minutes) if total_minutes else 0
        )
        allocations[track_key]["program_day"] = snapshot["program_day"]
        allocations[track_key]["program_end_date"] = snapshot["end_date"]
        allocations[track_key]["fixed_deadline"] = True
    return allocations


def _track_key_for_item(conn: sqlite3.Connection, item: dict[str, Any]) -> str | None:
    track_key = str(item.get("track_key") or "").strip().lower()
    if track_key:
        return track_key
    source_key = str(item.get("source_key") or "")
    if source_key.startswith("roadmap:"):
        return source_key.split(":", 1)[1].lower()
    task_id = item.get("task_id")
    if task_id is not None and _table_exists(conn, "track_tasks"):
        row = conn.execute(
            "SELECT track_key FROM track_tasks WHERE task_id=?", (int(task_id),)
        ).fetchone()
        value = _row_value(row, "track_key", 0, None)
        if value:
            return str(value).lower()
    return None


def _track_pace(conn: sqlite3.Connection, track_key: str | None) -> dict[str, Any]:
    if not track_key or not _table_exists(conn, "track_state"):
        return {}
    row = conn.execute(
        "SELECT weekly_target,metadata FROM track_state WHERE track_key=?", (track_key,)
    ).fetchone()
    if row is None:
        return {}
    try:
        metadata = json.loads(_row_value(row, "metadata", 1, "{}") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        metadata = {}
    metadata.setdefault("weekly_target", int(_row_value(row, "weekly_target", 0, 0) or 0))
    return metadata


def focus_detail(
    conn: sqlite3.Connection,
    item: dict[str, Any],
    detail: str,
    state: Any,
) -> str:
    """Guarantee a descriptive second line with daily, weekly, and 90-day pacing."""
    text = " ".join(str(detail or item.get("label") or "Continue assigned work").split())
    track_key = _track_key_for_item(conn, item)
    pace = _track_pace(conn, track_key)
    additions: list[str] = []
    if "Today " not in text and pace:
        today_target = int(pace.get("today_target", 0) or 0)
        today_completed = int(pace.get("today_completed", 0) or 0)
        if today_target:
            additions.append(f"Today {today_completed}/{today_target}")
    if "Week " not in text and pace:
        weekly_target = int(pace.get("weekly_target", 0) or 0)
        weekly_completed = int(pace.get("weekly_completed", 0) or 0)
        if weekly_target:
            additions.append(f"Week {weekly_completed}/{weekly_target}")

    contract_clock = clock(conn)
    if contract_clock.get("active") and "Day " not in text:
        additions.append(f"Day {contract_clock['program_day']}/{PROGRAM_DAYS}")
    if additions:
        text += " • " + " • ".join(additions)
    return text


def summary(conn: sqlite3.Connection, state: Any) -> dict[str, Any]:
    snapshot = ensure_contract(conn, state)
    if not snapshot.get("active"):
        return snapshot
    selected = _state_float(state, "weekly_target_hours", DEFAULT_WEEKLY_HOURS)
    required = float(snapshot.get("required_weekly_hours") or 0)
    snapshot["hours_gap"] = round(max(0.0, required - selected), 1)
    snapshot["on_pace_capacity"] = selected >= required
    return snapshot
