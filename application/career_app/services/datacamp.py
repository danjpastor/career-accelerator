from __future__ import annotations

"""DataCamp chapter task migration, scheduling, and progress helpers."""

from datetime import date, datetime
import json
from pathlib import Path
import sqlite3

from career_app.data.datacamp_curriculum import (
    DATACAMP_CHAPTERS,
    DataCampChapter,
    chapter_for_key,
    iter_before,
)
from career_app.navigation import PAGE_LEARNING

MANAGED_PREFIX = "datacamp:"
SORT_BAND = -300000


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS datacamp_chapter_progress (
               chapter_key TEXT PRIMARY KEY,
               course_name TEXT NOT NULL,
               chapter_number INTEGER NOT NULL,
               chapter_name TEXT NOT NULL,
               scheduled_date TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'Not Started',
               completed_date TEXT,
               task_id INTEGER,
               updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY(task_id) REFERENCES sprint_tasks(id) ON DELETE SET NULL
           )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_datacamp_progress_task ON datacamp_chapter_progress(task_id)"
    )


def _program_start(conn: sqlite3.Connection) -> date:
    row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
    try:
        return date.fromisoformat(str(row["start_date"]))
    except (TypeError, ValueError, KeyError):
        return date.today()


def _task_for_key(conn: sqlite3.Connection, key: str):
    return conn.execute(
        """SELECT s.id,s.completed,m.status,m.starter_path
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key=? LIMIT 1""",
        (f"{MANAGED_PREFIX}{key}",),
    ).fetchone()


