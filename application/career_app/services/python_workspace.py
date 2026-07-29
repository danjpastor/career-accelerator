"""File, progress, and evidence helpers for integrated Python exercises."""
from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import shutil
import subprocess
import sys

from career_app.data.python_exercises import PYTHON_EXERCISES
from career_app.services import roadmap_mastery

VALID_STATUSES = ("Not Started", "In Progress", "Completed")


def exercise(number: int) -> dict:
    number = int(number)
    if number not in PYTHON_EXERCISES:
        raise ValueError(f"Python Exercise {number:02d} is not in the catalog.")
    return PYTHON_EXERCISES[number]


def paths(root: Path, number: int) -> dict[str, Path]:
    item = exercise(number)
    practice_root = Path(root) / "practice" / "python"
    exercise_dir = practice_root / "exercises" / item["slug"]
    return {
        "practice_root": practice_root,
        "exercise_dir": exercise_dir,
        "instructions": exercise_dir / "README.md",
        "starter": exercise_dir / "starter.py",
        "dataset": practice_root / "datasets" / "operations.csv",
        "submissions": practice_root / "submissions",
        "outputs": practice_root / "outputs" / f"{number:02d}_{item['slug']}",
    }


def submission_path(root: Path, number: int) -> Path:
    item = exercise(number)
    # Keep each submission one folder below ``submissions`` so the starter's
    # relative DATA_PATH continues to resolve to ``practice/python/datasets``.
    return (
        paths(root, number)["submissions"]
        / f"{number:02d}_{item['slug']}"
        / "submission.py"
    )


def _submission_template(root: Path, number: int) -> str:
    starter = paths(root, number)["starter"]
    if not starter.is_file():
        raise FileNotFoundError(f"Starter Python file was not found: {starter}")
    return starter.read_text(encoding="utf-8")


def ensure_submission(root: Path, number: int, *, check_ready: bool = True) -> tuple[Path, bool]:
    if check_ready:
        db_path = Path(root) / "data" / "career_accelerator.db"
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                result = roadmap_mastery.python_exercise_readiness(conn, int(number))
                if not result["ready"]:
                    raise PermissionError(result["reason"])
            finally:
                conn.close()
    path = submission_path(root, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    if created:
        path.write_text(_submission_template(root, number), encoding="utf-8")
    return path, created


def save_code(root: Path, number: int, code: str) -> Path:
    path, _ = ensure_submission(root, number, check_ready=False)
    path.write_text(str(code or "").replace("\r\n", "\n"), encoding="utf-8")
    return path


def submission_has_changes(root: Path, number: int) -> bool:
    path = submission_path(root, number)
    if not path.is_file():
        return False
    return path.read_text(encoding="utf-8").strip() != _submission_template(root, number).strip()


def _task_rows(conn, number: int):
    item = exercise(number)
    return conn.execute(
        """SELECT s.id,s.completed,m.status
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key=? OR s.label=?""",
        (f"roadmap_v1026:python:{int(number)}", item["label"]),
    ).fetchall()


def progress(conn, root: Path, number: int) -> dict:
    row = conn.execute(
        "SELECT * FROM python_exercise_progress WHERE exercise_number=?",
        (int(number),),
    ).fetchone()
    status = str(row["status"] if row is not None else "Not Started")
    notes = str(row["notes"] or "") if row is not None else ""
    last_output = str(row["last_output"] or "") if row is not None else ""
    completed_date = row["completed_date"] if row is not None else None
    task_rows = _task_rows(conn, number)
    if any(bool(item["completed"]) or str(item["status"]) == "Completed" for item in task_rows):
        status = "Completed"
    path = submission_path(root, number)
    relative = str(path.relative_to(Path(root))).replace("\\", "/") if path.exists() else None
    return {
        "number": int(number),
        "status": status,
        "notes": notes,
        "last_output": last_output,
        "completed_date": completed_date,
        "submission_path": relative,
        "submission_exists": path.exists(),
        "submission_changed": submission_has_changes(root, number) if path.exists() else False,
        "task_ids": [int(item["id"]) for item in task_rows],
    }


def save_progress(
    conn,
    root: Path,
    number: int,
    *,
    status: str,
    notes: str = "",
    last_output: str = "",
) -> dict:
    number = int(number)
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported exercise status: {status}")
    readiness = roadmap_mastery.python_exercise_readiness(conn, number)
    if not readiness["ready"] and status != "Not Started":
        raise PermissionError(readiness["reason"])
    item = exercise(number)
    path = submission_path(root, number)
    relative = str(path.relative_to(Path(root))).replace("\\", "/") if path.exists() else None
    completed_date = date.today().isoformat() if status == "Completed" else None
    conn.execute(
        """INSERT INTO python_exercise_progress
           (exercise_number,status,submission_path,notes,last_output,completed_date,updated_at)
           VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(exercise_number) DO UPDATE SET
             status=excluded.status,
             submission_path=excluded.submission_path,
             notes=excluded.notes,
             last_output=excluded.last_output,
             completed_date=excluded.completed_date,
             updated_at=CURRENT_TIMESTAMP""",
        (number, status, relative, str(notes or ""), str(last_output or ""), completed_date),
    )
    completed = status == "Completed"
    for task in _task_rows(conn, number):
        task_id = int(task["id"])
        conn.execute("UPDATE sprint_tasks SET completed=? WHERE id=?", (1 if completed else 0, task_id))
        conn.execute(
            """UPDATE task_metadata
               SET status=?,prerequisite_state='Ready',prerequisite_reason=NULL
               WHERE task_id=?""",
            (status, task_id),
        )
    source_name = f"Python Exercise {number:02d}: {item['title']}"
    if completed:
        description = f"Completed a guided Python exercise using {item['concepts']}."
        if relative:
            description += f" Submission: {relative}"
        conn.execute(
            """INSERT INTO evidence(skill,source_type,source_name,description)
               VALUES(?,?,?,?)
               ON CONFLICT(skill,source_type,source_name)
               DO UPDATE SET description=excluded.description""",
            (f"Python — {item['concepts']}", "Python Practice", source_name, description),
        )
    else:
        conn.execute(
            "DELETE FROM evidence WHERE source_type='Python Practice' AND source_name=?",
            (source_name,),
        )
    conn.commit()
    if completed:
        roadmap_mastery.reconcile(conn, root)
    return progress(conn, root, number)


def open_folder(path: Path) -> str:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Folder was not found: {path}")
    if os.name == "nt":
        os.startfile(str(path))
        return "File Explorer"
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return "Finder"
    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        subprocess.Popen([xdg_open, str(path)])
        return "the file manager"
    raise RuntimeError("No supported folder-opening command was found.")
