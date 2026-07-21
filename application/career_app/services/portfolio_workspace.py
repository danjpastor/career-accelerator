"""Guided documents for portfolio milestones."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from career_app.data.roadmap import PROJECT_DIRS, PROJECT_NAMES
from career_app.data.portfolio_tasks import task_spec
from career_app.services import task_workspace


def _slug(value: str, limit: int = 72) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower())
    value = value.strip("-") or "milestone"
    return value[:limit].rstrip("-")


def project_task_record(conn, task_id: int):
    return conn.execute(
        """SELECT id,project_id,sort_order,stage,label,completed,
                  description,definition_of_done,starter_path,
                  estimated_minutes,managed_key
           FROM project_tasks
           WHERE id=?""",
        (int(task_id),),
    ).fetchone()


def _project_dir(root: Path, project_id: int) -> Path:
    try:
        dirname = PROJECT_DIRS[int(project_id)]
    except KeyError as exc:
        raise ValueError(f"Unknown portfolio project: {project_id}") from exc
    return Path(root) / "projects" / dirname


def document_path(root: Path, row) -> Path:
    return (
        _project_dir(root, int(row["project_id"]))
        / "workspaces"
        / "milestones"
        / f"{int(row['sort_order']):02d}-{_slug(row['label'])}.md"
    )


def _starter_path(root: Path, row) -> Path | None:
    value = str(row["starter_path"] or "").strip()
    if not value:
        spec = task_spec(row["label"], int(row["project_id"]))
        value = spec.starter_path if spec is not None else ""
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = Path(root) / path
    path = path.resolve()
    root_resolved = Path(root).resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("Portfolio starter path leaves the repository.") from exc
    return path


def _fallback_template(row) -> str:
    return (
        f"# {row['label']}\n\n"
        f"## What you are doing\n\n{row['description'] or 'Complete this portfolio milestone.'}\n\n"
        f"## Done when\n\n{row['definition_of_done'] or 'Review and save the completed work.'}\n\n"
        "## Work plan\n\n- [ ] \n\n"
        "## Notes and decisions\n\n- \n\n"
        "## Validation\n\n- \n\n"
        "## Result\n\n- \n"
    )


def starter_content(root: Path, row) -> str:
    starter = _starter_path(root, row)
    if starter is None or not starter.is_file():
        return _fallback_template(row)
    template = starter.read_text(encoding="utf-8")
    project_id = int(row["project_id"])
    return template.format(
        project_id=project_id,
        project_name=PROJECT_NAMES.get(project_id, f"Project {project_id}"),
        project_dir=PROJECT_DIRS.get(project_id, ""),
        label=str(row["label"]),
        stage=str(row["stage"]),
        date=date.today().isoformat(),
    )


def ensure_document(conn, root: Path, task_id: int) -> dict:
    row = project_task_record(conn, task_id)
    if row is None:
        raise ValueError("The selected portfolio milestone no longer exists.")
    path = document_path(root, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(starter_content(root, row), encoding="utf-8")
    content = path.read_text(encoding="utf-8")
    return {
        "task": row,
        "document_path": path,
        "content": content,
        "project_name": PROJECT_NAMES.get(
            int(row["project_id"]), f"Project {int(row['project_id'])}"
        ),
    }


def save_document(conn, root: Path, task_id: int, content: str) -> Path:
    workspace = ensure_document(conn, root, task_id)
    path = workspace["document_path"]
    path.write_text(str(content), encoding="utf-8")
    return path


def set_completed(conn, task_id: int, completed: bool) -> dict:
    row = project_task_record(conn, task_id)
    if row is None:
        raise ValueError("The selected portfolio milestone no longer exists.")
    conn.execute(
        "UPDATE project_tasks SET completed=? WHERE id=?",
        (1 if completed else 0, int(task_id)),
    )
    conn.commit()
    return {
        "project_id": int(row["project_id"]),
        "task_id": int(task_id),
        "label": str(row["label"]),
        "completed": bool(completed),
    }


def open_document(path: Path) -> str:
    return task_workspace.open_artifact(str(path), root=path.parent)


def open_folder(path: Path) -> str:
    return task_workspace.open_folder(path.parent)
