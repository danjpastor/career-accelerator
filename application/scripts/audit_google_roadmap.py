#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile


def _conn(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the topic-aligned Google Certificate roadmap.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "application"))

    from career_app.data import google_certificate_curriculum as curriculum
    from career_app.database import state
    from career_app.services import tracks, unified_tasks, weekly_checks

    errors = list(curriculum.validate())
    expected_counts = {1: 4, 2: 4, 3: 5, 4: 6, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4}
    if curriculum.COURSE_MODULE_COUNTS != expected_counts:
        errors.append(f"Course/module counts differ: {curriculum.COURSE_MODULE_COUNTS}")
    if len(curriculum.GOOGLE_MODULES) != 39:
        errors.append(f"Expected 39 Google modules; found {len(curriculum.GOOGLE_MODULES)}")
    if curriculum.module(7, 1).week != 8:
        errors.append("Course 7 Module 1 is not assigned to Week 8.")
    if curriculum.module(1, 1).week != 1:
        errors.append("Course 1 Module 1 is not assigned to Week 1.")

    source_db = (args.db or (root / "data" / "career_accelerator.db")).resolve()
    if not source_db.is_file():
        errors.append(f"Database is missing: {source_db}")
    else:
        folder = Path(tempfile.mkdtemp(prefix="career-accelerator-google-roadmap-"))
        db = folder / "career_accelerator.db"
        shutil.copy2(source_db, db)
        conn = _conn(db)
        try:
            # Exact current-user regression: Python is the next module in Week 3.
            conn.execute("UPDATE program_state SET current_week=3,google_course=7,google_module=1 WHERE id=1")
            conn.execute("DELETE FROM track_events WHERE track_key='google' AND event_key='course:7:module:1'")
            conn.commit()
            tracks.sync_all(conn, state(conn))
            google_task = conn.execute("SELECT * FROM track_tasks WHERE track_key='google'").fetchone()
            google_state = conn.execute("SELECT status,metadata FROM track_state WHERE track_key='google'").fetchone()
            if google_task is not None:
                errors.append("Future-topic Course 7 Module 1 remained in the Week 3 task queue.")
            if google_state is None or str(google_state["status"]) != "Locked":
                errors.append("Future-topic Google status is not Locked while held for Week 8.")
            active_google = [t for t in unified_tasks.all_tasks(conn, 3) if t.get("kind") == "google" and not t.get("completed")]
            if active_google:
                errors.append("Future-topic Google work entered the unified Week 3 planner.")

            # The same module must become the first-priority active task in Week 8.
            conn.execute("UPDATE program_state SET current_week=8 WHERE id=1")
            conn.commit()
            tracks.sync_all(conn, state(conn))
            task = conn.execute(
                """SELECT s.label,s.week,m.starter_path,t.target_key
                     FROM track_tasks t
                     JOIN sprint_tasks s ON s.id=t.task_id
                     JOIN task_metadata m ON m.task_id=s.id
                    WHERE t.track_key='google'"""
            ).fetchone()
            if task is None:
                errors.append("Course 7 Module 1 did not become active in Week 8.")
            else:
                if str(task["target_key"]) != "course:7:module:1":
                    errors.append(f"Unexpected Week 8 Google target: {task['target_key']}")
                if int(task["week"]) != 8:
                    errors.append("Week 8 Google task retained the wrong assigned week.")
                if not str(task["starter_path"] or "").startswith("https://www.coursera.org/learn/"):
                    errors.append("Google task does not route to the official course URL.")

            # New-program checkpoint regression: all assigned modules block the check,
            # not only the one active module task.
            conn.execute("DELETE FROM track_events WHERE track_key='google'")
            conn.execute("UPDATE program_state SET current_week=1,google_course=1,google_module=1 WHERE id=1")
            conn.execute("DELETE FROM weekly_check_progress")
            conn.commit()
            tracks.sync_all(conn, state(conn))
            weekly_checks.reconcile(conn)
            blockers = weekly_checks.incomplete_required_tasks(conn, 1)
            blocker_text = "\n".join(str(item.get("label") or item.get("title") or item) for item in blockers)
            for number in (1, 2, 3):
                if f"Module {number}" not in blocker_text:
                    errors.append(f"Week 1 check does not recognize Course 1 Module {number} as required.")
        finally:
            conn.close()

    if errors:
        print("Google roadmap audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Google roadmap audit passed")
    print("- 39 modules across nine courses")
    print("- future-topic Python is hidden in Week 3 and activates in Week 8")
    print("- weekly checks account for every assigned Google module")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
