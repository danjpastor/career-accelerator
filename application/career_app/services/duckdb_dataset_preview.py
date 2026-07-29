"""Build learner-facing schema and sample-row previews for DuckDB exercises.

The preview is generated from the same local files or read-only DuckDB database
used by the exercise runner.  It contains data context only; it never executes
or exposes an authored solution.
"""
from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any, Iterable, Sequence

PREVIEW_MARKER = "<!-- DCA:DUCKDB-DATASET-PREVIEW -->"
DEFAULT_ROW_LIMIT = 5
MAX_PREVIEW_COLUMNS = 16
MAX_CELL_LENGTH = 80
_FILE_PREVIEW_CACHE: dict[tuple[str, int, int, int], dict[str, Any]] = {}
_DATABASE_PREVIEW_CACHE: dict[tuple[str, int, int, int, tuple[str, ...]], list[dict[str, Any]]] = {}


def _markdown_text(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (date, datetime)):
        text = value.isoformat()
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    text = text.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    if len(text) > MAX_CELL_LENGTH:
        text = text[: MAX_CELL_LENGTH - 1].rstrip() + "…"
    return text or ""


def _markdown_table(headers: Sequence[Any], rows: Iterable[Sequence[Any]]) -> str:
    safe_headers = [_markdown_text(value) for value in headers]
    if not safe_headers:
        return "_No columns were detected._"
    lines = [
        "| " + " | ".join(safe_headers) + " |",
        "| " + " | ".join("---" for _ in safe_headers) + " |",
    ]
    for row in rows:
        values = list(row)
        padded = values + [None] * max(0, len(safe_headers) - len(values))
        lines.append(
            "| "
            + " | ".join(_markdown_text(value) for value in padded[: len(safe_headers)])
            + " |"
        )
    return "\n".join(lines)


def _quoted_identifier(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _duckdb_file_source(path: Path) -> str:
    escaped = str(path.resolve()).replace("'", "''")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return f"read_csv_auto('{escaped}', header=true, sample_size=-1)"
    if suffix == ".parquet":
        return f"read_parquet('{escaped}')"
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return f"read_json_auto('{escaped}')"
    raise ValueError(f"Unsupported dataset type: {suffix}")


def _duckdb_file_preview(path: Path, row_limit: int) -> dict[str, Any] | None:
    try:
        import duckdb  # type: ignore
    except ImportError:
        return None

    connection = duckdb.connect(":memory:")
    try:
        source = _duckdb_file_source(path)
        description_rows = connection.execute(
            f"DESCRIBE SELECT * FROM {source}"
        ).fetchall()
        schema = [(str(row[0]), str(row[1])) for row in description_rows]
        cursor = connection.execute(
            f"SELECT * FROM {source} LIMIT {max(1, int(row_limit))}"
        )
        columns = [str(column[0]) for column in cursor.description or []]
        rows = [list(row) for row in cursor.fetchall()]
        return {"schema": schema, "columns": columns, "rows": rows}
    finally:
        connection.close()


def _looks_null(value: Any) -> bool:
    return value is None or str(value).strip().casefold() in {"", "null", "none", "na", "n/a"}


def _infer_scalar_type(values: Sequence[Any]) -> str:
    observed = [value for value in values if not _looks_null(value)]
    if not observed:
        return "VARCHAR"

    lowered = [str(value).strip().casefold() for value in observed]
    if all(value in {"true", "false", "yes", "no", "0", "1"} for value in lowered):
        return "BOOLEAN"

    try:
        for value in observed:
            int(str(value).strip())
        return "BIGINT"
    except (TypeError, ValueError):
        pass

    try:
        for value in observed:
            Decimal(str(value).strip().replace(",", ""))
        return "DECIMAL"
    except (InvalidOperation, TypeError, ValueError):
        pass

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    datetime_pattern = re.compile(
        r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$"
    )
    if all(date_pattern.match(str(value).strip()) for value in observed):
        return "DATE"
    if all(datetime_pattern.match(str(value).strip()) for value in observed):
        return "TIMESTAMP"
    return "VARCHAR"


def _records_preview(records: Sequence[dict[str, Any]], row_limit: int) -> dict[str, Any]:
    columns: list[str] = []
    for record in records:
        for key in record:
            name = str(key)
            if name not in columns:
                columns.append(name)
    rows = [[record.get(column) for column in columns] for record in records[:row_limit]]
    schema = [
        (column, _infer_scalar_type([record.get(column) for record in records[:50]]))
        for column in columns
    ]
    return {"schema": schema, "columns": columns, "rows": rows}


def _csv_preview(path: Path, row_limit: int) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        records: list[dict[str, Any]] = []
        for record in reader:
            records.append(dict(record))
            if len(records) >= 50:
                break
    return _records_preview(records, row_limit)


def _json_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    stripped = text.lstrip()
    payload: Any
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
            else:
                records.append({"value": item})
            if len(records) >= 50:
                break
        return records

    if isinstance(payload, list):
        return [item if isinstance(item, dict) else {"value": item} for item in payload[:50]]
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return [item if isinstance(item, dict) else {"value": item} for item in value[:50]]
        return [payload]
    return [{"value": payload}]


def _standard_file_preview(path: Path, row_limit: int) -> dict[str, Any] | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _csv_preview(path, row_limit)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return _records_preview(_json_records(path), row_limit)
    return None


def _file_preview(path: Path, row_limit: int) -> dict[str, Any]:
    resolved = path.resolve()
    stat = resolved.stat()
    key = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size), int(row_limit))
    cached = _FILE_PREVIEW_CACHE.get(key)
    if cached is not None:
        return cached
    preview = _duckdb_file_preview(resolved, row_limit)
    if preview is None:
        preview = _standard_file_preview(resolved, row_limit)
    if preview is None:
        preview = {"schema": [], "columns": [], "rows": []}
    if len(_FILE_PREVIEW_CACHE) >= 32:
        _FILE_PREVIEW_CACHE.clear()
    _FILE_PREVIEW_CACHE[key] = preview
    return preview


