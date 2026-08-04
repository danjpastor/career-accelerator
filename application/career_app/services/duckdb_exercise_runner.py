"""Catalog-backed execution and validation for native SQL challenges.

The public API intentionally matches the original guided DuckDB runner so the
existing DuckDBExercisesWidget remains the UI and behavior source of truth.
Only the curriculum, datasets, prompts, hints, solutions, and validation
contracts are replaced.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

try:
    import duckdb
except Exception:  # pragma: no cover - surfaced to the learner at runtime
    duckdb = None

from career_app.data.duckdb_exercises import ordered_exercise_numbers, roadmap_number
from career_app.data.sql_challenge_practice import load_catalog
from career_app.services import duckdb_workspace, roadmap_mastery


class DuckDBExerciseRunnerError(RuntimeError):
    """Raised when a SQL challenge cannot be loaded, run, or checked safely."""


@dataclass(frozen=True)
class QuestionBlock:
    number: int
    prompt: str
    sql: str = ""
    requirements: tuple[str, ...] = ()
    hints: tuple[str, ...] = ()


_BLOCKED_SQL = re.compile(
    r"\b(?:ATTACH|DETACH|INSTALL|LOAD|COPY|EXPORT|IMPORT|PRAGMA|CALL|"
    r"READ_CSV|READ_PARQUET|READ_JSON|HTTPFS|GLOB|SHELL|SECRET|SYSTEM)\b",
    re.IGNORECASE,
)
_ALLOWED_TEMP_VIEW = re.compile(
    r"^CREATE\s+(?:OR\s+REPLACE\s+)?TEMP(?:ORARY)?\s+VIEW\b",
    re.IGNORECASE | re.DOTALL,
)
_QUERY_START = re.compile(r"^(?:SELECT|WITH)\b", re.IGNORECASE | re.DOTALL)


def _catalog() -> dict[str, Any]:
    try:
        return load_catalog()
    except Exception as exc:
        raise DuckDBExerciseRunnerError(
            f"The SQL challenge catalog could not be loaded: {exc}"
        ) from exc


def _display_number(number: int) -> int:
    try:
        return int(roadmap_number(int(number)))
    except Exception:
        numbers = list(ordered_exercise_numbers())
        try:
            return numbers.index(int(number)) + 1
        except ValueError as exc:
            raise DuckDBExerciseRunnerError(
                f"Unknown SQL challenge number: {number}"
            ) from exc


def _exercise(number: int) -> dict[str, Any]:
    display = _display_number(number)
    exercises = list(_catalog().get("exercises") or [])
    if display < 1 or display > len(exercises):
        raise DuckDBExerciseRunnerError(f"SQL challenge {display} is not defined.")
    return dict(exercises[display - 1])


def _dataset_tables(number: int) -> list[dict[str, Any]]:
    catalog = _catalog()
    spec = _exercise(number)
    tables = (catalog.get("datasets") or {}).get(spec.get("dataset_id"))
    if not isinstance(tables, list):
        raise DuckDBExerciseRunnerError(
            f"Dataset {spec.get('dataset_id')!r} is missing for "
            f"SQL challenge {_display_number(number)}."
        )
    return [dict(table) for table in tables]


def exercise_paths(root: Path, number: int) -> dict[str, Path]:
    paths = dict(duckdb_workspace.paths(Path(root), int(number)))
    paths["submission"] = duckdb_workspace.submission_path(Path(root), int(number))
    return paths


def _source_banner(spec: dict[str, Any]) -> str:
    source = dict(spec.get("source") or {})
    provider = str(source.get("provider") or "Source challenge")
    challenge = str(source.get("challenge") or "Original challenge structure")
    url = str(source.get("url") or "").strip()
    linked = f"[{provider} — {challenge}]({url})" if url else f"{provider} — {challenge}"
    return (
        f"> **Challenge structure source:** {linked}  \n"
        "> Career Accelerator rebuilt this exercise with original wording, scenario, "
        "schema, records, expected output, hints, and solution."
    )


def instructions_markdown(root: Path, number: int) -> str:
    del root
    spec = _exercise(number)
    requirements = "\n".join(
        f"- {item}" for item in spec.get("result_requirements", ())
    )
    return (
        f"# {spec['title']}\n\n"
        f"{_source_banner(spec)}\n\n"
        f"## Scenario\n\n{spec['scenario']}\n\n"
        f"## Your task\n\n{spec['task']}\n\n"
        f"## Result requirements\n\n{requirements}\n\n"
        f"## Skill focus\n\n**{spec['concept']}**\n\n"
        f"{spec['learning_objective']}\n"
    )


def starter_sql(root: Path, number: int) -> str:
    del root
    spec = _exercise(number)
    return (
        f"-- SQL Challenge {_display_number(number):02d}: {spec['title']}\n"
        "-- Write one query that returns the requested result.\n\n"
    )


def validation_markdown(root: Path, number: int) -> str:
    del root
    spec = _exercise(number)
    columns = ", ".join(str(value) for value in spec.get("expected_columns", ()))
    return (
        f"# Validation — SQL Challenge {_display_number(number):02d}\n\n"
        f"- Expected columns: {columns}\n"
        f"- Expected rows: {int(spec.get('expected_row_count', 0))}\n"
        f"- Ordering checked: {'Yes' if spec.get('order_matters') else 'No'}\n"
    )


def _ensure_reference_files(root: Path, number: int) -> dict[str, Path]:
    paths = exercise_paths(root, number)
    paths["exercise_dir"].mkdir(parents=True, exist_ok=True)
    paths["datasets"].mkdir(parents=True, exist_ok=True)
    paths["submissions"].mkdir(parents=True, exist_ok=True)
    paths["instructions"].write_text(
        instructions_markdown(root, number), encoding="utf-8", newline="\n"
    )
    paths["starter"].write_text(
        starter_sql(root, number), encoding="utf-8", newline="\n"
    )
    paths["validation"].write_text(
        validation_markdown(root, number), encoding="utf-8", newline="\n"
    )
    for table in _dataset_tables(number):
        path = paths["datasets"] / f"{table['name']}.json"
        path.write_text(
            json.dumps(table, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return paths


def question_definitions(root: Path, number: int) -> list[QuestionBlock]:
    del root
    spec = _exercise(number)
    hints = tuple(str(value) for value in spec.get("hints", ()))
    return [
        QuestionBlock(
            number=1,
            prompt=str(spec["task"]),
            sql="",
            requirements=tuple(
                str(item) for item in spec.get("result_requirements", ())
            ),
            hints=hints,
        )
    ]


def question_answers(root: Path, number: int) -> dict[int, str]:
    _ensure_reference_files(Path(root), int(number))
    path = exercise_paths(root, number)["submission"]
    if not path.is_file():
        return {1: ""}
    try:
        return {1: path.read_text(encoding="utf-8-sig").strip()}
    except OSError as exc:
        raise DuckDBExerciseRunnerError(
            f"The saved SQL submission could not be read: {exc}"
        ) from exc


def compose_submission(root: Path, number: int, answers: dict[int, str]) -> str:
    del root, number
    return str(answers.get(1, "") or "").strip()


def submission_sql(root: Path, number: int) -> str:
    return question_answers(root, number).get(1, "")


def save_submission(root: Path, number: int, sql: str) -> Path:
    roadmap_mastery.assert_duckdb_ready_from_root(root, number)
    paths = _ensure_reference_files(Path(root), int(number))
    text = str(sql or "").rstrip()
    if text:
        text += "\n"
    paths["submission"].write_text(text, encoding="utf-8", newline="\n")
    return paths["submission"]


def dataset_inventory(root: Path, number: int) -> list[dict[str, Any]]:
    del root
    inventory: list[dict[str, Any]] = []
    for table in _dataset_tables(number):
        columns = list(table.get("columns") or [])
        inventory.append(
            {
                "table": str(table["name"]),
                "prefixed_table": str(table["name"]),
                "columns": [str(column["name"]) for column in columns],
                "column_types": [str(column["type"]) for column in columns],
                "rows": list(table.get("rows") or []),
                "row_count": len(table.get("rows") or []),
                "grain": str(table.get("grain") or ""),
            }
        )
    return inventory


def task_contract(root: Path, number: int, question_number: int) -> dict[str, Any]:
    del root
    if int(question_number) != 1:
        return {}
    spec = _exercise(number)
    return {
        "prompt": spec["task"],
        "requirements": list(spec.get("result_requirements") or []),
        "hints": list(spec.get("hints") or []),
    }


def task_requirements(root: Path, number: int, question_number: int) -> tuple[str, ...]:
    return tuple(
        str(value)
        for value in task_contract(root, number, question_number).get(
            "requirements", ()
        )
    )


def task_hints(root: Path, number: int, question_number: int) -> tuple[str, ...]:
    return tuple(
        str(value)
        for value in task_contract(root, number, question_number).get("hints", ())
    )


def task_hint(root: Path, number: int, question_number: int, level: int = 0) -> str:
    hints = task_hints(root, number, question_number)
    if not hints:
        return (
            "Review the requested columns, filters, calculations, grouping, and "
            "sorting one requirement at a time."
        )
    return hints[min(max(int(level), 0), len(hints) - 1)]


def _split_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False
    index = 0
    while index < len(sql):
        char = sql[index]
        nxt = sql[index + 1] if index + 1 < len(sql) else ""
        if in_line_comment:
            current.append(char)
            if char == "\n":
                in_line_comment = False
            index += 1
            continue
        if in_block_comment:
            current.append(char)
            if char == "*" and nxt == "/":
                current.append(nxt)
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue
        if not in_single and not in_double and char == "-" and nxt == "-":
            current.extend([char, nxt])
            in_line_comment = True
            index += 2
            continue
        if not in_single and not in_double and char == "/" and nxt == "*":
            current.extend([char, nxt])
            in_block_comment = True
            index += 2
            continue
        if char == "'" and not in_double:
            if in_single and nxt == "'":
                current.extend([char, nxt])
                index += 2
                continue
            in_single = not in_single
        elif char == '"' and not in_single:
            if in_double and nxt == '"':
                current.extend([char, nxt])
                index += 2
                continue
            in_double = not in_double
        if char == ";" and not in_single and not in_double:
            text = "".join(current).strip()
            if text:
                statements.append(text)
            current = []
        else:
            current.append(char)
        index += 1
    text = "".join(current).strip()
    if text:
        statements.append(text)
    return statements


def _without_comments(sql: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", str(sql or ""), flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", text).strip()


def _validate_sql(spec: dict[str, Any], sql: str) -> list[str]:
    executable = _without_comments(sql)
    if not executable:
        raise DuckDBExerciseRunnerError("Write a SQL query before running this task.")
    if _BLOCKED_SQL.search(executable):
        raise DuckDBExerciseRunnerError(
            "This exercise only allows SQL against its bundled in-memory tables. "
            "File access, database attachment, extensions, and external commands are disabled."
        )
    statements = _split_statements(executable)
    if not statements:
        raise DuckDBExerciseRunnerError("Write a SQL query before running this task.")
    if len(statements) > 1 and not bool(spec.get("allow_multi_statement")):
        raise DuckDBExerciseRunnerError("This challenge expects one SQL statement.")
    for statement in statements:
        if _QUERY_START.match(statement) or _ALLOWED_TEMP_VIEW.match(statement):
            continue
        raise DuckDBExerciseRunnerError(
            "Only SELECT/WITH queries are allowed. A temporary view is allowed only "
            "when the task explicitly requests one."
        )
    if not _QUERY_START.match(statements[-1]):
        raise DuckDBExerciseRunnerError(
            "The final statement must return the result requested by the task."
        )
    return statements


def _connection(number: int):
    if duckdb is None:
        raise DuckDBExerciseRunnerError(
            "DuckDB is not installed in the active Career Accelerator environment. "
            "Restart through the launcher so requirements can be repaired."
        )
    connection = duckdb.connect(database=":memory:")
    for table in _dataset_tables(number):
        columns = list(table.get("columns") or [])
        column_sql = ", ".join(
            f'"{str(column["name"]).replace(chr(34), chr(34) * 2)}" {column["type"]}'
            for column in columns
        )
        name = str(table["name"]).replace('"', '""')
        connection.execute(f'CREATE TABLE "{name}" ({column_sql})')
        rows = list(table.get("rows") or [])
        if rows:
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f'INSERT INTO "{name}" VALUES ({placeholders})', rows
            )
    return connection


def _execute(number: int, sql: str) -> dict[str, Any]:
    spec = _exercise(number)
    statements = _validate_sql(spec, sql)
    connection = _connection(number)
    try:
        cursor = None
        for statement in statements:
            cursor = connection.execute(statement)
        if cursor is None or cursor.description is None:
            raise DuckDBExerciseRunnerError(
                "The final SQL statement did not return a result table."
            )
        columns = [str(item[0]) for item in cursor.description]
        all_rows = cursor.fetchall()
        limit = 250
        return {
            "last_result": {
                "columns": columns,
                "rows": all_rows[:limit],
                "all_rows": all_rows,
                "truncated": len(all_rows) > limit,
            }
        }
    except DuckDBExerciseRunnerError:
        raise
    except Exception as exc:
        raise DuckDBExerciseRunnerError(str(exc)) from exc
    finally:
        connection.close()


def run_question(root: Path, number: int, full_sql: str, question_number: int) -> dict[str, Any]:
    del root
    if int(question_number) != 1:
        raise DuckDBExerciseRunnerError("This compact exercise contains one task.")
    return _execute(number, full_sql)


def _normal_cell(value: Any) -> Any:
    if isinstance(value, Decimal):
        return round(float(value), 8)
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _normal_rows(rows: Iterable[Iterable[Any]]) -> list[tuple[Any, ...]]:
    return [tuple(_normal_cell(value) for value in row) for row in rows]


def _sort_key(row: tuple[Any, ...]) -> tuple[str, ...]:
    return tuple("<NULL>" if value is None else repr(value) for value in row)


def _reference(number: int) -> dict[str, Any]:
    return _execute(number, str(_exercise(number)["solution_sql"]))


def _pattern_check(spec: dict[str, Any], sql: str) -> tuple[bool, str]:
    missing: list[str] = []
    for pattern in spec.get("required_patterns") or []:
        if re.search(str(pattern), sql, flags=re.IGNORECASE | re.DOTALL) is None:
            missing.append(str(pattern))
    if not missing:
        return True, f"The query uses the SQL technique required for {spec['concept']}."
    return (
        False,
        f"The result may be close, but the query does not yet demonstrate "
        f"{spec['concept']}, which is the concept this exercise checks.",
    )


def _diagnostic_hint(
    spec: dict[str, Any], *, columns_ok: bool, row_count_ok: bool,
    values_ok: bool, pattern_ok: bool
) -> str:
    hints = [str(value) for value in spec.get("hints") or []]
    if not columns_ok:
        return (
            "Match the exact requested column names and order. Check every alias "
            "listed under Result requirements."
        )
    if not row_count_ok:
        return hints[0] if hints else (
            "The query includes too many or too few rows. Recheck the requested "
            "filters, join type, grouping grain, and HAVING condition."
        )
    if not values_ok:
        return hints[1] if len(hints) > 1 else (
            "The correct rows are present, but at least one value differs. Recheck "
            "the calculation, aggregation, NULL handling, and final sort order."
        )
    if not pattern_ok:
        return hints[-1] if hints else (
            f"Rewrite the query so it explicitly practices {spec['concept']}."
        )
    return "Review each result requirement one at a time."


def _check(number: int, sql: str) -> dict[str, Any]:
    spec = _exercise(number)
    run = _execute(number, sql)
    expected = _reference(number)
    actual_result = run["last_result"]
    expected_result = expected["last_result"]

    actual_columns = list(actual_result["columns"])
    expected_columns = list(
        spec.get("expected_columns") or expected_result["columns"]
    )
    columns_ok = actual_columns == expected_columns

    actual_rows = _normal_rows(actual_result["all_rows"])
    expected_rows = _normal_rows(expected_result["all_rows"])
    row_count_ok = len(actual_rows) == len(expected_rows)
    values_ok = (
        actual_rows == expected_rows
        if bool(spec.get("order_matters"))
        else sorted(actual_rows, key=_sort_key) == sorted(expected_rows, key=_sort_key)
    )
    pattern_ok, pattern_detail = _pattern_check(spec, sql)

    checklist = [
        {
            "label": "Query",
            "passed": True,
            "detail": "The SQL ran successfully against the exercise dataset.",
        },
        {"label": "Required SQL", "passed": pattern_ok, "detail": pattern_detail},
        {
            "label": "Columns",
            "passed": columns_ok,
            "detail": (
                f"Returned the required columns in order: {', '.join(expected_columns)}."
                if columns_ok
                else f"Expected {expected_columns}, but received {actual_columns}."
            ),
        },
        {
            "label": "Row count",
            "passed": row_count_ok,
            "detail": (
                f"Returned the expected {len(expected_rows)} row(s)."
                if row_count_ok
                else f"Expected {len(expected_rows)} row(s), but received {len(actual_rows)}."
            ),
        },
        {
            "label": "Values and order" if spec.get("order_matters") else "Values",
            "passed": values_ok,
            "detail": (
                "The values and required ordering match the challenge."
                if values_ok
                else (
                    "At least one value or row position differs from the requested result. "
                    "The feedback hint below points to the most likely part to review."
                )
            ),
        },
    ]
    passed = all(bool(item["passed"]) for item in checklist)
    return {
        "passed": passed,
        "checklist": checklist,
        "run": run,
        "hint": None if passed else _diagnostic_hint(
            spec,
            columns_ok=columns_ok,
            row_count_ok=row_count_ok,
            values_ok=values_ok,
            pattern_ok=pattern_ok,
        ),
    }


def check_question(root: Path, number: int, full_sql: str, question_number: int) -> dict[str, Any]:
    del root
    if int(question_number) != 1:
        raise DuckDBExerciseRunnerError("This compact exercise contains one task.")
    return _check(number, full_sql)


def check_exercise(
    root: Path,
    number: int,
    full_sql: str,
    question_numbers: list[int] | None = None,
) -> dict[str, Any]:
    requested = [int(value) for value in (question_numbers or [1])]
    if requested != [1]:
        requested = [value for value in requested if value == 1]
    if not requested:
        return {"passed": False, "questions": [], "passed_count": 0, "total_count": 1}
    result = _check(number, full_sql)
    question = question_definitions(root, number)[0]
    return {
        "passed": bool(result["passed"]),
        "questions": [{"question": question, **result}],
        "passed_count": int(bool(result["passed"])),
        "total_count": 1,
    }
