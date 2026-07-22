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


# BEGIN ACADEMY SPECIFIC FEEDBACK v10.20.6
_ACADEMY_SPECIFIC_FEEDBACK_VERSION = "1.0"

_KNOWN_PATTERN_LABELS = (
    ("group\\s", "GROUP BY"),
    ("order\\s", "ORDER BY"),
    ("partition\\s", "PARTITION BY"),
    ("select\\s+distinct", "SELECT DISTINCT"),
    ("count", "COUNT()"),
    ("sum", "SUM()"),
    ("avg", "AVG()"),
    ("min", "MIN()"),
    ("max", "MAX()"),
    ("having", "HAVING"),
    ("where", "WHERE"),
    ("left\\s", "LEFT JOIN"),
    ("right\\s", "RIGHT JOIN"),
    ("full\\s", "FULL JOIN"),
    ("inner\\s", "INNER JOIN"),
    ("join", "JOIN"),
    ("with", "WITH / CTE"),
    ("case", "CASE"),
    ("coalesce", "COALESCE()"),
    ("row_number", "ROW_NUMBER()"),
    ("rank", "RANK()"),
    ("dense_rank", "DENSE_RANK()"),
    ("lag", "LAG()"),
    ("lead", "LEAD()"),
    ("union", "UNION"),
    ("limit", "LIMIT"),
)

_RECOGNITION_CONCEPT_EXPLANATIONS = (
    ("selecting an explicit column list", "An explicit SELECT list controls which columns appear; it does not filter source rows."),
    ("select distinct", "SELECT DISTINCT removes duplicate combinations from the selected result columns."),
    ("distinct", "DISTINCT removes duplicate result-row combinations after the selected expressions are evaluated."),
    ("full outer join", "FULL JOIN preserves unmatched rows from both joined tables."),
    ("full join", "FULL JOIN preserves unmatched rows from both joined tables."),
    ("left outer join", "LEFT JOIN preserves every row from the left table and matches rows from the right table when available."),
    ("left join", "LEFT JOIN preserves every row from the left table and matches rows from the right table when available."),
    ("right outer join", "RIGHT JOIN preserves every row from the right table and matches rows from the left table when available."),
    ("right join", "RIGHT JOIN preserves every row from the right table and matches rows from the left table when available."),
    ("inner join", "INNER JOIN keeps only rows whose join condition finds a match on both sides."),
    ("cross join", "CROSS JOIN creates every possible row combination between the two inputs."),
    ("group by", "GROUP BY defines the groups at which aggregate calculations are produced."),
    ("having", "HAVING filters groups after aggregation; it does not filter individual source rows before grouping."),
    ("filtering with where", "WHERE filters which source rows qualify; it does not control which columns appear."),
    ("where", "WHERE filters source rows before grouping and aggregation."),
    ("sorting with order by", "ORDER BY changes result-row order; it does not change which rows or columns qualify."),
    ("order by", "ORDER BY changes result-row order without changing the underlying result membership."),
    ("union all", "UNION ALL stacks compatible result sets and retains duplicate rows."),
    ("union", "UNION stacks compatible result sets and removes duplicate rows unless UNION ALL is used."),
    ("primary key", "A primary key uniquely identifies each row in its own table."),
    ("foreign key", "A foreign key references a key in another table and represents a relationship between tables."),
    ("row_number", "ROW_NUMBER() assigns a unique sequence within the requested window ordering, even when values tie."),
    ("dense_rank", "DENSE_RANK() gives tied values the same rank without leaving gaps after a tie."),
    ("rank", "RANK() gives tied values the same rank and leaves gaps after a tie."),
    ("lag", "LAG() returns a value from an earlier row in the defined window order."),
    ("lead", "LEAD() returns a value from a later row in the defined window order."),
    ("coalesce", "COALESCE() returns the first non-NULL expression in its argument list."),
    ("count", "COUNT() measures rows or non-NULL values depending on the expression supplied."),
    ("sum", "SUM() adds numeric values within the current result group."),
    ("average", "AVG() calculates the mean of non-NULL numeric values within the current result group."),
    ("avg", "AVG() calculates the mean of non-NULL numeric values within the current result group."),
    ("minimum", "MIN() returns the smallest non-NULL value within the current result group."),
    ("maximum", "MAX() returns the largest non-NULL value within the current result group."),
    ("cte", "A CTE names an intermediate query result for use by the statement that follows it."),
    ("subquery", "A subquery produces an intermediate value or row set inside another query."),
)


