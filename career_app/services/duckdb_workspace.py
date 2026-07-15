"""File and progress helpers for guided DuckDB exercises."""

from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import shutil
import subprocess
import sys

from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES,
)


VALID_STATUSES = (
    "Not Started",
    "In Progress",
    "Completed",
)


def exercise(number: int) -> dict:
    number = int(number)
    if number not in DUCKDB_EXERCISES:
        raise ValueError(
            f"DuckDB Exercise {number:02d} is not in the catalog."
        )
    return DUCKDB_EXERCISES[number]


def paths(
    root: Path,
    number: int,
) -> dict[str, Path]:
    item = exercise(number)
    practice_root = (
        Path(root)
        / "practice"
        / "duckdb"
    )
    exercise_dir = (
        practice_root
        / "exercises"
        / item["slug"]
    )
    return {
        "practice_root": practice_root,
        "exercise_dir": exercise_dir,
        "instructions": (
            exercise_dir
            / "README.md"
        ),
        "starter": (
            exercise_dir
            / "starter.sql"
        ),
        "validation": (
            exercise_dir
            / "validation.md"
        ),
        "datasets": (
            practice_root
            / "datasets"
            / item["slug"]
        ),
        "database": (
            practice_root
            / "career_practice.duckdb"
        ),
        "submissions": (
            practice_root
            / "submissions"
        ),
    }


def submission_path(
    root: Path,
    number: int,
) -> Path:
    item = exercise(number)
    return (
        paths(root, number)[
            "submissions"
        ]
        / (
            f"{number:02d}_"
            f"{item['slug']}.sql"
        )
    )


def _submission_template(
    root: Path,
    number: int,
) -> str:
    item = exercise(number)
    starter = paths(
        root,
        number,
    )["starter"]
    if not starter.exists():
        raise FileNotFoundError(
            f"Starter SQL was not found: {starter}"
        )

    starter_text = starter.read_text(
        encoding="utf-8"
    )
    return (
        "-- Career Accelerator DuckDB submission\n"
        f"-- Exercise {number:02d}: {item['title']}\n"
        f"-- Concepts: {item['concepts']}\n"
        "-- Save your completed work in this file.\n"
        "\n"
        + starter_text
    )


