from __future__ import annotations

"""Canonical task/readiness/planning service for Career Accelerator v10.28.1.

The application historically accumulated several independent recommendation
systems.  This module is the single runtime source for:

* task identity and presentation;
* prerequisite/readiness state;
* Today\'s Focus selection;
* Next Tasks ordering;
* Coming Up lock explanations; and
* daily five-task snapshot and rolling catch-up planning.

The existing sprint/progress tables remain the durable storage layer so learner
history is preserved.  Legacy planners may still exist for migration support,
but normal runtime planning is delegated here.
"""

from dataclasses import dataclass
from datetime import date
import json
import re
import sqlite3
from typing import Iterable

from career_app.data.applied_exercises import exercise_for_label as applied_for_label
from career_app.data.applied_exercises import exercise_number_for_label as applied_number_for_label
from career_app.data.duckdb_exercises import exercise_for_label as duckdb_for_label
from career_app.data.duckdb_exercises import exercise_number_for_label
from career_app.data.python_exercises import exercise_for_label as python_for_label
from career_app.data.python_exercises import exercise_number_for_label as python_exercise_number_for_label
from career_app.data.roadmap import SQL_COMPANION
from career_app.services import roadmap_mastery
from career_app.services import datacamp
from career_app.services import weekly_checks
from career_app.services.task_titles import title_case_task
from career_app.navigation import PAGE_LEARNING, PAGE_PORTFOLIO, PAGE_WORKSPACES


GOOGLE_TRACK = "google"
DATACAMP_TRACK = "datacamp"
SQL_TRACK = "sql"
PORTFOLIO_TRACK = "portfolio"
APPLIED_TRACK = "applied"

MAX_FOCUS_TASKS = 5
MAX_NEXT_TASKS = 4
MAX_COMING_UP = 3

_SQL_TITLES = tuple(str(item[0]) for item in SQL_COMPANION)

_PREPARATION_TOKENS = (
    "business problem",
    "stakeholder",
    "business question",
    "define kpi",
    "kpi definition",
    "project brief",
    "data source",
    "source or generate",
    "create or acquire raw",
    "raw dataset",
    "data dictionary",
    "relationship map",
    "schema review",
    "analysis plan",
    "cleaning plan",
    "validation plan",
    "decision log",
    "document assumptions",
)

_EXECUTION_TOKENS = (
    "clean",
    "validate analytical",
    "create schema",
    "load data",
    "analysis quer",
    "sql analysis",
    "perform eda",
    "exploratory analysis",
    "derived metric",
    "document insight",
    "build data model",
    "power bi",
    "create measure",
    "build dashboard",
    "filters and drill",
    "executive summary",
    "recommendation",
    "screenshot",
    "finalize readme",
    "publish",
    "reproducible portfolio",
)


@dataclass(frozen=True)
class Readiness:
    ready: bool
    reason: str = ""


def _safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _durable_duckdb_completions(conn: sqlite3.Connection) -> set[int]:
    """Load submitted DuckDB exercises once for the entire planner pass.

    Sprint rows are presentation records and may be repaired or replaced during
    startup.  The planner must never show a submitted exercise merely because a
    reusable sprint row temporarily says incomplete.
    """
    completed: set[int] = set()
    if _table_exists(conn, "duckdb_exercise_progress"):
        completed.update(
            int(row["exercise_number"])
            for row in conn.execute(
                """SELECT exercise_number
                   FROM duckdb_exercise_progress
                   WHERE status='Completed'"""
            ).fetchall()
        )
    if _table_exists(conn, "duckdb_completion_evidence"):
        completed.update(
            int(row["exercise_number"])
            for row in conn.execute(
                "SELECT exercise_number FROM duckdb_completion_evidence"
            ).fetchall()
        )
    return completed


def _normalize_label(value: object) -> str:
    text = str(value or "").strip()
    # Early v10.26 reconciliation stored presentation prefixes in the title.
    text = re.sub(r"^Catch-Up:\s*Academy:\s*", "", text, flags=re.I)
    text = re.sub(r"^Catch-Up:\s*", "", text, flags=re.I)
    return title_case_task(text.strip())