def _recognition_choice_explanation(choice: str) -> Any:
    lowered = str(choice or "").strip().casefold()
    for phrase, explanation in _RECOGNITION_CONCEPT_EXPLANATIONS:
        if phrase in lowered:
            return explanation
    return None


def _feedback_block(problem: str, checks: list[str]) -> str:
    clean_checks = [str(item).strip() for item in checks if str(item).strip()]
    sections = ["Not correct yet.", "", "What is wrong", f"• {problem.strip()}"]
    if clean_checks:
        sections.extend(["", "What to check next"])
        sections.extend(f"• {item}" for item in clean_checks)
    return "\n".join(sections)


def _friendly_pattern_label(pattern: str, config: dict[str, Any]) -> str:
    labels = config.get("pattern_labels") or {}
    if isinstance(labels, dict):
        direct = labels.get(pattern)
        if direct:
            return str(direct)
    lowered = str(pattern).casefold()
    for fragment, label in _KNOWN_PATTERN_LABELS:
        if fragment in lowered:
            return label
    cleaned = str(pattern)
    replacements = {
        r"\\b": "",
        r"\\s+": " ",
        r"\\s*": " ",
        r"\\s": " ",
        r"\\(": "(",
        r"\\)": ")",
        "(?:": "(",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"[\^$?+*{}\[\]|]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ()")
    return cleaned or "the required SQL concept"


def _configured_pattern_feedback(
    config: dict[str, Any], key: str, pattern: str
) -> Any:
    mapping = config.get(key) or {}
    if isinstance(mapping, dict):
        value = mapping.get(pattern)
        if value:
            return str(value).strip()
    return None


