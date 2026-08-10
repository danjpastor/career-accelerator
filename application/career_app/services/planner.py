from __future__ import annotations

"""Unified Career Accelerator planner.

v10.27 replaces the overlapping adaptive, Get Ahead, Added Today, manual-focus,
and per-track recommendation planners with one deterministic runtime.  The
legacy implementation is isolated in :mod:`legacy_planner` only for durable
migration helpers and task-completion compatibility.
"""

from datetime import date
import re

from career_app.services import legacy_planner as _legacy
from career_app.services import unified_tasks


# Durable compatibility helpers. These functions update existing task/progress
# records but do not choose Today’s Focus or Next Tasks.
seed = _legacy.seed
sync_google_course_progress = _legacy.sync_google_course_progress
repair_persisted_planner_data = _legacy.repair_persisted_planner_data
defer = _legacy.defer
mark_focus_task_completed = _legacy.mark_focus_task_completed


def refresh_due_track_focus(conn, week, max_items=5):
    unified_tasks.migrate_runtime(conn, int(week))
    return unified_tasks.daily_plan(conn, int(week), max_items=max_items)


def intelligent_focus_plan(conn, week, guide, state, max_items=5):
    del guide, state
    return unified_tasks.daily_plan(conn, int(week), max_items=max_items)


def next_tasks(conn, week):
    return unified_tasks.next_tasks(conn, int(week), limit=4)


def coming_up_tasks(conn, week, limit=3):
    return unified_tasks.coming_up(conn, int(week), limit=int(limit))


def focus_day_summary(items, *, conn=None, week=None):
    del week
    active = list(items or [])
    if conn is None:
        return {
            "total_count": len(active),
            "completed_count": 0,
            "planned_minutes": sum(int(item.get("estimated_minutes") or 0) for item in active),
            "completed_titles": [],
            "session_count": 0,
            "active_extra": None,
            "all_base_complete": False,
            "inferred_empty_complete": False,
        }
    return unified_tasks.completion_summary(conn, active)


def rebuild_today_snapshot(conn, week, guide, state, max_items=5):
    del guide, state
    today = date.today().isoformat()
    conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (today,))
    conn.execute(
        "DELETE FROM settings WHERE key=?",
        (f"daily_focus_snapshot_v2:{today}",),
    )
    conn.commit()
    items = unified_tasks.daily_plan(conn, int(week), max_items=max_items)
    return {"focus_date": today, "created": len(items), "items": items}


# BEGIN SQL INTERVIEW COMPLETION ROLLOVER RECONCILIATION V10.46.20
def _sql_interview_completion_key(value):
    """Normalize a SQL interview title without changing its durable record."""
    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").casefold(),
    )
    normalized = " ".join(normalized.split())
    for prefix in (
        "solve ",
        "complete sql interview problem ",
        "complete interview problem ",
        "complete ",
        "practice ",
    ):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            break
    return normalized


