from __future__ import annotations

import csv
import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1
PACK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
READ_ONLY_SQL_RE = re.compile(r"^\s*(?:SELECT|WITH)\b", re.IGNORECASE | re.DOTALL)
DISALLOWED_SQL_RE = re.compile(
    r"\b(?:ATTACH|DETACH|COPY|INSTALL|LOAD|EXPORT|IMPORT|PRAGMA|CALL|CREATE|DROP|"
    r"ALTER|UPDATE|DELETE|INSERT|REPLACE|VACUUM|REINDEX|ANALYZE|TRUNCATE)\b",
    re.IGNORECASE,
)
MAX_PACK_FILES = 250
MAX_PACK_BYTES = 30 * 1024 * 1024
VALID_STATUSES = ("Not Started", "In Progress", "Completed")


class ExercisePackError(ValueError):
    """Raised when an exercise pack is invalid or cannot be used safely."""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def installed_root(root: Path) -> Path:
    path = Path(root) / "exercise_packs" / "installed"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundled_root(root: Path) -> Path:
    return Path(root) / "exercise_packs" / "bundled"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_pack_progress (
            pack_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Not Started',
            answer_sql TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            hint_index INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT,
            completed_at TEXT,
            PRIMARY KEY (pack_id, exercise_id)
        )
        """
    )
    progress_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(exercise_pack_progress)").fetchall()
    }
    if "hint_index" not in progress_columns:
        conn.execute(
            "ALTER TABLE exercise_pack_progress ADD COLUMN hint_index INTEGER NOT NULL DEFAULT 0"
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_concept_tags (
            task_id INTEGER NOT NULL,
            concept TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence INTEGER NOT NULL DEFAULT 100,
            updated_at TEXT,
            PRIMARY KEY (task_id, concept)
        )
        """
    )
    conn.commit()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ExercisePackError(f"Required file is missing: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ExercisePackError(
            f"{path.name} is not valid JSON: line {exc.lineno}, column {exc.colno}."
        ) from exc


