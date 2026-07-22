from __future__ import annotations

from datetime import date, timedelta
import json
import re

from career_app.data.applied_exercises import (
    exercise_for_label as applied_exercise_for_label,
)
from career_app.data.duckdb_exercises import exercise_for_label


ENERGY_RANK = {
    "Low": 1,
    "Normal": 2,
    "High": 3,
}

DEFAULTS = {
    "Learning": (40, "Normal", 1, 2),
    "SQL": (25, "Normal", 1, 4),
    "Portfolio": (45, "High", 2, 3),
    "Review": (20, "Low", 3, 8),
    "General": (25, "Low", 3, 1),
}

# The weekly roadmap remains the ground-truth structure:
# two learning priorities, one SQL priority, and one portfolio priority.
FOCUS_SLOT_ORDER = (
    "Learning",
    "Learning",
    "Learning",
    "SQL",
    "Portfolio",
)


def infer(label):
    applied_exercise = applied_exercise_for_label(label)
    if applied_exercise is not None:
        return {
            "category": applied_exercise["task_category"],
            "minutes": applied_exercise["minutes"],
            "energy": applied_exercise["energy"],
            "priority": applied_exercise["priority"],
            "destination": applied_exercise["destination"],
        }

    duckdb_exercise = exercise_for_label(label)
    if duckdb_exercise is not None:
        return {
            "category": "SQL",
            "minutes": duckdb_exercise["minutes"],
            "energy": "Normal",
            "priority": duckdb_exercise["priority"],
            "destination": 4,
        }

    lower = label.lower()

    if any(
        token in lower
        for token in (
            "google",
            "course",
            "module",
            "academy",
            "lesson",
            "quiz",
        )
    ):
        category = "Learning"
    elif any(
        token in lower
        for token in (
            "sql",
            "datalemur",
            "tweets",
            "skills",
            "likes",
            "listings",
        )
    ):
        category = "SQL"
    elif any(
        token in lower
        for token in (
            "project",
            "portfolio",
            "schema",
            "dataset",
            "charter",
            "kpi",
            "readme",
        )
    ):
        category = "Portfolio"
    elif any(
        token in lower
        for token in (
            "review",
            "retrospective",
            "summary",
        )
    ):
        category = "Review"
    else:
        category = "General"

    minutes, energy, priority, destination = DEFAULTS[category]
    return {
        "category": category,
        "minutes": minutes,
        "energy": energy,
        "priority": priority,
        "destination": destination,
    }


def seed(conn):
    rows = conn.execute(
        "SELECT id,label,completed FROM sprint_tasks"
    ).fetchall()

    for row in rows:
        meta = infer(row["label"])
        existing = conn.execute(
            "SELECT task_id FROM task_metadata WHERE task_id=?",
            (row["id"],),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE task_metadata
                   SET category=COALESCE(NULLIF(category,''),?)
                   WHERE task_id=?""",
                (meta["category"], row["id"]),
            )
            continue

        conn.execute(
            """INSERT INTO task_metadata
               (task_id,status,priority,estimated_minutes,
                energy,destination,category)
               VALUES(?,?,?,?,?,?,?)""",
            (
                row["id"],
                (
                    "Completed"
                    if row["completed"]
                    else "Not Started"
                ),
                meta["priority"],
                meta["minutes"],
                meta["energy"],
                meta["destination"],
                meta["category"],
            ),
        )

    conn.commit()


GOOGLE_COURSE_TASK = re.compile(
    r"^\[Google Course (\d+)\]",
    re.IGNORECASE,
)


def _managed_external_track_for_label(label):
    text = str(label or "").strip()
    lower = text.lower()
    if (
        GOOGLE_COURSE_TASK.match(text)
        or "google course" in lower
        or "google certificate" in lower
        or lower.startswith("google •")
    ):
        return "google"
    if "datacamp" in lower:
        return "datacamp"
    return None


def _normalized_task_label(label):
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(label or "").lower(),
    )
    return " ".join(value.split())


def _row_identity(row):
    track_key = str(
        row["track_key"]
        if "track_key" in row.keys()
        else ""
    ).strip().lower()
    if track_key:
        return f"track:{track_key}"

    managed = _managed_external_track_for_label(
        row["label"]
    )
    if managed:
        return f"track:{managed}"

    return (
        f"week:{int(row['week'])}:"
        f"{str(row['category'] or 'General').lower()}:"
        f"{_normalized_task_label(row['label'])}"
    )


def _focus_identity(conn, item):
    source_key = str(
        item.get("source_key") or ""
    )
    if source_key.startswith("roadmap:"):
        return (
            "track:"
            + source_key.split(":", 1)[1].lower()
        )

    task_id = item.get("task_id")
    if task_id is not None:
        row = conn.execute(
            """SELECT tt.track_key,s.week,s.label,m.category
               FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               LEFT JOIN track_tasks tt ON tt.task_id=s.id
               WHERE s.id=?""",
            (int(task_id),),
        ).fetchone()
        if row is not None:
            return _row_identity(row)

    return source_key or (
        "fallback:"
        + _normalized_task_label(
            item.get("label")
        )
    )


def _dedupe_focus_items(conn, items):
    result = []
    seen = set()
    for item in items:
        identity = _focus_identity(conn, item)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
    return result


def sync_google_course_progress(conn, current_course):
    """Recognize course-specific roadmap work already completed."""
    current_course = max(1, int(current_course))
    rows = conn.execute(
        """SELECT s.id,s.label,s.completed,m.status
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id"""
    ).fetchall()

    changed = 0
    for row in rows:
        match = GOOGLE_COURSE_TASK.match(row["label"])
        if not match:
            continue

        task_course = int(match.group(1))
        if task_course >= current_course:
            continue

        if not row["completed"] or row["status"] != "Completed":
            conn.execute(
                "UPDATE sprint_tasks SET completed=1 WHERE id=?",
                (row["id"],),
            )
            conn.execute(
                """UPDATE task_metadata
                   SET status='Completed',deferred_until=NULL
                   WHERE task_id=?""",
                (row["id"],),
            )
            changed += 1

    if changed:
        conn.commit()
    return changed



def available(conn, week):
    today = date.today().isoformat()
    week = int(week)
    previous_week = max(
        0,
        week - 1,
    )

    rows = conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status,
               m.priority,
               m.estimated_minutes,
               m.energy,
               m.deferred_until,
               m.destination,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason,
               tt.track_key,
               tt.target_key
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.week IN (?,?)
             AND s.completed=0
             AND m.status NOT IN ('Completed','Blocked')
             AND COALESCE(
                 m.prerequisite_state,
                 'Ready'
             )='Ready'
             AND (
                 m.deferred_until IS NULL
                 OR m.deferred_until<=?
             )
             AND NOT EXISTS (
                 SELECT 1
                 FROM track_tasks tt
                 JOIN track_state ts
                   ON ts.track_key=tt.track_key
                 WHERE tt.task_id=s.id
                   AND ts.status<>'Active'
             )""",
        (
            week,
            previous_week,
            today,
        ),
    ).fetchall()

    eligible = []
    for row in rows:
        if str(row["track_key"] or "").lower() == "datacamp" or "datacamp" in str(row["label"] or "").lower():
            continue
        task_week = int(row["week"])
        current_week_task = (
            task_week == week
        )
        monday_recovery = (
            _is_monday_recovery_retrospective(
                label=row["label"],
                task_week=task_week,
                current_week=week,
            )
        )

        if not (
            current_week_task
            or monday_recovery
        ):
            continue

        if not _task_allowed_today(
            label=row["label"],
            category=(
                row["category"]
                or "General"
            ),
            task_week=task_week,
            current_week=week,
        ):
            continue

        eligible.append(row)

    ordered = sorted(
        eligible,
        key=lambda row: (
            0
            if row["track_key"]
            else 1,
            0
            if _is_monday_recovery_retrospective(
                label=row["label"],
                task_week=row["week"],
                current_week=week,
            )
            else 1,
            int(row["priority"] or 3),
            0
            if row["status"] == "In Progress"
            else 1,
            int(row["week"]),
            int(row["sort_order"]),
        ),
    )

    deduplicated = []
    seen = set()
    for row in ordered:
        identity = _row_identity(row)
        if identity in seen:
            continue
        seen.add(identity)
        deduplicated.append(row)
    return deduplicated

def task_schedule_eligibility(
    conn,
    task_id,
    current_week,
):
    """Explain whether one task can appear in Next Tasks and Today’s Focus."""
    row = conn.execute(
        """SELECT
               s.id,
               s.week,
               s.label,
               s.completed,
               m.status,
               m.deferred_until,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason,
               tt.track_key,
               ts.status AS track_status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           LEFT JOIN track_state ts
             ON ts.track_key=tt.track_key
           WHERE s.id=?""",
        (int(task_id),),
    ).fetchone()

    if row is None:
        return {
            "eligible": False,
            "reason": "Task no longer exists.",
        }

    if bool(row["completed"]):
        return {
            "eligible": False,
            "reason": "Task is completed.",
        }

    if row["status"] in {
        "Completed",
        "Blocked",
    }:
        return {
            "eligible": False,
            "reason": (
                f"Status is {row['status']}."
            ),
        }

    if (
        row["prerequisite_state"]
        == "Blocked"
    ):
        return {
            "eligible": False,
            "reason": (
                row["prerequisite_reason"]
                or "Required concepts are still locked."
            ),
        }

    if (
        row["deferred_until"]
        and row["deferred_until"]
        > date.today().isoformat()
    ):
        return {
            "eligible": False,
            "reason": (
                "Deferred until "
                f"{row['deferred_until']}."
            ),
        }

    task_week = int(row["week"])
    current_week = int(current_week)
    current_week_task = (
        task_week == current_week
    )
    monday_recovery = (
        _is_monday_recovery_retrospective(
            label=row["label"],
            task_week=task_week,
            current_week=current_week,
        )
    )
    if not (
        current_week_task
        or monday_recovery
    ):
        return {
            "eligible": False,
            "reason": (
                f"Task belongs to Week {task_week}; "
                f"the active sprint is Week {current_week}."
            ),
        }

    if not _task_allowed_today(
        label=row["label"],
        category=(
            row["category"]
            or "General"
        ),
        task_week=task_week,
        current_week=current_week,
    ):
        return {
            "eligible": False,
            "reason": (
                "This task is outside its recommendation window."
            ),
        }

    if (
        row["track_key"]
        and row["track_status"]
        != "Active"
    ):
        return {
            "eligible": False,
            "reason": (
                "Adaptive track status is "
                f"{row['track_status']}."
            ),
        }

    return {
        "eligible": True,
        "reason": "Added back to the active schedule.",
    }


