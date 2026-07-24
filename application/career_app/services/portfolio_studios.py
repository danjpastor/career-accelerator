"""Project-local state and artifact helpers for portfolio milestone studios.

Studios reduce file hunting and repeated setup while preserving the learner's
manual analysis, cleaning, modeling, interpretation, and writing work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

from career_app.data.roadmap import PROJECT_DIRS, PROJECT_NAMES
from career_app.services import notebook_workspace, project_artifacts, project_data_workspace, task_workspace


STUDIO_VERSION = 2
SUPPORTED_TABULAR_SUFFIXES = {".csv", ".parquet", ".json", ".jsonl", ".ndjson"}
SPREADSHEET_SUFFIXES = {".xlsx", ".xls", ".ods"}
SQL_SUFFIXES = {".sql"}
POWER_BI_SUFFIXES = {".pbix", ".pbit"}


@dataclass(frozen=True)
class StudioContext:
    root: Path
    project_id: int
    project_name: str
    project_dir: Path
    milestone_key: str
    task_id: int
    label: str

    @property
    def state_dir(self) -> Path:
        return self.project_dir / "workspaces" / "studios"

    @property
    def state_path(self) -> Path:
        return self.state_dir / f"{self.milestone_key}.json"


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")
    return text or "milestone"


def milestone_key(row) -> str:
    managed = str(row["managed_key"] or "") if "managed_key" in row.keys() else ""
    if managed.startswith("milestone:"):
        return managed.split(":", 1)[1]
    return _slug(str(row["label"] or "milestone"))


def context_for(root: Path, row) -> StudioContext:
    project_id = int(row["project_id"])
    try:
        project_directory = PROJECT_DIRS[project_id]
    except KeyError as exc:
        raise ValueError(f"Unknown portfolio project: {project_id}") from exc
    project_dir = (Path(root) / "projects" / project_directory).resolve()
    root_resolved = Path(root).resolve()
    try:
        project_dir.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("The project folder is outside the repository.") from exc
    return StudioContext(
        root=root_resolved,
        project_id=project_id,
        project_name=PROJECT_NAMES.get(project_id, f"Project {project_id}"),
        project_dir=project_dir,
        milestone_key=milestone_key(row),
        task_id=int(row["id"]),
        label=str(row["label"]),
    )


def sibling_context(context: StudioContext, milestone: str) -> StudioContext:
    """Return the same project context pointed at a different milestone store."""
    return StudioContext(
        root=context.root,
        project_id=context.project_id,
        project_name=context.project_name,
        project_dir=context.project_dir,
        milestone_key=str(milestone),
        task_id=context.task_id,
        label=context.label,
    )


def _backup_before_replace(context: StudioContext, path: Path, category: str) -> Path | None:
    """Create a timestamped project-local backup before replacing learner work."""
    path = Path(path)
    if not path.is_file():
        return None
    backup_dir = context.project_dir / "backups" / _slug(category)
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup = backup_dir / f"{path.stem}-{timestamp}{path.suffix}"
    shutil.copy2(path, backup)
    return backup


def _atomic_write_text(path: Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(str(text), encoding="utf-8")
    temporary.replace(path)
    return path


def default_state(context: StudioContext) -> dict[str, Any]:
    return {
        "version": STUDIO_VERSION,
        "project_id": context.project_id,
        "milestone_key": context.milestone_key,
        "updated_at": "",
        "data": {},
    }


def load_state(context: StudioContext) -> dict[str, Any]:
    if not context.state_path.is_file():
        return default_state(context)
    try:
        payload = json.loads(context.state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return default_state(context)
    if not isinstance(payload, dict):
        return default_state(context)
    payload.setdefault("version", STUDIO_VERSION)
    payload.setdefault("project_id", context.project_id)
    payload.setdefault("milestone_key", context.milestone_key)
    payload.setdefault("updated_at", "")
    payload.setdefault("data", {})
    if not isinstance(payload["data"], dict):
        payload["data"] = {}
    return payload


def save_state(context: StudioContext, data: dict[str, Any]) -> Path:
    context.state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": STUDIO_VERSION,
        "project_id": context.project_id,
        "milestone_key": context.milestone_key,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "data": data,
    }
    return _atomic_write_text(
        context.state_path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )


def _file_hash(path: Path, *, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        remaining = limit
        while True:
            size = 1024 * 1024 if remaining is None else min(1024 * 1024, remaining)
            if size <= 0:
                break
            block = handle.read(size)
            if not block:
                break
            digest.update(block)
            if remaining is not None:
                remaining -= len(block)
    return digest.hexdigest()


def _csv_profile(path: Path) -> tuple[int | None, list[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = sum(1 for _ in reader)
        return rows, [str(value) for value in header]
    except (OSError, UnicodeError, csv.Error):
        return None, []


def file_record(project_dir: Path, path: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    try:
        relative = path.relative_to(project_dir.resolve()).as_posix()
    except ValueError:
        relative = str(path)
    row_count = None
    columns: list[str] = []
    if path.suffix.casefold() == ".csv":
        row_count, columns = _csv_profile(path)
    stat = path.stat()
    return {
        "path": relative,
        "name": path.name,
        "suffix": path.suffix.casefold(),
        "size_bytes": int(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "row_count": row_count,
        "column_count": len(columns) if columns else None,
        "columns": columns,
        "fingerprint": _file_hash(path, limit=8 * 1024 * 1024),
    }


def raw_inventory(context: StudioContext) -> list[dict[str, Any]]:
    raw_dir = context.project_dir / "data" / "raw"
    if not raw_dir.is_dir():
        return []
    result = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.name.casefold() == "readme.md":
            continue
        if path.suffix.casefold() not in SUPPORTED_TABULAR_SUFFIXES | SPREADSHEET_SUFFIXES:
            continue
        result.append(file_record(context.project_dir, path))
    return result


def processed_inventory(context: StudioContext) -> list[dict[str, Any]]:
    result = []
    for relative in (Path("data/processed"), Path("data/cleaned")):
        base = context.project_dir / relative
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.casefold() in SUPPORTED_TABULAR_SUFFIXES | SPREADSHEET_SUFFIXES:
                result.append(file_record(context.project_dir, path))
    return result


def _heading_sections(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        match = re.match(r"^#{1,4}\s+(.+?)\s*$", line)
        if match:
            current = _slug(match.group(1))
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def project_brief_defaults(context: StudioContext) -> dict[str, str]:
    values = {
        "business_problem": "",
        "audience": "",
        "decision": "",
        "goals": "",
        "questions": "",
        "scope": "",
        "out_of_scope": "",
        "deliverables": "",
        "success_criteria": "",
        "assumptions": "",
    }
    candidates = (
        context.project_dir / "documentation" / "project_brief.md",
        context.project_dir / "PROJECT_CHARTER.md",
        context.project_dir / "README.md",
    )
    merged: dict[str, str] = {}
    for path in candidates:
        for key, value in _heading_sections(path).items():
            merged.setdefault(key, value)
    aliases = {
        "business_problem": ("business_problem", "problem", "objective", "project_objective"),
        "audience": ("audience", "stakeholders", "primary_stakeholder"),
        "decision": ("decision", "decision_to_support", "business_decision"),
        "goals": ("goals", "objectives", "objective"),
        "questions": ("business_questions", "questions", "key_questions"),
        "scope": ("scope", "included", "in_scope"),
        "out_of_scope": ("out_of_scope", "excluded", "not_in_scope"),
        "deliverables": ("deliverables", "outputs", "expected_outputs"),
        "success_criteria": ("success_criteria", "success", "done_when"),
        "assumptions": ("assumptions", "constraints", "known_assumptions"),
    }
    for target, source_keys in aliases.items():
        for source_key in source_keys:
            value = merged.get(source_key, "").strip()
            if value:
                values[target] = value
                break
    state = load_state(context).get("data", {})
    stored = state.get("brief") if isinstance(state, dict) else None
    if isinstance(stored, dict):
        for key in values:
            if str(stored.get(key) or "").strip():
                values[key] = str(stored[key])
    return values


def save_project_brief(context: StudioContext, values: dict[str, str]) -> Path:
    state = load_state(context).get("data", {})
    state["brief"] = {key: str(value).strip() for key, value in values.items()}
    save_state(context, state)
    path = context.project_dir / "documentation" / "project_brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = (
        ("business_problem", "Business problem"),
        ("audience", "Audience"),
        ("decision", "Decision this project supports"),
        ("goals", "Goals"),
        ("questions", "Business questions"),
        ("scope", "In scope"),
        ("out_of_scope", "Out of scope"),
        ("deliverables", "Deliverables"),
        ("success_criteria", "Success criteria"),
        ("assumptions", "Assumptions"),
    )
    lines = [f"# {context.project_name} — Approved Project Brief", ""]
    for key, label in labels:
        lines.extend([f"## {label}", "", str(values.get(key) or "_Not yet approved._").strip(), ""])
    text = "\n".join(lines).rstrip() + "\n"
    if path.is_file() and path.read_text(encoding="utf-8", errors="replace") != text:
        _backup_before_replace(context, path, "project-brief")
    _atomic_write_text(path, text)
    return path


def project_brief_issues(values: dict[str, str]) -> list[str]:
    required = {
        "business_problem": "Business problem",
        "audience": "Audience",
        "decision": "Decision",
        "questions": "Business questions",
        "scope": "Scope",
        "deliverables": "Deliverables",
        "success_criteria": "Success criteria",
    }
    issues = []
    for key, label in required.items():
        text = str(values.get(key) or "").strip()
        if not text:
            issues.append(f"{label} is missing.")
        elif len(text.split()) < 3:
            issues.append(f"{label} needs a little more detail.")
    return issues


def data_source_defaults(context: StudioContext) -> dict[str, Any]:
    state = load_state(context).get("data", {})
    stored = state.get("source_review") if isinstance(state, dict) else None
    values = {
        "source_type": "Synthetic" if "synthetic" in " ".join(item["path"] for item in raw_inventory(context)).casefold() else "",
        "provenance": "",
        "permitted_use": "Portfolio learning project",
        "coverage": "",
        "grain": "",
        "required_fields": "",
        "known_limitations": "",
        "approval_notes": "",
        "approved": False,
    }
    if isinstance(stored, dict):
        values.update(stored)
    return values


def save_source_manifest(context: StudioContext) -> Path:
    """Save the current raw-file inventory without changing the source review."""
    documentation = context.project_dir / "documentation"
    documentation.mkdir(parents=True, exist_ok=True)
    manifest_path = documentation / "data_source_manifest.csv"
    temporary = manifest_path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "path",
                "name",
                "format",
                "size_bytes",
                "row_count",
                "column_count",
                "fingerprint",
                "modified_at",
            ),
        )
        writer.writeheader()
        for item in raw_inventory(context):
            writer.writerow(
                {
                    "path": item["path"],
                    "name": item["name"],
                    "format": item["suffix"].lstrip("."),
                    "size_bytes": item["size_bytes"],
                    "row_count": item["row_count"] if item["row_count"] is not None else "",
                    "column_count": item["column_count"] if item["column_count"] is not None else "",
                    "fingerprint": item["fingerprint"],
                    "modified_at": item["modified_at"],
                }
            )
    if manifest_path.is_file():
        if manifest_path.read_bytes() == temporary.read_bytes():
            temporary.unlink()
            return manifest_path
        _backup_before_replace(context, manifest_path, "source-manifest")
    temporary.replace(manifest_path)
    return manifest_path


def save_data_source_review(context: StudioContext, values: dict[str, Any]) -> tuple[Path, Path]:
    state = load_state(context).get("data", {})
    state["source_review"] = values
    save_state(context, state)
    documentation = context.project_dir / "documentation"
    documentation.mkdir(parents=True, exist_ok=True)
    review_path = documentation / "data_source_review.md"
    review_text = "\n".join(
        [
            f"# {context.project_name} — Data Source Review",
            "",
            f"**Approval status:** {'Approved' if values.get('approved') else 'In review'}",
            "",
            "## Source type",
            "",
            str(values.get("source_type") or "_Not recorded._"),
            "",
            "## Where the data came from",
            "",
            str(values.get("provenance") or "_Not recorded._"),
            "",
            "## Permitted use",
            "",
            str(values.get("permitted_use") or "_Not recorded._"),
            "",
            "## Coverage",
            "",
            str(values.get("coverage") or "_Not recorded._"),
            "",
            "## Table grain",
            "",
            str(values.get("grain") or "_Not recorded._"),
            "",
            "## Required fields",
            "",
            str(values.get("required_fields") or "_Not recorded._"),
            "",
            "## Known limitations",
            "",
            str(values.get("known_limitations") or "_None recorded._"),
            "",
            "## Approval notes",
            "",
            str(values.get("approval_notes") or "_No notes._"),
            "",
        ]
    )
    if review_path.is_file() and review_path.read_text(encoding="utf-8", errors="replace") != review_text:
        _backup_before_replace(context, review_path, "data-source-review")
    _atomic_write_text(review_path, review_text)
    manifest_path = save_source_manifest(context)
    return review_path, manifest_path


def import_raw_files(context: StudioContext, paths: Iterable[Path]) -> list[Path]:
    destination = context.project_dir / "data" / "raw" / "imported"
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    for source in paths:
        source = Path(source)
        if not source.is_file():
            continue
        target = destination / source.name
        counter = 2
        while target.exists() and _file_hash(target) != _file_hash(source):
            target = destination / f"{source.stem}-{counter}{source.suffix}"
            counter += 1
        if not target.exists():
            shutil.copy2(source, target)
        created.append(target)
    return created


def _dictionary_candidates(context: StudioContext) -> tuple[Path, ...]:
    return (
        context.project_dir / "documentation" / "data_dictionary.csv",
        context.project_dir / "docs" / "source_brief" / "provided_data_dictionary_reference.csv",
        context.project_dir / "DATA_DICTIONARY.csv",
    )


def _canonical_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")


def _canonical_table(value: str) -> str:
    text = str(value or "").strip().casefold()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    text = _canonical_header(text)
    if text.startswith("raw_"):
        text = text[4:]
    return text


def _existing_dictionary_rows(context: StudioContext) -> list[dict[str, str]]:
    for path in _dictionary_candidates(context):
        if not path.is_file():
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                result = []
                for raw in reader:
                    normalized = {_canonical_header(key): str(value or "").strip() for key, value in raw.items()}
                    result.append(
                        {
                            "table": _canonical_table(normalized.get("table", normalized.get("dataset", ""))),
                            "column": normalized.get("column", normalized.get("field", "")),
                            "observed_type": normalized.get("observed_type", normalized.get("expected_type", normalized.get("data_type", ""))),
                            "expected_type": normalized.get("expected_type", normalized.get("data_type", "")),
                            "definition": normalized.get("definition", normalized.get("description", "")),
                            "nullable": normalized.get("nullable", normalized.get("allows_null", "")),
                            "key": normalized.get("key", normalized.get("key_role", "")),
                            "valid_values": normalized.get("valid_values", normalized.get("format_values", "")),
                            "relationship": normalized.get("relationship", ""),
                            "expected_unique": normalized.get("expected_unique", normalized.get("uniqueness_rule", "")),
                            "unit": normalized.get("unit", normalized.get("unit_of_measurement", "")),
                            "notes": normalized.get("notes", normalized.get("seeded_quality_notes", "")),
                            "cleaning_expectation": normalized.get("cleaning_expectation", normalized.get("cleaning_rule", "")),
                            "warning_resolution": normalized.get("warning_resolution", normalized.get("review_decision", "")),
                            "reviewed": normalized.get("reviewed", ""),
                        }
                    )
                return result
        except (OSError, UnicodeError, csv.Error):
            continue
    return []


def _duckdb_quote(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def _open_dictionary_connection(plan, *, source_backed: bool = False):
    """Open the prepared database, falling back to source-backed in-memory views.

    DuckDB permits only limited cross-process access to a database file. The
    portfolio notebook or VS Code extension may therefore hold ``project.duckdb``
    open while the learner reviews the dictionary. Falling back to an in-memory
    connection keeps the Studio usable without changing or locking the project
    database.
    """
    try:
        import duckdb
    except ImportError:
        return None
    if not source_backed and plan.database_path and Path(plan.database_path).is_file():
        try:
            return duckdb.connect(str(plan.database_path), read_only=True)
        except Exception:
            pass
    try:
        connection = duckdb.connect(":memory:")
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {_duckdb_quote(plan.schema)}")
        for source in plan.sources:
            source_path = (plan.project_dir / source.path).resolve()
            reader = project_data_workspace._reader_sql(  # noqa: SLF001 - shared project reader contract
                source_path,
                source.format,
                absolute=True,
            )
            connection.execute(
                f"CREATE OR REPLACE VIEW {_duckdb_quote(plan.schema)}.{_duckdb_quote(source.view)} AS "
                f"SELECT * FROM {reader}"
            )
        return connection
    except Exception:
        try:
            connection.close()
        except Exception:
            pass
        return None


REVIEWED_VALUES = {"yes", "true", "reviewed", "1", "✓"}


def _is_reviewed(value: Any) -> bool:
    return str(value or "").strip().casefold() in REVIEWED_VALUES


def _logical_type_group(value: Any) -> str:
    text = str(value or "").strip().casefold()
    if not text:
        return ""
    if any(token in text for token in ("bool", "yes/no", "true/false", "flag")):
        return "boolean"
    if any(token in text for token in ("date", "time", "timestamp")):
        return "date"
    if any(token in text for token in ("int", "decimal", "numeric", "number", "double", "float", "currency", "money", "percent", "hours")):
        return "number"
    if any(token in text for token in ("char", "text", "string", "category", "identifier", "id")):
        return "text"
    return text


def _warning_explanation(row: dict[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "").strip()
        for key in ("warning_resolution", "notes", "cleaning_expectation")
        if str(row.get(key) or "").strip()
    ).strip()


def _field_location(row: dict[str, Any]) -> str:
    table = str(row.get("table") or "").strip()
    column = str(row.get("column") or "").strip()
    return f"{table}.{column}" if table or column else "Unknown field"


def _relationship_target(value: Any) -> tuple[str, str] | None:
    """Extract a ``table.column`` target from legacy or current relationship text."""
    text = str(value or "").strip()
    if not text:
        return None
    for marker in ("→", "->"):
        if marker in text:
            text = text.rsplit(marker, 1)[-1].strip()
    text = text.replace("`", "").strip()
    if "." not in text:
        return None
    table, column = (part.strip() for part in text.rsplit(".", 1))
    table = _canonical_table(table)
    column = str(column).strip()
    if not table or not column:
        return None
    return table, column


def _normalize_key_role(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.casefold()
    if not text:
        return ""
    if "self" in lowered and ("reference" in lowered or "foreign" in lowered):
        return "Self-referencing foreign key"
    if "primary" in lowered and "candidate" in lowered:
        return "Primary key candidate"
    if "foreign" in lowered and "candidate" in lowered:
        return "Foreign key candidate"
    if "primary" in lowered:
        return "Primary key"
    if "foreign" in lowered:
        return "Foreign key"
    if lowered in {"none", "not a key", "no", "n/a", "not applicable"}:
        return "Not a key"
    return text


def _expected_null_rule(value: Any, null_count: int | None) -> str:
    text = str(value or "").strip()
    if text.casefold() in {
        "",
        "observed",
        "nulls observed",
        "no nulls observed",
        "observed only",
    }:
        return "Observed only — rule needs confirmation"
    return text


def _issue(
    severity: str,
    code: str,
    message: str,
    *,
    table: str = "",
    column: str = "",
) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "table": str(table or ""),
        "column": str(column or ""),
        "location": f"{table}.{column}" if table and column else str(table or column or "Dictionary"),
    }


def _dictionary_invalid_expression(column_ref: str, expected_type: Any) -> str:
    """Return a DuckDB aggregate for values that violate the expected logical type."""
    text_ref = f"TRIM(CAST({column_ref} AS VARCHAR))"
    logical_group = _logical_type_group(expected_type)
    if logical_group == "number":
        numeric_text = f"REGEXP_REPLACE({text_ref}, '[,$%]', '', 'g')"
        return (
            f"COUNT(*) FILTER (WHERE {column_ref} IS NOT NULL AND {text_ref} <> '' "
            f"AND TRY_CAST({numeric_text} AS DOUBLE) IS NULL)"
        )
    if logical_group == "date":
        return (
            f"COUNT(*) FILTER (WHERE {column_ref} IS NOT NULL AND {text_ref} <> '' "
            f"AND TRY_CAST({text_ref} AS DATE) IS NULL)"
        )
    if logical_group == "boolean":
        return (
            f"COUNT(*) FILTER (WHERE {column_ref} IS NOT NULL AND {text_ref} <> '' "
            f"AND LOWER({text_ref}) NOT IN "
            "('true','false','yes','no','y','n','1','0','t','f'))"
        )
    return "CAST(NULL AS BIGINT)"


def _profile_dictionary_table(
    connection,
    table_ref: str,
    schema_rows: list[tuple[str, str]],
    expected_types: dict[str, str],
) -> tuple[int | None, dict[str, dict[str, int | None]]]:
    """Profile every column in one aggregate query instead of several queries per field."""
    if connection is None or not schema_rows:
        return None, {}

    expressions = ["COUNT(*)"]
    for column, _observed_type in schema_rows:
        column_ref = _duckdb_quote(column)
        text_ref = f"TRIM(CAST({column_ref} AS VARCHAR))"
        expected_type = expected_types.get(_canonical_header(column), "")
        expressions.extend(
            (
                f"COUNT(*) FILTER (WHERE {column_ref} IS NULL)",
                f"COUNT(DISTINCT CAST({column_ref} AS VARCHAR))",
                (
                    f"COUNT(*) FILTER (WHERE {column_ref} IS NOT NULL "
                    f"AND {text_ref} = '')"
                ),
                _dictionary_invalid_expression(column_ref, expected_type),
            )
        )

    try:
        values = connection.execute(
            "SELECT " + ", ".join(expressions) + f" FROM {table_ref}"
        ).fetchone()
    except Exception:
        # Unusual nested/complex columns can make a wide aggregate fail. Preserve
        # correctness with a slower per-field fallback instead of losing all facts.
        try:
            count_row = connection.execute(
                f"SELECT COUNT(*) FROM {table_ref}"
            ).fetchone()
            row_count = int(count_row[0]) if count_row else 0
        except Exception:
            return None, {}
        fallback: dict[str, dict[str, int | None]] = {}
        for column, _observed_type in schema_rows:
            column_ref = _duckdb_quote(column)
            text_ref = f"TRIM(CAST({column_ref} AS VARCHAR))"
            try:
                stats = connection.execute(
                    "SELECT "
                    f"COUNT(*) FILTER (WHERE {column_ref} IS NULL), "
                    f"COUNT(DISTINCT CAST({column_ref} AS VARCHAR)), "
                    f"COUNT(*) FILTER (WHERE {column_ref} IS NOT NULL AND {text_ref} = ''), "
                    + _dictionary_invalid_expression(
                        column_ref,
                        expected_types.get(_canonical_header(column), ""),
                    )
                    + f" FROM {table_ref}"
                ).fetchone()
            except Exception:
                continue
            null_count = int(stats[0] or 0)
            distinct_count = int(stats[1] or 0)
            fallback[_canonical_header(column)] = {
                "null_count": null_count,
                "distinct_count": distinct_count,
                "blank_count": int(stats[2] or 0),
                "duplicate_count": max(0, row_count - null_count - distinct_count),
                "invalid_value_count": int(stats[3]) if stats[3] is not None else None,
            }
        return row_count, fallback
    if not values:
        return 0, {}

    row_count = int(values[0] or 0)
    profile: dict[str, dict[str, int | None]] = {}
    offset = 1
    for column, _observed_type in schema_rows:
        null_count = int(values[offset] or 0)
        distinct_count = int(values[offset + 1] or 0)
        blank_count = int(values[offset + 2] or 0)
        invalid_raw = values[offset + 3]
        invalid_count = int(invalid_raw) if invalid_raw is not None else None
        duplicate_count = max(0, row_count - null_count - distinct_count)
        profile[_canonical_header(column)] = {
            "null_count": null_count,
            "distinct_count": distinct_count,
            "blank_count": blank_count,
            "duplicate_count": duplicate_count,
            "invalid_value_count": invalid_count,
        }
        offset += 4
    return row_count, profile


def _dictionary_orphan_count(connection, plan, child: str, child_key: str, parent: str, parent_key: str) -> int | None:
    if connection is None:
        return None
    child_ref = f"{_duckdb_quote(plan.schema)}.{_duckdb_quote(child)}"
    parent_ref = f"{_duckdb_quote(plan.schema)}.{_duckdb_quote(parent)}"
    child_column = _duckdb_quote(child_key)
    parent_column = _duckdb_quote(parent_key)
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM " + child_ref + " AS child "
            "LEFT JOIN " + parent_ref + " AS parent "
            f"ON child.{child_column} = parent.{parent_column} "
            f"WHERE child.{child_column} IS NOT NULL AND parent.{parent_column} IS NULL"
        ).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return None


def dictionary_rows(
    context: StudioContext,
    *,
    refresh: bool = False,
    plan=None,
) -> list[dict[str, Any]]:
    """Return documented fields with fast, read-only observations from DuckDB.

    Normal Studio opening does not rebuild the project database or rewrite generated
    notebook assets. Column counts are collected in one query per table. More costly
    examples and frequency lists are loaded only when the learner selects a field.
    """
    if plan is None:
        plan = project_data_workspace.prepare_project_data_workspace(
            context.root,
            context.project_id,
            refresh=refresh,
            build=refresh,
            write_files=refresh,
        )
    existing = _existing_dictionary_rows(context)
    lookup = {
        (_canonical_table(item.get("table") or ""), _canonical_header(item.get("column") or "")): item
        for item in existing
        if item.get("table") and item.get("column")
    }
    relationship_lookup: dict[tuple[str, str], str] = {}
    reverse_relationship_lookup: dict[tuple[str, str], list[str]] = {}
    for relationship in plan.relationships:
        relationship_lookup[(relationship.child.casefold(), relationship.child_key.casefold())] = (
            f"{relationship.parent}.{relationship.parent_key}"
        )
        reverse_relationship_lookup.setdefault(
            (relationship.parent.casefold(), relationship.parent_key.casefold()), []
        ).append(f"{relationship.child}.{relationship.child_key}")

    result: list[dict[str, Any]] = []
    connection = _open_dictionary_connection(plan, source_backed=True)
    orphan_counts: dict[tuple[str, str, str, str], int | None] = {}
    try:
        for relationship in plan.relationships:
            key = (
                relationship.child.casefold(),
                relationship.child_key.casefold(),
                relationship.parent.casefold(),
                relationship.parent_key.casefold(),
            )
            orphan_counts[key] = _dictionary_orphan_count(
                connection,
                plan,
                relationship.child,
                relationship.child_key,
                relationship.parent,
                relationship.parent_key,
            )

        for source in plan.sources:
            schema_rows: list[tuple[str, str]] = []
            if connection is not None:
                try:
                    schema_rows = [
                        (str(row[0]), str(row[1]))
                        for row in connection.execute(
                            f"DESCRIBE SELECT * FROM {_duckdb_quote(plan.schema)}.{_duckdb_quote(source.view)}"
                        ).fetchall()
                    ]
                except Exception:
                    schema_rows = []
            if not schema_rows:
                schema_rows = [(column, "") for column in source.columns]

            expected_types = {
                _canonical_header(column): str(
                    lookup.get(
                        (_canonical_table(source.view), _canonical_header(column)), {}
                    ).get("expected_type")
                    or observed_type
                    or ""
                )
                for column, observed_type in schema_rows
            }
            table_ref = f"{_duckdb_quote(plan.schema)}.{_duckdb_quote(source.view)}"
            row_count, profile = _profile_dictionary_table(
                connection,
                table_ref,
                schema_rows,
                expected_types,
            )

            for column, observed_type in schema_rows:
                old = lookup.get((_canonical_table(source.view), _canonical_header(column)), {})
                observed_type = str(observed_type or old.get("observed_type") or "")
                stats = profile.get(_canonical_header(column), {})
                expected_type = str(old.get("expected_type") or observed_type)

                raw_key_role = str(old.get("key") or "").strip()
                key_role = _normalize_key_role(raw_key_role)
                if not key_role and source.primary_key and column.casefold() == source.primary_key.casefold():
                    key_role = "Primary key candidate"
                if not key_role:
                    key_role = "Not a key"
                relationship = str(
                    old.get("relationship")
                    or relationship_lookup.get((source.view.casefold(), column.casefold()), "")
                )
                if not relationship:
                    embedded_target = _relationship_target(raw_key_role)
                    if embedded_target:
                        relationship = f"{embedded_target[0]}.{embedded_target[1]}"
                if relationship and key_role == "Not a key":
                    key_role = "Foreign key candidate"

                orphan_count: int | None = None
                target = _relationship_target(relationship)
                if target:
                    parent_table, parent_column = target
                    orphan_key = (
                        source.view.casefold(),
                        column.casefold(),
                        parent_table.casefold(),
                        parent_column.casefold(),
                    )
                    if orphan_key not in orphan_counts:
                        orphan_counts[orphan_key] = _dictionary_orphan_count(
                            connection,
                            plan,
                            source.view,
                            column,
                            parent_table,
                            parent_column,
                        )
                    orphan_count = orphan_counts.get(orphan_key)

                referenced_by = reverse_relationship_lookup.get((source.view.casefold(), column.casefold()), [])
                expected_unique = str(old.get("expected_unique") or "").strip()
                if not expected_unique:
                    expected_unique = "Required" if "primary" in key_role.casefold() else "Not required"

                result.append(
                    {
                        "table": source.view,
                        "column": column,
                        "observed_type": observed_type,
                        "expected_type": expected_type,
                        "definition": str(old.get("definition") or ""),
                        "nullable": _expected_null_rule(
                            old.get("nullable"), stats.get("null_count")
                        ),
                        "key": key_role,
                        "valid_values": str(old.get("valid_values") or ""),
                        "relationship": relationship,
                        "expected_unique": expected_unique,
                        "unit": str(old.get("unit") or ""),
                        "notes": str(old.get("notes") or ""),
                        "cleaning_expectation": str(old.get("cleaning_expectation") or ""),
                        "warning_resolution": str(old.get("warning_resolution") or ""),
                        "reviewed": str(old.get("reviewed") or ""),
                        "row_count": row_count,
                        "null_count": stats.get("null_count"),
                        "blank_count": stats.get("blank_count"),
                        "distinct_count": stats.get("distinct_count"),
                        "duplicate_count": stats.get("duplicate_count"),
                        "invalid_value_count": stats.get("invalid_value_count"),
                        "orphan_count": orphan_count,
                        "sample_values": "",
                        "top_values": "",
                        "duplicate_values": "",
                        "orphan_values": "",
                        "observed_range": "",
                        "referenced_by": "\n".join(referenced_by),
                        "source_path": source.path,
                        "evidence_loaded": False,
                    }
                )
    finally:
        if connection is not None:
            connection.close()

    observed_keys = {(_canonical_table(item["table"]), _canonical_header(item["column"])) for item in result}
    for old in existing:
        key = (_canonical_table(old.get("table") or ""), _canonical_header(old.get("column") or ""))
        if key not in observed_keys and all(key):
            row = dict(old)
            row.update(
                {
                    "row_count": None,
                    "null_count": None,
                    "blank_count": None,
                    "distinct_count": None,
                    "duplicate_count": None,
                    "invalid_value_count": None,
                    "orphan_count": None,
                    "sample_values": "",
                    "top_values": "",
                    "duplicate_values": "",
                    "orphan_values": "",
                    "observed_range": "",
                    "referenced_by": "",
                    "missing_from_data": True,
                    "evidence_loaded": True,
                }
            )
            result.append(row)
    return result



def dictionary_snapshot(
    context: StudioContext,
    *,
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load rows and table metadata from one prepared project-data plan."""
    plan = project_data_workspace.prepare_project_data_workspace(
        context.root,
        context.project_id,
        refresh=refresh,
        build=refresh,
        write_files=refresh,
    )
    rows = dictionary_rows(context, refresh=refresh, plan=plan)
    tables = dictionary_table_metadata(
        context,
        rows,
        refresh=refresh,
        plan=plan,
    )
    return rows, tables