def _diagnose_sql_error(exc: Exception) -> tuple[str, list[str], str]:
    raw = str(exc or "").strip()
    compact = " ".join(raw.split())
    lowered = compact.casefold()

    match = re.search(r'referenced column[\s\"]+"?([^"\s]+)"?[^\n]*not found', raw, re.IGNORECASE)
    if not match:
        match = re.search(r'column with name\s+"?([^"\s]+)"?\s+does not exist', raw, re.IGNORECASE)
    if match:
        column = match.group(1).rstrip(".,")
        return (
            f"The query references `{column}`, but DuckDB cannot find that column in the tables currently available to the query.",
            [
                "Check the spelling and capitalization against the table schema.",
                "Confirm the table containing that column appears in FROM or JOIN.",
                "If you used an alias, qualify the column with the correct alias.",
            ],
            "unknown_column",
        )

    match = re.search(r'table with name\s+"?([^"\s!]+)"?\s+does not exist', raw, re.IGNORECASE)
    if match:
        table = match.group(1).rstrip(".,")
        return (
            f"The query references a table named `{table}`, but that table is not part of this activity's dataset.",
            [
                "Compare the table name with the Data Tables list.",
                "Check whether you accidentally used a file name, schema name, or alias as the table name.",
            ],
            "unknown_table",
        )

    match = re.search(r'ambiguous reference to column name\s+"?([^"\s]+)"?', raw, re.IGNORECASE)
    if match or "ambiguous" in lowered and "column" in lowered:
        column = match.group(1).rstrip(".,") if match else "the referenced column"
        display = f"`{column}`" if match else column
        return (
            f"{display} exists in more than one joined table, so DuckDB cannot tell which one you intend to use.",
            [
                "Qualify the column with its table name or table alias, such as `orders.customer_id`.",
                "Use consistent aliases in SELECT, JOIN, WHERE, GROUP BY, and ORDER BY.",
            ],
            "ambiguous_column",
        )

    match = re.search(r'column\s+"?([^"\s]+)"?\s+must appear in the GROUP BY clause', raw, re.IGNORECASE)
    if match or "must appear in the group by clause" in lowered:
        column = match.group(1).rstrip(".,") if match else "a selected column"
        display = f"`{column}`" if match else column
        return (
            f"{display} is selected without being grouped or aggregated.",
            [
                "Add the non-aggregated column to GROUP BY if each value should define a group.",
                "Otherwise, apply the appropriate aggregate function to that column.",
                "Keep the requested result grain in mind before changing the grouping.",
            ],
            "group_by_violation",
        )

    if "conversion error" in lowered or "could not convert" in lowered or "cast" in lowered and "error" in lowered:
        return (
            "DuckDB could not convert one of the values to the data type required by your expression or comparison.",
            [
                "Check the inferred data types shown for the table columns.",
                "Compare dates with dates and numbers with numbers rather than relying on an implicit conversion.",
                "Inspect invalid or blank source values before applying CAST.",
            ],
            "type_conversion",
        )

    if "parser error" in lowered or "syntax error" in lowered:
        token_match = re.search(r'(?:at or near|near)\s+[\"\']([^\"\']+)[\"\']', raw, re.IGNORECASE)
        token = token_match.group(1) if token_match else None
        problem = "DuckDB could not parse the SQL syntax."
        if token:
            problem = f"DuckDB found a syntax problem near `{token}`."
        return (
            problem,
            [
                "Check commas, parentheses, quotes, and clause order near the reported location.",
                "Verify that SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, and LIMIT appear in valid SQL order.",
                "Run a smaller section of the query to isolate the first syntax problem.",
            ],
            "syntax_error",
        )

    if "binder error" in lowered:
        return (
            "DuckDB could not bind one or more names or expressions in the query to the available tables and columns.",
            [
                "Review table names, aliases, and column names against the activity schema.",
                "Check that every referenced column is available at the point where it is used.",
            ],
            "binding_error",
        )

    first_line = next((line.strip() for line in raw.splitlines() if line.strip()), "The query could not run.")
    return (
        first_line,
        [
            "Read the first DuckDB error line and inspect the clause it names.",
            "Run the query in smaller parts to find the first failing expression.",
        ],
        "execution_error",
    )


def _column_diagnostics(
    actual_columns: tuple[str, ...], expected_columns: tuple[str, ...]
) -> tuple[list[str], list[str], list[str]]:
    problems: list[str] = []
    checks: list[str] = []
    codes: list[str] = []
    if actual_columns == expected_columns:
        return problems, checks, codes

    actual_list = list(actual_columns)
    expected_list = list(expected_columns)
    missing = [name for name in expected_list if name not in actual_list]
    unexpected = [name for name in actual_list if name not in expected_list]

    if not missing and not unexpected and sorted(actual_list) == sorted(expected_list):
        problems.append(
            "The correct output columns are present, but they are in a different order from the requested result."
        )
        checks.append("Reorder the expressions in the SELECT list to match the requested column order.")
        codes.append("column_order")
        return problems, checks, codes

    if missing:
        problems.append("Missing output column(s): " + ", ".join(f"`{item}`" for item in missing) + ".")
        checks.append("Add the missing field or aggregate to the SELECT list using the requested alias.")
        codes.append("missing_columns")
    if unexpected:
        problems.append("Unexpected output column(s): " + ", ".join(f"`{item}`" for item in unexpected) + ".")
        checks.append("Return only the columns requested by the activity.")
        codes.append("unexpected_columns")
    if len(actual_list) == len(expected_list) and missing and unexpected:
        checks.append("A calculated expression may be correct but use the wrong alias; compare each output heading with the prompt.")
        codes.append("possible_alias_mismatch")
    return problems, checks, codes