def make_plan(conn, week, minutes, energy):
    capacity = ENERGY_RANK.get(energy, 2)
    eligible = [
        row
        for row in available(conn, week)
        if ENERGY_RANK.get(row["energy"], 2) <= capacity
    ]

    selected = []
    remaining = max(0, minutes)

    for row in eligible:
        estimate = int(row["estimated_minutes"])
        if estimate <= remaining or not selected:
            selected.append(row)
            remaining -= estimate
        if remaining <= 5:
            break

    return selected, max(0, remaining)


def defer(conn, task_id, days=1):
    target = (
        date.today() + timedelta(days=days)
    ).isoformat()

    conn.execute(
        """UPDATE task_metadata
           SET status='Deferred', deferred_until=?
           WHERE task_id=?""",
        (target, task_id),
    )
    conn.commit()


def _task_dict(
    row,
    *,
    carryover=False,
    carryover_note=None,
):
    return {
        "task_id": int(row["id"]),
        "week": int(row["week"]),
        "sort_order": int(row["sort_order"]),
        "label": row["label"],
        "category": row["category"] or "General",
        "status": row["status"] or "Not Started",
        "priority": int(row["priority"] or 3),
        "estimated_minutes": int(
            row["estimated_minutes"] or 30
        ),
        "destination": int(row["destination"] or 0),
        "carryover": bool(carryover),
        "carryover_note": carryover_note,
        "roadmap_fallback": False,
        "source_key": f"task:{row['id']}",
        "track_key": (
            row["track_key"]
            if "track_key" in row.keys()
            else None
        ),
        "target_key": (
            row["target_key"]
            if "target_key" in row.keys()
            else None
        ),
    }


def _carryover_tasks(conn, focus_date, current_week):
    today = date.today().isoformat()

    rows = conn.execute(
        """SELECT DISTINCT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status,
               m.priority,
               m.estimated_minutes,
               m.energy,
               m.deferred_until,
               m.destination,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason
           FROM daily_focus f
           JOIN sprint_tasks s ON s.id=f.task_id
           JOIN task_metadata m ON m.task_id=s.id
           WHERE f.focus_date=?
             AND COALESCE(f.is_extra,0)=0
             AND f.task_id IS NOT NULL
             AND s.completed=0
             AND m.status NOT IN ('Completed','Blocked')
             AND COALESCE(
                 m.prerequisite_state,
                 'Ready'
             )='Ready'
             AND (
                 m.deferred_until IS NULL
                 OR m.deferred_until<=?
             )
             AND NOT EXISTS (
                 SELECT 1
                 FROM track_tasks tt
                 JOIN track_state ts
                   ON ts.track_key=tt.track_key
                 WHERE tt.task_id=s.id
                   AND ts.status<>'Active'
             )
           ORDER BY
               m.priority,
               CASE
                   WHEN m.status='In Progress' THEN 0
                   ELSE 1
               END,
               f.position""",
        (focus_date, today),
    ).fetchall()

    return [
        _task_dict(
            row,
            carryover=True,
            carryover_note="Missed yesterday",
        )
        for row in rows
        if str(row["label"] or "").lower().find("datacamp") < 0
        and _task_allowed_today(
            label=row["label"],
            category=(
                row["category"]
                or "General"
            ),
            task_week=row["week"],
            current_week=current_week,
        )
    ]


def _candidate_sort_key(item):
    return (
        0 if item["carryover"] else 1,
        0 if item["status"] == "In Progress" else 1,
        item["priority"],
        item["week"],
        item["sort_order"],
    )


def _track_metadata(conn, track_key):
    row = conn.execute(
        """SELECT metadata
           FROM track_state
           WHERE track_key=?""",
        (track_key,),
    ).fetchone()
    if row is None:
        return {}
    try:
        return json.loads(
            row["metadata"]
            or "{}"
        )
    except (TypeError, ValueError):
        return {}


def _roadmap_fallbacks(conn, state):
    academy_meta = _track_metadata(
        conn,
        "academy",
    )
    sql_meta = _track_metadata(
        conn,
        "sql",
    )
    portfolio_meta = _track_metadata(
        conn,
        "portfolio",
    )

    academy_detail = academy_meta.get(
        "title",
        "Continue your next Accelerator Academy lesson",
    )

    sql_detail = sql_meta.get(
        "title",
        "Complete the next assigned SQL problem",
    )
    portfolio_detail = portfolio_meta.get(
        "milestone",
        "Advance the next unlocked portfolio milestone",
    )

    return [
        {
            "task_id": None,
            "label": f"Continue Course {state['google_course']}",
            "category": "Learning",
            "status": "Roadmap",
            "priority": 1,
            "estimated_minutes": 45,
            "destination": 2,
            "carryover": False,
            "roadmap_fallback": True,
            "source_key": "roadmap:google",
            "display_title": "Google Certificate",
            "detail": (
                f"Continue from Course {state['google_course']}, "
                f"Module {state['google_module']}"
            ),
        },
        {
            "task_id": None,
            "label": academy_detail,
            "category": "Learning",
            "status": "Roadmap",
            "priority": 1,
            "estimated_minutes": int(academy_meta.get("estimated_minutes", 30)),
            "destination": 12,
            "carryover": False,
            "roadmap_fallback": True,
            "source_key": "roadmap:academy",
            "track_key": "academy",
            "target_key": academy_meta.get("target_key"),
            "display_title": "Accelerator Academy",
            "detail": academy_detail,
        },
        {
            "task_id": None,
            "label": sql_detail,
            "category": "SQL",
            "status": "Roadmap",
            "priority": 1,
            "estimated_minutes": 35,
            "destination": 4,
            "carryover": False,
            "roadmap_fallback": True,
            "source_key": "roadmap:sql",
            "display_title": "SQL Practice",
            "detail": sql_detail,
        },
        {
            "task_id": None,
            "label": portfolio_detail,
            "category": "Portfolio",
            "status": "Roadmap",
            "priority": 2,
            "estimated_minutes": 45,
            "destination": 3,
            "carryover": False,
            "roadmap_fallback": True,
            "source_key": "roadmap:portfolio",
            "display_title": "Portfolio Project",
            "detail": portfolio_detail,
        },
    ]


def _remove_matching_slot(slots, category):
    try:
        slots.remove(category)
    except ValueError:
        if slots:
            slots.pop(0)


def _is_weekly_retrospective(label):
    return (
        "retrospective"
        in str(label or "").lower()
    )


def _retrospective_allowed_today(
    *,
    task_week,
    current_week,
):
    """Recommend this week's review Friday or last week's missed review Monday."""
    weekday = date.today().weekday()
    task_week = int(task_week)
    current_week = int(current_week)

    if weekday == 4:
        return task_week == current_week

    if weekday == 0 and current_week > 1:
        return task_week == current_week - 1

    return False


def _is_monday_recovery_retrospective(
    *,
    label,
    task_week,
    current_week,
):
    return (
        date.today().weekday() == 0
        and _is_weekly_retrospective(label)
        and int(current_week) > 1
        and int(task_week)
        == int(current_week) - 1
    )


def _task_allowed_today(
    *,
    label,
    category,
    task_week,
    current_week,
):
    # Only retrospective deliverables are calendar-gated. Other Review tasks
    # remain actionable according to their normal roadmap schedule.
    if not _is_weekly_retrospective(label):
        return True

    return _retrospective_allowed_today(
        task_week=task_week,
        current_week=current_week,
    )


def _track_accepts_work_today(
    conn,
    track_key,
):
    row = conn.execute(
        """SELECT status
           FROM track_state
           WHERE track_key=?""",
        (track_key,),
    ).fetchone()
    return (
        row is None
        or row["status"] == "Active"
    )


def _focus_track_rank(conn, item):
    task_id = item.get("task_id")
    if task_id is not None:
        link = conn.execute(
            """SELECT track_key
               FROM track_tasks
               WHERE task_id=?""",
            (task_id,),
        ).fetchone()
        if link:
            return {
                "google": 0,
                "academy": 1,
                "sql": 2,
                "portfolio": 3,
                "applied": 4,
            }.get(link["track_key"], 8)

    source_key = str(
        item.get("source_key") or ""
    )
    if source_key == "roadmap:google":
        return 0
    if source_key == "roadmap:academy":
        return 1
    if source_key == "roadmap:sql":
        return 2
    if source_key == "roadmap:portfolio":
        return 3

    return {
        "Learning": 5,
        "SQL": 6,
        "Portfolio": 7,
        "Review": 8,
        "General": 9,
    }.get(
        item.get("category"),
        10,
    )


def _order_focus_items(conn, items):
    return sorted(
        items,
        key=lambda item: (
            _focus_track_rank(conn, item),
            0
            if item.get("carryover")
            else 1,
            0
            if item.get("status")
            == "In Progress"
            else 1,
            int(item.get("priority") or 3),
            int(item.get("sort_order") or 0),
        ),
    )

def _daily_focus_track_identity(
    conn,
    item,
):
    """Return the exact assignment identity stored for a daily-focus row."""
    track_key = str(
        item.get("track_key") or ""
    ).strip().lower()
    target_key = str(
        item.get("target_key") or ""
    ).strip().lower()

    if track_key and target_key:
        return (
            f"track:{track_key}:"
            f"{target_key}"
        )
    if track_key:
        return f"track:{track_key}"

    source_key = str(
        item.get("source_key") or ""
    )
    if source_key.startswith(
        "roadmap:"
    ):
        return (
            "track:"
            + source_key.split(
                ":",
                1,
            )[1].lower()
        )

    task_id = item.get(
        "task_id"
    )
    if task_id is not None:
        return f"task:{int(task_id)}"

    return (
        source_key
        or (
            "focus:"
            + _normalized_task_label(
                item.get("label")
            )
        )
    )


