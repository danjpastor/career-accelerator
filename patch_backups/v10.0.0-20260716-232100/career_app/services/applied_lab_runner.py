"""In-app SQL sandbox and automated rubric checks for Applied Labs.

The runner executes SQL in an isolated in-memory DuckDB database. Dataset files
from the selected lab's dataset folder are exposed as views named after their
filenames. User SQL cannot attach databases, load extensions, export files, or
read arbitrary paths.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


class AppliedLabRunnerError(RuntimeError):
    """Raised when an Applied Lab SQL submission cannot be run safely."""


SQL_LAB_PROFILES: dict[int, dict[str, Any]] = {
    15: {
        "label": "SQL validation checklist",
        "minimum_statements": 4,
        "required_any": [
            ("row-count check", (r"\bcount\s*\(",)),
            ("null-quality check", (r"\bis\s+null\b", r"\bcoalesce\s*\(")),
            ("duplicate or uniqueness check", (r"\bgroup\s+by\b", r"\bdistinct\b")),
            ("relationship check", (r"\bjoin\b", r"\bnot\s+exists\b")),
        ],
    },
    16: {
        "label": "broken join diagnosis",
        "minimum_statements": 2,
        "required_all": [
            ("join logic", r"\bjoin\b"),
            ("revenue aggregation", r"\bsum\s*\("),
            ("grain-aware grouping", r"\bgroup\s+by\b"),
        ],
    },
    17: {
        "label": "KPI repair",
        "minimum_statements": 2,
        "required_any": [
            ("numerator or denominator aggregation", (r"\bsum\s*\(", r"\bcount\s*\(")),
            ("explicit date boundary", (r"\bbetween\b", r">=", r"<")),
            ("weighted or ratio calculation", (r"\bnullif\s*\(", r"\bcast\s*\(", r"\*\s*1\.0", r"/")),
        ],
    },
    29: {
        "label": "conversion funnel",
        "minimum_statements": 1,
        "required_all": [
            ("multi-step query", r"\bwith\b"),
            ("deduplicated users", r"\bcount\s*\(\s*distinct\b"),
            ("segmented aggregation", r"\bgroup\s+by\b"),
        ],
    },
    30: {
        "label": "cohort retention",
        "minimum_statements": 1,
        "required_all": [
            ("multi-step cohort query", r"\bwith\b"),
            ("unique-user counts", r"\bcount\s*\(\s*distinct\b"),
        ],
        "required_any": [
            ("cohort-period date logic", (r"date_diff\s*\(", r"date_trunc\s*\(", r"strftime\s*\(", r"extract\s*\(")),
        ],
    },
    31: {
        "label": "churn analysis",
        "minimum_statements": 1,
        "required_all": [
            ("multi-step churn query", r"\bwith\b"),
            ("customer or revenue aggregation", r"\b(?:sum|count)\s*\("),
        ],
        "required_any": [
            ("period comparison", (r"lag\s*\(", r"lead\s*\(", r"date_trunc\s*\(", r"\bjoin\b")),
        ],
    },
    34: {
        "label": "raw-to-analytics pipeline",
        "minimum_statements": 4,
        "required_all": [
            ("layer creation", r"\bcreate\s+(?:or\s+replace\s+)?(?:temp(?:orary)?\s+)?(?:table|view)\b"),
            ("final analytical query", r"\bselect\b"),
        ],
        "required_any": [
            ("deduplication or quality logic", (r"row_number\s*\(", r"\bdistinct\b", r"\bgroup\s+by\b")),
            ("relationship or reconciliation logic", (r"\bjoin\b", r"\bnot\s+exists\b", r"\bsum\s*\(")),
        ],
    },
}

_BLOCKED_SQL = re.compile(
    r"\b(?:attach|detach|copy|export|import|install|load|pragma|call|create\s+secret|"
    r"read_csv|read_csv_auto|read_parquet|parquet_scan|read_json|read_json_auto|"
    r"read_ndjson|read_text|read_blob|read_xlsx|glob|sqlite_scan|postgres_scan|"
    r"httpfs|shell|system)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_SQL = re.compile(
    r"(?:\bTODO\b|\bYOUR[_ ]QUERY\b|\bREPLACE[_ ]ME\b|<[^>]+>|\.\.\.)",
    re.IGNORECASE,
)
_EXTERNAL_PATH_LITERAL = re.compile(
    r"(?P<quote>['\"])(?P<value>(?:[A-Za-z]:[\\/]|https?://|file://|[^'\"]*[\\/][^'\"]*|"
    r"[^'\"]*\.(?:csv|tsv|parquet|json|ndjson|duckdb|db|sqlite|xlsx)))(?P=quote)",
    re.IGNORECASE,
)


def is_sql_lab(item: dict[str, Any]) -> bool:
    return Path(str(item.get("starter_filename", ""))).suffix.lower() == ".sql"


def lab_paths(root: Path, number: int, item: dict[str, Any]) -> dict[str, Path]:
    practice = Path(root) / "practice" / "applied"
    exercise_dir = practice / "exercises" / str(item["slug"])
    starter = exercise_dir / str(item["starter_filename"])
    suffix = starter.suffix
    submission = practice / "submissions" / f"{int(number):02d}_{item['slug']}{suffix}"
    return {
        "practice_root": practice,
        "exercise_dir": exercise_dir,
        "starter": starter,
        "instructions": exercise_dir / "README.md",
        "validation": exercise_dir / "validation.md",
        "datasets": practice / "datasets" / str(item["dataset_slug"]),
        "submission": submission,
    }


def prepare_sql_for_app(sql: str) -> str:
    """Replace explicit dataset readers with the automatically loaded table name."""
    pattern = re.compile(
        r"(?:read_csv_auto|read_csv|read_parquet|read_json_auto)\s*\(\s*"
        r"(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)"
        r"(?:\s*,[^)]*)?\)",
        re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        filename = Path(match.group("path").replace("\\", "/")).name
        stem = Path(filename).stem
        return re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_").lower() or "dataset"

    return pattern.sub(replace, str(sql or ""))


def starter_sql(root: Path, number: int, item: dict[str, Any]) -> str:
    path = lab_paths(root, number, item)["starter"]
    if not path.exists():
        raise AppliedLabRunnerError(f"Starter SQL was not found: {path}")
    return prepare_sql_for_app(path.read_text(encoding="utf-8"))


def current_sql(root: Path, number: int, item: dict[str, Any]) -> str:
    paths = lab_paths(root, number, item)
    path = paths["submission"] if paths["submission"].exists() else paths["starter"]
    if not path.exists():
        raise AppliedLabRunnerError(f"SQL file was not found: {path}")
    return prepare_sql_for_app(path.read_text(encoding="utf-8"))


def save_submission(root: Path, number: int, item: dict[str, Any], sql: str) -> Path:
    if not is_sql_lab(item):
        raise AppliedLabRunnerError("The selected Applied Lab is not a SQL lab.")
    path = lab_paths(root, number, item)["submission"]
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"-- Career Accelerator Applied Lab {int(number):02d}\n"
        f"-- {item['title']}\n\n"
    )
    clean = str(sql or "").replace("\r\n", "\n").strip()
    if clean.startswith("-- Career Accelerator Applied Lab"):
        content = clean + "\n"
    else:
        content = header + clean + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL on semicolons while respecting quotes and comments."""
    statements: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    line_comment = False
    block_comment = False
    index = 0
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""
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
                quote = None
            index += 1
            continue
        if char == "-" and next_char == "-":
            buffer.extend((char, next_char))
            line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            buffer.extend((char, next_char))
            block_comment = True
            index += 2
            continue
        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if _strip_comments(statement).strip():
                statements.append(statement)
            buffer.clear()
            index += 1
            continue
        buffer.append(char)
        index += 1
    statement = "".join(buffer).strip()
    if _strip_comments(statement).strip():
        statements.append(statement)
    return statements


