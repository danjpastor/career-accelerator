"""Topic-aligned Google Data Analytics Certificate roadmap.

Google Certificate modules remain the program's highest-priority external work,
but they only become eligible when the 12-week roadmap reaches the subject area
that the module teaches.  Completion still advances sequentially through the
certificate; scheduling never skips a module or rewrites completed progress.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GoogleModule:
    course: int
    module: int
    week: int
    course_name: str
    module_name: str
    url: str
    estimated_minutes: int = 120

    @property
    def key(self) -> str:
        return f"course:{self.course}:module:{self.module}"

    @property
    def task_label(self) -> str:
        return f"Google Course {self.course} — Module {self.module}: {self.module_name}"

    @property
    def source_label(self) -> str:
        return f"Google • Course {self.course}, Module {self.module}"


_COURSES = {
    1: (
        "Foundations: Data, Data, Everywhere",
        "https://www.coursera.org/learn/foundations-data",
        (
            (1, "Introducing data analytics and analytical thinking"),
            (1, "The wonderful world of data"),
            (1, "Set up your data analytics toolbox"),
            (2, "Become a fair and impactful data professional"),
        ),
    ),
    2: (
        "Ask Questions to Make Data-Driven Decisions",
        "https://www.coursera.org/learn/ask-questions-make-decisions",
        (
            (2, "Ask effective questions"),
            (2, "Make data-driven decisions"),
            (2, "Spreadsheet magic"),
            (3, "Always remember the stakeholder"),
        ),
    ),
    3: (
        "Prepare Data for Exploration",
        "https://www.coursera.org/learn/data-preparation",
        (
            (3, "Data types and structures"),
            (3, "Data responsibility"),
            (3, "Database essentials"),
            (4, "Organize and protect data"),
            (4, "Engage in the data community"),
        ),
    ),
    4: (
        "Process Data from Dirty to Clean",
        "https://www.coursera.org/learn/process-data",
        (
            (4, "The importance of integrity"),
            (4, "Clean data for more accurate insights"),
            (5, "Data cleaning with SQL"),
            (5, "Verify and report on cleaning results"),
            (5, "Add data to your resume"),
            (5, "Course wrap-up"),
        ),
    ),
    5: (
        "Analyze Data to Answer Questions",
        "https://www.coursera.org/learn/analyze-data",
        (
            (5, "Organize data for more effective analysis"),
            (6, "Format and adjust data"),
            (6, "Aggregate data for analysis"),
            (6, "Perform data calculations"),
        ),
    ),
    6: (
        "Share Data Through the Art of Visualization",
        "https://www.coursera.org/learn/visualize-data",
        (
            (7, "Visualize data"),
            (7, "Create data visualizations with Tableau"),
            (7, "Craft data stories"),
            (7, "Develop presentations and slideshows"),
        ),
    ),
    7: (
        "Introduction to Data Analysis Using Python",
        "https://www.coursera.org/learn/introduction-to-data-analysis-using-python",
        (
            (8, "Hello, Python!"),
            (8, "Functions and conditional statements"),
            (8, "Loops and strings"),
            (8, "Data structures in Python"),
        ),
    ),
    8: (
        "Google Data Analytics Capstone: Complete a Case Study",
        "https://www.coursera.org/learn/google-data-analytics-capstone",
        (
            (9, "Learn about capstone basics"),
            (10, "Optional: Build your portfolio"),
            (11, "Optional: Use your portfolio"),
            (11, "Put your certificate to work"),
        ),
    ),
    9: (
        "Accelerate Your Job Search with AI",
        "https://www.coursera.org/learn/accelerate-your-job-search-with-ai",
        (
            (11, "Uncover your transferable skills with AI"),
            (12, "Plan your job search with AI"),
            (12, "Manage your job applications with AI"),
            (12, "Prepare and practice for interviews with AI"),
        ),
    ),
}

GOOGLE_MODULES: tuple[GoogleModule, ...] = tuple(
    GoogleModule(
        course=course,
        module=module_number,
        week=week,
        course_name=course_name,
        module_name=module_name,
        url=url,
    )
    for course, (course_name, url, module_rows) in _COURSES.items()
    for module_number, (week, module_name) in enumerate(module_rows, start=1)
)

MODULE_BY_POSITION = {(item.course, item.module): item for item in GOOGLE_MODULES}
MODULE_BY_KEY = {item.key: item for item in GOOGLE_MODULES}
COURSE_MODULE_COUNTS = {
    course: len(module_rows)
    for course, (_course_name, _url, module_rows) in _COURSES.items()
}
_SEQUENCE_INDEX = {
    (item.course, item.module): index
    for index, item in enumerate(GOOGLE_MODULES)
}


def module(course: int, module_number: int) -> GoogleModule:
    return MODULE_BY_POSITION[(int(course), int(module_number))]


def module_or_none(course: int, module_number: int) -> GoogleModule | None:
    return MODULE_BY_POSITION.get((int(course), int(module_number)))


def modules_for_week(week: int) -> tuple[GoogleModule, ...]:
    return tuple(item for item in GOOGLE_MODULES if item.week == int(week))


def modules_through_week(week: int) -> tuple[GoogleModule, ...]:
    return tuple(item for item in GOOGLE_MODULES if item.week <= int(week))


def position_index(course: int, module_number: int) -> int:
    return _SEQUENCE_INDEX[(int(course), int(module_number))]


def is_position_after(
    current_course: int,
    current_module: int,
    target_course: int,
    target_module: int,
) -> bool:
    """Return True when the current next-module pointer is beyond the target."""
    current = module_or_none(current_course, current_module)
    target = module_or_none(target_course, target_module)
    if current is None or target is None:
        return False
    return position_index(current.course, current.module) > position_index(
        target.course, target.module
    )


def completed_event_keys(conn) -> set[str]:
    try:
        rows = conn.execute(
            "SELECT event_key FROM track_events WHERE track_key='google'"
        ).fetchall()
    except Exception:
        return set()
    return {str(row["event_key"]) for row in rows}


def is_completed(conn, item: GoogleModule) -> bool:
    """Use explicit events first, then the durable next-module pointer."""
    if item.key in completed_event_keys(conn):
        return True
    row = conn.execute(
        "SELECT google_course,google_module FROM program_state WHERE id=1"
    ).fetchone()
    if row is None:
        return False
    return is_position_after(
        int(row["google_course"]),
        int(row["google_module"]),
        item.course,
        item.module,
    )


def incomplete_modules_through_week(conn, week: int) -> list[GoogleModule]:
    return [item for item in modules_through_week(week) if not is_completed(conn, item)]


def roadmap_summary(week: int) -> str:
    items = modules_for_week(week)
    if not items:
        return "No new Google Certificate module is assigned this week."
    courses: list[str] = []
    for item in items:
        label = f"Course {item.course} Module {item.module}: {item.module_name}"
        courses.append(label)
    return " • ".join(courses)


def validate() -> list[str]:
    issues: list[str] = []
    expected = list(range(1, 10))
    if sorted(COURSE_MODULE_COUNTS) != expected:
        issues.append("Google Certificate courses must be numbered 1 through 9.")
    for course, count in COURSE_MODULE_COUNTS.items():
        positions = [item.module for item in GOOGLE_MODULES if item.course == course]
        if positions != list(range(1, count + 1)):
            issues.append(f"Course {course} modules are not sequential.")
    if any(item.week < 1 or item.week > 12 for item in GOOGLE_MODULES):
        issues.append("Every Google Certificate module must be assigned to Week 1–12.")
    if len(MODULE_BY_POSITION) != len(GOOGLE_MODULES):
        issues.append("Duplicate Google Certificate course/module positions exist.")
    return issues
