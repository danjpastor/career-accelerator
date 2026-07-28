from __future__ import annotations

"""Readiness and catch-up tasks for DuckDB and SQL interview practice.

Required external learning is represented by durable DataCamp chapter tasks.
This module adds independent local practice after the matching chapter is
complete and never treats opening an external page as evidence of mastery.
"""

import re
import sqlite3
from pathlib import Path

from career_app.data.duckdb_exercises import DUCKDB_EXERCISES
from career_app.navigation import PAGE_LEARNING
from career_app.services.task_titles import title_case_task
from career_app.services import content_gates

SQL_PROBLEM_SCHEDULE = {
    "Data Science Skills": 3,
    "Pharmacy Analytics Part 1": 3,
    "Laptop vs. Mobile Viewership": 3,
    "Teams Power Users": 3,
    "Page With No Likes": 4,
    "Signup Activation Rate": 4,
    "Second Day Confirmation": 4,
    "Histogram of Tweets": 5,
    "Duplicate Job Listings": 5,
    "Second Highest Salary": 5,
    "Supercloud Customer": 5,
    "User's Third Transaction": 6,
    "Top Three Salaries": 6,
    "Odd and Even Measurements": 6,
    "Tweets' Rolling Averages": 7,
    "User Shopping Sprees": 7,
}

DUCKDB_CHAPTER_REQUIREMENTS = dict(content_gates.DUCKDB_TERMINAL_CHAPTER)

SCHEMA = """
CREATE TABLE IF NOT EXISTS roadmap_requirement_state (
    requirement_key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    due_week INTEGER NOT NULL,
    source_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Future',
    reason TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_roadmap_requirement_due
    ON roadmap_requirement_state(due_week,status);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _program_state(conn: sqlite3.Connection):
    return conn.execute("SELECT * FROM program_state WHERE id=1").fetchone()


def sql_problem_readiness(conn: sqlite3.Connection, title: str) -> dict:
    from career_app.services import tracks

    state = _program_state(conn)
    if state is None:
        return {
            "ready": False,
            "missing": ["Program progress"],
            "missing_names": ["Program progress"],
            "required_keys": [],
            "required_names": [],
            "required_all_of": [],
            "required_any_of": [],
            "evidence": {},
            "reason": "Program progress is unavailable.",
        }
    result = dict(tracks.sql_problem_readiness(conn, state, str(title)))
    missing = list(result.get("missing_names") or [])
    result["missing"] = missing
    result["reason"] = "" if not missing else "Complete " + ", ".join(missing) + " first."
    return result


def duckdb_readiness(conn: sqlite3.Connection, number: int) -> dict:
    from career_app.services import datacamp

    number = int(number)
    item = DUCKDB_EXERCISES[number]
    datacamp_gate = content_gates.gate_status(
        conn,
        content_gates.requirements_for_duckdb(number),
    )
    if _table_exists(conn, "duckdb_exercise_progress"):
        completed = conn.execute(
            "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=? AND status='Completed'",
            (number,),
        ).fetchone()
        if completed:
            return {
                "ready": True,
                "missing": [],
                "required_datacamp_keys": datacamp_gate["required_keys"],
                "required_datacamp_names": datacamp_gate["required_names"],
                "missing_datacamp_keys": [],
                "missing_datacamp_names": [],
                "reason": "Already completed.",
            }

    missing: list[str] = []
    for prior in dict(item.get("prerequisites") or {}).get("prior_exercises", ()):
        row = conn.execute(
            "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=? AND status='Completed'",
            (int(prior),),
        ).fetchone()
        if row is None:
            missing.append(f"DuckDB Exercise {int(prior):02d}")

    if not datacamp_gate["ready"]:
        missing.append(datacamp_gate["summary"])

    missing = list(dict.fromkeys(missing))
    return {
        "ready": not missing,
        "missing": missing,
        "required_datacamp_keys": datacamp_gate["required_keys"],
        "required_datacamp_names": datacamp_gate["required_names"],
        "missing_datacamp_keys": datacamp_gate["missing_keys"],
        "missing_datacamp_names": datacamp_gate["missing_names"],
        "reason": "" if not missing else "Complete " + ", ".join(missing) + " first.",
    }


def assert_duckdb_ready(conn: sqlite3.Connection, number: int) -> None:
    result = duckdb_readiness(conn, number)
    if not result["ready"]:
        raise PermissionError(result["reason"])


def assert_duckdb_ready_from_root(root: Path, number: int) -> None:
    db_path = Path(root) / "data" / "career_accelerator.db"
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert_duckdb_ready(conn, number)
    finally:
        conn.close()


def _catchup_sort_order(key: str) -> int:
    match = re.match(r"duckdb:(\d+)$", str(key))
    if match:
        return -760000 + int(match.group(1)) * 10
    title = str(key).split(":", 1)[-1]
    try:
        index = list(SQL_PROBLEM_SCHEDULE).index(title)
    except ValueError:
        index = 999
    return -750000 + index


def _upsert_requirement(conn, key, kind, title, due_week, source_id, status, reason):
    conn.execute(
        """INSERT INTO roadmap_requirement_state
           (requirement_key,kind,title,due_week,source_id,status,reason,updated_at)
           VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(requirement_key) DO UPDATE SET
             kind=excluded.kind,title=excluded.title,due_week=excluded.due_week,
             source_id=excluded.source_id,status=excluded.status,reason=excluded.reason,
             updated_at=CURRENT_TIMESTAMP""",
        (key, kind, title, int(due_week), source_id, status, reason),
    )


def _task_for_managed_key(conn, managed_key):
    return conn.execute(
        """SELECT s.id,s.completed FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key=? LIMIT 1""",
        (managed_key,),
    ).fetchone()


def _retire_obsolete_learning_tasks(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """SELECT s.id FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:lesson:%'
              OR m.managed_key LIKE 'roadmap_v1026:assessment:%'"""
    ).fetchall()
    ids = [int(row["id"]) for row in rows]
    for task_id in ids:
        if _table_exists(conn, "daily_focus"):
            conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        if _table_exists(conn, "track_tasks"):
            conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
        if _table_exists(conn, "task_workspaces"):
            conn.execute("DELETE FROM task_workspaces WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
    return len(ids)


def _stage_existing_orders(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """SELECT s.id FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:%' ORDER BY s.id"""
    ).fetchall()
    for row in rows:
        task_id = int(row["id"])
        conn.execute(
            "UPDATE sprint_tasks SET sort_order=? WHERE id=?",
            (-9000000 - task_id, task_id),
        )


