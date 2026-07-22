from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
from typing import Any, Iterable
import uuid

from .portfolio_catalog import apply_runtime_catalog, write_project_catalog
from .paths import load_reset_layout
from .state import KEY_PORTFOLIO_STATUS, recompute_completion, set_settings


PACKAGE_TYPE = "career_accelerator.portfolio_projects"
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
MAX_PROJECTS = 5
MIN_PROJECT_MINUTES = 900
MAX_PROJECT_MINUTES = 1_800
MAX_PORTFOLIO_MINUTES = 4_200
MAX_TEXT_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".sql",
    ".py",
    ".ipynb",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".tsv",
    ".code-workspace",
}


class PortfolioImportError(ValueError):
    """Raised when a portfolio package is unsafe or does not satisfy the contract."""


@dataclass(frozen=True, slots=True)
class PortfolioImportResult:
    project_count: int
    milestone_count: int
    file_count: int
    backup_path: Path | None
    catalog_path: Path
    package_sha256: str
    project_directories: tuple[Path, ...]


def _require_text(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    minimum: int = 1,
    maximum: int = 20_000,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise PortfolioImportError(f"{context}.{key} must be text")
    value = value.strip()
    if len(value) < minimum:
        raise PortfolioImportError(f"{context}.{key} is required")
    if len(value) > maximum:
        raise PortfolioImportError(f"{context}.{key} exceeds {maximum} characters")
    return value


def _optional_text(
    mapping: dict[str, Any],
    key: str,
    *,
    maximum: int = 20_000,
) -> str:
    value = mapping.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise PortfolioImportError(f"{key} must be text")
    value = value.strip()
    if len(value) > maximum:
        raise PortfolioImportError(f"{key} exceeds {maximum} characters")
    return value


def _safe_slug(value: str, context: str) -> str:
    slug = value.strip().lower()
    if not slug or len(slug) > 80:
        raise PortfolioImportError(f"{context} must be between 1 and 80 characters")
    if slug[0] == "-" or slug[-1] == "-":
        raise PortfolioImportError(f"{context} cannot start or end with a hyphen")
    if not all(char.islower() or char.isdigit() or char == "-" for char in slug):
        raise PortfolioImportError(
            f"{context} may contain only lowercase letters, numbers, and hyphens"
        )
    return slug


def _safe_relative_path(value: str, context: str) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioImportError(f"{context} must be a relative path")
    value = value.replace("\\", "/").strip()
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise PortfolioImportError(f"{context} contains an unsafe path")
    protected = {"", ".git", ".github", ".venv", "venv", "__pycache__"}
    if any(part.lower() in protected or part.startswith(".") for part in path.parts):
        raise PortfolioImportError(f"{context} contains a protected or hidden path component")
    if ":" in value or value.startswith(("~", "/")):
        raise PortfolioImportError(f"{context} must remain inside the project directory")
    return path


def _safe_sql_identifier(value: str, context: str) -> str:
    identifier = value.strip()
    if not identifier or len(identifier) > 80:
        raise PortfolioImportError(f"{context} must be between 1 and 80 characters")
    if not (identifier[0].isalpha() or identifier[0] == "_"):
        raise PortfolioImportError(f"{context} must start with a letter or underscore")
    if not all(char.isalnum() or char == "_" for char in identifier):
        raise PortfolioImportError(f"{context} is not a safe SQL identifier")
    return identifier


def _string_list(value: Any, context: str, *, minimum: int = 0, maximum: int = 30) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PortfolioImportError(f"{context} must be a list of strings")
    cleaned = [item.strip() for item in value if item.strip()]
    if len(cleaned) < minimum:
        raise PortfolioImportError(f"{context} requires at least {minimum} entries")
    if len(cleaned) > maximum:
        raise PortfolioImportError(f"{context} allows at most {maximum} entries")
    return cleaned


def _normalize_milestones(project: dict[str, Any], context: str) -> list[dict[str, Any]]:
    raw_stages = project.get("stages")
    if not isinstance(raw_stages, list) or not raw_stages:
        raise PortfolioImportError(f"{context}.stages must contain at least one stage")
    milestones: list[dict[str, Any]] = []
    sort_order = 1
    for stage_index, stage in enumerate(raw_stages, start=1):
        if not isinstance(stage, dict):
            raise PortfolioImportError(f"{context}.stages[{stage_index}] must be an object")
        stage_name = _require_text(stage, "name", f"{context}.stages[{stage_index}]", maximum=100)
        raw_milestones = stage.get("milestones")
        if not isinstance(raw_milestones, list) or not raw_milestones:
            raise PortfolioImportError(
                f"{context}.stages[{stage_index}].milestones must not be empty"
            )
        for milestone_index, milestone in enumerate(raw_milestones, start=1):
            item_context = (
                f"{context}.stages[{stage_index}].milestones[{milestone_index}]"
            )
            if not isinstance(milestone, dict):
                raise PortfolioImportError(f"{item_context} must be an object")
            label = _require_text(milestone, "label", item_context, maximum=240)
            description = _require_text(
                milestone,
                "description",
                item_context,
                minimum=10,
                maximum=4_000,
            )
            definition_of_done = _require_text(
                milestone,
                "definition_of_done",
                item_context,
                minimum=5,
                maximum=4_000,
            )
            minutes = milestone.get("estimated_minutes", 60)
            if not isinstance(minutes, int) or not 10 <= minutes <= 4_800:
                raise PortfolioImportError(
                    f"{item_context}.estimated_minutes must be an integer from 10 to 4800"
                )
            starter_path = _optional_text(milestone, "starter_path", maximum=260)
            if starter_path:
                starter_path = str(_safe_relative_path(starter_path, f"{item_context}.starter_path"))
            milestones.append(
                {
                    "stage": stage_name,
                    "label": label,
                    "description": description,
                    "definition_of_done": definition_of_done,
                    "estimated_minutes": minutes,
                    "starter_path": starter_path,
                    "sort_order": sort_order,
                }
            )
            sort_order += 1
    if len(milestones) > 100:
        raise PortfolioImportError(f"{context} contains more than 100 milestones")
    return milestones


def _normalize_tables(project: dict[str, Any], context: str) -> list[dict[str, Any]]:
    datasets = project.get("datasets", [])
    if not isinstance(datasets, list):
        raise PortfolioImportError(f"{context}.datasets must be a list")
    normalized: list[dict[str, Any]] = []
    seen_dataset_ids: set[str] = set()
    for dataset_index, dataset in enumerate(datasets, start=1):
        dataset_context = f"{context}.datasets[{dataset_index}]"
        if not isinstance(dataset, dict):
            raise PortfolioImportError(f"{dataset_context} must be an object")
        dataset_id = _safe_slug(
            _require_text(dataset, "dataset_id", dataset_context, maximum=80),
            f"{dataset_context}.dataset_id",
        )
        if dataset_id in seen_dataset_ids:
            raise PortfolioImportError(f"Duplicate dataset_id: {dataset_id}")
        seen_dataset_ids.add(dataset_id)
        dataset_name = _require_text(dataset, "name", dataset_context, maximum=160)
        description = _require_text(dataset, "description", dataset_context, minimum=10)
        source_type = _require_text(dataset, "source_type", dataset_context, maximum=80)
        generation_notes = _optional_text(dataset, "generation_notes", maximum=20_000)
        raw_tables = dataset.get("tables", [])
        if not isinstance(raw_tables, list):
            raise PortfolioImportError(f"{dataset_context}.tables must be a list")
        tables: list[dict[str, Any]] = []
        seen_tables: set[str] = set()
        for table_index, table in enumerate(raw_tables, start=1):
            table_context = f"{dataset_context}.tables[{table_index}]"
            if not isinstance(table, dict):
                raise PortfolioImportError(f"{table_context} must be an object")
            table_name = _safe_sql_identifier(
                _require_text(table, "table_name", table_context, maximum=80),
                f"{table_context}.table_name",
            )
            if table_name.casefold() in seen_tables:
                raise PortfolioImportError(f"Duplicate table {table_name!r} in {dataset_context}")
            seen_tables.add(table_name.casefold())
            grain = _require_text(table, "grain", table_context, minimum=5, maximum=500)
            row_count_target = table.get("row_count_target")
            if row_count_target is not None and (
                not isinstance(row_count_target, int) or isinstance(row_count_target, bool) or row_count_target < 1
            ):
                raise PortfolioImportError(
                    f"{table_context}.row_count_target must be a positive integer or null"
                )
            columns = table.get("columns")
            if not isinstance(columns, list) or not columns:
                raise PortfolioImportError(f"{table_context}.columns must not be empty")
            normalized_columns: list[dict[str, Any]] = []
            seen_columns: set[str] = set()
            for column_index, column in enumerate(columns, start=1):
                column_context = f"{table_context}.columns[{column_index}]"
                if not isinstance(column, dict):
                    raise PortfolioImportError(f"{column_context} must be an object")
                name = _safe_sql_identifier(
                    _require_text(column, "name", column_context, maximum=80),
                    f"{column_context}.name",
                )
                if name.lower() in seen_columns:
                    raise PortfolioImportError(f"Duplicate column {name!r} in {table_context}")
                seen_columns.add(name.lower())
                normalized_columns.append(
                    {
                        "name": name,
                        "data_type": _require_text(column, "data_type", column_context, maximum=80),
                        "description": _require_text(
                            column,
                            "description",
                            column_context,
                            minimum=3,
                            maximum=1_000,
                        ),
                        "nullable": bool(column.get("nullable", True)),
                        "key_role": _optional_text(column, "key_role", maximum=80),
                        "example": _optional_text(column, "example", maximum=500),
                    }
                )
            tables.append(
                {
                    "table_name": table_name,
                    "grain": grain,
                    "row_count_target": row_count_target,
                    "columns": normalized_columns,
                }
            )
        normalized.append(
            {
                "dataset_id": dataset_id,
                "name": dataset_name,
                "description": description,
                "source_type": source_type,
                "generation_notes": generation_notes,
                "tables": tables,
            }
        )
    return normalized


def _normalize_kpis(project: dict[str, Any], context: str) -> list[dict[str, str]]:
    raw_kpis = project.get("kpis", [])
    if not isinstance(raw_kpis, list):
        raise PortfolioImportError(f"{context}.kpis must be a list")
    if len(raw_kpis) > 30:
        raise PortfolioImportError(f"{context}.kpis allows at most 30 entries")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_kpis, start=1):
        item_context = f"{context}.kpis[{index}]"
        if not isinstance(item, dict):
            raise PortfolioImportError(f"{item_context} must be an object")
        name = _require_text(item, "name", item_context, maximum=160)
        if name.casefold() in seen:
            raise PortfolioImportError(f"Duplicate KPI name {name!r} in {context}")
        seen.add(name.casefold())
        normalized.append(
            {
                "name": name,
                "definition": _require_text(
                    item, "definition", item_context, minimum=5, maximum=2_000
                ),
                "formula": _optional_text(item, "formula", maximum=2_000),
                "decision_use": _optional_text(item, "decision_use", maximum=2_000),
            }
        )
    return normalized


