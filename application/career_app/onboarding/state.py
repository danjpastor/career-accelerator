from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

from .catalog import PathwayCatalog, PathwayDefinition
from .portfolio_catalog import apply_runtime_catalog, write_project_catalog
from .paths import load_reset_layout


ONBOARDING_VERSION = "1"
KEY_PREFIX = "onboarding."
KEY_PATHWAY = KEY_PREFIX + "pathway_id"
KEY_DISPLAY_NAME = KEY_PREFIX + "display_name"
KEY_ORIGIN = KEY_PREFIX + "profile_origin"
KEY_PORTFOLIO_STATUS = KEY_PREFIX + "portfolio_status"
KEY_TOUR_COMPLETED = KEY_PREFIX + "tour_completed"
KEY_COMPLETED = KEY_PREFIX + "completed"
KEY_VERSION = KEY_PREFIX + "version"
KEY_SEED_CLEANUP = KEY_PREFIX + "seed_cleanup_completed"


class OnboardingStateError(RuntimeError):
    pass


def get_setting(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return str(row["value"])
    except (TypeError, IndexError):
        return str(row[0])


def set_settings(conn: sqlite3.Connection, values: dict[str, Any]) -> None:
    with conn:
        conn.executemany(
            """
            INSERT INTO settings(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            [(key, str(value)) for key, value in values.items()],
        )


def normalize_display_name(value: Any) -> str:
    name = " ".join(str(value or "").strip().split())
    if not name:
        raise OnboardingStateError("Enter the name Career Accelerator should use in your greeting.")
    if len(name) > 60:
        raise OnboardingStateError("The greeting name must be 60 characters or fewer.")
    if any(ord(character) < 32 for character in name):
        raise OnboardingStateError("The greeting name contains unsupported control characters.")
    return name


def set_display_name(conn: sqlite3.Connection, value: Any) -> str:
    name = normalize_display_name(value)
    set_settings(
        conn,
        {
            KEY_DISPLAY_NAME: name,
            KEY_PREFIX + "display_name_saved_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return name


def display_name(conn: sqlite3.Connection, default: str = "Learner") -> str:
    value = get_setting(conn, KEY_DISPLAY_NAME)
    return " ".join(value.split()) if value and value.strip() else default


def _existing_profile_display_name(conn: sqlite3.Connection) -> str:
    for key in (KEY_DISPLAY_NAME, "profile.display_name", "display_name", "user_name"):
        value = get_setting(conn, key)
        if value and value.strip():
            return normalize_display_name(value)
    # The pre-onboarding application was a single-user build whose greeting was Dan.
    # Fresh/reset profiles never take this migration branch and must enter their name.
    return "Dan"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
    )


def _count(conn: sqlite3.Connection, table: str, where: str = "1=1") -> int:
    if not _table_exists(conn, table):
        return 0
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0


def profile_has_meaningful_data(conn: sqlite3.Connection) -> bool:
    """Detect a real existing learner before default seed data is created."""
    if _count(conn, "project_tasks") or _count(conn, "project_notes"):
        return True
    if _count(conn, "study_sessions") or _count(conn, "applications"):
        return True
    if _count(conn, "evidence") or _count(conn, "track_events"):
        return True
    if _count(conn, "sprint_tasks", "completed=1"):
        return True
    for table in (
        "academy_activity_progress",
        "academy_lesson_progress",
        "academy_checkpoint_progress",
        "academy_project_progress",
        "exercise_pack_progress",
        "duckdb_exercise_progress",
        "applied_exercise_progress",
    ):
        if _count(conn, table):
            return True
    if _table_exists(conn, "program_state"):
        row = conn.execute(
            "SELECT current_week, google_course, google_module, current_project "
            "FROM program_state WHERE id=1"
        ).fetchone()
        if row:
            values = list(row)
            if any(int(value or 0) > 1 for value in values[:3]):
                return True
            if int(values[3] or 0) > 1:
                return True
    return False


def _force_new_profile_state(conn: sqlite3.Connection) -> None:
    """Write an unambiguous blank onboarding state after a destructive reset."""
    with conn:
        conn.execute("DELETE FROM settings WHERE key LIKE ?", (KEY_PREFIX + "%",))
    set_settings(
        conn,
        {
            KEY_VERSION: ONBOARDING_VERSION,
            KEY_ORIGIN: "new",
            KEY_PORTFOLIO_STATUS: "pending",
            KEY_TOUR_COMPLETED: "0",
            KEY_COMPLETED: "0",
            KEY_SEED_CLEANUP: "0",
            KEY_PREFIX + "reset_at": datetime.now().isoformat(timespec="seconds"),
        },
    )


def migrate_existing_profile_if_needed(
    conn: sqlite3.Connection,
    *,
    reset_marker_path: Path | None = None,
) -> str:
    """Classify the profile once and honor an explicit full-reset marker.

    Seed routines can add default rows during startup. Once a profile is classified as
    ``new``, those rows must never cause a later launch to reclassify it as an existing
    learner and bypass Step 1.
    """
    marker = Path(reset_marker_path) if reset_marker_path else None
    if marker is not None and marker.is_file():
        _force_new_profile_state(conn)
        marker.unlink(missing_ok=True)
        return "new"

    existing_origin = get_setting(conn, KEY_ORIGIN)
    if existing_origin in {"new", "existing"}:
        if existing_origin == "existing" and not get_setting(conn, KEY_DISPLAY_NAME):
            set_settings(conn, {KEY_DISPLAY_NAME: _existing_profile_display_name(conn)})
        return existing_origin

    existing_pathway = get_setting(conn, KEY_PATHWAY)
    if existing_pathway:
        set_settings(
            conn,
            {
                KEY_ORIGIN: "existing",
                KEY_VERSION: ONBOARDING_VERSION,
                KEY_DISPLAY_NAME: _existing_profile_display_name(conn),
            },
        )
        return "existing"

    if profile_has_meaningful_data(conn):
        set_settings(
            conn,
            {
                KEY_VERSION: ONBOARDING_VERSION,
                KEY_ORIGIN: "existing",
                KEY_PATHWAY: "data_analytics",
                KEY_DISPLAY_NAME: _existing_profile_display_name(conn),
                KEY_PORTFOLIO_STATUS: "completed",
                KEY_TOUR_COMPLETED: "1",
                KEY_COMPLETED: "1",
                KEY_SEED_CLEANUP: "1",
                KEY_PREFIX + "migrated_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        return "existing"

    _force_new_profile_state(conn)
    return "new"


def clear_seeded_portfolio_for_new_profile(
    conn: sqlite3.Connection,
    *,
    catalog_path: Path,
) -> bool:
    """Remove legacy sample portfolio records only for a verified new profile."""
    if get_setting(conn, KEY_ORIGIN) != "new":
        return False
    if get_setting(conn, KEY_PORTFOLIO_STATUS, "pending") not in {"pending", "skipped"}:
        return False
    if get_setting(conn, KEY_SEED_CLEANUP) == "1":
        return False

    with conn:
        portfolio_task_ids: list[int] = []
        if _table_exists(conn, "track_tasks"):
            portfolio_task_ids = [
                int(row[0])
                for row in conn.execute(
                    "SELECT task_id FROM track_tasks WHERE track_key='portfolio'"
                ).fetchall()
            ]
            conn.execute("DELETE FROM track_tasks WHERE track_key='portfolio'")
        if portfolio_task_ids and _table_exists(conn, "task_concept_tags"):
            conn.executemany(
                "DELETE FROM task_concept_tags WHERE task_id=?",
                [(task_id,) for task_id in portfolio_task_ids],
            )
        if portfolio_task_ids and _table_exists(conn, "sprint_tasks"):
            conn.executemany(
                "DELETE FROM sprint_tasks WHERE id=?",
                [(task_id,) for task_id in portfolio_task_ids],
            )
        for table in ("project_notes", "project_tasks"):
            if _table_exists(conn, table):
                conn.execute(f"DELETE FROM {table}")
        if _table_exists(conn, "program_state"):
            conn.execute(
                "UPDATE program_state SET current_project=0, total_projects=0 WHERE id=1"
            )
    write_project_catalog([], catalog_path)
    apply_runtime_catalog([])
    set_settings(conn, {KEY_SEED_CLEANUP: "1"})
    return True


def select_pathway(
    conn: sqlite3.Connection,
    catalog: PathwayCatalog,
    pathway_id: str,
) -> PathwayDefinition:
    definition = catalog.require(pathway_id)
    if not definition.is_available:
        raise OnboardingStateError(
            f"{definition.display_name} is a future pathway shell and is not available yet."
        )
    current = get_setting(conn, KEY_PATHWAY)
    if current and current != pathway_id and profile_has_meaningful_data(conn):
        raise OnboardingStateError(
            "The pathway cannot be changed while learner progress exists. Use the explicit "
            "factory-reset action after creating a backup."
        )
    set_settings(
        conn,
        {
            KEY_PATHWAY: definition.pathway_id,
            KEY_PREFIX + "pathway_selected_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return definition


def mark_portfolio_status(conn: sqlite3.Connection, status: str) -> None:
    if status not in {"pending", "completed", "skipped"}:
        raise OnboardingStateError(f"Unsupported portfolio status: {status}")
    set_settings(conn, {KEY_PORTFOLIO_STATUS: status})


def mark_tour_completed(conn: sqlite3.Connection) -> None:
    set_settings(
        conn,
        {
            KEY_TOUR_COMPLETED: "1",
            KEY_PREFIX + "tour_completed_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    recompute_completion(conn)


def restart_tour(conn: sqlite3.Connection) -> None:
    set_settings(conn, {KEY_TOUR_COMPLETED: "0", KEY_COMPLETED: "0"})


def recompute_completion(conn: sqlite3.Connection) -> bool:
    complete = bool(
        get_setting(conn, KEY_DISPLAY_NAME)
        and get_setting(conn, KEY_PATHWAY)
        and get_setting(conn, KEY_PORTFOLIO_STATUS) in {"completed", "skipped"}
        and get_setting(conn, KEY_TOUR_COMPLETED) == "1"
    )
    set_settings(conn, {KEY_COMPLETED: "1" if complete else "0"})
    return complete


def onboarding_required(conn: sqlite3.Connection) -> bool:
    return get_setting(conn, KEY_COMPLETED, "0") != "1"


def export_state(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        "SELECT key, value FROM settings WHERE key LIKE ? ORDER BY key",
        (KEY_PREFIX + "%",),
    ).fetchall()
    return {str(row[0]): str(row[1]) for row in rows}


def reset_to_first_run(
    conn: sqlite3.Connection,
    *,
    application_root: Path | None = None,
    repo_root: Path | None = None,
    catalog_path: Path | None = None,
    backup_destination: Path | None = None,
    manifest_path: Path | None = None,
):
    """Perform the explicit destructive reset and return its safety report.

    ``repo_root`` remains as a compatibility alias for v10.20.1 callers. All actual
    cleanup locations are loaded from the reset manifest under the resolved application
    root; no repository name, GitHub layout, drive letter, or fixed folder depth is used.
    """
    from .reset import perform_full_first_run_reset

    root = Path(application_root or repo_root or ".").expanduser().resolve()
    layout = load_reset_layout(root, manifest_path)
    report = perform_full_first_run_reset(
        conn,
        layout.root,
        backup_destination=backup_destination,
        create_backup=True,
        manifest_path=layout.manifest_path,
    )
    resolved_catalog = catalog_path or layout.configured_path("portfolio_catalog")
    write_project_catalog([], resolved_catalog)
    apply_runtime_catalog([])
    return report