def purge_academy(conn: sqlite3.Connection) -> dict[str, int]:
    """Remove active and historical Academy-owned records without conversion."""
    removed = {"tasks": 0, "tables": 0, "events": 0, "evidence": 0, "settings": 0}

    task_ids: set[int] = set()
    if _table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata"):
        rows = conn.execute(
            """SELECT DISTINCT s.id
               FROM sprint_tasks s
               LEFT JOIN task_metadata m ON m.task_id=s.id
               LEFT JOIN track_tasks tt ON tt.task_id=s.id
               WHERE LOWER(COALESCE(tt.track_key,''))='academy'
                  OR LOWER(COALESCE(m.managed_key,'')) LIKE '%academy%'
                  OR LOWER(COALESCE(m.managed_key,'')) LIKE 'roadmap_v1026:lesson:%'
                  OR LOWER(COALESCE(m.managed_key,'')) LIKE 'roadmap_v1026:assessment:%'
                  OR LOWER(COALESCE(m.starter_path,'')) LIKE 'academy:%'
                  OR LOWER(COALESCE(s.label,'')) LIKE '%accelerator academy%'
                  OR LOWER(COALESCE(s.label,'')) LIKE '%academy knowledge check%'"""
        ).fetchall()
        task_ids = {int(row["id"]) for row in rows}

    for task_id in task_ids:
        if _table_exists(conn, "daily_focus"):
            conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        if _table_exists(conn, "track_tasks"):
            conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
        if _table_exists(conn, "task_workspaces"):
            conn.execute("DELETE FROM task_workspaces WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
    removed["tasks"] = len(task_ids)

    if _table_exists(conn, "daily_focus"):
        conn.execute(
            """DELETE FROM daily_focus
               WHERE LOWER(COALESCE(track_key,''))='academy'
                  OR LOWER(COALESCE(source_key,'')) LIKE '%academy%'
                  OR LOWER(COALESCE(title,'')) LIKE '%academy%'"""
        )
    if _table_exists(conn, "track_tasks"):
        conn.execute("DELETE FROM track_tasks WHERE LOWER(track_key)='academy'")
    if _table_exists(conn, "roadmap_task_archive"):
        conn.execute(
            """DELETE FROM roadmap_task_archive
               WHERE LOWER(COALESCE(track_key,''))='academy'
                  OR LOWER(COALESCE(label,'')) LIKE '%academy%'
                  OR LOWER(COALESCE(reason,'')) LIKE '%academy%'
                  OR LOWER(COALESCE(metadata,'')) LIKE '%academy%'"""
        )
    if _table_exists(conn, "track_events"):
        removed["events"] = max(
            0, conn.execute("DELETE FROM track_events WHERE LOWER(track_key)='academy'").rowcount
        )
    if _table_exists(conn, "track_state"):
        conn.execute("DELETE FROM track_state WHERE LOWER(track_key)='academy'")
    if _table_exists(conn, "task_workspaces"):
        conn.execute(
            """DELETE FROM task_workspaces
               WHERE LOWER(COALESCE(track_key,''))='academy'
                  OR LOWER(COALESCE(workspace_key,'')) LIKE 'academy:%'
                  OR LOWER(COALESCE(workspace_type,'')) LIKE '%academy%'"""
        )
    if _table_exists(conn, "evidence"):
        removed["evidence"] += max(
            0,
            conn.execute(
                """DELETE FROM evidence
                   WHERE LOWER(COALESCE(source_type,'')) LIKE '%academy%'
                      OR LOWER(COALESCE(source_name,'')) LIKE '%academy%'"""
            ).rowcount,
        )
    if _table_exists(conn, "skill_evidence"):
        removed["evidence"] += max(
            0,
            conn.execute(
                """DELETE FROM skill_evidence
                   WHERE LOWER(COALESCE(source_type,'')) LIKE '%academy%'
                      OR LOWER(COALESCE(source_name,'')) LIKE '%academy%'
                      OR LOWER(COALESCE(evidence,'')) LIKE '%academy%'"""
            ).rowcount,
        )
    if _table_exists(conn, "skill_state"):
        columns = {row[1] for row in conn.execute("PRAGMA table_info(skill_state)")}
        source_cols = [name for name in ("source", "source_type", "evidence") if name in columns]
        if source_cols:
            clause = " OR ".join(f"LOWER(COALESCE({name},'')) LIKE '%academy%'" for name in source_cols)
            conn.execute(f"DELETE FROM skill_state WHERE {clause}")
    if _table_exists(conn, "settings"):
        removed["settings"] = max(
            0,
            conn.execute(
                """DELETE FROM settings
                   WHERE LOWER(key) LIKE '%academy%'
                      OR LOWER(COALESCE(value,'')) LIKE '%academy%'
                      OR key LIKE 'daily_focus_snapshot_v2:%'"""
            ).rowcount,
        )

    # Preserve learner-authored reflections while removing the retired provider
    # name from generated summaries and reusable retrospective workspace text.
    for table, column in (
        ("retrospective_notes", "note"),
        ("weekly_summaries", "summary"),
        ("task_workspaces", "content"),
    ):
        if not _table_exists(conn, table):
            continue
        columns = {str(row[1]) for row in conn.execute(f'PRAGMA table_info("{table}")')}
        if column not in columns:
            continue
        conn.execute(
            f"UPDATE \"{table}\" "
            f"SET \"{column}\"=REPLACE(REPLACE(\"{column}\", "
            "'Accelerator Academy','Career Accelerator'),'Academy','Career Accelerator') "
            f"WHERE LOWER(COALESCE(\"{column}\",'')) LIKE '%academy%'"
        )

    table_rows = conn.execute(
        """SELECT name FROM sqlite_master
           WHERE type='table' AND LOWER(name) LIKE 'academy_%'"""
    ).fetchall()
    for row in table_rows:
        table = str(row["name"])
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        removed["tables"] += 1

    return removed


def _retire_noncanonical_datacamp_tasks(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """SELECT DISTINCT s.id
           FROM sprint_tasks s
           LEFT JOIN task_metadata m ON m.task_id=s.id
           LEFT JOIN track_tasks tt ON tt.task_id=s.id
           WHERE (LOWER(COALESCE(tt.track_key,''))='datacamp'
                  OR LOWER(COALESCE(s.label,'')) LIKE '%datacamp%')
             AND LOWER(COALESCE(m.managed_key,'')) NOT LIKE 'datacamp:%'"""
    ).fetchall()
    for row in rows:
        task_id = int(row["id"])
        if _table_exists(conn, "daily_focus"):
            conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        if _table_exists(conn, "track_tasks"):
            conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
        if _table_exists(conn, "task_workspaces"):
            conn.execute("UPDATE task_workspaces SET task_id=NULL WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
    return len(rows)


def _retire_obsolete_chapter_tasks(conn: sqlite3.Connection) -> int:
    """Remove managed chapter rows that no longer exist in the live curriculum.

    DataCamp replaced the four-chapter Joining Data in SQL course with a
    two-chapter version in July 2026. Reconciliation must remove the obsolete
    Chapter 3/4 tasks instead of leaving them behind as ghost roadmap items.
    Existing progress for chapter keys that remain canonical is preserved.
    """
    canonical = {str(chapter.key) for chapter in DATACAMP_CHAPTERS}
    rows = conn.execute(
        """SELECT m.task_id,m.managed_key
           FROM task_metadata m
           WHERE LOWER(COALESCE(m.managed_key,'')) LIKE 'datacamp:%'"""
    ).fetchall()
    retired = 0
    for row in rows:
        managed_key = str(row["managed_key"] or "")
        chapter_key = managed_key.split(":", 1)[1] if ":" in managed_key else ""
        if chapter_key in canonical:
            continue
        task_id = int(row["task_id"])
        if _table_exists(conn, "task_day_promotions"):
            conn.execute("DELETE FROM task_day_promotions WHERE task_id=?", (task_id,))
        if _table_exists(conn, "daily_focus"):
            conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
        if _table_exists(conn, "track_tasks"):
            conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
        if _table_exists(conn, "task_workspaces"):
            conn.execute("UPDATE task_workspaces SET task_id=NULL WHERE task_id=?", (task_id,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
        retired += 1

    if _table_exists(conn, "datacamp_chapter_progress"):
        progress_rows = conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress"
        ).fetchall()
        obsolete = [
            str(row["chapter_key"])
            for row in progress_rows
            if str(row["chapter_key"]) not in canonical
        ]
        for chapter_key in obsolete:
            conn.execute(
                "DELETE FROM datacamp_chapter_progress WHERE chapter_key=?",
                (chapter_key,),
            )
    return retired


def reconcile(conn: sqlite3.Connection) -> dict[str, int]:
    """Seed/update one durable task per required chapter and sync progress."""
    ensure_schema(conn)
    start = _program_start(conn)
    stats = {"created": 0, "updated": 0, "completed": 0, "retired": 0}
    stats["retired"] = (
        _retire_noncanonical_datacamp_tasks(conn)
        + _retire_obsolete_chapter_tasks(conn)
    )

    for sequence, chapter in enumerate(DATACAMP_CHAPTERS, start=1):
        due = chapter.scheduled_date(start).isoformat()
        managed_key = f"{MANAGED_PREFIX}{chapter.key}"
        existing = _task_for_key(conn, chapter.key)
        sort_order = SORT_BAND + sequence
        description = (
            f"Complete Chapter {chapter.chapter_number}, {chapter.chapter_name}, in "
            f"DataCamp's {chapter.course_name} course. The Open button launches this "
            "exact chapter in your web browser."
        )
        definition = (
            "Finish the assigned DataCamp chapter, then deliberately mark this task "
            "complete in Career Accelerator. Opening DataCamp does not complete it."
        )
        if existing is None:
            cur = conn.execute(
                "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
                (chapter.week, sort_order, chapter.label),
            )
            task_id = int(cur.lastrowid)
            conn.execute(
                """INSERT INTO task_metadata
                   (task_id,status,priority,estimated_minutes,energy,deferred_until,
                    destination,category,prerequisite_state,prerequisite_reason,
                    description,definition_of_done,starter_path,managed_key)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    task_id,
                    "Not Started",
                    1,
                    chapter.estimated_minutes,
                    "Normal",
                    due,
                    PAGE_LEARNING,
                    "Learning",
                    "Ready",
                    None,
                    description,
                    definition,
                    chapter.url,
                    managed_key,
                ),
            )
            stats["created"] += 1
        else:
            task_id = int(existing["id"])
            completed = int(existing["completed"] or 0)
            status = "Completed" if completed else "Not Started"
            conn.execute(
                "UPDATE sprint_tasks SET week=?,sort_order=?,label=? WHERE id=?",
                (chapter.week, sort_order, chapter.label, task_id),
            )
            conn.execute(
                """UPDATE task_metadata SET status=?,priority=1,estimated_minutes=?,
                   energy='Normal',deferred_until=?,destination=?,category='Learning',
                   prerequisite_state='Ready',prerequisite_reason=NULL,description=?,
                   definition_of_done=?,starter_path=?,managed_key=? WHERE task_id=?""",
                (
                    status,
                    chapter.estimated_minutes,
                    None if completed else due,
                    PAGE_LEARNING,
                    description,
                    definition,
                    chapter.url,
                    managed_key,
                    task_id,
                ),
            )
            stats["updated"] += 1

        # Daily Focus is a frozen snapshot, so keep its visible title aligned
        # with the canonical chapter title when presentation wording changes.
        if _table_exists(conn, "daily_focus"):
            conn.execute(
                "UPDATE daily_focus SET title=? WHERE task_id=?",
                (chapter.label, task_id),
            )

        row = conn.execute("SELECT completed FROM sprint_tasks WHERE id=?", (task_id,)).fetchone()
        completed = bool(row and row["completed"])
        completed_date = None
        old = conn.execute(
            "SELECT completed_date FROM datacamp_chapter_progress WHERE chapter_key=?",
            (chapter.key,),
        ).fetchone()
        if completed:
            completed_date = str(old["completed_date"] or date.today().isoformat()) if old else date.today().isoformat()
            stats["completed"] += 1
        conn.execute(
            """INSERT INTO datacamp_chapter_progress
               (chapter_key,course_name,chapter_number,chapter_name,scheduled_date,
                status,completed_date,task_id,updated_at)
               VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(chapter_key) DO UPDATE SET
                   course_name=excluded.course_name,
                   chapter_number=excluded.chapter_number,
                   chapter_name=excluded.chapter_name,
                   scheduled_date=excluded.scheduled_date,
                   status=excluded.status,
                   completed_date=excluded.completed_date,
                   task_id=excluded.task_id,
                   updated_at=CURRENT_TIMESTAMP""",
            (
                chapter.key,
                chapter.course_name,
                chapter.chapter_number,
                chapter.chapter_name,
                due,
                "Completed" if completed else "Not Started",
                completed_date,
                task_id,
            ),
        )

    # DataCamp is an active supplemental summary track, but chapter tasks remain
    # ordinary sprint tasks so multiple chapters can be assigned on one day.
    progress_rows = {
        str(row["chapter_key"]): row
        for row in conn.execute(
            "SELECT chapter_key,status,scheduled_date FROM datacamp_chapter_progress"
        ).fetchall()
    }
    complete = sum(
        1 for row in progress_rows.values() if str(row["status"]) == "Completed"
    )
    total = len(DATACAMP_CHAPTERS)
    next_chapter = next(
        (
            chapter
            for chapter in DATACAMP_CHAPTERS
            if str(progress_rows[chapter.key]["status"]) != "Completed"
        ),
        None,
    )
    state_row = conn.execute(
        "SELECT current_week FROM program_state WHERE id=1"
    ).fetchone()
    current_week = max(1, int(state_row["current_week"] if state_row else 1))
    week_chapters = [chapter for chapter in DATACAMP_CHAPTERS if chapter.week == current_week]
    weekly_target = len(week_chapters)
    weekly_completed = sum(
        str(progress_rows[chapter.key]["status"]) == "Completed"
        for chapter in week_chapters
    )
    metadata = {
        "active": True,
        "provider": "DataCamp",
        "completed_chapters": int(complete),
        "total_chapters": total,
        "current_week": current_week,
        "weekly_completed": int(weekly_completed),
        "weekly_target": int(weekly_target),
        "next_chapter": next_chapter.chapter_name if next_chapter else None,
        "next_course": next_chapter.course_name if next_chapter else None,
        "next_date": (
            str(progress_rows[next_chapter.key]["scheduled_date"])
            if next_chapter else None
        ),
    }
    conn.execute(
        """INSERT INTO track_state(track_key,display_name,position,subposition,weekly_target,status,metadata,updated_at)
           VALUES('datacamp','DataCamp',?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(track_key) DO UPDATE SET display_name='DataCamp',position=excluded.position,
               subposition=excluded.subposition,weekly_target=excluded.weekly_target,
               status=excluded.status,metadata=excluded.metadata,updated_at=CURRENT_TIMESTAMP""",
        (
            int(complete),
            total,
            int(weekly_target),
            "Completed" if complete >= total else "Active",
            json.dumps(metadata, sort_keys=True),
        ),
    )
    conn.execute("DELETE FROM track_tasks WHERE LOWER(track_key)='datacamp'")
    conn.commit()
    return stats


def chapter_key_from_task(task: dict) -> str | None:
    managed = str(task.get("managed_key") or "")
    if managed.startswith(MANAGED_PREFIX):
        return managed[len(MANAGED_PREFIX):]
    return None


def chapter_for_task(task: dict) -> DataCampChapter | None:
    return chapter_for_key(chapter_key_from_task(task))


def readiness(conn: sqlite3.Connection, task: dict, *, today: date | None = None) -> tuple[bool, str]:
    chapter = chapter_for_task(task)
    if chapter is None:
        return False, "DataCamp chapter metadata is unavailable."
    today = today or date.today()
    start = _program_start(conn)
    scheduled = chapter.scheduled_date(start)
    if scheduled > today:
        return False, f"Scheduled for {scheduled.strftime('%A, %B')} {scheduled.day}."

    previous = list(iter_before(chapter))
    incomplete: list[DataCampChapter] = []
    for item in previous:
        row = conn.execute(
            "SELECT status FROM datacamp_chapter_progress WHERE chapter_key=?",
            (item.key,),
        ).fetchone()
        if row is None or str(row["status"]) != "Completed":
            incomplete.append(item)
    if incomplete:
        first = incomplete[0]
        return False, (
            f"Complete {first.course_name} — Chapter {first.chapter_number}: "
            f"{first.chapter_name} first."
        )
    return True, ""


def current_ready_task(conn: sqlite3.Connection, *, today: date | None = None):
    ensure_schema(conn)
    today = today or date.today()
    rows = conn.execute(
        """SELECT s.id,s.week,s.label,s.completed,m.*
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'datacamp:%' AND s.completed=0
           ORDER BY m.deferred_until,s.sort_order,s.id"""
    ).fetchall()
    for row in rows:
        task = {key: row[key] for key in row.keys()}
        ok, _reason = readiness(conn, task, today=today)
        if ok:
            return row
    return None


def chapter_url_for_task(conn: sqlite3.Connection, task_id: int) -> str | None:
    row = conn.execute(
        """SELECT starter_path,managed_key FROM task_metadata WHERE task_id=?""",
        (int(task_id),),
    ).fetchone()
    if row is None or not str(row["managed_key"] or "").startswith(MANAGED_PREFIX):
        return None
    url = str(row["starter_path"] or "").strip()
    return url if url.startswith("https://campus.datacamp.com/") else None


def mark_task_complete(conn: sqlite3.Connection, task_id: int) -> None:
    row = conn.execute(
        "SELECT managed_key FROM task_metadata WHERE task_id=?", (int(task_id),)
    ).fetchone()
    if row is None or not str(row["managed_key"] or "").startswith(MANAGED_PREFIX):
        return
    key = str(row["managed_key"])[len(MANAGED_PREFIX):]
    conn.execute(
        """UPDATE datacamp_chapter_progress SET status='Completed',
           completed_date=COALESCE(completed_date,?),updated_at=CURRENT_TIMESTAMP
           WHERE chapter_key=?""",
        (date.today().isoformat(), key),
    )
    conn.commit()


def mark_task_incomplete(
    conn: sqlite3.Connection,
    task_id: int,
    *,
    enforce_sequence: bool = True,
) -> None:
    """Restore one chapter to unfinished in every linked progress layer."""
    row = conn.execute(
        "SELECT managed_key FROM task_metadata WHERE task_id=?", (int(task_id),)
    ).fetchone()
    if row is None or not str(row["managed_key"] or "").startswith(MANAGED_PREFIX):
        return
    key = str(row["managed_key"])[len(MANAGED_PREFIX):]
    chapter = chapter_for_key(key)
    if chapter is None:
        raise ValueError("The selected DataCamp chapter is no longer in the curriculum.")

    if enforce_sequence:
        target_index = next(
            index for index, item in enumerate(DATACAMP_CHAPTERS) if item.key == key
        )
        later_completed = conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress WHERE status='Completed'"
        ).fetchall()
        completed_keys = {str(item["chapter_key"]) for item in later_completed}
        later = [
            item for item in DATACAMP_CHAPTERS[target_index + 1:]
            if item.key in completed_keys
        ]
        if later:
            latest = later[-1]
            raise ValueError(
                "Undo the later DataCamp chapter first: "
                f"{latest.course_name}, Chapter {latest.chapter_number}."
            )

    due = chapter.scheduled_date(_program_start(conn)).isoformat()
    conn.execute("UPDATE sprint_tasks SET completed=0 WHERE id=?", (int(task_id),))
    conn.execute(
        """UPDATE task_metadata
           SET status='Not Started',deferred_until=?,prerequisite_state='Ready',
               prerequisite_reason=NULL
           WHERE task_id=?""",
        (due, int(task_id)),
    )
    conn.execute(
        """UPDATE datacamp_chapter_progress
           SET status='Not Started',completed_date=NULL,updated_at=CURRENT_TIMESTAMP
           WHERE chapter_key=?""",
        (key,),
    )


def portfolio_ready(conn: sqlite3.Connection) -> bool:
    ensure_schema(conn)
    total = conn.execute("SELECT COUNT(*) FROM datacamp_chapter_progress").fetchone()[0]
    complete = conn.execute(
        "SELECT COUNT(*) FROM datacamp_chapter_progress WHERE status='Completed'"
    ).fetchone()[0]
    final_audit = conn.execute(
        "SELECT 1 FROM duckdb_exercise_progress "
        "WHERE exercise_number=18 AND status='Completed'"
    ).fetchone()
    return (
        total == len(DATACAMP_CHAPTERS)
        and complete == total
        and final_audit is not None
    )


def remove_academy_files(root: Path) -> list[str]:
    """Used by installers/tests; runtime never needs the retired Academy files."""
    targets = (
        root / "academy_workspace",
        root / "application" / "career_app" / "academy",
        root / "application" / "career_app" / "ui" / "academy.py",
    )
    return [str(path) for path in targets if path.exists()]
