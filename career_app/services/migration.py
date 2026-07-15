from __future__ import annotations
import re
from pathlib import Path

from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

CHECKBOX = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.+?)\s*$")

PROJECT_DIRS = {
    1: "project-01-vfx-production-intelligence",
    2: "project-02-retail-operations",
    3: "project-03-movie-industry-financial-analytics",
}

STAGE_KEYWORDS = [
    ("Discovery", ("business problem", "stakeholder", "kpi", "business question", "charter")),
    ("Dataset", ("dataset", "data dictionary", "validate", "clean")),
    ("SQL", ("schema", "sql", "query")),
    ("Python", ("python", "pandas", "eda", "anomaly")),
    ("Power BI", ("power bi", "dax", "dashboard", "measure")),
    ("GitHub", ("github", "release", "publish")),
    ("README", ("readme", "documentation", "screenshot")),
    ("Resume Bullet", ("resume", "bullet")),
    ("Presentation", ("presentation", "walkthrough")),
    ("Reflection", ("reflection", "lessons learned")),
]

def checkboxes(path: Path):
    if not path.exists():
        return []
    seen = set()
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CHECKBOX.match(line)
        if not match:
            continue
        label = match.group(2).strip()
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        rows.append((label, 1 if match.group(1).lower() == "x" else 0))
    return rows

def stage_for(label):
    lower = label.lower()
    for stage, words in STAGE_KEYWORDS:
        if any(word in lower for word in words):
            return stage
    return "Overview"


def _update_duckdb_exercise_tasks(conn):
    updated = 0
    for exercise in DUCKDB_EXERCISES.values():
        rows = conn.execute(
            """SELECT id,label
               FROM sprint_tasks
               WHERE label IN (?,?)""",
            (
                exercise["old_label"],
                exercise["label"],
            ),
        ).fetchall()

        for row in rows:
            if row["label"] != exercise["label"]:
                conn.execute(
                    "UPDATE sprint_tasks SET label=? WHERE id=?",
                    (exercise["label"], row["id"]),
                )
                updated += 1

            conn.execute(
                """UPDATE task_metadata
                   SET category='SQL',
                       priority=?,
                       estimated_minutes=?,
                       energy='Normal',
                       destination=4
                   WHERE task_id=?""",
                (
                    exercise["priority"],
                    exercise["minutes"],
                    row["id"],
                ),
            )
    return updated


def migrate(conn, root: Path):
    sprint_count = 0
    project_count = 0

    for week in range(1, 13):
        existing = conn.execute(
            "SELECT COUNT(*) FROM sprint_tasks WHERE week=?", (week,)
        ).fetchone()[0]
        if existing:
            continue
        path = root / "weeks" / f"week-{week:02d}" / "README.md"
        for order, (label, completed) in enumerate(checkboxes(path), start=1):
            conn.execute(
                """INSERT OR IGNORE INTO sprint_tasks
                   (week,sort_order,label,completed) VALUES(?,?,?,?)""",
                (week, order, label, completed),
            )
            sprint_count += 1

    for project_id, dirname in PROJECT_DIRS.items():
        existing = conn.execute(
            "SELECT COUNT(*) FROM project_tasks WHERE project_id=?", (project_id,)
        ).fetchone()[0]
        if existing:
            continue
        path = root / "projects" / dirname / "TASKS.md"
        for order, (label, completed) in enumerate(checkboxes(path), start=1):
            conn.execute(
                """INSERT OR IGNORE INTO project_tasks
                   (project_id,sort_order,stage,label,completed)
                   VALUES(?,?,?,?,?)""",
                (project_id, order, stage_for(label), label, completed),
            )
            project_count += 1

    updated_tasks = _update_duckdb_exercise_tasks(conn)

    conn.commit()
    return {
        "sprint_tasks": sprint_count,
        "project_tasks": project_count,
        "updated_tasks": updated_tasks,
    }