def dictionary_field_evidence(
    context: StudioContext,
    row: dict[str, Any],
) -> dict[str, Any]:
    """Load detailed examples for one selected field without blocking Studio opening."""
    table = str(row.get("table") or "").strip()
    column = str(row.get("column") or "").strip()
    if not table or not column or row.get("missing_from_data"):
        return {"evidence_loaded": True}

    plan = project_data_workspace.prepare_project_data_workspace(
        context.root,
        context.project_id,
        refresh=False,
        build=False,
        write_files=False,
    )
    connection = _open_dictionary_connection(plan, source_backed=True)
    if connection is None:
        return {"evidence_loaded": True}

    table_ref = f"{_duckdb_quote(plan.schema)}.{_duckdb_quote(table)}"
    column_ref = _duckdb_quote(column)
    evidence: dict[str, Any] = {"evidence_loaded": True}
    try:
        samples = connection.execute(
            f"SELECT DISTINCT CAST({column_ref} AS VARCHAR) "
            f"FROM {table_ref} WHERE {column_ref} IS NOT NULL LIMIT 8"
        ).fetchall()
        evidence["sample_values"] = "\n".join(str(value[0]) for value in samples)

        top = connection.execute(
            f"SELECT CAST({column_ref} AS VARCHAR), COUNT(*) AS value_count "
            f"FROM {table_ref} WHERE {column_ref} IS NOT NULL "
            f"GROUP BY 1 ORDER BY value_count DESC, 1 LIMIT 8"
        ).fetchall()
        evidence["top_values"] = "\n".join(
            f"{value[0]} — {int(value[1])}" for value in top
        )

        duplicates = connection.execute(
            f"SELECT CAST({column_ref} AS VARCHAR), COUNT(*) AS value_count "
            f"FROM {table_ref} WHERE {column_ref} IS NOT NULL "
            f"GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY value_count DESC, 1 LIMIT 8"
        ).fetchall()
        evidence["duplicate_values"] = "\n".join(
            f"{value[0]} — {int(value[1])} rows" for value in duplicates
        )

        observed_group = _logical_type_group(row.get("observed_type"))
        if observed_group in {"number", "date"}:
            range_row = connection.execute(
                f"SELECT CAST(MIN({column_ref}) AS VARCHAR), "
                f"CAST(MAX({column_ref}) AS VARCHAR) FROM {table_ref}"
            ).fetchone()
            if range_row and (range_row[0] is not None or range_row[1] is not None):
                evidence["observed_range"] = f"{range_row[0]} to {range_row[1]}"

        target = _relationship_target(row.get("relationship"))
        if target:
            parent_table, parent_column = target
            parent_ref = f"{_duckdb_quote(plan.schema)}.{_duckdb_quote(parent_table)}"
            parent_key = _duckdb_quote(parent_column)
            orphan_samples = connection.execute(
                "SELECT DISTINCT CAST(child." + column_ref + " AS VARCHAR) "
                "FROM " + table_ref + " AS child "
                "LEFT JOIN " + parent_ref + " AS parent "
                f"ON child.{column_ref} = parent.{parent_key} "
                f"WHERE child.{column_ref} IS NOT NULL AND parent.{parent_key} IS NULL LIMIT 8"
            ).fetchall()
            evidence["orphan_values"] = "\n".join(
                str(value[0]) for value in orphan_samples
            )
    finally:
        connection.close()
    return evidence

