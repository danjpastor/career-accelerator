from __future__ import annotations

"""Small compatibility layer for durable planner mutations.

Task selection lives in :mod:`unified_tasks`. These helpers remain separate so
older databases can still be repaired without reviving any retired learning
provider or recommendation engine.
"""

from datetime import date, timedelta
import re

from career_app.navigation import destination_for

GOOGLE_COURSE_TASK = re.compile(r"^\[Google Course (\d+)\]", re.IGNORECASE)


def _table_exists(conn, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _infer(label: str) -> dict:
    text = str(label or "").casefold()
    if "google" in text or "certificate" in text:
        category, minutes, priority, energy = "Learning", 45, 0, "Normal"
    elif "duckdb" in text or "sql" in text or "datalemur" in text:
        category, minutes, priority, energy = "SQL", 40, 2, "Normal"
    elif "portfolio" in text or "project" in text:
        category, minutes, priority, energy = "Portfolio", 60, 2, "Deep"
    elif "review" in text or "retrospective" in text:
        category, minutes, priority, energy = "Review", 30, 3, "Light"
    else:
        category, minutes, priority, energy = "General", 30, 3, "Normal"
    return {
        "category": category,
        "minutes": minutes,
        "priority": priority,
        "energy": energy,
        "destination": destination_for(category=category),
    }


def seed(conn) -> None:
    """Backfill metadata only for genuine task rows that predate the planner."""
    rows = conn.execute("SELECT id,label,completed FROM sprint_tasks").fetchall()
    for row in rows:
        existing = conn.execute(
            "SELECT 1 FROM task_metadata WHERE task_id=?", (int(row["id"]),)
        ).fetchone()
        if existing:
            continue
        meta = _infer(row["label"])
        conn.execute(
            """INSERT INTO task_metadata
               (task_id,status,priority,estimated_minutes,energy,destination,category,
                prerequisite_state,description,definition_of_done)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                int(row["id"]),
                "Completed" if bool(row["completed"]) else "Not Started",
                meta["priority"],
                meta["minutes"],
                meta["energy"],
                meta["destination"],
                meta["category"],
                "Ready",
                "",
                "",
            ),
        )
    conn.commit()


def sync_google_course_progress(conn, current_course: int) -> int:
    """Mark obsolete course-specific rows complete when progress has advanced."""
    current_course = max(1, int(current_course))
    rows = conn.execute(
        """SELECT s.id,s.label,s.completed,m.status
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id"""
    ).fetchall()
    changed = 0
    for row in rows:
        match = GOOGLE_COURSE_TASK.match(str(row["label"] or ""))
        if not match or int(match.group(1)) >= current_course:
            continue
        if not bool(row["completed"]) or str(row["status"]) != "Completed":
            conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (row["id"],))
            conn.execute(
                "UPDATE task_metadata SET status='Completed',deferred_until=NULL WHERE task_id=?",
                (row["id"],),
            )
            changed += 1
    if changed:
        conn.commit()
    return changed


def repair_persisted_planner_data(conn, week: int) -> None:
    """Remove dangling focus rows and normalize the active week's snapshot."""
    del week
    if not _table_exists(conn, "daily_focus"):
        return
    conn.execute(
        """DELETE FROM daily_focus
           WHERE task_id IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM sprint_tasks s WHERE s.id=daily_focus.task_id)"""
    )
    # Provider migrations can leave stale manually generated duplicates. Keep
    # the first canonical row for each task and date while preserving history.
    duplicates = conn.execute(
        """SELECT focus_date,task_id,MIN(id) AS keep_id
           FROM daily_focus WHERE task_id IS NOT NULL
           GROUP BY focus_date,task_id HAVING COUNT(*)>1"""
    ).fetchall()
    for row in duplicates:
        conn.execute(
            "DELETE FROM daily_focus WHERE focus_date=? AND task_id=? AND id<>?",
            (row["focus_date"], row["task_id"], row["keep_id"]),
        )
    conn.commit()


def defer(conn, task_id: int, days: int = 1) -> str:
    """Defer one incomplete task without changing its completion evidence."""
    target = (date.today() + timedelta(days=max(1, int(days)))).isoformat()
    conn.execute(
        """UPDATE task_metadata
           SET deferred_until=?,status=CASE WHEN status='Completed' THEN status ELSE 'Deferred' END
           WHERE task_id=?""",
        (target, int(task_id)),
    )
    conn.execute(
        "DELETE FROM daily_focus WHERE focus_date=? AND task_id=? AND completed_at IS NULL",
        (date.today().isoformat(), int(task_id)),
    )
    conn.commit()
    return target


def mark_focus_task_completed(conn, task_id: int) -> None:
    """Freeze today's visible assignment as completed."""
    if _table_exists(conn, "daily_focus"):
        conn.execute(
            """UPDATE daily_focus
               SET completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP)
               WHERE focus_date=? AND task_id=?""",
            (date.today().isoformat(), int(task_id)),
        )
    conn.commit()
