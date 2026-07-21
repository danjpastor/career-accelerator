"""Unified documents, schedules, artifacts, and sessions for roadmap tasks."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from career_app.database import state as program_state
from career_app.data.applied_exercises import (
    exercise_number_for_label as applied_number_for_label,
)
from career_app.data.duckdb_exercises import (
    exercise_number_for_label as duckdb_number_for_label,
)
from career_app.data.roadmap import PROJECT_DIRS, SQL_COMPANION
from career_app.services import (
    applied_workspace,
    duckdb_workspace,
    sql_workspace,
    tracks,
)


EXTERNAL_LEARNING_TRACKS = {
    "google",
    "datacamp",
}

GOOGLE_ROADMAP_PATTERN = re.compile(
    r"^\s*\[Google Course \d+\]",
    re.IGNORECASE,
)


WORKSPACE_TYPES = {
    "applied_lab": "Applied Lab Submission",
    "duckdb": "DuckDB Submission",
    "retrospective": "Weekly Retrospective",
    "study_plan": "Study Plan",
    "reflection": "Reflection",
    "portfolio": "Portfolio Task Notes",
    "sql": "SQL Task Notes",
    "learning": "Learning Notes",
    "task_notes": "Task Notes",
}


def _slug(value: str, limit: int = 72) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower())
    value = value.strip("-") or "task"
    return value[:limit].rstrip("-")


def _relative(root: Path, path: Path) -> str:
    path = Path(path).resolve()
    root = Path(root).resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _resolve(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = Path(root) / path
    return path.resolve()


def validate_iso_date(value: str | None, *, field: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD.") from exc
    return text


def task_record(conn, task_id: int):
    return conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status,
               m.priority,
               m.estimated_minutes,
               m.energy,
               m.deferred_until,
               m.destination,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason,
               m.description,
               m.definition_of_done,
               m.starter_path,
               m.managed_key,
               tt.track_key,
               tt.target_key,
               tt.source_label
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.id=?""",
        (int(task_id),),
    ).fetchone()


def is_external_learning_values(
    *,
    track_key=None,
    label=None,
) -> bool:
    track = str(track_key or "").strip().lower()
    if track in EXTERNAL_LEARNING_TRACKS:
        return True

    text = str(label or "").strip()
    lower = text.lower()
    return (
        GOOGLE_ROADMAP_PATTERN.match(text) is not None
        or "google course" in lower
        or "google certificate" in lower
        or lower.startswith("google •")
        or "datacamp" in lower
    )


def is_external_learning_task(row) -> bool:
    if row is None:
        return False
    keys = set(row.keys())
    label = (
        row["label"]
        if "label" in keys
        else row["task_label"]
        if "task_label" in keys
        else ""
    )
    track_key = (
        row["track_key"]
        if "track_key" in keys
        else None
    )
    return is_external_learning_values(
        track_key=track_key,
        label=label,
    )




_GUIDE_FILE_SUFFIXES = {
    ".csv",
    ".db",
    ".duckdb",
    ".json",
    ".md",
    ".pbix",
    ".py",
    ".sql",
    ".txt",
    ".xlsx",
    ".yaml",
    ".yml",
}
_ROOT_RELATIVE_PREFIXES = {
    "career",
    "curriculum",
    "data",
    "documentation",
    "practice",
    "projects",
    "resources",
    "weeks",
    "workspaces",
}


def sql_problem_title(row) -> str | None:
    """Return the DataLemur catalog title linked to a task, when present."""
    if row is None:
        return None
    keys = set(row.keys())
    track_key = str(row["track_key"] or "") if "track_key" in keys else ""
    target_key = str(row["target_key"] or "") if "target_key" in keys else ""
    label = str(row["label"] or "") if "label" in keys else ""
    catalog_titles = [str(entry[0]) for entry in SQL_COMPANION]
    if track_key.casefold() == "sql" and target_key.casefold().startswith("problem:"):
        direct = target_key.split(":", 1)[1].strip()
        if direct in catalog_titles:
            return direct
    normalized_label = re.sub(r"[^a-z0-9]+", " ", label.casefold()).strip()
    for title in catalog_titles:
        normalized_title = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
        if normalized_title and normalized_title in normalized_label:
            return title
    return None


def _workspace_creation_base(root: Path, document_path: Path) -> Path:
    root = Path(root).resolve()
    document_path = Path(document_path).resolve()
    projects_root = (root / "projects").resolve()
    try:
        relative = document_path.relative_to(projects_root)
    except ValueError:
        return document_path.parent
    if not relative.parts:
        return projects_root
    return projects_root / relative.parts[0]