def dictionary_field_issues(
    row: dict[str, Any],
    *,
    include_review_status: bool = True,
) -> list[dict[str, str]]:
    """Return specific, navigable issues for one documented field."""
    issues: list[dict[str, str]] = []
    table = str(row.get("table") or "").strip()
    column = str(row.get("column") or "").strip()
    location = _field_location(row)
    explanation = _warning_explanation(row)

    if row.get("missing_from_data"):
        issues.append(_issue("Blocking", "missing_from_data", f"{location} is documented but was not found in the current project data.", table=table, column=column))
    if not str(row.get("definition") or "").strip():
        issues.append(_issue("Documentation", "definition", f"{location} needs a clear business definition.", table=table, column=column))
    if not str(row.get("expected_type") or "").strip():
        issues.append(_issue("Documentation", "expected_type", f"{location} needs an expected logical data type.", table=table, column=column))
    if not str(row.get("nullable") or "").strip():
        issues.append(_issue("Documentation", "nullable", f"{location} needs an expected null rule.", table=table, column=column))
    elif "needs confirmation" in str(row.get("nullable") or "").casefold() or str(row.get("nullable") or "").strip().casefold() in {"observed", "nulls observed", "no nulls observed"}:
        issues.append(_issue("Documentation", "nullable_confirmation", f"{location} only records what was observed. Confirm whether nulls are allowed by the business rule.", table=table, column=column))
    if not str(row.get("key") or "").strip():
        issues.append(_issue("Documentation", "key", f"{location} needs a confirmed key role, including 'Not a key' when appropriate.", table=table, column=column))
    if not str(row.get("expected_unique") or "").strip():
        issues.append(_issue("Documentation", "expected_unique", f"{location} needs an expected uniqueness rule.", table=table, column=column))

    key_role = str(row.get("key") or "").strip().casefold()
    relationship = str(row.get("relationship") or "").strip()
    if "candidate" in key_role:
        issues.append(_issue("Documentation", "candidate_key", f"{location} still has a candidate key role. Confirm the final key role.", table=table, column=column))
    if "foreign" in key_role and not relationship:
        issues.append(_issue("Documentation", "relationship", f"{location} is a foreign key but its parent table and column are not documented.", table=table, column=column))

    null_count = row.get("null_count")
    duplicate_count = row.get("duplicate_count")
    invalid_count = row.get("invalid_value_count")
    orphan_count = row.get("orphan_count")
    null_rule = str(row.get("nullable") or "").casefold()
    if null_count not in (None, 0) and any(token in null_rule for token in ("no null", "not null", "required")) and not explanation:
        issues.append(_issue("Blocking", "unexpected_nulls", f"{location} contains {null_count} null value(s), but the expected rule does not allow nulls. Explain the exception or planned correction.", table=table, column=column))
    elif null_count not in (None, 0) and any(token in null_rule for token in ("no null", "not null", "required")):
        issues.append(_issue("Suggestion", "unexpected_nulls_documented", f"{location} contains {null_count} null value(s), and the exception or correction plan has been documented.", table=table, column=column))
    if "primary" in key_role and duplicate_count not in (None, 0) and not explanation:
        issues.append(_issue("Blocking", "duplicate_primary_key", f"{location} is marked as a primary key but contains {duplicate_count} repeated non-null row(s). Document the decision or cleaning requirement.", table=table, column=column))
    elif "primary" in key_role and duplicate_count not in (None, 0):
        issues.append(_issue("Suggestion", "duplicate_primary_key_documented", f"{location} is marked as a primary key and contains {duplicate_count} repeated non-null row(s); the exception or cleaning decision has been documented.", table=table, column=column))
    if "primary" in key_role and null_count not in (None, 0) and not explanation:
        issues.append(_issue("Blocking", "null_primary_key", f"{location} is marked as a primary key but contains {null_count} null value(s). Document the decision or cleaning requirement.", table=table, column=column))
    elif "primary" in key_role and null_count not in (None, 0):
        issues.append(_issue("Suggestion", "null_primary_key_documented", f"{location} is marked as a primary key and contains {null_count} null value(s); the exception or cleaning decision has been documented.", table=table, column=column))
    if "foreign" in key_role and orphan_count not in (None, 0) and not explanation:
        issues.append(_issue("Blocking", "orphan_foreign_key", f"{location} contains {orphan_count} value(s) that do not match the documented parent relationship. Explain the exception or planned correction.", table=table, column=column))
    elif "foreign" in key_role and orphan_count not in (None, 0):
        issues.append(_issue("Suggestion", "orphan_foreign_key_documented", f"{location} contains {orphan_count} unmatched relationship value(s); the exception or correction plan has been documented.", table=table, column=column))

    observed_group = _logical_type_group(row.get("observed_type"))
    expected_group = _logical_type_group(row.get("expected_type"))
    if observed_group and expected_group and observed_group != expected_group and not explanation:
        issues.append(_issue("Documentation", "type_difference", f"{location} is observed as {row.get('observed_type') or 'unknown'} but expected to behave as {row.get('expected_type') or 'unknown'}. Explain how the mismatch will be handled.", table=table, column=column))
    elif observed_group and expected_group and observed_group != expected_group:
        issues.append(_issue("Suggestion", "type_difference_documented", f"{location} is observed as {row.get('observed_type') or 'unknown'} but expected as {row.get('expected_type') or 'unknown'}; the handling decision has been documented.", table=table, column=column))
    if invalid_count not in (None, 0) and not explanation:
        issues.append(_issue("Documentation", "invalid_values", f"{location} contains {invalid_count} value(s) that do not match the expected {row.get('expected_type') or 'format'}. Document the exception or cleaning plan.", table=table, column=column))
    elif invalid_count not in (None, 0):
        issues.append(_issue("Suggestion", "invalid_values_documented", f"{location} contains {invalid_count} value(s) that do not match the expected rule; the handling decision has been documented.", table=table, column=column))

    if include_review_status and not _is_reviewed(row.get("reviewed")):
        issues.append(_issue("Review", "not_reviewed", f"{location} has not been marked reviewed.", table=table, column=column))
    return issues



