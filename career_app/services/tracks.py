from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

from career_app.data.roadmap import (
    DATACAMP_TRACK,
    SQL_COMPANION,
)


TRACK_CONFIG = {
    "google": {
        "display_name": "Google Certificate",
        "category": "Learning",
        "destination": 2,
        "priority": 0,
        "sort_band": -400000,
        "role": "Primary",
    },
    "datacamp": {
        "display_name": "DataCamp",
        "category": "Learning",
        "destination": 2,
        "priority": 1,
        "sort_band": -300000,
        "role": "Supplemental",
    },
    "sql": {
        "display_name": "SQL Practice",
        "category": "SQL",
        "destination": 4,
        "priority": 1,
        "sort_band": -200000,
        "role": "Supplemental",
    },
    "portfolio": {
        "display_name": "Portfolio",
        "category": "Portfolio",
        "destination": 3,
        "priority": 2,
        "sort_band": -100000,
        "role": "Application",
    },
}

TRACK_ORDER = (
    "google",
    "datacamp",
    "sql",
    "portfolio",
)


SKILL_DEFINITIONS = {
    "analytics_foundations": (
        "Analytics Foundations",
        "Google Course 1",
    ),
    "business_framing": (
        "Business Questions and Stakeholders",
        "Google Course 2",
    ),
    "data_preparation": (
        "Data Preparation and Documentation",
        "Google Course 3",
    ),
    "data_cleaning": (
        "Data Cleaning and Validation",
        "Google Course 4",
    ),
    "analysis_foundations": (
        "Analytical Thinking and Metrics",
        "Google Course 5",
    ),
    "sql_fundamentals": (
        "SQL Fundamentals",
        "DataCamp or completed SQL practice",
    ),
    "sql_joins": (
        "SQL Joins",
        "DataCamp joins or completed SQL practice",
    ),
    "sql_intermediate": (
        "Intermediate SQL",
        "DataCamp manipulation or advanced SQL practice",
    ),
    "visualization_foundations": (
        "Data Visualization",
        "Google Course 6",
    ),
    "data_storytelling": (
        "Data Storytelling",
        "Google Course 6",
    ),
    "power_bi_foundations": (
        "Power BI Foundations",
        "DataCamp Power BI",
    ),
    "power_bi": (
        "Power BI Modeling and DAX",
        "DataCamp Power BI modeling",
    ),
    "python_pandas": (
        "Python and pandas",
        "DataCamp Python",
    ),
    "portfolio_delivery": (
        "Portfolio Case Study Delivery",
        "Google capstone progress",
    ),
    "career_readiness": (
        "Career Readiness",
        "Google career course",
    ),
}


GOOGLE_ALIGNMENT = {
    1: "analytics foundations and data literacy",
    2: "business questions, stakeholders, and measurable outcomes",
    3: "data preparation, sourcing, and documentation",
    4: "data cleaning, validation, and integrity",
    5: "analysis, metrics, spreadsheets, and SQL",
    6: "visualization, storytelling, and recommendations",
    7: "advanced analysis and programming concepts",
    8: "capstone development and portfolio evidence",
    9: "career preparation and job-search execution",
}


SQL_REQUIREMENTS = {
    "Aggregation": {"analytics_foundations"},
    "Conditional Logic": {"data_cleaning"},
    "Joins": {"sql_fundamentals"},
    "Arithmetic": {"analysis_foundations"},
    "Window Functions": {"sql_joins"},
    "Ranking": {"sql_joins"},
    "Date Logic": {"sql_intermediate"},
    "Relational Division": {"sql_intermediate"},
}


PROJECT_EXACT_REQUIREMENTS = {
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
    "Run quality checks": {"data_cleaning"},
    "Answer business questions": {
        "analysis_foundations",
        "sql_fundamentals",
    },
    "Save documented queries": {"sql_fundamentals"},
    "Clean data": {"data_cleaning"},
    "Explore distributions": {"analysis_foundations"},
    "Detect anomalies": {"analysis_foundations"},
    "Validate SQL findings": {
        "sql_fundamentals",
        "sql_joins",
    },
    "Build data model": {
        "visualization_foundations",
        "power_bi_foundations",
    },
    "Create DAX measures": {"power_bi"},
    "Build executive dashboard": {
        "power_bi",
        "data_storytelling",
    },
    "Build workload dashboard": {
        "power_bi",
        "data_storytelling",
    },
    "Add filters and drill-through": {"power_bi"},
    "Write executive summary": {"data_storytelling"},
    "Add screenshots": {"visualization_foundations"},
    "Document assumptions and limitations": {
        "analysis_foundations"
    },
    "Finalize README": {"portfolio_delivery"},
    "Publish release": {"portfolio_delivery"},
}


def _json(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )


def _week_bounds(reference=None):
    current = reference or date.today()
    start = current - timedelta(
        days=current.weekday()
    )
    return start, start + timedelta(days=6)


def _days_remaining(reference=None):
    current = reference or date.today()
    return max(1, 7 - current.weekday())


def _state_row(conn, track_key):
    return conn.execute(
        """SELECT *
           FROM track_state
           WHERE track_key=?""",
        (track_key,),
    ).fetchone()


def _weekly_completed(conn, track_key):
    start, end = _week_bounds()
    return conn.execute(
        """SELECT COUNT(*)
           FROM track_events
           WHERE track_key=?
             AND completed_date BETWEEN ? AND ?""",
        (
            track_key,
            start.isoformat(),
            end.isoformat(),
        ),
    ).fetchone()[0]