def _task_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT
                 s.id,s.week,s.sort_order,s.label,s.completed,
                 m.status,m.priority,m.estimated_minutes,m.energy,m.deferred_until,
                 m.destination,m.category,m.prerequisite_state,
                 m.prerequisite_reason,m.description,m.definition_of_done,
                 m.starter_path,m.managed_key,
                 tt.track_key,tt.target_key,tt.source_label,tt.linked_entity_id,
                 r.due_week AS requirement_due_week
             FROM sprint_tasks AS s
             JOIN task_metadata AS m ON m.task_id=s.id
             LEFT JOIN track_tasks AS tt ON tt.task_id=s.id
             LEFT JOIN roadmap_requirement_state AS r
               ON m.managed_key=('roadmap_v1026:' || r.requirement_key)
             ORDER BY s.week,s.sort_order,s.id"""
    ).fetchall()


def _sql_title(label: str, target_key: str = "") -> str | None:
    haystack = f"{label} {target_key}".casefold()
    for title in _SQL_TITLES:
        if title.casefold() in haystack:
            return title
    return None


def _project_task(conn: sqlite3.Connection, linked_entity_id: object):
    task_id = _safe_int(linked_entity_id, 0)
    if not task_id:
        return None
    return conn.execute(
        "SELECT id,project_id,stage,label,managed_key FROM project_tasks WHERE id=?",
        (task_id,),
    ).fetchone()


def _portfolio_kind(conn: sqlite3.Connection, task: dict) -> str:
    label = str(task.get("label") or "").casefold()
    project_row = _project_task(conn, task.get("linked_entity_id"))
    if project_row is not None:
        label = f"{label} {str(project_row['label'] or '').casefold()} {str(project_row['stage'] or '').casefold()}"
    if any(token in label for token in _PREPARATION_TOKENS) and not any(
        token in label for token in _EXECUTION_TOKENS
    ):
        return "portfolio_preparation"
    return "portfolio_execution"


def _kind(conn: sqlite3.Connection, task: dict) -> str:
    track_key = str(task.get("track_key") or "").casefold()
    managed_key = str(task.get("managed_key") or "").casefold()
    label = str(task.get("label") or "")

    if track_key == GOOGLE_TRACK:
        return "google"
    if managed_key.startswith("weekly_check:") or re.fullmatch(
        r"week\s+\d+\s+knowledge\s+check", label.casefold()
    ):
        return "weekly_check"
    if managed_key.startswith("datacamp:") or track_key == DATACAMP_TRACK:
        return "datacamp_chapter"
    if duckdb_for_label(label) is not None or managed_key.startswith("roadmap_v1026:duckdb:"):
        return "duckdb"
    if python_for_label(label) is not None or managed_key.startswith("roadmap_v1026:python:"):
        return "python_exercise"
    if _sql_title(label, str(task.get("target_key") or "")) is not None:
        return "interview_problem"
    if applied_for_label(label) is not None or track_key == APPLIED_TRACK:
        return "applied_lab"
    if track_key == PORTFOLIO_TRACK or str(task.get("category") or "") == "Portfolio":
        return _portfolio_kind(conn, task)
    if str(task.get("category") or "") == "Review" or "retrospective" in label.casefold():
        return "review"
    if str(task.get("category") or "") == "SQL":
        return "sql_practice"
    if _safe_int(task.get("week"), 99) >= 10:
        return "career_readiness"
    return "general"


def _phase_for_week(week: int) -> str:
    week = max(1, int(week))
    if week <= 2:
        return "spreadsheets"
    if week <= 6:
        return "sql"
    if week == 7:
        return "power_bi"
    if week == 8:
        return "python"
    return "portfolio"


def _learning_area(task: dict) -> str:
    """Return the subject area represented by a learning task."""
    chapter = datacamp.chapter_for_task(task)
    if chapter is not None:
        return {
            "Spreadsheets": "spreadsheets",
            "SQL": "sql",
            "Power BI": "power_bi",
            "Python": "python",
        }.get(chapter.area, _phase_for_week(chapter.week))

    haystack = " ".join(
        str(task.get(key) or "")
        for key in ("managed_key", "target_key", "label", "source_label", "display_source")
    ).casefold()
    if any(token in haystack for token in (
        "spreadsheet", "google sheets", "cell reference", "pivot table",
        "vlookup", "xlookup", "countif", "sumif", "iferror",
    )):
        return "spreadsheets"
    if any(token in haystack for token in ("power_bi", "power bi", "power query", "dax")):
        return "power_bi"
    if any(token in haystack for token in ("python", "pandas", "dataframe", "numpy")):
        return "python"
    if any(token in haystack for token in (
        "sql", "duckdb", "select ", "join", "group by", "cte", "window function",
    )):
        return "sql"
    return _phase_for_week(_safe_int(task.get("week"), 1))


def _area_labels(task: dict) -> tuple[str, str]:
    area = _learning_area(task)
    return {
        "spreadsheets": ("Sheets", "Spreadsheets"),
        "sql": ("SQL", "SQL"),
        "power_bi": ("Power BI", "Power BI"),
        "python": ("Python", "Python"),
        "portfolio": ("Portfolio", "Portfolio"),
    }.get(area, ("Learning", "Learning"))


def task_type_label(task: dict, current_week: int | None = None) -> str:
    """Return the compact metadata label used by task lists."""
    kind = str(task.get("kind") or "general")
    short_area, _full_area = _area_labels(task)
    if kind == "google":
        return "Google"
    if kind == "weekly_check":
        return "Checkpoint"
    if kind == "datacamp_chapter":
        return "DataCamp"
    if kind in {"duckdb", "interview_problem", "sql_practice"}:
        return "SQL"
    if kind == "python_exercise":
        return "Python"
    if kind == "applied_lab":
        return "Skills Lab"
    if kind in {"portfolio_preparation", "portfolio_execution"}:
        return "Portfolio"
    if kind == "review":
        return "Review"
    if kind == "career_readiness":
        return "Career"
    category = str(task.get("category") or "General").strip()
    return {"Learning": short_area, "SQL": "SQL"}.get(category, category or "General")


def focus_context(task: dict, current_week: int) -> str:
    """Return the concise second line shown under a focus title.

    Catch-Up is a factual scheduling state, not a presentation prefix stored in
    the task title. It appears only when the task's scheduled week is earlier
    than the active sprint week.
    """
    kind = str(task.get("kind") or "general")
    week = max(1, _safe_int(task.get("week"), current_week))
    short_area, full_area = _area_labels(task)

    if kind == "google":
        detail = "Google Certification"
    elif kind == "weekly_check":
        detail = f"Weekly Assessment • Week {week}"
    elif kind == "datacamp_chapter":
        detail = f"DataCamp • {full_area} • Week {week}"
    elif kind == "duckdb":
        detail = f"DuckDB SQL • Week {week}"
    elif kind == "interview_problem":
        detail = f"SQL Interview Practice • Week {week}"
    elif kind == "python_exercise":
        detail = f"Python Practice • Week {week}"
    elif kind == "sql_practice":
        detail = f"SQL Practice • Week {week}"
    elif kind == "applied_lab":
        detail = f"Skills Lab • Week {week}"
    elif kind in {"portfolio_preparation", "portfolio_execution"}:
        detail = f"Portfolio • Week {week}"
    elif kind == "review":
        detail = f"Weekly Review • Week {week}"
    elif kind == "career_readiness":
        detail = f"Career Readiness • Week {week}"
    else:
        label = task_type_label(task, current_week)
        detail = f"{label} • Week {week}"

    return f"Catch-Up • {detail}" if bool(task.get("is_catch_up")) else detail


def _promoted_for_today(conn: sqlite3.Connection, task_id: int) -> bool:
    if not task_id or not _table_exists(conn, "task_day_promotions"):
        return False
    try:
        return conn.execute(
            """SELECT 1 FROM task_day_promotions
               WHERE promotion_date=? AND task_id=? LIMIT 1""",
            (date.today().isoformat(), int(task_id)),
        ).fetchone() is not None
    except Exception:
        return False


def _calendar_readiness(conn: sqlite3.Connection, task: dict) -> Readiness | None:
    """Return a day lock when the task is assigned later than today.

    Content prerequisites and calendar availability are separate.  A task may
    have every prerequisite complete while still belonging to a later roadmap
    day.  A deliberate Current Sprint promotion remains the only exception.
    """
    raw = str(task.get("deferred_until") or "").strip()
    if not raw:
        return None
    try:
        scheduled = date.fromisoformat(raw)
    except ValueError:
        return None
    task_id = _safe_int(task.get("task_id") or task.get("id"), 0)
    if scheduled > date.today() and not _promoted_for_today(conn, task_id):
        return Readiness(
            False,
            f"Scheduled for {scheduled.strftime('%A, %B %d')}.",
        )
    return None


def _readiness(conn: sqlite3.Connection, task: dict, current_week: int) -> Readiness:
    if bool(task.get("completed")) or str(task.get("status") or "") == "Completed":
        return Readiness(False, "Already completed.")

    week = _safe_int(task.get("week"), current_week)
    kind = str(task.get("kind") or "")
    metadata_state = str(task.get("prerequisite_state") or "Ready")
    metadata_reason = str(task.get("prerequisite_reason") or "").strip()

    if kind == "weekly_check":
        check_week = weekly_checks.week_from_task(task) or week
        result = weekly_checks.readiness(conn, int(check_week))
        return Readiness(result.ready, result.reason)

    if week > current_week and kind not in {"google"}:
        return Readiness(False, f"Scheduled for Week {week}.")

    progression = weekly_checks.progression_gate(
        conn, task_week=week, current_week=current_week, kind=kind
    )
    if not progression.ready:
        return Readiness(False, progression.reason)

    calendar = _calendar_readiness(conn, task)
    if calendar is not None:
        return calendar

    if kind == "datacamp_chapter":
        ready, reason = datacamp.readiness(conn, task)
        return Readiness(ready, reason)

    if metadata_state.casefold() not in {"ready", "unlocked", ""}:
        return Readiness(False, metadata_reason or "Complete the prerequisite first.")

    if kind == "duckdb":
        number = exercise_number_for_label(task.get("label"))
        if number is None:
            match = re.search(r"roadmap_v1026:duckdb:(\d+)", str(task.get("managed_key") or ""))
            number = int(match.group(1)) if match else None
        if number is not None:
            result = roadmap_mastery.duckdb_readiness(conn, int(number))
            return Readiness(bool(result.get("ready")), str(result.get("reason") or ""))

    if kind == "interview_problem":
        title = _sql_title(str(task.get("label") or ""), str(task.get("target_key") or ""))
        if title:
            result = roadmap_mastery.sql_problem_readiness(conn, title)
            return Readiness(bool(result.get("ready")), str(result.get("reason") or ""))

    if kind == "python_exercise":
        number = python_exercise_number_for_label(str(task.get("label") or ""))
        if number is None:
            match = re.search(r"roadmap_v1026:python:(\d+)", str(task.get("managed_key") or ""))
            number = int(match.group(1)) if match else None
        if number is not None:
            result = roadmap_mastery.python_exercise_readiness(conn, int(number))
            return Readiness(bool(result.get("ready")), str(result.get("reason") or ""))

    if kind == "applied_lab":
        item = applied_for_label(str(task.get("label") or ""))
        number = applied_number_for_label(str(task.get("label") or ""))
        if item is not None and number is not None:
            from career_app.services import tracks

            state_row = conn.execute("SELECT * FROM program_state WHERE id=1").fetchone()
            app_state = (
                {key: state_row[key] for key in state_row.keys()}
                if state_row is not None
                else {"current_week": current_week, "google_course": 1, "google_module": 1}
            )
            result = tracks.applied_lab_readiness(
                conn,
                app_state,
                int(number),
            )
            reason = "" if result.get("ready") else "Complete " + "; ".join(result.get("missing") or []) + " first."
            return Readiness(bool(result.get("ready")), reason)

    if kind in {"portfolio_preparation", "portfolio_execution"}:
        from career_app.services import tracks

        state_row = conn.execute("SELECT * FROM program_state WHERE id=1").fetchone()
        app_state = (
            {key: state_row[key] for key in state_row.keys()}
            if state_row is not None
            else {"current_week": current_week, "google_course": 1, "google_module": 1}
        )
        result = tracks.portfolio_task_readiness(
            conn,
            app_state,
            str(task.get("label") or ""),
        )
        reason = "" if result.get("ready") else "Complete " + "; ".join(result.get("missing") or []) + " first."
        return Readiness(bool(result.get("ready")), reason)

    if kind == "review":
        label = str(task.get("label") or "")
        managed_key = str(task.get("managed_key") or "")
        is_retrospective = (
            "retrospective" in label.casefold()
            or managed_key.casefold().startswith("weekly_retrospective_")
        )
        if is_retrospective and not weekly_checks.passed(conn, week):
            return Readiness(
                False,
                f"Pass Week {week} Knowledge Check to unlock this retrospective.",
            )
        today = date.today()
        if week == current_week and today.weekday() < 4:
            return Readiness(False, "Available on the final study days of this week.")

    return Readiness(True, "")


def _source(task: dict) -> str:
    kind = str(task.get("kind") or "general")
    if kind == "google":
        return str(task.get("source_label") or "Google Certificate")
    if kind == "weekly_check":
        return f"Week {_safe_int(task.get('week'), 1)} Mastery Check"
    if kind == "datacamp_chapter":
        chapter = datacamp.chapter_for_task(task)
        return f"DataCamp • {chapter.course_name}" if chapter else "DataCamp"
    if kind == "duckdb":
        item = duckdb_for_label(task.get("label"))
        return f"SQL Challenge • {item['title']}" if item else "SQL Challenge"
    if kind == "interview_problem":
        return "SQL Interview Practice"
    if kind == "python_exercise":
        item = python_for_label(task.get("label"))
        return f"Python Exercise • {item['title']}" if item else "Python Exercise"
    if kind == "applied_lab":
        return "Applied Lab"
    if kind == "portfolio_preparation":
        return "Portfolio Preparation"
    if kind == "portfolio_execution":
        return "Portfolio Execution"
    if kind == "review":
        return f"Weekly Review • Week {_safe_int(task.get('week'), 1)}"
    if kind == "career_readiness":
        return "Career Readiness"
    return f"Roadmap • Week {_safe_int(task.get('week'), 1)}"


def _display_title(task: dict) -> str:
    kind = str(task.get("kind") or "general")
    return {
        "google": "Google Certificate",
        "weekly_check": "Weekly Knowledge Check",
        "datacamp_chapter": "DataCamp Chapter",
        "duckdb": "DuckDB Practice",
        "interview_problem": "SQL Interview Practice",
        "sql_practice": "SQL Practice",
        "applied_lab": "Applied Lab",
        "portfolio_preparation": "Portfolio Preparation",
        "portfolio_execution": "Portfolio Project",
        "review": "Weekly Review",
        "career_readiness": "Career Readiness",
        "general": "Roadmap Task",
    }.get(kind, "Roadmap Task")


def _reason(task: dict, current_week: int) -> str:
    # Today’s Focus uses task type and scheduled week. Catch-up remains a
    # separate metadata state in Next Tasks and only begins after the week ends.
    return focus_context(task, current_week)


def _as_task(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    current_week: int,
    durable_duckdb_completed: set[int] | None = None,
) -> dict:
    task = {key: row[key] for key in row.keys()}
    task["id"] = _safe_int(task.get("id"), 0)
    task["task_id"] = task["id"]
    task["planner_week"] = _safe_int(task.get("week"), current_week)
    task["week"] = _safe_int(
        task.get("requirement_due_week"), task["planner_week"]
    )
    task["sort_order"] = _safe_int(task.get("sort_order"), 0)
    task["estimated_minutes"] = max(5, _safe_int(task.get("estimated_minutes"), 30))
    task["label"] = _normalize_label(task.get("label"))
    task["kind"] = _kind(conn, task)

    # Durable exercise evidence is the source of truth for DuckDB completion.
    # Overlay it before readiness, catch-up, Focus, and Next Tasks are derived so
    # a stale/recreated sprint row cannot resurrect a submitted exercise.
    if task["kind"] == "duckdb" and durable_duckdb_completed:
        # managed_key stores the stable internal exercise number. The visible
        # label contains the learner-facing roadmap number, which may differ
        # after curriculum resequencing (for example internal 19 is Exercise 02).
        match = re.search(
            r"roadmap_v1026:duckdb:(\d+)",
            str(task.get("managed_key") or ""),
        )
        number = int(match.group(1)) if match else None
        if number is None:
            number = exercise_number_for_label(task.get("label"))
        if number is not None and int(number) in durable_duckdb_completed:
            task["completed"] = 1
            task["status"] = "Completed"
            task["durable_completion"] = True

    # Weekly work becomes catch-up after its week ends. DataCamp chapters are
    # scheduled by day, so an unfinished chapter becomes catch-up the next day.
    deferred_text = str(task.get("deferred_until") or "").strip()
    overdue_datacamp = False
    if task["kind"] == "datacamp_chapter" and deferred_text:
        try:
            overdue_datacamp = date.fromisoformat(deferred_text) < date.today()
        except ValueError:
            overdue_datacamp = False
    task["is_catch_up"] = (
        (task["week"] < int(current_week) or overdue_datacamp)
        and not bool(task.get("completed"))
    )
    readiness = _readiness(conn, task, current_week)
    task["ready"] = readiness.ready
    task["prerequisite_state"] = "Ready" if readiness.ready else "Locked"
    task["prerequisite_reason"] = readiness.reason or None
    task["display_source"] = _source(task)
    task["display_title"] = _display_title(task)
    task["metadata_label"] = task_type_label(task, current_week)
    task["detail"] = _reason(task, current_week)
    task["roadmap_fallback"] = True
    return task


def task_by_id(conn: sqlite3.Connection, current_week: int, task_id: int) -> dict | None:
    for task in all_tasks(conn, current_week):
        if _safe_int(task.get("id"), 0) == int(task_id):
            return task
    return None


def all_tasks(conn: sqlite3.Connection, current_week: int) -> list[dict]:
    durable_duckdb_completed = _durable_duckdb_completions(conn)
    tasks = [
        _as_task(
            conn,
            row,
            current_week,
            durable_duckdb_completed,
        )
        for row in _task_rows(conn)
    ]

    # Current-week work must remain visible even when earlier learning work is
    # unfinished. Readiness rules decide whether the current lesson is available;
    # the queue no longer hides an otherwise-ready current-week task merely
    # because a catch-up task exists.

    # Only the current Google module may exist in the active task pool.
    google_seen = False
    filtered: list[dict] = []
    for task in tasks:
        if task["kind"] == "google":
            if google_seen:
                continue
            google_seen = True
        filtered.append(task)
    return filtered


def _semantic_task_identity(task: dict) -> str:
    """Return one logical identity even when legacy rows use different keys.

    SQL interview problems historically existed both as durable roadmap rows and
    reusable adaptive-track rows. Their managed keys differ, so key-only
    deduplication displayed the same problem twice. Resolve those rows through
    the canonical SQL catalog title before falling back to durable identifiers.
    """
    kind = str(task.get("kind") or "")
    if kind == "interview_problem":
        title = _sql_title(
            str(task.get("label") or ""),
            str(task.get("target_key") or ""),
        )
        if title:
            return "interview_problem:" + re.sub(
                r"[^a-z0-9]+", " ", title.casefold()
            ).strip()
    if kind == "datacamp_chapter":
        chapter = datacamp.chapter_for_task(task)
        if chapter is not None:
            return f"datacamp:{chapter.key}"
    return str(
        task.get("managed_key")
        or task.get("target_key")
        or f"task:{task.get('id')}"
    )


def _dedupe(tasks: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for task in tasks:
        key = _semantic_task_identity(task)
        if key in seen:
            continue
        seen.add(key)
        result.append(task)
    return result


def _roadmap_sort(task: dict, current_week: int) -> tuple:
    kind = str(task.get("kind") or "general")
    kind_rank = {
        "google": 0,
        "weekly_check": 5,
        "datacamp_chapter": 20,
        "duckdb": 30,
        "interview_problem": 31,
        "sql_practice": 32,
        "python_exercise": 33,
        "applied_lab": 35,
        "portfolio_preparation": 40,
        "portfolio_execution": 45,
        "review": 50,
        "career_readiness": 60,
        "general": 70,
    }.get(kind, 70)
    scheduled_week = _safe_int(task.get("week"), current_week)
    if scheduled_week == int(current_week):
        week_rank = 0
    elif scheduled_week < int(current_week):
        week_rank = 1
    else:
        week_rank = 2
    # Across every ready/open queue, Google remains first and DataCamp is
    # immediately next. Week/catch-up placement only breaks ties inside those
    # priority bands; it must not place an unrelated practice item above an
    # open DataCamp chapter.
    priority_band = 0 if kind == "google" else 1 if kind == "datacamp_chapter" else 2
    return (
        priority_band,
        week_rank,
        kind_rank,
        scheduled_week,
        _safe_int(task.get("sort_order"), 0),
        _safe_int(task.get("id"), 0),
    )


def _focus_display_sort(task: dict, current_week: int) -> tuple:
    """Keep actionable prerequisites above the grey chapters they unlock."""
    if not bool(task.get("ready")):
        return (
            1,
            0 if str(task.get("kind") or "") == "datacamp_chapter" else 1,
            _safe_int(task.get("sort_order"), 0),
            _safe_int(task.get("week"), current_week),
            _safe_int(task.get("id"), 0),
        )
    return (0, *_roadmap_sort(task, current_week))


def _queue_incomplete_tasks(tasks: Iterable[dict]) -> list[dict]:
    """Return incomplete logical assignments with completion merged by identity.

    A legacy roadmap row and an adaptive-track row can represent the same SQL
    problem. If either row is complete, the logical assignment is complete and
    must not reappear through the other row.
    """
    pool = list(tasks)
    completed_identities = {
        _semantic_task_identity(task)
        for task in pool
        if bool(task.get("completed"))
    }
    return [
        task
        for task in pool
        if not bool(task.get("completed"))
        and _semantic_task_identity(task) not in completed_identities
    ]


def ready_tasks(conn: sqlite3.Connection, current_week: int) -> list[dict]:
    tasks = [
        task
        for task in _queue_incomplete_tasks(all_tasks(conn, current_week))
        if task["ready"]
    ]
    return sorted(_dedupe(tasks), key=lambda task: _roadmap_sort(task, current_week))


def _locked_sort(task: dict, current_week: int) -> tuple:
    """Put the nearest missing prerequisite before distant mastery gates."""
    kind_rank = {
        "weekly_check": 5,
        "datacamp_chapter": 10,
        "duckdb": 20,
        "interview_problem": 21,
        "sql_practice": 22,
        "python_exercise": 23,
        "applied_lab": 25,
        "portfolio_preparation": 40,
        "portfolio_execution": 45,
        "review": 50,
        "career_readiness": 60,
        "general": 70,
        "google": 80,
    }.get(str(task.get("kind") or "general"), 70)
    return (
        0 if task.get("is_catch_up") or task.get("week", current_week) <= current_week else 1,
        _safe_int(task.get("week"), current_week),
        kind_rank,
        _safe_int(task.get("sort_order"), 0),
        _safe_int(task.get("id"), 0),
    )


def locked_tasks(conn: sqlite3.Connection, current_week: int) -> list[dict]:
    tasks = [
        task
        for task in _queue_incomplete_tasks(all_tasks(conn, current_week))
        if not task["ready"]
        and str(task.get("kind") or "") != "weekly_check"
    ]
    return sorted(_dedupe(tasks), key=lambda task: _locked_sort(task, current_week))


def _pick_first(pool: list[dict], selected: list[dict], kinds: set[str]) -> dict | None:
    selected_ids = {int(item["id"]) for item in selected}
    for task in pool:
        if int(task["id"]) in selected_ids:
            continue
        if task["kind"] in kinds:
            return task
    return None


def _snapshot_setting_key(focus_date: str) -> str:
    return f"daily_focus_snapshot_v2:{focus_date}"


def _locked_supplementary_focus_candidate(task: dict, current_week: int) -> bool:
    """Keep scheduled practice visible even while its prerequisite is incomplete.

    DataCamp chapters, DuckDB exercises, SQL interview problems, and Python
    exercises can occupy a grey Today's Focus row once their roadmap week has
    arrived. Controls remain disabled and the second line names the missing
    prerequisite. Future-week work stays hidden.
    """
    kind = str(task.get("kind") or "")
    allowed = {
        "datacamp_chapter",
        "duckdb",
        "interview_problem",
        "sql_practice",
        "python_exercise",
    }
    if kind not in allowed:
        return False
    if bool(task.get("completed")) or bool(task.get("ready")):
        return False
    if _safe_int(task.get("week"), current_week) > int(current_week):
        return False
    reason = str(task.get("prerequisite_reason") or "").strip()
    if not reason:
        return False
    if kind == "datacamp_chapter":
        due_text = str(task.get("deferred_until") or "").strip()
        if not due_text:
            return False
        try:
            return date.fromisoformat(due_text) <= date.today()
        except ValueError:
            return False
    return True


def _task_identity(task: dict) -> str:
    return str(
        task.get("target_key")
        or task.get("managed_key")
        or f"task:{_safe_int(task.get('id'), 0)}"
    )


def _load_daily_snapshot(
    conn: sqlite3.Connection,
    focus_date: str,
    current_week: int,
) -> dict | None:
    if not _table_exists(conn, "settings"):
        return None
    row = conn.execute(
        "SELECT value FROM settings WHERE key=?",
        (_snapshot_setting_key(focus_date),),
    ).fetchone()
    if row is None:
        return None
    try:
        payload = json.loads(str(row["value"] or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if _safe_int(payload.get("week"), 0) != int(current_week):
        return None
    assignments = payload.get("new_assignments")
    if not isinstance(assignments, list):
        return None
    return payload


def _save_daily_snapshot(
    conn: sqlite3.Connection,
    focus_date: str,
    current_week: int,
    assignments: list[dict],
) -> dict:
    payload = {
        "version": 3,
        "focus_date": focus_date,
        "week": int(current_week),
        "new_task_limit": MAX_FOCUS_TASKS,
        "new_assignments": assignments[:MAX_FOCUS_TASKS],
    }
    conn.execute(
        """INSERT INTO settings(key,value) VALUES(?,?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (_snapshot_setting_key(focus_date), json.dumps(payload, sort_keys=True)),
    )
    return payload


