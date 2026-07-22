from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile


@dataclass(frozen=True, slots=True)
class ResetReport:
    backup_path: Path | None
    database_tables_cleared: tuple[str, ...]
    removed_paths: tuple[str, ...]
    recreated_paths: tuple[str, ...]


PROJECTS_README = """# Portfolio Projects

This folder is intentionally blank until a validated Career Accelerator portfolio package is imported during onboarding.
"""

CAREER_README = """# Career Materials

Use the pathway-specific onboarding and job-readiness tools to create resume, LinkedIn, interview, and application materials here.
"""

WORKSPACES_README = """# Task Workspaces

Career Accelerator creates learner-owned task notes and generated workspaces here as work begins.
"""

DATALemur_README = """# DataLemur Solutions

Career Accelerator creates one learner-owned SQL file per opened interview problem. This folder is intentionally blank after a full first-run reset.
"""

SUBMISSIONS_README = """# Learner Submissions

Career Accelerator creates learner-owned submissions here. Starter exercises, datasets, and validation guides remain in their separate folders.
"""

SQL_LOG_TEMPLATE = """# SQL Practice Log

Use Career Accelerator to track SQL practice and completed submissions.
"""


# Entire directories whose contents are learner-owned or preference-specific.
CLEAR_AND_RECREATE: tuple[tuple[str, str | None], ...] = (
    ("projects", PROJECTS_README),
    ("career", CAREER_README),
    ("workspaces", WORKSPACES_README),
    ("resources/sql/datalemur", DATALemur_README),
    ("practice/duckdb/submissions", SUBMISSIONS_README),
    ("practice/applied/submissions", SUBMISSIONS_README),
    ("exercise_packs/installed", None),
    ("archive", None),
    ("backups", None),
)

# Runtime files that are safe to regenerate.
REMOVE_FILES: tuple[str, ...] = (
    "practice/duckdb/career_practice.duckdb",
    "practice/duckdb/career_practice.duckdb.wal",
    "practice/duckdb/career_practice.duckdb-shm",
    "practice/duckdb/career_practice.duckdb-wal",
    "documentation/PROGRESS_SNAPSHOT.md",
    "PROGRESS_SNAPSHOT.md",
)

# Files created inside otherwise static weekly sprint folders.
DYNAMIC_SUBMISSION_GLOBS: tuple[str, ...] = (
    "practice/**/submissions",
)

WEEKLY_GENERATED_GLOBS: tuple[str, ...] = (
    "weeks/week-*/RETROSPECTIVE.md",
    "weeks/week-*/STUDY_PLAN.md",
    "weeks/week-*/REFLECTION*.md",
    "weeks/week-*/CAREER_TRANSITION_REFLECTION.md",
    "weeks/week-*/artifacts/*",
)

# Personal paths included in the safety archive before deletion.
BACKUP_PATHS: tuple[str, ...] = (
    "projects",
    "career",
    "workspaces",
    "resources/sql/datalemur",
    "resources/sql/SQL_PRACTICE_LOG.md",
    "practice/duckdb/submissions",
    "practice/applied/submissions",
    "practice/duckdb/career_practice.duckdb",
    "exercise_packs/installed",
    "weeks",
    "data/portfolio_catalog.json",
    "documentation/PROGRESS_SNAPSHOT.md",
    "PROGRESS_SNAPSHOT.md",
    "archive",
    "backups",
)