def _normalize_files(project: dict[str, Any], context: str) -> list[dict[str, str]]:
    files = project.get("files", [])
    if not isinstance(files, list):
        raise PortfolioImportError(f"{context}.files must be a list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    total_bytes = 0
    for index, item in enumerate(files, start=1):
        item_context = f"{context}.files[{index}]"
        if not isinstance(item, dict):
            raise PortfolioImportError(f"{item_context} must be an object")
        relative_path = _safe_relative_path(
            _require_text(item, "path", item_context),
            f"{item_context}.path",
        )
        if relative_path.suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_TEXT_EXTENSIONS))
            raise PortfolioImportError(
                f"{item_context}.path must use a supported text-file extension: {allowed}"
            )
        relative = str(relative_path)
        content = item.get("content")
        if not isinstance(content, str):
            raise PortfolioImportError(f"{item_context}.content must be UTF-8 text")
        encoded_size = len(content.encode("utf-8"))
        if encoded_size > MAX_TEXT_FILE_BYTES:
            raise PortfolioImportError(f"{item_context} exceeds the 5 MB text-file limit")
        total_bytes += encoded_size
        if total_bytes > 25 * 1024 * 1024:
            raise PortfolioImportError(f"{context}.files exceeds the 25 MB package limit")
        if relative.lower() in seen:
            raise PortfolioImportError(f"Duplicate generated file path {relative!r}")
        seen.add(relative.lower())
        normalized.append({"path": relative, "content": content})
    return normalized