def _row_diagnostics(
    actual_rows: list[tuple[Any, ...]],
    expected_rows: list[tuple[Any, ...]],
    *,
    order_sensitive: bool,
    allow_subset: bool,
    expected_count: Any,
) -> tuple[list[str], list[str], list[str]]:
    problems: list[str] = []
    checks: list[str] = []
    codes: list[str] = []
    actual_normalized = _canonical(actual_rows, False)
    expected_normalized = _canonical(expected_rows, False)
    target_count = int(expected_count) if expected_count is not None else len(expected_rows)

    duplicate_count = len(actual_normalized) - len(set(actual_normalized))
    if duplicate_count > 0:
        problems.append(f"The result contains {duplicate_count} duplicate row(s) that should not be repeated.")
        checks.append("Inspect JOIN keys and relationship cardinality; a many-to-many join can multiply rows.")
        checks.append("Use DISTINCT only when duplicate rows are truly accidental rather than hiding an incorrect join.")
        codes.append("duplicate_rows")

    if allow_subset:
        expected_set = set(expected_normalized)
        outside_count = sum(1 for row in actual_normalized if row not in expected_set)
        if outside_count:
            problems.append(f"{outside_count} returned row(s) fall outside the valid result set for this activity.")
            checks.append("Review the filter and join conditions that allow those extra rows into the result.")
            codes.append("invalid_subset_rows")
        if len(actual_rows) != target_count:
            direction = "too many" if len(actual_rows) > target_count else "too few"
            problems.append(f"The query returns {len(actual_rows)} row(s), but this activity requires {target_count}; that is {direction}.")
            if len(actual_rows) > target_count:
                checks.append("Check for a filter that is too broad, duplicated join matches, or grouping at too detailed a grain.")
                codes.append("row_count_high")
            else:
                checks.append("Check for a filter that is too restrictive, an INNER JOIN dropping rows, or grouping at too broad a grain.")
                codes.append("row_count_low")
        return problems, checks, codes

    if len(actual_rows) != len(expected_rows):
        direction = "too many" if len(actual_rows) > len(expected_rows) else "too few"
        problems.append(
            f"The query returns {len(actual_rows)} row(s), while the requested result has {len(expected_rows)}; that is {direction}."
        )
        if len(actual_rows) > len(expected_rows):
            checks.append("Check whether WHERE is too broad, a JOIN multiplies rows, or GROUP BY uses too many columns.")
            codes.append("row_count_high")
        else:
            checks.append("Check whether WHERE is too restrictive, an INNER JOIN removes unmatched rows, or GROUP BY combines distinct groups.")
            codes.append("row_count_low")
        return problems, checks, codes

    unordered_match = actual_normalized == expected_normalized
    ordered_match = _canonical(actual_rows, True) == _canonical(expected_rows, True)
    if order_sensitive and unordered_match and not ordered_match:
        problems.append("The rows contain the correct values, but they are not in the required order.")
        checks.append("Add or correct ORDER BY, including the requested sort direction and tie-breaker columns.")
        codes.append("row_order")
        return problems, checks, codes

    if not unordered_match:
        actual_counts: dict[str, int] = {}
        expected_counts: dict[str, int] = {}
        for row in actual_normalized:
            key = repr(row)
            actual_counts[key] = actual_counts.get(key, 0) + 1
        for row in expected_normalized:
            key = repr(row)
            expected_counts[key] = expected_counts.get(key, 0) + 1
        unexpected = sum(max(0, count - expected_counts.get(key, 0)) for key, count in actual_counts.items())
        missing = sum(max(0, count - actual_counts.get(key, 0)) for key, count in expected_counts.items())
        difference_count = max(unexpected, missing, 1)
        problems.append(
            f"The row count is correct, but {difference_count} row position(s) or grouped result(s) contain different values than required."
        )
        checks.append("Verify calculated expressions, aggregate functions, JOIN conditions, and filter boundaries.")
        checks.append("Confirm the query is producing the grain requested in the question before comparing individual values.")
        codes.append("row_values")
    return problems, checks, codes


