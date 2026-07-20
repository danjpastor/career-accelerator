from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import duckdb

from ..models import DatasetDefinition
from .base import ValidationResult


_FORBIDDEN = re.compile(
    r"\b(ATTACH|DETACH|COPY|INSTALL|LOAD|PRAGMA|CALL|EXPORT|IMPORT|CREATE|ALTER|DROP|UPDATE|DELETE|INSERT|MERGE|VACUUM)\b",
    re.IGNORECASE,
)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqlValidationError(ValueError):
    pass


def _safe_query(sql: str) -> str:
    query = str(sql or "").strip()
    if not query:
        raise SqlValidationError("Enter a SQL query before checking the answer.")
    body = query[:-1].rstrip() if query.endswith(";") else query
    if ";" in body:
        raise SqlValidationError("Run one query at a time.")
    if _FORBIDDEN.search(body):
        raise SqlValidationError("Only read-only SELECT queries are allowed in Academy practice.")
    if not re.match(r"^(SELECT|WITH)\b", body, re.IGNORECASE):
        raise SqlValidationError("Academy SQL practice accepts SELECT or WITH queries.")
    return body


def _load_dataset(conn: duckdb.DuckDBPyConnection, dataset: DatasetDefinition) -> None:
    for table in dataset.tables:
        if not _IDENTIFIER.fullmatch(table.name):
            raise SqlValidationError(f"Unsafe table name: {table.name}")
        conn.execute(
            f'CREATE OR REPLACE TABLE "{table.name}" AS SELECT * FROM read_csv_auto(?, HEADER=TRUE)',
            [str(table.csv_path)],
        )


def _normalize(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    return value


def _canonical(rows: list[tuple[Any, ...]], order_sensitive: bool) -> list[tuple[Any, ...]]:
    normalized = [tuple(_normalize(value) for value in row) for row in rows]
    return normalized if order_sensitive else sorted(normalized, key=repr)


class SqlValidator:
    def __init__(self, dataset: DatasetDefinition):
        self.dataset = dataset

    def execute(self, sql: str) -> ValidationResult:
        try:
            query = _safe_query(sql)
            with duckdb.connect(":memory:") as conn:
                _load_dataset(conn, self.dataset)
                cursor = conn.execute(query)
                columns = tuple(item[0] for item in cursor.description or ())
                rows = tuple(cursor.fetchall())
            return ValidationResult(True, f"Query ran successfully and returned {len(rows)} row(s).", columns, rows)
        except (duckdb.Error, SqlValidationError) as exc:
            return ValidationResult(False, str(exc))

    def validate(self, sql: str, config: dict[str, Any]) -> ValidationResult:
        try:
            query = _safe_query(sql)
            expected_query = _safe_query(str(config.get("expected_query") or ""))
            required_patterns = [str(item) for item in config.get("required_patterns", [])]
            forbidden_patterns = [str(item) for item in config.get("forbidden_patterns", [])]
            missing = [pattern for pattern in required_patterns if not re.search(pattern, query, re.IGNORECASE | re.DOTALL)]
            present_forbidden = [pattern for pattern in forbidden_patterns if re.search(pattern, query, re.IGNORECASE | re.DOTALL)]
            with duckdb.connect(":memory:") as conn:
                _load_dataset(conn, self.dataset)
                actual_cursor = conn.execute(query)
                actual_columns = tuple(item[0] for item in actual_cursor.description or ())
                actual_rows = actual_cursor.fetchall()
                expected_cursor = conn.execute(expected_query)
                expected_columns = tuple(item[0] for item in expected_cursor.description or ())
                expected_rows = expected_cursor.fetchall()
            order_sensitive = bool(config.get("order_sensitive", False))
            column_sensitive = bool(config.get("column_sensitive", True))
            allow_subset = bool(config.get("allow_subset", False))
            expected_count = config.get("expected_row_count")
            if allow_subset:
                actual_canonical = _canonical(actual_rows, False)
                expected_canonical = _canonical(expected_rows, False)
                expected_set = set(expected_canonical)
                rows_match = all(row in expected_set for row in actual_canonical)
                rows_match = rows_match and len(set(actual_canonical)) == len(actual_canonical)
                if expected_count is not None:
                    rows_match = rows_match and len(actual_rows) == int(expected_count)
                else:
                    rows_match = rows_match and len(actual_rows) <= len(expected_rows)
            else:
                rows_match = _canonical(actual_rows, order_sensitive) == _canonical(expected_rows, order_sensitive)
            columns_match = (not column_sensitive) or actual_columns == expected_columns
            passed = rows_match and columns_match and not missing and not present_forbidden
            messages: list[str] = []
            if passed:
                messages.append("Correct. The query returns the required result and uses the expected concepts.")
            else:
                if not rows_match:
                    messages.append("The result rows do not yet match the expected answer.")
                if not columns_match:
                    messages.append(f"Expected columns {expected_columns}, but received {actual_columns}.")
                if missing:
                    messages.append("Required SQL concept missing: " + ", ".join(missing))
                if present_forbidden:
                    messages.append("Avoided concept required: " + ", ".join(present_forbidden))
            return ValidationResult(
                passed,
                " ".join(messages),
                actual_columns,
                tuple(actual_rows),
                {
                    "expected_columns": list(expected_columns),
                    "expected_row_count": int(expected_count) if expected_count is not None else len(expected_rows),
                    "actual_row_count": len(actual_rows),
                    "allow_subset": allow_subset,
                    "missing_patterns": missing,
                    "forbidden_patterns": present_forbidden,
                },
            )
        except (duckdb.Error, SqlValidationError) as exc:
            return ValidationResult(False, str(exc))


def validate_recognition(answer: str, config: dict[str, Any]) -> ValidationResult:
    expected = str(config.get("expected_answer") or "").strip()
    actual = str(answer or "").strip()
    passed = actual.casefold() == expected.casefold()
    return ValidationResult(
        passed,
        "Correct." if passed else "Review the concept and try again.",
        details={"expected_answer": expected},
    )
