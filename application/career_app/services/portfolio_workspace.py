"""Guided documents for portfolio milestones."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from career_app.data.roadmap import PROJECT_DIRS, PROJECT_NAMES
from career_app.data.portfolio_tasks import task_spec
from career_app.services import project_data_workspace, task_workspace


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


def _is_relationship_task(row) -> bool:
    managed_key = str(row["managed_key"] or "") if "managed_key" in row.keys() else ""
    return (
        str(row["label"]).strip().casefold() == "validate relationships"
        or managed_key.endswith("validate_relationships")
    )


def _prepare_project_data(root: Path, row, *, refresh: bool = False):
    if not _is_relationship_task(row):
        return None
    return project_data_workspace.prepare_project_data_workspace(
        root,
        int(row["project_id"]),
        refresh=refresh,
        build=True,
    )


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


def starter_content(root: Path, row, data_plan=None) -> str:
    if _is_relationship_task(row):
        plan = data_plan or _prepare_project_data(root, row)
        if plan is not None:
            return project_data_workspace.relationship_guide_markdown(
                root,
                plan,
                str(row["label"]),
            )
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
    data_plan = _prepare_project_data(root, row)
    path = document_path(root, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(starter_content(root, row, data_plan), encoding="utf-8")
    content = path.read_text(encoding="utf-8")
    if data_plan is not None:
        upgraded = project_data_workspace.upgrade_relationship_guide(
            root,
            data_plan,
            content,
        )
        if upgraded != content:
            content = upgraded
            path.write_text(content, encoding="utf-8")
    return {
        "task": row,
        "document_path": path,
        "content": content,
        "project_name": PROJECT_NAMES.get(
            int(row["project_id"]), f"Project {int(row['project_id'])}"
        ),
        "data_workspace": data_plan,
    }


def refresh_data_workspace(conn, root: Path, task_id: int) -> dict:
    row = project_task_record(conn, task_id)
    if row is None:
        raise ValueError("The selected portfolio milestone no longer exists.")
    if not _is_relationship_task(row):
        raise ValueError("This milestone does not use the project data workspace.")
    plan = _prepare_project_data(root, row, refresh=True)
    path = document_path(root, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        content = path.read_text(encoding="utf-8")
        content = project_data_workspace.upgrade_relationship_guide(root, plan, content)
    else:
        content = project_data_workspace.relationship_guide_markdown(
            root, plan, str(row["label"])
        )
    path.write_text(content, encoding="utf-8")
    return {
        "task": row,
        "document_path": path,
        "content": content,
        "project_name": PROJECT_NAMES.get(
            int(row["project_id"]), f"Project {int(row['project_id'])}"
        ),
        "data_workspace": plan,
    }


def open_relationship_notebook(conn, root: Path, task_id: int) -> str:
    workspace = ensure_document(conn, root, task_id)
    plan = workspace.get("data_workspace")
    if plan is None:
        raise ValueError("This milestone does not have a prepared notebook workspace.")
    return project_data_workspace.open_notebook_in_vscode(plan)


# Compatibility alias for older UI actions.
def open_sql_starter(conn, root: Path, task_id: int) -> str:
    return open_relationship_notebook(conn, root, task_id)


def project_data_files(conn, root: Path, task_id: int) -> dict:
    workspace = ensure_document(conn, root, task_id)
    plan = workspace.get("data_workspace")
    if plan is None:
        return {}
    return {
        "notebook": plan.notebook_path,
        "database": plan.database_path,
        "workspace": plan.workspace_path,
        "config": plan.config_path,
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