def adaptive_targets(state, *, portfolio_ready=True):
    """Allocate the weekly study budget with certificate-first priority."""
    hours = max(
        1.0,
        float(state["weekly_target_hours"]),
    )

    google_minutes = int(hours * 60 * 0.70)
    google_target = max(
        1,
        min(
            6,
            math.ceil(
                google_minutes / 120
            ),
        ),
    )

    datacamp_target = (
        2
        if hours >= 14
        else 1
        if hours >= 6
        else 0
    )
    sql_target = (
        3
        if hours >= 16
        else 2
        if hours >= 10
        else 1
        if hours >= 5
        else 0
    )
    portfolio_target = (
        2
        if portfolio_ready and hours >= 20
        else 1
        if portfolio_ready and hours >= 10
        else 0
    )

    return {
        "google": {
            "weekly_target": google_target,
            "allocation_percent": 70,
            "allocation_minutes": google_minutes,
        },
        "datacamp": {
            "weekly_target": datacamp_target,
            "allocation_percent": 12,
            "allocation_minutes": int(
                hours * 60 * 0.12
            ),
        },
        "sql": {
            "weekly_target": sql_target,
            "allocation_percent": 10,
            "allocation_minutes": int(
                hours * 60 * 0.10
            ),
        },
        "portfolio": {
            "weekly_target": portfolio_target,
            "allocation_percent": 8,
            "allocation_minutes": int(
                hours * 60 * 0.08
            ),
        },
    }


def _pace_metadata(
    *,
    weekly_target,
    weekly_completed,
    role,
    allocation_percent,
):
    days_left = _days_remaining()
    remaining = max(
        0,
        int(weekly_target)
        - int(weekly_completed),
    )
    today_target = (
        math.ceil(
            remaining / days_left
        )
        if remaining
        else 0
    )

    elapsed_before_today = max(
        0,
        date.today().weekday(),
    )
    expected_before_today = math.floor(
        int(weekly_target)
        * elapsed_before_today
        / 7
    )
    behind = max(
        0,
        expected_before_today
        - int(weekly_completed),
    )

    if weekly_target <= 0:
        pace_status = "Paused for certificate focus"
    elif remaining <= 0:
        pace_status = "Weekly goal complete"
    elif behind:
        pace_status = f"Catch up by {behind}"
    else:
        pace_status = "On pace"

    return {
        "role": role,
        "weekly_target": int(
            weekly_target
        ),
        "weekly_completed": int(
            weekly_completed
        ),
        "remaining_this_week": remaining,
        "today_target": today_target,
        "days_remaining": days_left,
        "allocation_percent": int(
            allocation_percent
        ),
        "pace_status": pace_status,
    }


def _upsert_state(
    conn,
    track_key,
    *,
    position=0,
    subposition=0,
    weekly_target=1,
    status="Active",
    metadata=None,
):
    config = TRACK_CONFIG[track_key]
    conn.execute(
        """INSERT INTO track_state
           (track_key,display_name,position,subposition,
            weekly_target,status,metadata,updated_at)
           VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(track_key)
           DO UPDATE SET
               display_name=excluded.display_name,
               position=excluded.position,
               subposition=excluded.subposition,
               weekly_target=excluded.weekly_target,
               status=excluded.status,
               metadata=excluded.metadata,
               updated_at=CURRENT_TIMESTAMP""",
        (
            track_key,
            config["display_name"],
            int(position),
            int(subposition),
            int(weekly_target),
            status,
            _json(metadata or {}),
        ),
    )


def _record_event(
    conn,
    track_key,
    event_key,
    item_label,
    *,
    event_type="Completed",
    metadata=None,
):
    conn.execute(
        """INSERT OR IGNORE INTO track_events
           (track_key,event_key,event_type,item_label,
            completed_date,metadata)
           VALUES(?,?,?,?,?,?)""",
        (
            track_key,
            event_key,
            event_type,
            item_label,
            date.today().isoformat(),
            _json(metadata or {}),
        ),
    )


def _active_link(conn, track_key):
    return conn.execute(
        """SELECT
               tt.track_key,
               tt.task_id,
               tt.target_key,
               tt.source_label,
               tt.linked_entity_id,
               s.week,
               s.sort_order,
               s.label,
               s.completed,
               m.status
           FROM track_tasks tt
           JOIN sprint_tasks s
             ON s.id=tt.task_id
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE tt.track_key=?""",
        (track_key,),
    ).fetchone()


def _next_sort_order(
    conn,
    week,
    track_key,
):
    base = TRACK_CONFIG[
        track_key
    ]["sort_band"]
    used = {
        int(row["sort_order"])
        for row in conn.execute(
            """SELECT sort_order
               FROM sprint_tasks
               WHERE week=?
                 AND sort_order<=?
                 AND sort_order>?""",
            (
                week,
                base,
                base - 99999,
            ),
        ).fetchall()
    }

    candidate = base
    while candidate in used:
        candidate -= 1
    return candidate


def _candidate_task(
    conn,
    *,
    track_key,
    week,
    label,
):
    row = conn.execute(
        """SELECT s.id
           FROM sprint_tasks s
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.completed=0
             AND tt.task_id IS NULL
             AND (
                 s.label=?
                 OR (
                     ?='datacamp'
                     AND LOWER(s.label)
                         LIKE '%datacamp%'
                 )
             )
           ORDER BY
               CASE
                   WHEN s.week=? THEN 0
                   ELSE 1
               END,
               s.id
           LIMIT 1""",
        (
            label,
            track_key,
            week,
        ),
    ).fetchone()
    return row["id"] if row else None