def _focus_track_fields(
    conn,
    item,
):
    track_key = item.get(
        "track_key"
    )
    target_key = item.get(
        "target_key"
    )

    task_id = item.get(
        "task_id"
    )
    if (
        task_id is not None
        and not track_key
    ):
        link = conn.execute(
            """SELECT track_key,target_key
               FROM track_tasks
               WHERE task_id=?""",
            (int(task_id),),
        ).fetchone()
        if link is not None:
            track_key = link[
                "track_key"
            ]
            target_key = link[
                "target_key"
            ]

    source_key = str(
        item.get("source_key") or ""
    )
    if (
        not track_key
        and source_key.startswith(
            "roadmap:"
        )
    ):
        track_key = source_key.split(
            ":",
            1,
        )[1]

    if (
        track_key
        and not target_key
    ):
        link = conn.execute(
            """SELECT target_key
               FROM track_tasks
               WHERE track_key=?""",
            (track_key,),
        ).fetchone()
        if link is not None:
            target_key = link[
                "target_key"
            ]

    return (
        track_key,
        target_key,
    )


def _backfill_daily_focus_fields(
    conn,
):
    rows = conn.execute(
        """SELECT
               id,task_id,source_key,
               title,track_key,target_key
           FROM daily_focus
           WHERE focus_date=?""",
        (
            date.today().isoformat(),
        ),
    ).fetchall()

    changed = False
    for row in rows:
        track_key = row[
            "track_key"
        ]
        target_key = row[
            "target_key"
        ]

        if (
            not track_key
            and row["task_id"]
            is not None
        ):
            link = conn.execute(
                """SELECT
                       track_key,target_key
                   FROM track_tasks
                   WHERE task_id=?""",
                (
                    int(
                        row["task_id"]
                    ),
                ),
            ).fetchone()
            if link is not None:
                track_key = link[
                    "track_key"
                ]
                target_key = link[
                    "target_key"
                ]

        if not track_key:
            source_key = str(
                row["source_key"]
                or ""
            )
            if source_key.startswith(
                "roadmap:"
            ):
                track_key = (
                    source_key.split(
                        ":",
                        1,
                    )[1]
                )
            else:
                track_key = (
                    _managed_external_track_for_label(
                        row["title"]
                    )
                )

        if (
            track_key
            and not target_key
        ):
            active = conn.execute(
                """SELECT target_key
                   FROM track_tasks
                   WHERE track_key=?""",
                (track_key,),
            ).fetchone()
            if active is not None:
                target_key = active[
                    "target_key"
                ]

        if (
            track_key
            != row["track_key"]
            or target_key
            != row["target_key"]
        ):
            conn.execute(
                """UPDATE daily_focus
                   SET track_key=?,
                       target_key=?
                   WHERE id=?""",
                (
                    track_key,
                    target_key,
                    int(row["id"]),
                ),
            )
            changed = True

    if changed:
        conn.commit()


def _track_daily_completed(
    conn,
    track_key,
):
    row = conn.execute(
        """SELECT status,metadata
           FROM track_state
           WHERE track_key=?""",
        (track_key,),
    ).fetchone()
    if row is None:
        return False

    try:
        metadata = json.loads(
            row["metadata"]
            or "{}"
        )
    except (
        TypeError,
        ValueError,
    ):
        metadata = {}

    target = int(
        metadata.get(
            "today_target",
            0,
        )
        or 0
    )
    completed = int(
        metadata.get(
            "today_completed",
            0,
        )
        or 0
    )

    return (
        target > 0
        and completed >= target
    ) or row["status"] in {
        "Daily Complete",
        "Weekly Complete",
    }


# DURABLE ADDED TODAY STORE + MAXIMIZED STARTUP 1
MANUAL_FOCUS_TABLE = "manual_daily_focus"


def _manual_focus_key(item):
    item = dict(item or {})
    track_key = str(item.get("track_key") or "").strip().lower()
    target_key = str(item.get("target_key") or "").strip().lower()

    if track_key and target_key:
        return f"track:{track_key}:{target_key}"

    source_key = str(item.get("source_key") or "").strip()
    if source_key:
        return f"source:{source_key}"

    task_id = item.get("task_id")
    if task_id is None:
        task_id = item.get("id")
    if task_id is not None:
        return f"task:{int(task_id)}"

    category = _normalized_task_label(
        item.get("category") or "general"
    )
    label = _normalized_task_label(
        item.get("label") or item.get("title") or "task"
    )
    return f"label:{category}:{label}"


def _create_manual_focus_store(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_daily_focus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            focus_date TEXT NOT NULL,
            manual_key TEXT NOT NULL,
            week INTEGER NOT NULL,
            task_id INTEGER,
            source_key TEXT,
            category TEXT NOT NULL DEFAULT 'General',
            title TEXT NOT NULL,
            detail TEXT,
            estimated_minutes INTEGER NOT NULL DEFAULT 30,
            destination INTEGER NOT NULL DEFAULT 0,
            track_key TEXT,
            target_key TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(focus_date, manual_key)
        )
        """
    )


def _manual_focus_task_id(conn, row):
    task_id = row["task_id"]
    if task_id is not None:
        existing = conn.execute(
            "SELECT id FROM sprint_tasks WHERE id=?",
            (int(task_id),),
        ).fetchone()
        if existing is not None:
            return int(existing["id"])

    track_key = str(row["track_key"] or "").strip()
    target_key = str(row["target_key"] or "").strip()
    if track_key and target_key:
        linked = conn.execute(
            """
            SELECT tt.task_id
            FROM track_tasks AS tt
            JOIN sprint_tasks AS s
              ON s.id=tt.task_id
            WHERE tt.track_key=?
              AND tt.target_key=?
            ORDER BY s.completed, s.week, s.sort_order
            LIMIT 1
            """,
            (track_key, target_key),
        ).fetchone()
        if linked is not None:
            return int(linked["task_id"])

    source_key = str(row["source_key"] or "")
    if source_key.startswith("task:"):
        try:
            source_task_id = int(source_key.split(":", 1)[1])
        except (TypeError, ValueError):
            source_task_id = None
        if source_task_id is not None:
            existing = conn.execute(
                "SELECT id FROM sprint_tasks WHERE id=?",
                (source_task_id,),
            ).fetchone()
            if existing is not None:
                return int(existing["id"])

    label = str(row["title"] or "").strip()
    if label:
        matching = conn.execute(
            """
            SELECT id
            FROM sprint_tasks
            WHERE label=?
            ORDER BY
                CASE WHEN completed=0 THEN 0 ELSE 1 END,
                ABS(week-?),
                sort_order
            LIMIT 1
            """,
            (
                label,
                int(row["week"] or 1),
            ),
        ).fetchone()
        if matching is not None:
            return int(matching["id"])

    return None


def _backfill_manual_focus_store(conn):
    _create_manual_focus_store(conn)
    rows = conn.execute(
        """
        SELECT
            f.focus_date,
            f.week,
            f.task_id,
            f.source_key,
            COALESCE(m.category,f.category,'General') AS category,
            COALESCE(s.label,f.title) AS title,
            f.title AS detail,
            COALESCE(
                m.estimated_minutes,
                f.estimated_minutes,
                30
            ) AS estimated_minutes,
            COALESCE(m.destination,0) AS destination,
            f.track_key,
            f.target_key,
            CASE
                WHEN f.completed_at IS NOT NULL
                  OR COALESCE(s.completed,0)=1
                  OR COALESCE(m.status,'')='Completed'
                THEN COALESCE(f.completed_at,CURRENT_TIMESTAMP)
                ELSE NULL
            END AS completed_at
        FROM daily_focus AS f
        LEFT JOIN sprint_tasks AS s
          ON s.id=f.task_id
        LEFT JOIN task_metadata AS m
          ON m.task_id=f.task_id
        WHERE COALESCE(f.is_extra,0)=1
        """
    ).fetchall()

    for row in rows:
        item = dict(row)
        manual_key = _manual_focus_key(item)
        conn.execute(
            """
            INSERT INTO manual_daily_focus (
                focus_date,manual_key,week,task_id,source_key,
                category,title,detail,estimated_minutes,destination,
                track_key,target_key,completed_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(focus_date,manual_key) DO UPDATE SET
                week=excluded.week,
                task_id=COALESCE(excluded.task_id,manual_daily_focus.task_id),
                source_key=COALESCE(
                    NULLIF(excluded.source_key,''),
                    manual_daily_focus.source_key
                ),
                category=excluded.category,
                title=excluded.title,
                detail=COALESCE(
                    NULLIF(excluded.detail,''),
                    manual_daily_focus.detail
                ),
                estimated_minutes=excluded.estimated_minutes,
                destination=excluded.destination,
                track_key=COALESCE(
                    NULLIF(excluded.track_key,''),
                    manual_daily_focus.track_key
                ),
                target_key=COALESCE(
                    NULLIF(excluded.target_key,''),
                    manual_daily_focus.target_key
                ),
                completed_at=COALESCE(
                    excluded.completed_at,
                    manual_daily_focus.completed_at
                ),
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                row["focus_date"],
                manual_key,
                int(row["week"]),
                row["task_id"],
                row["source_key"],
                row["category"] or "General",
                row["title"] or "Get Ahead task",
                row["detail"],
                int(row["estimated_minutes"] or 30),
                int(row["destination"] or 0),
                row["track_key"],
                row["target_key"],
                row["completed_at"],
            ),
        )


