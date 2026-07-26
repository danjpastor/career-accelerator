from __future__ import annotations

"""Unified Career Accelerator planner.

v10.27 replaces the overlapping adaptive, Get Ahead, Added Today, manual-focus,
and per-track recommendation planners with one deterministic runtime.  The
legacy implementation is isolated in :mod:`legacy_planner` only for durable
migration helpers and task-completion compatibility.
"""

from datetime import date

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
    return unified_tasks.next_tasks(conn, int(week), limit=6)


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
    conn.execute(
        "DELETE FROM daily_focus WHERE focus_date=? AND completed_at IS NULL",
        (today,),
    )
    conn.commit()
    items = unified_tasks.daily_plan(conn, int(week), max_items=max_items)
    return {"focus_date": today, "created": len(items), "items": items}


def available(conn, week):
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


def get_ahead_candidates(conn, week, state, limit=12):
    """Compatibility name for the Optional Practice browser."""
    del state
    candidates = unified_tasks.optional_practice(conn, int(week), limit=int(limit))
    for candidate in candidates:
        candidate["extra_reason"] = "Optional prerequisite-ready practice"
    return candidates


def started_get_ahead_tasks(conn, week):
    del conn, week
    return []


def start_get_ahead(conn, week, state, item):
    del conn, week, state
    # Optional work is never persisted into Today’s Focus.
    return dict(item or {})


def remove_get_ahead_task(conn, week, item):
    del conn, week
    return {"removed": False, "label": str((item or {}).get("label") or "")}


def optional_focus_candidate(conn, week, state):
    del conn, week, state
    return None


def start_extra_focus(conn, week, state, item):
    return start_get_ahead(conn, week, state, item)


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