def _path_like_guide_token(token: str) -> tuple[str, bool] | None:
    value = str(token or "").strip().strip('"\'')
    if not value or "\n" in value or len(value) > 220:
        return None
    value = value.replace("\\", "/")
    if value.startswith(("http://", "https://", "mailto:")):
        return None
    if value.startswith(("SELECT ", "FROM ", "WHERE ", "JOIN ")):
        return None
    is_directory = value.endswith("/")
    candidate = value.rstrip("/")
    if not candidate or candidate.startswith(("/", "~")):
        return None
    path = Path(candidate)
    if any(part in {"", ".", ".."} for part in path.parts):
        return None
    suffix = path.suffix.casefold()
    if not is_directory and suffix not in _GUIDE_FILE_SUFFIXES:
        return None
    return candidate, is_directory


def _starter_from_nearby_fence(content: str, start: int, suffix: str) -> str | None:
    if suffix.casefold() not in {".sql", ".py", ".json", ".yaml", ".yml", ".txt", ".csv"}:
        return None
    remainder = content[start : start + 2400]
    next_heading = re.search(r"\n#{1,6}\s", remainder)
    fence = re.search(r"```[^\n]*\n(.*?)\n```", remainder, flags=re.S)
    if fence is None:
        return None
    if next_heading is not None and fence.start() > next_heading.start():
        return None
    starter = fence.group(1).strip()
    return starter + "\n" if starter else None


def guide_referenced_paths(
    root: Path,
    document_path: Path,
    content: str,
) -> list[dict]:
    """Extract safe file/folder references from a Markdown task guide."""
    root = Path(root).resolve()
    document_path = Path(document_path).resolve()
    base = _workspace_creation_base(root, document_path).resolve()
    results: list[dict] = []
    seen: set[str] = set()
    for match in re.finditer(r"`([^`\n]+)`", str(content or "")):
        parsed = _path_like_guide_token(match.group(1))
        if parsed is None:
            continue
        relative_value, is_directory = parsed
        relative_path = Path(relative_value)
        if relative_path.parts and relative_path.parts[0].casefold() in _ROOT_RELATIVE_PREFIXES:
            resolved = (root / relative_path).resolve()
        else:
            resolved = (base / relative_path).resolve()
        if resolved != root and root not in resolved.parents:
            continue
        key = str(resolved).casefold()
        if key in seen:
            continue
        seen.add(key)
        starter = None
        if not is_directory:
            starter = _starter_from_nearby_fence(
                str(content or ""),
                match.end(),
                resolved.suffix,
            )
        results.append(
            {
                "reference": relative_value + ("/" if is_directory else ""),
                "resolved_path": resolved,
                "display_path": _relative(root, resolved),
                "is_directory": is_directory,
                "exists": resolved.exists(),
                "starter_content": starter,
                "base_path": base,
            }
        )
    return results


def create_guide_reference(
    root: Path,
    document_path: Path,
    reference: str,
    *,
    is_directory: bool,
    starter_content: str | None = None,
) -> Path:
    """Create one guide-declared path without allowing writes outside the repo."""
    root = Path(root).resolve()
    base = _workspace_creation_base(root, Path(document_path)).resolve()
    value = str(reference or "").strip().replace("\\", "/").rstrip("/")
    parsed = _path_like_guide_token(value + ("/" if is_directory else ""))
    if parsed is None:
        raise ValueError("The selected guide path is not a supported project file or folder.")
    relative_path = Path(parsed[0])
    if relative_path.parts and relative_path.parts[0].casefold() in _ROOT_RELATIVE_PREFIXES:
        destination = (root / relative_path).resolve()
    else:
        destination = (base / relative_path).resolve()
    if destination != root and root not in destination.parents:
        raise ValueError("The selected guide path would be outside the repository.")
    if is_directory:
        destination.mkdir(parents=True, exist_ok=True)
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        content = starter_content
        if content is None:
            if destination.suffix.casefold() == ".sql":
                content = (
                    "-- Starter file created from the linked task guide.\n"
                    "-- Follow the guide, replace placeholders, and save your validation results.\n"
                )
            elif destination.suffix.casefold() == ".py":
                content = (
                    '"""Starter file created from the linked task guide."""\n\n'
                )
            elif destination.suffix.casefold() == ".md":
                content = f"# {destination.stem.replace('_', ' ').replace('-', ' ').title()}\n\n"
            else:
                content = ""
        destination.write_text(str(content), encoding="utf-8")
    return destination

def workspace_supported(row) -> bool:
    return row is not None and not is_external_learning_task(row)


def workspace_supported_task_id(conn, task_id: int | None) -> bool:
    if task_id is None:
        return False
    return workspace_supported(
        task_record(conn, int(task_id))
    )