def _store_manual_focus_item(conn, week, item):
    _backfill_manual_focus_store(conn)
    item = dict(item or {})

    track_key, target_key = _focus_track_fields(
        conn,
        item,
    )
    task_id = item.get("task_id")
    if task_id is None:
        task_id = item.get("id")

    source_key = (
        item.get("source_key")
        or (
            f"get-ahead:"
            f"{item.get('category','general')}:"
            f"{item.get('label','task')}"
        )
    )

    destination = item.get("destination")
    if destination is None and task_id is not None:
        metadata = conn.execute(
            """
            SELECT destination
            FROM task_metadata
            WHERE task_id=?
            """,
            (int(task_id),),
        ).fetchone()
        destination = (
            int(metadata["destination"] or 0)
            if metadata is not None
            else 0
        )

    stored = {
        "task_id": task_id,
        "source_key": source_key,
        "category": item.get("category") or "General",
        "label": item.get("label") or "Get Ahead task",
        "track_key": track_key,
        "target_key": target_key,
    }
    manual_key = _manual_focus_key(stored)

    conn.execute(
        """
        INSERT INTO manual_daily_focus (
            focus_date,manual_key,week,task_id,source_key,
            category,title,detail,estimated_minutes,destination,
            track_key,target_key,completed_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(focus_date,manual_key) DO UPDATE SET
            week=excluded.week,
            task_id=COALESCE(excluded.task_id,manual_daily_focus.task_id),
            source_key=excluded.source_key,
            category=excluded.category,
            title=excluded.title,
            detail=COALESCE(
                NULLIF(excluded.detail,''),
                manual_daily_focus.detail
            ),
            estimated_minutes=excluded.estimated_minutes,
            destination=excluded.destination,
            track_key=COALESCE(
                NULLIF(excluded.track_key,''),
                manual_daily_focus.track_key
            ),
            target_key=COALESCE(
                NULLIF(excluded.target_key,''),
                manual_daily_focus.target_key
            ),
            completed_at=COALESCE(
                excluded.completed_at,
                manual_daily_focus.completed_at
            ),
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            date.today().isoformat(),
            manual_key,
            int(week),
            task_id,
            source_key,
            item.get("category") or "General",
            item.get("label") or "Get Ahead task",
            item.get("detail"),
            int(item.get("estimated_minutes", 30) or 30),
            int(destination or 0),
            track_key,
            target_key,
            (
                item.get("completed_at")
                if item.get("completed")
                else None
            ),
        ),
    )
    return manual_key


def _restore_manual_focus_rows(conn, week):
    _backfill_manual_focus_store(conn)
    focus_date = date.today().isoformat()

    rows = conn.execute(
        """
        SELECT *
        FROM manual_daily_focus
        WHERE focus_date=?
        ORDER BY created_at,id
        """,
        (focus_date,),
    ).fetchall()

    changed = False
    for row in rows:
        task_id = _manual_focus_task_id(
            conn,
            row,
        )

        task_completed = False
        current_destination = int(row["destination"] or 0)
        current_category = row["category"] or "General"
        current_title = row["title"] or "Get Ahead task"
        current_minutes = int(row["estimated_minutes"] or 30)

        if task_id is not None:
            task_row = conn.execute(
                """
                SELECT
                    s.label,
                    s.completed,
                    m.status,
                    m.category,
                    m.estimated_minutes,
                    m.destination
                FROM sprint_tasks AS s
                LEFT JOIN task_metadata AS m
                  ON m.task_id=s.id
                WHERE s.id=?
                """,
                (int(task_id),),
            ).fetchone()
            if task_row is not None:
                task_completed = bool(
                    task_row["completed"]
                    or task_row["status"] == "Completed"
                )
                current_title = (
                    task_row["label"]
                    or current_title
                )
                current_category = (
                    task_row["category"]
                    or current_category
                )
                current_minutes = int(
                    task_row["estimated_minutes"]
                    or current_minutes
                )
                current_destination = int(
                    task_row["destination"]
                    or current_destination
                )

        completed_at = row["completed_at"]
        if task_completed and completed_at is None:
            completed_at = date.today().isoformat()

        existing = None
        if task_id is not None:
            existing = conn.execute(
                """
                SELECT id
                FROM daily_focus
                WHERE focus_date=?
                  AND COALESCE(is_extra,0)=1
                  AND task_id=?
                LIMIT 1
                """,
                (
                    focus_date,
                    int(task_id),
                ),
            ).fetchone()

        if existing is None and row["source_key"]:
            existing = conn.execute(
                """
                SELECT id
                FROM daily_focus
                WHERE focus_date=?
                  AND COALESCE(is_extra,0)=1
                  AND source_key=?
                LIMIT 1
                """,
                (
                    focus_date,
                    row["source_key"],
                ),
            ).fetchone()

        if (
            existing is None
            and row["track_key"]
            and row["target_key"]
        ):
            existing = conn.execute(
                """
                SELECT id
                FROM daily_focus
                WHERE focus_date=?
                  AND COALESCE(is_extra,0)=1
                  AND track_key=?
                  AND target_key=?
                LIMIT 1
                """,
                (
                    focus_date,
                    row["track_key"],
                    row["target_key"],
                ),
            ).fetchone()

        if existing is None:
            position = conn.execute(
                """
                SELECT COALESCE(MAX(position),0)+1
                FROM daily_focus
                WHERE focus_date=?
                """,
                (focus_date,),
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO daily_focus (
                    focus_date,week,position,task_id,source_key,
                    category,title,estimated_minutes,track_key,
                    target_key,is_extra,completed_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,1,?)
                """,
                (
                    focus_date,
                    int(week),
                    int(position),
                    task_id,
                    row["source_key"],
                    current_category,
                    current_title,
                    current_minutes,
                    row["track_key"],
                    row["target_key"],
                    completed_at,
                ),
            )
            changed = True
        else:
            conn.execute(
                """
                UPDATE daily_focus
                SET week=?,
                    task_id=?,
                    source_key=?,
                    category=?,
                    title=?,
                    estimated_minutes=?,
                    track_key=?,
                    target_key=?,
                    completed_at=COALESCE(completed_at,?)
                WHERE id=?
                """,
                (
                    int(week),
                    task_id,
                    row["source_key"],
                    current_category,
                    current_title,
                    current_minutes,
                    row["track_key"],
                    row["target_key"],
                    completed_at,
                    int(existing["id"]),
                ),
            )

        conn.execute(
            """
            UPDATE manual_daily_focus
            SET week=?,
                task_id=?,
                category=?,
                title=?,
                estimated_minutes=?,
                destination=?,
                completed_at=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                int(week),
                task_id,
                current_category,
                current_title,
                current_minutes,
                current_destination,
                completed_at,
                int(row["id"]),
            ),
        )

    if rows or changed:
        conn.commit()
    return len(rows)


def _sync_manual_focus_completion(conn):
    _backfill_manual_focus_store(conn)
    focus_date = date.today().isoformat()

    conn.execute(
        """
        UPDATE manual_daily_focus
        SET completed_at=COALESCE(
                completed_at,
                (
                    SELECT f.completed_at
                    FROM daily_focus AS f
                    WHERE f.focus_date=manual_daily_focus.focus_date
                      AND COALESCE(f.is_extra,0)=1
                      AND (
                          (
                              manual_daily_focus.task_id IS NOT NULL
                              AND f.task_id=manual_daily_focus.task_id
                          )
                          OR (
                              manual_daily_focus.source_key IS NOT NULL
                              AND f.source_key=manual_daily_focus.source_key
                          )
                      )
                    ORDER BY f.position
                    LIMIT 1
                )
            ),
            updated_at=CURRENT_TIMESTAMP
        WHERE focus_date=?
        """,
        (focus_date,),
    )

    rows = conn.execute(
        """
        SELECT id,task_id
        FROM manual_daily_focus
        WHERE focus_date=?
          AND task_id IS NOT NULL
          AND completed_at IS NULL
        """,
        (focus_date,),
    ).fetchall()
    for row in rows:
        task = conn.execute(
            """
            SELECT s.completed,m.status
            FROM sprint_tasks AS s
            LEFT JOIN task_metadata AS m
              ON m.task_id=s.id
            WHERE s.id=?
            """,
            (int(row["task_id"]),),
        ).fetchone()
        if (
            task is not None
            and (
                bool(task["completed"])
                or task["status"] == "Completed"
            )
        ):
            conn.execute(
                """
                UPDATE manual_daily_focus
                SET completed_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (int(row["id"]),),
            )

    conn.commit()