def _new_assignment_payload(task: dict) -> dict:
    return {
        "task_id": _safe_int(task.get("id"), 0),
        "identity": _task_identity(task),
        "target_key": str(task.get("target_key") or ""),
        "track_key": str(task.get("track_key") or ""),
        "category": str(task.get("category") or "General"),
        "title": str(task.get("label") or "Task"),
        "estimated_minutes": max(5, _safe_int(task.get("estimated_minutes"), 30)),
    }


def _daily_focus_rows(conn: sqlite3.Connection, focus_date: str) -> list[sqlite3.Row]:
    if not _table_exists(conn, "daily_focus"):
        return []
    return conn.execute(
        """SELECT id,focus_date,week,position,task_id,source_key,category,title,
                  estimated_minutes,track_key,target_key,is_extra,focus_kind,
                  completed_at,created_at
           FROM daily_focus
           WHERE focus_date=?
           ORDER BY position,id""",
        (focus_date,),
    ).fetchall()


def _daily_row_for_identity(
    rows: list[sqlite3.Row],
    identity: str,
    *,
    focus_kind: str,
) -> sqlite3.Row | None:
    for row in rows:
        if str(row["focus_kind"] or "new") != focus_kind:
            continue
        if str(row["source_key"] or "") == identity:
            return row
    return None


