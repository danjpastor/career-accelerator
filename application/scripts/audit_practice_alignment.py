from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "application"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES, ordered_exercise_numbers, roadmap_number, exercise_number_for_label
)
from career_app.data.python_exercises import PYTHON_EXERCISES
from career_app.data.roadmap import SQL_COMPANION
from career_app.services import content_gates, roadmap_mastery, tracks

EXPECTED_DUCKDB = {3: 5, 4: 10, 5: 9, 6: 9}
EXPECTED_SQL = {3: 4, 4: 5, 5: 7}
EXPECTED_PYTHON = {8: 13}


def counts(items):
    return dict(sorted(Counter(int(value["week"]) for value in items.values()).items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    app = root / "application"
    issues: list[str] = []

    duck_counts = counts(DUCKDB_EXERCISES)
    python_counts = counts(PYTHON_EXERCISES)
    sql_counts = dict(sorted(Counter(int(week) for week in roadmap_mastery.SQL_PROBLEM_SCHEDULE.values()).items()))
    if duck_counts != EXPECTED_DUCKDB:
        issues.append(f"DuckDB week counts {duck_counts}; expected {EXPECTED_DUCKDB}.")
    if sql_counts != EXPECTED_SQL:
        issues.append(f"SQL interview week counts {sql_counts}; expected {EXPECTED_SQL}.")
    if python_counts != EXPECTED_PYTHON:
        issues.append(f"Python week counts {python_counts}; expected {EXPECTED_PYTHON}.")

    if tracks.SQL_PROBLEM_WEEK != roadmap_mastery.SQL_PROBLEM_SCHEDULE:
        issues.append("tracks.SQL_PROBLEM_WEEK differs from roadmap_mastery.")
    companion = {str(item[0]): int(item[4]) for item in SQL_COMPANION}
    if companion != roadmap_mastery.SQL_PROBLEM_SCHEDULE:
        issues.append("roadmap.SQL_COMPANION differs from roadmap_mastery.")

    ordered_duckdb = list(ordered_exercise_numbers())
    display_numbers = [roadmap_number(number) for number in ordered_duckdb]
    if display_numbers != list(range(1, len(DUCKDB_EXERCISES) + 1)):
        issues.append(f"DuckDB learner-facing numbers are {display_numbers}; expected 1-{len(DUCKDB_EXERCISES)}.")
    for number in ordered_duckdb:
        item = DUCKDB_EXERCISES[number]
        if exercise_number_for_label(item["label"]) != number:
            issues.append(f"DuckDB display label does not route back to internal exercise {number}.")
        key = content_gates.DUCKDB_TERMINAL_CHAPTER.get(int(number))
        chapter = CHAPTER_BY_KEY.get(str(key or ""))
        if chapter is None:
            issues.append(f"DuckDB Exercise {number:02d} has no valid terminal DataCamp chapter.")
        elif int(chapter.week) > int(item["week"]):
            issues.append(
                f"DuckDB Exercise {number:02d} is Week {item['week']} before its chapter Week {chapter.week}."
            )
        folder = root / "practice" / "duckdb" / "exercises" / str(item["slug"])
        for filename in ("README.md", "starter.sql", "validation.md"):
            if not (folder / filename).is_file():
                issues.append(f"Missing {folder.relative_to(root) / filename}.")

    for number, item in PYTHON_EXERCISES.items():
        chapter = CHAPTER_BY_KEY.get(str(item.get("terminal_chapter") or ""))
        if chapter is None:
            issues.append(f"Python Exercise {number:02d} has no valid terminal DataCamp chapter.")
        elif int(chapter.week) != int(item["week"]):
            issues.append(
                f"Python Exercise {number:02d} is Week {item['week']} but its chapter is Week {chapter.week}."
            )
        folder = root / "practice" / "python" / "exercises" / str(item["slug"])
        for filename in ("README.md", "starter.py"):
            if not (folder / filename).is_file():
                issues.append(f"Missing {folder.relative_to(root) / filename}.")

    if not (root / "practice" / "python" / "datasets" / "operations.csv").is_file():
        issues.append("Missing shared Python practice dataset.")

    unified = (app / "career_app" / "services" / "unified_tasks.py").read_text(encoding="utf-8")
    for token in ("datacamp_chapter", "duckdb", "interview_problem", "sql_practice", "python_exercise"):
        if token not in unified:
            issues.append(f"Locked supplementary focus support is missing {token}.")
    main_source = (app / "career_app" / "main.py").read_text(encoding="utf-8")
    python_ui = app / "career_app" / "ui" / "python_exercises.py"
    python_runner = app / "career_app" / "services" / "python_exercise_runner.py"
    python_workspace = app / "career_app" / "services" / "python_workspace.py"
    for path in (python_ui, python_runner, python_workspace):
        if not path.is_file():
            issues.append(f"Missing integrated Python workspace file: {path.relative_to(root)}.")
    for token in ("PythonExercisesWidget", '"Python Exercises"', "python_exercise_number_for_label"):
        if token not in main_source:
            issues.append(f"Learning integration is missing {token}.")
    if python_ui.is_file():
        source = python_ui.read_text(encoding="utf-8")
        for token in ("AssistedPlainTextEdit", "Run", "Check Exercise", "Submit Exercise", "chart_label"):
            if token not in source:
                issues.append(f"Python editor workspace is missing {token}.")

    checks = (app / "career_app" / "services" / "weekly_checks.py").read_text(encoding="utf-8")
    for prefix in ("roadmap_v1026:duckdb:", "roadmap_v1026:sql:", "roadmap_v1026:python:"):
        if prefix not in checks:
            issues.append(f"Weekly-check supplementary exclusion missing {prefix}.")

    if issues:
        print("Practice alignment audit FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Practice alignment audit PASSED")
    print(f"- DuckDB exercises: {len(DUCKDB_EXERCISES)} {duck_counts}")
    print(f"- SQL interview problems: {len(roadmap_mastery.SQL_PROBLEM_SCHEDULE)} {sql_counts}")
    print(f"- Python exercises: {len(PYTHON_EXERCISES)} {python_counts}")
    print("- locked supplementary tasks remain visible in Today's Focus")
    print("- supplementary tasks do not block weekly knowledge checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