def reconcile_daily_focus(conn):
    """Reconcile concrete focus rows only from their actual task state."""
    _restore_manual_focus_rows(
        conn,
        int(
            conn.execute(
                "SELECT COALESCE(MAX(week),1) FROM daily_focus "
                "WHERE focus_date=?",
                (date.today().isoformat(),),
            ).fetchone()[0]
            or 1
        ),
    )
    _backfill_daily_focus_fields(conn)
    focus_date = date.today().isoformat()

    falsely_completed = conn.execute(
        """
        SELECT f.id
        FROM daily_focus AS f
        LEFT JOIN sprint_tasks AS s
          ON s.id=f.task_id
        LEFT JOIN task_metadata AS m
          ON m.task_id=f.task_id
        WHERE f.focus_date=?
          AND f.task_id IS NOT NULL
          AND f.completed_at IS NOT NULL
          AND COALESCE(s.completed,0)=0
          AND COALESCE(m.status,'')<>'Completed'
        """,
        (focus_date,),
    ).fetchall()

    if falsely_completed:
        conn.executemany(
            """
            UPDATE daily_focus
            SET completed_at=NULL
            WHERE id=?
            """,
            [
                (int(row["id"]),)
                for row in falsely_completed
            ],
        )

    rows = conn.execute(
        """
        SELECT
            f.*,
            s.completed AS task_completed,
            m.status AS task_status
        FROM daily_focus AS f
        LEFT JOIN sprint_tasks AS s
          ON s.id=f.task_id
        LEFT JOIN task_metadata AS m
          ON m.task_id=f.task_id
        WHERE f.focus_date=?
          AND f.completed_at IS NULL
        ORDER BY f.position
        """,
        (focus_date,),
    ).fetchall()

    changed = bool(falsely_completed)

    for row in rows:
        complete = False

        if (
            row["task_id"] is not None
            and (
                bool(row["task_completed"])
                or row["task_status"] == "Completed"
            )
        ):
            complete = True

        # Only roadmap fallback rows without a concrete task ID may infer
        # completion from aggregate adaptive-track state.
        if (
            not complete
            and row["task_id"] is None
            and row["track_key"]
        ):
            active = conn.execute(
                """
                SELECT target_key
                FROM track_tasks
                WHERE track_key=?
                """,
                (row["track_key"],),
            ).fetchone()
            active_target = (
                active["target_key"]
                if active is not None
                else None
            )

            if (
                row["target_key"]
                and active_target
                and str(active_target)
                != str(row["target_key"])
            ):
                complete = True
            elif (
                not bool(row["is_extra"])
                and _track_daily_completed(
                    conn,
                    row["track_key"],
                )
            ):
                complete = True

        if complete:
            conn.execute(
                """
                UPDATE daily_focus
                SET completed_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (int(row["id"]),),
            )
            changed = True

    if changed:
        conn.commit()

    _sync_manual_focus_completion(conn)
    return changed




def mark_focus_task_completed(
    conn,
    task_id,
):
    """Freeze the visible daily assignment before an adaptive row is reused."""
    conn.execute(
        """UPDATE daily_focus
           SET completed_at=COALESCE(
               completed_at,
               CURRENT_TIMESTAMP
           )
           WHERE focus_date=?
             AND task_id=?""",
        (
            date.today().isoformat(),
            int(task_id),
        ),
    )
    _backfill_manual_focus_store(conn)
    conn.execute(
        """
        UPDATE manual_daily_focus
        SET completed_at=COALESCE(
                completed_at,
                CURRENT_TIMESTAMP
            ),
            updated_at=CURRENT_TIMESTAMP
        WHERE focus_date=?
          AND task_id=?
        """,
        (
            date.today().isoformat(),
            int(task_id),
        ),
    )
    conn.commit()



def _stored_focus_plan(
    conn,
    week,
):
    focus_date = (
        date.today().isoformat()
    )
    _restore_manual_focus_rows(
        conn,
        int(week),
    )
    rows = conn.execute(
        """SELECT
               f.*,
               m.status,
               m.priority,
               m.destination,
               s.completed AS task_completed
           FROM daily_focus f
           LEFT JOIN sprint_tasks s
             ON s.id=f.task_id
           LEFT JOIN task_metadata m
             ON m.task_id=f.task_id
           WHERE f.focus_date=?
           ORDER BY f.position""",
        (focus_date,),
    ).fetchall()

    if not rows:
        return []

    # PERSIST ADDED TODAY TASKS 1
    # The base recommendation may be regenerated after a sprint-week sync,
    # but rows explicitly added by the learner are durable for the date.
    base_rows = [
        row
        for row in rows
        if not bool(row["is_extra"])
    ]
    extra_rows = [
        row
        for row in rows
        if bool(row["is_extra"])
    ]

    stale_base = any(
        int(row["week"]) != int(week)
        for row in base_rows
    )

    if stale_base:
        conn.execute(
            """DELETE FROM daily_focus
               WHERE focus_date=?
                 AND COALESCE(is_extra,0)=0""",
            (focus_date,),
        )

    if extra_rows:
        conn.execute(
            """UPDATE daily_focus
               SET week=?
               WHERE focus_date=?
                 AND COALESCE(is_extra,0)=1
                 AND week<>?""",
            (
                int(week),
                focus_date,
                int(week),
            ),
        )

    if stale_base or not base_rows:
        conn.commit()
        # Returning no base plan lets intelligent_focus_plan regenerate the
        # scheduled recommendation. _record_focus_plan preserves extra rows.
        return []

    conn.commit()
    reconcile_daily_focus(
        conn
    )
    rows = conn.execute(
        """SELECT
               f.*,
               m.status,
               m.priority,
               m.destination,
               s.completed AS task_completed
           FROM daily_focus f
           LEFT JOIN sprint_tasks s
             ON s.id=f.task_id
           LEFT JOIN task_metadata m
             ON m.task_id=f.task_id
           WHERE f.focus_date=?
           ORDER BY f.position""",
        (focus_date,),
    ).fetchall()

    display_titles = {
        "google": "Google Certificate",
        "academy": "Accelerator Academy",
        "sql": "SQL Practice",
        "portfolio": "Portfolio Project",
        "applied": "Applied Labs",
    }

    result = []
    for row in rows:
        if str(row["track_key"] or "").lower() == "datacamp" or "datacamp" in str(row["title"] or "").lower():
            continue
        source_key = str(
            row["source_key"]
            or ""
        )
        track_key = row[
            "track_key"
        ]
        completed = bool(
            row["completed_at"]
            or row["task_completed"]
            or row["status"]
            == "Completed"
        )
        roadmap_fallback = (
            source_key.startswith(
                "roadmap:"
            )
        )
        result.append(
            {
                "task_id": (
                    int(row["task_id"])
                    if row["task_id"]
                    is not None
                    else None
                ),
                "week": int(
                    row["week"]
                ),
                "sort_order": int(
                    row["position"]
                ),
                "label": row["title"],
                "category": (
                    row["category"]
                    or "General"
                ),
                "status": (
                    "Completed"
                    if completed
                    else (
                        row["status"]
                        or "Not Started"
                    )
                ),
                "priority": int(
                    row["priority"]
                    or 3
                ),
                "estimated_minutes": int(
                    row[
                        "estimated_minutes"
                    ]
                    or 30
                ),
                "destination": int(
                    row["destination"]
                    or 0
                ),
                "carryover": False,
                "carryover_note": None,
                "roadmap_fallback": (
                    roadmap_fallback
                ),
                "source_key": source_key,
                "track_key": track_key,
                "target_key": row[
                    "target_key"
                ],
                "completed": completed,
                "is_extra": bool(
                    row["is_extra"]
                ),
                "display_title": (
                    display_titles.get(
                        track_key
                    )
                    if track_key
                    else None
                ),
                "detail": row["title"],
                "frozen_focus": True,
            }
        )

    return result




def _today_completion_evidence(
    conn,
    week,
):
    """Summarize work completed today when no saved base plan exists."""
    today = date.today().isoformat()
    items = []
    seen = set()

    event_rows = conn.execute(
        """SELECT
               track_key,event_key,
               item_label,metadata
           FROM track_events
           WHERE completed_date=?
             AND event_type='Completed'
           ORDER BY id""",
        (today,),
    ).fetchall()

    category_map = {
        "google": "Learning",
        "academy": "Learning",
        "sql": "SQL",
        "portfolio": "Portfolio",
        "applied": "Learning",
    }

    for row in event_rows:
        if str(row["track_key"] or "").lower() == "datacamp":
            continue
        identity = (
            f"{row['track_key']}:"
            f"{row['event_key']}"
        )
        if identity in seen:
            continue
        seen.add(identity)

        try:
            metadata = json.loads(
                row["metadata"]
                or "{}"
            )
        except (
            TypeError,
            ValueError,
        ):
            metadata = {}

        task_id = metadata.get(
            "task_id"
        )
        estimate = 0
        if task_id is not None:
            task_row = conn.execute(
                """SELECT
                       m.estimated_minutes
                   FROM task_metadata m
                   WHERE m.task_id=?""",
                (int(task_id),),
            ).fetchone()
            if task_row is not None:
                estimate = int(
                    task_row[
                        "estimated_minutes"
                    ]
                    or 0
                )

        items.append(
            {
                "title": (
                    row["item_label"]
                    or row["track_key"].title()
                ),
                "track_key": row[
                    "track_key"
                ],
                "category": category_map.get(
                    row["track_key"],
                    "General",
                ),
                "estimated_minutes": estimate,
            }
        )

    sql_rows = conn.execute(
        """SELECT title
           FROM sql_practice
           WHERE status='Completed'
             AND completed_date=?
           ORDER BY title""",
        (today,),
    ).fetchall()

    for row in sql_rows:
        normalized = (
            "sql:"
            + _normalized_task_label(
                row["title"]
            )
        )
        if any(
            normalized
            in (
                "sql:"
                + _normalized_task_label(
                    item["title"]
                )
            )
            for item in items
        ):
            continue
        items.append(
            {
                "title": row["title"],
                "track_key": "sql",
                "category": "SQL",
                "estimated_minutes": 0,
            }
        )

    session_row = conn.execute(
        """SELECT
               COUNT(*) AS session_count,
               COALESCE(SUM(hours),0) AS hours
           FROM study_sessions
           WHERE session_date=?""",
        (today,),
    ).fetchone()

    return {
        "items": items,
        "count": len(items),
        "minutes": sum(
            int(
                item[
                    "estimated_minutes"
                ]
                or 0
            )
            for item in items
        ),
        "titles": [
            item["title"]
            for item in items
        ],
        "session_count": int(
            session_row[
                "session_count"
            ]
            or 0
        ),
        "session_minutes": int(
            round(
                float(
                    session_row["hours"]
                    or 0
                )
                * 60
            )
        ),
    }


def _empty_plan_is_complete(
    conn,
    week,
    extras,
):
    """Treat a genuinely exhausted day as complete, including upgrade days."""
    if extras:
        # Optional work can only be started after the required day is complete.
        return True

    if available(
        conn,
        week,
    ):
        return False

    for track_key in (
        "google",
        "academy",
        "sql",
        "portfolio",
    ):
        if _track_accepts_work_today(
            conn,
            track_key,
        ):
            return False

    return True


def focus_day_summary(
    items,
    *,
    conn=None,
    week=None,
):
    base = [
        item
        for item in items
        if not item.get(
            "is_extra"
        )
    ]
    extras = [
        item
        for item in items
        if item.get(
            "is_extra"
        )
    ]
    completed_base = [
        item
        for item in base
        if item.get(
            "completed"
        )
    ]
    active_extra = next(
        (
            item
            for item in extras
            if not item.get(
                "completed"
            )
        ),
        None,
    )

    inferred = {
        "items": [],
        "count": 0,
        "minutes": 0,
        "titles": [],
        "session_count": 0,
        "session_minutes": 0,
    }
    inferred_empty_complete = False

    if (
        not base
        and conn is not None
        and week is not None
        and _empty_plan_is_complete(
            conn,
            int(week),
            extras,
        )
    ):
        inferred_empty_complete = True
        inferred = (
            _today_completion_evidence(
                conn,
                int(week),
            )
        )

    regular_complete = (
        bool(base)
        and len(
            completed_base
        )
        == len(base)
    )
    all_complete = (
        regular_complete
        or inferred_empty_complete
    )

    completed_count = (
        len(completed_base)
        if base
        else inferred["count"]
    )
    total_count = (
        len(base)
        if base
        else inferred["count"]
    )
    planned_minutes = (
        sum(
            int(
                item.get(
                    "estimated_minutes",
                    0,
                )
            )
            for item in base
        )
        if base
        else (
            inferred["minutes"]
            or inferred[
                "session_minutes"
            ]
        )
    )
    completed_titles = (
        [
            item.get(
                "display_title"
            )
            or item.get(
                "label"
            )
            or "Task"
            for item in completed_base
        ]
        if base
        else inferred["titles"]
    )

    return {
        "base_items": base,
        "extra_items": extras,
        "completed_base": (
            completed_base
        ),
        "completed_count": (
            completed_count
        ),
        "total_count": (
            total_count
        ),
        "planned_minutes": (
            planned_minutes
        ),
        "all_base_complete": (
            all_complete
        ),
        "active_extra": active_extra,
        "completed_titles": (
            completed_titles
        ),
        "inferred_empty_complete": (
            inferred_empty_complete
        ),
        "session_count": inferred[
            "session_count"
        ],
        "has_completion_evidence": bool(
            inferred["count"]
            or inferred[
                "session_count"
            ]
        ),
    }


def _extra_task_rows(
    conn,
    week,
):
    today = (
        date.today().isoformat()
    )
    return conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status,
               m.priority,
               m.estimated_minutes,
               m.energy,
               m.deferred_until,
               m.destination,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason,
               tt.track_key,
               tt.target_key,
               ts.status AS track_status,
               ts.metadata AS track_metadata
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           LEFT JOIN track_state ts
             ON ts.track_key=tt.track_key
           WHERE s.week=?
             AND s.completed=0
             AND m.status NOT IN (
                 'Completed',
                 'Blocked'
             )
             AND COALESCE(
                 m.prerequisite_state,
                 'Ready'
             )='Ready'
             AND (
                 m.deferred_until IS NULL
                 OR m.deferred_until<=?
             )
           ORDER BY
               CASE
                   WHEN m.status='In Progress'
                       THEN 0
                   ELSE 1
               END,
               m.priority,
               s.sort_order""",
        (
            int(week),
            today,
        ),
    ).fetchall()


