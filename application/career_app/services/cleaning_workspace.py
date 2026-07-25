"""Guided, table-by-table data-cleaning workspace helpers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from career_app.services import notebook_workspace, project_artifacts


DICTIONARY_COLUMNS = (
    "table",
    "column",
    "observed_type",
    "expected_type",
    "definition",
    "nullable",
    "key",
    "expected_unique",
    "valid_values",
    "relationship",
    "unit",
    "notes",
    "cleaning_expectation",
    "warning_resolution",
    "reviewed",
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_") or "table"


def _display_name(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _escape_markdown(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def dictionary_path(project_dir: Path) -> Path:
    return Path(project_dir) / "documentation" / "data_dictionary.csv"


def load_dictionary(project_dir: Path) -> list[dict[str, str]]:
    path = dictionary_path(project_dir)
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = []
        for source in csv.DictReader(handle):
            row = {key: str(source.get(key) or "").strip() for key in DICTIONARY_COLUMNS}
            # Older dictionaries used observed null text and omitted these columns.
            if not row["expected_unique"]:
                row["expected_unique"] = "Required" if "primary key" in row["key"].casefold() else "Not required"
            rows.append(row)
        return rows


def _load_table_setup(project_dir: Path) -> dict[str, dict[str, Any]]:
    path = Path(project_dir) / "workspaces" / "studios" / "data_dictionary_review.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    stored = (payload.get("data") or {}).get("dictionary_tables")
    if isinstance(stored, dict):
        return {
            str(key).casefold(): dict(value)
            for key, value in stored.items()
            if isinstance(value, dict)
        }
    if isinstance(stored, list):
        result = {}
        for value in stored:
            if not isinstance(value, dict):
                continue
            key = str(value.get("table") or value.get("name") or "").casefold()
            if key:
                result[key] = dict(value)
        return result
    return {}


def _table_fields(dictionary_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for row in dictionary_rows:
        table = row["table"].strip()
        if table:
            result.setdefault(table.casefold(), []).append(row)
    return result


def _primary_key(fields: list[dict[str, str]]) -> str:
    keys = [row["column"] for row in fields if "primary key" in row["key"].casefold()]
    return ", ".join(keys)


def _relationships(fields: list[dict[str, str]]) -> list[str]:
    result = []
    for row in fields:
        relationship = row["relationship"].strip()
        if relationship:
            result.append(f"{row['column']} → {relationship}")
    return result


def _known_issues(fields: list[dict[str, str]]) -> list[str]:
    result: list[str] = []
    for row in fields:
        details = [
            row["notes"],
            row["warning_resolution"],
        ]
        for detail in details:
            detail = detail.strip()
            if detail:
                text = f"{row['column']}: {detail}"
                if text not in result:
                    result.append(text)
    return result


def _cleaning_rules(fields: list[dict[str, str]]) -> list[str]:
    result: list[str] = []
    for row in fields:
        expectation = row["cleaning_expectation"].strip()
        if expectation:
            result.append(f"{row['column']}: {expectation}")
    return result


def _source_records(context) -> list[dict[str, Any]]:
    # Import lazily to avoid a service-module cycle during application startup.
    from career_app.services import portfolio_studios

    return portfolio_studios.cleaning_rows(context)


def table_records(context) -> list[dict[str, Any]]:
    dictionary_rows = load_dictionary(context.project_dir)
    field_lookup = _table_fields(dictionary_rows)
    setup_lookup = _load_table_setup(context.project_dir)
    rows = _source_records(context)
    result: list[dict[str, Any]] = []
    for source in rows:
        table = str(source.get("table") or Path(str(source.get("source_path") or "table")).stem)
        fields = field_lookup.get(table.casefold(), [])
        setup = setup_lookup.get(table.casefold(), {})
        primary_key = str(
            setup.get("primary_key")
            or setup.get("expected_primary_key")
            or setup.get("pk")
            or _primary_key(fields)
        ).strip()
        purpose = str(
            setup.get("purpose")
            or setup.get("description")
            or setup.get("table_purpose")
            or setup.get("business_purpose")
            or f"Source table used by the {context.project_name} analysis."
        ).strip()
        grain = str(
            setup.get("grain")
            or setup.get("one_row_represents")
            or setup.get("row_grain")
            or f"One {table.rstrip('s').replace('_', ' ')} record."
        ).strip()
        business_name = str(
            setup.get("business_name")
            or setup.get("display_name")
            or _display_name(table)
        ).strip()
        result.append(
            {
                **dict(source),
                "table": table,
                "business_name": business_name,
                "purpose": purpose,
                "grain": grain,
                "primary_key": primary_key,
                "relationships": _relationships(fields),
                "known_issues": _known_issues(fields),
                "cleaning_rules": _cleaning_rules(fields),
                "fields": fields,
                "notebook_path": f"notebooks/cleaning/{_slug(table)}_cleaning.ipynb",
                "processed_path": f"data/processed/csv/{_slug(table)}.csv",
            }
        )
    return result


def table_record(context, table_name: str) -> dict[str, Any]:
    key = str(table_name or "").casefold()
    for row in table_records(context):
        if row["table"].casefold() == key:
            return row
    raise KeyError(f"Unknown cleaning table: {table_name}")


def _dictionary_markdown(record: dict[str, Any]) -> str:
    lines = [
        "## What we already know",
        "",
        f"- **Business name:** {record['business_name']}",
        f"- **Purpose:** {record['purpose']}",
        f"- **One row represents:** {record['grain']}",
        f"- **Expected primary key:** `{record['primary_key'] or 'Not established'}`",
        "",
        "### Relationships",
    ]
    if record["relationships"]:
        lines.extend(f"- {item}" for item in record["relationships"])
    else:
        lines.append("- No parent relationship is documented for this table.")
    lines.extend(
        [
            "",
            "### Field rules from the approved data dictionary",
            "",
            "| Field | Definition | Expected type | Null rule | Key role | Uniqueness | Allowed values / format | Cleaning expectation |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for field in record["fields"]:
        lines.append(
            "| `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
                _escape_markdown(field["column"]),
                _escape_markdown(field["definition"]),
                _escape_markdown(field["expected_type"] or field["observed_type"]),
                _escape_markdown(field["nullable"]),
                _escape_markdown(field["key"] or "Not a key"),
                _escape_markdown(field["expected_unique"]),
                _escape_markdown(field["valid_values"]),
                _escape_markdown(field["cleaning_expectation"]),
            )
        )
    lines.extend(["", "### Known issues and approved decisions"])
    if record["known_issues"]:
        lines.extend(f"- {item}" for item in record["known_issues"])
    else:
        lines.append("- No specific warning is documented; still run the standard profiling checks.")
    return "\n".join(lines).rstrip() + "\n"


def cleaning_brief_markdown(context, record: dict[str, Any]) -> str:
    upstream = project_artifacts.upstream_context_markdown(
        context.project_dir,
        "clean_analytical_data",
    )
    lines = [
        f"# {context.project_name} — {record['business_name']} Cleaning Brief",
        "",
        "This brief was generated from the completed project milestones. Preserve the raw source and document any decision that differs from the approved dictionary.",
        "",
        upstream.rstrip(),
        "",
        _dictionary_markdown(record).rstrip(),
        "",
        "## Required result",
        "",
        f"- Reviewed processed dataset: `{record['processed_path']}`",
        f"- Table cleaning summary: `documentation/cleaning/{_slug(record['table'])}_cleaning_summary.md`",
        "- Validation must cover row counts, required columns, primary-key uniqueness, null rules, categories, ranges, dates, and relationships where applicable.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _setup_code(context, record: dict[str, Any]) -> str:
    project = context.project_dir.as_posix().replace("'", "\\'")
    source = str(record["source_path"]).replace("'", "\\'")
    processed = str(record["processed_path"]).replace("'", "\\'")
    table = str(record["table"]).replace("'", "\\'")
    return f'''from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(r'{project}')
TABLE_NAME = '{table}'
RAW_PATH = PROJECT_DIR / r'{source}'
PROCESSED_PATH = PROJECT_DIR / r'{processed}'
PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)

if RAW_PATH.suffix.lower() == '.csv':
    raw_df = pd.read_csv(RAW_PATH)
elif RAW_PATH.suffix.lower() == '.parquet':
    raw_df = pd.read_parquet(RAW_PATH)
else:
    raise ValueError(f'Add the appropriate pandas reader for {{RAW_PATH.suffix}}')

clean_df = raw_df.copy()
print(f'{{TABLE_NAME}}: {{len(raw_df):,}} raw rows, {{len(raw_df.columns)}} columns')
raw_df.head()
'''


def _profile_prompt(record: dict[str, Any]) -> str:
    checks = [
        "Confirm the source row count and column names.",
        "Measure missing values by field.",
        "Check exact duplicate rows.",
    ]
    if record["primary_key"]:
        checks.append(f"Test uniqueness and nulls for `{record['primary_key']}`.")
    checks.extend(
        [
            "Review observed categories and parsing problems.",
            "Compare findings with the dictionary rules above before changing data.",
        ]
    )
    return "## 1. Profile the raw table\n\n" + "\n".join(f"- {item}" for item in checks)


def _validation_prompt(record: dict[str, Any]) -> str:
    checks = [
        "Required columns are still present.",
        "Expected logical types can be produced consistently.",
        "Required fields do not contain unresolved nulls.",
        "Allowed values and formats match the dictionary.",
        "Invalid negative, out-of-range, or impossible values are resolved or documented.",
    ]
    if record["primary_key"]:
        checks.append(f"`{record['primary_key']}` is non-null and unique.")
    if record["relationships"]:
        checks.append("Foreign-key and relationship exceptions are measured and documented.")
    return "## 3. Validate the processed result\n\n" + "\n".join(f"- {item}" for item in checks)


def _notebook_cells(context, record: dict[str, Any]) -> list[dict[str, Any]]:
    context_cell = notebook_workspace.new_markdown_cell(
        _dictionary_markdown(record)
    )
    context_cell.setdefault("metadata", {})["dcaRole"] = "dictionary_context"
    return [
        notebook_workspace.new_markdown_cell(
            f"# {context.project_name} — {record['business_name']} Cleaning\n\n"
            "Work through this table from top to bottom. The context and rules below are inherited from earlier milestones."
        ),
        context_cell,
        notebook_workspace.new_code_cell(_setup_code(context, record)),
        notebook_workspace.new_markdown_cell(_profile_prompt(record)),
        notebook_workspace.new_code_cell(
            "# Write the profiling checks for this table here.\n"
            "# Keep the outputs that justify your cleaning decisions.\n"
        ),
        notebook_workspace.new_markdown_cell(
            "## 2. Apply the approved cleaning plan\n\n"
            "Transform `clean_df` without modifying `raw_df`. Follow the field-level expectations above. "
            "Document any treatment that differs from the approved dictionary."
        ),
        notebook_workspace.new_code_cell(
            "# Write this table's cleaning transformations here.\n"
            "# Example structure only: clean_df = clean_df.copy()\n"
        ),
        notebook_workspace.new_markdown_cell(_validation_prompt(record)),
        notebook_workspace.new_code_cell(
            "# Write the before-and-after validation checks here.\n"
            "# The checks should fail visibly when an unresolved issue remains.\n"
        ),
        notebook_workspace.new_markdown_cell(
            "## 4. Export the reviewed table\n\n"
            f"After validation, save the reviewed result to `{record['processed_path']}`. "
            "The Data Cleaning Studio will discover and validate the file."
        ),
        notebook_workspace.new_code_cell(
            "# Run only after the table has passed your validation checks.\n"
            "clean_df.to_csv(PROCESSED_PATH, index=False)\n"
            "print(f'Saved {len(clean_df):,} rows to {PROCESSED_PATH}')\n"
        ),
        notebook_workspace.new_markdown_cell(
            "## Cleaning summary\n\n"
            "<!-- Describe what changed, why each important decision was appropriate, how many records were affected, and any remaining exception that a later milestone must know about. -->\n"
        ),
    ]


def _dictionary_fingerprint(record: dict[str, Any]) -> str:
    relevant = {
        "business_name": record.get("business_name"),
        "purpose": record.get("purpose"),
        "grain": record.get("grain"),
        "primary_key": record.get("primary_key"),
        "relationships": record.get("relationships"),
        "fields": record.get("fields"),
    }
    encoded = json.dumps(relevant, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def ensure_table_notebooks(context) -> list[dict[str, Any]]:
    result = []
    for record in table_records(context):
        path = context.project_dir / record["notebook_path"]
        fingerprint = _dictionary_fingerprint(record)
        created = not path.is_file()
        notebook_workspace.ensure_notebook(
            path,
            title=f"{context.project_name} — {record['business_name']} Cleaning",
            cells=_notebook_cells(context, record),
            template=f"portfolio-cleaning-table:{_slug(record['table'])}",
        )
        payload = notebook_workspace.load_notebook(path)
        metadata = payload.setdefault("metadata", {})
        previous = str(metadata.get("dcaDictionaryFingerprint") or "")
        if created or previous != fingerprint:
            context_text = _dictionary_markdown(record)
            context_cell = next(
                (
                    cell
                    for cell in payload.get("cells", [])
                    if (cell.get("metadata") or {}).get("dcaRole")
                    == "dictionary_context"
                ),
                None,
            )
            if context_cell is None:
                context_cell = notebook_workspace.new_markdown_cell(context_text)
                context_cell.setdefault("metadata", {})["dcaRole"] = "dictionary_context"
                payload.setdefault("cells", []).insert(1, context_cell)
            else:
                notebook_workspace.set_source_text(context_cell, context_text)
            metadata["dcaDictionaryFingerprint"] = fingerprint
            metadata["dcaDictionaryRefreshedAt"] = datetime.now().isoformat(timespec="seconds")
            notebook_workspace.save_notebook(path, payload)
        result.append({**record, "notebook": path})
    return result



def inspect_cleaning_notebook(
    context,
    source: Path,
) -> dict[str, Any]:
    """Validate an external notebook and identify the table it appears to use."""
    source = Path(source)
    if source.suffix.casefold() != ".ipynb":
        raise ValueError("Choose a Jupyter notebook file ending in .ipynb.")
    payload = notebook_workspace.load_notebook(source)
    if int(payload.get("nbformat") or 0) < 4:
        raise ValueError(
            "The notebook uses an unsupported legacy format. Open and resave it "
            "as notebook format 4 before importing."
        )
    cells = list(payload.get("cells") or [])
    if not cells:
        raise ValueError("The notebook does not contain any cells.")
    valid_types = {"code", "markdown", "raw"}
    invalid_types = sorted(
        {
            str(cell.get("cell_type") or "")
            for cell in cells
            if str(cell.get("cell_type") or "") not in valid_types
        }
    )
    if invalid_types:
        raise ValueError(
            "The notebook contains unsupported cell type(s): "
            + ", ".join(invalid_types)
        )

    searchable_parts = [source.stem.replace("_", " ")]
    for cell in cells:
        searchable_parts.append(notebook_workspace._source_text(cell))
    searchable = "\n".join(searchable_parts).casefold()

    detected: list[str] = []
    for record in table_records(context):
        table = str(record["table"])
        business = str(record["business_name"])
        candidates = {
            table.casefold(),
            _slug(table).replace("_", " "),
            business.casefold(),
            _slug(business).replace("_", " "),
        }
        if any(
            candidate and re.search(
                rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])",
                searchable,
            )
            for candidate in candidates
        ):
            detected.append(table)

    return {
        "source": source,
        "payload": payload,
        "cell_count": len(cells),
        "code_cell_count": sum(
            1 for cell in cells if cell.get("cell_type") == "code"
        ),
        "detected_tables": detected,
    }


def import_cleaning_notebook(
    context,
    table_name: str,
    source: Path,
) -> dict[str, Any]:
    """Import an external notebook into the selected managed table slot."""
    record = table_record(context, table_name)
    inspection = inspect_cleaning_notebook(context, source)
    payload = inspection["payload"]
    source = Path(source).resolve()
    target = (context.project_dir / record["notebook_path"]).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if target.is_file():
        backup_dir = context.project_dir / "backups" / "cleaning-notebooks"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_dir / f"{target.stem}-{stamp}.ipynb"
        shutil.copy2(target, backup_path)

    metadata = payload.setdefault("metadata", {})
    metadata["dcaManaged"] = True
    metadata["dcaTemplate"] = (
        f"portfolio-cleaning-table:{_slug(record['table'])}"
    )
    metadata["dcaCleaningTable"] = record["table"]
    metadata["dcaImportedAt"] = datetime.now().isoformat(timespec="seconds")
    metadata["dcaImportedFrom"] = str(source)
    metadata["dcaDictionaryFingerprint"] = _dictionary_fingerprint(record)
    notebook_workspace.save_notebook(target, payload)

    relative_backup = ""
    if backup_path is not None:
        try:
            relative_backup = backup_path.relative_to(
                context.project_dir
            ).as_posix()
        except ValueError:
            relative_backup = str(backup_path)

    update_table_state(
        context,
        record["table"],
        status="Imported notebook ready for review",
        reviewed=False,
        notebook_path=record["notebook_path"],
        notebook_imported_at=metadata["dcaImportedAt"],
        notebook_imported_from=str(source),
        notebook_backup=relative_backup,
    )
    project_artifacts.refresh_registry(context.project_dir)
    return {
        "table": record["table"],
        "target": target,
        "backup": backup_path,
        "detected_tables": inspection["detected_tables"],
        "cell_count": inspection["cell_count"],
        "code_cell_count": inspection["code_cell_count"],
    }


def _state_path(context) -> Path:
    return context.project_dir / "workspaces" / "studios" / "clean_analytical_data.json"


def load_state(context) -> dict[str, Any]:
    path = _state_path(context)
    if not path.is_file():
        return {"version": 2, "tables": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"version": 2, "tables": {}}
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("version", 2)
    payload.setdefault("tables", {})
    if not isinstance(payload["tables"], dict):
        payload["tables"] = {}
    return payload


def save_state(context, payload: dict[str, Any]) -> Path:
    path = _state_path(context)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["version"] = 2
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    project_artifacts.refresh_registry(context.project_dir)
    return path


def table_state(context, table_name: str) -> dict[str, Any]:
    payload = load_state(context)
    return dict(payload["tables"].get(_slug(table_name), {}))


def update_table_state(context, table_name: str, **updates: Any) -> Path:
    payload = load_state(context)
    key = _slug(table_name)
    current = dict(payload["tables"].get(key, {}))
    current.update(updates)
    current["updated_at"] = datetime.now().isoformat(timespec="seconds")
    payload["tables"][key] = current
    return save_state(context, payload)


def expected_columns(record: dict[str, Any]) -> list[str]:
    return [row["column"] for row in record["fields"] if row["column"]]


def _null_not_allowed(rule: str) -> bool:
    value = str(rule or "").casefold()
    return "no null" in value or value == "required"


def _unique_required(rule: str, key_role: str) -> bool:
    value = str(rule or "").casefold()
    return value == "required" or "primary key" in str(key_role or "").casefold()


_ENUM_PROSE_MARKERS = (
    "allowed only",
    "first and last",
    "format",
    "numeric",
    "amount",
    "without",
    "uppercase",
    "digits",
    "or null",
    "yyyy",
    "date",
    "hours",
    "when",
    "pattern",
    "example",
)


def _strict_allowed_values(field: dict[str, str]) -> list[str]:
    """Return only values that are clearly an exhaustive controlled set.

    Data Dictionary cells often contain formats, examples, ranges, or prose.
    Those must never be treated as an enumeration merely because they contain
    semicolons.
    """

    text = str(field.get("valid_values") or "").strip()
    if not text:
        return []
    lowered = text.casefold()
    if any(marker in lowered for marker in _ENUM_PROSE_MARKERS):
        return []

    raw_items = [
        item.strip().rstrip(".")
        for item in re.split(r"[;|]", text)
        if item.strip()
    ]
    if len(raw_items) < 2 or len(raw_items) > 50:
        return []

    values: list[str] = []
    for item in raw_items:
        candidate = item
        if "=" in candidate:
            left, _right = candidate.split("=", 1)
            left = left.strip()
            if not left or len(left) > 24 or len(left.split()) > 2:
                return []
            candidate = left
        if not candidate or len(candidate) > 64 or len(candidate.split()) > 4:
            return []
        if any(char in candidate for char in (":", "@", "#")):
            return []
        values.append(candidate)

    # Preserve dictionary order while removing accidental duplicates.
    return list(dict.fromkeys(values))


def _decimal_value(value: str) -> Decimal | None:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _format_rule_issues(field: dict[str, str], values: list[str]) -> list[str]:
    """Validate documented formats and ranges without inventing enums."""

    column = str(field.get("column") or "Field")
    rule_text = " ".join(
        str(field.get(key) or "")
        for key in (
            "valid_values",
            "expected_type",
            "cleaning_expectation",
        )
    ).strip()
    lowered = rule_text.casefold()
    nonempty = [value for value in values if value]
    issues: list[str] = []

    if "yyyy-mm-dd" in lowered:
        invalid = []
        for value in nonempty:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                invalid.append(value)
        if invalid:
            sample = ", ".join(sorted(set(invalid))[:5])
            issues.append(
                f"{column}: {len(invalid)} value(s) do not use the documented YYYY-MM-DD date format. Sample: {sample}"
            )

    numeric_rule = "numeric" in lowered or any(
        token in str(field.get("expected_type") or "").casefold()
        for token in ("integer", "decimal", "double", "float", "number")
    )
    if numeric_rule:
        parsed = [(value, _decimal_value(value)) for value in nonempty]
        invalid = [value for value, parsed_value in parsed if parsed_value is None]
        if invalid:
            sample = ", ".join(sorted(set(invalid))[:5])
            issues.append(
                f"{column}: {len(invalid)} value(s) are not numeric. Sample: {sample}"
            )
        valid_numbers = [parsed_value for _value, parsed_value in parsed if parsed_value is not None]
        if "non-negative" in lowered:
            negatives = [value for value in valid_numbers if value < 0]
            if negatives:
                issues.append(f"{column}: {len(negatives)} value(s) are below the documented minimum of 0.")
        elif "positive" in lowered:
            nonpositive = [value for value in valid_numbers if value <= 0]
            if nonpositive:
                issues.append(f"{column}: {len(nonpositive)} value(s) must be greater than 0.")

    # Convert documented hash placeholders such as ART-### into a real format check.
    pattern_match = re.search(r"\b([A-Z][A-Z0-9_]*)-(#+)(?!#)", rule_text)
    if pattern_match:
        prefix = re.escape(pattern_match.group(1))
        digit_count = len(pattern_match.group(2))
        pattern = re.compile(rf"^{prefix}-\d{{{digit_count}}}$")
        invalid = [value for value in nonempty if not pattern.fullmatch(value)]
        if invalid:
            sample = ", ".join(sorted(set(invalid))[:5])
            issues.append(
                f"{column}: {len(invalid)} value(s) do not match the documented {pattern_match.group(0)} format. Sample: {sample}"
            )

    email_match = re.search(r"@([A-Za-z0-9.-]+)", rule_text)
    if email_match:
        domain = re.escape(email_match.group(1).rstrip("."))
        pattern = re.compile(rf"^[A-Za-z0-9._%+\-]+@{domain}$", re.IGNORECASE)
        invalid = [value for value in nonempty if not pattern.fullmatch(value)]
        if invalid:
            sample = ", ".join(sorted(set(invalid))[:5])
            issues.append(
                f"{column}: {len(invalid)} value(s) do not match the documented email domain and format. Sample: {sample}"
            )

    return issues


def _primary_key_columns(record: dict[str, Any]) -> list[str]:
    columns = [
        str(field.get("column") or "").strip()
        for field in record.get("fields") or []
        if "primary key" in str(field.get("key") or "").casefold()
    ]
    if columns:
        return [column for column in columns if column]
    return [
        column.strip()
        for column in str(record.get("primary_key") or "").split(",")
        if column.strip()
    ]


def _row_key(row: dict[str, Any], columns: list[str]) -> str:
    return " | ".join(str(row.get(column) or "").strip() for column in columns)


def validate_csv(path: Path, record: dict[str, Any], context=None) -> dict[str, Any]:
    path = Path(path)
    report: dict[str, Any] = {
        "path": str(path),
        "row_count": None,
        "raw_row_count": None,
        "row_difference": None,
        "columns": [],
        "missing_columns": [],
        "new_columns": [],
        "blocking": [],
        "warnings": [],
        "structural_changes": [],
        "information": [],
        "removed_primary_keys": [],
        "added_primary_keys": [],
        "metrics": {},
        "dictionary_fingerprint": _dictionary_fingerprint(record),
    }
    if path.suffix.casefold() != ".csv":
        report["blocking"].append("Only CSV files can be fully validated inside the application. Export the cleaned table as CSV before importing it.")
        return report
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = [str(value) for value in (reader.fieldnames or [])]
        rows = [dict(row) for row in reader]
    report["row_count"] = len(rows)
    report["columns"] = columns
    expected = expected_columns(record)
    report["missing_columns"] = [column for column in expected if column not in columns]
    report["new_columns"] = [column for column in columns if column not in expected]
    if report["missing_columns"]:
        report["blocking"].append("Missing required dictionary columns: " + ", ".join(report["missing_columns"]))
    if report["new_columns"]:
        report["warnings"].append("New columns not yet documented in the dictionary: " + ", ".join(report["new_columns"]))
    for field in record["fields"]:
        column = field["column"]
        if not column or column not in columns:
            continue
        values = [str(row.get(column) or "").strip() for row in rows]
        null_count = sum(1 for value in values if value == "")
        if _null_not_allowed(field["nullable"]) and null_count:
            report["blocking"].append(f"{column}: {null_count} null or blank value(s) violate the dictionary rule.")
        if _unique_required(field["expected_unique"], field["key"]):
            nonempty = [value for value in values if value]
            duplicates = len(nonempty) - len(set(nonempty))
            if duplicates:
                report["blocking"].append(f"{column}: {duplicates} duplicate value(s) violate the uniqueness rule.")
        allowed = _strict_allowed_values(field)
        if allowed:
            allowed_lookup = {value.casefold(): value for value in allowed}
            invalid = sorted(
                {value for value in values if value and value.casefold() not in allowed_lookup}
            )
            if invalid:
                sample = ", ".join(invalid[:8])
                suffix = "" if len(invalid) <= 8 else f" …and {len(invalid) - 8} more"
                report["warnings"].append(
                    f"{column}: {len(invalid)} value(s) are outside the controlled dictionary set. Sample: {sample}{suffix}"
                )
        report["warnings"].extend(_format_rule_issues(field, values))
        report["metrics"][column] = {
            "null_count": null_count,
            "distinct_count": len(set(values)),
            "rule_type": "controlled set" if allowed else "format/range or open-ended guidance",
        }
    if context is not None:
        raw_path = context.project_dir / str(record.get("source_path") or "")
        if raw_path.is_file() and raw_path.suffix.casefold() == ".csv":
            with raw_path.open("r", encoding="utf-8-sig", newline="") as handle:
                raw_reader = csv.DictReader(handle)
                raw_rows = [dict(row) for row in raw_reader]
            report["raw_row_count"] = len(raw_rows)
            report["row_difference"] = len(rows) - len(raw_rows)
            if report["row_difference"]:
                direction = "more" if report["row_difference"] > 0 else "fewer"
                report["structural_changes"].append(
                    f"Processed row count is {abs(report['row_difference'])} {direction} than the raw source ({len(raw_rows)} → {len(rows)})."
                )

            primary_keys = _primary_key_columns(record)
            if primary_keys and all(column in columns for column in primary_keys):
                raw_keys = {_row_key(row, primary_keys) for row in raw_rows}
                processed_keys = {_row_key(row, primary_keys) for row in rows}
                raw_keys.discard("")
                processed_keys.discard("")
                removed = sorted(raw_keys - processed_keys)
                added = sorted(processed_keys - raw_keys)
                report["removed_primary_keys"] = removed
                report["added_primary_keys"] = added
                if removed:
                    sample = ", ".join(removed[:12])
                    suffix = "" if len(removed) <= 12 else f" …and {len(removed) - 12} more"
                    report["structural_changes"].append(
                        f"Removed {len(removed)} primary-key record(s): {sample}{suffix}"
                    )
                if added:
                    sample = ", ".join(added[:12])
                    suffix = "" if len(added) <= 12 else f" …and {len(added) - 12} more"
                    report["structural_changes"].append(
                        f"Added {len(added)} new primary-key record(s): {sample}{suffix}"
                    )
                if report["row_difference"] < 0:
                    additional_reduction = max(
                        0,
                        abs(report["row_difference"]) - len(removed),
                    )
                    if additional_reduction:
                        report["structural_changes"].append(
                            f"Consolidated {additional_reduction} additional duplicate row(s) under retained primary keys."
                        )

        table_lookup = {item["table"].casefold(): item for item in table_records(context)}
        for field in record["fields"]:
            relationship = str(field.get("relationship") or "").strip()
            column = str(field.get("column") or "").strip()
            if not relationship or not column or column not in columns:
                continue
            parts = [part.strip() for part in relationship.replace("→", ".").split(".") if part.strip()]
            if len(parts) < 2:
                report["warnings"].append(f"{column}: could not parse parent relationship '{relationship}'.")
                continue
            parent_table = parts[-2].casefold()
            parent_column = parts[-1]
            parent_record = table_lookup.get(parent_table)
            if parent_record is None:
                report["warnings"].append(f"{column}: parent table '{parts[-2]}' is not registered in the cleaning workspace.")
                continue
            if parent_table == str(record.get("table") or "").casefold():
                parent_values = {str(parent.get(parent_column) or "").strip() for parent in rows}
            else:
                parent_path = discover_processed(context, parent_record)
                if parent_path is None:
                    parent_path = context.project_dir / str(parent_record.get("source_path") or "")
                if not parent_path.is_file() or parent_path.suffix.casefold() != ".csv":
                    report["warnings"].append(f"{column}: parent values could not be loaded from {parent_path}.")
                    continue
                with parent_path.open("r", encoding="utf-8-sig", newline="") as handle:
                    parent_rows = csv.DictReader(handle)
                    parent_values = {str(parent.get(parent_column) or "").strip() for parent in parent_rows}
            child_values = [str(row.get(column) or "").strip() for row in rows]
            orphans = sorted({value for value in child_values if value and value not in parent_values})
            if orphans:
                report["blocking"].append(
                    f"{column}: {sum(1 for value in child_values if value and value not in parent_values)} row(s) reference values not found in {parts[-2]}.{parent_column}."
                )

    controlled_fields = sum(
        1 for field in record.get("fields") or [] if _strict_allowed_values(field)
    )
    open_ended_fields = sum(
        1
        for field in record.get("fields") or []
        if str(field.get("valid_values") or "").strip() and not _strict_allowed_values(field)
    )
    if controlled_fields:
        report["information"].append(
            f"Checked {controlled_fields} controlled-value field(s) against exhaustive dictionary sets."
        )
    if open_ended_fields:
        report["information"].append(
            f"Treated {open_ended_fields} dictionary entries as formats, ranges, or examples—not fixed value lists."
        )
    if not rows:
        report["warnings"].append("The cleaned file contains no data rows.")
    return report


def processed_path(context, record: dict[str, Any]) -> Path:
    return context.project_dir / record["processed_path"]


def discover_processed(context, record: dict[str, Any]) -> Path | None:
    expected = processed_path(context, record)
    if expected.is_file():
        return expected
    legacy = context.project_dir / str(record.get("cleaned_output") or "")
    return legacy if legacy.is_file() else None


def import_cleaned_csv(context, table_name: str, source: Path) -> tuple[Path, dict[str, Any]]:
    record = table_record(context, table_name)
    source = Path(source)
    report = validate_csv(source, record, context)
    if report["blocking"]:
        raise ValueError("\n".join(report["blocking"]))
    target = processed_path(context, record)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        backup = context.project_dir / "backups" / "cleaned-data"
        backup.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(target, backup / f"{target.stem}-{stamp}{target.suffix}")
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    update_table_state(
        context,
        table_name,
        processed_path=record["processed_path"],
        imported_from=str(source),
        imported_at=datetime.now().isoformat(timespec="seconds"),
        validation=report,
        status="Ready for review" if (report["warnings"] or report["structural_changes"]) else "Validated",
        reviewed=False,
    )
    return target, report


def validate_processed(context, table_name: str) -> dict[str, Any]:
    record = table_record(context, table_name)
    path = discover_processed(context, record)
    if path is None:
        return {
            "row_count": None,
            "columns": [],
            "missing_columns": [],
            "new_columns": [],
            "blocking": ["No processed CSV has been generated or imported for this table."],
            "warnings": [],
            "structural_changes": [],
            "information": [],
            "metrics": {},
        }
    report = validate_csv(path, record, context)
    update_table_state(
        context,
        table_name,
        processed_path=str(path.relative_to(context.project_dir).as_posix()),
        validation=report,
        validated_at=datetime.now().isoformat(timespec="seconds"),
        status=("Validation issues" if report["blocking"] else "Ready for review" if (report["warnings"] or report["structural_changes"]) else "Validated"),
    )
    return report


def save_summary(context, table_name: str, summary: str) -> Path:
    record = table_record(context, table_name)
    path = context.project_dir / "documentation" / "cleaning" / f"{_slug(table_name)}_cleaning_summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    state = table_state(context, table_name)
    report = state.get("validation") if isinstance(state.get("validation"), dict) else {}
    lines = [
        f"# {record['business_name']} Cleaning Summary",
        "",
        f"- **Source:** `{record['source_path']}`",
        f"- **Processed output:** `{record['processed_path']}`",
        f"- **Expected primary key:** `{record['primary_key'] or 'Not established'}`",
        f"- **Last updated:** {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Decisions and remaining exceptions",
        "",
        str(summary or "").strip(),
        "",
        "## Latest validation",
        "",
        f"- Blocking issues: {len(report.get('blocking') or [])}",
        f"- Warnings: {len(report.get('warnings') or [])}",
        f"- Structural changes reviewed: {len(report.get('structural_changes') or [])}",
        f"- Processed rows: {report.get('row_count') if report.get('row_count') is not None else 'Not recorded'}",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    update_table_state(context, table_name, summary=str(summary or "").strip(), summary_path=path.relative_to(context.project_dir).as_posix())
    return path


def mark_reviewed(context, table_name: str, reviewed: bool) -> list[str]:
    issues = table_completion_issues(context, table_name)
    if reviewed and issues:
        return issues
    update_table_state(context, table_name, reviewed=bool(reviewed), status="Complete" if reviewed else "Ready for review")
    return []


def table_completion_issues(context, table_name: str) -> list[str]:
    record = table_record(context, table_name)
    state = table_state(context, table_name)
    path = discover_processed(context, record)
    issues: list[str] = []
    if path is None:
        issues.append("Generate or import the processed CSV.")
    report = state.get("validation") if isinstance(state.get("validation"), dict) else None
    if report is None:
        issues.append("Run processed-table validation.")
    elif str(report.get("dictionary_fingerprint") or "") != _dictionary_fingerprint(record):
        issues.append("The Data Dictionary changed after the last validation. Revalidate this table.")
    elif report.get("blocking"):
        issues.extend(str(item) for item in report["blocking"])
    if not str(state.get("summary") or "").strip():
        issues.append("Save the table cleaning summary and remaining exceptions.")
    return issues


def milestone_completion_issues(context) -> list[str]:
    issues: list[str] = []
    for record in table_records(context):
        state = table_state(context, record["table"])
        for issue in table_completion_issues(context, record["table"]):
            issues.append(f"{record['business_name']}: {issue}")
        if not bool(state.get("reviewed")):
            issues.append(f"{record['business_name']}: mark the table complete after review.")
    return issues


def export_raw_csv(context, table_name: str, destination: Path) -> Path:
    record = table_record(context, table_name)
    source = context.project_dir / record["source_path"]
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = Path(destination)
    if source.suffix.casefold() == ".csv":
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination
    raise ValueError("This source is not a CSV. Use Export Cleaning Package to copy the original source and its rules.")


def export_cleaning_package(context, table_name: str, destination_dir: Path) -> Path:
    record = table_record(context, table_name)
    destination = Path(destination_dir) / f"{_slug(table_name)}_cleaning_package"
    destination.mkdir(parents=True, exist_ok=True)
    source = context.project_dir / record["source_path"]
    if not source.is_file():
        raise FileNotFoundError(source)
    shutil.copy2(source, destination / source.name)
    (destination / "cleaning_brief.md").write_text(cleaning_brief_markdown(context, record), encoding="utf-8")
    schema_path = destination / "expected_schema.csv"
    with schema_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DICTIONARY_COLUMNS)
        writer.writeheader()
        writer.writerows(record["fields"])
    return destination