def cleanup_external_learning_workspaces(conn) -> dict:
    rows = conn.execute(
        """SELECT workspace_key,task_id,task_label,track_key
           FROM task_workspaces"""
    ).fetchall()

    removed = []
    for row in rows:
        task_row = (
            task_record(conn, int(row["task_id"]))
            if row["task_id"] is not None
            else None
        )
        external = (
            is_external_learning_task(task_row)
            if task_row is not None
            else is_external_learning_values(
                track_key=row["track_key"],
                label=row["task_label"],
            )
        )
        if not external:
            continue

        key = row["workspace_key"]
        conn.execute(
            """UPDATE study_sessions
               SET workspace_key=NULL
               WHERE workspace_key=?""",
            (key,),
        )
        conn.execute(
            """DELETE FROM task_workspace_artifacts
               WHERE workspace_key=?""",
            (key,),
        )
        conn.execute(
            """DELETE FROM task_workspaces
               WHERE workspace_key=?""",
            (key,),
        )
        removed.append(key)

    conn.commit()
    return {
        "removed": len(removed),
        "workspace_keys": removed,
    }


def workspace_key_for_task(conn, task_id: int) -> str:
    row = task_record(conn, task_id)
    if row is None:
        raise ValueError("The selected task no longer exists.")
    if row["track_key"] and row["target_key"]:
        return (
            f"track:{row['track_key']}:"
            f"{row['target_key']}"
        )
    return f"task:{int(task_id)}"


def classify_task(row) -> str:
    label = str(row["label"] or "")
    lower = label.lower()
    if applied_number_for_label(label) is not None:
        return "applied_lab"
    if duckdb_number_for_label(label) is not None:
        return "duckdb"
    if "retrospective" in lower:
        return "retrospective"
    if "study schedule" in lower or "study plan" in lower:
        return "study_plan"
    if "reflection" in lower:
        return "reflection"
    category = str(row["category"] or "General")
    if category == "Portfolio":
        return "portfolio"
    if category == "SQL":
        return "sql"
    if category == "Learning":
        return "learning"
    if category == "Review":
        return "reflection"
    return "task_notes"


def _default_document_path(
    root: Path,
    row,
    workspace_type: str,
    *,
    current_project: int,
) -> Path:
    root = Path(root)
    label = str(row["label"] or "")
    number = applied_number_for_label(label)
    if workspace_type == "applied_lab" and number is not None:
        return applied_workspace.ensure_submission(root, number)[0]

    number = duckdb_number_for_label(label)
    if workspace_type == "duckdb" and number is not None:
        return duckdb_workspace.ensure_submission(root, number)[0]

    week_dir = root / "weeks" / f"week-{int(row['week']):02d}"
    if workspace_type == "retrospective":
        return week_dir / "RETROSPECTIVE.md"
    if workspace_type == "study_plan":
        return week_dir / "STUDY_PLAN.md"
    if workspace_type == "reflection":
        if "career-transition" in label.lower():
            return week_dir / "CAREER_TRANSITION_REFLECTION.md"
        return week_dir / f"REFLECTION-task-{int(row['id'])}.md"
    if workspace_type == "portfolio":
        project_dir = root / "projects" / PROJECT_DIRS.get(
            int(current_project),
            PROJECT_DIRS[1],
        )
        return (
            project_dir
            / "workspaces"
            / f"task-{int(row['id'])}-{_slug(label)}.md"
        )
    return (
        root
        / "workspaces"
        / "tasks"
        / f"week-{int(row['week']):02d}"
        / f"task-{int(row['id'])}-{_slug(label)}.md"
    )


def _task_snapshot(conn, week: int) -> str:
    rows = conn.execute(
        """SELECT s.label,m.status,m.estimated_minutes,m.category
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.week=?
           ORDER BY m.priority,s.sort_order""",
        (int(week),),
    ).fetchall()
    if not rows:
        return "- No roadmap tasks are currently assigned."
    return "\n".join(
        (
            f"- [ ] {row['label']} "
            f"({row['estimated_minutes']}m • {row['category']} • "
            f"{row['status']})"
        )
        for row in rows
        if row["status"] != "Completed"
    ) or "- All assigned tasks are complete."


def _starter_template(root: Path, row) -> str | None:
    starter = str(row["starter_path"] or "").strip() if "starter_path" in row.keys() else ""
    if not starter:
        return None
    path = _resolve(Path(root), starter)
    if path is None or not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    return content.format(
        week=int(row["week"]),
        label=str(row["label"]),
        date=date.today().isoformat(),
    )


def _generic_template_marker(content: str) -> bool:
    text = str(content or "")
    return (
        "What needs to be completed and why?" in text
        or "## Objective\n\n## Plan" in text
        or "- DataCamp progress:" in text
    )