def _safe_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _remove_path(path: Path, removed: list[str], root: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    relative = _safe_relative(root, path)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
    removed.append(relative)


def _write_readme(directory: Path, content: str | None) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    created = [directory]
    if content is not None:
        readme = directory / "README.md"
        readme.write_text(content.rstrip() + "\n", encoding="utf-8")
        created.append(readme)
    else:
        keep = directory / ".gitkeep"
        keep.write_text("", encoding="utf-8")
        created.append(keep)
    return created


def clean_personal_files(repo_root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Remove learner-specific files and rebuild only safe empty scaffolding."""
    root = Path(repo_root).resolve()
    removed: list[str] = []
    recreated: list[str] = []

    for relative, readme in CLEAR_AND_RECREATE:
        target = root / relative
        _remove_path(target, removed, root)
        for created in _write_readme(target, readme):
            recreated.append(_safe_relative(root, created))

    # Keep expected subfolders available for future pathway-generated career material.
    for relative in (
        "career/resume",
        "career/linkedin",
        "career/interview",
        "career/applications",
        "workspaces/tasks",
    ):
        target = root / relative
        target.mkdir(parents=True, exist_ok=True)
        keep = target / ".gitkeep"
        keep.write_text("", encoding="utf-8")
        recreated.extend((_safe_relative(root, target), _safe_relative(root, keep)))

    for relative in REMOVE_FILES:
        _remove_path(root / relative, removed, root)

    fixed_submission_paths = {
        (root / relative).resolve()
        for relative, _ in CLEAR_AND_RECREATE
        if relative.endswith("/submissions")
    }
    for pattern in DYNAMIC_SUBMISSION_GLOBS:
        for directory in sorted(root.glob(pattern)):
            if directory.resolve() in fixed_submission_paths:
                continue
            _remove_path(directory, removed, root)
            for created in _write_readme(directory, SUBMISSIONS_README):
                recreated.append(_safe_relative(root, created))

    for pattern in WEEKLY_GENERATED_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.name == ".gitkeep":
                continue
            _remove_path(path, removed, root)

    sql_log = root / "resources" / "sql" / "SQL_PRACTICE_LOG.md"
    sql_log.parent.mkdir(parents=True, exist_ok=True)
    sql_log.write_text(SQL_LOG_TEMPLATE, encoding="utf-8")
    recreated.append(_safe_relative(root, sql_log))

    catalog = root / "data" / "portfolio_catalog.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_by": "Career Accelerator first-run reset",
                "projects": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    recreated.append(_safe_relative(root, catalog))

    return tuple(sorted(set(removed))), tuple(sorted(set(recreated)))


def _database_snapshot(conn: sqlite3.Connection, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(str(destination))
    try:
        conn.backup(target)
        target.commit()
    finally:
        target.close()


def create_external_reset_backup(
    conn: sqlite3.Connection,
    repo_root: Path,
    *,
    destination_directory: Path | None = None,
) -> Path:
    """Create a safety archive outside the repository before destructive cleanup."""
    root = Path(repo_root).resolve()
    destination_root = (
        Path(destination_directory).expanduser().resolve()
        if destination_directory
        else root.parent / "Career-Accelerator-Reset-Backups"
    )
    try:
        destination_root.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError(
            "The full-reset backup destination must be outside the Career Accelerator repository."
        )
    destination_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = destination_root / f"Career-Accelerator-Pre-Reset-{stamp}.zip"
    counter = 1
    while archive.exists():
        archive = destination_root / f"Career-Accelerator-Pre-Reset-{stamp}-{counter}.zip"
        counter += 1

    with tempfile.TemporaryDirectory(prefix="career-accelerator-reset-") as temporary:
        temp_root = Path(temporary)
        database_copy = temp_root / "data" / "career_accelerator.db"
        _database_snapshot(conn, database_copy)
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source_repository": str(root),
            "purpose": "Safety backup created immediately before a full first-run reset.",
        }
        (temp_root / "RESET_BACKUP_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
            for path in sorted(temp_root.rglob("*")):
                if path.is_file():
                    zipped.write(path, path.relative_to(temp_root).as_posix())
            for relative in BACKUP_PATHS:
                source = root / relative
                if not source.exists():
                    continue
                if source.is_file():
                    zipped.write(source, f"repository/{relative}")
                    continue
                for path in sorted(source.rglob("*")):
                    if path.is_file():
                        zipped.write(path, f"repository/{path.relative_to(root).as_posix()}")
    return archive


def wipe_database(conn: sqlite3.Connection) -> tuple[str, ...]:
    """Delete all application rows, including unknown future progress tables."""
    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    tables = [str(row[0]) for row in rows]
    failures: list[str] = []
    try:
        conn.execute("BEGIN IMMEDIATE")
        for table in tables:
            escaped = table.replace('"', '""')
            try:
                conn.execute(f'DELETE FROM "{escaped}"')
            except sqlite3.Error as exc:
                failures.append(f"{table}: {exc}")
        if failures:
            conn.rollback()
            raise RuntimeError("Could not clear every database table: " + "; ".join(failures))
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
        ).fetchone():
            conn.execute("DELETE FROM sqlite_sequence")
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error:
        pass
    try:
        conn.execute("VACUUM")
    except sqlite3.Error:
        pass
    return tuple(tables)


def perform_full_first_run_reset(
    conn: sqlite3.Connection,
    repo_root: Path,
    *,
    backup_destination: Path | None = None,
    create_backup: bool = True,
) -> ResetReport:
    """Back up externally, wipe all learner data, and restore blank onboarding scaffolding."""
    root = Path(repo_root).resolve()
    backup_path = (
        create_external_reset_backup(
            conn,
            root,
            destination_directory=backup_destination,
        )
        if create_backup
        else None
    )
    tables = wipe_database(conn)
    removed, recreated = clean_personal_files(root)
    return ResetReport(
        backup_path=backup_path,
        database_tables_cleared=tables,
        removed_paths=removed,
        recreated_paths=recreated,
    )