def _ensure_task(
    conn,
    *,
    track_key,
    week,
    target_key,
    label,
    source_label,
    estimate,
    linked_entity_id=None,
):
    config = TRACK_CONFIG[track_key]
    active = _active_link(
        conn,
        track_key,
    )

    if (
        active
        and active["target_key"]
        == target_key
    ):
        task_id = active["task_id"]
        target_changed = (
            int(active["week"])
            != int(week)
            or active["label"] != label
        )

        if target_changed:
            conn.execute(
                """UPDATE sprint_tasks
                   SET week=?,
                       sort_order=?,
                       label=?,
                       completed=0
                   WHERE id=?""",
                (
                    int(week),
                    _next_sort_order(
                        conn,
                        int(week),
                        track_key,
                    ),
                    label,
                    task_id,
                ),
            )

        conn.execute(
            """UPDATE task_metadata
               SET status=CASE
                       WHEN status='Completed'
                       THEN 'In Progress'
                       ELSE status
                   END,
                   priority=?,
                   estimated_minutes=?,
                   energy='Normal',
                   deferred_until=NULL,
                   destination=?,
                   category=?,
                   prerequisite_state='Ready',
                   prerequisite_reason=NULL
               WHERE task_id=?""",
            (
                config["priority"],
                int(estimate),
                config["destination"],
                config["category"],
                task_id,
            ),
        )
        conn.execute(
            """UPDATE track_tasks
               SET source_label=?,
                   linked_entity_id=?,
                   updated_at=CURRENT_TIMESTAMP
               WHERE track_key=?""",
            (
                source_label,
                linked_entity_id,
                track_key,
            ),
        )
        return task_id

    if active:
        conn.execute(
            """DELETE FROM track_tasks
               WHERE track_key=?""",
            (track_key,),
        )

    task_id = _candidate_task(
        conn,
        track_key=track_key,
        week=int(week),
        label=label,
    )
    sort_order = _next_sort_order(
        conn,
        int(week),
        track_key,
    )

    if task_id is None:
        cursor = conn.execute(
            """INSERT INTO sprint_tasks
               (week,sort_order,label,completed)
               VALUES(?,?,?,0)""",
            (
                int(week),
                sort_order,
                label,
            ),
        )
        task_id = cursor.lastrowid
    else:
        conn.execute(
            """UPDATE sprint_tasks
               SET week=?,
                   sort_order=?,
                   label=?,
                   completed=0
               WHERE id=?""",
            (
                int(week),
                sort_order,
                label,
                task_id,
            ),
        )

    conn.execute(
        """INSERT INTO task_metadata
           (task_id,status,priority,estimated_minutes,
            energy,destination,category,
            prerequisite_state,prerequisite_reason)
           VALUES(?,?,?,?,?,?,?,?,?)
           ON CONFLICT(task_id)
           DO UPDATE SET
               status='In Progress',
               priority=excluded.priority,
               estimated_minutes=excluded.estimated_minutes,
               energy=excluded.energy,
               deferred_until=NULL,
               destination=excluded.destination,
               category=excluded.category,
               prerequisite_state='Ready',
               prerequisite_reason=NULL""",
        (
            task_id,
            "In Progress",
            config["priority"],
            int(estimate),
            "Normal",
            config["destination"],
            config["category"],
            "Ready",
            None,
        ),
    )

    conn.execute(
        """INSERT INTO track_tasks
           (track_key,task_id,target_key,source_label,
            linked_entity_id,updated_at)
           VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(track_key)
           DO UPDATE SET
               task_id=excluded.task_id,
               target_key=excluded.target_key,
               source_label=excluded.source_label,
               linked_entity_id=excluded.linked_entity_id,
               updated_at=CURRENT_TIMESTAMP""",
        (
            track_key,
            task_id,
            target_key,
            source_label,
            linked_entity_id,
        ),
    )
    return task_id


def _google_target(
    state,
    pace,
):
    course = max(
        1,
        int(state["google_course"]),
    )
    module = max(
        1,
        int(state["google_module"]),
    )
    alignment = GOOGLE_ALIGNMENT.get(
        course,
        "the current certificate material",
    )
    metadata = {
        "course": course,
        "module": module,
        "alignment": alignment,
        "primary_goal": (
            "Complete the certificate as quickly "
            "and efficiently as possible."
        ),
    }
    metadata.update(pace)

    return {
        "target_key": (
            f"course:{course}:module:{module}"
        ),
        "label": (
            f"Continue Google Course {course}, "
            f"Module {module}"
        ),
        "source_label": (
            f"Google • Course {course}, "
            f"Module {module}"
        ),
        "estimate": 90,
        "position": course,
        "subposition": module,
        "metadata": metadata,
    }


def _datacamp_alignment(course):
    if course <= 2:
        return (
            "Reinforces foundational data "
            "and querying concepts."
        )
    if course == 3:
        return (
            "Supports data preparation "
            "and structured exploration."
        )
    if course == 4:
        return (
            "Supports cleaning, filtering, "
            "and validation work."
        )
    if course == 5:
        return (
            "Supports Course 5 analysis "
            "and SQL practice."
        )
    if course == 6:
        return (
            "Supports visualization "
            "and dashboard development."
        )
    if course == 7:
        return (
            "Supports programming "
            "and advanced analysis."
        )
    return (
        "Supports capstone and portfolio "
        "delivery."
    )


def _datacamp_target(
    conn,
    state,
    pace,
):
    row = _state_row(
        conn,
        "datacamp",
    )
    position = (
        int(row["position"])
        if row else 0
    )

    if position >= len(DATACAMP_TRACK):
        return None

    course_name, lesson, estimate = (
        DATACAMP_TRACK[position]
    )
    metadata = {
        "course": course_name,
        "lesson": lesson,
        "total_items": len(
            DATACAMP_TRACK
        ),
        "alignment": _datacamp_alignment(
            int(state["google_course"])
        ),
    }
    metadata.update(pace)

    return {
        "target_key": f"item:{position}",
        "label": (
            f"Continue DataCamp: {lesson}"
        ),
        "source_label": (
            f"DataCamp • {course_name}"
        ),
        "estimate": estimate,
        "position": position,
        "subposition": 0,
        "metadata": metadata,
    }


