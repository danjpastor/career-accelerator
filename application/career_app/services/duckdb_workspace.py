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
    exercise_labels,
    roadmap_number,
)
from career_app.services import roadmap_mastery


VALID_STATUSES = (
    "Not Started",
    "In Progress",
    "Completed",
)


PROGRESS_SCHEMA = """
CREATE TABLE IF NOT EXISTS duckdb_completion_evidence (
    exercise_number INTEGER PRIMARY KEY,
    completed_date TEXT NOT NULL,
    submission_path TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS duckdb_task_validation (
    exercise_number INTEGER NOT NULL,
    task_number INTEGER NOT NULL,
    answer_digest TEXT NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    checked_at TEXT,
    PRIMARY KEY (exercise_number, task_number)
);
CREATE INDEX IF NOT EXISTS idx_duckdb_task_validation_passed
    ON duckdb_task_validation(exercise_number, passed);
"""


def ensure_progress_schema(conn) -> None:
    conn.executescript(PROGRESS_SCHEMA)


def task_validation_digests(conn, number: int) -> dict[int, str]:
    ensure_progress_schema(conn)
    return {
        int(row["task_number"]): str(row["answer_digest"])
        for row in conn.execute(
            """SELECT task_number,answer_digest
               FROM duckdb_task_validation
               WHERE exercise_number=? AND passed=1""",
            (int(number),),
        ).fetchall()
    }


def task_validation_digest(conn, number: int, task_number: int) -> str:
    return task_validation_digests(conn, number).get(int(task_number), "")


def save_task_validation(
    conn,
    number: int,
    task_number: int,
    *,
    answer_digest: str,
    passed: bool,
) -> None:
    ensure_progress_schema(conn)
    conn.execute(
        """INSERT INTO duckdb_task_validation
           (exercise_number,task_number,answer_digest,passed,checked_at)
           VALUES(?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(exercise_number,task_number)
           DO UPDATE SET answer_digest=excluded.answer_digest,
                         passed=excluded.passed,
                         checked_at=CURRENT_TIMESTAMP""",
        (int(number), int(task_number), str(answer_digest or ""), 1 if passed else 0),
    )
    conn.commit()


def seed_completed_task_validations(
    conn,
    number: int,
    digests: dict[int, str],
) -> None:
    """Restore task checkmarks for an exercise already completed durably."""
    ensure_progress_schema(conn)
    row = conn.execute(
        "SELECT status FROM duckdb_exercise_progress WHERE exercise_number=?",
        (int(number),),
    ).fetchone()
    if row is None or str(row["status"]) != "Completed":
        return
    for task_number, digest in digests.items():
        if not str(digest or ""):
            continue
        conn.execute(
            """INSERT INTO duckdb_task_validation
               (exercise_number,task_number,answer_digest,passed,checked_at)
               VALUES(?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(exercise_number,task_number) DO UPDATE SET
                   answer_digest=excluded.answer_digest,
                   passed=1,
                   checked_at=CURRENT_TIMESTAMP""",
            (int(number), int(task_number), str(digest), 1),
        )
    conn.commit()