INTEGRATED_CAPABILITIES = {
    "SQL": (" sql", "sql ", "duckdb", "joins", "querying"),
    "Python/pandas": ("python", "pandas", "jupyter", ".py", ".ipynb"),
    "Power BI/DAX": ("power bi", "power query", "dax", "dimensional model"),
    "Spreadsheet inspection": ("excel", "google sheets", "spreadsheet", "source inspection"),
    "GitHub/reproducibility": ("github", " git", "repository", "reproducib"),
    "Stakeholder communication": (
        "stakeholder",
        "presentation",
        "executive summary",
        "walkthrough",
        "recommendation",
    ),
}


def _project_capability_text(project: dict[str, Any]) -> str:
    payload = {
        "title": project.get("title", ""),
        "summary": project.get("summary", ""),
        "skills": project.get("skills", []),
        "tools": project.get("tools", []),
        "milestones": project.get("milestones", []),
        "files": [item.get("path", "") for item in project.get("files", [])],
        "decisions_supported": project.get("decisions_supported", []),
        "portfolio_story": project.get("portfolio_story", ""),
    }
    return " " + json.dumps(payload, ensure_ascii=False).casefold() + " "


def _validate_integrated_capabilities(project: dict[str, Any], context: str) -> None:
    text = _project_capability_text(project)
    missing = [
        label
        for label, keywords in INTEGRATED_CAPABILITIES.items()
        if not any(keyword.casefold() in text for keyword in keywords)
    ]

    tool_text = " ".join(project.get("tools", [])).casefold()
    required_tools = {
        "SQL": ("sql", "duckdb"),
        "Python/pandas": ("python", "pandas"),
        "Power BI": ("power bi",),
        "Spreadsheet": ("excel", "google sheets", "spreadsheet"),
        "Git/GitHub": ("git", "github"),
    }
    for label, keywords in required_tools.items():
        if not any(keyword in tool_text for keyword in keywords) and label not in missing:
            missing.append(label)

    file_paths = [str(item.get("path", "")).casefold() for item in project.get("files", [])]
    if not any(path.endswith(".sql") for path in file_paths):
        missing.append("SQL starter file")
    if not any(path.endswith((".py", ".ipynb")) for path in file_paths):
        missing.append("Python starter file")
    if not any(
        "power_bi" in path or "power-bi" in path or "dashboard" in path
        for path in file_paths
    ):
        missing.append("Power BI/dashboard build guide")

    if missing:
        raise PortfolioImportError(
            f"{context} must be an end-to-end analyst project. Missing integrated "
            "capabilities or starter evidence: " + ", ".join(dict.fromkeys(missing))
        )

    project_minutes = sum(
        int(item.get("estimated_minutes", 0) or 0)
        for item in project.get("milestones", [])
    )
    if not MIN_PROJECT_MINUTES <= project_minutes <= MAX_PROJECT_MINUTES:
        raise PortfolioImportError(
            f"{context} must be scoped to {MIN_PROJECT_MINUTES // 60}-"
            f"{MAX_PROJECT_MINUTES // 60} hours so all three projects fit the fixed "
            f"90-day program; received {project_minutes / 60:.1f} hours."
        )