def _completed_sql(conn):
    return {
        row["title"]
        for row in conn.execute(
            """SELECT title
               FROM sql_practice
               WHERE status='Completed'"""
        ).fetchall()
    }


def _derived_skills(conn, state):
    course = int(
        state["google_course"]
    )
    datacamp = _state_row(
        conn,
        "datacamp",
    )
    data_position = (
        int(datacamp["position"])
        if datacamp else 0
    )
    sql_count = len(_completed_sql(conn))

    skills = set()

    # Current course means prior courses are complete.
    if course > 1:
        skills.add("analytics_foundations")
    if course > 2:
        skills.add("business_framing")
    if course > 3:
        skills.add("data_preparation")
    if course > 4:
        skills.add("data_cleaning")
    if course > 5:
        skills.add("analysis_foundations")
    if course > 6:
        skills.update(
            {
                "visualization_foundations",
                "data_storytelling",
            }
        )
    if course > 8:
        skills.add("portfolio_delivery")
    if course > 9:
        skills.add("career_readiness")

    if data_position >= 3 or sql_count >= 2:
        skills.add("sql_fundamentals")
    if data_position >= 7 or sql_count >= 5:
        skills.add("sql_joins")
    if data_position >= 9 or sql_count >= 9:
        skills.add("sql_intermediate")
    if data_position >= 10:
        skills.add("power_bi_foundations")
    if data_position >= 11:
        skills.add("power_bi")
    if data_position >= 12:
        skills.add("python_pandas")

    return skills


def _sync_skill_state(
    conn,
    state,
):
    unlocked = _derived_skills(
        conn,
        state,
    )

    for (
        skill_key,
        (
            display_name,
            evidence,
        ),
    ) in SKILL_DEFINITIONS.items():
        status = (
            "Unlocked"
            if skill_key in unlocked
            else "Locked"
        )
        source_track = (
            "google"
            if skill_key
            in {
                "analytics_foundations",
                "business_framing",
                "data_preparation",
                "data_cleaning",
                "analysis_foundations",
                "visualization_foundations",
                "data_storytelling",
                "portfolio_delivery",
                "career_readiness",
            }
            else "datacamp_sql"
        )

        conn.execute(
            """INSERT INTO skill_state
               (skill_key,display_name,status,
                source_track,evidence,updated_at)
               VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(skill_key)
               DO UPDATE SET
                   display_name=excluded.display_name,
                   status=excluded.status,
                   source_track=excluded.source_track,
                   evidence=excluded.evidence,
                   updated_at=CURRENT_TIMESTAMP""",
            (
                skill_key,
                display_name,
                status,
                source_track,
                evidence,
            ),
        )

    return unlocked


def _requirements_for_project(
    label,
    stage=None,
):
    if label in PROJECT_EXACT_REQUIREMENTS:
        return set(
            PROJECT_EXACT_REQUIREMENTS[
                label
            ]
        )

    lower = label.lower()
    requirements = set()

    if any(
        token in lower
        for token in (
            "business problem",
            "stakeholder",
            "kpi",
            "business question",
            "charter",
        )
    ):
        requirements.add(
            "business_framing"
        )

    if any(
        token in lower
        for token in (
            "dataset",
            "data dictionary",
            "source",
            "specification",
        )
    ):
        requirements.add(
            "data_preparation"
        )

    if any(
        token in lower
        for token in (
            "clean",
            "quality",
            "validate data",
        )
    ):
        requirements.add(
            "data_cleaning"
        )

    if any(
        token in lower
        for token in (
            "schema",
            "load data",
            "query",
            "sql",
            "relationship",
        )
    ):
        requirements.add(
            "sql_fundamentals"
        )

    if any(
        token in lower
        for token in (
            "dashboard",
            "dax",
            "data model",
            "drill-through",
            "measure",
        )
    ):
        requirements.add("power_bi")

    if any(
        token in lower
        for token in (
            "executive summary",
            "recommendation",
            "story",
        )
    ):
        requirements.add(
            "data_storytelling"
        )

    if any(
        token in lower
        for token in (
            "readme",
            "publish",
            "release",
            "walkthrough",
        )
    ):
        requirements.add(
            "portfolio_delivery"
        )

    if not requirements:
        requirements.add(
            "analytics_foundations"
        )

    return requirements


def _missing_skill_names(
    required,
    unlocked,
):
    missing = sorted(
        set(required)
        - set(unlocked)
    )
    return [
        SKILL_DEFINITIONS[
            skill
        ][0]
        for skill in missing
    ]


def _sql_target(
    conn,
    state,
    pace,
    unlocked,
):
    completed = _completed_sql(conn)
    course = int(
        state["google_course"]
    )

    locked_candidates = []

    for index, item in enumerate(
        SQL_COMPANION
    ):
        (
            title,
            difficulty,
            topic,
            concepts,
            _,
            estimate,
        ) = item

        if title in completed:
            continue

        required = SQL_REQUIREMENTS.get(
            topic,
            {"analytics_foundations"},
        )
        missing = set(required) - set(
            unlocked
        )
        if missing:
            locked_candidates.append(
                (
                    index,
                    title,
                    difficulty,
                    topic,
                    concepts,
                    estimate,
                    required,
                    missing,
                )
            )
            continue

        metadata = {
            "title": title,
            "difficulty": difficulty,
            "topic": topic,
            "concepts": concepts,
            "total_items": len(
                SQL_COMPANION
            ),
            "alignment": (
                f"Reinforces Course {course} "
                f"{GOOGLE_ALIGNMENT.get(course, 'skills')}."
            ),
            "required_skills": sorted(
                required
            ),
        }
        metadata.update(pace)

        return {
            "target_key": (
                f"problem:{title}"
            ),
            "label": f"Solve {title}",
            "source_label": (
                f"SQL Practice • {topic}"
            ),
            "estimate": estimate,
            "position": len(completed),
            "subposition": index,
            "metadata": metadata,
        }

    if locked_candidates:
        (
            index,
            title,
            difficulty,
            topic,
            concepts,
            _estimate,
            required,
            missing,
        ) = locked_candidates[0]

        missing_names = [
            SKILL_DEFINITIONS[
                skill
            ][0]
            for skill in sorted(missing)
        ]
        metadata = {
            "title": title,
            "difficulty": difficulty,
            "topic": topic,
            "concepts": concepts,
            "total_items": len(
                SQL_COMPANION
            ),
            "required_skills": sorted(
                required
            ),
            "missing_skills": missing_names,
            "blocked_reason": (
                "Learn first: "
                + ", ".join(
                    missing_names
                )
            ),
        }
        metadata.update(pace)

        return {
            "locked": True,
            "position": len(completed),
            "subposition": index,
            "metadata": metadata,
        }

    return None

