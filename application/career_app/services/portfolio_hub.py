"""Data and artifact services for the Portfolio Workspace command center."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import re
from typing import Any

import yaml

from career_app.data.roadmap import PROJECT_DIRS, PROJECT_NAMES
from career_app.data.portfolio_tasks import task_spec
from career_app.services import portfolio_guides, project_data_workspace


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".ipynb_checkpoints",
    "node_modules",
    "patch_backup",
    "backups",
}

CATEGORY_ORDER = (
    "Notebooks",
    "SQL",
    "Power BI",
    "Reports",
    "Documentation",
    "Configuration",
    "Data",
    "Images",
    "Other",
)


@dataclass
class TableProfile:
    name: str
    source_path: str
    source_format: str
    row_count: int = 0
    columns: list[dict[str, Any]] = field(default_factory=list)
    head_columns: list[str] = field(default_factory=list)
    head_rows: list[list[str]] = field(default_factory=list)
    error: str = ""


def project_directory(root: Path, project_id: int) -> Path:
    directory = PROJECT_DIRS.get(int(project_id))
    if not directory:
        raise ValueError(f"Unknown project: {project_id}")
    return Path(root) / "projects" / directory


def project_name(project_id: int) -> str:
    return PROJECT_NAMES.get(int(project_id), f"Project {int(project_id)}")


def overview_markdown(root: Path, project_id: int) -> tuple[str, Path]:
    directory = project_directory(root, project_id)
    path = directory / "README.md"
    if path.is_file():
        return path.read_text(encoding="utf-8"), path
    return (
        f"# {project_name(project_id)}\n\n"
        "The project README has not been created yet. Complete the README milestone "
        "or create `README.md` in the project root.",
        path,
    )


def milestone_rows(conn, project_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id,project_id,sort_order,stage,label,completed,
               description,definition_of_done,starter_path,
               estimated_minutes,managed_key
        FROM project_tasks
        WHERE project_id=?
        ORDER BY sort_order,id
        """,
        (int(project_id),),
    ).fetchall()
    return [dict(row) for row in rows]


def milestone_summary(conn, project_id: int) -> dict[str, Any]:
    rows = milestone_rows(conn, project_id)
    total = len(rows)
    complete = sum(bool(row["completed"]) for row in rows)
    stage_rows: dict[str, dict[str, int]] = {}
    for row in rows:
        stage = str(row["stage"])
        item = stage_rows.setdefault(stage, {"complete": 0, "total": 0})
        item["total"] += 1
        item["complete"] += int(bool(row["completed"]))
    return {
        "total": total,
        "complete": complete,
        "percent": round(complete / total * 100) if total else 0,
        "stages": stage_rows,
    }


def _source_reader(path: Path, source_format: str) -> str:
    quoted = "'" + path.resolve().as_posix().replace("'", "''") + "'"
    if source_format == "csv":
        return f"read_csv_auto({quoted}, header=true)"
    if source_format == "parquet":
        return f"read_parquet({quoted})"
    if source_format == "json_lines":
        return f"read_json_auto({quoted}, format='newline_delimited')"
    if source_format == "json":
        return f"read_json_auto({quoted})"
    raise ValueError(f"Unsupported source format: {source_format}")


