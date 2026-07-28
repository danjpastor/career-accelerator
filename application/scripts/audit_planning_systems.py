from __future__ import annotations

"""End-to-end release audit for linked planning and DataCamp progress systems."""

from datetime import date, timedelta
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "application"))

from career_app.data.datacamp_curriculum import DATACAMP_CHAPTERS  # noqa: E402
from career_app.database import state  # noqa: E402
from career_app.services import (  # noqa: E402
    completion_contract,
    datacamp,
    task_icons,
    task_workspace,
    tracks,
    unified_tasks,
)

DB_PATH = ROOT / "data" / "career_accelerator.db"
ASSET_ROOT = ROOT / "application" / "assets"


def _connection(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _copy_database(name: str) -> tuple[sqlite3.Connection, Path]:
    folder = Path(tempfile.mkdtemp(prefix=f"career-accelerator-{name}-"))
    target = folder / "career_accelerator.db"
    shutil.copy2(DB_PATH, target)
    return _connection(target), target


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _current_state_audit(errors: list[str]) -> None:
    conn, _ = _copy_database("planner")
    try:
        datacamp.reconcile(conn)
        current = state(conn)
        tracks.sync_all(conn, current)
        datacamp.reconcile(conn)
        current = state(conn)
        week = int(current["current_week"])

        _assert(conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity check failed", errors)
        _assert(not conn.execute("PRAGMA foreign_key_check").fetchall(), "Foreign-key violations found", errors)

        health = tracks.health_report(conn, current)
        _assert(bool(health.get("healthy")), f"Track health failed: {health.get('issues')}", errors)

        tasks = unified_tasks.all_tasks(conn, week)
        chapters = [task for task in tasks if task.get("kind") == "datacamp_chapter"]
        _assert(len(chapters) == len(DATACAMP_CHAPTERS), "DataCamp task/progress count mismatch", errors)
        _assert(
            all(task_icons.key_for_task(task, week) == "datacamp" for task in chapters),
            "A DataCamp chapter still resolves to a generic subject icon",
            errors,
        )
        _assert(
            task_icons.path_for_key(ASSET_ROOT, "datacamp").is_file(),
            "DataCamp logo asset is missing",
            errors,
        )

        # Rebuild only the audit copy's current-day planner snapshot.
        focus_date = date.today().isoformat()
        conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (focus_date,))
        conn.execute("DELETE FROM settings WHERE key=?", (f"daily_focus_snapshot_v2:{focus_date}",))
        conn.commit()
        focus = unified_tasks.daily_plan(conn, week)
        next_items = unified_tasks.next_tasks(conn, week)
        coming = unified_tasks.coming_up(conn, week)
        focus_ids = {int(item["id"]) for item in focus}
        next_ids = {int(item["id"]) for item in next_items}
        _assert(len(focus) <= unified_tasks.MAX_FOCUS_TASKS == 5, "Today’s Focus limit/linkage failed", errors)
        _assert(len(next_items) <= unified_tasks.MAX_NEXT_TASKS == 4, "Next Tasks limit/linkage failed", errors)
        expected_focus_prefix = [
            int(item["id"])
            for item in focus[: unified_tasks.MAX_NEXT_TASKS]
        ]
        actual_next_prefix = [
            int(item["id"])
            for item in next_items[: len(expected_focus_prefix)]
        ]
        _assert(
            actual_next_prefix == expected_focus_prefix,
            "Next Tasks does not begin with the active Today’s Focus assignments",
            errors,
        )
        locked_focus = [item for item in focus if not bool(item.get("ready"))]
        _assert(
            all(
                item.get("kind") == "datacamp_chapter"
                and str(item.get("prerequisite_reason") or "").startswith("Complete ")
                for item in locked_focus
            ),
            "A non-DataCamp or future-scheduled lock entered Today’s Focus",
            errors,
        )
        _assert(
            all(
                bool(item.get("ready"))
                or (
                    item.get("kind") == "datacamp_chapter"
                    and str(item.get("prerequisite_reason") or "").startswith("Complete ")
                )
                for item in next_items
            ),
            "Next Tasks contains an unsupported locked item",
            errors,
        )
        google_ready = [item for item in unified_tasks.ready_tasks(conn, week) if item.get("kind") == "google"]
        if google_ready and focus:
            _assert(focus[0].get("kind") == "google", "Google Certificate is not first priority", errors)
        _assert(all(not bool(item.get("completed")) for item in coming), "Completed task entered Coming Soon", errors)

        sprint_items = task_workspace.current_sprint_items(conn, week)
        sprint_chapters = [
            item for item in sprint_items
            if item.get("section") == "DataCamp"
        ]
        _assert(bool(sprint_chapters), "Current Sprint omitted DataCamp chapters", errors)
        _assert(
            all(not str(item.get("label") or "").startswith("DataCamp —") for item in sprint_chapters),
            "Current Sprint still shows the redundant DataCamp title prefix",
            errors,
        )

        summary = completion_contract.summary(conn, current)
        _assert(bool(summary.get("active")), "90-day completion contract is inactive", errors)

        row = conn.execute("SELECT weekly_target,metadata FROM track_state WHERE track_key='datacamp'").fetchone()
        metadata = json.loads(row["metadata"] or "{}") if row else {}
        expected_weekly = sum(chapter.week == week for chapter in DATACAMP_CHAPTERS)
        _assert(row is not None and int(row["weekly_target"]) == expected_weekly, "DataCamp weekly target is not linked to the current curriculum week", errors)
        _assert(int(metadata.get("weekly_target", -1)) == expected_weekly, "DataCamp status metadata has a stale weekly target", errors)

        ready = datacamp.current_ready_task(conn)
        if ready is not None:
            task_id = int(ready["id"])
            before = conn.execute("SELECT completed FROM sprint_tasks WHERE id=?", (task_id,)).fetchone()[0]
            url = datacamp.chapter_url_for_task(conn, task_id)
            after = conn.execute("SELECT completed FROM sprint_tasks WHERE id=?", (task_id,)).fetchone()[0]
            _assert(bool(url and url.startswith("https://campus.datacamp.com/courses/")), "Open does not resolve to an exact DataCamp Campus chapter", errors)
            _assert(before == after == 0, "Resolving/opening a DataCamp URL changed completion", errors)

            conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
            conn.execute("UPDATE task_metadata SET status='Completed',deferred_until=NULL WHERE task_id=?", (task_id,))
            conn.commit()
            datacamp.mark_task_complete(conn, task_id)
            # Match the live checkbox path: provider evidence must survive the
            # central track-repair pass before DataCamp reconciliation.
            tracks.sync_all(conn, state(conn))
            datacamp.reconcile(conn)
            completed_row = conn.execute(
                "SELECT completed FROM sprint_tasks WHERE id=?",
                (task_id,),
            ).fetchone()[0]
            progress = conn.execute("SELECT status FROM datacamp_chapter_progress WHERE task_id=?", (task_id,)).fetchone()[0]
            _assert(
                int(completed_row) == 1 and progress == "Completed",
                "Live checkbox completion was reset by track repair",
                errors,
            )
            history = [item for item in tracks.completion_history(conn) if item.get("task_id") == task_id]
            _assert(bool(history and history[0].get("track_key") == "datacamp"), "Completion History lost the DataCamp provider identity", errors)
            tracks.undo_completion(conn, current, task_id=task_id)
            undone = conn.execute(
                """SELECT s.completed,m.status,p.status AS progress_status,p.completed_date
                   FROM sprint_tasks s
                   JOIN task_metadata m ON m.task_id=s.id
                   JOIN datacamp_chapter_progress p ON p.task_id=s.id
                   WHERE s.id=?""",
                (task_id,),
            ).fetchone()
            _assert(
                int(undone["completed"]) == 0
                and undone["status"] == "Not Started"
                and undone["progress_status"] == "Not Started"
                and undone["completed_date"] is None,
                "Undo did not reset every DataCamp completion layer",
                errors,
            )

        counts_before = tuple(
            conn.execute(query).fetchone()[0]
            for query in (
                "SELECT COUNT(*) FROM sprint_tasks",
                "SELECT COUNT(*) FROM datacamp_chapter_progress",
                "SELECT COUNT(*) FROM track_state",
            )
        )
        datacamp.reconcile(conn)
        datacamp.reconcile(conn)
        counts_after = tuple(
            conn.execute(query).fetchone()[0]
            for query in (
                "SELECT COUNT(*) FROM sprint_tasks",
                "SELECT COUNT(*) FROM datacamp_chapter_progress",
                "SELECT COUNT(*) FROM track_state",
            )
        )
        _assert(counts_before == counts_after, "DataCamp reconciliation is not idempotent", errors)
    finally:
        conn.close()


def _same_week_catchup_audit(errors: list[str]) -> None:
    conn, _ = _copy_database("catchup")
    try:
        # Beginning Week 1 yesterday makes Chapter 1 overdue and Chapter 2 due today.
        start = (date.today() - timedelta(days=1)).isoformat()
        conn.execute("UPDATE program_state SET current_week=1,start_date=? WHERE id=1", (start,))
        conn.execute("DELETE FROM daily_focus")
        conn.execute("DELETE FROM settings WHERE key LIKE 'daily_focus_snapshot_v2:%'")
        conn.execute("UPDATE sprint_tasks SET completed=0 WHERE id IN (SELECT task_id FROM task_metadata WHERE managed_key LIKE 'datacamp:%')")
        conn.execute("UPDATE task_metadata SET status='Not Started' WHERE managed_key LIKE 'datacamp:%'")
        conn.execute("UPDATE datacamp_chapter_progress SET status='Not Started',completed_date=NULL")
        conn.commit()
        datacamp.reconcile(conn)

        tasks = unified_tasks.all_tasks(conn, 1)
        first = next(item for item in tasks if item.get("managed_key") == "datacamp:w01_intro_sheets_01")
        second = next(item for item in tasks if item.get("managed_key") == "datacamp:w01_intro_sheets_02")
        _assert(bool(first.get("ready") and first.get("is_catch_up")), "Yesterday’s unfinished chapter did not become Catch-Up", errors)
        _assert(not bool(second.get("ready")), "Later chapter unlocked before the earlier chapter", errors)

        focus = unified_tasks.daily_plan(conn, 1)
        _assert(
            any(item["id"] == first["id"] and item.get("focus_kind") == "catch_up" for item in focus),
            "Same-week overdue chapter entered the new-work quota instead of Catch-Up",
            errors,
        )
        _assert(
            any(
                item["id"] == second["id"]
                and not bool(item.get("ready"))
                and str(item.get("prerequisite_reason") or "").startswith("Complete ")
                for item in focus
            ),
            "The due next DataCamp chapter is not shown as a locked Focus row",
            errors,
        )
        focus_ids = [int(item["id"]) for item in focus]
        _assert(
            focus_ids.index(first["id"]) < focus_ids.index(second["id"]),
            "The prerequisite chapter is not ordered before its locked successor",
            errors,
        )
        snapshot_row = conn.execute(
            "SELECT value FROM settings WHERE key=?",
            (f"daily_focus_snapshot_v2:{date.today().isoformat()}",),
        ).fetchone()
        snapshot = json.loads(snapshot_row["value"] or "{}")
        new_ids = {int(item.get("task_id") or 0) for item in snapshot.get("new_assignments", [])}
        _assert(first["id"] not in new_ids, "Catch-Up chapter consumed a new-task snapshot slot", errors)

        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (first["id"],))
        conn.execute("UPDATE task_metadata SET status='Completed',deferred_until=NULL WHERE task_id=?", (first["id"],))
        conn.commit()
        datacamp.mark_task_complete(conn, first["id"])
        datacamp.reconcile(conn)
        focus_after = unified_tasks.daily_plan(conn, 1)
        next_after = unified_tasks.next_tasks(conn, 1)
        second_after = next((item for item in focus_after if item["id"] == second["id"]), None)
        _assert(
            second_after is not None and bool(second_after.get("ready")),
            "The already-visible locked chapter did not become actionable after its prerequisite completed",
            errors,
        )
        expected_prefix = [
            int(item["id"])
            for item in focus_after[: unified_tasks.MAX_NEXT_TASKS]
        ]
        actual_prefix = [
            int(item["id"])
            for item in next_after[: len(expected_prefix)]
        ]
        _assert(
            actual_prefix == expected_prefix,
            "Next Tasks stopped mirroring the remaining active focus assignments",
            errors,
        )
        _assert(
            second["id"] in {item["id"] for item in unified_tasks.ready_tasks(conn, 1)},
            "Completing Catch-Up did not unlock the next due-today chapter",
            errors,
        )
    finally:
        conn.close()