def _create_or_update_catchup(
    conn,
    *,
    key,
    title,
    task_week,
    category,
    reason,
    minutes,
    starter_path=None,
    prerequisite_state="Ready",
    prerequisite_reason=None,
):
    managed_key = f"roadmap_v1026:{key}"
    existing = _task_for_managed_key(conn, managed_key)
    sort_order = _catchup_sort_order(key)
    if existing is None:
        cur = conn.execute(
            "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
            (task_week, sort_order, title_case_task(title)),
        )
        task_id = int(cur.lastrowid)
        conn.execute(
            """INSERT INTO task_metadata
               (task_id,status,priority,estimated_minutes,energy,destination,category,
                prerequisite_state,prerequisite_reason,description,definition_of_done,
                starter_path,managed_key)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                task_id,
                "Not Started",
                0,
                int(minutes),
                "Normal",
                PAGE_LEARNING,
                category,
                prerequisite_state,
                prerequisite_reason,
                reason,
                "Complete the linked practice requirement and save its evidence.",
                starter_path,
                managed_key,
            ),
        )
        return task_id

    task_id = int(existing["id"])
    conn.execute(
        "UPDATE sprint_tasks SET week=?,sort_order=?,label=?,completed=0 WHERE id=?",
        (task_week, sort_order, title_case_task(title), task_id),
    )
    conn.execute(
        """UPDATE task_metadata SET status='Not Started',priority=0,estimated_minutes=?,
           destination=?,category=?,prerequisite_state=?,prerequisite_reason=?,description=?,
           definition_of_done=?,starter_path=?,managed_key=? WHERE task_id=?""",
        (
            int(minutes),
            PAGE_LEARNING,
            category,
            prerequisite_state,
            prerequisite_reason,
            reason,
            "Complete the linked practice requirement and save its evidence.",
            starter_path,
            managed_key,
            task_id,
        ),
    )
    return task_id


def _complete_catchup(conn, key):
    row = _task_for_managed_key(conn, f"roadmap_v1026:{key}")
    if row is None:
        return
    task_id = int(row["id"])
    conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
    conn.execute(
        "UPDATE task_metadata SET status='Completed',prerequisite_state='Ready',prerequisite_reason=NULL WHERE task_id=?",
        (task_id,),
    )


def reconcile(conn: sqlite3.Connection, root=None) -> dict:
    del root
    ensure_schema(conn)
    retired = _retire_obsolete_learning_tasks(conn)
    _stage_existing_orders(conn)
    state = _program_state(conn)
    current_week = max(1, int(state["current_week"] if state else 1))
    overdue: list[str] = []
    completed: list[str] = []

    conn.execute("DELETE FROM roadmap_requirement_state WHERE kind NOT IN ('duckdb','sql_problem')")

    for number, item in DUCKDB_EXERCISES.items():
        due_week = int(item.get("week", 99))
        row = conn.execute(
            "SELECT status FROM duckdb_exercise_progress WHERE exercise_number=?",
            (int(number),),
        ).fetchone()
        done = bool(row and row["status"] == "Completed")
        readiness = duckdb_readiness(conn, number)
        status = "Completed" if done else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if done else (readiness["reason"] or f"Expected by Week {due_week}.")
        key = f"duckdb:{number}"
        _upsert_requirement(conn, key, "duckdb", item["title"], due_week, str(number), status, reason)
        if done:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=item["label"],
                task_week=due_week,
                category="SQL",
                reason=f"Expected by Week {due_week}. Complete this skill-gated DuckDB exercise.",
                minutes=int(item.get("minutes", 40)),
                starter_path=f"duckdb:{number}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    for title, due_week in SQL_PROBLEM_SCHEDULE.items():
        row = conn.execute(
            "SELECT status FROM sql_practice WHERE platform='DataLemur' AND title=?",
            (title,),
        ).fetchone()
        done = bool(row and row["status"] == "Completed")
        key = f"sql:{title}"
        readiness = sql_problem_readiness(conn, title)
        status = "Completed" if done else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if done else (readiness["reason"] or f"Expected by Week {due_week}.")
        _upsert_requirement(conn, key, "sql_problem", title, due_week, title, status, reason)
        if done:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=f"Solve {title}",
                task_week=due_week,
                category="SQL",
                reason=f"Expected by Week {due_week}. Complete this SQL interview problem in Learning Practice.",
                minutes=35,
                starter_path=f"sql-problem:{title}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    conn.commit()
    return {
        "current_week": current_week,
        "overdue": overdue,
        "completed": completed,
        "retired_legacy_learning_tasks": retired,
    }