def _future_extra_task_rows(
    conn,
    week,
    limit=12,
):
    today = date.today().isoformat()
    return conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status,
               m.priority,
               m.estimated_minutes,
               m.energy,
               m.deferred_until,
               m.destination,
               m.category,
               m.prerequisite_state,
               m.prerequisite_reason,
               tt.track_key,
               tt.target_key,
               ts.status AS track_status,
               ts.metadata AS track_metadata
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           LEFT JOIN track_state ts
             ON ts.track_key=tt.track_key
           WHERE s.week>?
             AND s.completed=0
             AND m.status NOT IN (
                 'Completed',
                 'Blocked'
             )
             AND COALESCE(
                 m.prerequisite_state,
                 'Ready'
             )='Ready'
             AND (
                 m.deferred_until IS NULL
                 OR m.deferred_until<=?
             )
           ORDER BY
               s.week,
               CASE
                   WHEN m.status='In Progress'
                       THEN 0
                   ELSE 1
               END,
               m.priority,
               s.sort_order
           LIMIT ?""",
        (
            int(week),
            today,
            int(limit),
        ),
    ).fetchall()


def _candidate_weekly_gap(
    row,
):
    try:
        metadata = json.loads(
            row["track_metadata"]
            or "{}"
        )
    except (
        TypeError,
        ValueError,
    ):
        metadata = {}

    target = int(
        metadata.get(
            "weekly_target",
            0,
        )
        or 0
    )
    completed = int(
        metadata.get(
            "weekly_completed",
            0,
        )
        or 0
    )
    return max(
        0,
        target - completed,
    )


def _optional_candidate_pool(
    conn,
    week,
    state,
):
    stored = _stored_focus_plan(
        conn,
        week,
    )
    exact_used = {
        _daily_focus_track_identity(
            conn,
            item,
        )
        for item in stored
    }
    used_tracks = {
        str(
            item.get(
                "track_key"
            )
            or ""
        )
        for item in stored
        if item.get(
            "track_key"
        )
    }

    candidates = []
    for row in _extra_task_rows(
        conn,
        week,
    ):
        item = _task_dict(row)
        item["track_key"] = row[
            "track_key"
        ]
        item["target_key"] = row[
            "target_key"
        ]
        item["track_status"] = row[
            "track_status"
        ]
        item["weekly_gap"] = (
            _candidate_weekly_gap(
                row
            )
        )

        identity = (
            _daily_focus_track_identity(
                conn,
                item,
            )
        )
        if identity in exact_used:
            continue

        track_key = str(
            item.get(
                "track_key"
            )
            or ""
        )
        track_status = str(
            item.get(
                "track_status"
            )
            or "Active"
        )
        same_track = (
            track_key in used_tracks
        )

        category_rank = {
            "SQL": 0,
            "Portfolio": 1,
            "Review": 3,
            "Learning": 4,
            "General": 5,
        }.get(
            item["category"],
            5,
        )
        if track_key == "applied":
            category_rank = 2

        track_status_rank = {
            "Active": 0,
            "Daily Complete": 2,
            "Weekly Complete": 4,
            "Complete": 5,
        }.get(
            track_status,
            1,
        )

        if (
            item["weekly_gap"] > 0
            and track_status
            != "Weekly Complete"
        ):
            reason = (
                "Unfinished weekly target"
            )
        elif track_key == "portfolio":
            reason = (
                "Advance the current "
                "portfolio milestone"
            )
        elif (
            track_key == "sql"
            or item["category"]
            == "SQL"
        ):
            reason = (
                "Practice current SQL skills"
            )
        elif track_key == "applied":
            reason = (
                "Complete the next "
                "eligible Applied Lab"
            )
        else:
            reason = (
                "Get ahead on an "
                "eligible roadmap task"
            )

        item["extra_reason"] = reason
        item["_extra_score"] = (
            0
            if item["status"]
            == "In Progress"
            else 1,
            0
            if item["weekly_gap"] > 0
            else 1,
            1
            if same_track
            else 0,
            track_status_rank,
            category_rank,
            item["priority"],
            item["sort_order"],
        )
        candidates.append(
            item
        )

    if not candidates:
        for row in _future_extra_task_rows(
            conn,
            week,
        ):
            item = _task_dict(row)
            item["track_key"] = row[
                "track_key"
            ]
            item["target_key"] = row[
                "target_key"
            ]
            item["track_status"] = row[
                "track_status"
            ]
            item["weekly_gap"] = 0

            identity = (
                _daily_focus_track_identity(
                    conn,
                    item,
                )
            )
            if identity in exact_used:
                continue

            item["extra_reason"] = (
                f"Get ahead on Week "
                f"{int(row['week'])} roadmap work"
            )
            item["_extra_score"] = (
                2,
                2,
                0,
                5,
                {
                    "Portfolio": 0,
                    "SQL": 1,
                    "Learning": 2,
                    "Review": 3,
                    "General": 4,
                }.get(
                    item["category"],
                    4,
                ),
                item["priority"],
                int(row["week"]),
                item["sort_order"],
            )
            candidates.append(
                item
            )

    # External learning tracks may have no distinct real sprint row.
    for fallback in _roadmap_fallbacks(
        conn,
        state,
    ):
        track_key = str(
            fallback["source_key"]
        ).split(
            ":",
            1,
        )[-1]
        active = conn.execute(
            """SELECT target_key
               FROM track_tasks
               WHERE track_key=?""",
            (track_key,),
        ).fetchone()
        fallback["track_key"] = (
            track_key
        )
        fallback["target_key"] = (
            active["target_key"]
            if active is not None
            else None
        )
        identity = (
            _daily_focus_track_identity(
                conn,
                fallback,
            )
        )
        if identity in exact_used:
            continue

        state_row = conn.execute(
            """SELECT status,metadata
               FROM track_state
               WHERE track_key=?""",
            (track_key,),
        ).fetchone()
        if state_row is None:
            continue

        try:
            metadata = json.loads(
                state_row["metadata"]
                or "{}"
            )
        except (
            TypeError,
            ValueError,
        ):
            metadata = {}

        weekly_gap = max(
            0,
            int(
                metadata.get(
                    "weekly_target",
                    0,
                )
                or 0
            )
            - int(
                metadata.get(
                    "weekly_completed",
                    0,
                )
                or 0
            ),
        )
        if (
            weekly_gap <= 0
            and state_row["status"]
            == "Weekly Complete"
        ):
            continue

        fallback["weekly_gap"] = (
            weekly_gap
        )
        fallback["track_status"] = (
            state_row["status"]
        )
        fallback["extra_reason"] = (
            "Get ahead on tomorrow's "
            "external learning"
        )
        fallback["_extra_score"] = (
            1,
            0
            if weekly_gap > 0
            else 1,
            1
            if track_key in used_tracks
            else 0,
            3,
            4,
            fallback["priority"],
            999,
        )
        candidates.append(
            fallback
        )

    deduplicated = []
    seen = set()
    for item in sorted(
        candidates,
        key=lambda candidate:
        candidate["_extra_score"],
    ):
        identity = (
            _daily_focus_track_identity(
                conn,
                item,
            )
        )
        if identity in seen:
            continue
        seen.add(identity)
        deduplicated.append(
            item
        )

    return deduplicated


def optional_focus_candidate(
    conn,
    week,
    state,
):
    plan = _stored_focus_plan(
        conn,
        week,
    )
    summary = focus_day_summary(
        plan,
        conn=conn,
        week=week,
    )
    if not summary[
        "all_base_complete"
    ]:
        return None

    if summary[
        "active_extra"
    ] is not None:
        return summary[
            "active_extra"
        ]

    pool = _optional_candidate_pool(
        conn,
        week,
        state,
    )
    return (
        pool[0]
        if pool
        else None
    )


def start_extra_focus(
    conn,
    week,
    state,
    item,
):
    plan = _stored_focus_plan(
        conn,
        week,
    )
    summary = focus_day_summary(
        plan,
        conn=conn,
        week=week,
    )
    if not summary[
        "all_base_complete"
    ]:
        raise ValueError(
            "Complete today's original "
            "focus plan before starting "
            "optional extra work."
        )
    if summary[
        "active_extra"
    ] is not None:
        return summary[
            "active_extra"
        ]

    track_key, target_key = (
        _focus_track_fields(
            conn,
            item,
        )
    )
    position = conn.execute(
        """SELECT
               COALESCE(MAX(position),0)+1
           FROM daily_focus
           WHERE focus_date=?""",
        (
            date.today().isoformat(),
        ),
    ).fetchone()[0]

    conn.execute(
        """INSERT INTO daily_focus
           (
               focus_date,week,position,
               task_id,source_key,
               category,title,
               estimated_minutes,
               track_key,target_key,
               is_extra
           )
           VALUES(
               ?,?,?,?,?,?,?,?,?,?,1
           )""",
        (
            date.today().isoformat(),
            int(week),
            int(position),
            item.get("task_id"),
            item["source_key"],
            item["category"],
            item["label"],
            int(
                item[
                    "estimated_minutes"
                ]
            ),
            track_key,
            target_key,
        ),
    )

    task_id = item.get(
        "task_id"
    )
    if task_id is not None:
        conn.execute(
            """UPDATE task_metadata
               SET status=CASE
                   WHEN status IN (
                       'Not Started',
                       'Deferred'
                   )
                   THEN 'In Progress'
                   ELSE status
               END,
               deferred_until=NULL
               WHERE task_id=?""",
            (int(task_id),),
        )

    conn.commit()
    return _stored_focus_plan(
        conn,
        week,
    )[-1]


def tomorrow_preview(
    conn,
    week,
    state,
    limit=3,
):
    """Return a non-binding preview without modifying tomorrow's plan."""
    pool = _optional_candidate_pool(
        conn,
        week,
        state,
    )
    result = []
    seen_tracks = set()

    for item in pool:
        track_key = str(
            item.get(
                "track_key"
            )
            or ""
        )
        if (
            track_key
            and track_key
            in seen_tracks
        ):
            continue
        if track_key:
            seen_tracks.add(
                track_key
            )

        result.append(
            {
                "title": (
                    item.get(
                        "display_title"
                    )
                    or {
                        "google": (
                            "Google Certificate"
                        ),
                        "academy": "Accelerator Academy",
                        "sql": "SQL Practice",
                        "portfolio": (
                            "Portfolio Project"
                        ),
                        "applied": (
                            "Applied Labs"
                        ),
                    }.get(
                        track_key,
                        {
                            "SQL": (
                                "SQL Practice"
                            ),
                            "Portfolio": (
                                "Portfolio Project"
                            ),
                            "Review": (
                                "Weekly Review"
                            ),
                            "Learning": (
                                "Learning"
                            ),
                        }.get(
                            item[
                                "category"
                            ],
                            "Roadmap Task",
                        ),
                    )
                ),
                "detail": item[
                    "label"
                ],
                "minutes": int(
                    item[
                        "estimated_minutes"
                    ]
                ),
            }
        )
        if len(result) >= int(
            limit
        ):
            break

    return result