def ensure_submission(
    root: Path,
    number: int,
) -> tuple[Path, bool]:
    path = submission_path(
        root,
        number,
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    created = not path.exists()
    if created:
        path.write_text(
            _submission_template(
                root,
                number,
            ),
            encoding="utf-8",
        )
    return path, created


def submission_has_changes(
    root: Path,
    number: int,
) -> bool:
    path = submission_path(
        root,
        number,
    )
    if not path.exists():
        return False

    actual = path.read_text(
        encoding="utf-8"
    ).replace(
        "\r\n",
        "\n",
    ).strip()
    template = _submission_template(
        root,
        number,
    ).replace(
        "\r\n",
        "\n",
    ).strip()
    return actual != template


def _task_rows(
    conn,
    number: int,
):
    item = exercise(number)
    return conn.execute(
        """SELECT
               s.id,
               s.completed,
               m.status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.label IN (?,?)""",
        (
            item["label"],
            item["old_label"],
        ),
    ).fetchall()


def progress(
    conn,
    root: Path,
    number: int,
) -> dict:
    item = exercise(number)
    row = conn.execute(
        """SELECT *
           FROM duckdb_exercise_progress
           WHERE exercise_number=?""",
        (int(number),),
    ).fetchone()

    status = (
        row["status"]
        if row is not None
        else "Not Started"
    )
    notes = (
        row["notes"]
        if row is not None
        and row["notes"]
        else ""
    )
    completed_date = (
        row["completed_date"]
        if row is not None
        else None
    )
    saved_path = (
        row["submission_path"]
        if row is not None
        and row["submission_path"]
        else None
    )

    task_rows = _task_rows(
        conn,
        number,
    )
    if any(
        bool(task["completed"])
        or task["status"]
        == "Completed"
        for task in task_rows
    ):
        status = "Completed"
    elif (
        status == "Not Started"
        and any(
            task["status"]
            == "In Progress"
            for task in task_rows
        )
    ):
        status = "In Progress"

    path = submission_path(
        root,
        number,
    )
    if path.exists():
        saved_path = str(
            path.relative_to(
                Path(root)
            )
        ).replace(
            "\\",
            "/",
        )

    return {
        "number": int(number),
        "title": item["title"],
        "status": status,
        "notes": notes,
        "completed_date": completed_date,
        "submission_path": saved_path,
        "submission_exists": path.exists(),
        "submission_changed": (
            submission_has_changes(
                root,
                number,
            )
            if path.exists()
            else False
        ),
        "task_ids": [
            int(task["id"])
            for task in task_rows
        ],
    }


def save_progress(
    conn,
    root: Path,
    number: int,
    *,
    status: str,
    notes: str = "",
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Unsupported exercise status: {status}"
        )

    item = exercise(number)
    path = submission_path(
        root,
        number,
    )
    relative_path = (
        str(
            path.relative_to(
                Path(root)
            )
        ).replace(
            "\\",
            "/",
        )
        if path.exists()
        else None
    )
    completed_date = (
        date.today().isoformat()
        if status == "Completed"
        else None
    )

    conn.execute(
        """INSERT INTO duckdb_exercise_progress
           (
               exercise_number,
               status,
               submission_path,
               notes,
               completed_date,
               updated_at
           )
           VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(exercise_number)
           DO UPDATE SET
               status=excluded.status,
               submission_path=excluded.submission_path,
               notes=excluded.notes,
               completed_date=excluded.completed_date,
               updated_at=CURRENT_TIMESTAMP""",
        (
            int(number),
            status,
            relative_path,
            str(notes or ""),
            completed_date,
        ),
    )

    task_rows = _task_rows(
        conn,
        number,
    )
    task_ids = [
        int(task["id"])
        for task in task_rows
    ]
    completed = (
        status == "Completed"
    )

    for task_id in task_ids:
        conn.execute(
            """UPDATE sprint_tasks
               SET completed=?
               WHERE id=?""",
            (
                1 if completed else 0,
                task_id,
            ),
        )
        conn.execute(
            """UPDATE task_metadata
               SET status=?,
                   prerequisite_state='Ready',
                   prerequisite_reason=NULL
               WHERE task_id=?""",
            (
                status,
                task_id,
            ),
        )

    source_name = (
        f"DuckDB Exercise {number:02d}: "
        f"{item['title']}"
    )
    if completed:
        description = (
            "Completed a guided DuckDB exercise using "
            f"{item['concepts']}."
        )
        if relative_path:
            description += (
                " Submission: "
                + relative_path
            )

        conn.execute(
            """INSERT INTO evidence
               (
                   skill,
                   source_type,
                   source_name,
                   description
               )
               VALUES(?,?,?,?)
               ON CONFLICT(
                   skill,
                   source_type,
                   source_name
               )
               DO UPDATE SET
                   description=excluded.description""",
            (
                f"SQL — {item['concepts']}",
                "SQL Practice",
                source_name,
                description,
            ),
        )
    else:
        conn.execute(
            """DELETE FROM evidence
               WHERE source_type='SQL Practice'
                 AND source_name=?""",
            (source_name,),
        )

    conn.commit()
    return progress(
        conn,
        root,
        number,
    )


def open_folder(
    path: Path,
) -> str:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Folder was not found: {path}"
        )

    if os.name == "nt":
        os.startfile(str(path))
        return "File Explorer"

    if sys.platform == "darwin":
        subprocess.Popen(
            ["open", str(path)]
        )
        return "Finder"

    xdg_open = shutil.which(
        "xdg-open"
    )
    if xdg_open:
        subprocess.Popen(
            [xdg_open, str(path)]
        )
        return "the file manager"

    raise RuntimeError(
        "No supported folder-opening command was found."
    )