def _next_free_position(rows: list[sqlite3.Row], start: int) -> int:
    used = {_safe_int(row["position"], 0) for row in rows}
    position = int(start)
    while position in used:
        position += 1
    return position


def _insert_daily_focus_assignment(
    conn: sqlite3.Connection,
    *,
    focus_date: str,
    current_week: int,
    position: int,
    task: dict,
    focus_kind: str,
) -> None:
    conn.execute(
        """INSERT INTO daily_focus
           (focus_date,week,position,task_id,source_key,category,title,
            estimated_minutes,track_key,target_key,is_extra,focus_kind,completed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,0,?,NULL)""",
        (
            focus_date,
            int(current_week),
            int(position),
            _safe_int(task.get("id"), 0) or None,
            _task_identity(task),
            str(task.get("category") or "General"),
            str(task.get("label") or "Task"),
            max(5, _safe_int(task.get("estimated_minutes"), 30)),
            task.get("track_key"),
            task.get("target_key"),
            focus_kind,
        ),
    )


def _normalize_daily_focus_positions(
    conn: sqlite3.Connection,
    focus_date: str,
    assignments: list[dict],
) -> None:
    """Reconcile persisted Focus rows with the current snapshot safely.

    Older builds could leave a completed, replaced, or stale row occupying one
    of positions 1-5.  Because ``daily_focus`` enforces a unique
    ``(focus_date, position)`` pair, inserting a newly promoted task into that
    slot could fail before the dashboard opened.  Move every row to a temporary
    unique position first, reclassify rows no longer owned by the snapshot, and
    then assign stable position bands for current Focus, Catch-Up, and history.
    """
    rows = _daily_focus_rows(conn, focus_date)
    if not rows:
        return

    assignment_positions = {
        str(item.get("identity") or ""): index
        for index, item in enumerate(assignments, start=1)
        if str(item.get("identity") or "")
    }

    # Move all rows outside the live position bands before any resequencing.
    # The temporary range starts above the largest current position, so each
    # update remains valid even under SQLite's immediate UNIQUE enforcement.
    max_position = max((_safe_int(row["position"], 0) for row in rows), default=0)
    temp_base = max(1000, max_position + len(rows) + 100)
    for offset, row in enumerate(rows, start=1):
        conn.execute(
            "UPDATE daily_focus SET position=? WHERE id=?",
            (temp_base + offset, int(row["id"])),
        )

    # Rows that are no longer part of the frozen snapshot must not occupy or be
    # counted as active Focus work. Keep completed rows as history; remove only
    # stale, incomplete planner rows. Also collapse duplicate planner rows that
    # may have been created by older builds before source identity was stable.
    new_groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        if str(row["focus_kind"] or "new") == "new":
            new_groups.setdefault(str(row["source_key"] or ""), []).append(row)

    for identity, group in new_groups.items():
        ordered = sorted(group, key=lambda row: int(row["id"]))
        keeper = ordered[0]
        completed_values = [
            str(row["completed_at"]) for row in ordered if row["completed_at"]
        ]
        if completed_values and not keeper["completed_at"]:
            conn.execute(
                "UPDATE daily_focus SET completed_at=? WHERE id=?",
                (min(completed_values), int(keeper["id"])),
            )
        for duplicate in ordered[1:]:
            conn.execute("DELETE FROM daily_focus WHERE id=?", (int(duplicate["id"]),))

        if identity not in assignment_positions:
            if completed_values or keeper["completed_at"]:
                conn.execute(
                    "UPDATE daily_focus SET focus_kind='history' WHERE id=?",
                    (int(keeper["id"]),),
                )
            else:
                conn.execute("DELETE FROM daily_focus WHERE id=?", (int(keeper["id"]),))

    rows = _daily_focus_rows(conn, focus_date)
    by_identity = {
        str(row["source_key"] or ""): row
        for row in rows
        if str(row["focus_kind"] or "new") == "new"
    }
    for identity, position in assignment_positions.items():
        row = by_identity.get(identity)
        if row is not None:
            conn.execute(
                "UPDATE daily_focus SET position=? WHERE id=?",
                (int(position), int(row["id"])),
            )

    catchup_rows = [
        row for row in _daily_focus_rows(conn, focus_date)
        if str(row["focus_kind"] or "") == "catch_up"
    ]
    for index, row in enumerate(catchup_rows, start=21):
        conn.execute(
            "UPDATE daily_focus SET position=? WHERE id=?",
            (index, int(row["id"])),
        )

    history_rows = [
        row for row in _daily_focus_rows(conn, focus_date)
        if str(row["focus_kind"] or "") not in {"new", "catch_up"}
    ]
    for index, row in enumerate(history_rows, start=101):
        conn.execute(
            "UPDATE daily_focus SET position=? WHERE id=?",
            (index, int(row["id"])),
        )