def intelligent_focus_plan(
    conn,
    week,
    guide,
    state,
    max_items=4,
):
    """Build today's focus from task intelligence and roadmap structure.

    Selection order:
    1. Promote up to two unfinished items shown yesterday.
    2. Fill the roadmap's Learning/Learning/SQL/Portfolio slots with
       in-progress and highest-priority real tasks.
    3. Use the hard-coded weekly roadmap only when no real task can
       satisfy a required slot.
    """
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()

    existing_plan = _stored_focus_plan(
        conn,
        week,
    )
    if existing_plan:
        return existing_plan

    current = []
    for row in available(conn, week):
        monday_recovery = (
            _is_monday_recovery_retrospective(
                label=row["label"],
                task_week=row["week"],
                current_week=week,
            )
        )
        current.append(
            _task_dict(
                row,
                carryover=monday_recovery,
                carryover_note=(
                    "Missed Friday"
                    if monday_recovery
                    else None
                ),
            )
        )

    carryover = _carryover_tasks(
        conn,
        yesterday,
        week,
    )

    candidates_by_id = {}

    for item in current:
        candidates_by_id[item["task_id"]] = item

    for item in carryover:
        existing = candidates_by_id.get(item["task_id"])
        if existing:
            existing["carryover"] = True
        else:
            candidates_by_id[item["task_id"]] = item

    candidates = sorted(
        candidates_by_id.values(),
        key=_candidate_sort_key,
    )

    selected = []
    used_task_ids = set()
    used_focus_identities = set()
    remaining_slots = list(FOCUS_SLOT_ORDER)

    # Promote yesterday's unfinished recommendations while preserving
    # at least two roadmap-grounded slots for today's work.
    for item in [
        candidate
        for candidate in candidates
        if (
            candidate["carryover"]
            and _task_allowed_today(
                label=candidate["label"],
                category=candidate["category"],
                task_week=candidate["week"],
                current_week=week,
            )
        )
    ][:2]:
        identity = _focus_identity(conn, item)
        if identity in used_focus_identities:
            continue
        selected.append(item)
        used_task_ids.add(item["task_id"])
        used_focus_identities.add(identity)
        _remove_matching_slot(
            remaining_slots,
            item["category"],
        )

    # Fill each remaining roadmap slot with the best real task of the
    # matching category. In-progress work outranks new work.
    for category in list(remaining_slots):
        matching = [
            candidate
            for candidate in candidates
            if (
                candidate["task_id"] not in used_task_ids
                and _focus_identity(conn, candidate)
                    not in used_focus_identities
                and candidate["category"] == category
                and _task_allowed_today(
                    label=candidate["label"],
                    category=candidate["category"],
                    task_week=candidate["week"],
                    current_week=week,
                )
            )
        ]
        if matching:
            chosen = matching[0]
            selected.append(chosen)
            used_task_ids.add(chosen["task_id"])
            used_focus_identities.add(
                _focus_identity(conn, chosen)
            )

        if len(selected) >= max_items:
            break

    # If unusual carryover/general work left a slot open, use the next
    # highest-impact real task before falling back to template text.
    if len(selected) < max_items:
        for candidate in candidates:
            if candidate["task_id"] in used_task_ids:
                continue
            if (
                _focus_identity(conn, candidate)
                in used_focus_identities
            ):
                continue
            if not _task_allowed_today(
                label=candidate["label"],
                category=candidate["category"],
                task_week=candidate["week"],
                current_week=week,
            ):
                continue
            selected.append(candidate)
            used_task_ids.add(candidate["task_id"])
            used_focus_identities.add(
                _focus_identity(conn, candidate)
            )
            if len(selected) >= max_items:
                break

    # The template remains ground truth and supplies any missing
    # categories when the sprint backlog has no suitable real task.
    if len(selected) < max_items:
        fallbacks = _roadmap_fallbacks(conn, state)
        represented = [
            item["category"]
            for item in selected
        ]

        for slot_index, slot_category in enumerate(
            FOCUS_SLOT_ORDER
        ):
            if len(selected) >= max_items:
                break

            represented_count = represented.count(slot_category)
            required_count = (
                list(FOCUS_SLOT_ORDER)[: slot_index + 1]
                .count(slot_category)
            )
            if represented_count >= required_count:
                continue

            fallback = fallbacks[slot_index]
            fallback_identity = _focus_identity(
                conn,
                fallback,
            )
            if fallback_identity in used_focus_identities:
                continue
            fallback_track = str(
                fallback["source_key"]
            ).split(":", 1)[-1]
            if not _track_accepts_work_today(
                conn,
                fallback_track,
            ):
                continue

            selected.append(fallback)
            represented.append(slot_category)
            used_focus_identities.add(
                fallback_identity
            )

    # The Applied Labs track may reserve one slot when it is actively
    # due. It replaces the matching lower-priority core category when
    # possible, never the Google Certificate assignment.
    applied_candidate = None
    for candidate in candidates:
        link = conn.execute(
            """SELECT track_key
               FROM track_tasks
               WHERE task_id=?""",
            (
                candidate[
                    "task_id"
                ],
            ),
        ).fetchone()
        if (
            link is not None
            and link["track_key"]
            == "applied"
        ):
            applied_candidate = candidate
            break

    if (
        applied_candidate is not None
        and applied_candidate[
            "task_id"
        ] not in used_task_ids
    ):
        if len(selected) < max_items:
            selected.append(
                applied_candidate
            )
            used_task_ids.add(
                applied_candidate[
                    "task_id"
                ]
            )
            used_focus_identities.add(
                _focus_identity(
                    conn,
                    applied_candidate,
                )
            )
        else:
            replaceable = []
            for index, item in enumerate(
                selected
            ):
                item_link = (
                    conn.execute(
                        """SELECT track_key
                           FROM track_tasks
                           WHERE task_id=?""",
                        (
                            item.get(
                                "task_id"
                            ),
                        ),
                    ).fetchone()
                    if item.get(
                        "task_id"
                    )
                    is not None
                    else None
                )
                item_track = (
                    item_link[
                        "track_key"
                    ]
                    if item_link
                    is not None
                    else None
                )
                if item_track == "google":
                    continue
                if item.get(
                    "carryover"
                ):
                    continue
                same_category = (
                    item[
                        "category"
                    ]
                    == applied_candidate[
                        "category"
                    ]
                )
                replaceable.append(
                    (
                        0
                        if same_category
                        else 1,
                        -_focus_track_rank(
                            conn,
                            item,
                        ),
                        index,
                    )
                )

            if replaceable:
                _, _, replace_index = min(
                    replaceable
                )
                removed = selected[
                    replace_index
                ]
                used_task_ids.discard(
                    removed.get(
                        "task_id"
                    )
                )
                used_focus_identities.discard(
                    _focus_identity(
                        conn,
                        removed,
                    )
                )
                selected[
                    replace_index
                ] = applied_candidate
                used_task_ids.add(
                    applied_candidate[
                        "task_id"
                    ]
                )
                used_focus_identities.add(
                    _focus_identity(
                        conn,
                        applied_candidate,
                    )
                )

    selected = _dedupe_focus_items(
        conn,
        _order_focus_items(
            conn,
            selected,
        ),
    )[:max_items]
    _record_focus_plan(conn, week, selected)
    return _stored_focus_plan(
        conn,
        int(week),
    )