_TABLE_DECISION_PLACEHOLDERS = {
    "",
    "review required",
    "not recorded",
    "not available",
    "unknown",
}


def _clean_markdown_value(value: Any) -> str:
    """Normalize a short Markdown value without changing its meaning."""
    text = str(value or "").strip()
    text = text.replace("`", "")
    text = re.sub(r"^\*\*(.*?)\**$", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" \t\r\n|-")


def _table_decision_entry(
    decisions: dict[str, dict[str, Any]],
    table_name: str,
) -> dict[str, Any]:
    canonical = _canonical_table(table_name)
    if not canonical:
        return {}
    return decisions.setdefault(
        canonical,
        {
            "business_name": "",
            "description": "",
            "grain": "",
            "expected_primary_key": "",
            "sources": [],
        },
    )


def _record_table_decision(
    decisions: dict[str, dict[str, Any]],
    table_name: str,
    *,
    source: str,
    business_name: str = "",
    description: str = "",
    grain: str = "",
    expected_primary_key: str = "",
    overwrite: bool = False,
) -> None:
    entry = _table_decision_entry(decisions, table_name)
    if not entry:
        return
    values = {
        "business_name": _clean_markdown_value(business_name),
        "description": _clean_markdown_value(description),
        "grain": _clean_markdown_value(grain),
        "expected_primary_key": _clean_markdown_value(expected_primary_key),
    }
    for key, value in values.items():
        if value and (overwrite or not str(entry.get(key) or "").strip()):
            entry[key] = value
    source = str(source or "").strip()
    if source and source not in entry["sources"]:
        entry["sources"].append(source)


def _specification_markdown_candidates(context: StudioContext) -> list[Path]:
    """Find likely outputs from the earlier source/specification milestones."""
    explicit = (
        context.project_dir / "docs" / "synthetic_data_specification.md",
        context.project_dir / "documentation" / "synthetic_data_specification.md",
        context.project_dir / "documentation" / "data_source_review.md",
        context.project_dir / "documentation" / "data_source_specification.md",
        context.project_dir / "SYNTHETIC_DATA_SPECIFICATION.md",
        context.project_dir / "DATASET_SPECIFICATION.md",
    )
    candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in explicit:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                candidates.append(candidate)

    for base in (context.project_dir / "docs", context.project_dir / "documentation"):
        if not base.is_dir():
            continue
        for candidate in sorted(base.rglob("*.md")):
            lowered = candidate.name.casefold()
            if not any(token in lowered for token in ("specification", "source_review", "data_model")):
                continue
            if any(part.casefold() in {"backup", "backups", "archive", "archives"} for part in candidate.parts):
                continue
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                candidates.append(candidate)
    return candidates