def reconcile_completion_state(conn, root: Path | None = None) -> dict:
    """Repair DuckDB completion from durable evidence before planner startup.

    Completion can be represented by the exercise progress row, the stable
    completion-evidence row, or an already-completed managed sprint task. The
    union is intentional: routine task synchronization may replace a sprint row,
    but it must never erase a submitted exercise.
    """
    del root
    ensure_progress_schema(conn)
    completed: set[int] = {
        int(row["exercise_number"])
        for row in conn.execute(
            "SELECT exercise_number FROM duckdb_completion_evidence"
        ).fetchall()
    }
    completed.update(
        int(row["exercise_number"])
        for row in conn.execute(
            """SELECT exercise_number
               FROM duckdb_exercise_progress
               WHERE status='Completed'"""
        ).fetchall()
    )
    for row in conn.execute(
        """SELECT m.managed_key
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE (s.completed=1 OR m.status='Completed')
             AND m.managed_key LIKE 'roadmap_v1026:duckdb:%'"""
    ).fetchall():
        try:
            completed.add(int(str(row["managed_key"]).rsplit(":", 1)[-1]))
        except (TypeError, ValueError):
            continue

    repaired = 0
    for number in sorted(value for value in completed if value in DUCKDB_EXERCISES):
        prior = conn.execute(
            """SELECT status,submission_path,completed_date
               FROM duckdb_exercise_progress WHERE exercise_number=?""",
            (number,),
        ).fetchone()
        durable = conn.execute(
            """SELECT completed_date,submission_path
               FROM duckdb_completion_evidence WHERE exercise_number=?""",
            (number,),
        ).fetchone()
        submission = (
            prior["submission_path"]
            if prior is not None and prior["submission_path"]
            else durable["submission_path"] if durable is not None else None
        )
        completed_date = (
            prior["completed_date"]
            if prior is not None and prior["completed_date"]
            else durable["completed_date"]
            if durable is not None and durable["completed_date"]
            else date.today().isoformat()
        )
        conn.execute(
            """INSERT INTO duckdb_exercise_progress
               (exercise_number,status,submission_path,notes,completed_date,updated_at)
               VALUES(?,'Completed',?,'',?,CURRENT_TIMESTAMP)
               ON CONFLICT(exercise_number) DO UPDATE SET
                   status='Completed',
                   submission_path=COALESCE(duckdb_exercise_progress.submission_path,excluded.submission_path),
                   completed_date=COALESCE(duckdb_exercise_progress.completed_date,excluded.completed_date),
                   updated_at=CURRENT_TIMESTAMP""",
            (number, submission, completed_date),
        )
        conn.execute(
            """INSERT INTO duckdb_completion_evidence
               (exercise_number,completed_date,submission_path,updated_at)
               VALUES(?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(exercise_number) DO UPDATE SET
                   completed_date=COALESCE(duckdb_completion_evidence.completed_date,excluded.completed_date),
                   submission_path=COALESCE(duckdb_completion_evidence.submission_path,excluded.submission_path),
                   updated_at=CURRENT_TIMESTAMP""",
            (number, completed_date, submission),
        )
        labels = exercise_labels(number)
        placeholders = ",".join("?" for _ in labels)
        rows = conn.execute(
            f"""SELECT s.id
                FROM sprint_tasks s
                JOIN task_metadata m ON m.task_id=s.id
                WHERE s.label IN ({placeholders}) OR m.managed_key=?""",
            (*labels, f"roadmap_v1026:duckdb:{number}"),
        ).fetchall()
        for task in rows:
            task_id = int(task["id"])
            conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
            conn.execute(
                """UPDATE task_metadata
                   SET status='Completed',prerequisite_state='Ready',prerequisite_reason=NULL
                   WHERE task_id=?""",
                (task_id,),
            )
        repaired += 1
    conn.commit()
    return {"completed": sorted(completed), "repaired": repaired}


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
        f"-- Exercise {roadmap_number(number):02d}: {item['title']}\n"
        f"-- Concepts: {item['concepts']}\n"
        "-- Save your completed work in this file.\n"
        "\n"
        + starter_text
    )


def ensure_submission(
    root: Path,
    number: int,
) -> tuple[Path, bool]:
    roadmap_mastery.assert_duckdb_ready_from_root(root, number)
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
    labels = exercise_labels(number)
    placeholders = ",".join("?" for _ in labels)
    return conn.execute(
        f"""SELECT
               s.id,
               s.completed,
               m.status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.label IN ({placeholders})
              OR m.managed_key=?""",
        (*labels, f"roadmap_v1026:duckdb:{int(number)}"),
    ).fetchall()


def progress(
    conn,
    root: Path,
    number: int,
) -> dict:
    ensure_progress_schema(conn)
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
    ensure_progress_schema(conn)
    roadmap_mastery.assert_duckdb_ready(conn, number)
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
    existing = conn.execute(
        "SELECT status,completed_date FROM duckdb_exercise_progress WHERE exercise_number=?",
        (int(number),),
    ).fetchone()
    # Routine autosave or task synchronization must never downgrade an exercise
    # that was already submitted. Explicit undo uses tracks.undo_completion and
    # clears the durable completion evidence separately.
    if existing is not None and str(existing["status"]) == "Completed":
        status = "Completed"
    completed_date = (
        str(existing["completed_date"])
        if existing is not None and existing["completed_date"] and status == "Completed"
        else date.today().isoformat() if status == "Completed" else None
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
        f"DuckDB Exercise {roadmap_number(number):02d}: "
        f"{item['title']}"
    )
    if completed:
        conn.execute(
            """INSERT INTO duckdb_completion_evidence
               (exercise_number,completed_date,submission_path,updated_at)
               VALUES(?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(exercise_number) DO UPDATE SET
                   completed_date=excluded.completed_date,
                   submission_path=COALESCE(excluded.submission_path,duckdb_completion_evidence.submission_path),
                   updated_at=CURRENT_TIMESTAMP""",
            (int(number), completed_date or date.today().isoformat(), relative_path),
        )
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
    if completed:
        roadmap_mastery.reconcile_duckdb_completion(conn, number)
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