def _portfolio_target(
    conn,
    state,
    pace,
    unlocked,
):
    project_id = max(
        1,
        int(state["current_project"]),
    )
    row = conn.execute(
        """SELECT id,sort_order,stage,label
           FROM project_tasks
           WHERE project_id=?
             AND completed=0
           ORDER BY sort_order
           LIMIT 1""",
        (project_id,),
    ).fetchone()

    completed = conn.execute(
        """SELECT COUNT(*)
           FROM project_tasks
           WHERE project_id=?
             AND completed=1""",
        (project_id,),
    ).fetchone()[0]
    total = conn.execute(
        """SELECT COUNT(*)
           FROM project_tasks
           WHERE project_id=?""",
        (project_id,),
    ).fetchone()[0]

    if row is None:
        return None

    required = _requirements_for_project(
        row["label"],
        row["stage"],
    )
    missing_names = _missing_skill_names(
        required,
        unlocked,
    )

    metadata = {
        "project_id": project_id,
        "stage": row["stage"],
        "milestone": row["label"],
        "completed": completed,
        "total": total,
        "required_skills": sorted(
            required
        ),
        "missing_skills": missing_names,
    }
    metadata.update(pace)

    if missing_names:
        metadata["blocked_reason"] = (
            "Learn first: "
            + ", ".join(missing_names)
        )
        return {
            "locked": True,
            "position": completed,
            "subposition": int(
                row["sort_order"]
            ),
            "metadata": metadata,
        }

    metadata["alignment"] = (
        "All prerequisite skills are unlocked."
    )
    return {
        "target_key": (
            f"project:{project_id}:"
            f"task:{row['id']}"
        ),
        "label": row["label"],
        "source_label": (
            f"Portfolio • Project "
            f"{project_id} • {row['stage']}"
        ),
        "estimate": 45,
        "position": completed,
        "subposition": int(
            row["sort_order"]
        ),
        "linked_entity_id": int(
            row["id"]
        ),
        "metadata": metadata,
    }


def _sync_sprint_prerequisites(
    conn,
    state,
    unlocked,
):
    active_ids = {
        int(row["task_id"])
        for row in conn.execute(
            "SELECT task_id FROM track_tasks"
        ).fetchall()
    }

    sql_lookup = {
        item[0]: item
        for item in SQL_COMPANION
    }

    rows = conn.execute(
        """SELECT
               s.id,s.label,s.completed,
               m.category,m.status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id"""
    ).fetchall()

    for row in rows:
        task_id = int(row["id"])

        if row["completed"]:
            conn.execute(
                """UPDATE task_metadata
                   SET prerequisite_state='Ready',
                       prerequisite_reason=NULL
                   WHERE task_id=?""",
                (task_id,),
            )
            continue

        if task_id in active_ids:
            conn.execute(
                """UPDATE task_metadata
                   SET prerequisite_state='Ready',
                       prerequisite_reason=NULL
                   WHERE task_id=?""",
                (task_id,),
            )
            continue

        label = row["label"]
        lower = label.lower()
        required = set()
        reason = None

        google_match = re.match(
            r"^\[Google Course (\d+)\]",
            label,
            re.IGNORECASE,
        )
        if google_match:
            target_course = int(
                google_match.group(1)
            )
            if target_course > int(
                state["google_course"]
            ):
                reason = (
                    f"Reach Google Course "
                    f"{target_course} first."
                )

        elif "datacamp" in lower:
            reason = (
                "Managed by the independent "
                "DataCamp track."
            )

        elif row["category"] == "SQL":
            title = re.sub(
                r"^Solve\s+",
                "",
                label,
                flags=re.IGNORECASE,
            )
            item = sql_lookup.get(title)
            if item:
                required = (
                    SQL_REQUIREMENTS.get(
                        item[2],
                        {
                            "analytics_foundations"
                        },
                    )
                )

        elif row["category"] == "Portfolio":
            required = (
                _requirements_for_project(
                    label
                )
            )

        missing = _missing_skill_names(
            required,
            unlocked,
        )
        if missing:
            reason = (
                "Learn first: "
                + ", ".join(missing)
            )

        conn.execute(
            """UPDATE task_metadata
               SET prerequisite_state=?,
                   prerequisite_reason=?
               WHERE task_id=?""",
            (
                (
                    "Blocked"
                    if reason
                    else "Ready"
                ),
                reason,
                task_id,
            ),
        )