def _source_records(root: Path, project_id: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directory = project_directory(root, project_id)
    config = directory / "config" / "project_sources.yaml"
    if config.is_file():
        payload = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
        sources = [
            dict(item)
            for item in payload.get("sources") or []
            if isinstance(item, dict)
        ]
        relationships = [
            dict(item)
            for item in payload.get("relationships") or []
            if isinstance(item, dict)
        ]
        return sources, relationships

    discovered = project_data_workspace.discover_sources(directory)
    inferred = project_data_workspace.infer_relationships(discovered)
    return (
        [
            {
                "name": source.name,
                "path": source.path,
                "format": source.format,
                "view": source.view,
                "primary_key": source.primary_key,
            }
            for source in discovered
        ],
        [
            {
                "parent": relation.parent,
                "parent_key": relation.parent_key,
                "child": relation.child,
                "child_key": relation.child_key,
                "cardinality": relation.cardinality,
                "inferred": relation.inferred,
            }
            for relation in inferred
        ],
    )


def dataset_signature(root: Path, project_id: int) -> tuple:
    directory = project_directory(root, project_id)
    sources, _relationships = _source_records(root, project_id)
    values = [int(project_id)]
    config = directory / "config" / "project_sources.yaml"
    if config.is_file():
        stat = config.stat()
        values.append((config.as_posix(), stat.st_mtime_ns, stat.st_size))
    for source in sources:
        relative = str(source.get("path") or "").strip()
        path = directory / relative
        if path.is_file():
            stat = path.stat()
            values.append((relative, stat.st_mtime_ns, stat.st_size))
        else:
            values.append((relative, None, None))
    return tuple(values)


def dataset_profiles(root: Path, project_id: int, limit: int = 5) -> dict[str, Any]:
    directory = project_directory(root, project_id)
    sources, relationships = _source_records(root, project_id)
    profiles: list[TableProfile] = []

    try:
        import duckdb
    except Exception as exc:
        return {
            "tables": [],
            "relationships": relationships,
            "warnings": [f"DuckDB is unavailable: {exc}"],
        }

    connection = duckdb.connect(":memory:")
    try:
        for index, source in enumerate(sources, 1):
            relative = str(source.get("path") or "").strip()
            name = str(
                source.get("view")
                or source.get("name")
                or Path(relative).stem
                or f"table_{index}"
            )
            source_format = str(source.get("format") or "").strip()
            path = directory / relative
            profile = TableProfile(
                name=name,
                source_path=relative,
                source_format=source_format,
            )
            try:
                if not path.is_file():
                    raise FileNotFoundError(f"Source file not found: {relative}")
                reader = _source_reader(path, source_format)
                schema_rows = connection.execute(
                    f"DESCRIBE SELECT * FROM {reader}"
                ).fetchall()
                profile.columns = [
                    {
                        "name": str(row[0]),
                        "type": str(row[1]),
                        "nullable": str(row[2]) if len(row) > 2 else "",
                        "key": (
                            "Candidate key"
                            if str(row[0]) == str(source.get("primary_key") or "")
                            else ""
                        ),
                    }
                    for row in schema_rows
                ]
                profile.row_count = int(
                    connection.execute(
                        f"SELECT COUNT(*) FROM {reader}"
                    ).fetchone()[0]
                )
                cursor = connection.execute(
                    f"SELECT * FROM {reader} LIMIT {max(1, int(limit))}"
                )
                profile.head_columns = [str(item[0]) for item in cursor.description]
                profile.head_rows = [
                    ["" if value is None else str(value) for value in row]
                    for row in cursor.fetchall()
                ]
            except Exception as exc:
                profile.error = str(exc)
            profiles.append(profile)
    finally:
        connection.close()

    return {
        "tables": profiles,
        "relationships": relationships,
        "warnings": [],
    }


def _category(path: Path, project_dir: Path) -> str:
    relative = path.relative_to(project_dir)
    suffix = path.suffix.casefold()
    parts = {part.casefold() for part in relative.parts}
    if suffix == ".ipynb":
        return "Notebooks"
    if suffix == ".sql":
        return "SQL"
    if suffix == ".pbix" or "power-bi" in parts or "power_bi" in parts:
        return "Power BI"
    if "reports" in parts:
        return "Reports"
    if suffix in {".md", ".txt", ".docx", ".pdf"} or "documentation" in parts:
        return "Documentation"
    if suffix in {".yaml", ".yml", ".json", ".toml"} or "config" in parts:
        return "Configuration"
    if "data" in parts or suffix in {".csv", ".parquet", ".jsonl", ".ndjson"}:
        return "Data"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"} or "images" in parts:
        return "Images"
    return "Other"


def artifact_inventory(root: Path, project_id: int) -> dict[str, list[dict[str, Any]]]:
    directory = project_directory(root, project_id)
    grouped = {category: [] for category in CATEGORY_ORDER}
    if not directory.is_dir():
        return grouped

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(part in IGNORED_DIRS or part.startswith(".") for part in relative.parts):
            continue
        category = _category(path, directory)
        stat = path.stat()
        grouped[category].append(
            {
                "path": path,
                "relative": relative.as_posix(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        )
    return grouped


def _artifact_matches(project_dir: Path, pattern: str) -> list[Path]:
    value = str(pattern)
    if value.endswith("/"):
        path = project_dir / value.rstrip("/")
        if not path.is_dir():
            return []
        return [item for item in path.rglob("*") if item.is_file()]

    direct = project_dir / value
    if direct.is_file():
        return [direct]

    if "*" in value:
        return [item for item in project_dir.glob(value) if item.is_file()]

    parent = direct.parent
    if parent.is_dir():
        stem = direct.stem.casefold()
        return [
            item
            for item in parent.iterdir()
            if item.is_file() and stem in item.stem.casefold()
        ]
    return []


def deliverable_rows(conn, root: Path, project_id: int) -> list[dict[str, Any]]:
    directory = project_directory(root, project_id)
    results = []
    for row in milestone_rows(conn, project_id):
        spec = task_spec(str(row["label"]), project_id)
        key = spec.key if spec is not None else str(row.get("managed_key") or row["label"])
        patterns = portfolio_guides.expected_artifacts(str(row["label"]), project_id)
        matches: list[Path] = []
        for pattern in patterns:
            matches.extend(_artifact_matches(directory, pattern))
        unique = sorted({path.resolve() for path in matches})
        complete = bool(row["completed"])
        if complete and unique:
            status = "Ready"
        elif complete:
            status = "Completed — artifact not detected"
        elif unique:
            status = "Artifact exists — milestone open"
        else:
            status = "Planned"
        results.append(
            {
                "task_id": int(row["id"]),
                "stage": str(row["stage"]),
                "label": str(row["label"]),
                "status": status,
                "expected": ", ".join(patterns),
                "artifacts": [path for path in unique],
                "key": key,
            }
        )
    return results


def evidence_rows(conn, project_id: int) -> list[dict[str, Any]]:
    project = project_name(project_id)
    try:
        rows = conn.execute(
            """
            SELECT skill,source_type,source_name,description
            FROM evidence
            WHERE lower(source_type)='portfolio'
               OR source_name LIKE ?
               OR source_name LIKE ?
            ORDER BY skill,source_name
            """,
            (f"%Project {int(project_id)}%", f"%{project}%"),
        ).fetchall()
    except Exception:
        return []
    return [dict(row) for row in rows]


def readiness_rows(conn, root: Path, project_id: int) -> list[dict[str, Any]]:
    deliverables = {
        row["task_id"]: row
        for row in deliverable_rows(conn, root, project_id)
    }
    rows = []
    for task in milestone_rows(conn, project_id):
        skills = portfolio_guides.skills_for_task(str(task["label"]), project_id)
        deliverable = deliverables[int(task["id"])]
        for skill in skills:
            if bool(task["completed"]) and deliverable["artifacts"]:
                status = "Demonstrated"
            elif bool(task["completed"]):
                status = "Completed — evidence path needed"
            elif deliverable["artifacts"]:
                status = "In progress"
            else:
                status = "Not yet demonstrated"
            rows.append(
                {
                    "skill": skill,
                    "status": status,
                    "milestone": str(task["label"]),
                    "artifact": (
                        deliverable["artifacts"][0].relative_to(
                            project_directory(root, project_id)
                        ).as_posix()
                        if deliverable["artifacts"]
                        else ""
                    ),
                }
            )

    # Collapse duplicate skill names, keeping the strongest status.
    rank = {
        "Demonstrated": 3,
        "Completed — evidence path needed": 2,
        "In progress": 1,
        "Not yet demonstrated": 0,
    }
    collapsed: dict[str, dict[str, Any]] = {}
    for row in rows:
        previous = collapsed.get(row["skill"])
        if previous is None or rank[row["status"]] > rank[previous["status"]]:
            collapsed[row["skill"]] = row
    return sorted(collapsed.values(), key=lambda row: (-rank[row["status"]], row["skill"]))


def guide_audit_rows(conn, root: Path, project_id: int) -> list[dict[str, Any]]:
    directory = project_directory(root, project_id)
    results = []
    for task in milestone_rows(conn, project_id):
        slug = re.sub(r"[^a-z0-9]+", "-", str(task["label"]).casefold()).strip("-")[:72]
        path = (
            directory
            / "workspaces"
            / "milestones"
            / f"{int(task['sort_order']):02d}-{slug}.md"
        )
        if not path.is_file():
            results.append(
                {
                    "task_id": int(task["id"]),
                    "label": str(task["label"]),
                    "status": "Guide will be generated when opened",
                    "issues": [],
                    "path": path,
                }
            )
            continue
        content = path.read_text(encoding="utf-8")
        if str(task["label"]).strip().casefold() == "validate relationships":
            required = (
                "primary",
                "foreign",
                "cardinality",
                "consistency",
                "definition of done",
            )
            lowered = content.casefold()
            issues = [
                f"Missing relationship-guide coverage: {value}"
                for value in required
                if value not in lowered
            ]
            if len(content.split()) < 500:
                issues.append("Relationship guide is too brief")
        else:
            issues = portfolio_guides.audit_guide(content)
        results.append(
            {
                "task_id": int(task["id"]),
                "label": str(task["label"]),
                "status": "Pass" if not issues else "Needs upgrade",
                "issues": issues,
                "path": path,
            }
        )
    return results
