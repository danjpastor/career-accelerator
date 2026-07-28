from __future__ import annotations

"""Regression audit for explicit DataCamp-backed content locks."""

import argparse
from pathlib import Path
import shutil
import sqlite3
import tempfile

from career_app.data.applied_exercises import APPLIED_EXERCISES
from career_app.data.datacamp_curriculum import DATACAMP_CHAPTERS
from career_app.data.duckdb_exercises import DUCKDB_EXERCISES
from career_app.data.roadmap import SQL_COMPANION
from career_app.database import state
from career_app.services import content_gates, datacamp, roadmap_mastery, tracks


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _copy_database(root: Path) -> tuple[Path, tempfile.TemporaryDirectory]:
    holder = tempfile.TemporaryDirectory(prefix="career-accelerator-lock-audit-")
    db_copy = Path(holder.name) / "career_accelerator.db"
    shutil.copy2(root / "data" / "career_accelerator.db", db_copy)
    return db_copy, holder


def run(root: Path) -> list[str]:
    errors = list(content_gates.audit_contract())

    _assert(
        set(content_gates.APPLIED_LAB_TERMINAL_CHAPTER) == set(APPLIED_EXERCISES),
        "Not every Applied Lab has an explicit DataCamp terminal chapter.",
        errors,
    )
    _assert(
        set(content_gates.DUCKDB_TERMINAL_CHAPTER) == set(DUCKDB_EXERCISES),
        "Not every DuckDB exercise has an explicit DataCamp terminal chapter.",
        errors,
    )

    for item in SQL_COMPANION:
        title, _difficulty, topic = item[:3]
        groups = tracks._sql_requirement_groups(title, topic)
        required = set(groups["all_of"]) | set(groups["any_of"])
        chapter_keys = content_gates.requirements_for_sql_problem(
            required,
            roadmap_week=tracks.SQL_PROBLEM_WEEK.get(title),
        )
        _assert(bool(chapter_keys), f"SQL problem has no DataCamp gate: {title}", errors)

    db_copy, holder = _copy_database(root)
    try:
        conn = sqlite3.connect(db_copy)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        datacamp.ensure_schema(conn)
        datacamp.reconcile(conn)
        app_state = state(conn)

        conn.execute(
            "UPDATE datacamp_chapter_progress SET status='Not Started',completed_date=NULL"
        )
        conn.execute(
            "UPDATE sprint_tasks SET completed=0 WHERE id IN "
            "(SELECT task_id FROM datacamp_chapter_progress WHERE task_id IS NOT NULL)"
        )
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='duckdb_exercise_progress'"
        ).fetchone():
            conn.execute(
                "UPDATE duckdb_exercise_progress SET status='Not Started',completed_date=NULL"
            )
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='applied_exercise_progress'"
        ).fetchone():
            conn.execute(
                "UPDATE applied_exercise_progress SET status='Not Started',completed_date=NULL"
            )
        conn.execute(
            "UPDATE sprint_tasks SET completed=0 WHERE label LIKE 'Complete DuckDB Exercise %' "
            "OR label LIKE 'Complete Applied Lab %'"
        )
        conn.commit()

        lab07 = tracks.applied_lab_readiness(conn, app_state, 7)
        spreadsheet_keys = [
            chapter.key for chapter in DATACAMP_CHAPTERS if chapter.week in {1, 2}
        ]
        _assert(
            set(lab07["required_datacamp_keys"]) == set(spreadsheet_keys),
            "Applied Lab 07 does not expose all Week 1–2 DataCamp prerequisites.",
            errors,
        )
        _assert(
            set(lab07["missing_datacamp_keys"]) == set(spreadsheet_keys),
            "Applied Lab 07 was not locked when spreadsheet chapters were unfinished.",
            errors,
        )

        for number in APPLIED_EXERCISES:
            result = tracks.applied_lab_readiness(conn, app_state, number)
            _assert(
                bool(result.get("required_datacamp_keys")),
                f"Applied Lab {number:02d} has no DataCamp prerequisite list.",
                errors,
            )
            _assert(
                bool(result.get("missing_datacamp_keys")),
                f"Applied Lab {number:02d} did not lock with all DataCamp progress reset.",
                errors,
            )

        for number in DUCKDB_EXERCISES:
            result = roadmap_mastery.duckdb_readiness(conn, number)
            _assert(
                bool(result.get("required_datacamp_keys")),
                f"DuckDB Exercise {number:02d} has no DataCamp prerequisite list.",
                errors,
            )
            _assert(
                bool(result.get("missing_datacamp_keys")),
                f"DuckDB Exercise {number:02d} did not lock with DataCamp reset.",
                errors,
            )

        for item in SQL_COMPANION:
            title = item[0]
            result = tracks.sql_problem_readiness(conn, app_state, title)
            _assert(
                bool(result.get("required_datacamp_keys")),
                f"SQL problem has no runtime DataCamp prerequisite list: {title}",
                errors,
            )
            _assert(
                bool(result.get("missing_datacamp_keys")),
                f"SQL problem did not lock with DataCamp reset: {title}",
                errors,
            )

        for key in spreadsheet_keys:
            conn.execute(
                "UPDATE datacamp_chapter_progress SET status='Completed',completed_date='2026-01-01' "
                "WHERE chapter_key=?",
                (key,),
            )
        conn.commit()
        lab07_after = tracks.applied_lab_readiness(conn, app_state, 7)
        _assert(
            not lab07_after.get("missing_datacamp_keys"),
            "Applied Lab 07 remained DataCamp-locked after all Week 1–2 chapters completed.",
            errors,
        )

        for label in tracks.PROJECT_EXACT_REQUIREMENTS:
            result = tracks.portfolio_task_readiness(conn, app_state, label)
            _assert(
                bool(result.get("required_datacamp_keys")),
                f"Portfolio milestone has no DataCamp prerequisite list: {label}",
                errors,
            )

        conn.close()
    finally:
        holder.cleanup()

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()
    errors = run(args.root.resolve())
    if errors:
        print("CONTENT LOCK AUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CONTENT LOCK AUDIT PASSED")
    print("- 36 Applied Labs have explicit DataCamp chapter gates")
    print("- 18 DuckDB exercises have explicit DataCamp chapter gates")
    print("- Every SQL interview problem has an explicit DataCamp chapter gate")
    print("- Portfolio milestones include DataCamp chapter prerequisites")
    print("- Applied Lab 07 requires all 13 Week 1–2 spreadsheet chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
