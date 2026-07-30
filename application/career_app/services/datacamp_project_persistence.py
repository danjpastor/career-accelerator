from __future__ import annotations

"""Durable completion evidence for DataCamp project tasks."""

from datetime import datetime
import sqlite3
from typing import Any, Callable

_INSTALLED = False


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (str(table),)
    ).fetchone() is not None


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS datacamp_project_completion (
            project_key TEXT PRIMARY KEY,
            task_id INTEGER,
            completed INTEGER NOT NULL DEFAULT 1,
            completed_at TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _project_key(project: dict[str, Any]) -> str:
    return str(project.get("project_key") or project.get("key") or "").strip()


def mark_complete(
    conn: sqlite3.Connection,
    project: dict[str, Any],
    task_id: int,
) -> None:
    ensure_schema(conn)
    key = _project_key(project)
    if not key:
        raise ValueError("The DataCamp project does not have a stable project key.")
    completed_at = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO datacamp_project_completion
            (project_key,task_id,completed,completed_at,updated_at)
        VALUES(?,?,1,?,CURRENT_TIMESTAMP)
        ON CONFLICT(project_key) DO UPDATE SET
            task_id=excluded.task_id,
            completed=1,
            completed_at=excluded.completed_at,
            updated_at=CURRENT_TIMESTAMP
        """,
        (key, int(task_id), completed_at),
    )
    if _table_exists(conn, "sprint_tasks"):
        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (int(task_id),))
    if _table_exists(conn, "task_metadata"):
        conn.execute(
            """
            UPDATE task_metadata
            SET status='Completed',prerequisite_state='Ready',
                prerequisite_reason='Completed.',deferred_until=NULL
            WHERE task_id=?
            """,
            (int(task_id),),
        )
    if _table_exists(conn, "daily_focus"):
        conn.execute(
            """
            UPDATE daily_focus
            SET completed_at=COALESCE(completed_at,CURRENT_TIMESTAMP)
            WHERE task_id=?
            """,
            (int(task_id),),
        )
    conn.commit()


def restore_completions(conn: sqlite3.Connection) -> int:
    ensure_schema(conn)
    if not _table_exists(conn, "datacamp_project_tasks"):
        return 0
    rows = conn.execute(
        """
        SELECT c.project_key,c.task_id AS saved_task_id,d.task_id AS current_task_id
        FROM datacamp_project_completion c
        LEFT JOIN datacamp_project_tasks d ON d.project_key=c.project_key
        WHERE c.completed=1
        """
    ).fetchall()
    restored = 0
    for row in rows:
        try:
            current_id = int(row["current_task_id"] or row["saved_task_id"])
            project_key = str(row["project_key"])
        except Exception:
            project_key = str(row[0])
            current_id = int(row[2] or row[1])
        if not current_id:
            continue
        if _table_exists(conn, "sprint_tasks"):
            cursor = conn.execute(
                "UPDATE sprint_tasks SET completed=1 WHERE id=? AND COALESCE(completed,0)=0",
                (current_id,),
            )
            restored += int(cursor.rowcount or 0)
        if _table_exists(conn, "task_metadata"):
            conn.execute(
                """
                UPDATE task_metadata
                SET status='Completed',prerequisite_state='Ready',
                    prerequisite_reason='Completed.',deferred_until=NULL
                WHERE task_id=?
                """,
                (current_id,),
            )
        conn.execute(
            "UPDATE datacamp_project_completion SET task_id=?,updated_at=CURRENT_TIMESTAMP WHERE project_key=?",
            (current_id, project_key),
        )
    conn.commit()
    return restored


def install(CareerAccelerator: type) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    from career_app.services import datacamp_projects

    original_sync: Callable[..., Any] = datacamp_projects.sync_tasks
    if not getattr(original_sync, "_project_persistence_wrapped", False):
        def sync_tasks(conn: sqlite3.Connection, *args: Any, **kwargs: Any) -> Any:
            ensure_schema(conn)
            result = original_sync(conn, *args, **kwargs)
            restore_completions(conn)
            return result
        sync_tasks._project_persistence_wrapped = True  # type: ignore[attr-defined]
        datacamp_projects.sync_tasks = sync_tasks

    original_init = getattr(CareerAccelerator, "__init__", None)
    if callable(original_init) and not getattr(original_init, "_project_persistence_wrapped", False):
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            try:
                datacamp_projects.sync_tasks(self.conn, getattr(self, "state", None))
                restore_completions(self.conn)
            except Exception as exc:
                setattr(self, "datacamp_project_restore_error", str(exc))
        __init__._project_persistence_wrapped = True  # type: ignore[attr-defined]
        CareerAccelerator.__init__ = __init__

    original_refresh_all = getattr(CareerAccelerator, "refresh_all", None)
    if callable(original_refresh_all) and not getattr(original_refresh_all, "_project_persistence_wrapped", False):
        def refresh_all(self: Any, *args: Any, **kwargs: Any) -> Any:
            result = original_refresh_all(self, *args, **kwargs)
            try:
                restored = restore_completions(self.conn)
                if restored:
                    try:
                        self.refresh_dashboard(sync_tracks=False)
                    except TypeError:
                        self.refresh_dashboard()
            except Exception as exc:
                setattr(self, "datacamp_project_restore_error", str(exc))
            return result
        refresh_all._project_persistence_wrapped = True  # type: ignore[attr-defined]
        CareerAccelerator.refresh_all = refresh_all

    original_complete = getattr(CareerAccelerator, "complete_task", None)
    if callable(original_complete) and not getattr(original_complete, "_project_persistence_wrapped", False):
        def complete_task(self: Any, task_id: int, *, refresh_scope: str = "all") -> Any:
            project = datacamp_projects.project_for_task(self.conn, int(task_id))
            if project is None:
                return original_complete(self, task_id, refresh_scope=refresh_scope)

            mark_complete(self.conn, project, int(task_id))
            # Re-run synchronization and then restore from the durable key. This
            # survives task-row reuse, track repair, and a full application close.
            datacamp_projects.sync_tasks(self.conn, getattr(self, "state", None))
            restore_completions(self.conn)
            try:
                if refresh_scope == "dashboard":
                    self.refresh_dashboard(sync_tracks=False)
                    refresh_linked = getattr(self, "_refresh_linked_task_surfaces", None)
                    if callable(refresh_linked):
                        refresh_linked(int(task_id))
                else:
                    self.refresh_all()
            except TypeError:
                if refresh_scope == "dashboard":
                    self.refresh_dashboard()
                else:
                    self.refresh_all()
            restore_completions(self.conn)
            if refresh_scope != "dashboard":
                try:
                    self.refresh_dashboard(sync_tracks=False)
                except Exception:
                    pass
            notify = getattr(self, "_notify", None)
            if callable(notify):
                notify("DataCamp project completed and saved.", 5200)
            return None
        complete_task._project_persistence_wrapped = True  # type: ignore[attr-defined]
        CareerAccelerator.complete_task = complete_task

    _INSTALLED = True
