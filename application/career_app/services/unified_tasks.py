from __future__ import annotations

"""Canonical task/readiness/planning service for Career Accelerator v10.28.1.

The application historically accumulated several independent recommendation
systems.  This module is the single runtime source for:

* task identity and presentation;
* prerequisite/readiness state;
* Today\'s Focus selection;
* Next Tasks ordering;
* Coming Up lock explanations; and
* optional practice discovery.

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
from career_app.data.duckdb_exercises import exercise_for_label as duckdb_for_label
from career_app.data.duckdb_exercises import exercise_number_for_label
from career_app.data.roadmap import SQL_COMPANION
from career_app.services import roadmap_mastery
from career_app.navigation import PAGE_LEARNING, PAGE_PORTFOLIO, PAGE_WORKSPACES


GOOGLE_TRACK = "google"
ACADEMY_TRACK = "academy"
SQL_TRACK = "sql"
PORTFOLIO_TRACK = "portfolio"
APPLIED_TRACK = "applied"

MAX_FOCUS_TASKS = 5
MAX_NEXT_TASKS = 6
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


def _normalize_label(value: object) -> str:
    text = str(value or "").strip()
    # Early v10.26 reconciliation stored presentation prefixes in the title.
    text = re.sub(r"^Catch-Up:\s*Academy:\s*", "", text, flags=re.I)
    text = re.sub(r"^Catch-Up:\s*", "", text, flags=re.I)
    return text.strip()


def _task_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT
                 s.id,s.week,s.sort_order,s.label,s.completed,
                 m.status,m.priority,m.estimated_minutes,m.energy,
                 m.destination,m.category,m.prerequisite_state,
                 m.prerequisite_reason,m.description,m.definition_of_done,
                 m.starter_path,m.managed_key,
                 tt.track_key,tt.target_key,tt.source_label,tt.linked_entity_id
             FROM sprint_tasks AS s
             JOIN task_metadata AS m ON m.task_id=s.id
             LEFT JOIN track_tasks AS tt ON tt.task_id=s.id
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
    if managed_key.startswith("roadmap_v1026:assessment:"):
        return "knowledge_check"
    if managed_key.startswith("roadmap_v1026:lesson:"):
        return "academy_lesson"
    if track_key == ACADEMY_TRACK:
        return "academy_lesson"
    if duckdb_for_label(label) is not None or managed_key.startswith("roadmap_v1026:duckdb:"):
        return "duckdb"
    if _sql_title(label, str(task.get("target_key") or "")) is not None:
        return "interview_problem"
    if applied_for_label(label) is not None or track_key == APPLIED_TRACK:
        return "applied_lab"
    if track_key == PORTFOLIO_TRACK or str(task.get("category") or "") == "Portfolio":
        return _portfolio_kind(conn, task)
    if str(task.get("category") or "") == "Review" or "retrospective" in label.casefold():
        return "review"
    if str(task.get("category") or "") == "Learning":
        return "academy_practice"
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
    """Return the specific Academy/learning area represented by a task."""
    haystack = " ".join(
        str(task.get(key) or "")
        for key in (
            "managed_key",
            "target_key",
            "label",
            "source_label",
            "display_source",
        )
    ).casefold()

    if any(token in haystack for token in (
        "spreadsheet", "google sheets", "cell reference", "pivot table",
        "vlookup", "countif", "sumif",
    )):
        return "spreadsheets"
    if any(token in haystack for token in (
        "power_bi", "power bi", "power query", "dax",
    )):
        return "power_bi"
    if any(token in haystack for token in (
        "python", "pandas", "dataframe",
    )):
        return "python"
    if any(token in haystack for token in (
        "sql", "duckdb", "select ", "join", "group by", "cte",
        "window function",
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
    if kind in {"academy_lesson", "academy_practice"}:
        return short_area
    if kind == "knowledge_check":
        return f"{short_area} Check" if short_area != "Learning" else "Assessment"
    if kind in {"duckdb", "interview_problem", "sql_practice"}:
        return "SQL"
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
    """Return the concise task-type line shown under a focus title."""
    kind = str(task.get("kind") or "general")
    week = max(1, _safe_int(task.get("week"), current_week))
    short_area, full_area = _area_labels(task)

    if kind == "google":
        return "Google Certification"
    if kind in {"academy_lesson", "academy_practice"}:
        return f"{full_area} • Week {week}"
    if kind == "knowledge_check":
        area = full_area if full_area != "Learning" else "Weekly"
        return f"{area} Assessment • Week {week}"
    if kind == "duckdb":
        return f"DuckDB SQL • Week {week}"
    if kind == "interview_problem":
        return f"SQL Interview Practice • Week {week}"
    if kind == "sql_practice":
        return f"SQL Practice • Week {week}"
    if kind == "applied_lab":
        return f"Skills Lab • Week {week}"
    if kind in {"portfolio_preparation", "portfolio_execution"}:
        return f"Portfolio • Week {week}"
    if kind == "review":
        return f"Weekly Review • Week {week}"
    if kind == "career_readiness":
        return f"Career Readiness • Week {week}"
    label = task_type_label(task, current_week)
    return f"{label} • Week {week}"


def _assessment_id_from_managed_key(managed_key: str) -> str | None:
    prefix = "roadmap_v1026:assessment:"
    text = str(managed_key or "")
    return text[len(prefix):] if text.startswith(prefix) else None


def _readiness(conn: sqlite3.Connection, task: dict, current_week: int) -> Readiness:
    if bool(task.get("completed")) or str(task.get("status") or "") == "Completed":
        return Readiness(False, "Already completed.")

    week = _safe_int(task.get("week"), current_week)
    kind = str(task.get("kind") or "")
    metadata_state = str(task.get("prerequisite_state") or "Ready")
    metadata_reason = str(task.get("prerequisite_reason") or "").strip()

    if week > current_week and kind not in {"google"}:
        return Readiness(False, f"Scheduled for Week {week}.")

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

    if kind == "knowledge_check":
        assessment_id = _assessment_id_from_managed_key(str(task.get("managed_key") or ""))
        if assessment_id:
            result = roadmap_mastery.assessment_readiness(conn, assessment_id)
            return Readiness(bool(result.get("ready")), str(result.get("reason") or ""))

    if kind == "portfolio_execution":
        if current_week < 9:
            return Readiness(False, "Portfolio execution begins in Week 9 after the learning phase.")
        if not roadmap_mastery.assessment_passed(conn, "week_8_portfolio_readiness"):
            return Readiness(False, "Pass the Week 8 Portfolio Readiness Assessment first.")

    if kind == "review":
        # Weekly retrospectives become actionable Friday through Sunday even
        # when other weekly work remains unfinished. A missed earlier-week
        # retrospective remains available as catch-up.
        today = date.today()
        if week == current_week and today.weekday() < 4:
            return Readiness(False, "Available on the final study days of this week.")

    return Readiness(True, "")


def _source(task: dict) -> str:
    kind = str(task.get("kind") or "general")
    if kind == "google":
        return str(task.get("source_label") or "Google Certificate")
    if kind in {"academy_lesson", "academy_practice"}:
        _short, full = _area_labels(task)
        return f"Accelerator Academy • {full}"
    if kind == "knowledge_check":
        _short, full = _area_labels(task)
        return f"{full} Mastery Check"
    if kind == "duckdb":
        item = duckdb_for_label(task.get("label"))
        return f"DuckDB Exercise • {item['title']}" if item else "DuckDB Exercise"
    if kind == "interview_problem":
        return "SQL Interview Practice"
    if kind == "applied_lab":
        return "Accelerator Academy • Skills Lab"
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
        "academy_lesson": "Accelerator Academy",
        "academy_practice": "Accelerator Academy",
        "knowledge_check": "Weekly Mastery Check",
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


def _as_task(conn: sqlite3.Connection, row: sqlite3.Row, current_week: int) -> dict:
    task = {key: row[key] for key in row.keys()}
    task["id"] = _safe_int(task.get("id"), 0)
    task["task_id"] = task["id"]
    task["week"] = _safe_int(task.get("week"), current_week)
    task["sort_order"] = _safe_int(task.get("sort_order"), 0)
    task["estimated_minutes"] = max(5, _safe_int(task.get("estimated_minutes"), 30))
    task["label"] = _normalize_label(task.get("label"))
    task["kind"] = _kind(conn, task)
    # A task is catch-up only after its scheduled week has ended. Missing an
    # earlier day in the same week does not change its status.
    task["is_catch_up"] = (
        task["week"] < int(current_week)
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


def all_tasks(conn: sqlite3.Connection, current_week: int) -> list[dict]:
    tasks = [_as_task(conn, row, current_week) for row in _task_rows(conn)]

    # A catch-up Academy lesson owns the visible progression slot.  Suppress a
    # stale reusable Academy pointer until the catch-up queue advances.
    catchup_active = any(
        task["is_catch_up"]
        and task["kind"] in {"academy_lesson", "knowledge_check"}
        and not task["completed"]
        for task in tasks
    )
    if catchup_active:
        tasks = [
            task
            for task in tasks
            if not (
                str(task.get("track_key") or "").casefold() == ACADEMY_TRACK
                and not task["is_catch_up"]
            )
        ]

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


def _dedupe(tasks: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for task in tasks:
        key = str(task.get("managed_key") or task.get("target_key") or f"task:{task.get('id')}")
        if key in seen:
            continue
        seen.add(key)
        result.append(task)
    return result


def _roadmap_sort(task: dict, current_week: int) -> tuple:
    kind = str(task.get("kind") or "general")
    kind_rank = {
        "google": 0,
        "knowledge_check": 10,
        "academy_lesson": 20,
        "academy_practice": 25,
        "duckdb": 30,
        "interview_problem": 31,
        "sql_practice": 32,
        "applied_lab": 35,
        "portfolio_preparation": 40,
        "portfolio_execution": 45,
        "review": 50,
        "career_readiness": 60,
        "general": 70,
    }.get(kind, 70)
    overdue_rank = 0 if task.get("is_catch_up") or task.get("week", current_week) < current_week else 1
    return (
        0 if kind == "google" else 1,
        overdue_rank,
        _safe_int(task.get("week"), current_week),
        kind_rank,
        _safe_int(task.get("sort_order"), 0),
        _safe_int(task.get("id"), 0),
    )


def ready_tasks(conn: sqlite3.Connection, current_week: int) -> list[dict]:
    tasks = [
        task
        for task in all_tasks(conn, current_week)
        if task["ready"] and not bool(task.get("completed"))
    ]
    return sorted(_dedupe(tasks), key=lambda task: _roadmap_sort(task, current_week))


def _locked_sort(task: dict, current_week: int) -> tuple:
    """Put the nearest missing prerequisite before distant mastery gates."""
    kind_rank = {
        "academy_lesson": 10,
        "academy_practice": 15,
        "duckdb": 20,
        "interview_problem": 21,
        "sql_practice": 22,
        "applied_lab": 25,
        "knowledge_check": 30,
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
        for task in all_tasks(conn, current_week)
        if not task["ready"] and not bool(task.get("completed"))
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


def daily_plan(conn: sqlite3.Connection, current_week: int, max_items: int = MAX_FOCUS_TASKS) -> list[dict]:
    """Return up to five ready tasks using fixed, explainable slot rules."""
    max_items = max(1, min(MAX_FOCUS_TASKS, int(max_items or MAX_FOCUS_TASKS)))
    pool = ready_tasks(conn, current_week)
    selected: list[dict] = []

    # 1. Google is always the highest-priority unfinished requirement.
    google = _pick_first(pool, selected, {"google"})
    if google:
        selected.append(google)

    # 2. Main progression: mastery gate, Academy, then portfolio execution.
    main = _pick_first(
        pool,
        selected,
        {"knowledge_check", "academy_lesson", "academy_practice", "portfolio_execution"},
    )
    if main:
        selected.append(main)

    # 3. Related practice.
    practice = _pick_first(
        pool,
        selected,
        {"duckdb", "interview_problem", "sql_practice", "applied_lab"},
    )
    if practice:
        selected.append(practice)

    # 4. Secondary progression.
    secondary = _pick_first(
        pool,
        selected,
        {"academy_lesson", "academy_practice", "knowledge_check", "portfolio_preparation", "portfolio_execution"},
    )
    if secondary:
        selected.append(secondary)

    # 5. Supporting work.
    supporting = _pick_first(
        pool,
        selected,
        {"knowledge_check", "portfolio_preparation", "review", "career_readiness", "general"},
    )
    if supporting:
        selected.append(supporting)

    # Fill any still-empty slots with the next ready item in roadmap order.
    selected_ids = {int(item["id"]) for item in selected}
    for task in pool:
        if len(selected) >= max_items:
            break
        if int(task["id"]) not in selected_ids:
            selected.append(task)
            selected_ids.add(int(task["id"]))

    selected = selected[:max_items]
    _persist_focus(conn, current_week, selected)
    return selected


def next_tasks(conn: sqlite3.Connection, current_week: int, limit: int = MAX_NEXT_TASKS) -> list[dict]:
    return ready_tasks(conn, current_week)[: max(1, int(limit or MAX_NEXT_TASKS))]


def coming_up(conn: sqlite3.Connection, current_week: int, limit: int = MAX_COMING_UP) -> list[dict]:
    return locked_tasks(conn, current_week)[: max(1, int(limit or MAX_COMING_UP))]


def optional_practice(conn: sqlite3.Connection, current_week: int, limit: int = 3) -> list[dict]:
    focus_ids = {int(item["id"]) for item in daily_plan(conn, current_week)}
    candidates = [
        task
        for task in ready_tasks(conn, current_week)
        if int(task["id"]) not in focus_ids
        and task["kind"] in {"duckdb", "interview_problem", "sql_practice", "applied_lab", "academy_practice"}
    ]
    return candidates[: max(0, int(limit or 0))]


def _persist_focus(conn: sqlite3.Connection, current_week: int, items: list[dict]) -> None:
    today = date.today().isoformat()
    if not _table_exists(conn, "daily_focus"):
        return

    completed_rows = conn.execute(
        """SELECT task_id,source_key,category,title,estimated_minutes,track_key,target_key,completed_at
             FROM daily_focus
             WHERE focus_date=? AND completed_at IS NOT NULL
             ORDER BY completed_at,id""",
        (today,),
    ).fetchall()
    conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (today,))

    for position, item in enumerate(items, start=1):
        source_key = str(item.get("managed_key") or item.get("target_key") or f"task:{item['id']}")
        conn.execute(
            """INSERT INTO daily_focus
               (focus_date,week,position,task_id,source_key,category,title,
                estimated_minutes,track_key,target_key,is_extra,completed_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,0,NULL)""",
            (
                today,
                int(current_week),
                position,
                int(item["id"]),
                source_key,
                str(item.get("category") or "General"),
                str(item.get("label") or "Task"),
                int(item.get("estimated_minutes") or 30),
                item.get("track_key"),
                item.get("target_key"),
            ),
        )

    # Retain completion history outside active positions for the footer.
    seen: set[tuple] = set()
    history_position = 101
    for row in completed_rows:
        identity = (row["task_id"], row["source_key"], row["title"])
        if identity in seen:
            continue
        seen.add(identity)
        conn.execute(
            """INSERT INTO daily_focus
               (focus_date,week,position,task_id,source_key,category,title,
                estimated_minutes,track_key,target_key,is_extra,completed_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,0,?)""",
            (
                today,
                int(current_week),
                history_position,
                row["task_id"],
                row["source_key"] or f"history:{history_position}",
                row["category"] or "General",
                row["title"] or "Completed task",
                _safe_int(row["estimated_minutes"], 30),
                row["track_key"],
                row["target_key"],
                row["completed_at"],
            ),
        )
        history_position += 1
    conn.commit()


def completion_summary(conn: sqlite3.Connection, active_items: list[dict]) -> dict:
    today = date.today().isoformat()
    completed_rows = []
    if _table_exists(conn, "daily_focus"):
        completed_rows = conn.execute(
            """SELECT title,estimated_minutes FROM daily_focus
               WHERE focus_date=? AND completed_at IS NOT NULL""",
            (today,),
        ).fetchall()
    completed_titles = [str(row["title"] or "Completed task") for row in completed_rows]
    completed_minutes = sum(_safe_int(row["estimated_minutes"], 0) for row in completed_rows)
    planned_minutes = sum(_safe_int(item.get("estimated_minutes"), 0) for item in active_items)
    session_count = 0
    if _table_exists(conn, "study_sessions"):
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM study_sessions WHERE session_date=?",
            (today,),
        ).fetchone()
        session_count = _safe_int(row["n"] if row else 0, 0)

    no_ready = not active_items
    return {
        "total_count": len(active_items) + len(completed_rows),
        "completed_count": len(completed_rows),
        "planned_minutes": planned_minutes + completed_minutes,
        "completed_titles": completed_titles,
        "session_count": session_count,
        "active_extra": None,
        "all_base_complete": bool(no_ready and completed_rows),
        "inferred_empty_complete": bool(no_ready and (completed_rows or session_count)),
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
                   WHERE LOWER(track_key) IN ('google','academy','sql','applied')
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
    """Retire active legacy planners without deleting learner history."""
    removed = {"datacamp_tasks": 0, "manual_focus": 0, "duplicate_google": 0, "navigation_routes": 0}

    # DataCamp remains in historical study-session/event rows only.
    datacamp_ids = [
        int(row["id"])
        for row in conn.execute(
            """SELECT DISTINCT s.id
               FROM sprint_tasks AS s
               LEFT JOIN track_tasks AS tt ON tt.task_id=s.id
               WHERE s.completed=0 AND (
                   LOWER(s.label) LIKE '%datacamp%'
                   OR LOWER(COALESCE(tt.track_key,''))='datacamp'
               )"""
        ).fetchall()
    ]
    for task_id in datacamp_ids:
        conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM task_metadata WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
    removed["datacamp_tasks"] = len(datacamp_ids)
    conn.execute("DELETE FROM track_tasks WHERE LOWER(track_key)='datacamp'")
    conn.execute(
        """UPDATE track_state SET status='Historical',weekly_target=0,
           metadata='{"active": false, "historical": true}',
           updated_at=CURRENT_TIMESTAMP WHERE LOWER(track_key)='datacamp'"""
    )

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
        """INSERT INTO settings(key,value) VALUES('unified_planner_version','10.28.0')
           ON CONFLICT(key) DO UPDATE SET value=excluded.value"""
    )
    conn.execute(
        """INSERT INTO settings(key,value) VALUES('navigation_layout_version','10.28.0')
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