def _template(conn, root: Path, row, workspace_type: str) -> str:
    starter = _starter_template(root, row)
    if starter is not None:
        return starter

    week = int(row["week"])
    label = str(row["label"])
    today = date.today().isoformat()

    if workspace_type == "retrospective":
        return (
            f"# Week {week} Retrospective\n\n"
            "## Completion\n"
            "- Hours studied:\n"
            "- Google progress:\n"
            "- Accelerator Academy progress:\n"
            "- SQL practice:\n"
            "- Portfolio or Applied Labs:\n\n"
            "## Biggest Wins\n\n- \n\n"
            "## Blockers and Friction\n\n- \n\n"
            "## What I Learned\n\n- \n\n"
            "## Evidence Created\n\n- \n\n"
            "## Next-Week Adjustments\n\n- \n\n"
            "## Confidence\n\n- Score (1–10):\n"
            "- Why:\n"
        )

    if workspace_type == "study_plan":
        snapshot = _task_snapshot(conn, week)
        return (
            f"# Week {week} Study Plan\n\n"
            f"Created: {today}\n\n"
            "## Weekly Outcomes\n\n"
            "1. \n2. \n3. \n\n"
            "## Schedule\n\n"
            "### Monday\n- \n\n"
            "### Tuesday\n- \n\n"
            "### Wednesday\n- \n\n"
            "### Thursday\n- \n\n"
            "### Friday\n- \n\n"
            "### Saturday\n- \n\n"
            "### Sunday\n- Weekly retrospective and next-week setup\n\n"
            "## Current Roadmap Snapshot\n\n"
            f"{snapshot}\n\n"
            "## Constraints and Adjustments\n\n- \n"
        )

    if workspace_type == "reflection":
        return (
            f"# Reflection — {label}\n\n"
            "## Context\n\n"
            "What prompted this reflection?\n\n"
            "## What I Did\n\n- \n\n"
            "## What I Learned\n\n- \n\n"
            "## Skills and Transferable Experience\n\n- \n\n"
            "## Evidence or Example\n\n- \n\n"
            "## Next Action\n\n- \n"
        )

    return (
        f"# {label}\n\n"
        f"**Week:** {week}  \n"
        f"**Category:** {row['category']}  \n"
        f"**Created:** {today}\n\n"
        "## Task Brief\n\n"
        f"{str(row['description'] or 'Complete the task described in the title.')}\n\n"
        "## Definition of Done\n\n"
        f"{str(row['definition_of_done'] or 'Finish the work, review it, and save the result.')}\n\n"
        "## Plan\n\n- [ ] \n\n"
        "## Work Log\n\n"
        f"### {today}\n- \n\n"
        "## Decisions and Assumptions\n\n- \n\n"
        "## Validation or Review\n\n- \n\n"
        "## Blockers\n\n- \n\n"
        "## Result and Evidence\n\n- \n\n"
        "## Next Action\n\n- \n"
    )


def _workspace_row(conn, workspace_key: str):
    return conn.execute(
        """SELECT *
           FROM task_workspaces
           WHERE workspace_key=?""",
        (workspace_key,),
    ).fetchone()