def _specific_sql_validation(
    validator: "SqlValidator", sql: str, config: dict[str, Any]
) -> ValidationResult:
    try:
        query = _safe_query(sql)
        expected_query = _safe_query(str(config.get("expected_query") or ""))
        required_patterns = [str(item) for item in config.get("required_patterns", [])]
        forbidden_patterns = [str(item) for item in config.get("forbidden_patterns", [])]
        missing = [
            pattern
            for pattern in required_patterns
            if not re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        ]
        present_forbidden = [
            pattern
            for pattern in forbidden_patterns
            if re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        ]

        with duckdb.connect(":memory:") as conn:
            _load_dataset(conn, validator.dataset)
            actual_cursor = conn.execute(query)
            actual_columns = tuple(item[0] for item in actual_cursor.description or ())
            actual_rows = actual_cursor.fetchall()
            expected_cursor = conn.execute(expected_query)
            expected_columns = tuple(item[0] for item in expected_cursor.description or ())
            expected_rows = expected_cursor.fetchall()

        order_sensitive = bool(config.get("order_sensitive", False))
        column_sensitive = bool(config.get("column_sensitive", True))
        allow_subset = bool(config.get("allow_subset", False))
        raw_expected_count = config.get("expected_row_count")
        expected_count = int(raw_expected_count) if raw_expected_count is not None else None

        if allow_subset:
            actual_canonical = _canonical(actual_rows, False)
            expected_canonical = _canonical(expected_rows, False)
            expected_set = set(expected_canonical)
            rows_match = all(row in expected_set for row in actual_canonical)
            rows_match = rows_match and len(set(actual_canonical)) == len(actual_canonical)
            if expected_count is not None:
                rows_match = rows_match and len(actual_rows) == expected_count
            else:
                rows_match = rows_match and len(actual_rows) <= len(expected_rows)
        else:
            rows_match = _canonical(actual_rows, order_sensitive) == _canonical(expected_rows, order_sensitive)
        columns_match = (not column_sensitive) or actual_columns == expected_columns
        passed = rows_match and columns_match and not missing and not present_forbidden

        if passed:
            return ValidationResult(
                True,
                "Correct. The query returns the required result and uses the expected concepts.",
                actual_columns,
                tuple(actual_rows),
                {
                    "diagnostic_codes": [],
                    "expected_row_count": expected_count if expected_count is not None else len(expected_rows),
                    "actual_row_count": len(actual_rows),
                    "allow_subset": allow_subset,
                },
            )

        problems: list[str] = []
        checks: list[str] = []
        codes: list[str] = []

        if column_sensitive and not columns_match:
            column_problems, column_checks, column_codes = _column_diagnostics(actual_columns, expected_columns)
            problems.extend(column_problems)
            checks.extend(column_checks)
            codes.extend(column_codes)

        if not rows_match:
            row_problems, row_checks, row_codes = _row_diagnostics(
                actual_rows,
                expected_rows,
                order_sensitive=order_sensitive,
                allow_subset=allow_subset,
                expected_count=expected_count,
            )
            problems.extend(row_problems)
            checks.extend(row_checks)
            codes.extend(row_codes)

        for pattern in missing:
            label = _friendly_pattern_label(pattern, config)
            custom = _configured_pattern_feedback(config, "required_pattern_feedback", pattern)
            problems.append(custom or f"This activity requires you to practice `{label}`, but that concept is not present in the query.")
            checks.append(f"Revise the query to use {label} for the requested task rather than an equivalent shortcut.")
            codes.append("missing_required_concept")

        for pattern in present_forbidden:
            label = _friendly_pattern_label(pattern, config)
            custom = _configured_pattern_feedback(config, "forbidden_pattern_feedback", pattern)
            problems.append(custom or f"The query uses `{label}`, which this activity specifically asks you to avoid.")
            checks.append("Use the technique named in the lesson prompt instead of the prohibited shortcut.")
            codes.append("forbidden_concept")

        if not problems:
            problems.append("The result does not yet meet all of the activity requirements.")
            checks.append("Compare the requested grain, output columns, filters, calculations, and ordering with your query.")
            codes.append("result_mismatch")

        feedback = "Not correct yet.\n\nWhat is wrong\n" + "\n".join(f"• {item}" for item in problems)
        if checks:
            deduplicated_checks = list(dict.fromkeys(checks))
            feedback += "\n\nWhat to check next\n" + "\n".join(f"• {item}" for item in deduplicated_checks)

        return ValidationResult(
            False,
            feedback,
            actual_columns,
            tuple(actual_rows),
            {
                "diagnostic_codes": list(dict.fromkeys(codes)),
                "expected_columns": list(expected_columns),
                "actual_columns": list(actual_columns),
                "expected_row_count": expected_count if expected_count is not None else len(expected_rows),
                "actual_row_count": len(actual_rows),
                "allow_subset": allow_subset,
                "missing_patterns": missing,
                "forbidden_patterns": present_forbidden,
            },
        )
    except (duckdb.Error, SqlValidationError) as exc:
        problem, checks, code = _diagnose_sql_error(exc)
        return ValidationResult(
            False,
            _feedback_block(problem, checks),
            details={"diagnostic_codes": [code], "raw_error": str(exc)},
        )


