"""One-time migration for chronological Applied Lab numbering.

The migration preserves learner progress while converting the legacy category-first
numbers to the actual adaptive unlock sequence introduced in v10.37.0.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from career_app.data.applied_exercises import (
    APPLIED_EXERCISES,
    APPLIED_LAB_NUMBERING_VERSION,
    LEGACY_TO_CURRENT_LAB_NUMBER,
)

SETTING_KEY = "applied_lab_numbering_version"


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _legacy_label_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for item in APPLIED_EXERCISES.values():
        current = str(item["label"])
        for alias in item.get("aliases", []):
            if str(alias).startswith("Complete Applied Lab "):
                result[str(alias)] = current
    return result


def _current_number_from_legacy_label(label: str) -> int | None:
    current_by_legacy = _legacy_label_map()
    current = current_by_legacy.get(str(label))
    if current is None:
        return None
    match = re.match(r"^Complete Applied Lab (\d{2}):", current)
    return int(match.group(1)) if match else None


def _current_number_from_any_label(label: object) -> int | None:
    wanted = str(label or "").strip().casefold()
    if not wanted:
        return None
    for number, item in APPLIED_EXERCISES.items():
        labels = [str(item.get("label") or ""), *[str(v) for v in item.get("aliases", [])]]
        if any(candidate.strip().casefold() == wanted for candidate in labels):
            return int(number)
    return None


def _remap_lab_key(value: object) -> tuple[str, int | None]:
    text = str(value or "")
    if not text.startswith("lab:"):
        return text, None
    try:
        legacy = int(text.split(":", 1)[1])
    except ValueError:
        return text, None
    current = LEGACY_TO_CURRENT_LAB_NUMBER.get(legacy)
    if current is None:
        return text, None
    return f"lab:{current:02d}", current


def _remap_progress(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, "applied_exercise_progress"):
        return 0
    rows = conn.execute(
        "SELECT exercise_number FROM applied_exercise_progress"
    ).fetchall()
    legacy_numbers = {int(row[0]) for row in rows}
    changed = 0
    for legacy, current in LEGACY_TO_CURRENT_LAB_NUMBER.items():
        if legacy == current or legacy not in legacy_numbers:
            continue
        conn.execute(
            "UPDATE applied_exercise_progress SET exercise_number=? WHERE exercise_number=?",
            (-1000 - int(legacy), int(legacy)),
        )
        changed += 1
    for legacy, current in LEGACY_TO_CURRENT_LAB_NUMBER.items():
        if legacy == current or legacy not in legacy_numbers:
            continue
        conn.execute(
            "UPDATE applied_exercise_progress SET exercise_number=? WHERE exercise_number=?",
            (int(current), -1000 - int(legacy)),
        )
    return changed


def _remap_tasks(conn: sqlite3.Connection) -> int:
    changed = 0
    labels = _legacy_label_map()
    if _table_exists(conn, "sprint_tasks"):
        for old_label, new_label in labels.items():
            changed += max(
                0,
                conn.execute(
                    "UPDATE sprint_tasks SET label=? WHERE label=?",
                    (new_label, old_label),
                ).rowcount,
            )
    if _table_exists(conn, "track_tasks"):
        row = conn.execute(
            "SELECT target_key,source_label,linked_entity_id FROM track_tasks WHERE track_key='applied'"
        ).fetchone()
        if row is not None:
            target = str(row[0] or "")
            legacy = None
            if target.startswith("lab:"):
                try:
                    legacy = int(target.split(":", 1)[1])
                except ValueError:
                    legacy = None
            if legacy in LEGACY_TO_CURRENT_LAB_NUMBER:
                current = LEGACY_TO_CURRENT_LAB_NUMBER[legacy]
                item = APPLIED_EXERCISES[current]
                conn.execute(
                    """UPDATE track_tasks
                       SET target_key=?,source_label=?,linked_entity_id=?,updated_at=CURRENT_TIMESTAMP
                       WHERE track_key='applied'""",
                    (f"lab:{current:02d}", item["label"], current),
                )
                changed += 1
    return changed


def _remap_daily_focus(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, "daily_focus"):
        return 0
    changed = 0
    labels = _legacy_label_map()
    for old_label, new_label in labels.items():
        changed += max(
            0,
            conn.execute(
                "UPDATE daily_focus SET title=? WHERE title=?",
                (new_label, old_label),
            ).rowcount,
        )
    rows = conn.execute(
        "SELECT id,target_key,source_key FROM daily_focus WHERE track_key='applied'"
    ).fetchall()
    for row in rows:
        target = str(row[1] or "")
        source = str(row[2] or "")
        new_target, current = _remap_lab_key(target)
        source_basis = source if source.startswith("lab:") else target
        new_source, source_current = _remap_lab_key(source_basis)
        current = current or source_current
        if current is None:
            continue
        item = APPLIED_EXERCISES[current]
        conn.execute(
            """UPDATE daily_focus
               SET target_key=?,source_key=?,title=?
               WHERE id=?""",
            (new_target, new_source, item["label"], int(row[0])),
        )
        changed += 1
    return changed


def _remap_evidence_and_achievements(conn: sqlite3.Connection) -> int:
    changed = 0
    labels = _legacy_label_map()
    title_map = {
        old.replace("Complete ", "", 1): new.replace("Complete ", "", 1)
        for old, new in labels.items()
    }
    if _table_exists(conn, "evidence"):
        for old, new in title_map.items():
            changed += max(
                0,
                conn.execute(
                    "UPDATE OR IGNORE evidence SET source_name=? WHERE source_name=?",
                    (new, old),
                ).rowcount,
            )
            conn.execute("DELETE FROM evidence WHERE source_name=?", (old,))
    if _table_exists(conn, "achievements"):
        rows = conn.execute(
            "SELECT id,title,description FROM achievements"
        ).fetchall()
        for row in rows:
            title = str(row[1] or "")
            description = str(row[2] or "")
            new_title = title
            new_description = description
            for old, new in title_map.items():
                new_title = new_title.replace(old, new)
                new_description = new_description.replace(old, new)
            if (new_title, new_description) != (title, description):
                conn.execute(
                    "UPDATE achievements SET title=?,description=? WHERE id=?",
                    (new_title, new_description, int(row[0])),
                )
                changed += 1
    return changed


def _remap_settings(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, "settings"):
        return 0
    changed = 0
    changed += max(
        0,
        conn.execute(
            "UPDATE settings SET value='Google Sheets' WHERE key='applied_branch_pin' AND value='Excel'"
        ).rowcount,
    )
    rows = conn.execute(
        "SELECT key,value FROM settings WHERE key LIKE 'content_unlock_notified:applied_lab:%'"
    ).fetchall()
    for row in rows:
        key = str(row[0])
        try:
            legacy = int(key.rsplit(":", 1)[1])
        except ValueError:
            continue
        current = LEGACY_TO_CURRENT_LAB_NUMBER.get(legacy)
        if current is None:
            continue
        new_key = f"content_unlock_notified:applied_lab:{current:02d}"
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (new_key, str(row[1])),
        )
        if new_key != key:
            conn.execute("DELETE FROM settings WHERE key=?", (key,))
        changed += 1

    # Frozen daily snapshots store their own target identity. Remap those
    # identities in the same transaction as daily_focus so the planner never
    # treats a renumbered lab as a brand-new assignment occupying the same slot.
    snapshots = conn.execute(
        "SELECT key,value FROM settings WHERE key LIKE 'daily_focus_snapshot_v2:%'"
    ).fetchall()
    for row in snapshots:
        try:
            payload = json.loads(str(row[1] or "{}"))
        except Exception:
            continue
        assignments = payload.get("new_assignments") if isinstance(payload, dict) else None
        if not isinstance(assignments, list):
            continue
        remapped: list[dict] = []
        seen: set[str] = set()
        snapshot_changed = False
        for raw in assignments:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            identity = str(item.get("identity") or "")
            target = str(item.get("target_key") or "")
            basis = target if target.startswith("lab:") else identity
            new_key, current = _remap_lab_key(basis)
            if current is not None:
                catalog = APPLIED_EXERCISES[current]
                item["identity"] = new_key
                item["target_key"] = new_key
                item["track_key"] = "applied"
                item["title"] = str(catalog["label"])
                snapshot_changed = True
            item_identity = str(item.get("identity") or "")
            if item_identity and item_identity in seen:
                snapshot_changed = True
                continue
            if item_identity:
                seen.add(item_identity)
            remapped.append(item)
        if snapshot_changed:
            payload["new_assignments"] = remapped[:5]
            conn.execute(
                "UPDATE settings SET value=? WHERE key=?",
                (json.dumps(payload, sort_keys=True), str(row[0])),
            )
            changed += 1
    return changed


def _repair_current_focus_references(conn: sqlite3.Connection) -> tuple[int, int]:
    """Repair v10.37.0 focus rows after a partially completed renumbering.

    The original migration could commit the new ``target_key`` while leaving
    ``source_key`` and the frozen snapshot on the legacy lab number.  Once the
    numbering-version setting is present, legacy mapping must not be applied a
    second time because the mapping is a permutation.  This repair treats the
    current target/title as authoritative and only synchronizes identities.
    """
    focus_changed = 0
    snapshot_changed_count = 0
    task_targets: dict[int, tuple[str, int]] = {}

    if _table_exists(conn, "track_tasks"):
        for row in conn.execute(
            "SELECT task_id,target_key,source_label FROM track_tasks WHERE track_key='applied'"
        ).fetchall():
            target = str(row[1] or "")
            number = _current_number_from_any_label(row[2])
            if number is None and target.startswith("lab:"):
                try:
                    candidate = int(target.split(":", 1)[1])
                except ValueError:
                    candidate = 0
                if candidate in APPLIED_EXERCISES:
                    number = candidate
            if number is not None:
                task_targets[int(row[0])] = (f"lab:{number:02d}", number)

    if _table_exists(conn, "daily_focus"):
        rows = conn.execute(
            "SELECT id,task_id,target_key,source_key,title FROM daily_focus WHERE track_key='applied'"
        ).fetchall()
        for row in rows:
            task_id = int(row[1]) if row[1] is not None else None
            number = _current_number_from_any_label(row[4])
            target = str(row[2] or "")
            if number is None and task_id is not None and task_id in task_targets:
                _, number = task_targets[task_id]
            if number is None and target.startswith("lab:"):
                try:
                    candidate = int(target.split(":", 1)[1])
                except ValueError:
                    candidate = 0
                if candidate in APPLIED_EXERCISES:
                    number = candidate
            if number is None:
                continue
            current_key = f"lab:{number:02d}"
            current_title = str(APPLIED_EXERCISES[number]["label"])
            if (target, str(row[3] or ""), str(row[4] or "")) != (
                current_key, current_key, current_title
            ):
                conn.execute(
                    "UPDATE daily_focus SET target_key=?,source_key=?,title=? WHERE id=?",
                    (current_key, current_key, current_title, int(row[0])),
                )
                focus_changed += 1
            if task_id is not None:
                task_targets[task_id] = (current_key, number)

    if not _table_exists(conn, "settings"):
        return focus_changed, snapshot_changed_count

    snapshots = conn.execute(
        "SELECT key,value FROM settings WHERE key LIKE 'daily_focus_snapshot_v2:%'"
    ).fetchall()
    for row in snapshots:
        try:
            payload = json.loads(str(row[1] or "{}"))
        except Exception:
            continue
        assignments = payload.get("new_assignments") if isinstance(payload, dict) else None
        if not isinstance(assignments, list):
            continue
        remapped: list[dict] = []
        seen: set[str] = set()
        changed = False
        for raw in assignments:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            task_id = item.get("task_id")
            try:
                task_id_int = int(task_id) if task_id is not None else None
            except (TypeError, ValueError):
                task_id_int = None
            number = _current_number_from_any_label(item.get("title"))
            if number is None and task_id_int is not None and task_id_int in task_targets:
                _, number = task_targets[task_id_int]
            target = str(item.get("target_key") or "")
            identity = str(item.get("identity") or "")
            if number is None and target.startswith("lab:"):
                try:
                    candidate = int(target.split(":", 1)[1])
                except ValueError:
                    candidate = 0
                if candidate in APPLIED_EXERCISES:
                    number = candidate
            # A legacy snapshot may have only the old title/identity. The alias
            # lookup above resolves that safely without reinterpreting current
            # lab numbers through the legacy permutation.
            if number is not None:
                current_key = f"lab:{number:02d}"
                current_title = str(APPLIED_EXERCISES[number]["label"])
                before = (identity, target, str(item.get("title") or ""), str(item.get("track_key") or ""))
                item["identity"] = current_key
                item["target_key"] = current_key
                item["track_key"] = "applied"
                item["title"] = current_title
                if before != (current_key, current_key, current_title, "applied"):
                    changed = True
            item_identity = str(item.get("identity") or "")
            if item_identity and item_identity in seen:
                changed = True
                continue
            if item_identity:
                seen.add(item_identity)
            remapped.append(item)
        if changed:
            payload["new_assignments"] = remapped[:5]
            conn.execute(
                "UPDATE settings SET value=? WHERE key=?",
                (json.dumps(payload, sort_keys=True), str(row[0])),
            )
            snapshot_changed_count += 1
    return focus_changed, snapshot_changed_count


def _submission_suffix(item: dict) -> str:
    suffix = Path(str(item.get("starter_filename") or "submission.md")).suffix
    slug = str(item.get("submission_slug") or re.sub(r"^\d+_", "", str(item["slug"])))
    return slug + suffix


def _remap_files(root: Path) -> int:
    submissions = Path(root) / "practice" / "applied" / "submissions"
    if not submissions.exists():
        return 0
    changed = 0
    legacy_slugs = {
        7: "07_excel_analyst_workbook",
        **{
            legacy: str(APPLIED_EXERCISES[current]["slug"])
            for legacy, current in LEGACY_TO_CURRENT_LAB_NUMBER.items()
            if legacy != 7
        },
    }
    for legacy, current in LEGACY_TO_CURRENT_LAB_NUMBER.items():
        item = APPLIED_EXERCISES[current]
        suffix = Path(str(item.get("starter_filename") or "submission.md")).suffix
        old_path = submissions / f"{legacy:02d}_{legacy_slugs[legacy]}{suffix}"
        new_path = submissions / f"{current:02d}_{_submission_suffix(item)}"
        if old_path.exists() and old_path != new_path and not new_path.exists():
            old_path.rename(new_path)
            changed += 1
    legacy_state = submissions / "07_excel_workbook_studio.json"
    current_state = submissions / "01_google_sheets_studio.json"
    if legacy_state.exists() and not current_state.exists():
        try:
            data = json.loads(legacy_state.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict):
            # Preserve stage evidence, but an Excel file is not treated as the new Google Sheet artifact.
            data["spreadsheet_id"] = ""
            data["spreadsheet_url"] = ""
            data["artifact_path"] = ""
            current_state.write_text(json.dumps(data, indent=2), encoding="utf-8")
            changed += 1
    old_shot = submissions / "07_management_summary.png"
    new_shot = submissions / "01_management_summary.png"
    if old_shot.exists() and not new_shot.exists():
        old_shot.rename(new_shot)
        changed += 1
    return changed


def reconcile(conn: sqlite3.Connection, root: Path) -> dict[str, int]:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (SETTING_KEY,)).fetchone()
    current_version = 0
    if row is not None:
        try:
            current_version = int(row[0])
        except (TypeError, ValueError):
            current_version = 0

    conn.execute("SAVEPOINT applied_lab_numbering")
    try:
        if current_version >= APPLIED_LAB_NUMBERING_VERSION:
            focus, settings = _repair_current_focus_references(conn)
            result = {
                "progress": 0,
                "tasks": 0,
                "focus": focus,
                "evidence": 0,
                "settings": settings,
                "files": 0,
            }
        else:
            result = {
                "progress": _remap_progress(conn),
                "tasks": _remap_tasks(conn),
                "focus": _remap_daily_focus(conn),
                "evidence": _remap_evidence_and_achievements(conn),
                "settings": _remap_settings(conn),
                "files": _remap_files(Path(root)),
            }
            repaired_focus, repaired_settings = _repair_current_focus_references(conn)
            result["focus"] += repaired_focus
            result["settings"] += repaired_settings
            conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (SETTING_KEY, str(APPLIED_LAB_NUMBERING_VERSION)),
            )
        conn.execute("RELEASE SAVEPOINT applied_lab_numbering")
        return result
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT applied_lab_numbering")
        conn.execute("RELEASE SAVEPOINT applied_lab_numbering")
        raise