def validate_sql_safety(sql: str) -> None:
    cleaned = _strip_comments(sql)
    blocked = _BLOCKED_SQL.search(cleaned)
    if blocked:
        raise AppliedLabRunnerError(
            f"'{blocked.group(0)}' is not allowed in the in-app SQL sandbox. "
            "Use the automatically loaded dataset tables instead."
        )
    path_literal = _EXTERNAL_PATH_LITERAL.search(cleaned)
    if path_literal:
        raise AppliedLabRunnerError(
            "External file and URL paths are not allowed in the in-app SQL sandbox. "
            "Use the automatically loaded dataset tables instead."
        )


def _table_name(path: Path, dataset_root: Path, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_").lower() or "dataset"
    candidate = base
    if candidate in used:
        parent = re.sub(r"[^A-Za-z0-9_]+", "_", path.parent.name).strip("_").lower()
        candidate = f"{parent}_{base}" if parent else base
    suffix = 2
    original = candidate
    while candidate in used:
        candidate = f"{original}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def dataset_inventory(root: Path, number: int, item: dict[str, Any]) -> list[dict[str, Any]]:
    dataset_root = lab_paths(root, number, item)["datasets"]
    if not dataset_root.exists():
        return []
    used: set[str] = set()
    inventory: list[dict[str, Any]] = []
    for path in sorted(dataset_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".csv", ".parquet", ".json"}:
            continue
        name = _table_name(path, dataset_root, used)
        size = path.stat().st_size
        rows: int | None = None
        columns: list[str] = []
        if path.suffix.lower() == ".csv":
            try:
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.reader(handle)
                    columns = next(reader, [])
                    rows = sum(1 for _ in reader)
            except (OSError, UnicodeError, csv.Error):
                pass
        inventory.append(
            {
                "table": name,
                "path": path,
                "relative_path": str(path.relative_to(dataset_root)).replace("\\", "/"),
                "rows": rows,
                "columns": columns,
                "size_bytes": size,
            }
        )
    return inventory


def _duckdb_connection(root: Path, number: int, item: dict[str, Any]):
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - exercised on user machine if dependency missing
        raise AppliedLabRunnerError(
            "DuckDB is required for in-app Applied Lab SQL. Re-run the Career "
            "Accelerator launcher so requirements are installed."
        ) from exc
    connection = duckdb.connect(":memory:")
    inventory = dataset_inventory(root, number, item)
    for dataset in inventory:
        path = Path(dataset["path"])
        escaped_path = str(path.resolve()).replace("'", "''")
        table = dataset["table"].replace('"', '""')
        suffix = path.suffix.lower()
        if suffix == ".csv":
            source = f"read_csv_auto('{escaped_path}', header=true, sample_size=-1)"
        elif suffix == ".parquet":
            source = f"read_parquet('{escaped_path}')"
        else:
            source = f"read_json_auto('{escaped_path}')"
        connection.execute(f'CREATE VIEW "{table}" AS SELECT * FROM {source}')
    return connection, inventory


def run_sql(
    root: Path,
    number: int,
    item: dict[str, Any],
    sql: str,
    *,
    row_limit: int = 500,
) -> dict[str, Any]:
    if not is_sql_lab(item):
        raise AppliedLabRunnerError("The selected Applied Lab is not a SQL lab.")
    validate_sql_safety(sql)
    statements = split_sql_statements(sql)
    if not statements:
        raise AppliedLabRunnerError("Write at least one SQL statement before running the lab.")
    connection, inventory = _duckdb_connection(Path(root), number, item)
    result_sets: list[dict[str, Any]] = []
    executed: list[str] = []
    try:
        for position, statement in enumerate(statements, start=1):
            try:
                cursor = connection.execute(statement)
            except Exception as exc:
                raise AppliedLabRunnerError(
                    f"Statement {position} failed: {exc}"
                ) from exc
            executed.append(statement)
            description = cursor.description
            if description:
                columns = [str(column[0]) for column in description]
                rows = cursor.fetchmany(row_limit + 1)
                truncated = len(rows) > row_limit
                if truncated:
                    rows = rows[:row_limit]
                result_sets.append(
                    {
                        "statement_number": position,
                        "columns": columns,
                        "rows": [list(row) for row in rows],
                        "truncated": truncated,
                    }
                )
    finally:
        connection.close()
    return {
        "statement_count": len(executed),
        "result_sets": result_sets,
        "last_result": result_sets[-1] if result_sets else None,
        "datasets": inventory,
    }


def _normalized_sql(sql: str) -> str:
    cleaned = _strip_comments(sql).lower()
    return re.sub(r"\s+", " ", cleaned).strip().rstrip(";")


def _pattern_present(sql: str, pattern: str) -> bool:
    return bool(re.search(pattern, sql, flags=re.IGNORECASE | re.DOTALL))


def check_sql(root: Path, number: int, item: dict[str, Any], sql: str) -> dict[str, Any]:
    checklist: list[dict[str, Any]] = []

    def add(label: str, passed: bool, detail: str) -> None:
        checklist.append({"label": label, "passed": bool(passed), "detail": detail})

    clean = str(sql or "").strip()
    add("SQL has been written", bool(clean), "The editor must contain a submission.")
    if not clean:
        return {"passed": False, "checklist": checklist, "run": None}

    try:
        validate_sql_safety(clean)
        add("Sandbox safety", True, "No external file, extension, or database commands were found.")
    except AppliedLabRunnerError as exc:
        add("Sandbox safety", False, str(exc))
        return {"passed": False, "checklist": checklist, "run": None}

    try:
        starter = starter_sql(Path(root), number, item)
        changed = _normalized_sql(clean) != _normalized_sql(starter)
    except AppliedLabRunnerError:
        changed = True
    add(
        "Submission differs from the starter",
        changed,
        "Replace starter prompts and demonstrate your own analysis.",
    )
    no_placeholders = not bool(_PLACEHOLDER_SQL.search(_strip_comments(clean)))
    add(
        "No unfinished placeholders",
        no_placeholders,
        "Remove TODO, REPLACE ME, angle-bracket prompts, and ellipses.",
    )

    try:
        run = run_sql(Path(root), number, item, clean)
        add(
            "Every SQL statement executes",
            True,
            f"Executed {run['statement_count']} statement(s) in an isolated DuckDB database.",
        )
        has_result = bool(run["result_sets"])
        add(
            "At least one query returns evidence",
            has_result,
            "Include a SELECT that produces a reviewable result table.",
        )
    except AppliedLabRunnerError as exc:
        add("Every SQL statement executes", False, str(exc))
        return {"passed": False, "checklist": checklist, "run": None}

    profile = SQL_LAB_PROFILES.get(int(number), {})
    minimum_statements = int(profile.get("minimum_statements", 1))
    add(
        "Enough analytical steps",
        run["statement_count"] >= minimum_statements,
        f"This lab expects at least {minimum_statements} executable statement(s).",
    )
    flattened = _strip_comments(clean)
    for label, pattern in profile.get("required_all", []):
        passed = _pattern_present(flattened, pattern)
        add(f"Rubric: {label}", passed, f"Expected SQL pattern: {label}.")
    for label, patterns in profile.get("required_any", []):
        passed = any(_pattern_present(flattened, pattern) for pattern in patterns)
        add(f"Rubric: {label}", passed, f"Include evidence of {label} in the SQL.")

    passed = all(item_["passed"] for item_ in checklist)
    return {
        "passed": passed,
        "checklist": checklist,
        "run": run,
        "profile": profile.get("label", "Applied Lab SQL rubric"),
    }
