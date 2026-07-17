from __future__ import annotations

from datetime import date, timedelta
import sqlite3
import unittest
from unittest.mock import patch

from career_app.services import planner


SCHEMA = """
CREATE TABLE daily_focus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    focus_date TEXT NOT NULL,
    week INTEGER NOT NULL,
    position INTEGER NOT NULL,
    task_id INTEGER,
    source_key TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    track_key TEXT,
    target_key TEXT,
    is_extra INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(focus_date, position)
)
"""


class DailySnapshotV1005Tests(unittest.TestCase):
    def make_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(SCHEMA)
        return conn

    def insert_focus(
        self,
        conn: sqlite3.Connection,
        focus_date: str,
        title: str,
        *,
        position: int = 1,
        completed_at: str | None = None,
    ) -> None:
        conn.execute(
            """INSERT INTO daily_focus
               (focus_date,week,position,source_key,category,title,
                estimated_minutes,track_key,target_key,is_extra,completed_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (
                focus_date,
                1,
                position,
                f"test:{title}",
                "Learning",
                title,
                30,
                "google",
                "course-1-module-1",
                0,
                completed_at,
            ),
        )
        conn.commit()

    def test_rebuild_replaces_only_the_current_day(self) -> None:
        conn = self.make_connection()
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.insert_focus(conn, yesterday, "Yesterday")
        self.insert_focus(conn, today, "Old Today")

        def regenerate(*_args, **_kwargs):
            current_count = conn.execute(
                "SELECT COUNT(*) FROM daily_focus WHERE focus_date=?",
                (today,),
            ).fetchone()[0]
            self.assertEqual(current_count, 0)
            conn.execute(
                """INSERT INTO daily_focus
                   (focus_date,week,position,source_key,category,title,estimated_minutes)
                   VALUES(?,?,?,?,?,?,?)""",
                (today, 1, 1, "test:new", "SQL", "New Today", 25),
            )
            conn.commit()
            return [{"label": "New Today"}]

        with patch.object(planner, "intelligent_focus_plan", side_effect=regenerate):
            report = planner.rebuild_today_snapshot(conn, 1, (), {}, max_items=4)

        self.assertEqual(report["removed"], 1)
        self.assertEqual(report["created"], 1)
        self.assertEqual(
            conn.execute(
                "SELECT title FROM daily_focus WHERE focus_date=?",
                (today,),
            ).fetchone()[0],
            "New Today",
        )
        self.assertEqual(
            conn.execute(
                "SELECT title FROM daily_focus WHERE focus_date=?",
                (yesterday,),
            ).fetchone()[0],
            "Yesterday",
        )
        conn.close()

    def test_failed_rebuild_restores_the_original_snapshot(self) -> None:
        conn = self.make_connection()
        today = date.today().isoformat()
        self.insert_focus(
            conn,
            today,
            "Original Today",
            completed_at="2026-07-17 12:00:00",
        )

        with patch.object(
            planner,
            "intelligent_focus_plan",
            side_effect=RuntimeError("planned failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "planned failure"):
                planner.rebuild_today_snapshot(conn, 1, (), {}, max_items=4)

        restored = conn.execute(
            """SELECT title,completed_at
               FROM daily_focus
               WHERE focus_date=?""",
            (today,),
        ).fetchone()
        self.assertEqual(restored["title"], "Original Today")
        self.assertEqual(restored["completed_at"], "2026-07-17 12:00:00")
        conn.close()


if __name__ == "__main__":
    unittest.main()