def _specific_recognition_validation(answer: str, config: dict[str, Any]) -> ValidationResult:
    expected = str(config.get("expected_answer") or "").strip()
    actual = str(answer or "").strip()
    if not actual:
        return ValidationResult(
            False,
            _feedback_block("No answer is selected.", ["Choose one option, then check the answer again."]),
            details={"diagnostic_codes": ["no_answer_selected"]},
        )

    passed = actual.casefold() == expected.casefold()
    if passed:
        correct_feedback = str(config.get("correct_feedback") or "").strip()
        feedback = "Correct."
        if correct_feedback:
            feedback += " " + correct_feedback
        return ValidationResult(True, feedback, details={"diagnostic_codes": []})

    mappings = config.get("choice_feedback") or config.get("feedback_by_answer") or {}
    specific = None
    if isinstance(mappings, dict):
        for choice, message in mappings.items():
            if str(choice).strip().casefold() == actual.casefold() and str(message).strip():
                specific = str(message).strip()
                break
    fallback = str(config.get("incorrect_feedback") or "").strip()
    concept_explanation = _recognition_choice_explanation(actual)
    problem = specific or fallback
    if not problem and concept_explanation:
        problem = f"`{actual}` is not correct for this question. {concept_explanation}"
    if not problem:
        problem = f"`{actual}` does not match the distinction this question is testing."
    checks = [
        "Re-read the question and identify the exact concept or result each option describes.",
        "Compare the selected option with the lesson example, then eliminate choices that change the grain, rows, or meaning.",
    ]
    return ValidationResult(
        False,
        _feedback_block(problem, checks),
        details={
            "diagnostic_codes": ["incorrect_recognition_choice"],
            "selected_answer": actual,
            "feedback_source": (
                "choice_feedback"
                if specific
                else "incorrect_feedback"
                if fallback
                else "concept_explanation"
                if concept_explanation
                else "fallback"
            ),
        },
    )
# END ACADEMY SPECIFIC FEEDBACK v10.20.6

class SqlValidator:
    def __init__(self, dataset: DatasetDefinition):
        self.dataset = dataset

    def table_schema(self, table_name: str) -> tuple[tuple[str, str], ...]:
        """Return the DuckDB-inferred schema for one curriculum table.

        The same CSV loader used by the exercise runtime is used here so the
        learner sees the exact column names and data types available to their
        query.
        """
        table = next((item for item in self.dataset.tables if item.name == table_name), None)
        if table is None:
            raise SqlValidationError(f"Unknown table {table_name!r} in dataset {self.dataset.dataset_id!r}.")
        if not _IDENTIFIER.fullmatch(table.name):
            raise SqlValidationError(f"Unsafe table name: {table.name}")
        try:
            with duckdb.connect(":memory:") as conn:
                _load_dataset(conn, self.dataset)
                rows = conn.execute(f'PRAGMA table_info("{table.name}")').fetchall()
            return tuple((str(row[1]), str(row[2])) for row in rows)
        except duckdb.Error as exc:
            raise SqlValidationError(str(exc)) from exc

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
        return _specific_sql_validation(self, sql, config)


def validate_recognition(answer: str, config: dict[str, Any]) -> ValidationResult:
    return _specific_recognition_validation(answer, config)