def main() -> int:
    errors: list[str] = []
    _assert(DB_PATH.is_file(), f"Packaged database is missing: {DB_PATH}", errors)
    _assert((ASSET_ROOT / "task_icons" / "datacamp.svg").is_file(), "DataCamp logo file is missing", errors)
    widgets_source = (ROOT / "application" / "career_app" / "ui" / "widgets.py").read_text(encoding="utf-8")
    main_source = (ROOT / "application" / "career_app" / "main.py").read_text(encoding="utf-8")
    _assert(
        "self.checkbox = VisibleCheckBox(checked=checked)" in widgets_source,
        "Today’s Focus rows do not construct a visible completion checkbox",
        errors,
    )
    _assert(
        "on_toggle=on_toggle" in main_source
        and "self.queue_dashboard_task_completion(" in main_source,
        "Today’s Focus checkbox is not linked to canonical dashboard completion",
        errors,
    )
    completion_segment = main_source[
        main_source.index("    def queue_dashboard_task_completion("):
        main_source.index("    def show_dashboard_tomorrow_preview(")
    ]
    _assert(
        'refresh_scope="dashboard"' in completion_segment,
        "Dashboard checkboxes still use the blocking full-refresh completion path",
        errors,
    )
    _assert(
        "self.refresh_git()" not in completion_segment,
        "Dashboard checkbox completion still invokes Git status",
        errors,
    )
    _assert(
        'QLabel("COMING SOON")' in main_source,
        "Next Tasks is missing the Coming Soon section divider label",
        errors,
    )
    _assert(
        'if is_catch_up and is_datacamp' in main_source,
        "DataCamp Catch-Up metadata is not shortened",
        errors,
    )
    _assert(
        "QTimer.singleShot(0, self._refresh_after_session_log)" in main_source
        and "self.refresh_all()" not in main_source[
            main_source.index("    def save_session("):
            main_source.index("    def add_evidence(")
        ],
        "Study Session logging still uses the blocking full-application refresh",
        errors,
    )
    focus_segment = main_source[
        main_source.index("        def add_focus_item(item):"):
        main_source.index("        if focus_summary[")
    ]
    next_tasks_segment = main_source[
        main_source.index("    def _refresh_dashboard_next_tasks(self, week):"):
        main_source.index("    def refresh_dashboard(")
    ]
    _assert(
        'locked = bool(not completed and not item.get("ready", True))' in focus_segment
        and 'if locked:' in focus_segment
        and 'locked=locked' in focus_segment,
        "Locked DataCamp focus rows are not rendered as disabled prerequisite guidance",
        errors,
    )
    _assert(
        'locked_focus_items' in next_tasks_segment
        and '[*locked_focus_items, *coming_soon]' in next_tasks_segment
        and 'visible_items.append(("coming_soon", item))' in next_tasks_segment,
        "Locked Focus chapters are not grouped beneath Coming Soon in Next Tasks",
        errors,
    )
    _assert(
        'f"{week_hours:.2f}h"' in main_source,
        "Study-time totals are not formatted to two decimal places",
        errors,
    )
    if not errors:
        _current_state_audit(errors)
        _same_week_catchup_audit(errors)

    if errors:
        print("Planning systems audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Planning systems audit passed")
    print("- Ready Focus work stays above the Next Tasks divider; locked Focus previews are grouped under Coming Soon")
    print("- Today’s Focus and Next Tasks both expose the canonical non-blocking completion flow")
    print("- Coming Soon has a separate divider and DataCamp Catch-Up metadata stays compact")
    print("- Google remains first priority; due locked DataCamp chapters stay visible and sequential")
    print("- Study Session logging avoids the full-application refresh and study totals use two decimals")
    print("- DataCamp open, complete, history, undo, weekly totals, and portfolio gates share one progress source")
    print("- all DataCamp chapter tasks resolve to the DataCamp logo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