def _safe_relative(base: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ExercisePackError("A referenced file path is empty.")
    candidate = (base / relative).resolve()
    resolved_base = base.resolve()
    try:
        candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise ExercisePackError(f"Unsafe file path in pack: {relative}") from exc
    if must_exist and not candidate.exists():
        raise ExercisePackError(f"Referenced file does not exist: {relative}")
    if must_exist and not candidate.is_file():
        raise ExercisePackError(f"Referenced path is not a file: {relative}")
    return candidate


def _normalize_entry(entry: Any, entry_type: str) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ExercisePackError(f"Every {entry_type} entry must be an object.")
    for field in ("id", "title", "file"):
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            raise ExercisePackError(f"Every {entry_type} needs a non-empty '{field}'.")
    if not PACK_ID_RE.match(entry["id"]):
        raise ExercisePackError(
            f"Invalid {entry_type} id '{entry['id']}'. Use lowercase words and hyphens."
        )
    return dict(entry)


def validate_pack(pack_dir: Path) -> dict[str, Any]:
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "manifest.json"
    manifest = _read_json(manifest_path)

    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ExercisePackError(
            f"Unsupported schema_version {manifest.get('schema_version')!r}; "
            f"this app supports schema version {SCHEMA_VERSION}."
        )

    pack_id = manifest.get("pack_id")
    if not isinstance(pack_id, str) or not PACK_ID_RE.match(pack_id):
        raise ExercisePackError(
            "manifest.json needs a lowercase, hyphenated pack_id such as "
            "'sql-subqueries-foundations'."
        )

    for field in ("title", "version", "description"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ExercisePackError(f"manifest.json needs a non-empty '{field}'.")

    concepts = manifest.get("concepts", [])
    if not isinstance(concepts, list) or not all(
        isinstance(item, str) and item.strip() for item in concepts
    ):
        raise ExercisePackError("manifest.json 'concepts' must be a list of strings.")

    lessons = [_normalize_entry(item, "lesson") for item in manifest.get("lessons", [])]
    exercises = [
        _normalize_entry(item, "exercise") for item in manifest.get("exercises", [])
    ]
    if not exercises:
        raise ExercisePackError("An exercise pack must contain at least one exercise.")

    ids = [item["id"] for item in lessons + exercises]
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ExercisePackError(
            "Lesson and exercise ids must be unique. Duplicate ids: "
            + ", ".join(sorted(duplicates))
        )

    for entry in lessons + exercises:
        _safe_relative(pack_dir, entry["file"])

    lesson_ids = {item["id"] for item in lessons}
    associated_entries = [item for item in exercises if item.get("lesson_id")]
    if associated_entries:
        missing_associations = [item["id"] for item in exercises if not item.get("lesson_id")]
        if missing_associations:
            raise ExercisePackError(
                "When lesson-linked questions are used, every exercise needs a lesson_id. "
                "Missing: " + ", ".join(missing_associations)
            )
        invalid_associations = [
            item["id"] for item in exercises if item.get("lesson_id") not in lesson_ids
        ]
        if invalid_associations:
            raise ExercisePackError(
                "Exercises reference an unknown lesson_id: "
                + ", ".join(invalid_associations)
            )
        uncovered_lessons = [
            item["id"] for item in lessons
            if not any(exercise.get("lesson_id") == item["id"] for exercise in exercises)
        ]
        if uncovered_lessons:
            raise ExercisePackError(
                "Every lesson must include at least one practice question. Missing: "
                + ", ".join(uncovered_lessons)
            )
        question_keys: set[tuple[str, int]] = set()
        for item in exercises:
            number = item.get("question_number")
            if isinstance(number, bool) or not isinstance(number, int) or number < 1:
                raise ExercisePackError(
                    f"Lesson-linked exercise {item['id']} needs a positive integer question_number."
                )
            key = (item["lesson_id"], number)
            if key in question_keys:
                raise ExercisePackError(
                    f"Duplicate question_number {number} for lesson {item['lesson_id']}."
                )
            question_keys.add(key)
            show_starter = item.get("show_starter_sql", True)
            if not isinstance(show_starter, bool):
                raise ExercisePackError(
                    f"Exercise {item['id']} show_starter_sql must be true or false."
                )

    for entry in exercises:
        exercise = _read_json(_safe_relative(pack_dir, entry["file"]))
        if exercise.get("id") != entry["id"]:
            raise ExercisePackError(
                f"Exercise id mismatch for {entry['file']}: expected {entry['id']!r}."
            )
        for association_field in ("lesson_id", "question_number", "show_starter_sql"):
            if association_field in entry and association_field in exercise:
                if exercise[association_field] != entry[association_field]:
                    raise ExercisePackError(
                        f"Exercise {entry['id']} {association_field} disagrees with manifest.json."
                    )
        for field in ("title", "prompt", "starter_sql", "solution_file"):
            if not isinstance(exercise.get(field), str):
                raise ExercisePackError(
                    f"Exercise {entry['id']} needs a string '{field}'."
                )
        for field in (
            "stage",
            "difficulty",
            "learning_objective",
            "recommended_lesson",
            "why",
            "expected_result",
            "explanation",
            "stretch_goal",
            "solution_explanation",
        ):
            value = exercise.get(field)
            if value is not None and not isinstance(value, str):
                raise ExercisePackError(
                    f"Exercise {entry['id']} optional field '{field}' must be a string."
                )
        for field in (
            "concepts",
            "build_steps",
            "common_mistakes",
            "hints",
            "takeaways",
            "reflection_questions",
            "solution_walkthrough",
        ):
            value = exercise.get(field, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                raise ExercisePackError(
                    f"Exercise {entry['id']} optional field '{field}' "
                    "must be a list of non-empty strings."
                )
        _safe_relative(pack_dir, exercise["solution_file"])
        datasets = exercise.get("datasets", [])
        if not isinstance(datasets, list) or not datasets:
            raise ExercisePackError(
                f"Exercise {entry['id']} must list at least one dataset."
            )
        for dataset in datasets:
            if not isinstance(dataset, dict):
                raise ExercisePackError(
                    f"Exercise {entry['id']} has an invalid dataset entry."
                )
            table = dataset.get("table")
            file_name = dataset.get("file")
            if not isinstance(table, str) or not IDENTIFIER_RE.match(table):
                raise ExercisePackError(
                    f"Exercise {entry['id']} has an invalid table name: {table!r}."
                )
            _safe_relative(pack_dir, file_name)

        validation = exercise.get("validation", {})
        if validation is not None and not isinstance(validation, dict):
            raise ExercisePackError(
                f"Exercise {entry['id']} has an invalid validation object."
            )
        for keyword_field in (
            "required_keywords",
            "required_any_keywords",
            "forbidden_keywords",
        ):
            keywords = (validation or {}).get(keyword_field, [])
            if not isinstance(keywords, list) or not all(
                isinstance(item, str) and item.strip() for item in keywords
            ):
                raise ExercisePackError(
                    f"Exercise {entry['id']} validation '{keyword_field}' "
                    "must be a list of non-empty strings."
                )
        min_select_count = (validation or {}).get("min_select_count", 1)
        if not isinstance(min_select_count, int) or min_select_count < 1:
            raise ExercisePackError(
                f"Exercise {entry['id']} validation 'min_select_count' "
                "must be an integer of at least 1."
            )

    total_files = 0
    total_bytes = 0
    for path in pack_dir.rglob("*"):
        if path.is_symlink():
            raise ExercisePackError("Exercise packs may not contain symbolic links.")
        if path.is_file():
            total_files += 1
            total_bytes += path.stat().st_size
    if total_files > MAX_PACK_FILES:
        raise ExercisePackError(
            f"Pack contains {total_files} files; the maximum is {MAX_PACK_FILES}."
        )
    if total_bytes > MAX_PACK_BYTES:
        raise ExercisePackError(
            f"Pack is larger than the {MAX_PACK_BYTES // (1024 * 1024)} MB limit."
        )

    normalized = dict(manifest)
    normalized["lessons"] = lessons
    normalized["exercises"] = exercises
    normalized["path"] = str(pack_dir)
    return normalized


def _manifest_directory(extracted_root: Path) -> Path:
    if (extracted_root / "manifest.json").is_file():
        return extracted_root
    candidates = [
        path.parent for path in extracted_root.rglob("manifest.json") if path.is_file()
    ]
    candidates = sorted(set(candidates))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ExercisePackError("No manifest.json was found in the selected pack.")
    raise ExercisePackError(
        "The archive contains multiple manifests. Select a zip containing one pack."
    )


def _extract_zip_safely(source: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(source) as archive:
            members = archive.infolist()
            if len(members) > MAX_PACK_FILES:
                raise ExercisePackError(
                    f"Archive contains too many files ({len(members)})."
                )
            declared_size = sum(member.file_size for member in members)
            if declared_size > MAX_PACK_BYTES:
                raise ExercisePackError("Archive is larger than the allowed pack size.")
            for member in members:
                name = member.filename.replace("\\", "/")
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ExercisePackError(f"Unsafe archive path: {member.filename}")
                target = (destination / name).resolve()
                try:
                    target.relative_to(destination.resolve())
                except ValueError as exc:
                    raise ExercisePackError(
                        f"Unsafe archive path: {member.filename}"
                    ) from exc
            archive.extractall(destination)
    except zipfile.BadZipFile as exc:
        raise ExercisePackError("The selected file is not a valid zip archive.") from exc


def install_pack(
    source: Path,
    root: Path,
    conn: sqlite3.Connection,
    *,
    allow_update: bool = True,
) -> dict[str, Any]:
    """Validate and install a folder or zip pack into exercise_packs/installed."""
    ensure_schema(conn)
    source = Path(source).expanduser().resolve()
    if not source.exists():
        raise ExercisePackError(f"Selected pack does not exist: {source}")

    with tempfile.TemporaryDirectory(prefix="career-exercise-pack-") as temp_name:
        temp_root = Path(temp_name)
        if source.is_dir():
            staged_root = temp_root / "pack"
            shutil.copytree(source, staged_root)
        elif source.suffix.lower() == ".zip":
            staged_root = temp_root / "extracted"
            staged_root.mkdir()
            _extract_zip_safely(source, staged_root)
        else:
            raise ExercisePackError("Select an exercise pack folder or a .zip file.")

        pack_dir = _manifest_directory(staged_root)
        manifest = validate_pack(pack_dir)
        destination = installed_root(root) / manifest["pack_id"]
        if destination.exists() and not allow_update:
            raise ExercisePackError(
                f"{manifest['title']} is already installed."
            )
        replacement = destination.with_name(destination.name + ".installing")
        if replacement.exists():
            shutil.rmtree(replacement)
        shutil.copytree(pack_dir, replacement)
        if destination.exists():
            shutil.rmtree(destination)
        replacement.replace(destination)

    return validate_pack(destination)


def _version_key(version: Any) -> tuple[int, ...]:
    numbers = [int(item) for item in re.findall(r"\d+", str(version or ""))]
    return tuple(numbers or [0])


def ensure_bundled_packs(root: Path, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Install or update packs shipped with the application."""
    installed: list[dict[str, Any]] = []
    source_root = bundled_root(root)
    if not source_root.exists():
        return installed
    for candidate in sorted(source_root.iterdir()):
        if not candidate.is_dir() or not (candidate / "manifest.json").exists():
            continue
        bundled_manifest = validate_pack(candidate)
        destination = installed_root(root) / bundled_manifest["pack_id"]
        needs_install = True
        if destination.exists():
            try:
                current = validate_pack(destination)
                needs_install = _version_key(bundled_manifest.get("version")) > _version_key(
                    current.get("version")
                )
            except ExercisePackError:
                needs_install = True
        if needs_install:
            installed.append(install_pack(candidate, root, conn, allow_update=True))
    return installed


def list_installed_packs(root: Path, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_schema(conn)
    ensure_bundled_packs(root, conn)
    packs: list[dict[str, Any]] = []
    for candidate in sorted(installed_root(root).iterdir()):
        if not candidate.is_dir() or not (candidate / "manifest.json").exists():
            continue
        try:
            manifest = validate_pack(candidate)
        except ExercisePackError:
            continue
        progress = progress_summary(conn, manifest["pack_id"], manifest)
        manifest["progress"] = progress
        packs.append(manifest)
    return packs


def get_pack(root: Path, conn: sqlite3.Connection, pack_id: str) -> dict[str, Any]:
    ensure_schema(conn)
    pack_dir = installed_root(root) / pack_id
    if not pack_dir.exists():
        raise ExercisePackError(f"Exercise pack is not installed: {pack_id}")
    manifest = validate_pack(pack_dir)
    manifest["progress"] = progress_summary(conn, pack_id, manifest)
    return manifest


def load_lesson(pack: dict[str, Any], lesson_id: str) -> str:
    entry = next(
        (item for item in pack.get("lessons", []) if item["id"] == lesson_id), None
    )
    if entry is None:
        raise ExercisePackError(f"Lesson was not found: {lesson_id}")
    return _safe_relative(Path(pack["path"]), entry["file"]).read_text(encoding="utf-8")


def load_exercise(pack: dict[str, Any], exercise_id: str) -> dict[str, Any]:
    entry = next(
        (item for item in pack.get("exercises", []) if item["id"] == exercise_id), None
    )
    if entry is None:
        raise ExercisePackError(f"Exercise was not found: {exercise_id}")
    exercise = _read_json(_safe_relative(Path(pack["path"]), entry["file"]))
    for field in ("lesson_id", "question_number", "show_starter_sql"):
        if field in entry and field not in exercise:
            exercise[field] = entry[field]
    exercise["pack_id"] = pack["pack_id"]
    exercise["pack_path"] = pack["path"]
    return exercise


def describe_datasets(exercise: dict[str, Any]) -> list[dict[str, Any]]:
    """Return safe, learner-facing table schemas and row counts for an exercise."""
    summaries: list[dict[str, Any]] = []
    pack_path = Path(exercise["pack_path"])
    for dataset in exercise.get("datasets", []):
        csv_path = _safe_relative(pack_path, dataset["file"])
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                columns = [item.strip() for item in next(reader)]
            except StopIteration:
                columns = []
                row_count = 0
            else:
                row_count = sum(1 for _ in reader)
        summaries.append(
            {
                "table": dataset["table"],
                "columns": columns,
                "row_count": row_count,
            }
        )
    return summaries


def progress_for(
    conn: sqlite3.Connection, pack_id: str, exercise_id: str
) -> dict[str, Any]:
    ensure_schema(conn)
    row = conn.execute(
        """
        SELECT status,answer_sql,notes,hint_index,updated_at,completed_at
        FROM exercise_pack_progress
        WHERE pack_id=? AND exercise_id=?
        """,
        (pack_id, exercise_id),
    ).fetchone()
    if row is None:
        return {
            "status": "Not Started",
            "answer_sql": "",
            "notes": "",
            "hint_index": 0,
            "updated_at": None,
            "completed_at": None,
        }
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return {
        "status": row[0],
        "answer_sql": row[1],
        "notes": row[2],
        "hint_index": row[3],
        "updated_at": row[4],
        "completed_at": row[5],
    }


def save_progress(
    conn: sqlite3.Connection,
    pack_id: str,
    exercise_id: str,
    *,
    status: str,
    answer_sql: str = "",
    notes: str = "",
    hint_index: int | None = None,
) -> None:
    ensure_schema(conn)
    if status not in VALID_STATUSES:
        raise ExercisePackError(f"Unknown exercise status: {status}")
    existing = progress_for(conn, pack_id, exercise_id)
    completed_at = existing.get("completed_at")
    resolved_hint_index = (
        int(existing.get("hint_index", 0) or 0)
        if hint_index is None
        else max(0, int(hint_index))
    )
    if status == "Completed" and not completed_at:
        completed_at = _now()
    elif status != "Completed":
        completed_at = None
    conn.execute(
        """
        INSERT INTO exercise_pack_progress(
            pack_id,exercise_id,status,answer_sql,notes,hint_index,updated_at,completed_at
        ) VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(pack_id,exercise_id) DO UPDATE SET
            status=excluded.status,
            answer_sql=excluded.answer_sql,
            notes=excluded.notes,
            hint_index=excluded.hint_index,
            updated_at=excluded.updated_at,
            completed_at=excluded.completed_at
        """,
        (
            pack_id,
            exercise_id,
            status,
            answer_sql,
            notes,
            resolved_hint_index,
            _now(),
            completed_at,
        ),
    )
    conn.commit()


def progress_summary(
    conn: sqlite3.Connection, pack_id: str, manifest: dict[str, Any]
) -> dict[str, Any]:
    ensure_schema(conn)
    exercise_ids = [item["id"] for item in manifest.get("exercises", [])]
    if not exercise_ids:
        return {"completed": 0, "total": 0, "percent": 0, "next_id": None}
    placeholders = ",".join("?" for _ in exercise_ids)
    rows = conn.execute(
        f"""
        SELECT exercise_id,status
        FROM exercise_pack_progress
        WHERE pack_id=? AND exercise_id IN ({placeholders})
        """,
        (pack_id, *exercise_ids),
    ).fetchall()
    status_by_id = {
        (row["exercise_id"] if isinstance(row, sqlite3.Row) else row[0]):
        (row["status"] if isinstance(row, sqlite3.Row) else row[1])
        for row in rows
    }
    completed = sum(status_by_id.get(item) == "Completed" for item in exercise_ids)
    next_id = next(
        (item for item in exercise_ids if status_by_id.get(item) != "Completed"), None
    )
    return {
        "completed": completed,
        "total": len(exercise_ids),
        "percent": round(completed / len(exercise_ids) * 100),
        "next_id": next_id,
    }


def _infer_column(values: list[str]) -> str:
    non_empty = [value for value in values if value not in ("", None)]
    if not non_empty:
        return "TEXT"
    try:
        for value in non_empty:
            int(value)
        return "INTEGER"
    except (TypeError, ValueError):
        pass
    try:
        for value in non_empty:
            float(value)
        return "REAL"
    except (TypeError, ValueError):
        return "TEXT"


def _coerce(value: str, sql_type: str) -> Any:
    if value == "":
        return None
    if sql_type == "INTEGER":
        return int(value)
    if sql_type == "REAL":
        return float(value)
    return value


def _quote_identifier(identifier: str) -> str:
    if not IDENTIFIER_RE.match(identifier):
        raise ExercisePackError(f"Unsafe SQL identifier: {identifier!r}")
    return f'"{identifier}"'


def _load_dataset(
    conn: sqlite3.Connection, pack_path: Path, dataset: dict[str, Any]
) -> None:
    table = dataset["table"]
    csv_path = _safe_relative(pack_path, dataset["file"])
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ExercisePackError(f"Dataset has no header row: {dataset['file']}")
        fields = [field.strip() for field in reader.fieldnames]
        if not all(IDENTIFIER_RE.match(field) for field in fields):
            raise ExercisePackError(
                f"Dataset columns must use letters, numbers, and underscores: {dataset['file']}"
            )
        records = list(reader)
    columns = {
        field: _infer_column([record.get(field, "") for record in records])
        for field in fields
    }
    definitions = ", ".join(
        f"{_quote_identifier(field)} {columns[field]}" for field in fields
    )
    conn.execute(f"CREATE TABLE {_quote_identifier(table)} ({definitions})")
    if records:
        placeholders = ",".join("?" for _ in fields)
        values = [
            tuple(_coerce(record.get(field, ""), columns[field]) for field in fields)
            for record in records
        ]
        conn.executemany(
            f"INSERT INTO {_quote_identifier(table)} VALUES ({placeholders})", values
        )


def _sql_validation_view(sql: str) -> str:
    """Remove comments and string contents before safety keyword checks."""
    output: list[str] = []
    index = 0
    state = "normal"
    while index < len(sql):
        char = sql[index]
        nxt = sql[index + 1] if index + 1 < len(sql) else ""
        if state == "normal":
            if char == "-" and nxt == "-":
                output.extend("  ")
                index += 2
                state = "line_comment"
                continue
            if char == "/" and nxt == "*":
                output.extend("  ")
                index += 2
                state = "block_comment"
                continue
            if char == "'":
                output.append(" ")
                index += 1
                state = "single_quote"
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
            if char == "*" and nxt == "/":
                output.extend("  ")
                index += 2
                state = "normal"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if state == "single_quote":
            if char == "'" and nxt == "'":
                output.extend("  ")
                index += 2
            elif char == "'":
                output.append(" ")
                index += 1
                state = "normal"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
    return "".join(output)


def _validate_read_only_sql(sql: str) -> str:
    cleaned = sql.strip()
    if not cleaned:
        raise ExercisePackError("Enter a SQL query first.")
    validation_view = _sql_validation_view(cleaned).strip()
    if not READ_ONLY_SQL_RE.match(validation_view):
        raise ExercisePackError("Exercises only allow SELECT or WITH queries.")
    if DISALLOWED_SQL_RE.search(validation_view):
        raise ExercisePackError("This query contains a statement not allowed in exercises.")
    # Allow a single trailing semicolon, but not multiple statements. Semicolons
    # inside comments or quoted values have already been removed from this view.
    without_trailing = (
        validation_view[:-1] if validation_view.endswith(";") else validation_view
    )
    if ";" in without_trailing:
        raise ExercisePackError("Run one SQL statement at a time.")
    return cleaned


def execute_query(exercise: dict[str, Any], sql: str) -> dict[str, Any]:
    sql = _validate_read_only_sql(sql)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        pack_path = Path(exercise["pack_path"])
        for dataset in exercise["datasets"]:
            _load_dataset(conn, pack_path, dataset)
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        rows = [tuple(row) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows}
    except sqlite3.Error as exc:
        raise ExercisePackError(f"SQL error: {exc}") from exc
    finally:
        conn.close()


def _normalized_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    return value


def _normalized_rows(rows: Iterable[Iterable[Any]], ordered: bool) -> list[tuple[Any, ...]]:
    normalized = [tuple(_normalized_value(value) for value in row) for row in rows]
    if not ordered:
        normalized.sort(key=lambda row: tuple("" if value is None else repr(value) for value in row))
    return normalized


def _keyword_present(validation_view: str, keyword: str) -> bool:
    """Match SQL keywords while allowing flexible whitespace between words."""
    parts = [item for item in re.split(r"\s+", keyword.strip()) if item]
    if not parts:
        return False
    pattern = r"\b" + r"\s+".join(re.escape(item) for item in parts) + r"\b"
    return bool(re.search(pattern, validation_view, re.IGNORECASE))


def _select_count(validation_view: str) -> int:
    return len(re.findall(r"\bselect\b", validation_view, re.IGNORECASE))


def check_answer(exercise: dict[str, Any], user_sql: str) -> dict[str, Any]:
    user_result = execute_query(exercise, user_sql)
    solution_path = _safe_relative(
        Path(exercise["pack_path"]), exercise["solution_file"]
    )
    solution_sql = solution_path.read_text(encoding="utf-8")
    solution_result = execute_query(exercise, solution_sql)
    validation = exercise.get("validation", {})
    ordered = bool(validation.get("ordered", False))
    columns_match = [item.lower() for item in user_result["columns"]] == [
        item.lower() for item in solution_result["columns"]
    ]
    rows_match = _normalized_rows(user_result["rows"], ordered) == _normalized_rows(
        solution_result["rows"], ordered
    )

    validation_view = _sql_validation_view(user_sql)
    required_keywords = validation.get("required_keywords", [])
    required_any = validation.get("required_any_keywords", [])
    forbidden_keywords = validation.get("forbidden_keywords", [])
    minimum_selects = int(validation.get("min_select_count", 1) or 1)
    actual_selects = _select_count(validation_view)
    missing_keywords = [
        keyword
        for keyword in required_keywords
        if not _keyword_present(validation_view, keyword)
    ]
    any_keyword_match = not required_any or any(
        _keyword_present(validation_view, keyword) for keyword in required_any
    )
    present_forbidden = [
        keyword
        for keyword in forbidden_keywords
        if _keyword_present(validation_view, keyword)
    ]
    select_count_match = actual_selects >= minimum_selects
    style_match = (
        not missing_keywords
        and any_keyword_match
        and not present_forbidden
        and select_count_match
    )

    return {
        "correct": columns_match and rows_match and style_match,
        "columns_match": columns_match,
        "rows_match": rows_match,
        "style_match": style_match,
        "missing_keywords": missing_keywords,
        "required_any_keywords": required_any if not any_keyword_match else [],
        "forbidden_keywords": present_forbidden,
        "minimum_select_count": minimum_selects,
        "actual_select_count": actual_selects,
        "select_count_match": select_count_match,
        "user": user_result,
        "expected": solution_result,
        "solution_sql": solution_sql,
    }


# Canonical task concepts used by exercise-pack recommendations. These names mirror
# the adaptive planner's skill taxonomy so packs can match stable concepts rather
# than brittle display text.
CONCEPT_LABELS = {
    "analytics_foundations": "analytics foundations",
    "business_framing": "business questions and stakeholder framing",
    "data_preparation": "data preparation and documentation",
    "data_cleaning": "data cleaning and validation",
    "analysis_foundations": "analytical thinking and metrics",
    "spreadsheet_analysis": "spreadsheet analysis",
    "sql_fundamentals": "SQL fundamentals",
    "sql_querying": "SQL querying",
    "sql_aggregation": "SQL aggregation",
    "sql_date_logic": "SQL date logic",
    "sql_case": "SQL conditional logic",
    "sql_joins": "SQL joins",
    "sql_subqueries": "SQL subqueries",
    "sql_ctes": "SQL common table expressions",
    "sql_window_functions": "SQL window functions",
    "sql_intermediate": "intermediate SQL",
    "visualization_foundations": "data visualization",
    "data_storytelling": "data storytelling",
    "power_bi_foundations": "Power BI foundations",
    "power_bi": "Power BI modeling and DAX",
    "power_query": "Power Query",
    "dimensional_modeling": "dimensional modeling",
    "dax_measures": "DAX measures",
    "report_design": "dashboard and report design",
    "python_fundamentals": "Python fundamentals",
    "python_pandas": "Python and pandas",
    "portfolio_delivery": "portfolio delivery",
    "career_readiness": "career readiness",
    "analyst_communication": "analyst communication",
    "sql_validation": "SQL validation",
    "statistics_foundations": "statistics foundations",
    "descriptive_statistics": "descriptive statistics",
    "sampling_bias": "sampling and bias",
    "confidence_intervals": "confidence intervals",
    "hypothesis_testing": "hypothesis testing",
    "experiment_analysis": "experiment analysis",
    "causal_reasoning": "causal reasoning",
    "funnel_analysis": "funnel analysis",
    "cohort_analysis": "cohort analysis",
    "churn_analysis": "churn analysis",
    "variance_analysis": "variance analysis",
    "api_ingestion": "API and JSON ingestion",
    "data_pipeline": "analytics pipelines",
    "ai_validation": "responsible AI validation",
}

GOOGLE_COURSE_CONCEPTS = {
    1: {"analytics_foundations"},
    2: {"business_framing"},
    3: {"data_preparation"},
    4: {"data_cleaning"},
    5: {"analysis_foundations", "spreadsheet_analysis", "sql_fundamentals"},
    6: {"visualization_foundations", "data_storytelling"},
    7: {"analysis_foundations"},
    8: {"portfolio_delivery"},
    9: {"career_readiness"},
}

# Module-level overrides are intentionally explicit. Course 5 Module 3 is the
# current Google certificate unit that combines joins and subqueries.
GOOGLE_MODULE_CONCEPTS = {
    (5, 3): {"analysis_foundations", "sql_joins", "sql_subqueries"},
}

DATACAMP_CATALOG = [
    ("Introduction to SQL", "Chapter 1: Relational Databases", {"sql_fundamentals"}),
    ("Introduction to SQL", "Chapter 2: Querying", {"sql_fundamentals", "sql_querying"}),
    ("Intermediate SQL", "Chapter 1: Data Aggregation", {"sql_aggregation"}),
    ("Intermediate SQL", "Chapter 2: Data Transformation", {"sql_querying"}),
    ("Intermediate SQL", "Chapter 3: Data Filtering", {"sql_querying", "sql_date_logic"}),
    ("Intermediate SQL", "Chapter 4: Conditional Operations", {"sql_case"}),
    ("Joining Data in SQL", "Chapter 1: Combining Data Vertically", {"sql_joins"}),
    ("Joining Data in SQL", "Chapter 2: Combining Data Horizontally", {"sql_joins"}),
    ("Data Manipulation in SQL", "Chapter 1: We'll take the CASE", {"sql_case"}),
    ("Data Manipulation in SQL", "Chapter 2: Short and Simple Subqueries", {"sql_subqueries", "sql_intermediate"}),
    ("Data Manipulation in SQL", "Chapter 3: Correlated Queries, Nested Queries, and Common Table Expressions", {"sql_subqueries", "sql_ctes", "sql_intermediate"}),
    ("Data Manipulation in SQL", "Chapter 4: Window Functions", {"sql_window_functions", "sql_intermediate"}),
    ("Introduction to Power BI", "Chapter 1: Getting Started with Power BI", {"power_bi_foundations"}),
    ("Introduction to Power BI", "Chapter 2: Transforming Data", {"power_bi_foundations", "power_query"}),
    ("Introduction to Power BI", "Chapter 3: Visualizing Data", {"power_bi_foundations", "report_design"}),
    ("Introduction to Power BI", "Chapter 4: Filtering", {"power_bi_foundations", "report_design"}),
    ("Data Modeling in Power BI", "Chapter 1: Defining Tables", {"power_bi", "dimensional_modeling"}),
    ("Data Modeling in Power BI", "Chapter 2: Shaping Tables", {"power_bi", "power_query"}),
    ("Data Modeling in Power BI", "Chapter 3: Dimensional Modeling", {"power_bi", "dimensional_modeling"}),
    ("Data Modeling in Power BI", "Chapter 4: Star and Snowflake schemas", {"power_bi", "dimensional_modeling"}),
    ("Introduction to Python", "Chapter 1: Python Basics", {"python_fundamentals"}),
    ("Introduction to Python", "Chapter 2: Python Lists", {"python_fundamentals"}),
    ("Introduction to Python", "Chapter 3: Functions and Packages", {"python_fundamentals"}),
    ("Introduction to Python", "Chapter 4: NumPy", {"python_fundamentals"}),
    ("Data Manipulation with pandas", "Chapter 1: Transforming DataFrames", {"python_pandas"}),
    ("Data Manipulation with pandas", "Chapter 2: Aggregating DataFrames", {"python_pandas"}),
    ("Data Manipulation with pandas", "Chapter 3: Slicing and Indexing DataFrames", {"python_pandas"}),
    ("Data Manipulation with pandas", "Chapter 4: Creating and Visualizing DataFrames", {"python_pandas", "visualization_foundations"}),
]

SQL_PROBLEM_CONCEPTS = {
    "Histogram of Tweets": {"sql_aggregation", "sql_ctes"},
    "Data Science Skills": {"sql_aggregation"},
    "Page With No Likes": {"sql_joins"},
    "Laptop vs. Mobile Viewership": {"sql_aggregation", "sql_case"},
    "Duplicate Job Listings": {"sql_aggregation"},
    "Teams Power Users": {"sql_aggregation"},
    "Pharmacy Analytics Part 1": {"analysis_foundations", "sql_aggregation"},
    "Signup Activation Rate": {"sql_aggregation", "sql_joins"},
    "User's Third Transaction": {"sql_window_functions"},
    "Second Highest Salary": {"sql_window_functions"},
    "Top Three Salaries": {"sql_joins", "sql_window_functions"},
    "Tweets' Rolling Averages": {"sql_window_functions"},
    "Odd and Even Measurements": {"sql_ctes", "sql_window_functions"},
    "User Shopping Sprees": {"sql_aggregation", "sql_date_logic"},
    "Supercloud Customer": {"sql_aggregation", "sql_joins"},
    "Second Day Confirmation": {"sql_date_logic", "sql_joins"},
    "Timed SQL review": {"sql_intermediate"},
}

DUCKDB_EXERCISE_CONCEPTS = {
    1: {"sql_fundamentals", "sql_querying"},
    2: {"sql_aggregation"},
    3: {"sql_case"},
    4: {"sql_aggregation", "sql_date_logic", "sql_case"},
    5: {"sql_aggregation", "sql_case"},
    6: {"sql_joins"},
    7: {"sql_subqueries", "sql_ctes", "sql_intermediate"},
    8: {"sql_aggregation", "sql_case", "sql_joins", "sql_ctes", "sql_window_functions", "sql_intermediate"},
    9: {"sql_aggregation", "sql_case", "sql_joins", "sql_ctes", "sql_intermediate"},
    10: {"sql_aggregation", "sql_joins", "sql_ctes", "sql_window_functions", "sql_intermediate"},
    11: {"sql_joins", "sql_window_functions", "sql_intermediate"},
    12: {"sql_ctes", "sql_intermediate"},
}

APPLIED_LAB_CONCEPTS = {
    1: {"power_bi_foundations"},
    2: {"power_query"},
    3: {"power_query"},
    4: {"dimensional_modeling"},
    5: {"dax_measures"},
    6: {"report_design"},
    7: {"data_preparation"},
    8: {"python_pandas"},
    9: {"python_pandas"},
    10: {"python_pandas"},
    11: {"sql_aggregation"},
    12: {"analysis_foundations", "analyst_communication"},
    13: {"analyst_communication"},
    14: {"analyst_communication"},
    15: {"sql_querying", "sql_validation"},
    16: {"sql_joins", "sql_validation"},
    17: {"sql_aggregation", "sql_date_logic", "sql_validation"},
    18: {"data_storytelling"},
    19: {"sql_validation", "analyst_communication"},
    20: {"analysis_foundations"},
    21: {"analyst_communication"},
    22: {"descriptive_statistics"},
    23: {"descriptive_statistics", "data_preparation"},
    24: {"sampling_bias", "descriptive_statistics"},
    25: {"confidence_intervals"},
    26: {"hypothesis_testing", "analyst_communication"},
    27: {"experiment_analysis"},
    28: {"causal_reasoning", "python_pandas"},
    29: {"business_framing", "sql_aggregation", "funnel_analysis"},
    30: {"sql_date_logic", "sql_ctes", "funnel_analysis"},
    31: {"cohort_analysis", "sql_date_logic", "sql_joins"},
    32: {"analysis_foundations", "sql_aggregation", "churn_analysis", "variance_analysis"},
    33: {"python_pandas", "data_preparation", "api_ingestion"},
    34: {"api_ingestion", "data_cleaning", "sql_ctes", "data_pipeline"},
    35: {"analyst_communication", "sql_validation", "ai_validation"},
    36: {"power_bi", "report_design"},
}

PROJECT_TASK_CONCEPTS = {
    "Finalize business problem": {"business_framing"},
    "Finalize stakeholders": {"business_framing"},
    "Finalize KPIs": {"business_framing"},
    "Finalize business questions": {"business_framing"},
    "Create synthetic data specification": {"data_preparation"},
    "Generate dataset": {"data_preparation"},
    "Validate relationships": {"sql_fundamentals"},
    "Complete data dictionary": {"data_preparation"},
    "Create schema": {"sql_fundamentals"},
    "Load data": {"sql_fundamentals"},
    "Run quality checks": {"data_cleaning", "sql_validation"},
    "Answer business questions": {"analysis_foundations", "sql_fundamentals"},
    "Save documented queries": {"sql_fundamentals", "analyst_communication"},
    "Clean data": {"data_cleaning"},
    "Explore distributions": {"analysis_foundations", "descriptive_statistics"},
    "Detect anomalies": {"analysis_foundations"},
    "Validate SQL findings": {"sql_fundamentals", "sql_joins", "sql_validation"},
    "Build data model": {"visualization_foundations", "power_bi_foundations", "dimensional_modeling"},
    "Create DAX measures": {"power_bi", "dax_measures"},
    "Build executive dashboard": {"power_bi", "data_storytelling", "report_design"},
    "Build workload dashboard": {"power_bi", "data_storytelling", "report_design"},
    "Add filters and drill-through": {"power_bi", "report_design"},
    "Write executive summary": {"data_storytelling", "analyst_communication"},
    "Add screenshots": {"visualization_foundations", "portfolio_delivery"},
    "Document assumptions and limitations": {"analysis_foundations", "analyst_communication"},
    "Finalize README": {"portfolio_delivery", "analyst_communication"},
    "Publish release": {"portfolio_delivery"},
}

TRACK_FALLBACK_CONCEPTS = {
    "google": {"google_certificate"},
    "datacamp": {"datacamp_curriculum"},
    "sql": {"sql_practice"},
    "portfolio": {"portfolio_work"},
    "applied": {"applied_practice"},
}

CATEGORY_FALLBACK_CONCEPTS = {
    "learning": {"general_learning"},
    "sql": {"sql_practice"},
    "portfolio": {"portfolio_work"},
    "applications": {"career_readiness"},
    "career": {"career_readiness"},
}

KEYWORD_CONCEPT_PATTERNS = (
    (r"\bsubquer(?:y|ies)\b|\bnested quer(?:y|ies)\b|\bcorrelated quer(?:y|ies)\b", "sql_subqueries"),
    (r"\bcommon table expression(?:s)?\b|\bctes?\b", "sql_ctes"),
    (r"\bjoins?\b|\bleft join\b|\bright join\b|\binner join\b|\bfull join\b", "sql_joins"),
    (r"\bwindow function(?:s)?\b|\brow_number\b|\bdense_rank\b|\bpartition by\b", "sql_window_functions"),
    (r"\bgroup by\b|\bhaving\b|\baggregation\b|\bcount distinct\b", "sql_aggregation"),
    (r"\bcase expression\b|\bconditional operations?\b|\bcase\b", "sql_case"),
    (r"\bdate logic\b|\bdate filtering\b|\bdates?\b", "sql_date_logic"),
    (r"\bselect\b|\bfiltering\b|\bsorting\b|\blimit\b", "sql_querying"),
    (r"\bpower query\b", "power_query"),
    (r"\bdax\b|\bmeasures?\b", "dax_measures"),
    (r"\bstar schema\b|\bsnowflake schema\b|\bdimensional model", "dimensional_modeling"),
    (r"\bpower bi\b", "power_bi"),
    (r"\bpandas\b|\bdataframes?\b", "python_pandas"),
    (r"\bpython\b|\bnumpy\b", "python_fundamentals"),
    (r"\bdata clean(?:ing)?\b|\bquality checks?\b", "data_cleaning"),
    (r"\bdata dictionary\b|\bsynthetic data specification\b|\bprepare data\b", "data_preparation"),
    (r"\bstakeholders?\b|\bbusiness questions?\b|\bkpis?\b", "business_framing"),
    (r"\bdashboard\b|\bvisualiz(?:e|ation|ations)\b", "visualization_foundations"),
    (r"\bexecutive summary\b|\bstorytell(?:ing)?\b|\bpresentation\b", "data_storytelling"),
    (r"\bhypothesis test(?:ing)?\b", "hypothesis_testing"),
    (r"\bconfidence intervals?\b|\bmargin of error\b", "confidence_intervals"),
    (r"\bsampling\b|\bbias\b", "sampling_bias"),
    (r"\bcohort\b|\bretention\b", "cohort_analysis"),
    (r"\bchurn\b", "churn_analysis"),
    (r"\bfunnel\b|\bconversion rate\b", "funnel_analysis"),
    (r"\bapi\b|\bjson ingestion\b", "api_ingestion"),
)


def _task_value(task: Any, key: str, default: Any = None) -> Any:
    try:
        value = task[key]
    except (KeyError, IndexError, TypeError):
        value = getattr(task, key, default)
    return default if value is None else value


def _task_text(task: Any) -> str:
    fields = []
    for key in (
        "label",
        "category",
        "status",
        "prerequisite_reason",
        "track_key",
        "target_key",
        "source_label",
    ):
        value = _task_value(task, key, "")
        if value:
            fields.append(str(value))
    return " ".join(fields).lower()


def _task_incomplete(task: Any) -> bool:
    return not bool(_task_value(task, "completed", False))


def _task_category(task: Any) -> str:
    return str(_task_value(task, "category", "") or "")


def _task_concepts(task: Any) -> set[str]:
    value = _task_value(task, "concepts", [])
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            value = parsed if isinstance(parsed, list) else [value]
        except json.JSONDecodeError:
            value = [item.strip() for item in value.split(",")]
    if not isinstance(value, (list, tuple, set)):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _state_value(state: Any, key: str, default: Any = None) -> Any:
    try:
        value = state[key]
    except (KeyError, IndexError, TypeError):
        getter = getattr(state, "get", None)
        value = getter(key, default) if callable(getter) else default
    return default if value is None else value


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _parse_google_position(task: Any, state: dict[str, Any]) -> tuple[int | None, int | None]:
    text = _task_text(task)
    course_match = re.search(r"\bcourse\s*0?(\d+)\b", text, re.IGNORECASE)
    module_match = re.search(r"\bmodule\s*0?(\d+)\b", text, re.IGNORECASE)
    course = int(course_match.group(1)) if course_match else None
    module = int(module_match.group(1)) if module_match else None
    track = str(_task_value(task, "track_key", "") or "").lower()
    if track == "google" and _task_incomplete(task):
        if course is None:
            try:
                course = int(_state_value(state, "google_course", 0)) or None
            except (TypeError, ValueError):
                course = None
        if module is None:
            try:
                module = int(_state_value(state, "google_module", 0)) or None
            except (TypeError, ValueError):
                module = None
    return course, module


def _target_index(task: Any, prefix: str) -> int | None:
    target = str(_task_value(task, "target_key", "") or "")
    match = re.search(rf"(?:^|[^a-z]){re.escape(prefix)}[^0-9]*(\d+)", target, re.IGNORECASE)
    if not match and target and str(_task_value(task, "track_key", "")).lower() == prefix:
        numbers = re.findall(r"\d+", target)
        match_value = numbers[-1] if numbers else None
        return int(match_value) if match_value else None
    return int(match.group(1)) if match else None


def _number_from_text(task: Any, pattern: str) -> int | None:
    match = re.search(pattern, _task_text(task), re.IGNORECASE)
    return int(match.group(1)) if match else None


def _datacamp_index(task: Any) -> int | None:
    direct = _target_index(task, "datacamp")
    if direct and 1 <= direct <= len(DATACAMP_CATALOG):
        return direct
    text = _normalize_title(_task_text(task))
    for index, (course, chapter, _) in enumerate(DATACAMP_CATALOG, start=1):
        if _normalize_title(course) in text and _normalize_title(chapter) in text:
            return index
    return None


_LIVE_CATALOG_OVERRIDES_CACHE: dict[str, Any] | None = None


def _load_live_catalog_overrides() -> dict[str, Any]:
    """Use the app's current catalogs when available, with bundled fallbacks for tests."""
    global _LIVE_CATALOG_OVERRIDES_CACHE
    if _LIVE_CATALOG_OVERRIDES_CACHE is not None:
        return _LIVE_CATALOG_OVERRIDES_CACHE
    overrides: dict[str, Any] = {}
    try:
        from career_app.services import tracks as track_service  # type: ignore

        for name in (
            "SQL_PROBLEM_REQUIREMENTS",
            "DUCKDB_SKILL_EVIDENCE",
            "APPLIED_REQUIRED_SKILLS",
            "PROJECT_EXACT_REQUIREMENTS",
        ):
            value = getattr(track_service, name, None)
            if isinstance(value, dict):
                overrides[name] = value
    except (ImportError, AttributeError):
        pass
    try:
        from career_app.data.roadmap import DATACAMP_TRACK  # type: ignore

        if isinstance(DATACAMP_TRACK, list):
            overrides["DATACAMP_TRACK"] = DATACAMP_TRACK
    except (ImportError, AttributeError):
        pass
    _LIVE_CATALOG_OVERRIDES_CACHE = overrides
    return overrides


def infer_task_concepts(
    task: Any, state: dict[str, Any] | None = None
) -> dict[str, tuple[str, int]]:
    """Return concept -> (source, confidence) for one task.

    Exact track/catalog matches win over title-keyword fallbacks. Every task also
    receives a low-confidence track/category coverage tag so the audit can detect
    genuinely unclassified tasks without losing them entirely.
    """
    state = state or {}
    found: dict[str, tuple[str, int]] = {}

    def add(concepts: Iterable[str], source: str, confidence: int) -> None:
        for concept in concepts:
            concept = str(concept).strip()
            if not concept:
                continue
            previous = found.get(concept)
            if previous is None or confidence > previous[1]:
                found[concept] = (source, confidence)

    track = str(_task_value(task, "track_key", "") or "").strip().lower()
    category = _task_category(task).strip().lower()
    text = _task_text(task)
    normalized_text = _normalize_title(text)
    overrides = _load_live_catalog_overrides()

    if track in TRACK_FALLBACK_CONCEPTS:
        add(TRACK_FALLBACK_CONCEPTS[track], f"track:{track}", 25)
    if category in CATEGORY_FALLBACK_CONCEPTS:
        add(CATEGORY_FALLBACK_CONCEPTS[category], f"category:{category}", 20)

    course, module = _parse_google_position(task, state)
    if course is not None:
        add(GOOGLE_COURSE_CONCEPTS.get(course, set()), f"google-course:{course}", 90)
        if module is not None:
            add(
                GOOGLE_MODULE_CONCEPTS.get((course, module), set()),
                f"google-course:{course}-module:{module}",
                100,
            )

    datacamp_index = _datacamp_index(task)
    if datacamp_index is not None:
        _, _, concepts = DATACAMP_CATALOG[datacamp_index - 1]
        add(concepts, f"datacamp-chapter:{datacamp_index}", 100)

    live_datacamp = overrides.get("DATACAMP_TRACK", [])
    if live_datacamp:
        for index, item in enumerate(live_datacamp, start=1):
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            if _normalize_title(item[0]) in normalized_text and _normalize_title(item[1]) in normalized_text:
                if 1 <= index <= len(DATACAMP_CATALOG):
                    add(DATACAMP_CATALOG[index - 1][2], f"live-datacamp:{index}", 100)
                break

    sql_map = dict(SQL_PROBLEM_CONCEPTS)
    live_sql = overrides.get("SQL_PROBLEM_REQUIREMENTS")
    if isinstance(live_sql, dict):
        sql_map.update({str(key): set(value) for key, value in live_sql.items()})
    for title, concepts in sql_map.items():
        if _normalize_title(title) in normalized_text:
            add(concepts, f"sql-problem:{title}", 100)
            break

    duckdb_number = _number_from_text(
        task, r"\bduckdb(?:\s+sql)?(?:\s+exercise)?\s*0?(\d+)\b"
    )
    if duckdb_number is None and track == "sql":
        target = str(_task_value(task, "target_key", "") or "")
        if "duckdb" in target.lower():
            numbers = re.findall(r"\d+", target)
            duckdb_number = int(numbers[-1]) if numbers else None
    duckdb_map = dict(DUCKDB_EXERCISE_CONCEPTS)
    live_duckdb = overrides.get("DUCKDB_SKILL_EVIDENCE")
    if isinstance(live_duckdb, dict):
        duckdb_map.update({int(key): set(value) for key, value in live_duckdb.items()})
    if duckdb_number in duckdb_map:
        add(duckdb_map[duckdb_number], f"duckdb-exercise:{duckdb_number}", 100)

    applied_number = _number_from_text(
        task, r"\bapplied(?:\s+lab|\s+exercise)?\s*0?(\d+)\b"
    )
    if applied_number is None and track == "applied":
        target = str(_task_value(task, "target_key", "") or "")
        numbers = re.findall(r"\d+", target)
        applied_number = int(numbers[-1]) if numbers else None
    applied_map = dict(APPLIED_LAB_CONCEPTS)
    live_applied = overrides.get("APPLIED_REQUIRED_SKILLS")
    if isinstance(live_applied, dict):
        for key, value in live_applied.items():
            applied_map.setdefault(int(key), set()).update(set(value))
    if applied_number in applied_map:
        add(applied_map[applied_number], f"applied-lab:{applied_number}", 100)

    project_map = dict(PROJECT_TASK_CONCEPTS)
    live_project = overrides.get("PROJECT_EXACT_REQUIREMENTS")
    if isinstance(live_project, dict):
        project_map.update({str(key): set(value) for key, value in live_project.items()})
    for title, concepts in project_map.items():
        if _normalize_title(title) in normalized_text:
            add(concepts, f"portfolio-task:{title}", 100)

    for pattern, concept in KEYWORD_CONCEPT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            add({concept}, f"keyword:{pattern}", 70)

    if not found:
        add({"general_task"}, "fallback:unclassified", 10)
    return found


def _rule_matches(
    rule: dict[str, Any], state: dict[str, Any], tasks: list[Any]
) -> tuple[bool, str | None]:
    incomplete = [task for task in tasks if _task_incomplete(task)]
    categories = {str(item).lower() for item in rule.get("category_any", [])}
    if categories and not any(_task_category(task).lower() in categories for task in incomplete):
        return False, None

    course_values = rule.get("google_course_any")
    if course_values and int(_state_value(state, "google_course", 0)) not in {
        int(item) for item in course_values
    }:
        return False, None

    module_values = rule.get("google_module_any")
    if module_values and int(_state_value(state, "google_module", 0)) not in {
        int(item) for item in module_values
    }:
        return False, None

    concept_any = {str(item) for item in rule.get("concept_any", [])}
    if concept_any and not any(_task_concepts(task) & concept_any for task in incomplete):
        return False, None

    concept_all = {str(item) for item in rule.get("concept_all", [])}
    if concept_all and not any(concept_all.issubset(_task_concepts(task)) for task in incomplete):
        return False, None

    keywords = [str(item).lower() for item in rule.get("task_keyword_any", [])]
    if keywords and not any(
        any(keyword in _task_text(task) for keyword in keywords) for task in incomplete
    ):
        return False, None

    reason = rule.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = f"A current task is connected to {rule.get('concept', 'this concept')}."
    return True, reason


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except sqlite3.Error:
        return set()


def _rows_as_dicts(rows: Iterable[Any], names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            name: (row[name] if isinstance(row, sqlite3.Row) else row[index])
            for index, name in enumerate(names)
        }
        for row in rows
    ]


def all_task_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read every task plus adaptive-track identity used by the tag audit."""
    sprint_columns = _table_columns(conn, "sprint_tasks")
    if {"id", "label", "completed"}.issubset(sprint_columns):
        metadata_columns = _table_columns(conn, "task_metadata")
        track_columns = _table_columns(conn, "track_tasks")
        can_join_metadata = "task_id" in metadata_columns
        can_join_track = "task_id" in track_columns
        names = [
            "task_id", "week", "sort_order", "label", "category", "status",
            "prerequisite_reason", "completed", "track_key", "target_key", "source_label",
        ]
        category_expr = "COALESCE(m.category, '')" if can_join_metadata and "category" in metadata_columns else "''"
        status_expr = "COALESCE(m.status, '')" if can_join_metadata and "status" in metadata_columns else "''"
        reason_expr = "COALESCE(m.prerequisite_reason, '')" if can_join_metadata and "prerequisite_reason" in metadata_columns else "''"
        track_expr = "COALESCE(tt.track_key, '')" if can_join_track and "track_key" in track_columns else "''"
        target_expr = "COALESCE(tt.target_key, '')" if can_join_track and "target_key" in track_columns else "''"
        source_expr = "COALESCE(tt.source_label, '')" if can_join_track and "source_label" in track_columns else "''"
        week_expr = "COALESCE(s.week, 0)" if "week" in sprint_columns else "0"
        sort_expr = "COALESCE(s.sort_order, 0)" if "sort_order" in sprint_columns else "0"
        joins = []
        if can_join_metadata:
            joins.append("LEFT JOIN task_metadata AS m ON m.task_id = s.id")
        if can_join_track:
            joins.append("LEFT JOIN track_tasks AS tt ON tt.task_id = s.id")
        sql = f"""
            SELECT s.id AS task_id, {week_expr} AS week, {sort_expr} AS sort_order,
                   s.label AS label, {category_expr} AS category, {status_expr} AS status,
                   {reason_expr} AS prerequisite_reason, s.completed AS completed,
                   {track_expr} AS track_key, {target_expr} AS target_key,
                   {source_expr} AS source_label
            FROM sprint_tasks AS s
            {' '.join(joins)}
            ORDER BY week, sort_order, task_id
        """
        try:
            return _rows_as_dicts(conn.execute(sql).fetchall(), names)
        except sqlite3.Error:
            return []

    task_columns = _table_columns(conn, "tasks")
    if "completed" not in task_columns:
        return []
    names = ["task_id", "week", "sort_order", "label", "category", "status", "prerequisite_reason", "completed", "track_key", "target_key", "source_label"]
    expressions = [
        ("id AS task_id" if "id" in task_columns else "rowid AS task_id"),
        ("week" if "week" in task_columns else "0 AS week"),
        ("sort_order" if "sort_order" in task_columns else "0 AS sort_order"),
        ("label" if "label" in task_columns else "'' AS label"),
        ("category" if "category" in task_columns else "'' AS category"),
        ("status" if "status" in task_columns else "'' AS status"),
        ("prerequisite_reason" if "prerequisite_reason" in task_columns else "'' AS prerequisite_reason"),
        "completed",
        ("track_key" if "track_key" in task_columns else "'' AS track_key"),
        ("target_key" if "target_key" in task_columns else "'' AS target_key"),
        ("source_label" if "source_label" in task_columns else "'' AS source_label"),
    ]
    try:
        return _rows_as_dicts(conn.execute(f"SELECT {', '.join(expressions)} FROM tasks").fetchall(), names)
    except sqlite3.Error:
        return []


def sync_task_concept_tags(
    conn: sqlite3.Connection, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Re-audit every task and persist only concept tags that actually changed."""
    ensure_schema(conn)
    rows = all_task_rows(conn)
    current_ids = {int(row["task_id"]) for row in rows}
    existing: dict[int, dict[str, tuple[str, int]]] = {}
    try:
        for item in conn.execute(
            "SELECT task_id,concept,source,confidence FROM task_concept_tags"
        ).fetchall():
            task_id = int(item["task_id"] if isinstance(item, sqlite3.Row) else item[0])
            concept = str(item["concept"] if isinstance(item, sqlite3.Row) else item[1])
            source = str(item["source"] if isinstance(item, sqlite3.Row) else item[2])
            confidence = int(item["confidence"] if isinstance(item, sqlite3.Row) else item[3])
            existing.setdefault(task_id, {})[concept] = (source, confidence)
    except sqlite3.Error:
        existing = {}

    stale_ids = sorted(set(existing) - current_ids)
    changed: list[tuple[int, dict[str, tuple[str, int]]]] = []
    for row in rows:
        task_id = int(row["task_id"])
        inferred = infer_task_concepts(row, state or {})
        if existing.get(task_id, {}) != inferred:
            changed.append((task_id, inferred))

    if stale_ids or changed:
        with conn:
            if stale_ids:
                placeholders = ",".join("?" for _ in stale_ids)
                conn.execute(
                    f"DELETE FROM task_concept_tags WHERE task_id IN ({placeholders})",
                    tuple(stale_ids),
                )
            for task_id, inferred in changed:
                conn.execute("DELETE FROM task_concept_tags WHERE task_id=?", (task_id,))
                for concept, (source, confidence) in sorted(inferred.items()):
                    conn.execute(
                        """
                        INSERT INTO task_concept_tags(task_id,concept,source,confidence,updated_at)
                        VALUES(?,?,?,?,?)
                        """,
                        (task_id, concept, source, int(confidence), _now()),
                    )
    return task_tag_audit(conn, state or {}, synchronize=False)


def task_tag_audit(
    conn: sqlite3.Connection,
    state: dict[str, Any] | None = None,
    *,
    synchronize: bool = True,
) -> dict[str, Any]:
    """Return coverage details for every live task in the catalog."""
    if synchronize:
        return sync_task_concept_tags(conn, state or {})
    rows = all_task_rows(conn)
    tagged: dict[int, list[dict[str, Any]]] = {}
    try:
        for row in conn.execute(
            "SELECT task_id,concept,source,confidence FROM task_concept_tags ORDER BY task_id,concept"
        ).fetchall():
            task_id = int(row["task_id"] if isinstance(row, sqlite3.Row) else row[0])
            tagged.setdefault(task_id, []).append(
                {
                    "concept": row["concept"] if isinstance(row, sqlite3.Row) else row[1],
                    "source": row["source"] if isinstance(row, sqlite3.Row) else row[2],
                    "confidence": int(row["confidence"] if isinstance(row, sqlite3.Row) else row[3]),
                }
            )
    except sqlite3.Error:
        tagged = {}
    details = []
    untagged = []
    generic_only = []
    counts: Counter[str] = Counter()
    for task in rows:
        task_id = int(task["task_id"])
        tags = tagged.get(task_id, [])
        concepts = [item["concept"] for item in tags]
        counts.update(concepts)
        record = {
            "task_id": task_id,
            "label": task.get("label", ""),
            "track_key": task.get("track_key", ""),
            "concepts": concepts,
            "tags": tags,
        }
        details.append(record)
        if not tags:
            untagged.append(record)
        elif not any(int(item["confidence"]) >= 60 for item in tags):
            generic_only.append(record)
    return {
        "total_tasks": len(rows),
        "tagged_tasks": len(rows) - len(untagged),
        "untagged_tasks": untagged,
        "generic_only_tasks": generic_only,
        "concept_counts": dict(sorted(counts.items())),
        "tasks": details,
    }


def _attach_persisted_concepts(
    conn: sqlite3.Connection, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not rows:
        return rows
    task_ids = [int(row["task_id"]) for row in rows]
    placeholders = ",".join("?" for _ in task_ids)
    by_task: dict[int, list[str]] = {}
    try:
        for item in conn.execute(
            f"SELECT task_id,concept FROM task_concept_tags WHERE task_id IN ({placeholders}) ORDER BY concept",
            tuple(task_ids),
        ).fetchall():
            task_id = int(item["task_id"] if isinstance(item, sqlite3.Row) else item[0])
            concept = str(item["concept"] if isinstance(item, sqlite3.Row) else item[1])
            by_task.setdefault(task_id, []).append(concept)
    except sqlite3.Error:
        return rows
    for row in rows:
        row["concepts"] = by_task.get(int(row["task_id"]), [])
    return rows


def active_task_rows(
    conn: sqlite3.Connection, week: int | None = None
) -> list[dict[str, Any]]:
    """Read live incomplete tasks, independently of the frozen daily snapshot."""
    rows = [
        row for row in all_task_rows(conn)
        if _task_incomplete(row) and (week is None or int(row.get("week", 0)) == int(week))
    ]
    return _attach_persisted_concepts(conn, rows)


def best_suggestion_for_database(
    root: Path, conn: sqlite3.Connection, state: dict[str, Any]
) -> dict[str, Any] | None:
    """Recalculate a recommendation from live tasks on every dashboard refresh."""
    sync_task_concept_tags(conn, state)
    current_week = _state_value(state, "current_week", None)
    try:
        current_week = int(current_week) if current_week is not None else None
    except (TypeError, ValueError):
        current_week = None
    return best_suggestion(root, conn, state, active_task_rows(conn, current_week))


def best_suggestion(
    root: Path,
    conn: sqlite3.Connection,
    state: dict[str, Any],
    tasks: Iterable[Any],
) -> dict[str, Any] | None:
    """Return a live optional pack recommendation; nothing is written to snapshots."""
    task_list = list(tasks)
    candidates: list[tuple[int, dict[str, Any]]] = []
    for pack in list_installed_packs(root, conn):
        progress = pack.get("progress", {})
        if progress.get("total") and progress.get("completed") == progress.get("total"):
            continue
        score = 0
        reasons: list[str] = []

        for rule in pack.get("suggestion_rules", []):
            if not isinstance(rule, dict):
                continue
            matched, reason = _rule_matches(rule, state, task_list)
            if matched:
                score += int(rule.get("score", 60))
                if reason and reason not in reasons:
                    reasons.append(reason)

        trigger_concepts = {str(item) for item in pack.get("trigger_concepts", [])}
        if trigger_concepts:
            for task in task_list:
                if not _task_incomplete(task):
                    continue
                hits = sorted(_task_concepts(task) & trigger_concepts)
                if hits:
                    score += 150 + len(hits) * 10
                    labels = [CONCEPT_LABELS.get(item, item.replace("_", " ")) for item in hits]
                    reason = f"A current task is tagged for {', '.join(labels)}."
                    if reason not in reasons:
                        reasons.append(reason)
                    break

        keywords = [str(item).lower() for item in pack.get("trigger_keywords", [])]
        if keywords:
            for task in task_list:
                if not _task_incomplete(task):
                    continue
                text = _task_text(task)
                hits = [keyword for keyword in keywords if keyword in text]
                if hits:
                    score += 100 + len(hits) * 5
                    reason = f"A current task references {', '.join(sorted(set(hits)))}."
                    if reason not in reasons:
                        reasons.append(reason)
                    break

        if score:
            candidates.append(
                (
                    score,
                    {
                        "pack_id": pack["pack_id"],
                        "title": pack["title"],
                        "reason": reasons[0] if reasons else "A current task matches this pack.",
                        "progress": progress,
                    },
                )
            )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]["title"].lower()))
    return candidates[0][1]