def _candidate_table_names(markdown: str, number: int) -> list[str]:
    candidates: list[str] = []
    patterns = (
        r"(?i)\b(?:FROM|JOIN)\s+[`\"]?([A-Za-z_][A-Za-z0-9_]*)",
        r"`([A-Za-z_][A-Za-z0-9_]*)`",
    )
    for pattern in patterns:
        for match in re.findall(pattern, str(markdown or "")):
            name = str(match)
            if name.casefold() in {"select", "where", "group", "order", "limit", "null"}:
                continue
            if name not in candidates:
                candidates.append(name)
    prefix = f"ex{int(number):02d}_"
    return [name for name in candidates if name.startswith(prefix)] + [
        name for name in candidates if not name.startswith(prefix)
    ]


def _database_previews(
    root: Path,
    number: int,
    markdown: str,
    row_limit: int,
) -> list[dict[str, Any]]:
    database = Path(root) / "practice" / "duckdb" / "career_practice.duckdb"
    if not database.exists():
        return []
    try:
        import duckdb  # type: ignore
    except ImportError:
        return []

    stat = database.stat()
    candidates = tuple(_candidate_table_names(markdown, number))
    cache_key = (
        str(database.resolve()),
        int(stat.st_mtime_ns),
        int(number),
        int(row_limit),
        candidates,
    )
    cached = _DATABASE_PREVIEW_CACHE.get(cache_key)
    if cached is not None:
        return cached

    connection = duckdb.connect(str(database), read_only=True)
    try:
        table_rows = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_name
            """
        ).fetchall()
        available = [str(row[0]) for row in table_rows]
        available_lookup = {name.casefold(): name for name in available}
        selected: list[str] = []
        for candidate in candidates:
            actual = available_lookup.get(candidate.casefold())
            if actual and actual not in selected:
                selected.append(actual)
        prefix = f"ex{int(number):02d}_"
        for name in available:
            if name.startswith(prefix) and name not in selected:
                selected.append(name)
        if not selected and len(available) == 1:
            selected = available

        previews: list[dict[str, Any]] = []
        for table in selected[:4]:
            quoted = _quoted_identifier(table)
            schema_rows = connection.execute(f"DESCRIBE {quoted}").fetchall()
            schema = [(str(row[0]), str(row[1])) for row in schema_rows]
            cursor = connection.execute(
                f"SELECT * FROM {quoted} LIMIT {max(1, int(row_limit))}"
            )
            columns = [str(column[0]) for column in cursor.description or []]
            rows = [list(row) for row in cursor.fetchall()]
            previews.append(
                {
                    "table": table,
                    "prefixed_table": table,
                    "path": database,
                    "schema": schema,
                    "columns": columns,
                    "rows": rows,
                    "source_kind": "database",
                }
            )
        if len(_DATABASE_PREVIEW_CACHE) >= 16:
            _DATABASE_PREVIEW_CACHE.clear()
        _DATABASE_PREVIEW_CACHE[cache_key] = previews
        return previews
    finally:
        connection.close()


def _dataset_sections(
    *,
    root: Path,
    number: int,
    markdown: str,
    inventory: Sequence[dict[str, Any]],
    row_limit: int,
) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for dataset in inventory:
        path_value = dataset.get("path")
        if not path_value:
            continue
        path = Path(path_value)
        try:
            preview = _file_preview(path, row_limit)
        except Exception as exc:  # Dataset context should not block the lesson.
            preview = {"schema": [], "columns": [], "rows": [], "error": str(exc)}
        sections.append(
            {
                **dict(dataset),
                "row_count": dataset.get("rows"),
                **preview,
                "source_kind": "file",
            }
        )
    if sections:
        return sections
    return _database_previews(root, number, markdown, row_limit)


def build_preview_markdown(
    *,
    root: Path,
    number: int,
    markdown: str,
    inventory: Sequence[dict[str, Any]] | None = None,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> str:
    """Return a Markdown Dataset Preview section for one exercise."""
    datasets = _dataset_sections(
        root=Path(root),
        number=int(number),
        markdown=str(markdown or ""),
        inventory=list(inventory or []),
        row_limit=max(1, int(row_limit)),
    )
    lines = [
        PREVIEW_MARKER,
        "## Dataset Preview",
        "",
        "Review the table structure before writing your query. The sample below comes from the same local dataset used by this exercise.",
        "",
    ]

    if not datasets:
        lines.extend(
            [
                "> **Preview unavailable:** The exercise dataset could not be read. Restore the `practice/duckdb` files or restart Career Accelerator through its launcher, then reopen this exercise.",
                "",
            ]
        )
        return "\n".join(lines).rstrip()

    for dataset in datasets:
        table = str(dataset.get("table") or Path(dataset.get("path", "dataset")).stem or "dataset")
        prefixed = str(dataset.get("prefixed_table") or "")
        aliases = [table]
        if prefixed and prefixed != table:
            aliases.append(prefixed)
        lines.append(f"### `{table}`")
        lines.append("")
        lines.append(f"One row represents one record in the `{table}` table.")
        if aliases:
            alias_text = " and ".join(f"`{name}`" for name in aliases)
            lines.append(f"Use {alias_text} as the table name in this exercise.")
        row_count = dataset.get("row_count")
        if row_count is None and isinstance(dataset.get("rows"), int):
            row_count = dataset.get("rows")
        if row_count is not None:
            lines.append(f"The source contains **{int(row_count):,} rows**.")
        lines.append("")

        schema = list(dataset.get("schema") or [])
        if not schema:
            inventory_columns = [str(value) for value in dataset.get("columns") or []]
            schema = [(column, "Type detected when the exercise runs") for column in inventory_columns]
        lines.append("#### Schema")
        lines.append("")
        if schema:
            lines.append(_markdown_table(("Column", "Data type"), schema))
        else:
            lines.append("_No schema information was available._")
        lines.append("")

        columns = [str(value) for value in dataset.get("columns") or []]
        sample_rows = (
            list(dataset.get("rows") or [])
            if not isinstance(dataset.get("rows"), int)
            else []
        )
        preview_columns = columns[:MAX_PREVIEW_COLUMNS]
        preview_rows = [list(row)[:MAX_PREVIEW_COLUMNS] for row in sample_rows]
        lines.append(f"#### First {min(max(1, int(row_limit)), 5)} rows")
        lines.append("")
        if preview_columns:
            if len(columns) > MAX_PREVIEW_COLUMNS:
                lines.append(
                    f"_Showing the first {MAX_PREVIEW_COLUMNS} of {len(columns)} columns. The full schema is listed above._"
                )
                lines.append("")
            lines.append(_markdown_table(preview_columns, preview_rows))
            if not preview_rows:
                lines.append("")
                lines.append("_The table has columns but no sample rows._")
        else:
            error = str(dataset.get("error") or "").strip()
            if error:
                lines.append(f"_The sample rows could not be loaded: {_markdown_text(error)}_")
            else:
                lines.append("_No sample rows were available._")
        lines.append("")

    return "\n".join(lines).rstrip()


def inject_preview(
    *,
    root: Path,
    number: int,
    markdown: str,
    inventory: Sequence[dict[str, Any]] | None = None,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> str:
    """Insert one generated Dataset Preview after the lesson title."""
    original = str(markdown or "").strip()
    if PREVIEW_MARKER in original:
        return original
    preview = build_preview_markdown(
        root=Path(root),
        number=int(number),
        markdown=original,
        inventory=inventory,
        row_limit=row_limit,
    )
    lines = original.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("# "):
            insert_at = index + 1
            while insert_at < len(lines) and not lines[insert_at].strip():
                insert_at += 1
            break
    combined = lines[:insert_at] + ["", preview, ""] + lines[insert_at:]
    return "\n".join(combined).strip() + "\n"
