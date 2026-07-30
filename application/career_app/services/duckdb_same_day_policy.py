from __future__ import annotations

"""Make DuckDB availability and planner placement use the same chapter day."""

from datetime import date
from typing import Any

_INSTALLED = False
_CACHE_KEY = "duckdb_same_day_schedule:v10.42.0"


def _table_exists(conn: Any, table: str) -> bool:
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (str(table),)
        ).fetchone() is not None
    except Exception:
        return False


def _apply_same_day_catalog() -> None:
    from career_app.data import duckdb_exercises
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
    from career_app.services import duckdb_curriculum_policy as policy

    for internal_id in policy.ROADMAP_INTERNAL_ORDER:
        chapter = CHAPTER_BY_KEY[policy.TERMINAL_CHAPTER_BY_ID[int(internal_id)]]
        duckdb_exercises.DUCKDB_EXERCISES[int(internal_id)]["week"] = int(chapter.week)


def _install_schedule_override() -> None:
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
    from career_app.services import duckdb_curriculum_policy as policy

    def scheduled_date(conn: Any, internal_id: int) -> date:
        """Return the terminal chapter's own weekday, not the following day."""
        chapter = CHAPTER_BY_KEY[policy.TERMINAL_CHAPTER_BY_ID[int(internal_id)]]
        return chapter.scheduled_date(policy._program_start(conn))

    policy.scheduled_date = scheduled_date
    _apply_same_day_catalog()


def _refresh_once(conn: Any) -> None:
    from career_app.services import duckdb_curriculum_policy as policy

    policy._sync_task_metadata(conn)
    if _table_exists(conn, "settings"):
        row = conn.execute("SELECT value FROM settings WHERE key=?", (_CACHE_KEY,)).fetchone()
        if row is None:
            today = date.today().isoformat()
            if _table_exists(conn, "daily_focus"):
                conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (today,))
            conn.execute("DELETE FROM settings WHERE key=?", (f"daily_focus_snapshot_v2:{today}",))
            conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (_CACHE_KEY, "1"))
    conn.commit()


def install(CareerAccelerator: type) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _install_schedule_override()
    from career_app.services import duckdb_curriculum_policy as policy

    original_init = getattr(CareerAccelerator, "__init__", None)
    if callable(original_init):
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)
            _refresh_once(self.conn)
            try:
                self.refresh_dashboard(sync_tracks=False)
            except Exception:
                pass
        CareerAccelerator.__init__ = __init__

    # Chapter completion from a dashboard checkbox may redraw only the dashboard.
    # Synchronize DuckDB metadata before either refresh route so an exercise that
    # has just become available never continues to say "tomorrow" in Next Tasks.
    for name in ("refresh_dashboard", "refresh_all"):
        original = getattr(CareerAccelerator, name, None)
        if not callable(original) or getattr(original, "_duckdb_same_day_wrapped", False):
            continue
        def make_wrapper(method):
            def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
                try:
                    policy._sync_task_metadata(self.conn)
                    self.conn.commit()
                except Exception as exc:
                    setattr(self, "duckdb_same_day_sync_error", str(exc))
                return method(self, *args, **kwargs)
            wrapped._duckdb_same_day_wrapped = True  # type: ignore[attr-defined]
            return wrapped
        setattr(CareerAccelerator, name, make_wrapper(original))

    _INSTALLED = True