def reconcile_completed_sql_interview_tasks(conn):
    """Overlay durable SQL Practice completion onto every concrete task row.

    SQL interview completion lives durably in ``sql_practice``.  Sprint rollover
    and adaptive-track synchronization may recreate another concrete task row for
    the same logical problem.  A recreated row must inherit the durable completed
    state before Today’s Focus, Next Tasks, catch-up, or Get Ahead are derived.
    """
    try:
        completed_rows = conn.execute(
            """SELECT title,completed_date
               FROM sql_practice
               WHERE platform='DataLemur'
                 AND status='Completed'"""
        ).fetchall()
    except Exception:
        return 0

    completed_by_key = {}
    for completed_row in completed_rows:
        key = _sql_interview_completion_key(completed_row["title"])
        if key:
            completed_by_key[key] = completed_row
    if not completed_by_key:
        return 0

    try:
        task_rows = conn.execute(
            """SELECT
                   s.id,
                   s.label,
                   s.completed,
                   m.status,
                   m.category,
                   m.managed_key,
                   tt.track_key,
                   tt.target_key
               FROM sprint_tasks AS s
               JOIN task_metadata AS m
                 ON m.task_id=s.id
               LEFT JOIN track_tasks AS tt
                 ON tt.task_id=s.id"""
        ).fetchall()
    except Exception:
        return 0

    changed = 0
    processed_task_ids = set()
    for row in task_rows:
        task_id = int(row["id"])
        if task_id in processed_task_ids:
            continue

        track_key = str(row["track_key"] or "").casefold()
        category = str(row["category"] or "").casefold()
        target_key = str(row["target_key"] or "")
        managed_key = str(row["managed_key"] or "")
        label = str(row["label"] or "")

        # Restrict reconciliation to SQL-shaped tasks.  This prevents an
        # unrelated task with coincidental wording from inheriting SQL progress.
        if track_key != "sql" and category != "sql":
            continue

        candidates = []
        if (
            track_key == "sql"
            and target_key.casefold().startswith("problem:")
        ):
            candidates.append(target_key.split(":", 1)[1])
        managed_prefix = "roadmap_v1026:sql:"
        if managed_key.casefold().startswith(managed_prefix):
            candidates.append(managed_key[len(managed_prefix):])
        candidates.append(label)

        matched = None
        for candidate in candidates:
            candidate_key = _sql_interview_completion_key(candidate)
            if not candidate_key:
                continue
            matched = completed_by_key.get(candidate_key)
            if matched is not None:
                break
            # Compatibility for older labels that prepend a category/source
            # token before the exact interview title.
            for completed_key, completed_row in completed_by_key.items():
                if candidate_key.endswith(" " + completed_key):
                    matched = completed_row
                    break
            if matched is not None:
                break

        if matched is None:
            continue

        processed_task_ids.add(task_id)
        task_changed = False
        if not bool(row["completed"]):
            conn.execute(
                "UPDATE sprint_tasks SET completed=1 WHERE id=?",
                (task_id,),
            )
            task_changed = True
        if str(row["status"] or "") != "Completed":
            conn.execute(
                """UPDATE task_metadata
                   SET status='Completed',
                       deferred_until=NULL
                   WHERE task_id=?""",
                (task_id,),
            )
            task_changed = True

        # A stored daily-focus row may exist for the stale concrete ID.  Keep
        # its historical date and simply mark the row reconciled when possible.
        if task_changed:
            try:
                completed_date = (
                    matched["completed_date"]
                    or date.today().isoformat()
                )
                conn.execute(
                    """UPDATE daily_focus
                       SET completed_at=COALESCE(completed_at,?)
                       WHERE task_id=?""",
                    (completed_date, task_id),
                )
            except Exception:
                pass
            changed += 1

    if changed:
        conn.commit()
    return changed
# END SQL INTERVIEW COMPLETION ROLLOVER RECONCILIATION V10.46.20

def available(conn, week):
    reconcile_completed_sql_interview_tasks(conn)
    return unified_tasks.ready_tasks(conn, int(week))


def make_plan(conn, week, available_minutes, energy):
    del energy
    remaining = max(0, int(available_minutes or 0))
    selected = []
    for task in unified_tasks.ready_tasks(conn, int(week)):
        minutes = int(task.get("estimated_minutes") or 30)
        if selected and minutes > remaining:
            continue
        selected.append(task)
        remaining = max(0, remaining - minutes)
        if remaining <= 0:
            break
    return selected, remaining


def task_schedule_eligibility(conn, task_id, week):
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        return {"eligible": False, "ready": False, "reason": "Task not found."}
    task = next(
        (
            item
            for item in unified_tasks.all_tasks(conn, int(week))
            if int(item.get("id") or 0) == task_id
        ),
        None,
    )
    if task is None:
        return {"eligible": False, "ready": False, "reason": "Task not found."}
    if task.get("ready"):
        return {"eligible": True, "ready": True, "reason": "Ready for the dynamic queue."}
    return {
        "eligible": False,
        "ready": False,
        "reason": str(task.get("prerequisite_reason") or "Complete the prerequisite first."),
    }


def tomorrow_preview(conn, week, state, limit=3):
    del state
    today_ids = {
        int(item.get("id") or 0)
        for item in unified_tasks.daily_plan(conn, int(week))
    }
    preview = []
    for item in unified_tasks.next_tasks(conn, int(week), limit=20):
        if int(item.get("id") or 0) in today_ids:
            continue
        preview.append(
            {
                "title": str(item.get("label") or "Task"),
                "detail": str(item.get("display_source") or item.get("detail") or "Ready next"),
                "minutes": int(item.get("estimated_minutes") or 30),
                "task_id": item.get("id"),
            }
        )
        if len(preview) >= int(limit):
            break
    return preview