def _migrate_today_focus_rows(
    conn: sqlite3.Connection,
    focus_date: str,
    current_week: int,
    task_map: dict[int, dict],
) -> None:
    """Classify same-day rows created before the v2 snapshot migration."""
    for row in _daily_focus_rows(conn, focus_date):
        task = task_map.get(_safe_int(row["task_id"], 0))
        kind = str(row["focus_kind"] or "new")
        if task is not None and bool(task.get("is_catch_up")):
            kind = "catch_up"
        elif row["completed_at"] and task is None:
            kind = "history"
        if kind != str(row["focus_kind"] or "new"):
            conn.execute(
                "UPDATE daily_focus SET focus_kind=? WHERE id=?",
                (kind, int(row["id"])),
            )


def _promote_newly_ready_focus_task(
    conn: sqlite3.Connection,
    focus_date: str,
    current_week: int,
    focus_limit: int,
    snapshot: dict,
    tasks: list[dict],
) -> dict:
    """Replace one locked preview with newly unlocked current-week work.

    The daily plan remains stable for actionable assignments. The only dynamic
    promotion is a task whose prerequisites became satisfied during the day,
    such as Applied Lab 01 after the final spreadsheet chapter is completed.
    """
    assignments = list(snapshot.get("new_assignments") or [])[:MAX_FOCUS_TASKS]
    task_map = {int(task["id"]): task for task in tasks}
    assigned = {str(item.get("identity") or "") for item in assignments}
    candidates = [
        task
        for task in tasks
        if bool(task.get("ready"))
        and not bool(task.get("completed"))
        and (
            (not bool(task.get("is_catch_up"))
             and _safe_int(task.get("week"), current_week) == int(current_week))
            or str(task.get("kind") or "") == "weekly_check"
        )
        and _task_identity(task) not in assigned
    ]
    priority_kinds = {
        "weekly_check": -1,
        "applied_lab": 0,
        "duckdb": 1,
        "interview_problem": 2,
        "sql_practice": 3,
        "python_exercise": 3,
        "portfolio_preparation": 4,
        "portfolio_execution": 5,
        "datacamp_chapter": 20,
    }
    candidates.sort(
        key=lambda task: (
            priority_kinds.get(str(task.get("kind") or ""), 10),
            _roadmap_sort(task, current_week),
        )
    )
    if not candidates:
        return snapshot

    replaceable = []
    for index, assignment in enumerate(assignments):
        task = task_map.get(_safe_int(assignment.get("task_id"), 0))
        if (
            task is not None
            and not bool(task.get("ready"))
            and str(task.get("kind") or "") in {
                "datacamp_chapter", "duckdb", "interview_problem",
                "sql_practice", "python_exercise"
            }
        ):
            replaceable.append(index)

    changed = False
    for task in candidates:
        if len(assignments) < focus_limit:
            assignments.append(_new_assignment_payload(task))
            changed = True
            break
        if replaceable:
            assignments[replaceable[-1]] = _new_assignment_payload(task)
            changed = True
            break

    if not changed:
        return snapshot

    snapshot = _save_daily_snapshot(
        conn, focus_date, current_week, assignments
    )
    valid_identities = {str(item.get("identity") or "") for item in assignments}
    for row in _daily_focus_rows(conn, focus_date):
        if (
            str(row["focus_kind"] or "new") == "new"
            and not row["completed_at"]
            and str(row["source_key"] or "") not in valid_identities
        ):
            conn.execute("DELETE FROM daily_focus WHERE id=?", (int(row["id"]),))
    return snapshot