def _parse_table_decisions_from_markdown(
    context: StudioContext,
    path: Path,
    known_tables: set[str],
    decisions: dict[str, dict[str, Any]],
) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    try:
        source_label = str(path.relative_to(context.project_dir)).replace("\\", "/")
    except ValueError:
        source_label = path.name

    # Table-definition sections usually contain explicit grain and key decisions.
    headings = list(
        re.finditer(
            r"(?m)^(#{2,5})\s+(.+?)\s*$",
            text,
        )
    )
    for heading_index, match in enumerate(headings):
        raw_heading = _clean_markdown_value(match.group(2))
        business_name = re.sub(r"^\d+(?:\.\d+)*\s+", "", raw_heading).strip()
        table_name = _canonical_table(business_name)
        if table_name not in known_tables:
            continue
        section_end = headings[heading_index + 1].start() if heading_index + 1 < len(headings) else len(text)
        section = text[match.end():section_end]

        def metadata_value(*labels: str) -> str:
            label_pattern = "|".join(re.escape(label) for label in labels)
            metadata = re.search(
                rf"(?im)^\s*(?:[-*]\s*)?\*{{0,2}}(?:{label_pattern})\s*:\s*\*{{0,2}}\s*(.+?)\s*$",
                section,
            )
            return _clean_markdown_value(metadata.group(1)) if metadata else ""

        description = metadata_value("Table purpose", "Purpose", "Description")
        if not description:
            for paragraph in re.split(r"\n\s*\n", section):
                paragraph = " ".join(line.strip() for line in paragraph.splitlines()).strip()
                if not paragraph:
                    continue
                if paragraph.startswith(("**", "|", "```", "#", "- ")):
                    continue
                if re.search(r"\b(?:File|Grain|Primary key|Foreign key)s?\s*:", paragraph, re.I):
                    continue
                if len(paragraph) >= 24:
                    description = _clean_markdown_value(paragraph)
                    break

        _record_table_decision(
            decisions,
            table_name,
            source=source_label,
            business_name=business_name,
            description=description,
            grain=metadata_value("Grain", "Table grain", "One row represents"),
            expected_primary_key=metadata_value("Primary key", "Expected primary key"),
        )

    # A compact dataset-size table may record grains even when no detailed section exists.
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [_clean_markdown_value(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        table_name = _canonical_table(cells[0])
        grain = cells[2]
        if table_name in known_tables and grain.casefold().startswith("one row"):
            _record_table_decision(
                decisions,
                table_name,
                source=source_label,
                business_name=cells[0],
                grain=grain,
            )


def _latest_primary_key_report(context: StudioContext) -> Path | None:
    report_root = context.project_dir / "reports"
    if not report_root.is_dir():
        return None
    candidates = list(report_root.rglob("primary_key_results.csv"))
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: (
            candidate.stat().st_mtime if candidate.exists() else 0,
            str(candidate.parent),
        ),
    )


def _prior_table_decisions(context: StudioContext, plan) -> dict[str, dict[str, Any]]:
    """Collect table decisions already completed in earlier portfolio milestones.

    Saved Data Dictionary Studio edits always take precedence later. This helper
    only supplies defaults from the approved specification, source configuration,
    and the newest relationship-validation report.
    """
    known_tables = {_canonical_table(source.view) for source in plan.sources}
    decisions: dict[str, dict[str, Any]] = {}

    for path in _specification_markdown_candidates(context):
        _parse_table_decisions_from_markdown(
            context,
            path,
            known_tables,
            decisions,
        )

    report = _latest_primary_key_report(context)
    if report is not None:
        try:
            with report.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for raw in reader:
                    normalized = {
                        _canonical_header(key): str(value or "").strip()
                        for key, value in raw.items()
                    }
                    table_name = _canonical_table(normalized.get("table", ""))
                    if table_name not in known_tables:
                        continue
                    key_text = normalized.get("key", "")
                    if "," in key_text:
                        key_text = "No single-column primary key"
                    _record_table_decision(
                        decisions,
                        table_name,
                        source=str(report.relative_to(context.project_dir)).replace("\\", "/"),
                        grain=normalized.get("grain", ""),
                        expected_primary_key=key_text,
                        overwrite=True,
                    )
        except (OSError, UnicodeError, csv.Error, ValueError):
            pass

    for source in plan.sources:
        _record_table_decision(
            decisions,
            source.view,
            source="config/project_sources.yaml",
            business_name=source.view.replace("_", " ").title(),
            expected_primary_key=source.primary_key,
        )

    return decisions


def _derived_table_purpose(
    business_name: str,
    table_rows: list[dict[str, Any]],
) -> str:
    """Compose a concise purpose from field definitions already approved earlier."""
    concepts: list[str] = []
    for row in table_rows:
        definition = _clean_markdown_value(row.get("definition"))
        if not definition:
            continue
        key_role = str(row.get("key") or "").casefold()
        lowered = definition.casefold()
        if "primary" in key_role and ("identifier" in lowered or lowered.startswith("unique")):
            continue
        concept = definition.rstrip(". ")
        if concept:
            concept = concept[:1].casefold() + concept[1:]
        if concept and concept.casefold() not in {item.casefold() for item in concepts}:
            concepts.append(concept)
        if len(concepts) == 3:
            break

    base = (
        f"Contains records for {str(business_name or 'this table').casefold()} "
        "used by the approved project analysis"
    )
    if not concepts:
        return base + "."
    if len(concepts) == 1:
        detail = concepts[0]
    elif len(concepts) == 2:
        detail = f"{concepts[0]} and {concepts[1]}"
    else:
        detail = f"{concepts[0]}, {concepts[1]}, and {concepts[2]}"
    return f"{base}, including {detail}."

def dictionary_table_metadata(
    context: StudioContext,
    rows: list[dict[str, Any]] | None = None,
    *,
    refresh: bool = False,
    plan=None,
) -> dict[str, dict[str, Any]]:
    """Return table-level documentation and observed facts for the studio.

    Table purpose, grain, and expected primary key are prefilled from completed
    specification and relationship-validation milestones. Existing learner edits
    always win, and refreshing observed data never replaces those decisions.
    """
    if plan is None:
        plan = project_data_workspace.prepare_project_data_workspace(
            context.root,
            context.project_id,
            refresh=refresh,
            build=refresh,
            write_files=refresh,
        )
    if rows is None:
        rows = dictionary_rows(context, refresh=refresh, plan=plan)
    saved = load_state(context).get("data", {}).get("dictionary_tables", {})
    if not isinstance(saved, dict):
        saved = {}
    sources = {source.view.casefold(): source for source in plan.sources}
    prior_decisions = _prior_table_decisions(context, plan)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("table") or ""), []).append(row)

    relationships_by_table: dict[str, list[str]] = {}
    for relationship in plan.relationships:
        relationships_by_table.setdefault(relationship.child, []).append(
            f"{relationship.child}.{relationship.child_key} → {relationship.parent}.{relationship.parent_key}"
        )
        relationships_by_table.setdefault(relationship.parent, []).append(
            f"{relationship.child}.{relationship.child_key} → {relationship.parent}.{relationship.parent_key}"
        )

    result: dict[str, dict[str, Any]] = {}
    for table, table_rows in grouped.items():
        old = saved.get(table, saved.get(table.casefold(), {}))
        if not isinstance(old, dict):
            old = {}
        source = sources.get(table.casefold())
        prior = prior_decisions.get(_canonical_table(table), {})
        inferred_key = source.primary_key if source else ""

        old_business_name = str(old.get("business_name") or "").strip()
        old_description = str(old.get("description") or "").strip()
        old_grain = str(old.get("grain") or "").strip()
        old_key = str(old.get("expected_primary_key") or "").strip()
        key_is_placeholder = old_key.casefold() in _TABLE_DECISION_PLACEHOLDERS

        business_name = (
            old_business_name
            or str(prior.get("business_name") or "").strip()
            or table.replace("_", " ").title()
        )
        description = old_description or str(prior.get("description") or "").strip()
        if not description and prior.get("sources"):
            description = _derived_table_purpose(business_name, table_rows)
        grain = old_grain or str(prior.get("grain") or "").strip()
        expected_key = (
            old_key
            if old_key and not key_is_placeholder
            else str(prior.get("expected_primary_key") or inferred_key or "Review required").strip()
        )

        autofilled_fields: list[str] = []
        if not old_business_name and business_name:
            autofilled_fields.append("business name")
        if not old_description and description:
            autofilled_fields.append("table purpose")
        if not old_grain and grain:
            autofilled_fields.append("grain")
        if (not old_key or key_is_placeholder) and expected_key.casefold() != "review required":
            autofilled_fields.append("expected primary key")

        result[table] = {
            "table": table,
            "business_name": business_name,
            "description": description,
            "grain": grain,
            "expected_primary_key": expected_key,
            "notes": str(old.get("notes") or ""),
            "reviewed": str(old.get("reviewed") or ""),
            "row_count": table_rows[0].get("row_count") if table_rows else None,
            "column_count": len(table_rows),
            "source_path": str(table_rows[0].get("source_path") or "") if table_rows else "",
            "relationships": "\n".join(sorted(set(relationships_by_table.get(table, [])))),
            "autofilled_fields": autofilled_fields,
            "autofill_source": "; ".join(str(item) for item in prior.get("sources", []) if str(item).strip()),
        }
    return result


