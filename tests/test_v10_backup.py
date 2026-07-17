from __future__ import annotations

from datetime import datetime, timedelta
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from career_app.services.backup import create_backup, prune_backups_with_report


class BackupV10Tests(unittest.TestCase):
    def test_identical_sqlite_snapshots_are_not_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "data" / "career_accelerator.db"
            database.parent.mkdir(parents=True)
            conn = sqlite3.connect(database)
            conn.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY, value TEXT)")
            conn.execute("INSERT INTO sample(value) VALUES('first')")
            conn.commit()
            conn.close()

            first = create_backup(root)
            second = create_backup(root)
            self.assertEqual(first, second)
            self.assertEqual(len(list((root / "backups").glob("career_accelerator_*.db"))), 1)

            conn = sqlite3.connect(database)
            conn.execute("INSERT INTO sample(value) VALUES('second')")
            conn.commit()
            conn.close()
            # Ensure a distinct filename on fast filesystems.
            time.sleep(1.05)
            third = create_backup(root)
            self.assertNotEqual(first, third)
            self.assertEqual(len(list((root / "backups").glob("career_accelerator_*.db"))), 2)

    def test_retention_keeps_newest_daily_and_weekly_representatives(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            backup_dir = Path(temp)
            now = datetime.now()

            def make(name: str, age: timedelta, size: int = 16) -> Path:
                path = backup_dir / f"career_accelerator_{name}.db"
                path.write_bytes(b"x" * size)
                stamp = (now - age).timestamp()
                os.utime(path, (stamp, stamp))
                return path

            newest = [make(f"new_{index:02d}", timedelta(hours=index)) for index in range(12)]
            daily = [make(f"daily_{days}", timedelta(days=days, hours=2)) for days in range(1, 8)]
            weekly_a_new = make("week_a_new", timedelta(days=10))
            weekly_a_old = make("week_a_old", timedelta(days=11))
            weekly_b = make("week_b", timedelta(days=18))
            expired = make("expired", timedelta(days=40), size=64)

            fixture_stamps = {path: datetime.fromtimestamp(path.stat().st_mtime) for path in backup_dir.glob("career_accelerator_*.db")}
            report = prune_backups_with_report(backup_dir)
            remaining = set(backup_dir.glob("career_accelerator_*.db"))

            for path in newest[:10]:
                self.assertIn(path, remaining)
            # One newest representative should remain for every calendar day
            # represented in the seven-day retention window. Hourly newest files may
            # already satisfy the same day as a named daily fixture.
            daily_dates = {fixture_stamps[path].date() for path in daily}
            remaining_dates = {datetime.fromtimestamp(path.stat().st_mtime).date() for path in remaining}
            self.assertTrue(daily_dates.issubset(remaining_dates))

            # One newest representative should remain for each ISO week between
            # seven days and four weeks old.
            weekly_candidates = [
                path for path, stamp in fixture_stamps.items()
                if timedelta(days=7) < (now - stamp) <= timedelta(weeks=4)
            ]
            by_week = {}
            for path in weekly_candidates:
                stamp = fixture_stamps[path]
                key = (stamp.isocalendar().year, stamp.isocalendar().week)
                by_week.setdefault(key, []).append(path)
            for candidates in by_week.values():
                expected = max(candidates, key=lambda path: fixture_stamps[path])
                self.assertIn(expected, remaining)
                self.assertEqual(sum(path in remaining for path in candidates), 1)

            self.assertNotIn(expired, remaining)
            self.assertGreaterEqual(report["removed"], 2)
            self.assertGreaterEqual(report["recovered_bytes"], 64)


if __name__ == "__main__":
    unittest.main()
