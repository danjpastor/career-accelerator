from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

from .paths import ResetLayout, load_reset_layout


@dataclass(frozen=True, slots=True)
class ResetReport:
    backup_path: Path | None
    database_tables_cleared: tuple[str, ...]
    removed_paths: tuple[str, ...]
    recreated_paths: tuple[str, ...]
    runtime_databases_removed: tuple[str, ...]
    reset_marker_path: Path


README_TEMPLATES: dict[str, str | None] = {
    "portfolio": """# Portfolio Projects

This folder is intentionally blank until a validated Career Accelerator portfolio package is imported during onboarding.
""",
    "career": """# Career Materials

Use the pathway-specific onboarding and job-readiness tools to create resume, LinkedIn, interview, and application materials here.
""",
    "workspaces": """# Task Workspaces

Career Accelerator creates learner-owned task notes and generated workspaces here as work begins.
""",
    "datalemur": """# DataLemur Solutions

Career Accelerator creates one learner-owned SQL file per opened interview problem. This folder is intentionally blank after a full first-run reset.
""",
    "submissions": """# Learner Submissions

Career Accelerator creates learner-owned submissions here. Starter exercises, datasets, and validation guides remain in their separate folders.
""",
    "empty": None,
}

SQL_LOG_TEMPLATE = """# SQL Practice Log

Use Career Accelerator to track SQL practice and completed submissions.
"""


def _lexical_relative(root: Path, path: Path) -> str:
    try:
        return path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError:
        return str(path)


def _remove_path(path: Path, removed: list[str], root: Path) -> None:
    """Remove the configured entry itself; never follow a directory symlink."""
    if not path.exists() and not path.is_symlink():
        return
    relative = _lexical_relative(root, path)
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
    removed.append(relative)


def _write_scaffold(directory: Path, template_name: str | None) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    created = [directory]
    content = README_TEMPLATES.get(template_name or "empty")
    if content is not None:
        readme = directory / "README.md"
        readme.write_text(content.rstrip() + "\n", encoding="utf-8")
        created.append(readme)
    else:
        keep = directory / ".gitkeep"
        keep.write_text("", encoding="utf-8")
        created.append(keep)
    return created


def _safe_glob(layout: ResetLayout, pattern: str, *, field: str):
    for path in layout.glob(pattern, field=field):
        # The glob is lexically rooted. Symlinks are removed as links and not traversed.
        try:
            path.absolute().relative_to(layout.root.absolute())
        except ValueError as exc:
            raise RuntimeError(f"Reset glob escaped the application root: {path}") from exc
        yield path


