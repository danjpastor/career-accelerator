from __future__ import annotations

from datetime import date, timedelta
import json
import re

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
    "SQL",
    "Portfolio",
)


def infer(label):
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
            "datacamp",
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
               m.prerequisite_reason
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.week=?
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
               s.sort_order""",
        (week, today),
    ).fetchall()


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


def _task_dict(row, *, carryover=False):
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
        "roadmap_fallback": False,
        "source_key": f"task:{row['id']}",
    }


def _carryover_tasks(conn, focus_date):
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
        _task_dict(row, carryover=True)
        for row in rows
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
    datacamp_meta = _track_metadata(
        conn,
        "datacamp",
    )
    sql_meta = _track_metadata(
        conn,
        "sql",
    )
    portfolio_meta = _track_metadata(
        conn,
        "portfolio",
    )

    datacamp_course = datacamp_meta.get(
        "course",
        "Current DataCamp course",
    )
    datacamp_chapter = datacamp_meta.get(
        "chapter",
        datacamp_meta.get(
            "lesson",
            "next assigned chapter",
        ),
    )
    datacamp_detail = (
        f"{datacamp_course} — "
        f"{datacamp_chapter}"
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
            "label": datacamp_detail,
            "category": "Learning",
            "status": "Roadmap",
            "priority": 1,
            "estimated_minutes": int(
                datacamp_meta.get(
                    "estimated_minutes",
                    45,
                )
            ),
            "destination": 2,
            "carryover": False,
            "roadmap_fallback": True,
            "source_key": "roadmap:datacamp",
            "display_title": "DataCamp",
            "detail": datacamp_detail,
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
                "datacamp": 1,
                "sql": 2,
                "portfolio": 3,
            }.get(link["track_key"], 8)

    source_key = str(
        item.get("source_key") or ""
    )
    if source_key == "roadmap:google":
        return 0
    if source_key == "roadmap:datacamp":
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

    current = [
        _task_dict(row)
        for row in available(conn, week)
    ]
    carryover = _carryover_tasks(conn, yesterday)

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
    remaining_slots = list(FOCUS_SLOT_ORDER)

    # Promote yesterday's unfinished recommendations while preserving
    # at least two roadmap-grounded slots for today's work.
    for item in [
        candidate
        for candidate in candidates
        if candidate["carryover"]
    ][:2]:
        selected.append(item)
        used_task_ids.add(item["task_id"])
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
                and candidate["category"] == category
            )
        ]
        if matching:
            chosen = matching[0]
            selected.append(chosen)
            used_task_ids.add(chosen["task_id"])

        if len(selected) >= max_items:
            break

    # If unusual carryover/general work left a slot open, use the next
    # highest-impact real task before falling back to template text.
    if len(selected) < max_items:
        for candidate in candidates:
            if candidate["task_id"] in used_task_ids:
                continue
            selected.append(candidate)
            used_task_ids.add(candidate["task_id"])
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

    selected = _order_focus_items(
        conn,
        selected,
    )[:max_items]
    _record_focus_plan(conn, week, selected)
    return selected


def _record_focus_plan(conn, week, selected):
    focus_date = date.today().isoformat()

    conn.execute(
        "DELETE FROM daily_focus WHERE focus_date=?",
        (focus_date,),
    )

    for position, item in enumerate(selected, start=1):
        conn.execute(
            """INSERT INTO daily_focus
               (focus_date,week,position,task_id,source_key,
                category,title,estimated_minutes)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                focus_date,
                week,
                position,
                item.get("task_id"),
                item["source_key"],
                item["category"],
                item["label"],
                item["estimated_minutes"],
            ),
        )

    conn.commit()