def ensure_workspace(
    conn,
    root: Path,
    *,
    task_id: int | None = None,
    workspace_key: str | None = None,
    current_project: int = 1,
) -> dict:
    root = Path(root)
    existing = _workspace_row(conn, workspace_key) if workspace_key else None

    if existing is not None:
        stored_task_id = existing["task_id"]
        current_row = task_record(conn, stored_task_id) if stored_task_id else None
        current_key = (
            workspace_key_for_task(conn, stored_task_id)
            if current_row is not None
            else None
        )
        is_current = current_key == existing["workspace_key"]
        path = _resolve(root, existing["document_path"])
        if path is None:
            raise ValueError("The stored workspace has no document path.")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(existing["content"] or "", encoding="utf-8")
        content = path.read_text(encoding="utf-8")
        if current_row is not None and _generic_template_marker(content):
            upgraded = _starter_template(root, current_row)
            if upgraded is not None:
                content = upgraded
                path.write_text(content, encoding="utf-8")
        conn.execute(
            """UPDATE task_workspaces
               SET content=?,last_opened_at=CURRENT_TIMESTAMP,
                   updated_at=CURRENT_TIMESTAMP
               WHERE workspace_key=?""",
            (content, existing["workspace_key"]),
        )
        conn.commit()
        sync_managed_artifacts(
            conn,
            root,
            existing["workspace_key"],
        )
        return {
            "workspace_key": existing["workspace_key"],
            "task_id": stored_task_id,
            "task": current_row,
            "task_label": existing["task_label"],
            "workspace_type": existing["workspace_type"],
            "workspace_type_label": WORKSPACE_TYPES.get(
                existing["workspace_type"],
                "Task Workspace",
            ),
            "document_path": path,
            "content": content,
            "scheduled_for": existing["scheduled_for"],
            "is_current": is_current,
        }

    if task_id is None:
        raise ValueError("A task or workspace must be selected.")
    row = task_record(conn, int(task_id))
    if row is None:
        raise ValueError("The selected task no longer exists.")
    if not workspace_supported(row):
        raise ValueError(
            "Google Certificate and DataCamp activities are tracked through "
            "Learning and Study Sessions. They do not need Task Workspaces."
        )
    key = workspace_key_for_task(conn, int(task_id))

    existing = _workspace_row(conn, key)
    if existing is not None:
        return ensure_workspace(
            conn,
            root,
            workspace_key=key,
            current_project=current_project,
        )

    workspace_type = classify_task(row)
    path = _default_document_path(
        root,
        row,
        workspace_type,
        current_project=int(current_project),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            _template(conn, root, row, workspace_type),
            encoding="utf-8",
        )
    content = path.read_text(encoding="utf-8")

    conn.execute(
        """INSERT INTO task_workspaces
           (
               workspace_key,task_id,task_label,track_key,target_key,
               workspace_type,document_path,content,last_opened_at,
               updated_at
           )
           VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
           ON CONFLICT(workspace_key)
           DO UPDATE SET
               task_id=excluded.task_id,
               task_label=excluded.task_label,
               track_key=excluded.track_key,
               target_key=excluded.target_key,
               workspace_type=excluded.workspace_type,
               document_path=excluded.document_path,
               content=excluded.content,
               last_opened_at=CURRENT_TIMESTAMP,
               updated_at=CURRENT_TIMESTAMP""",
        (
            key,
            int(task_id),
            row["label"],
            row["track_key"],
            row["target_key"],
            workspace_type,
            _relative(root, path),
            content,
        ),
    )
    conn.commit()
    return ensure_workspace(
        conn,
        root,
        workspace_key=key,
        current_project=current_project,
    )