def repair_track_links(conn):
    """Remove stale links and duplicate active tasks safely."""
    conn.execute(
        """DELETE FROM track_tasks
           WHERE task_id NOT IN (
               SELECT id
               FROM sprint_tasks
           )"""
    )

    duplicate_rows = conn.execute(
        """SELECT tt.track_key,tt.task_id
           FROM track_tasks tt
           JOIN sprint_tasks s
             ON s.id=tt.task_id
           WHERE s.completed=1"""
    ).fetchall()

    for row in duplicate_rows:
        conn.execute(
            """DELETE FROM track_tasks
               WHERE track_key=?""",
            (row["track_key"],),
        )

    active_ids = {
        int(row["task_id"])
        for row in conn.execute(
            "SELECT task_id FROM track_tasks"
        ).fetchall()
    }

    # Retire orphaned negative-sort track tasks that are no longer linked.
    orphan_rows = conn.execute(
        """SELECT s.id
           FROM sprint_tasks s
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.sort_order<0
             AND tt.task_id IS NULL
             AND s.completed=0"""
    ).fetchall()

    for row in orphan_rows:
        task_id = int(row["id"])
        if task_id in active_ids:
            continue
        conn.execute(
            """UPDATE sprint_tasks
               SET completed=1
               WHERE id=?""",
            (task_id,),
        )
        conn.execute(
            """UPDATE task_metadata
               SET status='Completed',
                   prerequisite_state='Ready',
                   prerequisite_reason=NULL
               WHERE task_id=?""",
            (task_id,),
        )

    conn.commit()


def health_report(conn, state):
    snapshot_data = snapshot(
        conn,
        state,
    )
    issues = []

    for track_key in TRACK_ORDER:
        track = snapshot_data[
            track_key
        ]
        if (
            track["status"] == "Active"
            and track["task_id"] is None
        ):
            issues.append(
                f"{track_key}: active without task"
            )
        if (
            track["status"] == "Locked"
            and track["task_id"] is not None
        ):
            issues.append(
                f"{track_key}: locked with active task"
            )

    duplicate_task_count = conn.execute(
        """SELECT COUNT(*)
           FROM (
               SELECT task_id
               FROM track_tasks
               GROUP BY task_id
               HAVING COUNT(*)>1
           )"""
    ).fetchone()[0]
    if duplicate_task_count:
        issues.append(
            "duplicate active track links"
        )

    blocked_visible = conn.execute(
        """SELECT COUNT(*)
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.week=?
             AND s.completed=0
             AND COALESCE(
                 m.prerequisite_state,
                 'Ready'
             )<>'Ready'
             AND s.id IN (
                 SELECT task_id
                 FROM track_tasks
             )""",
        (int(state["current_week"]),),
    ).fetchone()[0]
    if blocked_visible:
        issues.append(
            "blocked task linked as active"
        )

    return {
        "healthy": not issues,
        "issues": issues,
        "track_count": len(
            snapshot_data
        ),
    }

def initialize(conn, state):
    defaults = {
        "google": (
            int(state["google_course"]),
            int(state["google_module"]),
        ),
        "datacamp": (0, 0),
        "sql": (
            len(_completed_sql(conn)),
            0,
        ),
        "portfolio": (0, 0),
    }

    for track_key in TRACK_ORDER:
        if _state_row(conn, track_key):
            continue
        position, subposition = defaults[
            track_key
        ]
        _upsert_state(
            conn,
            track_key,
            position=position,
            subposition=subposition,
            weekly_target=1,
            status="Active",
            metadata={},
        )
    conn.commit()


def sync_all(conn, state):
    repair_track_links(conn)
    initialize(conn, state)

    unlocked = _sync_skill_state(
        conn,
        state,
    )

    preliminary_targets = (
        adaptive_targets(
            state,
            portfolio_ready=True,
        )
    )
    portfolio_preview = _portfolio_target(
        conn,
        state,
        {},
        unlocked,
    )
    portfolio_ready = not (
        portfolio_preview
        and portfolio_preview.get(
            "locked"
        )
    )
    allocations = adaptive_targets(
        state,
        portfolio_ready=portfolio_ready,
    )

    weekly = {
        track_key: _weekly_completed(
            conn,
            track_key,
        )
        for track_key in TRACK_ORDER
    }

    pace = {
        track_key: _pace_metadata(
            weekly_target=allocations[
                track_key
            ]["weekly_target"],
            weekly_completed=weekly[
                track_key
            ],
            role=TRACK_CONFIG[
                track_key
            ]["role"],
            allocation_percent=allocations[
                track_key
            ]["allocation_percent"],
        )
        for track_key in TRACK_ORDER
    }

    week = max(
        1,
        int(state["current_week"]),
    )
    targets = {
        "google": _google_target(
            state,
            pace["google"],
        ),
        "datacamp": _datacamp_target(
            conn,
            state,
            pace["datacamp"],
        ),
        "sql": _sql_target(
            conn,
            state,
            pace["sql"],
            unlocked,
        ),
        "portfolio": _portfolio_target(
            conn,
            state,
            pace["portfolio"],
            unlocked,
        ),
    }

    for track_key in TRACK_ORDER:
        target = targets[track_key]

        if (
            target
            and target.get("locked")
        ):
            conn.execute(
                """DELETE FROM track_tasks
                   WHERE track_key=?""",
                (track_key,),
            )
            _upsert_state(
                conn,
                track_key,
                position=target[
                    "position"
                ],
                subposition=target[
                    "subposition"
                ],
                weekly_target=allocations[
                    track_key
                ]["weekly_target"],
                status="Locked",
                metadata=target[
                    "metadata"
                ],
            )
            continue

        if (
            allocations[track_key][
                "weekly_target"
            ] <= 0
            and track_key != "google"
        ):
            conn.execute(
                """DELETE FROM track_tasks
                   WHERE track_key=?""",
                (track_key,),
            )
            existing = _state_row(
                conn,
                track_key,
            )
            metadata = dict(
                pace[track_key]
            )
            metadata["alignment"] = (
                "Paused to protect certificate "
                "study time."
            )
            _upsert_state(
                conn,
                track_key,
                position=(
                    int(existing["position"])
                    if existing else 0
                ),
                subposition=(
                    int(existing["subposition"])
                    if existing else 0
                ),
                weekly_target=0,
                status="Paused",
                metadata=metadata,
            )
            continue

        if target is None:
            conn.execute(
                """DELETE FROM track_tasks
                   WHERE track_key=?""",
                (track_key,),
            )
            existing = _state_row(
                conn,
                track_key,
            )
            metadata = dict(
                pace[track_key]
            )
            metadata["complete"] = True
            _upsert_state(
                conn,
                track_key,
                position=(
                    int(existing["position"])
                    if existing else 0
                ),
                subposition=(
                    int(existing["subposition"])
                    if existing else 0
                ),
                weekly_target=allocations[
                    track_key
                ]["weekly_target"],
                status="Completed",
                metadata=metadata,
            )
            continue

        _upsert_state(
            conn,
            track_key,
            position=target["position"],
            subposition=target[
                "subposition"
            ],
            weekly_target=allocations[
                track_key
            ]["weekly_target"],
            status="Active",
            metadata=target["metadata"],
        )
        _ensure_task(
            conn,
            track_key=track_key,
            week=week,
            target_key=target[
                "target_key"
            ],
            label=target["label"],
            source_label=target[
                "source_label"
            ],
            estimate=target["estimate"],
            linked_entity_id=target.get(
                "linked_entity_id"
            ),
        )

    _sync_sprint_prerequisites(
        conn,
        state,
        unlocked,
    )
    conn.commit()