def dictionary_table_issues(
    table: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    include_review_status: bool = True,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    table_name = str(table.get("table") or "").strip()
    if not str(table.get("description") or "").strip():
        issues.append(_issue("Documentation", "table_description", f"{table_name} needs a table-level business description.", table=table_name))
    if not str(table.get("grain") or "").strip():
        issues.append(_issue("Documentation", "table_grain", f"{table_name} needs a grain statement describing what one row represents.", table=table_name))
    expected_key = str(table.get("expected_primary_key") or "").strip()
    if not expected_key:
        issues.append(_issue("Documentation", "table_primary_key", f"{table_name} needs an expected primary-key decision.", table=table_name))
    elif expected_key.casefold() not in {"no single-column primary key", "none", "not applicable", "review required"}:
        matching = next((row for row in rows if str(row.get("column") or "").casefold() == expected_key.casefold()), None)
        if matching is None:
            issues.append(_issue("Blocking", "missing_primary_key_column", f"{table_name} names {expected_key} as its primary key, but that column is not present in the table.", table=table_name))
    if expected_key.casefold() == "review required":
        issues.append(_issue("Documentation", "unconfirmed_primary_key", f"{table_name} still needs a final primary-key decision.", table=table_name))
    unreviewed = [row for row in rows if not _is_reviewed(row.get("reviewed"))]
    if include_review_status and unreviewed:
        issues.append(_issue("Review", "table_fields_unreviewed", f"{table_name} still has {len(unreviewed)} unreviewed field(s).", table=table_name))
    if include_review_status and not _is_reviewed(table.get("reviewed")):
        issues.append(_issue("Review", "table_not_reviewed", f"{table_name} has not been marked reviewed.", table=table_name))
    return issues


def dictionary_validation(
    rows: Iterable[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
    *,
    include_review_status: bool = True,
) -> list[dict[str, str]]:
    rows_list = list(rows)
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows_list:
        table = str(row.get("table") or "").strip()
        column = str(row.get("column") or "").strip()
        key = (table.casefold(), column.casefold())
        if key in seen:
            issues.append(_issue("Blocking", "duplicate_dictionary_row", f"{table}.{column} appears more than once in the dictionary.", table=table, column=column))
        seen.add(key)
        issues.extend(dictionary_field_issues(row, include_review_status=include_review_status))

    if table_metadata:
        for table_name, metadata in table_metadata.items():
            table_rows = [row for row in rows_list if str(row.get("table") or "") == table_name]
            issues.extend(dictionary_table_issues(metadata, table_rows, include_review_status=include_review_status))
    return issues


def dictionary_issues(
    rows: Iterable[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Backward-compatible completion messages for the portfolio workspace."""
    return [
        issue["message"]
        for issue in dictionary_validation(rows, table_metadata, include_review_status=True)
        if issue["severity"] != "Suggestion"
    ]


def _dictionary_editable_table_payload(table_metadata: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    fields = ("business_name", "description", "grain", "expected_primary_key", "notes", "reviewed")
    return {
        table_name: {field: str(table.get(field) or "") for field in fields}
        for table_name, table in table_metadata.items()
    }


def dictionary_fingerprint(
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
) -> str:
    row_fields = (
        "table", "column", "observed_type", "expected_type", "definition",
        "nullable", "key", "expected_unique", "valid_values", "relationship",
        "unit", "notes", "cleaning_expectation", "warning_resolution", "reviewed",
    )
    payload = {
        "rows": [{field: str(row.get(field) or "") for field in row_fields} for row in rows],
        "tables": _dictionary_editable_table_payload(table_metadata or {}),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def save_dictionary_progress(
    context: StudioContext,
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
) -> Path:
    documentation = context.project_dir / "documentation"
    documentation.mkdir(parents=True, exist_ok=True)
    csv_path = documentation / "data_dictionary.csv"
    fields = (
        "table", "column", "observed_type", "expected_type", "definition",
        "nullable", "key", "expected_unique", "valid_values", "relationship",
        "unit", "notes", "cleaning_expectation", "warning_resolution", "reviewed",
    )
    from io import StringIO
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    csv_text = buffer.getvalue()
    old_text = csv_path.read_text(encoding="utf-8", errors="replace") if csv_path.is_file() else None
    if old_text != csv_text:
        if csv_path.is_file():
            _backup_before_replace(context, csv_path, "data-dictionary")
        _atomic_write_text(csv_path, csv_text)

    tables = table_metadata or dictionary_table_metadata(context, rows)
    fingerprint = dictionary_fingerprint(rows, tables)
    state = load_state(context).get("data", {})
    state["dictionary_tables"] = _dictionary_editable_table_payload(tables)
    state["dictionary_saved_at"] = datetime.now().isoformat(timespec="seconds")
    state["dictionary_saved_hash"] = fingerprint
    state["dictionary_issue_count"] = len(dictionary_issues(rows, tables))
    save_state(context, state)
    return csv_path


def record_dictionary_validation(
    context: StudioContext,
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]],
    issues: list[dict[str, str]],
) -> None:
    state = load_state(context).get("data", {})
    state["dictionary_validated_at"] = datetime.now().isoformat(timespec="seconds")
    state["dictionary_validation_issue_count"] = len([issue for issue in issues if issue["severity"] != "Suggestion"])
    state["dictionary_validated_hash"] = dictionary_fingerprint(rows, table_metadata)
    save_state(context, state)


def generate_dictionary_markdown(
    context: StudioContext,
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
) -> Path:
    documentation = context.project_dir / "documentation"
    documentation.mkdir(parents=True, exist_ok=True)
    md_path = documentation / "data_dictionary.md"
    tables = table_metadata or dictionary_table_metadata(context, rows)
    escape = lambda value: str(value or "").replace("|", "\\|").replace("\n", "<br>")
    lines = [
        f"# {context.project_name} — Data Dictionary",
        "",
        f"Generated from the reviewed Data Dictionary Studio on {datetime.now().strftime('%Y-%m-%d %H:%M')}.",
        "",
        f"- Tables: {len(tables)}",
        f"- Fields: {len(rows)}",
        "",
    ]
    for table_name, table in tables.items():
        table_rows = [row for row in rows if str(row.get("table") or "") == table_name]
        lines.extend(
            [
                f"## {escape(table.get('business_name') or table_name)} (`{escape(table_name)}`)",
                "",
                f"**Description:** {escape(table.get('description') or 'Not documented')}",
                "",
                f"**Grain:** {escape(table.get('grain') or 'Not documented')}",
                "",
                f"**Expected primary key:** `{escape(table.get('expected_primary_key') or 'Not documented')}`",
                "",
            ]
        )
        if table.get("relationships"):
            lines.extend(["**Relationships:**", ""])
            lines.extend(f"- {escape(item)}" for item in str(table["relationships"]).splitlines() if item.strip())
            lines.append("")
        if table.get("notes"):
            lines.extend([f"**Table notes:** {escape(table.get('notes'))}", ""])
        lines.extend(
            [
                "| Column | Observed type | Expected type | Definition | Null rule | Key role | Uniqueness | Valid values / format | Relationship | Unit | Notes / exceptions | Cleaning expectation |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in table_rows:
            lines.append(
                f"| `{escape(row.get('column'))}` | {escape(row.get('observed_type'))} | "
                f"{escape(row.get('expected_type'))} | {escape(row.get('definition'))} | "
                f"{escape(row.get('nullable'))} | {escape(row.get('key'))} | "
                f"{escape(row.get('expected_unique'))} | {escape(row.get('valid_values'))} | "
                f"{escape(row.get('relationship'))} | {escape(row.get('unit'))} | "
                f"{escape(row.get('warning_resolution') or row.get('notes'))} | "
                f"{escape(row.get('cleaning_expectation'))} |"
            )
        lines.append("")
    markdown_text = "\n".join(lines).rstrip() + "\n"
    old_text = md_path.read_text(encoding="utf-8", errors="replace") if md_path.is_file() else None
    if old_text != markdown_text:
        if md_path.is_file():
            _backup_before_replace(context, md_path, "data-dictionary")
        _atomic_write_text(md_path, markdown_text)

    state = load_state(context).get("data", {})
    state["dictionary_generated_at"] = datetime.now().isoformat(timespec="seconds")
    state["dictionary_generated_hash"] = dictionary_fingerprint(rows, tables)
    save_state(context, state)
    return md_path


def save_dictionary(
    context: StudioContext,
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]] | None = None,
) -> tuple[Path, Path]:
    """Compatibility helper used by older callers: save progress and regenerate Markdown."""
    tables = table_metadata or dictionary_table_metadata(context, rows)
    csv_path = save_dictionary_progress(context, rows, tables)
    md_path = generate_dictionary_markdown(context, rows, tables)
    return csv_path, md_path


def dictionary_completion_issues(
    context: StudioContext,
    rows: list[dict[str, Any]],
    table_metadata: dict[str, dict[str, Any]],
) -> list[str]:
    issues = dictionary_issues(rows, table_metadata)
    current_hash = dictionary_fingerprint(rows, table_metadata)
    state = load_state(context).get("data", {})
    if state.get("dictionary_validated_hash") != current_hash:
        issues.append("Run Check Dictionary after the final edits so the saved version is validated.")
    elif int(state.get("dictionary_validation_issue_count") or 0) > 0:
        issues.append("Check Dictionary still reports unresolved blocking or documentation items.")
    if state.get("dictionary_generated_hash") != current_hash:
        issues.append("Generate the final data dictionary document after the last saved edit.")
    return issues

def _starter_setup_markdown(context: StudioContext, purpose: str) -> str:
    return (
        f"# {context.project_name} — {purpose}\n\n"
        "Use the Guide tab for the full task. Keep this notebook focused on your "
        "code, outputs, decisions, and validation notes.\n\n"
        + project_artifacts.upstream_context_markdown(
            context.project_dir,
            context.milestone_key,
        )
    )


def _project_setup_code(context: StudioContext) -> str:
    project_dir = context.project_dir.as_posix().replace("'", "\\'")
    return (
        "from pathlib import Path\n"
        f"PROJECT_DIR = Path(r'{project_dir}')\n"
        "RAW_DIR = PROJECT_DIR / 'data' / 'raw'\n"
        "PROCESSED_DIR = PROJECT_DIR / 'data' / 'processed'\n"
        "PROCESSED_DIR.mkdir(parents=True, exist_ok=True)\n"
        "PROJECT_DIR\n"
    )


def ensure_cleaning_notebook(context: StudioContext) -> Path:
    path = context.project_dir / "notebooks" / "clean_data.ipynb"
    cells = [
        notebook_workspace.new_markdown_cell(_starter_setup_markdown(context, "Clean and Validate Analytical Data")),
        notebook_workspace.new_code_cell(_project_setup_code(context)),
        notebook_workspace.new_markdown_cell("## 1. Profile the raw data\n\nRecord the issues you find before changing anything."),
        notebook_workspace.new_code_cell("# Write your profiling code or DuckDB SQL here.\n"),
        notebook_workspace.new_markdown_cell("## 2. Decide how each issue should be handled\n\nExplain why the chosen treatment is appropriate."),
        notebook_workspace.new_code_cell("# Write your cleaning transformations here.\n"),
        notebook_workspace.new_markdown_cell("## 3. Validate the cleaned results\n\nCompare row counts, keys, relationships, categories, ranges, and business rules."),
        notebook_workspace.new_code_cell("# Write before-and-after validation checks here.\n"),
        notebook_workspace.new_markdown_cell("## 4. Export cleaned datasets\n\nSave only reviewed outputs under `data/processed/`."),
        notebook_workspace.new_code_cell("# Export your reviewed cleaned tables here.\n"),
        notebook_workspace.new_markdown_cell("## Cleaning summary\n\nWhat changed, why, and what remains unresolved?\n"),
    ]
    return notebook_workspace.ensure_notebook(
        path,
        title=f"{context.project_name} — Clean and Validate Analytical Data",
        cells=cells,
        template="portfolio-cleaning",
    )


def ensure_eda_notebook(context: StudioContext) -> Path:
    path = context.project_dir / "notebooks" / "eda.ipynb"
    cells = [
        notebook_workspace.new_markdown_cell(_starter_setup_markdown(context, "Exploratory Analysis")),
        notebook_workspace.new_code_cell(_project_setup_code(context)),
        notebook_workspace.new_markdown_cell("## Coverage and distributions"),
        notebook_workspace.new_code_cell("# Explore coverage, distributions, and important categories here.\n"),
        notebook_workspace.new_markdown_cell("## Segments, time patterns, and relationships"),
        notebook_workspace.new_code_cell("# Explore patterns tied to the approved business questions.\n"),
        notebook_workspace.new_markdown_cell("## Anomalies and follow-up questions"),
        notebook_workspace.new_code_cell("# Investigate unusual records without assuming they are errors.\n"),
        notebook_workspace.new_markdown_cell("## Candidate findings\n\nSeparate observations, hypotheses, and validated findings.\n"),
    ]
    return notebook_workspace.ensure_notebook(
        path,
        title=f"{context.project_name} — Exploratory Analysis",
        cells=cells,
        template="portfolio-eda",
    )


def cleaning_rows(context: StudioContext) -> list[dict[str, Any]]:
    """Return one cleaning-plan row per configured analytical source table."""
    state = load_state(context).get("data", {})
    saved = state.get("cleaning_tables") if isinstance(state, dict) else None
    saved_lookup: dict[str, dict[str, Any]] = {}
    if isinstance(saved, list):
        for item in saved:
            if not isinstance(item, dict):
                continue
            key = str(item.get("table") or item.get("source_path") or "").casefold()
            if key:
                saved_lookup[key] = item

    processed = processed_inventory(context)
    try:
        plan = project_data_workspace.prepare_project_data_workspace(
            context.root,
            context.project_id,
            build=False,
        )
        configured = list(plan.sources)
    except Exception:
        configured = []

    source_rows: list[dict[str, str]] = []
    for source in configured:
        source_rows.append(
            {
                "table": str(source.view or source.name),
                "source_path": str(source.path),
            }
        )

    if not source_rows:
        # Fall back to physical files when the project has not registered sources yet.
        for raw in raw_inventory(context):
            if raw["suffix"] in SPREADSHEET_SUFFIXES:
                # A workbook may contain several logical tables. Keep it visible as
                # one source only until the learner registers its sheet-level tables.
                table_name = Path(raw["name"]).stem.removeprefix("raw_")
            else:
                table_name = Path(raw["name"]).stem.removeprefix("raw_")
            source_rows.append({"table": table_name, "source_path": raw["path"]})

    result = []
    seen: set[tuple[str, str]] = set()
    for source_row in source_rows:
        table = str(source_row["table"])
        source_path = str(source_row["source_path"])
        unique_key = (table.casefold(), source_path.casefold())
        if unique_key in seen:
            continue
        seen.add(unique_key)
        existing = saved_lookup.get(table.casefold()) or saved_lookup.get(source_path.casefold()) or {}
        stem = Path(source_path).stem.removeprefix("raw_")
        matched = next(
            (
                item
                for item in processed
                if table.casefold() in Path(item["name"]).stem.casefold()
                or stem.casefold() in Path(item["name"]).stem.casefold()
            ),
            None,
        )
        result.append(
            {
                "source_path": source_path,
                "table": str(existing.get("table") or table),
                "method": str(existing.get("method") or "SQL in Cleaning Notebook"),
                "working_artifact": str(existing.get("working_artifact") or "notebooks/clean_data.ipynb"),
                "cleaned_output": str(existing.get("cleaned_output") or (matched["path"] if matched else "")),
                "status": str(existing.get("status") or ("Output found" if matched else "Not started")),
                "notes": str(existing.get("notes") or ""),
                "google_sheet": existing.get("google_sheet") if isinstance(existing.get("google_sheet"), dict) else None,
            }
        )
    return result


def save_cleaning_rows(context: StudioContext, rows: list[dict[str, Any]]) -> Path:
    state = load_state(context).get("data", {})
    state["cleaning_tables"] = rows
    return save_state(context, state)


def create_spreadsheet_working_copy(context: StudioContext, source_relative: str) -> Path:
    source = (context.project_dir / source_relative).resolve()
    try:
        source.relative_to(context.project_dir.resolve())
    except ValueError as exc:
        raise ValueError("The selected source is outside the project folder.") from exc
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = context.project_dir / "data" / "staging"
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"{source.stem.removeprefix('raw_')}_working{source.suffix}"
    if not target.exists():
        shutil.copy2(source, target)
    return target


def register_cleaned_output(context: StudioContext, source_path: Path, table_name: str) -> Path:
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = context.project_dir / "data" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    safe_name = _slug(table_name).replace("_", "-") or source.stem
    target = destination / f"{safe_name}_cleaned{source.suffix.casefold()}"
    if target.exists():
        backup_dir = context.project_dir / "backups" / "cleaned-data"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(target, backup_dir / f"{target.stem}-{timestamp}{target.suffix}")
    shutil.copy2(source, target)
    return target


def compare_tabular_files(raw_path: Path, cleaned_path: Path) -> dict[str, Any]:
    raw_path = Path(raw_path)
    cleaned_path = Path(cleaned_path)
    result = {
        "raw_rows": None,
        "cleaned_rows": None,
        "row_difference": None,
        "raw_columns": [],
        "cleaned_columns": [],
        "missing_columns": [],
        "new_columns": [],
    }
    if raw_path.suffix.casefold() == ".csv" and cleaned_path.suffix.casefold() == ".csv":
        raw_rows, raw_columns = _csv_profile(raw_path)
        cleaned_rows, cleaned_columns = _csv_profile(cleaned_path)
        result.update(
            {
                "raw_rows": raw_rows,
                "cleaned_rows": cleaned_rows,
                "row_difference": None if raw_rows is None or cleaned_rows is None else cleaned_rows - raw_rows,
                "raw_columns": raw_columns,
                "cleaned_columns": cleaned_columns,
                "missing_columns": [item for item in raw_columns if item not in cleaned_columns],
                "new_columns": [item for item in cleaned_columns if item not in raw_columns],
            }
        )
    return result


def ensure_database_build_script(context: StudioContext) -> Path:
    path = context.project_dir / "sql" / "schema" / "build_analytical_database.sql"
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "-- Build the analytical database from the reviewed cleaned datasets.",
                "-- Keep this script reproducible: a clean database should be buildable from top to bottom.",
                "",
                "-- 1. Create the analytical schemas, tables, or views you need.",
                "",
                "-- 2. Load each cleaned dataset in dependency order.",
                "",
                "-- 3. Add any reviewed type conversions or analytical views.",
                "",
                "-- 4. Add row-count, key, relationship, and business-rule checks.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL on semicolons while respecting strings and comments."""
    text = str(sql_text or "")
    statements: list[str] = []
    buffer: list[str] = []
    index = 0
    quote = ""
    line_comment = False
    block_comment = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            buffer.append(char)
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            buffer.append(char)
            if char == "*" and next_char == "/":
                buffer.append(next_char)
                index += 2
                block_comment = False
            else:
                index += 1
            continue
        if quote:
            buffer.append(char)
            if char == quote:
                if next_char == quote:
                    buffer.append(next_char)
                    index += 2
                    continue
                quote = ""
            index += 1
            continue
        if char == "-" and next_char == "-":
            buffer.extend((char, next_char))
            index += 2
            line_comment = True
            continue
        if char == "/" and next_char == "*":
            buffer.extend((char, next_char))
            index += 2
            block_comment = True
            continue
        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if _sql_has_code(statement):
                statements.append(statement)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    statement = "".join(buffer).strip()
    if _sql_has_code(statement):
        statements.append(statement)
    return statements


def _sql_has_code(sql_text: str) -> bool:
    text = re.sub(r"/\*.*?\*/", " ", str(sql_text or ""), flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return bool(text.strip())


def database_build_status(context: StudioContext) -> dict[str, Any]:
    data = load_state(context).get("data", {})
    status = data.get("database_build") if isinstance(data, dict) else None
    return dict(status) if isinstance(status, dict) else {}


def run_database_build(context: StudioContext, sql_text: str) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("DuckDB is not installed in the Career Accelerator environment.") from exc

    statements = _split_sql_statements(sql_text)
    if not statements:
        raise ValueError("Write the database build SQL before running the build.")

    database = context.project_dir / "data" / "working" / "analytical.duckdb"
    database.parent.mkdir(parents=True, exist_ok=True)
    temporary = database.with_suffix(".duckdb.building")
    for candidate in (temporary, Path(str(temporary) + ".wal")):
        if candidate.exists():
            candidate.unlink()

    connection = duckdb.connect(str(temporary))
    messages = []
    try:
        try:
            escaped = str(context.project_dir).replace("'", "''")
            connection.execute(f"SET file_search_path='{escaped}'")
        except Exception:
            pass
        for index, statement in enumerate(statements, 1):
            cursor = connection.execute(statement)
            try:
                rows = cursor.fetchmany(20)
                columns = [str(item[0]) for item in (cursor.description or [])]
            except Exception:
                rows = []
                columns = []
            messages.append({"statement": index, "columns": columns, "preview": rows})
        tables = [str(row[0]) for row in connection.execute("SHOW TABLES").fetchall()]
        table_counts: dict[str, int | None] = {}
        for table in tables:
            try:
                table_counts[table] = int(
                    connection.execute(f"SELECT COUNT(*) FROM {_duckdb_quote(table)}").fetchone()[0]
                )
            except Exception:
                table_counts[table] = None
        connection.execute("CHECKPOINT")
    except Exception:
        connection.close()
        for candidate in (temporary, Path(str(temporary) + ".wal")):
            if candidate.exists():
                candidate.unlink()
        raise
    else:
        connection.close()

    if database.is_file():
        _backup_before_replace(context, database, "analytical-database")
        database.unlink()
    temporary.replace(database)
    temporary_wal = Path(str(temporary) + ".wal")
    if temporary_wal.exists():
        temporary_wal.unlink()

    status = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "database": database.relative_to(context.project_dir).as_posix(),
        "script_hash": hashlib.sha256(str(sql_text).encode("utf-8")).hexdigest(),
        "statements": len(statements),
        "tables": tables,
        "table_counts": table_counts,
    }
    data = load_state(context).get("data", {})
    data["database_build"] = status
    save_state(context, data)
    return {
        "database": database,
        "statements": len(statements),
        "tables": tables,
        "table_counts": table_counts,
        "messages": messages,
        "built_at": status["built_at"],
    }


def results_verification_rows(context: StudioContext) -> list[dict[str, Any]]:
    data = load_state(context).get("data", {})
    rows = data.get("results_verification") if isinstance(data, dict) else None
    return list(rows) if isinstance(rows, list) else []


def save_results_verification(context: StudioContext, rows: list[dict[str, Any]]) -> tuple[Path, Path]:
    data = load_state(context).get("data", {})
    data["results_verification"] = rows
    save_state(context, data)
    documentation = context.project_dir / "documentation"
    documentation.mkdir(parents=True, exist_ok=True)
    csv_path = documentation / "findings_validation.csv"
    fields = ("metric", "sql_value", "python_value", "power_bi_value", "tolerance", "status", "resolution")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    md_path = documentation / "findings_validation.md"
    lines = [f"# {context.project_name} — Findings Validation", "", "| Metric | SQL | Python | Power BI | Status | Resolution |", "|---|---:|---:|---:|---|---|"]
    for row in rows:
        esc = lambda value: str(value or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {esc(row.get('metric'))} | {esc(row.get('sql_value'))} | {esc(row.get('python_value'))} | {esc(row.get('power_bi_value'))} | {esc(row.get('status'))} | {esc(row.get('resolution'))} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def findings_rows(context: StudioContext) -> list[dict[str, Any]]:
    data = load_state(context).get("data", {})
    rows = data.get("findings") if isinstance(data, dict) else None
    return list(rows) if isinstance(rows, list) else []


def save_findings(context: StudioContext, rows: list[dict[str, Any]], summary: str = "") -> Path:
    data = load_state(context).get("data", {})
    data["findings"] = rows
    data["executive_summary_intro"] = summary
    save_state(context, data)
    path = context.project_dir / "documentation" / "executive_summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {context.project_name} — Executive Summary", "", str(summary or "_Add a short decision-focused introduction._"), ""]
    for index, row in enumerate(rows, 1):
        lines.extend(
            [
                f"## {index}. {str(row.get('finding') or 'Finding').strip()}",
                "",
                f"**Evidence:** {str(row.get('evidence') or '_Not linked._').strip()}",
                "",
                f"**Why it matters:** {str(row.get('impact') or '_Not explained._').strip()}",
                "",
                f"**Recommendation:** {str(row.get('recommendation') or '_Not written._').strip()}",
                "",
                f"**Owner / next action:** {str(row.get('owner') or '_Not assigned._').strip()}",
                "",
                f"**Limitations:** {str(row.get('limitations') or '_None recorded._').strip()}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def publisher_checks(context: StudioContext) -> list[dict[str, Any]]:
    project = context.project_dir
    screenshots = False
    for folder in (project / "images", project / "outputs" / "screenshots"):
        if folder.is_dir() and any(
            path.is_file() and path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
            for path in folder.rglob("*")
        ):
            screenshots = True
            break

    sql_files = []
    analysis_dir = project / "sql" / "analysis"
    if analysis_dir.is_dir():
        sql_files = [
            path
            for path in analysis_dir.glob("*.sql")
            if _sql_has_code(path.read_text(encoding="utf-8", errors="replace"))
        ]
    processed = processed_inventory(context)
    power_bi = find_power_bi_file(context)
    checks = [
        ("README is present", (project / "README.md").is_file()),
        (
            "Approved project brief is present",
            (project / "documentation" / "project_brief.md").is_file()
            or (project / "PROJECT_CHARTER.md").is_file(),
        ),
        (
            "Data-source review and manifest are present",
            (project / "documentation" / "data_source_review.md").is_file()
            and (project / "documentation" / "data_source_manifest.csv").is_file(),
        ),
        (
            "Relationship-validation notebook is present",
            (project / "notebooks" / "validate_relationships.ipynb").is_file(),
        ),
        (
            "Final data dictionary is present",
            (project / "documentation" / "data_dictionary.csv").is_file()
            or (project / "DATA_DICTIONARY.md").is_file(),
        ),
        ("Reviewed cleaned datasets are present", bool(processed)),
        (
            "Analytical database build script is present",
            (project / "sql" / "schema" / "build_analytical_database.sql").is_file(),
        ),
        ("Final SQL analysis files are present", bool(sql_files)),
        ("Exploratory-analysis notebook is present", (project / "notebooks" / "eda.ipynb").is_file()),
        (
            "Cross-tool findings validation is present",
            (project / "documentation" / "findings_validation.md").is_file(),
        ),
        ("Power BI project file is present", power_bi is not None),
        ("Executive summary is present", (project / "documentation" / "executive_summary.md").is_file()),
        ("At least one final screenshot is present", screenshots),
    ]
    readme_path = project / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8", errors="replace") if readme_path.is_file() else ""
    local_path_pattern = re.compile(r"(?:[A-Za-z]:\\|file:///|/Users/|/home/)")
    checks.append(("README has no obvious local-only paths", not bool(local_path_pattern.search(readme_text))))
    checks.append(
        (
            "README has no unfinished placeholder markers",
            not any(
                token in readme_text.casefold()
                for token in ("todo", "tbd", "replace me", "lorem ipsum")
            ),
        )
    )
    return [{"label": label, "passed": bool(passed)} for label, passed in checks]


def ensure_analysis_query(context: StudioContext) -> Path:
    directory = context.project_dir / "sql" / "analysis"
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("*.sql"))
    if existing:
        return existing[0]
    path = directory / "01_analysis.sql"
    path.write_text(
        "\n".join(
            [
                "-- Business question:",
                "-- Intended output grain:",
                "-- Validation check:",
                "",
                "-- Write the analysis query here. Keep the final query readable and reproducible.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def analysis_query_files(context: StudioContext) -> list[Path]:
    ensure_analysis_query(context)
    return sorted((context.project_dir / "sql" / "analysis").glob("*.sql"))


def save_analysis_query(context: StudioContext, filename: str, sql_text: str, interpretation: str) -> Path:
    safe = _slug(Path(str(filename or "analysis")).stem)
    path = context.project_dir / "sql" / "analysis" / f"{safe}.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8", errors="replace") != str(sql_text):
        _backup_before_replace(context, path, "sql-analysis")
    _atomic_write_text(path, str(sql_text).rstrip() + "\n")
    data = load_state(context).get("data", {})
    interpretations = data.get("sql_interpretations")
    if not isinstance(interpretations, dict):
        interpretations = {}
    interpretations[path.name] = str(interpretation or "").strip()
    data["sql_interpretations"] = interpretations
    save_state(context, data)
    return path


def analysis_interpretation(context: StudioContext, filename: str) -> str:
    data = load_state(context).get("data", {})
    values = data.get("sql_interpretations") if isinstance(data, dict) else None
    return str(values.get(str(filename), "")) if isinstance(values, dict) else ""


def run_analysis_query(context: StudioContext, sql_text: str, *, limit: int = 500) -> dict[str, Any]:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("DuckDB is not installed in the Career Accelerator environment.") from exc
    candidates = (
        context.project_dir / "data" / "working" / "analytical.duckdb",
        context.project_dir / "data" / "working" / "project.duckdb",
    )
    database = next((path for path in candidates if path.is_file()), None)
    if database is None:
        raise FileNotFoundError("Build or prepare the project DuckDB database first.")
    statements = _split_sql_statements(sql_text)
    if not statements:
        raise ValueError("Write a SQL query before running it.")
    connection = duckdb.connect(str(database), read_only=True)
    try:
        columns: list[str] = []
        rows: list[tuple] = []
        for statement in statements:
            cursor = connection.execute(statement)
            if cursor.description:
                columns = [str(item[0]) for item in cursor.description]
                rows = cursor.fetchmany(max(1, int(limit)))
        return {
            "database": database,
            "columns": columns,
            "rows": rows,
            "truncated": len(rows) >= max(1, int(limit)),
            "statements": len(statements),
        }
    finally:
        connection.close()


def sql_analysis_issues(context: StudioContext) -> list[str]:
    issues: list[str] = []
    files = analysis_query_files(context)
    executable = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if _sql_has_code(text):
            executable.append(path)
    if not executable:
        issues.append("Write at least one analysis query.")
    data = load_state(context).get("data", {})
    interpretations = data.get("sql_interpretations") if isinstance(data, dict) else None
    if not isinstance(interpretations, dict) or not any(str(value).strip() for value in interpretations.values()):
        issues.append("Save a short interpretation for at least one final query.")
    return issues


def review_checklist_values(
    context: StudioContext,
    checklist_key: str,
    items: Iterable[str],
) -> dict[str, Any]:
    data = load_state(context).get("data", {})
    stored = data.get(checklist_key) if isinstance(data, dict) else None
    checked = stored.get("checked") if isinstance(stored, dict) else {}
    notes = stored.get("notes") if isinstance(stored, dict) else ""
    screenshots = stored.get("screenshots") if isinstance(stored, dict) else []
    return {
        "checked": {
            str(item): bool(checked.get(str(item), False)) if isinstance(checked, dict) else False
            for item in items
        },
        "notes": str(notes or ""),
        "screenshots": list(screenshots) if isinstance(screenshots, list) else [],
    }


def save_review_checklist(
    context: StudioContext,
    checklist_key: str,
    checked: dict[str, bool],
    notes: str,
    screenshots: Iterable[str],
) -> Path:
    data = load_state(context).get("data", {})
    data[checklist_key] = {
        "checked": {str(key): bool(value) for key, value in checked.items()},
        "notes": str(notes or "").strip(),
        "screenshots": [str(value) for value in screenshots if str(value).strip()],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return save_state(context, data)


def find_power_bi_file(context: StudioContext) -> Path | None:
    folder = context.project_dir / "power-bi"
    if not folder.is_dir():
        return None
    files = [path for path in folder.rglob("*") if path.is_file() and path.suffix.casefold() in POWER_BI_SUFFIXES]
    return sorted(files)[0] if files else None


def register_review_screenshot(context: StudioContext, source: Path, category: str) -> Path:
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Choose a PNG, JPEG, or WebP screenshot.")
    destination = context.project_dir / "outputs" / "screenshots" / _slug(category)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / source.name
    counter = 2
    while target.exists() and _file_hash(target) != _file_hash(source):
        target = destination / f"{source.stem}-{counter}{source.suffix.casefold()}"
        counter += 1
    if not target.exists():
        shutil.copy2(source, target)
    return target


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.is_file() else ""


def generate_case_study_draft(context: StudioContext) -> Path:
    """Assemble a reviewable draft without overwriting the public README."""
    project = context.project_dir
    brief = _read_optional(project / "documentation" / "project_brief.md") or _read_optional(project / "PROJECT_CHARTER.md")
    source = _read_optional(project / "documentation" / "data_source_review.md")
    summary = _read_optional(project / "documentation" / "executive_summary.md")
    validation = _read_optional(project / "documentation" / "findings_validation.md")
    lines = [
        f"# {context.project_name}",
        "",
        "> Draft assembled by Career Accelerator from approved project artifacts. Review and edit every section before publishing.",
        "",
        "## Project overview",
        "",
        brief or "_Add the approved business problem, audience, decision, and scope._",
        "",
        "## Data source",
        "",
        source or "_Describe the data source, coverage, and limitations._",
        "",
        "## Approach",
        "",
        "- Relationship validation: `notebooks/validate_relationships.ipynb`",
        "- Data dictionary: `documentation/data_dictionary.csv`",
        "- Cleaning work: `notebooks/clean_data.ipynb` and `data/processed/`",
        "- SQL analysis: `sql/analysis/`",
        "- Exploratory analysis: `notebooks/eda.ipynb`",
        "- Power BI report: `power-bi/`",
        "",
        "## Findings and recommendations",
        "",
        summary or "_Add the approved findings and recommendations._",
        "",
        "## Validation",
        "",
        validation or "_Explain how the headline results were checked across tools._",
        "",
        "## Reproduce the project",
        "",
        "1. Review the source and environment notes in this repository.",
        "2. Run the cleaning work and save the reviewed outputs.",
        "3. Run the analytical database build script.",
        "4. Run the final SQL and notebook analysis.",
        "5. Open the Power BI file and compare the headline values with the saved validation matrix.",
        "",
        "## Limitations",
        "",
        "_List the limits that could change how the findings should be used._",
        "",
    ]
    path = project / "documentation" / "case_study_draft.md"
    text = "\n".join(lines).rstrip() + "\n"
    if path.is_file() and path.read_text(encoding="utf-8", errors="replace") != text:
        _backup_before_replace(context, path, "case-study-draft")
    _atomic_write_text(path, text)
    return path


def apply_case_study_draft(context: StudioContext) -> Path:
    draft = context.project_dir / "documentation" / "case_study_draft.md"
    if not draft.is_file():
        raise FileNotFoundError("Generate the case-study draft first.")
    readme = context.project_dir / "README.md"
    if readme.is_file():
        _backup_before_replace(context, readme, "case-study-publication")
    _atomic_write_text(readme, draft.read_text(encoding="utf-8"))
    return readme


def open_path(context: StudioContext, path: Path) -> str:
    return task_workspace.open_artifact(path, root=context.root)