def rebuild_today_snapshot(
    conn,
    week,
    guide,
    state,
    max_items=4,
):
    """Discard and regenerate only today's frozen focus recommendation.

    Task completion, study sessions, notes, and all historical daily-focus
    records remain untouched. Only rows for the current calendar date are
    replaced using the live adaptive-planning inputs.
    """
    focus_date = date.today().isoformat()
    _restore_manual_focus_rows(
        conn,
        int(week),
    )
    existing_rows = conn.execute(
        """SELECT
               id,focus_date,week,position,task_id,source_key,category,title,
               estimated_minutes,track_key,target_key,is_extra,completed_at,created_at
           FROM daily_focus
           WHERE focus_date=?
           ORDER BY position""",
        (focus_date,),
    ).fetchall()
    existing_count = sum(
        1
        for row in existing_rows
        if not bool(row["is_extra"])
    )
    # PERSIST ADDED TODAY TASKS 1
    # A manual rebuild replaces the recommendation, not learner-selected work.
    conn.execute(
        """DELETE FROM daily_focus
           WHERE focus_date=?
             AND COALESCE(is_extra,0)=0""",
        (focus_date,),
    )
    conn.commit()

    try:
        rebuilt = intelligent_focus_plan(
            conn,
            int(week),
            guide,
            state,
            max_items=max_items,
        )
    except Exception:
        # A snapshot is derived data, but a failed rebuild should still leave
        # the learner exactly where they started. Restore today's frozen rows
        # before surfacing the error to the Settings page.
        conn.execute(
            """DELETE FROM daily_focus
               WHERE focus_date=?""",
            (focus_date,),
        )
        for row in existing_rows:
            conn.execute(
                """INSERT INTO daily_focus
                   (
                       id,focus_date,week,position,task_id,source_key,category,title,
                       estimated_minutes,track_key,target_key,is_extra,completed_at,created_at
                   )
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                tuple(row),
            )
        conn.commit()
        raise

    return {
        "focus_date": focus_date,
        "removed": existing_count,
        "created": len(rebuilt),
        "items": rebuilt,
    }




def _record_focus_plan(
    conn,
    week,
    selected,
):
    focus_date = (
        date.today().isoformat()
    )
    _restore_manual_focus_rows(
        conn,
        int(week),
    )

    # PERSIST ADDED TODAY TASKS 1
    # Preserve work the learner explicitly added. Only the generated base
    # recommendation is replaceable.
    extra_rows = conn.execute(
        """SELECT id
           FROM daily_focus
           WHERE focus_date=?
             AND COALESCE(is_extra,0)=1
           ORDER BY position,id""",
        (focus_date,),
    ).fetchall()

    # DAILY FOCUS POSITION COLLISION HOTFIX 1
    # Move preserved manual rows out of the positive display range before
    # inserting regenerated base rows. The date/position pair is unique, so
    # waiting until after insertion to move extras can collide mid-rebuild.
    conn.execute(
        """UPDATE daily_focus
           SET position=-(1000000000 + id)
           WHERE focus_date=?
             AND COALESCE(is_extra,0)=1""",
        (focus_date,),
    )

    conn.execute(
        """DELETE FROM daily_focus
           WHERE focus_date=?
             AND COALESCE(is_extra,0)=0""",
        (focus_date,),
    )

    for position, item in enumerate(
        selected,
        start=1,
    ):
        track_key, target_key = (
            _focus_track_fields(
                conn,
                item,
            )
        )
        conn.execute(
            """INSERT INTO daily_focus
               (
                   focus_date,week,
                   position,task_id,
                   source_key,category,
                   title,estimated_minutes,
                   track_key,target_key,
                   is_extra
               )
               VALUES(
                   ?,?,?,?,?,?,?,?,?,?,0
               )""",
            (
                focus_date,
                int(week),
                int(position),
                item.get("task_id"),
                item["source_key"],
                item["category"],
                item["label"],
                int(
                    item[
                        "estimated_minutes"
                    ]
                ),
                track_key,
                target_key,
            ),
        )

    # Place preserved additions directly after the regenerated base plan.
    for position, row in enumerate(
        extra_rows,
        start=len(selected) + 1,
    ):
        conn.execute(
            """UPDATE daily_focus
               SET week=?,position=?
               WHERE id=?""",
            (
                int(week),
                int(position),
                int(row["id"]),
            ),
        )

    conn.commit()
    _sync_manual_focus_completion(conn)




# BEGIN ALWAYS AVAILABLE GET AHEAD V10.21.1
def get_ahead_candidates(conn, week, state, limit=12):
    """Return prerequisite-ready optional work for the Get Ahead browser."""
    requested = max(1, int(limit))
    candidates = [
        dict(item)
        for item in _optional_candidate_pool(
            conn,
            int(week),
            state,
        )
    ]

    seen = set()
    result = []

    def add(item):
        item = dict(item)
        if item.get("task_id") is None and item.get("id") is not None:
            item["task_id"] = item.get("id")
        if item.get("id") is None and item.get("task_id") is not None:
            item["id"] = item.get("task_id")
        identity = _daily_focus_track_identity(conn, item)
        if identity in seen:
            return
        seen.add(identity)
        item.pop("_extra_score", None)
        result.append(item)

    for item in candidates:
        add(item)

    # Add future prerequisite-ready rows independently. They remain browser
    # candidates and are not inserted into Next Tasks automatically.
    for row in _future_extra_task_rows(
        conn,
        int(week),
        limit=max(requested * 3, 24),
    ):
        item = _task_dict(row)
        item["track_key"] = row["track_key"]
        item["target_key"] = row["target_key"]
        item["track_status"] = row["track_status"]
        item["weekly_gap"] = 0
        item["extra_reason"] = (
            f"Get ahead on Week {int(row['week'])} roadmap work"
        )
        add(item)

    return result[:requested]


def start_get_ahead(conn, week, state, item):
    """Add an optional task to today without starting or reconciling it."""
    item = dict(item or {})
    focus_date = date.today().isoformat()

    track_key, target_key = _focus_track_fields(
        conn,
        item,
    )
    task_id = item.get("task_id")
    if task_id is None:
        task_id = item.get("id")

    source_key = (
        item.get("source_key")
        or (
            f"get-ahead:"
            f"{item.get('category','general')}:"
            f"{item.get('label','task')}"
        )
    )

    _store_manual_focus_item(
        conn,
        int(week),
        {
            **item,
            "task_id": task_id,
            "source_key": source_key,
            "track_key": track_key,
            "target_key": target_key,
        },
    )

    if task_id is not None:
        existing = conn.execute(
            """
            SELECT id
            FROM daily_focus
            WHERE focus_date=?
              AND is_extra=1
              AND task_id=?
            LIMIT 1
            """,
            (
                focus_date,
                int(task_id),
            ),
        ).fetchone()
    else:
        existing = conn.execute(
            """
            SELECT id
            FROM daily_focus
            WHERE focus_date=?
              AND is_extra=1
              AND task_id IS NULL
              AND source_key=?
            LIMIT 1
            """,
            (
                focus_date,
                source_key,
            ),
        ).fetchone()

    if existing is not None:
        conn.commit()
        return {
            "id": int(existing["id"]),
            "added": False,
        }

    position = conn.execute(
        """
        SELECT COALESCE(MAX(position),0)+1
        FROM daily_focus
        WHERE focus_date=?
        """,
        (focus_date,),
    ).fetchone()[0]

    cursor = conn.execute(
        """
        INSERT INTO daily_focus (
            focus_date,week,position,
            task_id,source_key,category,title,
            estimated_minutes,track_key,target_key,
            is_extra
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,1)
        """,
        (
            focus_date,
            int(week),
            int(position),
            task_id,
            source_key,
            item.get("category") or "General",
            item.get("label") or "Get Ahead task",
            int(
                item.get(
                    "estimated_minutes",
                    30,
                )
                or 30
            ),
            track_key,
            target_key,
        ),
    )
    conn.commit()
    _restore_manual_focus_rows(
        conn,
        int(week),
    )

    return {
        "id": int(cursor.lastrowid),
        "added": True,
        "task_id": task_id,
        "source_key": source_key,
    }




def started_get_ahead_tasks(conn, week):
    """Return durable Get Ahead work explicitly added to today's plan."""
    try:
        _restore_manual_focus_rows(
            conn,
            int(week),
        )
        _sync_manual_focus_completion(conn)
        rows = conn.execute(
            """
            SELECT
                manual.task_id AS id,
                manual.task_id,
                COALESCE(s.label,manual.title) AS label,
                CASE
                    WHEN manual.completed_at IS NOT NULL
                      OR COALESCE(s.completed,0)=1
                      OR COALESCE(m.status,'')='Completed'
                    THEN 1
                    ELSE 0
                END AS completed,
                COALESCE(
                    m.category,
                    manual.category,
                    'General'
                ) AS category,
                COALESCE(
                    m.estimated_minutes,
                    manual.estimated_minutes,
                    30
                ) AS estimated_minutes,
                manual.source_key,
                manual.track_key,
                manual.target_key,
                manual.week,
                manual.id AS position,
                manual.detail,
                COALESCE(
                    m.destination,
                    manual.destination,
                    0
                ) AS destination,
                1 AS is_extra
            FROM manual_daily_focus AS manual
            LEFT JOIN sprint_tasks AS s
              ON s.id=manual.task_id
            LEFT JOIN task_metadata AS m
              ON m.task_id=manual.task_id
            WHERE manual.focus_date=?
            ORDER BY manual.created_at,manual.id
            """,
            (date.today().isoformat(),),
        ).fetchall()
    except Exception:
        return []

    return [dict(row) for row in rows]



# Existing Today’s Focus Get Ahead controls remain prerequisite-based. Starting
# one inserts it into daily_focus, which is the same explicit "add to today"
# state used by the browser and Next Tasks.
def optional_focus_candidate(conn, week, state):
    plan = _stored_focus_plan(conn, int(week))
    summary = focus_day_summary(
        plan,
        conn=conn,
        week=int(week),
    )
    if summary["active_extra"] is not None:
        return summary["active_extra"]
    candidates = get_ahead_candidates(
        conn,
        int(week),
        state,
        limit=1,
    )
    return candidates[0] if candidates else None


def start_extra_focus(conn, week, state, item):
    return start_get_ahead(
        conn,
        int(week),
        state,
        item,
    )
# END ALWAYS AVAILABLE GET AHEAD V10.21.1