def _ensure_daily_snapshot(
    conn: sqlite3.Connection,
    current_week: int,
    max_items: int,
    tasks: list[dict],
) -> dict:
    focus_date = date.today().isoformat()
    snapshot = _load_daily_snapshot(conn, focus_date, current_week)
    task_map = {int(task["id"]): task for task in tasks}
    _migrate_today_focus_rows(conn, focus_date, current_week, task_map)

    focus_limit = max(1, min(MAX_FOCUS_TASKS, int(max_items)))
    current_candidates = sorted(
        (
            task
            for task in tasks
            if not bool(task.get("completed"))
            and _safe_int(task.get("week"), current_week) == int(current_week)
            and not bool(task.get("is_catch_up"))
            and (
                bool(task.get("ready"))
                or _locked_supplementary_focus_candidate(task, current_week)
            )
        ),
        key=lambda task: _roadmap_sort(task, current_week),
    )

    if snapshot is None:
        assignments = [
            _new_assignment_payload(task)
            for task in current_candidates[:focus_limit]
        ]
        snapshot = _save_daily_snapshot(
            conn,
            focus_date,
            current_week,
            assignments,
        )
    else:
        assignments = list(snapshot.get("new_assignments") or [])[:MAX_FOCUS_TASKS]
        # v10.36.7 upgrades an existing same-day snapshot once. Preserve every
        # assignment already chosen, then fill unused positions with due locked
        # DataCamp chapters so the learner can see the full five-task sequence.
        if _safe_int(snapshot.get("version"), 2) < 3 and len(assignments) < focus_limit:
            existing = {str(item.get("identity") or "") for item in assignments}
            for task in current_candidates:
                identity = _task_identity(task)
                if identity in existing:
                    continue
                assignments.append(_new_assignment_payload(task))
                existing.add(identity)
                if len(assignments) >= focus_limit:
                    break
            snapshot = _save_daily_snapshot(
                conn, focus_date, current_week, assignments
            )

    snapshot = _promote_newly_ready_focus_task(
        conn,
        focus_date,
        current_week,
        focus_limit,
        snapshot,
        tasks,
    )
    assignments = list(snapshot.get("new_assignments") or [])[:MAX_FOCUS_TASKS]
    _normalize_daily_focus_positions(conn, focus_date, assignments)

    rows = _daily_focus_rows(conn, focus_date)
    for index, assignment in enumerate(assignments, start=1):
        identity = str(assignment.get("identity") or "")
        if not identity:
            continue
        existing = _daily_row_for_identity(rows, identity, focus_kind="new")
        if existing is not None:
            continue
        task = task_map.get(_safe_int(assignment.get("task_id"), 0))
        if task is None:
            task = {
                "id": assignment.get("task_id"),
                "target_key": assignment.get("target_key"),
                "track_key": assignment.get("track_key"),
                "category": assignment.get("category"),
                "label": assignment.get("title"),
                "estimated_minutes": assignment.get("estimated_minutes"),
            }
        _insert_daily_focus_assignment(
            conn,
            focus_date=focus_date,
            current_week=current_week,
            position=index,
            task=task,
            focus_kind="new",
        )
        rows = _daily_focus_rows(conn, focus_date)

    return snapshot