def clean_personal_files(
    application_root: Path,
    *,
    manifest_path: Path | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Remove learner-specific files and rebuild only configured safe scaffolding."""
    layout = load_reset_layout(application_root, manifest_path)
    root = layout.root
    removed: list[str] = []
    recreated: list[str] = []
    recreated_roots: set[Path] = set()

    for index, item in enumerate(layout.mappings("clear_and_recreate")):
        target = layout.path(str(item["path"]), field=f"clear_and_recreate[{index}].path")
        _remove_path(target, removed, root)
        template = str(item.get("template", "empty"))
        if template not in README_TEMPLATES:
            raise RuntimeError(f"Unknown reset scaffold template: {template}")
        for created in _write_scaffold(target, template):
            recreated.append(_lexical_relative(root, created))
        recreated_roots.add(target.absolute())

    for index, item in enumerate(layout.mappings("scaffold_directories")):
        target = layout.path(str(item["path"]), field=f"scaffold_directories[{index}].path")
        target.mkdir(parents=True, exist_ok=True)
        keep = target / ".gitkeep"
        keep.write_text("", encoding="utf-8")
        recreated.extend((_lexical_relative(root, target), _lexical_relative(root, keep)))

    for index, relative in enumerate(layout.strings("remove_files")):
        _remove_path(layout.path(relative, field=f"remove_files[{index}]"), removed, root)

    for index, pattern in enumerate(layout.strings("remove_globs")):
        for path in sorted(_safe_glob(layout, pattern, field=f"remove_globs[{index}]")):
            _remove_path(path, removed, root)

    # Generated submission directories can exist under future pathway-specific practice
    # trees. Preserve static exercises/datasets and only rebuild the matched submission root.
    for index, pattern in enumerate(layout.strings("generated_file_globs")):
        for path in sorted(_safe_glob(layout, pattern, field=f"generated_file_globs[{index}]")):
            if path.name == ".gitkeep":
                continue
            path_absolute = path.absolute()
            if path_absolute in recreated_roots:
                continue
            is_submission_directory = path.is_dir() and path.name in {"submissions", "solutions"}
            _remove_path(path, removed, root)
            if is_submission_directory:
                for created in _write_scaffold(path, "submissions"):
                    recreated.append(_lexical_relative(root, created))

    sql_log = layout.configured_path("sql_practice_log")
    sql_log.parent.mkdir(parents=True, exist_ok=True)
    sql_log.write_text(SQL_LOG_TEMPLATE, encoding="utf-8")
    recreated.append(_lexical_relative(root, sql_log))

    catalog = layout.configured_path("portfolio_catalog")
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "generated_by": "Career Accelerator full first-run reset",
                "projects": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    recreated.append(_lexical_relative(root, catalog))

    return tuple(sorted(set(removed))), tuple(sorted(set(recreated)))


def _database_snapshot(conn: sqlite3.Connection, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    target = sqlite3.connect(str(destination))
    try:
        conn.backup(target)
        target.commit()
    finally:
        target.close()


def _archive_path(zipped: zipfile.ZipFile, source: Path, root: Path, relative: str) -> None:
    if not source.exists() and not source.is_symlink():
        return
    if source.is_symlink():
        # Record the link target as text without reading outside the application root.
        zipped.writestr(f"repository/{relative}.symlink.txt", str(source.readlink()))
        return
    if source.is_file():
        zipped.write(source, f"repository/{relative}")
        return
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            link_relative = path.relative_to(root).as_posix()
            zipped.writestr(f"repository/{link_relative}.symlink.txt", str(path.readlink()))
        elif path.is_file():
            zipped.write(path, f"repository/{path.relative_to(root).as_posix()}")


def create_external_reset_backup(
    conn: sqlite3.Connection,
    application_root: Path,
    *,
    destination_directory: Path | None = None,
    manifest_path: Path | None = None,
) -> Path:
    """Create a safety archive outside the application root before destructive cleanup."""
    layout = load_reset_layout(application_root, manifest_path)
    root = layout.root
    default_name = str(layout.raw.get("external_backup_directory_name") or "Career-Accelerator-Reset-Backups")
    destination_root = (
        Path(destination_directory).expanduser().resolve()
        if destination_directory
        else root.parent / default_name
    )
    try:
        destination_root.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("The full-reset backup destination must be outside the application root.")
    destination_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = destination_root / f"Career-Accelerator-Pre-Reset-{stamp}.zip"
    counter = 1
    while archive.exists():
        archive = destination_root / f"Career-Accelerator-Pre-Reset-{stamp}-{counter}.zip"
        counter += 1

    with tempfile.TemporaryDirectory(prefix="career-accelerator-reset-") as temporary:
        temp_root = Path(temporary)
        database_copy = temp_root / "database" / "active_application_database.db"
        _database_snapshot(conn, database_copy)
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source_application_root": str(root),
            "reset_manifest": str(layout.manifest_path),
            "purpose": "Safety backup created immediately before a full first-run reset.",
        }
        (temp_root / "RESET_BACKUP_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
            for path in sorted(temp_root.rglob("*")):
                if path.is_file():
                    zipped.write(path, path.relative_to(temp_root).as_posix())
            for index, relative in enumerate(layout.strings("backup_paths")):
                source = layout.path(relative, field=f"backup_paths[{index}]")
                _archive_path(zipped, source, root, relative)
    return archive


def wipe_database(conn: sqlite3.Connection) -> tuple[str, ...]:
    """Delete all rows from every application table, including future progress tables."""
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


def _active_database_path(conn: sqlite3.Connection) -> Path | None:
    try:
        rows = conn.execute("PRAGMA database_list").fetchall()
    except sqlite3.Error:
        return None
    for row in rows:
        if str(row[1]) == "main" and str(row[2] or "").strip():
            return Path(str(row[2])).expanduser().resolve()
    return None


def remove_runtime_databases(
    conn: sqlite3.Connection,
    layout: ResetLayout,
) -> tuple[str, ...]:
    """Remove configured secondary SQLite/DuckDB stores without deleting the open DB."""
    active = _active_database_path(conn)
    candidates: list[Path] = []
    for index, relative in enumerate(layout.strings("runtime_database_files")):
        candidates.append(layout.path(relative, field=f"runtime_database_files[{index}]"))
    for index, pattern in enumerate(layout.strings("runtime_database_globs")):
        candidates.extend(_safe_glob(layout, pattern, field=f"runtime_database_globs[{index}]"))

    removed: list[str] = []
    for path in sorted(set(candidates)):
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path.absolute()
        if active is not None and resolved == active:
            continue
        if not path.exists() and not path.is_symlink():
            continue
        try:
            _remove_path(path, removed, layout.root)
        except PermissionError as exc:
            raise RuntimeError(f"Could not remove runtime database {path}. Close tools using it and retry.") from exc
    return tuple(sorted(set(removed)))


def write_reset_marker(layout: ResetLayout) -> Path:
    marker = layout.configured_path("reset_marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary = marker.with_suffix(marker.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "action": "force_first_run_on_next_start",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(marker)
    return marker


def perform_full_first_run_reset(
    conn: sqlite3.Connection,
    application_root: Path,
    *,
    backup_destination: Path | None = None,
    create_backup: bool = True,
    manifest_path: Path | None = None,
) -> ResetReport:
    """Back up externally, wipe all learner data, and force Step 1 on next launch."""
    layout = load_reset_layout(application_root, manifest_path)
    backup_path = (
        create_external_reset_backup(
            conn,
            layout.root,
            destination_directory=backup_destination,
            manifest_path=layout.manifest_path,
        )
        if create_backup
        else None
    )
    tables = wipe_database(conn)
    runtime_removed = remove_runtime_databases(conn, layout)
    removed, recreated = clean_personal_files(layout.root, manifest_path=layout.manifest_path)
    marker = write_reset_marker(layout)
    return ResetReport(
        backup_path=backup_path,
        database_tables_cleared=tables,
        removed_paths=removed,
        recreated_paths=recreated,
        runtime_databases_removed=runtime_removed,
        reset_marker_path=marker,
    )