def _capability_matrix(project: dict[str, Any]) -> str:
    text = _project_capability_text(project)
    lines = [
        f"# {project['title']} — Analyst Capability Matrix",
        "",
        "Every project is expected to combine the full analyst workflow. Use this checklist to link completed work to evidence.",
        "",
        "| Capability | Required evidence | Status |",
        "|---|---|---|",
    ]
    evidence = {
        "SQL": "Validated queries, joins, aggregations, and documented checks",
        "Python/pandas": "Reproducible preparation, validation, automation, or analysis",
        "Power BI/DAX": "Data model, measures, stakeholder dashboard, and design rationale",
        "Spreadsheet inspection": "Documented source review and initial quality observations",
        "GitHub/reproducibility": "README, environment/setup steps, organized files, and reproducible workflow",
        "Stakeholder communication": "Findings, recommendations, limitations, and presentation",
    }
    for label, keywords in INTEGRATED_CAPABILITIES.items():
        included = any(keyword.casefold() in text for keyword in keywords)
        lines.append(
            f"| {label} | {evidence[label]} | {'Planned' if included else 'Missing'} |"
        )
    lines.extend(["", "Replace **Planned** with links to completed evidence as the project progresses.", ""])
    return "\n".join(lines)


def validate_package(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PortfolioImportError("The portfolio import must contain a JSON object")
    if raw.get("package_type") != PACKAGE_TYPE:
        raise PortfolioImportError(
            f"package_type must be {PACKAGE_TYPE!r}"
        )
    schema_version = str(raw.get("schema_version", "")).strip()
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise PortfolioImportError(
            f"Unsupported schema_version {schema_version!r}; supported: "
            + ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
        )
    pathway_id = str(raw.get("pathway_id", "")).strip().lower()
    if pathway_id != "data_analytics":
        raise PortfolioImportError(
            "This release can import only data_analytics portfolio packages."
        )
    package_id = _safe_slug(
        _require_text(raw, "package_id", "package", maximum=80),
        "package.package_id",
    )
    generated_for = raw.get("generated_for", {})
    if not isinstance(generated_for, dict):
        raise PortfolioImportError("generated_for must be an object")
    profile = {
        "display_name": _require_text(generated_for, "display_name", "generated_for", maximum=120),
        "target_roles": _string_list(
            generated_for.get("target_roles", []),
            "generated_for.target_roles",
            minimum=1,
            maximum=8,
        ),
        "experience_summary": _require_text(
            generated_for,
            "experience_summary",
            "generated_for",
            minimum=20,
            maximum=5_000,
        ),
    }

    raw_projects = raw.get("projects")
    if not isinstance(raw_projects, list) or len(raw_projects) != 3:
        raise PortfolioImportError(
            "Data Analytics portfolio packages must contain exactly three projects so "
            "the fixed 90-day plan can schedule the complete portfolio."
        )

    projects: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_slugs: set[str] = set()
    for index, project in enumerate(raw_projects, start=1):
        context = f"projects[{index}]"
        if not isinstance(project, dict):
            raise PortfolioImportError(f"{context} must be an object")
        project_key = _safe_slug(
            _require_text(project, "project_key", context, maximum=80),
            f"{context}.project_key",
        )
        slug = _safe_slug(
            _require_text(project, "slug", context, maximum=80),
            f"{context}.slug",
        )
        if project_key in seen_keys:
            raise PortfolioImportError(f"Duplicate project_key: {project_key}")
        if slug in seen_slugs:
            raise PortfolioImportError(f"Duplicate project slug: {slug}")
        seen_keys.add(project_key)
        seen_slugs.add(slug)
        title = _require_text(project, "title", context, maximum=180)
        project_id = index
        directory = f"project-{index:02d}-{slug}"
        projects.append(
            {
                "project_id": project_id,
                "project_key": project_key,
                "slug": slug,
                "directory": directory,
                "title": title,
                "summary": _require_text(project, "summary", context, minimum=20, maximum=3_000),
                "business_problem": _require_text(
                    project,
                    "business_problem",
                    context,
                    minimum=30,
                    maximum=5_000,
                ),
                "stakeholders": _string_list(
                    project.get("stakeholders", []),
                    f"{context}.stakeholders",
                    minimum=1,
                    maximum=12,
                ),
                "decisions_supported": _string_list(
                    project.get("decisions_supported", []),
                    f"{context}.decisions_supported",
                    minimum=1,
                    maximum=15,
                ),
                "skills": _string_list(
                    project.get("skills", []),
                    f"{context}.skills",
                    minimum=3,
                    maximum=30,
                ),
                "tools": _string_list(
                    project.get("tools", []),
                    f"{context}.tools",
                    minimum=1,
                    maximum=20,
                ),
                "portfolio_story": _require_text(
                    project,
                    "portfolio_story",
                    context,
                    minimum=30,
                    maximum=5_000,
                ),
                "milestones": _normalize_milestones(project, context),
                "datasets": _normalize_tables(project, context),
                "kpis": _normalize_kpis(project, context),
                "files": _normalize_files(project, context),
            }
        )
        _validate_integrated_capabilities(projects[-1], context)

    total_portfolio_minutes = sum(
        int(milestone["estimated_minutes"])
        for project in projects
        for milestone in project["milestones"]
    )
    if total_portfolio_minutes > MAX_PORTFOLIO_MINUTES:
        raise PortfolioImportError(
            "The three projects require "
            f"{total_portfolio_minutes / 60:.1f} hours. The fixed 90-day program allows "
            f"at most {MAX_PORTFOLIO_MINUTES / 60:.1f} portfolio hours so SQL, Python, "
            "Power BI, foundational learning, practice, and job readiness can also be completed. "
            "Reduce dataset size, KPI count, or analysis breadth without removing the required toolchain."
        )

    generated_at = _require_text(raw, "generated_at", "package", maximum=100)
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PortfolioImportError("package.generated_at must be an ISO-8601 timestamp") from exc
    normalized = {
        "package_type": PACKAGE_TYPE,
        "schema_version": schema_version,
        "package_id": package_id,
        "pathway_id": pathway_id,
        "generated_at": generated_at,
        "generated_for": profile,
        "projects": projects,
    }
    return normalized


def load_and_validate_package(source: Path | str) -> tuple[dict[str, Any], str]:
    path = Path(source)
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise PortfolioImportError(f"Could not read {path}: {exc}") from exc
    if len(raw_bytes) > 30 * 1024 * 1024:
        raise PortfolioImportError("Portfolio package exceeds 30 MB")
    try:
        raw = json.loads(raw_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise PortfolioImportError("Portfolio package must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise PortfolioImportError(
            f"Portfolio package contains invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return validate_package(raw), hashlib.sha256(raw_bytes).hexdigest()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
    )


def _portfolio_is_populated(conn: sqlite3.Connection) -> bool:
    for table in ("project_tasks", "project_notes"):
        if _table_exists(conn, table):
            if conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
                return True
    return False


def _row_dict(row: sqlite3.Row | tuple[Any, ...], columns: list[str]) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return {key: row[key] for key in row.keys()}
    return dict(zip(columns, row))


def _snapshot_table(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, table):
        return []
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [item[0] for item in cursor.description or []]
    return [_row_dict(row, columns) for row in cursor.fetchall()]


def _create_backup(conn: sqlite3.Connection, backup_root: Path) -> Path | None:
    if not _portfolio_is_populated(conn):
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / timestamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_tasks": _snapshot_table(conn, "project_tasks"),
        "project_notes": _snapshot_table(conn, "project_notes"),
        "program_state": _snapshot_table(conn, "program_state"),
        "settings": [
            row
            for row in _snapshot_table(conn, "settings")
            if str(row.get("key", "")).startswith("onboarding.")
        ],
    }
    path = backup_dir / "portfolio_database_backup.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return backup_dir


def _markdown_list(values: Iterable[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def _project_readme(project: dict[str, Any]) -> str:
    milestone_lines = []
    for milestone in project["milestones"]:
        milestone_lines.append(
            f"- [ ] **{milestone['stage']} — {milestone['label']}**  \n"
            f"  {milestone['description']}  \n"
            f"  Definition of done: {milestone['definition_of_done']}"
        )
    return (
        f"# {project['title']}\n\n"
        f"## Project summary\n\n{project['summary']}\n\n"
        f"## Business problem\n\n{project['business_problem']}\n\n"
        f"## Stakeholders\n\n{_markdown_list(project['stakeholders'])}\n\n"
        f"## Decisions supported\n\n{_markdown_list(project['decisions_supported'])}\n\n"
        f"## Tools\n\n{_markdown_list(project['tools'])}\n\n"
        f"## Skills demonstrated\n\n{_markdown_list(project['skills'])}\n\n"
        f"## KPI definitions\n\n{_kpi_summary(project)}\n\n"
        f"## Portfolio story\n\n{project['portfolio_story']}\n\n"
        f"## Milestones\n\n" + "\n".join(milestone_lines) + "\n"
    )


def _data_dictionary(project: dict[str, Any]) -> str:
    lines = [f"# {project['title']} — Data Dictionary", ""]
    if not project["datasets"]:
        lines.extend(
            [
                "No fixed dataset was embedded in this package.",
                "Use the project specification to select or create a suitable dataset before analysis.",
                "",
            ]
        )
        return "\n".join(lines)
    for dataset in project["datasets"]:
        lines.extend(
            [
                f"## {dataset['name']}",
                "",
                dataset["description"],
                "",
                f"Source type: **{dataset['source_type']}**",
                "",
            ]
        )
        if dataset["generation_notes"]:
            lines.extend(["### Generation notes", "", dataset["generation_notes"], ""])
        for table in dataset["tables"]:
            lines.extend(
                [
                    f"### `{table['table_name']}`",
                    "",
                    f"**Grain:** {table['grain']}",
                    "",
                    "| Column | Type | Nullable | Key role | Description | Example |",
                    "|---|---|---:|---|---|---|",
                ]
            )
            for column in table["columns"]:
                lines.append(
                    "| {name} | {data_type} | {nullable} | {key_role} | {description} | {example} |".format(
                        name=column["name"],
                        data_type=column["data_type"],
                        nullable="Yes" if column["nullable"] else "No",
                        key_role=column["key_role"].replace("|", "\\|"),
                        description=column["description"].replace("|", "\\|"),
                        example=column["example"].replace("|", "\\|"),
                    )
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _kpi_summary(project: dict[str, Any]) -> str:
    if not project["kpis"]:
        return "No fixed KPIs were specified. Define decision-relevant measures before analysis."
    return "\n".join(
        f"- **{item['name']}** — {item['definition']}" for item in project["kpis"]
    )


def _kpi_guide(project: dict[str, Any]) -> str:
    lines = [f"# {project['title']} — KPI Definitions", ""]
    if not project["kpis"]:
        lines.extend(
            [
                "No KPIs were preselected.",
                "Define measures only after confirming the business decision and available data.",
                "",
            ]
        )
        return "\n".join(lines)
    for item in project["kpis"]:
        lines.extend([f"## {item['name']}", "", item["definition"], ""])
        if item["formula"]:
            lines.extend([f"**Formula:** `{item['formula']}`", ""])
        if item["decision_use"]:
            lines.extend(["**Decision use:**", "", item["decision_use"], ""])
    return "\n".join(lines).rstrip() + "\n"


def _project_specification(project: dict[str, Any]) -> str:
    return (
        f"# {project['title']} — Project Specification\n\n"
        f"## Problem\n\n{project['business_problem']}\n\n"
        f"## Audience\n\n{_markdown_list(project['stakeholders'])}\n\n"
        f"## Decisions this work should support\n\n{_markdown_list(project['decisions_supported'])}\n\n"
        f"## Required tools\n\n{_markdown_list(project['tools'])}\n\n"
        f"## Evidence to demonstrate\n\n{_markdown_list(project['skills'])}\n\n"
        f"## KPI definitions\n\n{_kpi_summary(project)}\n\n"
        "## Completion standard\n\n"
        "The final repository should contain reproducible data preparation, validated analysis, "
        "a stakeholder-facing output, documented findings, and a clear explanation of limitations.\n"
    )


def _normalized_project_files(project: dict[str, Any]) -> dict[str, str]:
    files = {item["path"]: item["content"] for item in project["files"]}
    files.setdefault("README.md", _project_readme(project))
    files.setdefault("documentation/project_specification.md", _project_specification(project))
    files.setdefault("documentation/analyst_capability_matrix.md", _capability_matrix(project))
    files.setdefault("documentation/data_dictionary.md", _data_dictionary(project))
    files.setdefault("documentation/kpi_definitions.md", _kpi_guide(project))
    files.setdefault(
        "documentation/analysis_findings.md",
        f"# {project['title']} — Analysis Findings\n\n"
        "Record validated findings, business implications, limitations, and recommended next actions here.\n",
    )
    files.setdefault(
        "documentation/project_reflection.md",
        f"# {project['title']} — Reflection\n\n"
        "Document what changed, what was difficult, how the work improved, and what you would do next.\n",
    )
    files.setdefault(
        "data/specifications/datasets.json",
        json.dumps({"datasets": project["datasets"]}, indent=2) + "\n",
    )
    files.setdefault(
        "data/specifications/kpis.json",
        json.dumps({"kpis": project["kpis"]}, indent=2) + "\n",
    )
    return files


def _write_staging_project(staging_root: Path, project: dict[str, Any]) -> Path:
    project_dir = staging_root / project["directory"]
    project_dir.mkdir(parents=True, exist_ok=False)
    for relative, content in _normalized_project_files(project).items():
        safe = _safe_relative_path(relative, "generated file path")
        destination = project_dir.joinpath(*safe.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
    return project_dir


def _archive_existing_directory(archive_base: Path, project_dir: Path, timestamp: str) -> Path:
    archive_root = archive_base / timestamp
    archive_root.mkdir(parents=True, exist_ok=True)
    destination = archive_root / project_dir.name
    counter = 1
    while destination.exists():
        destination = archive_root / f"{project_dir.name}-{counter}"
        counter += 1
    shutil.move(str(project_dir), str(destination))
    return destination


def _insert_database_rows(
    conn: sqlite3.Connection,
    package: dict[str, Any],
    package_sha256: str,
) -> int:
    milestone_count = 0
    with conn:
        conn.execute("DELETE FROM project_notes")
        conn.execute("DELETE FROM project_tasks")
        for project in package["projects"]:
            project_id = project["project_id"]
            sections = {
                "Overview": project["summary"],
                "Business Problem": project["business_problem"],
                "Stakeholders": "\n".join(project["stakeholders"]),
                "Decisions Supported": "\n".join(project["decisions_supported"]),
                "Skills": "\n".join(project["skills"]),
                "Tools": "\n".join(project["tools"]),
                "Portfolio Story": project["portfolio_story"],
                "Project Directory": project["directory"],
            }
            conn.executemany(
                "INSERT INTO project_notes(project_id, section, content) VALUES(?, ?, ?)",
                [(project_id, section, content) for section, content in sections.items()],
            )
            rows = [
                (
                    project_id,
                    milestone["sort_order"],
                    milestone["stage"],
                    milestone["label"],
                    0,
                    milestone["description"],
                    milestone["definition_of_done"],
                    milestone["starter_path"] or None,
                    milestone["estimated_minutes"],
                    f"portfolio:{project['project_key']}:{milestone['sort_order']}",
                )
                for milestone in project["milestones"]
            ]
            milestone_count += len(rows)
            conn.executemany(
                """
                INSERT INTO project_tasks(
                    project_id,
                    sort_order,
                    stage,
                    label,
                    completed,
                    description,
                    definition_of_done,
                    starter_path,
                    estimated_minutes,
                    managed_key
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        conn.execute(
            "UPDATE program_state SET current_project=?, total_projects=? WHERE id=1",
            (1, len(package["projects"])),
        )
        conn.executemany(
            """
            INSERT INTO settings(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            [
                (KEY_PORTFOLIO_STATUS, "completed"),
                ("onboarding.portfolio_package_id", package["package_id"]),
                ("onboarding.portfolio_package_sha256", package_sha256),
                ("onboarding.portfolio_imported_at", datetime.now().isoformat(timespec="seconds")),
            ],
        )
    recompute_completion(conn)
    return milestone_count


def import_portfolio_package(
    conn: sqlite3.Connection,
    repo_root: Path | str,
    source: Path | str,
    *,
    replace_existing: bool = False,
) -> PortfolioImportResult:
    repo_root = Path(repo_root).resolve()
    layout = load_reset_layout(repo_root)
    package, package_sha256 = load_and_validate_package(source)
    if _portfolio_is_populated(conn) and not replace_existing:
        raise PortfolioImportError(
            "Portfolio data already exists. Re-run the import with explicit replacement after reviewing the backup warning."
        )

    projects_root = layout.configured_path("projects_root")
    projects_root.mkdir(parents=True, exist_ok=True)
    backup_path = _create_backup(conn, layout.configured_path("portfolio_import_backup"))
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    staging_root = layout.configured_path("portfolio_import_staging") / uuid.uuid4().hex
    staging_root.mkdir(parents=True, exist_ok=False)
    installed_dirs: list[Path] = []
    archived_dirs: list[tuple[Path, Path]] = []
    catalog_target = layout.configured_path("portfolio_catalog")
    previous_catalog = catalog_target.read_bytes() if catalog_target.is_file() else None
    catalog_written = False
    try:
        staged = [_write_staging_project(staging_root, project) for project in package["projects"]]
        for staged_dir, project in zip(staged, package["projects"]):
            destination = projects_root / project["directory"]
            if destination.exists():
                if not replace_existing:
                    raise PortfolioImportError(
                        f"Project directory already exists: {destination.name}"
                    )
                archived = _archive_existing_directory(
                    layout.configured_path("portfolio_import_archive"), destination, timestamp
                )
                archived_dirs.append((archived, destination))
            shutil.move(str(staged_dir), str(destination))
            installed_dirs.append(destination)

        catalog_projects = [
            {
                "project_id": project["project_id"],
                "project_key": project["project_key"],
                "title": project["title"],
                "directory": project["directory"],
            }
            for project in package["projects"]
        ]
        catalog_path = write_project_catalog(catalog_projects, catalog_target)
        catalog_written = True
        milestone_count = _insert_database_rows(conn, package, package_sha256)
        apply_runtime_catalog(catalog_projects)
        file_count = sum(len(_normalized_project_files(project)) for project in package["projects"])
        return PortfolioImportResult(
            project_count=len(package["projects"]),
            milestone_count=milestone_count,
            file_count=file_count,
            backup_path=backup_path,
            catalog_path=catalog_path,
            package_sha256=package_sha256,
            project_directories=tuple(installed_dirs),
        )
    except Exception:
        if catalog_written:
            try:
                if previous_catalog is None:
                    catalog_target.unlink(missing_ok=True)
                else:
                    catalog_target.parent.mkdir(parents=True, exist_ok=True)
                    catalog_target.write_bytes(previous_catalog)
            except OSError:
                pass
        for destination in reversed(installed_dirs):
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
        for archived, original in reversed(archived_dirs):
            if archived.exists() and not original.exists():
                shutil.move(str(archived), str(original))
        raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
        staging_parent = staging_root.parent
        try:
            staging_parent.rmdir()
        except OSError:
            pass