def _mark_completed_snapshot_rows(
    conn: sqlite3.Connection,
    focus_date: str,
    task_map: dict[int, dict],
) -> None:
    for row in _daily_focus_rows(conn, focus_date):
        task = task_map.get(_safe_int(row["task_id"], 0))
        if task is None:
            continue
        completed = bool(task.get("completed"))
        if completed and not row["completed_at"]:
            conn.execute(
                "UPDATE daily_focus SET completed_at=CURRENT_TIMESTAMP WHERE id=?",
                (int(row["id"]),),
            )
        elif not completed and row["completed_at"]:
            # A task can be restored by an undo or track repair. Clear the
            # stale daily marker so the footer cannot report 1/1 while the
            # same task is still visibly active.
            conn.execute(
                "UPDATE daily_focus SET completed_at=NULL WHERE id=?",
                (int(row["id"]),),
            )


def _active_new_tasks(
    conn: sqlite3.Connection,
    focus_date: str,
    snapshot: dict,
    task_map: dict[int, dict],
    current_week: int,
) -> list[dict]:
    rows = _daily_focus_rows(conn, focus_date)
    completed_by_identity = {
        str(row["source_key"] or "")
        for row in rows
        if str(row["focus_kind"] or "new") == "new" and row["completed_at"]
    }
    active: list[dict] = []
    for assignment in snapshot.get("new_assignments") or []:
        identity = str(assignment.get("identity") or "")
        if not identity or identity in completed_by_identity:
            continue
        task = task_map.get(_safe_int(assignment.get("task_id"), 0))
        if task is None or bool(task.get("completed")):
            continue
        # A migration may correct a task's scheduled week after the daily
        # snapshot was created. Do not keep an overdue task in the frozen
        # current-week quota; the rolling Catch-Up queue owns it instead.
        if bool(task.get("is_catch_up")):
            continue
        item = dict(task)
        item["focus_kind"] = "new"
        active.append(item)
    return active


def _sync_active_catchup(
    conn: sqlite3.Connection,
    focus_date: str,
    current_week: int,
    slots: int,
    ready: list[dict],
) -> list[dict]:
    catchup = [
        dict(task)
        for task in ready
        if bool(task.get("is_catch_up"))
        and (
            bool(task.get("ready"))
            or _locked_supplementary_focus_candidate(task, current_week)
        )
    ]
    selected = catchup[: max(0, int(slots))]
    selected_identities = {_task_identity(task) for task in selected}

    rows = _daily_focus_rows(conn, focus_date)
    for row in rows:
        if str(row["focus_kind"] or "new") != "catch_up" or row["completed_at"]:
            continue
        if str(row["source_key"] or "") not in selected_identities:
            conn.execute("DELETE FROM daily_focus WHERE id=?", (int(row["id"]),))

    rows = _daily_focus_rows(conn, focus_date)
    for index, task in enumerate(selected, start=1):
        identity = _task_identity(task)
        existing = _daily_row_for_identity(rows, identity, focus_kind="catch_up")
        if existing is None:
            _insert_daily_focus_assignment(
                conn,
                focus_date=focus_date,
                current_week=current_week,
                position=_next_free_position(rows, 20 + index),
                task=task,
                focus_kind="catch_up",
            )
            rows = _daily_focus_rows(conn, focus_date)
        task["focus_kind"] = "catch_up"
        task["is_catch_up"] = True
    return selected


def daily_plan(conn: sqlite3.Connection, current_week: int, max_items: int = MAX_FOCUS_TASKS) -> list[dict]:
    """Return the frozen daily new-task quota plus rolling catch-up work.

    Exactly five prerequisite-ready current-week tasks (or fewer when fewer are
    ready) are assigned once per local date. Completing those tasks never pulls
    another current-week task into the same day. Earlier-week catch-up work fills
    vacant visible slots and advances one task at a time until the learner is
    caught up.
    """
    max_items = max(1, min(MAX_FOCUS_TASKS, int(max_items or MAX_FOCUS_TASKS)))
    tasks = all_tasks(conn, current_week)
    task_map = {int(task["id"]): task for task in tasks}
    snapshot = _ensure_daily_snapshot(conn, current_week, max_items, tasks)
    focus_date = date.today().isoformat()
    _mark_completed_snapshot_rows(conn, focus_date, task_map)

    active_new = _active_new_tasks(conn, focus_date, snapshot, task_map, current_week)
    catchup_candidates = sorted(
        all_tasks(conn, current_week),
        key=lambda task: _roadmap_sort(task, current_week),
    )
    active_catchup = _sync_active_catchup(
        conn,
        focus_date,
        current_week,
        max_items - len(active_new),
        catchup_candidates,
    )
    conn.commit()
    combined = _dedupe([*active_new, *active_catchup])
    return sorted(
        combined,
        key=lambda task: _focus_display_sort(task, current_week),
    )[:max_items]


def next_tasks(conn: sqlite3.Connection, current_week: int, limit: int = MAX_NEXT_TASKS) -> list[dict]:
    """Return actionable work before locked Focus previews.

    Today’s Focus may include greyed-out learning and practice tasks. Those rows still
    belong beneath the Coming Soon divider in Next Tasks and must never consume
    the compact card before a newly unlocked actionable item such as an
    Applied Lab.
    """
    focus = daily_plan(conn, current_week, max_items=MAX_FOCUS_TASKS)
    focus_ids = {_safe_int(item.get("id"), 0) for item in focus}
    ready_focus = [item for item in focus if bool(item.get("ready"))]
    locked_focus = [item for item in focus if not bool(item.get("ready"))]
    following = [
        task
        for task in ready_tasks(conn, current_week)
        if _safe_int(task.get("id"), 0) not in focus_ids
    ]
    queue = _dedupe([*ready_focus, *following, *locked_focus])
    return queue[: max(1, int(limit or MAX_NEXT_TASKS))]


def coming_up(conn: sqlite3.Connection, current_week: int, limit: int = MAX_COMING_UP) -> list[dict]:
    return locked_tasks(conn, current_week)[: max(1, int(limit or MAX_COMING_UP))]


def _persist_focus(conn: sqlite3.Connection, current_week: int, items: list[dict]) -> None:
    """Compatibility wrapper for callers that still request a planner write.

    The v2 planner owns its snapshot directly in :func:`daily_plan`; rewriting
    the day here would break the five-new-task cap. Calling this helper now only
    ensures the canonical snapshot exists.
    """
    del items
    daily_plan(conn, current_week, max_items=MAX_FOCUS_TASKS)