def task_track(conn, task_id):
    return conn.execute(
        """SELECT *
           FROM track_tasks
           WHERE task_id=?""",
        (task_id,),
    ).fetchone()


def source_for_task(conn, task_id):
    row = task_track(
        conn,
        task_id,
    )
    return (
        row["source_label"]
        if row else None
    )


def task_detail(conn, task_id):
    link = task_track(
        conn,
        task_id,
    )
    if link is None:
        return None

    state_row = _state_row(
        conn,
        link["track_key"],
    )
    if state_row is None:
        return None

    metadata = json.loads(
        state_row["metadata"]
        or "{}"
    )
    role = metadata.get(
        "role",
        TRACK_CONFIG[
            link["track_key"]
        ]["role"],
    )
    completed = int(
        metadata.get(
            "weekly_completed",
            0,
        )
    )
    target = int(
        metadata.get(
            "weekly_target",
            state_row["weekly_target"],
        )
    )
    today = int(
        metadata.get(
            "today_target",
            0,
        )
    )
    pace_status = metadata.get(
        "pace_status",
        "On pace",
    )

    if link["track_key"] == "google":
        return (
            f"{role} • Week {completed}/{target} • "
            f"Aim for {today} today • {pace_status}"
        )

    alignment = metadata.get(
        "alignment",
        "Aligned supplemental work.",
    )
    return (
        f"{role} • Week {completed}/{target} • "
        f"{alignment}"
    )


def skill_snapshot(conn):
    return {
        row["skill_key"]: {
            "display_name": row[
                "display_name"
            ],
            "status": row["status"],
            "evidence": row["evidence"],
        }
        for row in conn.execute(
            """SELECT *
               FROM skill_state
               ORDER BY skill_key"""
        ).fetchall()
    }


def _sql_item(title):
    for item in SQL_COMPANION:
        if item[0] == title:
            return item
    return None


def complete_track_task(
    conn,
    task_id,
    state,
):
    link = task_track(
        conn,
        task_id,
    )
    if link is None:
        return {
            "handled": False,
        }

    track_key = link["track_key"]
    label = conn.execute(
        """SELECT label
           FROM sprint_tasks
           WHERE id=?""",
        (task_id,),
    ).fetchone()["label"]

    conn.execute(
        """UPDATE sprint_tasks
           SET completed=1
           WHERE id=?""",
        (task_id,),
    )
    conn.execute(
        """UPDATE task_metadata
           SET status='Completed',
               deferred_until=NULL
           WHERE task_id=?""",
        (task_id,),
    )

    message = (
        f"{TRACK_CONFIG[track_key]['display_name']} "
        "task completed."
    )

    if track_key == "google":
        course = int(
            state["google_course"]
        )
        module = int(
            state["google_module"]
        )
        _record_event(
            conn,
            "google",
            f"course:{course}:module:{module}",
            label,
            metadata={
                "course": course,
                "module": module,
            },
        )
        conn.execute(
            """UPDATE program_state
               SET google_module=google_module+1
               WHERE id=1"""
        )
        message = (
            f"Google progress advanced to "
            f"Course {course}, "
            f"Module {module + 1}."
        )

    elif track_key == "datacamp":
        row = _state_row(
            conn,
            "datacamp",
        )
        position = (
            int(row["position"])
            if row else 0
        )
        _record_event(
            conn,
            "datacamp",
            f"item:{position}",
            label,
            metadata={
                "position": position,
            },
        )
        _upsert_state(
            conn,
            "datacamp",
            position=position + 1,
            subposition=0,
            weekly_target=int(
                row["weekly_target"]
            ) if row else 1,
            status="Active",
            metadata={},
        )
        message = (
            "DataCamp advanced to "
            "the next aligned lesson."
        )

    elif track_key == "sql":
        target_key = link[
            "target_key"
        ]
        title = target_key.split(
            "problem:",
            1,
        )[-1]
        item = _sql_item(title)

        if item:
            (
                _,
                difficulty,
                topic,
                concepts,
                _,
                _,
            ) = item
            conn.execute(
                """INSERT INTO sql_practice
                   (platform,title,difficulty,topic,
                    concepts,status,mastery,
                    completed_date,notes)
                   VALUES('DataLemur',?,?,?,?,?,?,?,?)
                   ON CONFLICT(platform,title)
                   DO UPDATE SET
                       difficulty=excluded.difficulty,
                       topic=excluded.topic,
                       concepts=excluded.concepts,
                       status='Completed',
                       completed_date=excluded.completed_date""",
                (
                    title,
                    difficulty,
                    topic,
                    concepts,
                    "Completed",
                    1,
                    date.today().isoformat(),
                    (
                        "Completed from the adaptive "
                        "SQL track."
                    ),
                ),
            )

        _record_event(
            conn,
            "sql",
            f"problem:{title}",
            title,
            metadata={
                "title": title,
            },
        )
        message = (
            f"SQL completed: {title}"
        )

    elif track_key == "portfolio":
        project_task_id = link[
            "linked_entity_id"
        ]
        if project_task_id is not None:
            conn.execute(
                """UPDATE project_tasks
                   SET completed=1
                   WHERE id=?""",
                (project_task_id,),
            )
            _record_event(
                conn,
                "portfolio",
                (
                    f"project:"
                    f"{state['current_project']}:"
                    f"task:{project_task_id}"
                ),
                label,
                metadata={
                    "project_id": int(
                        state[
                            "current_project"
                        ]
                    ),
                    "project_task_id": int(
                        project_task_id
                    ),
                },
            )
        message = (
            "Portfolio milestone completed: "
            f"{label}"
        )

    conn.execute(
        """DELETE FROM track_tasks
           WHERE track_key=?""",
        (track_key,),
    )
    conn.commit()

    return {
        "handled": True,
        "track_key": track_key,
        "message": message,
    }


