from __future__ import annotations

"""Static release audit for the v10.36 DataCamp curriculum contract."""

from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "application"))

from career_app.data.datacamp_curriculum import DATACAMP_CHAPTERS  # noqa: E402
from career_app.services import unified_tasks  # noqa: E402


def main() -> int:
    errors: list[str] = []
    if len(DATACAMP_CHAPTERS) != 74:
        errors.append(f"Expected 74 DataCamp chapters, found {len(DATACAMP_CHAPTERS)}")
    keys = [chapter.key for chapter in DATACAMP_CHAPTERS]
    if len(keys) != len(set(keys)):
        errors.append("DataCamp chapter keys are not unique")
    daily = Counter((chapter.week, chapter.weekday) for chapter in DATACAMP_CHAPTERS)
    slots = [
        (chapter.week, chapter.weekday, chapter.order_in_day)
        for chapter in DATACAMP_CHAPTERS
    ]
    if len(slots) != len(set(slots)):
        errors.append("DataCamp schedule contains duplicate daily order slots")
    if daily and max(daily.values()) > 4:
        errors.append("A day contains more than four DataCamp chapter tasks")
    courses: dict[str, list] = defaultdict(list)
    for chapter in DATACAMP_CHAPTERS:
        courses[chapter.course_name].append(chapter)
        if not chapter.url.startswith("https://campus.datacamp.com/courses/"):
            errors.append(f"Invalid Campus URL for {chapter.key}")
    for course, chapters in courses.items():
        if len(chapters) > 1 and len({(c.week, c.weekday) for c in chapters}) < 2:
            errors.append(f"Multi-chapter course is assigned on one day: {course}")

    # These slugs are easy to "normalize" incorrectly. DataCamp's live Campus
    # routes intentionally include the numeric suffixes and PostgresSQL spelling.
    exact_routes = {
        "w01_analysis_sheets_01": "exploring-data-1",
        "w03_intermediate_sql_02": "filtering-records-2",
        "w03_intermediate_sql_03": "aggregate-functions-3",
        "w05_functions_sql_02": "working-with-datetime-functions-and-operators",
        "w06_functions_sql_04": "full-text-search-and-postgressql-extensions",
        "w08_intro_python_01": "chapter-1-python-basics",
        "w08_intro_python_02": "chapter-2-python-lists",
        "w08_intro_python_03": "chapter-3-functions-and-packages",
        "w08_intro_python_04": "chapter-4-numpy",
    }
    by_key = {chapter.key: chapter for chapter in DATACAMP_CHAPTERS}
    for key, expected_slug in exact_routes.items():
        chapter = by_key.get(key)
        if chapter is None or chapter.chapter_slug != expected_slug:
            errors.append(f"Incorrect exact Campus chapter route for {key}")
    if unified_tasks.MAX_FOCUS_TASKS != 5:
        errors.append("Today’s Focus limit is not five")
    if unified_tasks.MAX_NEXT_TASKS != 4:
        errors.append("Next Tasks limit is not four")
    retired = (
        ROOT / "application" / "career_app" / "academy",
        ROOT / "application" / "career_app" / "ui" / "academy.py",
        ROOT / "academy_workspace",
        ROOT / "curriculum",
    )
    for path in retired:
        if path.exists():
            errors.append(f"Retired Academy path still exists: {path.relative_to(ROOT)}")
    if errors:
        print("DataCamp contract audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DataCamp contract audit passed")
    print(f"- {len(DATACAMP_CHAPTERS)} chapter tasks")
    print(f"- {len(courses)} courses")
    print(f"- maximum {max(daily.values())} chapter tasks per day")
    print("- five Today’s Focus tasks and four Next Tasks rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