def completion_summary(conn: sqlite3.Connection, active_items: list[dict]) -> dict:
    focus_date = date.today().isoformat()
    state_row = conn.execute(
        "SELECT current_week FROM program_state WHERE id=1"
    ).fetchone()
    current_week = _safe_int(state_row["current_week"] if state_row else 1, 1)
    snapshot = _load_daily_snapshot(conn, focus_date, current_week) or {
        "new_assignments": []
    }
    rows = _daily_focus_rows(conn, focus_date)

    new_rows = [row for row in rows if str(row["focus_kind"] or "new") == "new"]
    catchup_rows = [row for row in rows if str(row["focus_kind"] or "") == "catch_up"]
    new_total = len(snapshot.get("new_assignments") or [])
    completed_new = sum(bool(row["completed_at"]) for row in new_rows)
    completed_catchup = sum(bool(row["completed_at"]) for row in catchup_rows)
    completed_rows = [row for row in rows if row["completed_at"]]
    completed_titles = [str(row["title"] or "Completed task") for row in completed_rows]

    assigned_minutes = sum(
        max(5, _safe_int(item.get("estimated_minutes"), 30))
        for item in snapshot.get("new_assignments") or []
    )
    active_catchup_minutes = sum(
        _safe_int(item.get("estimated_minutes"), 0)
        for item in active_items
        if item.get("is_catch_up") or item.get("focus_kind") == "catch_up"
    )

    remaining_catchup = [
        task
        for task in ready_tasks(conn, current_week)
        if bool(task.get("is_catch_up"))
    ]
    new_complete = completed_new >= new_total
    all_complete = bool(new_complete and not remaining_catchup and not active_items)

    session_count = 0
    if _table_exists(conn, "study_sessions"):
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM study_sessions WHERE session_date=?",
            (focus_date,),
        ).fetchone()
        session_count = _safe_int(row["n"] if row else 0, 0)

    return {
        "total_count": new_total,
        "completed_count": min(completed_new, new_total),
        "new_total_count": new_total,
        "new_completed_count": min(completed_new, new_total),
        "catchup_completed_count": completed_catchup,
        "catchup_remaining_count": len(remaining_catchup),
        "planned_minutes": assigned_minutes + active_catchup_minutes,
        "completed_titles": completed_titles,
        "session_count": session_count,
        "active_extra": None,
        "all_base_complete": all_complete,
        "inferred_empty_complete": all_complete,
    }


def _migrate_navigation_destinations(conn: sqlite3.Connection) -> int:
    """Align persisted task routes with the consolidated nine-page shell."""
    if not _table_exists(conn, "task_metadata"):
        return 0
    changed = 0
    statements = (
        (
            """UPDATE task_metadata SET destination=?
               WHERE LOWER(COALESCE(category,'')) IN ('learning','sql')
                 AND destination<>?""",
            (PAGE_LEARNING, PAGE_LEARNING),
        ),
        (
            """UPDATE task_metadata SET destination=?
               WHERE LOWER(COALESCE(category,''))='portfolio'
                 AND destination<>?""",
            (PAGE_PORTFOLIO, PAGE_PORTFOLIO),
        ),
        (
            """UPDATE task_metadata SET destination=?
               WHERE LOWER(COALESCE(category,''))='review'
                 AND destination<>?""",
            (PAGE_WORKSPACES, PAGE_WORKSPACES),
        ),
        (
            """UPDATE task_metadata SET destination=?
               WHERE task_id IN (
                   SELECT task_id FROM track_tasks
                   WHERE LOWER(track_key) IN ('google','datacamp','sql','applied')
               ) AND destination<>?""",
            (PAGE_LEARNING, PAGE_LEARNING),
        ),
        (
            """UPDATE task_metadata SET destination=?
               WHERE task_id IN (
                   SELECT task_id FROM track_tasks
                   WHERE LOWER(track_key)='portfolio'
               ) AND destination<>?""",
            (PAGE_PORTFOLIO, PAGE_PORTFOLIO),
        ),
    )
    for sql, params in statements:
        changed += max(0, conn.execute(sql, params).rowcount)
    return changed


def migrate_runtime(conn: sqlite3.Connection, current_week: int) -> dict:
    """Retire legacy planner rows while preserving active DataCamp chapters."""
    removed = {"academy_tasks": 0, "manual_focus": 0, "duplicate_google": 0, "navigation_routes": 0}
    purge = datacamp.purge_academy(conn)
    removed["academy_tasks"] = int(purge.get("tasks", 0))
    datacamp.reconcile(conn)
    weekly_checks.reconcile(conn)

    # Remove temporary presentation prefixes from canonical titles.
    rows = conn.execute(
        """SELECT s.id,s.label FROM sprint_tasks AS s
           JOIN task_metadata AS m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:%'"""
    ).fetchall()
    for row in rows:
        clean = _normalize_label(row["label"])
        if clean != str(row["label"] or ""):
            conn.execute("UPDATE sprint_tasks SET label=? WHERE id=?", (clean, int(row["id"])))

    # Manual/Get Ahead storage was derived UI state.  It is safe to clear.
    if _table_exists(conn, "manual_daily_focus"):
        removed["manual_focus"] = conn.execute("DELETE FROM manual_daily_focus").rowcount
    if _table_exists(conn, "daily_focus"):
        conn.execute("DELETE FROM daily_focus WHERE is_extra=1")

    # Keep only one active Google task; preserve the task linked by track_tasks.
    google_rows = conn.execute(
        """SELECT s.id,CASE WHEN tt.track_key='google' THEN 0 ELSE 1 END AS rank
           FROM sprint_tasks AS s
           JOIN task_metadata AS m ON m.task_id=s.id
           LEFT JOIN track_tasks AS tt ON tt.task_id=s.id
           WHERE s.completed=0 AND (
               LOWER(COALESCE(tt.track_key,''))='google'
               OR LOWER(s.label) LIKE '%google course%'
               OR LOWER(s.label) LIKE '%google certificate%'
           )
           ORDER BY rank,s.id DESC"""
    ).fetchall()
    keep = int(google_rows[0]["id"]) if google_rows else None
    for row in google_rows[1:]:
        task_id = int(row["id"])
        if task_id == keep:
            continue
        conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM track_tasks WHERE task_id=? AND track_key<>'google'", (task_id,))
        conn.execute("DELETE FROM task_metadata WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
        removed["duplicate_google"] += 1

    removed["navigation_routes"] = _migrate_navigation_destinations(conn)
    conn.execute(
        """INSERT INTO settings(key,value) VALUES('unified_planner_version','10.36.2')
           ON CONFLICT(key) DO UPDATE SET value=excluded.value"""
    )
    conn.execute(
        """INSERT INTO settings(key,value) VALUES('navigation_layout_version','10.36.2')
           ON CONFLICT(key) DO UPDATE SET value=excluded.value"""
    )
    conn.commit()
    return removed


def audit(conn: sqlite3.Connection, current_week: int) -> dict:
    tasks = all_tasks(conn, current_week)
    ready = [task for task in tasks if task["ready"] and not task["completed"]]
    locked = [task for task in tasks if not task["ready"] and not task["completed"]]
    google = [task for task in ready if task["kind"] == "google"]
    return {
        "total": len(tasks),
        "ready": len(ready),
        "locked": len(locked),
        "google_ready": len(google),
        "focus": [task["label"] for task in daily_plan(conn, current_week)],
        "next": [task["label"] for task in next_tasks(conn, current_week)],
        "coming_up": [task["label"] for task in coming_up(conn, current_week)],
    }