def record_google_manual_change(
    conn,
    old_state,
    new_course,
    new_module,
):
    old_course = int(
        old_state["google_course"]
    )
    old_module = int(
        old_state["google_module"]
    )
    new_course = int(new_course)
    new_module = int(new_module)

    if (
        old_course == new_course
        and old_module == new_module
    ):
        return

    if (
        new_course == old_course
        and new_module > old_module
    ):
        for module in range(
            old_module,
            new_module,
        ):
            _record_event(
                conn,
                "google",
                (
                    f"course:{old_course}:"
                    f"module:{module}"
                ),
                (
                    f"Google Course "
                    f"{old_course}, "
                    f"Module {module}"
                ),
                event_type=(
                    "Progress Updated"
                ),
                metadata={
                    "from_course": old_course,
                    "from_module": module,
                    "to_course": new_course,
                    "to_module": new_module,
                },
            )
    elif new_course > old_course:
        _record_event(
            conn,
            "google",
            (
                f"course:{old_course}:"
                f"module:{old_module}"
            ),
            (
                f"Google Course {old_course}, "
                f"Module {old_module}"
            ),
            event_type="Progress Updated",
            metadata={
                "from_course": old_course,
                "from_module": old_module,
                "to_course": new_course,
                "to_module": new_module,
            },
        )
    else:
        # Rewinds correct the checkpoint but do not fabricate completions.
        conn.execute(
            """DELETE FROM track_tasks
               WHERE track_key='google'"""
        )

    conn.commit()

def record_sql_completion(
    conn,
    title,
):
    item = _sql_item(title)
    metadata = {
        "title": title,
    }
    if item:
        metadata.update(
            {
                "difficulty": item[1],
                "topic": item[2],
            }
        )
    _record_event(
        conn,
        "sql",
        f"problem:{title}",
        title,
        metadata=metadata,
    )
    conn.commit()


def record_portfolio_change(
    conn,
    *,
    project_id,
    project_task_id,
    label,
    completed,
):
    event_key = (
        f"project:{project_id}:"
        f"task:{project_task_id}"
    )
    if completed:
        _record_event(
            conn,
            "portfolio",
            event_key,
            label,
            metadata={
                "project_id": int(
                    project_id
                ),
                "project_task_id": int(
                    project_task_id
                ),
            },
        )
    else:
        conn.execute(
            """DELETE FROM track_events
               WHERE event_key=?""",
            (event_key,),
        )
    conn.commit()


def snapshot(conn, state):
    initialize(conn, state)
    result = {}

    for track_key in TRACK_ORDER:
        row = _state_row(
            conn,
            track_key,
        )
        metadata = json.loads(
            row["metadata"]
            or "{}"
        )
        active = _active_link(
            conn,
            track_key,
        )

        result[track_key] = {
            "track_key": track_key,
            "display_name": row[
                "display_name"
            ],
            "position": int(
                row["position"]
            ),
            "subposition": int(
                row["subposition"]
            ),
            "weekly_target": int(
                row["weekly_target"]
            ),
            "weekly_completed": int(
                metadata.get(
                    "weekly_completed",
                    _weekly_completed(
                        conn,
                        track_key,
                    ),
                )
            ),
            "status": row["status"],
            "metadata": metadata,
            "task_id": (
                int(active["task_id"])
                if active else None
            ),
            "task_label": (
                active["label"]
                if active else None
            ),
            "source_label": (
                active["source_label"]
                if active else None
            ),
        }

    return result


def next_sql_titles(
    conn,
    state=None,
    limit=5,
):
    completed = _completed_sql(conn)
    unlocked = (
        _derived_skills(conn, state)
        if state is not None
        else set(SKILL_DEFINITIONS)
    )

    titles = []
    for item in SQL_COMPANION:
        title = item[0]
        if title in completed:
            continue
        required = SQL_REQUIREMENTS.get(
            item[2],
            {"analytics_foundations"},
        )
        if not set(required).issubset(
            unlocked
        ):
            continue
        titles.append(title)
        if len(titles) >= max(
            1,
            int(limit),
        ):
            break

    return titles
