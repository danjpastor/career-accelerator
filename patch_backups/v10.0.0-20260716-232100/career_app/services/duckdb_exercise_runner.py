"""Safe in-app execution and result checking for guided DuckDB exercises.

The existing DuckDB exercise folders remain the source of truth.  This module
reads their README, starter SQL, validation checkpoints, datasets, and standard
submission file so the exercises can be completed without leaving Career
Accelerator.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from career_app.services import duckdb_workspace
from career_app.services.applied_lab_runner import split_sql_statements


class DuckDBExerciseRunnerError(RuntimeError):
    """Raised when a guided exercise cannot safely run or be checked."""


@dataclass(frozen=True)
class QuestionBlock:
    number: int
    prompt: str
    sql: str


@dataclass(frozen=True)
class ValidationCheckpoint:
    number: int
    expected_rows: int | None
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


_QUESTION_MARKER = re.compile(
    r"(?mi)^\s*--\s*Q(?:uestion\s*)?(\d+)\s*[.):-]?\s*(.*?)\s*$"
)
_BLOCKED_WRITE_SQL = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|UPSERT|CREATE|DROP|ALTER|TRUNCATE|"
    r"REPLACE|VACUUM|CHECKPOINT|EXPORT|IMPORT|COPY|ATTACH|DETACH|INSTALL|LOAD|"
    r"CALL|SET|RESET)\b",
    re.IGNORECASE,
)
_BLOCKED_FILE_SQL = re.compile(
    r"\b(?:read_csv|read_csv_auto|read_parquet|read_json|read_json_auto|"
    r"read_ndjson|glob|parquet_scan|csv_scan|sqlite_scan|postgres_scan|"
    r"httpfs|shell|system)\s*\(",
    re.IGNORECASE,
)
_PATH_LITERAL = re.compile(
    r"['\"](?:[A-Za-z]:[\\/]|\\\\|/|https?://|s3://|gs://|azure://)[^'\"]*['\"]",
    re.IGNORECASE,
)
_PLACEHOLDER = re.compile(
    r"(?i)(?:\bTODO\b|\bREPLACE\s+ME\b|write\s+(?:and\s+run\s+)?your\s+query|"
    r"<[^>]+>|\.\.\.)"
)


def exercise_paths(root: Path, number: int) -> dict[str, Path]:
    return duckdb_workspace.paths(Path(root), int(number))


def read_text(path: Path, *, required: bool = False) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        if required:
            raise DuckDBExerciseRunnerError(f"Required exercise file was not found: {path}")
        return ""
    except (OSError, UnicodeError) as exc:
        raise DuckDBExerciseRunnerError(f"Could not read {path.name}: {exc}") from exc


def instructions_markdown(root: Path, number: int) -> str:
    path = exercise_paths(root, number)["instructions"]
    text = read_text(path, required=True).strip()
    if not text:
        raise DuckDBExerciseRunnerError(f"Exercise instructions are empty: {path}")
    return text


def starter_sql(root: Path, number: int) -> str:
    return read_text(exercise_paths(root, number)["starter"], required=True)


def validation_markdown(root: Path, number: int) -> str:
    return read_text(exercise_paths(root, number)["validation"], required=True)


def submission_sql(root: Path, number: int) -> str:
    path = duckdb_workspace.submission_path(Path(root), int(number))
    if path.exists():
        return read_text(path, required=True)
    return starter_sql(root, number)


def save_submission(root: Path, number: int, sql: str) -> Path:
    path = duckdb_workspace.submission_path(Path(root), int(number))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = str(sql or "").replace("\r\n", "\n").replace("\r", "\n")
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def parse_questions(sql: str) -> list[QuestionBlock]:
    """Split a starter/submission script into its Q1, Q2, ... sections."""
    text = str(sql or "").replace("\r\n", "\n").replace("\r", "\n")
    matches = list(_QUESTION_MARKER.finditer(text))
    if not matches:
        return [QuestionBlock(1, "Exercise query", text.strip())] if text.strip() else []

    blocks: list[QuestionBlock] = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        prompt = match.group(2).strip() or f"Question {number}"
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        # Keep learner comments that explain their reasoning, but remove the
        # repeated scaffold instruction and decorative comment separators.
        cleaned_lines: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            if re.fullmatch(r"--\s*[-=#_*]{3,}", stripped):
                continue
            if re.search(r"(?i)write\s+(?:and\s+run\s+)?your\s+query", stripped):
                continue
            cleaned_lines.append(line)
        blocks.append(QuestionBlock(number, prompt, "\n".join(cleaned_lines).strip()))
    return blocks


def question_definitions(root: Path, number: int) -> list[QuestionBlock]:
    """Return the canonical question order and prompts from starter.sql."""
    questions = parse_questions(starter_sql(Path(root), int(number)))
    if not questions:
        raise DuckDBExerciseRunnerError(
            "The starter SQL does not contain any Q1, Q2, ... question sections."
        )
    return questions


def question_answers(root: Path, number: int) -> dict[int, str]:
    """Load independently editable answers from the standard submission file."""
    definitions = question_definitions(Path(root), int(number))
    current = {item.number: item.sql for item in parse_questions(submission_sql(root, number))}
    return {item.number: current.get(item.number, item.sql).strip() for item in definitions}


def compose_submission(root: Path, number: int, answers: dict[int, str]) -> str:
    """Build the reviewable standard SQL file from per-question answers.

    The original exercise preamble is retained, while each question receives
    only its own learner-authored SQL. This keeps the repository submission
    format compatible with the existing DuckDB practice library.
    """
    template = starter_sql(Path(root), int(number)).replace("\r\n", "\n").replace("\r", "\n")
    matches = list(_QUESTION_MARKER.finditer(template))
    if not matches:
        answer = str(answers.get(1, "") or "").strip()
        return (answer + "\n") if answer else ""

    preamble = template[: matches[0].start()].rstrip()
    parts: list[str] = [preamble] if preamble else []
    separator = "-- -----------------------------------------------------------------"
    for match in matches:
        question_number = int(match.group(1))
        marker = template[match.start() : match.end()].strip()
        answer = str(answers.get(question_number, "") or "").strip()
        parts.append(marker)
        if answer:
            parts.append(answer)
        else:
            parts.append("-- Write and run your query below this comment.")
        parts.append(separator)
    return "\n\n".join(parts).rstrip() + "\n"


def _scan_sql(sql: str, *, mask_literals: bool) -> str:
    """Remove comments and optionally mask quoted literals/identifiers.

    The scanner keeps newlines so error locations remain readable. Doubled quote
    escapes are handled for both SQL string literals and quoted identifiers.
    """
    text = str(sql or "")
    output: list[str] = []
    index = 0
    state = "normal"
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if state == "normal":
            if char == "-" and next_char == "-":
                output.extend((" ", " "))
                index += 2
                state = "line_comment"
                continue
            if char == "/" and next_char == "*":
                output.extend((" ", " "))
                index += 2
                state = "block_comment"
                continue
            if char == "'":
                output.append(" " if mask_literals else char)
                index += 1
                state = "single_quote"
                continue
            if char == '"':
                output.append(" " if mask_literals else char)
                index += 1
                state = "double_quote"
                continue
            output.append(char)
            index += 1
            continue

        if state == "line_comment":
            if char == "\n":
                output.append("\n")
                state = "normal"
            else:
                output.append(" ")
            index += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                output.extend((" ", " "))
                index += 2
                state = "normal"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
            continue

        quote = "'" if state == "single_quote" else '"'
        if char == quote and next_char == quote:
            replacement = "  " if mask_literals else quote + quote
            output.append(replacement)
            index += 2
            continue
        if char == quote:
            output.append(" " if mask_literals else char)
            index += 1
            state = "normal"
            continue
        output.append("\n" if char == "\n" else (" " if mask_literals else char))
        index += 1

    return "".join(output)


def _strip_sql_comments(sql: str) -> str:
    return _scan_sql(sql, mask_literals=False)


def _mask_sql_literals_and_comments(sql: str) -> str:
    return _scan_sql(sql, mask_literals=True)


def validate_read_only_sql(sql: str) -> None:
    code = _mask_sql_literals_and_comments(sql)
    comments_removed = _strip_sql_comments(sql)
    blocked = _BLOCKED_WRITE_SQL.search(code)
    if blocked:
        raise DuckDBExerciseRunnerError(
            f"'{blocked.group(0)}' is not allowed in guided exercises. "
            "Use read-only SELECT, WITH, VALUES, DESCRIBE, SHOW, or EXPLAIN queries."
        )
    file_call = _BLOCKED_FILE_SQL.search(code)
    if file_call:
        raise DuckDBExerciseRunnerError(
            "Direct file-reading functions are disabled. The exercise datasets "
            "are already available as DuckDB tables."
        )
    if _PATH_LITERAL.search(comments_removed):
        raise DuckDBExerciseRunnerError(
            "External file and URL paths are disabled in the in-app exercise runner."
        )
    statements = split_sql_statements(sql)
    if not statements:
        raise DuckDBExerciseRunnerError("Write a SQL query before running this question.")
    for statement in statements:
        first = re.match(r"\s*([A-Za-z]+)", _mask_sql_literals_and_comments(statement))
        keyword = first.group(1).upper() if first else ""
        if keyword not in {"SELECT", "WITH", "VALUES", "DESCRIBE", "DESC", "SHOW", "EXPLAIN", "SUMMARIZE"}:
            raise DuckDBExerciseRunnerError(
                f"Statements beginning with '{keyword or 'unknown'}' are not allowed. "
                "Guided exercises run read-only queries only."
            )


def _dataset_table_name(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", path.stem).strip("_").lower() or "dataset"


def dataset_inventory(root: Path, number: int) -> list[dict[str, Any]]:
    paths = exercise_paths(root, number)
    folder = paths["datasets"]
    inventory: list[dict[str, Any]] = []
    if not folder.exists():
        return inventory
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".csv", ".parquet", ".json"}:
            continue
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
        stem = _dataset_table_name(path)
        inventory.append(
            {
                "path": path,
                "table": stem,
                "prefixed_table": f"ex{int(number):02d}_{stem}",
                "rows": rows,
                "columns": columns,
            }
        )
    return inventory


def _connect(root: Path, number: int):
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - user environment only
        raise DuckDBExerciseRunnerError(
            "DuckDB is required for the in-app exercise runner. Restart Career "
            "Accelerator through its launcher so requirements are installed."
        ) from exc

    paths = exercise_paths(root, number)
    database = paths["database"]
    inventory = dataset_inventory(root, number)
    if database.exists():
        try:
            connection = duckdb.connect(str(database), read_only=True)
        except Exception as exc:
            raise DuckDBExerciseRunnerError(
                f"Could not open the practice database read-only: {exc}"
            ) from exc
        return connection, inventory

    connection = duckdb.connect(":memory:")
    try:
        for dataset in inventory:
            path = Path(dataset["path"])
            escaped = str(path.resolve()).replace("'", "''")
            suffix = path.suffix.lower()
            if suffix == ".csv":
                source = f"read_csv_auto('{escaped}', header=true, sample_size=-1)"
            elif suffix == ".parquet":
                source = f"read_parquet('{escaped}')"
            else:
                source = f"read_json_auto('{escaped}')"
            names = [str(dataset["table"]), str(dataset["prefixed_table"])]
            for table in dict.fromkeys(names):
                quoted = table.replace('"', '""')
                connection.execute(f'CREATE VIEW "{quoted}" AS SELECT * FROM {source}')
    except Exception:
        connection.close()
        raise
    return connection, inventory


def run_sql(root: Path, number: int, sql: str, *, row_limit: int = 500) -> dict[str, Any]:
    validate_read_only_sql(sql)
    statements = split_sql_statements(sql)
    connection, inventory = _connect(Path(root), int(number))
    result_sets: list[dict[str, Any]] = []
    try:
        for position, statement in enumerate(statements, start=1):
            try:
                cursor = connection.execute(statement)
            except Exception as exc:
                raise DuckDBExerciseRunnerError(f"Statement {position} failed: {exc}") from exc
            if cursor.description:
                columns = [str(column[0]) for column in cursor.description]
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
    if not result_sets:
        raise DuckDBExerciseRunnerError(
            "The question ran, but it did not return a result table to review."
        )
    return {
        "statement_count": len(statements),
        "result_sets": result_sets,
        "last_result": result_sets[-1],
        "datasets": inventory,
    }


def run_question(root: Path, number: int, full_sql: str, question_number: int) -> dict[str, Any]:
    questions = {question.number: question for question in parse_questions(full_sql)}
    question = questions.get(int(question_number))
    if question is None:
        raise DuckDBExerciseRunnerError(f"Question {question_number} was not found in the SQL file.")
    return run_sql(root, number, question.sql)


def _split_table_line(line: str) -> list[str]:
    if "|" in line:
        return [part.strip() for part in line.strip().strip("|").split("|")]
    # Validation checkpoints use aligned whitespace; two or more spaces are
    # the reliable delimiter while preserving single spaces inside values.
    return [part.strip() for part in re.split(r"\s{2,}|\t+", line.strip()) if part.strip()]


def _is_separator_row(parts: Iterable[str]) -> bool:
    values = list(parts)
    return bool(values) and all(re.fullmatch(r":?-{2,}:?", value or "") for value in values)


def parse_validation(markdown: str) -> dict[int, ValidationCheckpoint]:
    text = str(markdown or "").replace("\r\n", "\n").replace("\r", "\n")
    heading = re.compile(r"(?mi)^\s*##+\s*Q(?:uestion\s*)?(\d+)\b[^\n]*$")
    matches = list(heading.finditer(text))
    checkpoints: dict[int, ValidationCheckpoint] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[match.end():end]
        rows_match = re.search(r"(?im)Expected\s+rows?\s*:\s*(\d+)", section)
        expected_rows = int(rows_match.group(1)) if rows_match else None
        lines = []
        in_fence = False
        for raw in section.splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if not stripped:
                continue
            if re.match(r"(?i)Expected\s+rows?\s*:", stripped):
                continue
            if re.match(r"(?i)(Only\s+the\s+first|Checkpoint|Notes?|Expected\s+columns?)", stripped):
                continue
            if stripped.startswith(("- ", "* ", "> ")) and not in_fence:
                continue
            if in_fence or "|" in stripped or re.search(r"\s{2,}|\t", stripped):
                lines.append(stripped)
        columns: list[str] = []
        expected_data: list[tuple[str, ...]] = []
        if lines:
            first = _split_table_line(lines[0])
            if first and not _is_separator_row(first):
                columns = first
            cursor = 1
            if cursor < len(lines) and _is_separator_row(_split_table_line(lines[cursor])):
                cursor += 1
            for line in lines[cursor:]:
                parts = _split_table_line(line)
                if not parts or _is_separator_row(parts):
                    continue
                if columns and len(parts) != len(columns):
                    continue
                expected_data.append(tuple(parts))
        checkpoints[number] = ValidationCheckpoint(
            number=number,
            expected_rows=expected_rows,
            columns=tuple(columns),
            rows=tuple(expected_data),
        )
    return checkpoints


def _normal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, Decimal)):
        try:
            decimal = Decimal(str(value))
            if decimal == decimal.to_integral():
                return str(decimal.quantize(Decimal("1")))
            return format(decimal.normalize(), "f").rstrip("0").rstrip(".")
        except (InvalidOperation, ValueError):
            pass
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return "null"
    try:
        decimal = Decimal(text.replace(",", ""))
        if decimal == decimal.to_integral():
            return str(decimal.quantize(Decimal("1")))
        return format(decimal.normalize(), "f").rstrip("0").rstrip(".")
    except (InvalidOperation, ValueError):
        return re.sub(r"\s+", " ", text).lower()


def _compare_checkpoint(run: dict[str, Any], checkpoint: ValidationCheckpoint | None) -> list[dict[str, Any]]:
    result = run["last_result"]
    columns = list(result["columns"])
    rows = list(result["rows"])
    checks: list[dict[str, Any]] = []

    def add(label: str, passed: bool, detail: str) -> None:
        checks.append({"label": label, "passed": bool(passed), "detail": detail})

    add("Query executes", True, f"Returned {len(rows)} displayed row(s).")
    if checkpoint is None:
        add(
            "Validation checkpoint available",
            False,
            "The validation file does not contain a matching Q heading for this question.",
        )
        return checks
    if checkpoint.expected_rows is not None:
        add(
            "Expected row count",
            len(rows) == checkpoint.expected_rows,
            f"Expected {checkpoint.expected_rows}; received {len(rows)}.",
        )
    if checkpoint.columns:
        actual_columns = [_normal(value) for value in columns]
        expected_columns = [_normal(value) for value in checkpoint.columns]
        add(
            "Expected columns",
            actual_columns == expected_columns,
            "Expected " + ", ".join(checkpoint.columns) + "; received " + ", ".join(columns) + ".",
        )
    if checkpoint.rows:
        actual_preview = [tuple(_normal(value) for value in row) for row in rows[: len(checkpoint.rows)]]
        expected_preview = [tuple(_normal(value) for value in row) for row in checkpoint.rows]
        add(
            "Expected checkpoint values",
            actual_preview == expected_preview,
            f"Compared the first {len(expected_preview)} validation row(s) in order.",
        )
    return checks


def check_question(
    root: Path,
    number: int,
    full_sql: str,
    question_number: int,
) -> dict[str, Any]:
    questions = {question.number: question for question in parse_questions(full_sql)}
    question = questions.get(int(question_number))
    if question is None:
        raise DuckDBExerciseRunnerError(f"Question {question_number} was not found in the SQL file.")
    if not question.sql.strip() or _PLACEHOLDER.search(_strip_sql_comments(question.sql)):
        return {
            "passed": False,
            "question": question,
            "run": None,
            "checklist": [
                {
                    "label": "Question answered",
                    "passed": False,
                    "detail": "Replace the starter prompt with your own SQL before checking.",
                }
            ],
        }
    run = run_sql(root, number, question.sql)
    checkpoints = parse_validation(validation_markdown(root, number))
    checklist = _compare_checkpoint(run, checkpoints.get(int(question_number)))
    return {
        "passed": bool(checklist) and all(item["passed"] for item in checklist),
        "question": question,
        "run": run,
        "checklist": checklist,
    }


def check_exercise(root: Path, number: int, full_sql: str) -> dict[str, Any]:
    questions = parse_questions(full_sql)
    if not questions:
        raise DuckDBExerciseRunnerError("The submission does not contain any exercise questions.")
    results: list[dict[str, Any]] = []
    for question in questions:
        try:
            result = check_question(root, number, full_sql, question.number)
        except DuckDBExerciseRunnerError as exc:
            result = {
                "passed": False,
                "question": question,
                "run": None,
                "checklist": [
                    {"label": "Query executes", "passed": False, "detail": str(exc)}
                ],
            }
        results.append(result)
    passed = bool(results) and all(result["passed"] for result in results)
    return {
        "passed": passed,
        "questions": results,
        "passed_count": sum(1 for result in results if result["passed"]),
        "total_count": len(results),
    }