def save_document(
    conn,
    root: Path,
    workspace_key: str,
    content: str,
    *,
    scheduled_for: str | None = None,
) -> dict:
    row = _workspace_row(conn, workspace_key)
    if row is None:
        raise ValueError("The workspace no longer exists.")
    path = _resolve(root, row["document_path"])
    if path is None:
        raise ValueError("The workspace has no document path.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content or ""), encoding="utf-8")
    scheduled = validate_iso_date(
        scheduled_for,
        field="Scheduled date",
    )
    conn.execute(
        """UPDATE task_workspaces
           SET content=?,scheduled_for=?,updated_at=CURRENT_TIMESTAMP,
               last_opened_at=CURRENT_TIMESTAMP
           WHERE workspace_key=?""",
        (str(content or ""), scheduled, workspace_key),
    )
    conn.commit()
    return {
        "workspace_key": workspace_key,
        "document_path": path,
        "scheduled_for": scheduled,
    }



def _sql_problem_title(workspace) -> str | None:
    target_key = str(workspace["target_key"] or "")
    if str(workspace["track_key"] or "") == "sql" and target_key.startswith("problem:"):
        return target_key.split(":", 1)[1].strip() or None

    workspace_key = str(workspace["workspace_key"] or "")
    marker = "track:sql:problem:"
    if workspace_key.startswith(marker):
        return workspace_key[len(marker):].strip() or None

    label = str(workspace["task_label"] or "").strip()
    if label.lower().startswith("solve "):
        return label[6:].strip() or None
    return None


def _managed_artifact_candidates(conn, root: Path, workspace_key: str):
    workspace = _workspace_row(conn, workspace_key)
    if workspace is None:
        return []

    root = Path(root)
    candidates = []
    workspace_type = str(workspace["workspace_type"] or "")
    document_path = _resolve(root, workspace["document_path"])

    if (
        workspace_type in {"applied_lab", "duckdb"}
        and document_path is not None
        and document_path.exists()
    ):
        label = (
            "Applied Lab submission"
            if workspace_type == "applied_lab"
            else "DuckDB SQL submission"
        )
        candidates.append(
            {
                "source_key": f"workspace-document:{workspace_type}",
                "label": label,
                "path": document_path,
            }
        )

    title = _sql_problem_title(workspace)
    if title:
        practice = conn.execute(
            """SELECT solution_path
               FROM sql_practice
               WHERE platform='DataLemur'
                 AND title=?
               ORDER BY id DESC
               LIMIT 1""",
            (title,),
        ).fetchone()

        solution = None
        if practice is not None and practice["solution_path"]:
            solution = _resolve(root, practice["solution_path"])
        if solution is None or not solution.exists():
            expected = sql_workspace.solution_path(root, title).resolve()
            if expected.exists():
                solution = expected

        if solution is not None and solution.exists():
            candidates.append(
                {
                    "source_key": f"sql-solution:{title}",
                    "label": f"SQL solution — {title}",
                    "path": solution,
                }
            )

    return candidates


def _upsert_managed_artifact(
    conn,
    root: Path,
    workspace_key: str,
    *,
    path: Path,
    label: str,
    source_key: str,
) -> int:
    stored_path = _relative(root, Path(path))
    conn.execute(
        """INSERT INTO task_workspace_artifacts
           (
               workspace_key,artifact_path,label,
               is_managed,source_key
           )
           VALUES(?,?,?,1,?)
           ON CONFLICT(workspace_key,artifact_path)
           DO UPDATE SET
               label=excluded.label,
               is_managed=1,
               source_key=excluded.source_key""",
        (
            workspace_key,
            stored_path,
            label,
            source_key,
        ),
    )
    row = conn.execute(
        """SELECT id
           FROM task_workspace_artifacts
           WHERE workspace_key=?
             AND artifact_path=?""",
        (workspace_key, stored_path),
    ).fetchone()
    return int(row["id"])


def sync_managed_artifacts(
    conn,
    root: Path,
    workspace_key: str,
) -> int:
    linked = 0
    for candidate in _managed_artifact_candidates(
        conn,
        root,
        workspace_key,
    ):
        _upsert_managed_artifact(
            conn,
            root,
            workspace_key,
            path=candidate["path"],
            label=candidate["label"],
            source_key=candidate["source_key"],
        )
        linked += 1
    conn.commit()
    return linked


def link_sql_solution_artifact(
    conn,
    root: Path,
    *,
    title: str,
    solution_path: Path,
    task_id: int | None = None,
    current_project: int = 1,
) -> str | None:
    title = str(title or "").strip()
    if not title:
        return None

    workspace_key = f"track:sql:problem:{title}"
    workspace = _workspace_row(conn, workspace_key)
    if workspace is None and task_id is not None:
        workspace = ensure_workspace(
            conn,
            root,
            task_id=int(task_id),
            current_project=int(current_project),
        )
        workspace_key = workspace["workspace_key"]
    elif workspace is None:
        return None

    _upsert_managed_artifact(
        conn,
        root,
        workspace_key,
        path=Path(solution_path),
        label=f"SQL solution — {title}",
        source_key=f"sql-solution:{title}",
    )
    conn.commit()
    return workspace_key


def add_artifact(
    conn,
    workspace_key: str,
    artifact_path: str,
    label: str = "",
) -> int:
    path_text = str(artifact_path or "").strip()
    if not path_text:
        raise ValueError("Choose or enter an artifact path.")
    conn.execute(
        """INSERT INTO task_workspace_artifacts
           (
               workspace_key,artifact_path,label,
               is_managed,source_key
           )
           VALUES(?,?,?,0,NULL)
           ON CONFLICT(workspace_key,artifact_path)
           DO UPDATE SET label=excluded.label""",
        (workspace_key, path_text, str(label or "").strip()),
    )
    conn.commit()
    row = conn.execute(
        """SELECT id FROM task_workspace_artifacts
           WHERE workspace_key=? AND artifact_path=?""",
        (workspace_key, path_text),
    ).fetchone()
    return int(row["id"])


def artifacts(
    conn,
    workspace_key: str,
    *,
    root: Path | None = None,
):
    if root is not None:
        sync_managed_artifacts(
            conn,
            root,
            workspace_key,
        )
    return conn.execute(
        """SELECT * FROM task_workspace_artifacts
           WHERE workspace_key=?
           ORDER BY is_managed DESC,id DESC""",
        (workspace_key,),
    ).fetchall()


def remove_artifact(conn, artifact_id: int) -> None:
    row = conn.execute(
        """SELECT is_managed
           FROM task_workspace_artifacts
           WHERE id=?""",
        (int(artifact_id),),
    ).fetchone()
    if row is None:
        return
    if int(row["is_managed"] or 0):
        raise ValueError(
            "This artifact is linked automatically by the application and "
            "cannot be removed manually."
        )
    conn.execute(
        "DELETE FROM task_workspace_artifacts WHERE id=?",
        (int(artifact_id),),
    )
    conn.commit()


def sessions(conn, workspace_key: str):
    return conn.execute(
        """SELECT * FROM study_sessions
           WHERE workspace_key=?
           ORDER BY session_date DESC,id DESC""",
        (workspace_key,),
    ).fetchall()


def recent_unlinked_sessions(conn, limit: int = 20):
    return conn.execute(
        """SELECT * FROM study_sessions
           WHERE workspace_key IS NULL OR workspace_key=''
           ORDER BY id DESC
           LIMIT ?""",
        (int(limit),),
    ).fetchall()


def link_session(conn, session_id: int, workspace_key: str) -> None:
    workspace = _workspace_row(conn, workspace_key)
    if workspace is None:
        raise ValueError("The workspace no longer exists.")
    conn.execute(
        """UPDATE study_sessions
           SET task_id=?,workspace_key=?,task_label_snapshot=?
           WHERE id=?""",
        (
            workspace["task_id"],
            workspace_key,
            workspace["task_label"],
            int(session_id),
        ),
    )
    conn.commit()


def unlink_session(conn, session_id: int) -> None:
    conn.execute(
        """UPDATE study_sessions
           SET task_id=NULL,workspace_key=NULL,task_label_snapshot=NULL
           WHERE id=?""",
        (int(session_id),),
    )
    conn.commit()


def session_link_values(conn, task_id: int | None):
    if task_id is None:
        return None, None, None
    row = task_record(conn, int(task_id))
    if row is None:
        return None, None, None
    return (
        int(task_id),
        (
            None
            if is_external_learning_task(row)
            else workspace_key_for_task(conn, int(task_id))
        ),
        row["label"],
    )


def task_rows(
    conn,
    *,
    week: int | None = None,
    status: str | None = None,
    search: str = "",
) -> list[dict]:
    query = """SELECT s.id,s.week,s.label,s.completed,m.status,m.priority,
                      m.estimated_minutes,m.energy,m.category,
                      m.deferred_until,m.prerequisite_state,
                      tt.track_key
               FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               LEFT JOIN track_tasks tt ON tt.task_id=s.id
               WHERE 1=1"""
    values: list[object] = []
    if week is not None:
        query += " AND s.week=?"
        values.append(int(week))
    if status and status != "All":
        query += " AND m.status=?"
        values.append(status)
    if search.strip():
        query += " AND LOWER(s.label) LIKE ?"
        values.append(f"%{search.strip().lower()}%")
    query += " ORDER BY s.week,m.priority,s.sort_order"

    rows = []
    seen = set()
    for row in conn.execute(query, tuple(values)).fetchall():
        if is_external_learning_task(row):
            continue
        key = workspace_key_for_task(conn, int(row["id"]))
        logical_key = (
            key
            if row["track_key"]
            else (
                int(row["week"]),
                re.sub(
                    r"[^a-z0-9]+",
                    " ",
                    str(row["label"] or "").lower(),
                ).strip(),
            )
        )
        if logical_key in seen:
            continue
        seen.add(logical_key)
        workspace = _workspace_row(conn, key)
        artifact_count = conn.execute(
            """SELECT COUNT(*) FROM task_workspace_artifacts
               WHERE workspace_key=?""",
            (key,),
        ).fetchone()[0]
        session_count = conn.execute(
            """SELECT COUNT(*) FROM study_sessions
               WHERE workspace_key=?""",
            (key,),
        ).fetchone()[0]
        rows.append(
            {
                **dict(row),
                "workspace_key": key,
                "document_path": (
                    workspace["document_path"] if workspace else None
                ),
                "scheduled_for": (
                    workspace["scheduled_for"] if workspace else None
                ),
                "artifact_count": int(artifact_count),
                "session_count": int(session_count),
            }
        )
    return rows


def save_task_settings(
    conn,
    state,
    task_id: int,
    *,
    status: str,
    priority: int,
    estimated_minutes: int,
    energy: str,
    deferred_until: str | None,
    scheduled_for: str | None,
    workspace_key: str,
) -> int:
    valid_statuses = {
        "Not Started",
        "In Progress",
        "Blocked",
        "Deferred",
        "Completed",
    }
    if status not in valid_statuses:
        raise ValueError("Unsupported task status.")

    identity = tracks.task_edit_identity(conn, int(task_id))
    if identity is None:
        raise ValueError("The task no longer exists.")

    deferred = validate_iso_date(
        deferred_until,
        field="Deferred date",
    )
    scheduled = validate_iso_date(
        scheduled_for,
        field="Scheduled date",
    )
    if status == "Deferred" and deferred is None:
        deferred = (date.today() + timedelta(days=1)).isoformat()
    elif status != "Deferred":
        deferred = None

    was_completed = tracks.task_has_completion_evidence(conn, int(task_id))
    if was_completed and status != "Completed":
        tracks.undo_completion(
            conn,
            state,
            task_id=int(task_id),
        )

    current_state = program_state(conn)
    tracks.sync_all(conn, current_state)
    effective_task_id = tracks.resolve_task_edit_target(conn, identity)
    if effective_task_id is None:
        raise RuntimeError("The task could not be resolved after scheduling refreshed.")
    effective_task_id = int(effective_task_id)

    conn.execute(
        """UPDATE task_metadata
           SET status=?,priority=?,estimated_minutes=?,energy=?,
               deferred_until=?,
               prerequisite_state=CASE
                   WHEN ?='Blocked' THEN 'Blocked'
                   ELSE 'Ready'
               END,
               prerequisite_reason=CASE
                   WHEN ?='Blocked'
                   THEN 'Manually blocked in Task Workspace.'
                   ELSE NULL
               END
           WHERE task_id=?""",
        (
            status,
            int(priority),
            int(estimated_minutes),
            energy,
            deferred,
            status,
            status,
            effective_task_id,
        ),
    )
    conn.execute(
        "UPDATE sprint_tasks SET completed=? WHERE id=?",
        (1 if status == "Completed" else 0, effective_task_id),
    )
    conn.execute(
        """UPDATE task_workspaces
           SET task_id=?,scheduled_for=?,updated_at=CURRENT_TIMESTAMP
           WHERE workspace_key=?""",
        (effective_task_id, scheduled, workspace_key),
    )
    conn.commit()
    return effective_task_id


def mark_in_progress(conn, task_id: int) -> None:
    row = task_record(conn, int(task_id))
    if row is None:
        return
    if row["status"] == "Not Started" and row["prerequisite_state"] == "Ready":
        conn.execute(
            """UPDATE task_metadata
               SET status='In Progress',deferred_until=NULL
               WHERE task_id=?""",
            (int(task_id),),
        )
        conn.commit()


def ensure_weekly_workspace_task(conn, week: int, kind: str) -> int:
    week = int(week)
    if kind == "retrospective":
        row = conn.execute(
            """SELECT id FROM sprint_tasks
               WHERE week=? AND LOWER(label) LIKE '%retrospective%'
               ORDER BY id LIMIT 1""",
            (week,),
        ).fetchone()
        label = (
            "Complete the 90-day retrospective"
            if week == 12
            else f"Complete the Week {week} retrospective"
        )
        minutes = 25
    elif kind == "study_plan":
        row = conn.execute(
            """SELECT id FROM sprint_tasks
               WHERE week=? AND (
                   LOWER(label) LIKE '%study schedule%'
                   OR LOWER(label) LIKE '%study plan%'
               )
               ORDER BY id LIMIT 1""",
            (week,),
        ).fetchone()
        label = f"Create Week {week} study plan"
        minutes = 20
    else:
        raise ValueError("Unsupported weekly workspace type.")

    if row is not None:
        return int(row["id"])

    sort_order = conn.execute(
        """SELECT COALESCE(MAX(sort_order),0)+100
           FROM sprint_tasks WHERE week=?""",
        (week,),
    ).fetchone()[0]
    cursor = conn.execute(
        """INSERT INTO sprint_tasks
           (week,sort_order,label,completed)
           VALUES(?,?,?,0)""",
        (week, int(sort_order), label),
    )
    task_id = int(cursor.lastrowid)
    conn.execute(
        """INSERT INTO task_metadata
           (
               task_id,status,priority,estimated_minutes,energy,
               destination,category,prerequisite_state
           )
           VALUES(?,'Not Started',3,?,'Low',11,'Review','Ready')""",
        (task_id, minutes),
    )
    conn.commit()
    return task_id


def upsert_generated_section(
    conn,
    root: Path,
    task_id: int,
    *,
    heading: str,
    body: str,
    current_project: int,
) -> None:
    workspace = ensure_workspace(
        conn,
        root,
        task_id=int(task_id),
        current_project=int(current_project),
    )
    start_marker = f"<!-- {heading.upper().replace(' ', '_')}_START -->"
    end_marker = f"<!-- {heading.upper().replace(' ', '_')}_END -->"
    section = (
        f"{start_marker}\n## {heading}\n\n{body.strip()}\n{end_marker}"
    )
    content = workspace["content"]
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if pattern.search(content):
        content = pattern.sub(section, content)
    else:
        content = content.rstrip() + "\n\n" + section + "\n"
    save_document(
        conn,
        root,
        workspace["workspace_key"],
        content,
        scheduled_for=workspace["scheduled_for"],
    )


def open_folder(path: Path) -> str:
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_file():
        path = path.parent
    if os.name == "nt":
        os.startfile(str(path))
        return "File Explorer"
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return "Finder"
    command = shutil.which("xdg-open")
    if command:
        subprocess.Popen([command, str(path)])
        return "the file manager"
    raise RuntimeError("No supported folder-opening command was found.")


def open_artifact(path_text: str, *, root: Path) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        path = Path(root) / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        return open_folder(path)
    if os.name == "nt":
        os.startfile(str(path))
        return "the default Windows application"
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return "the default macOS application"
    command = shutil.which("xdg-open")
    if command:
        subprocess.Popen([command, str(path)])
        return "the default desktop application"
    raise RuntimeError(f"Open this artifact manually: {path}")
