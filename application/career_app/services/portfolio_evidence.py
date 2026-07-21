from __future__ import annotations

import sqlite3
from pathlib import Path

from career_app.data.roadmap import PROJECT_DIRS, PROJECT_NAMES


SKILL = "SQL relationship validation and data-quality testing"
SOURCE_TYPE = "Portfolio"
TARGET_LABEL = "validate relationships"


def _normalized(value: object) -> str:
    return " ".join(
        str(value or "")
        .replace("–", "-")
        .replace("—", "-")
        .casefold()
        .split()
    )


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _task_details(root: Path, row) -> dict[str, object] | None:
    if row is None or _normalized(row["label"]) != TARGET_LABEL:
        return None

    project_id = int(row["project_id"])
    project_name = PROJECT_NAMES.get(project_id, f"Project {project_id}")
    directory_name = PROJECT_DIRS.get(project_id)
    if not directory_name:
        return None

    project_dir = root / "projects" / directory_name
    notebook = project_dir / "notebooks" / "validate_relationships.ipynb"
    if not notebook.is_file():
        candidates = sorted(
            project_dir.rglob("validate_relationships.ipynb"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            notebook = candidates[0]

    source_name = (
        f"Project {project_id} — {project_name} — Validate Relationships"
    )

    if not notebook.is_file():
        return {
            "source_name": source_name,
            "artifact_ready": False,
            "description": "",
        }

    report_root = project_dir / "reports" / "relationship_validation"
    reports: list[Path] = []
    for name in (
        "primary_key_results.csv",
        "relationship_results.csv",
        "consistency_results.csv",
        "summary.md",
    ):
        matches: list[Path] = []
        if report_root.exists():
            matches = sorted(
                report_root.rglob(name),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        if matches:
            reports.append(matches[0])

    artifact_text = f"Primary artifact: {_relative(root, notebook)}."
    if reports:
        artifact_text += (
            " Supporting automated reports: "
            + ", ".join(_relative(root, path) for path in reports)
            + "."
        )

    description = (
        "Validated primary keys, foreign keys, join cardinality, and "
        "production-chain consistency across the portfolio project's "
        "source tables using DuckDB, SQL, Jupyter, and a repeatable "
        "automated audit. Documented duplicate identifiers, null and "
        "orphaned references, unexpected row multiplication, "
        "inconsistent project assignments, and the cleaning actions "
        "required before final KPI reporting. No raw source records "
        "were modified. "
        + artifact_text
    )

    return {
        "source_name": source_name,
        "artifact_ready": True,
        "description": description,
    }


def sync_task(
    conn: sqlite3.Connection,
    root: Path,
    *,
    task_id: int,
    completed: bool | None = None,
) -> bool:
    row = conn.execute(
        """
        SELECT id,project_id,label,completed
        FROM project_tasks
        WHERE id=?
        """,
        (int(task_id),),
    ).fetchone()
    details = _task_details(Path(root), row)
    if details is None:
        return False

    is_completed = bool(row["completed"]) if completed is None else bool(completed)
    source_name = str(details["source_name"])

    if not is_completed:
        cursor = conn.execute(
            """
            DELETE FROM evidence
            WHERE skill=?
              AND source_type=?
              AND source_name=?
            """,
            (SKILL, SOURCE_TYPE, source_name),
        )
        return bool(cursor.rowcount)

    if not bool(details["artifact_ready"]):
        return False

    description = str(details["description"])
    existing = conn.execute(
        """
        SELECT description
        FROM evidence
        WHERE skill=?
          AND source_type=?
          AND source_name=?
        """,
        (SKILL, SOURCE_TYPE, source_name),
    ).fetchone()
    if existing is not None and str(existing["description"] or "") == description:
        return False

    conn.execute(
        """
        INSERT INTO evidence(skill,source_type,source_name,description)
        VALUES(?,?,?,?)
        ON CONFLICT(skill,source_type,source_name)
        DO UPDATE SET description=excluded.description
        """,
        (SKILL, SOURCE_TYPE, source_name, description),
    )
    return True


def reconcile(conn: sqlite3.Connection, root: Path) -> int:
    rows = conn.execute(
        """
        SELECT id,completed
        FROM project_tasks
        WHERE lower(trim(label))='validate relationships'
        """
    ).fetchall()

    changed = 0
    for row in rows:
        if sync_task(
            conn,
            Path(root),
            task_id=int(row["id"]),
            completed=bool(row["completed"]),
        ):
            changed += 1

    if changed:
        conn.commit()
    return changed


def reconcile_database(repo: Path) -> str:
    database = Path(repo) / "data" / "career_accelerator.db"
    if not database.is_file():
        return "No local database found; the app will reconcile on startup."

    conn = sqlite3.connect(database, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not {"project_tasks", "evidence"}.issubset(tables):
            return "Database tables are not ready; the app will reconcile on startup."
        changed = reconcile(conn, Path(repo))
        return f"Evidence reconciliation complete: {changed} record(s) changed."
    finally:
        conn.close()
