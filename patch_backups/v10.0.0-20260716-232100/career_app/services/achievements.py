"""Derived achievement reconciliation helpers."""

from __future__ import annotations

import re


MANAGED_PREFIXES = (
    "task:",
    "project-task:",
    "sql-problem:",
    "study-session:",
    "application:",
    "milestone:",
)


def is_managed_key(key: str) -> bool:
    text = str(key or "")
    return any(
        text.startswith(prefix)
        for prefix in MANAGED_PREFIXES
    )


_ACTIVITY_PREFIXES = (
    "complete ",
    "completed ",
    "finish ",
    "finished ",
    "solve ",
    "solved ",
    "continue ",
    "work on ",
)

_CATEGORY_PREFIXES = {
    "sql": (
        "sql challenge ",
        "sql problem ",
        "sql practice ",
        "datalemur ",
        "sql companion ",
    ),
    "portfolio": (
        "portfolio milestone ",
        "portfolio project ",
        "project milestone ",
    ),
    "learning": (
        "learning milestone ",
    ),
    "review": (
        "weekly reflection ",
    ),
    "general": (
        "roadmap accomplishment ",
    ),
}


def normalize_activity_label(
    value,
    category=None,
):
    """Return a stable identity for one completed accomplishment."""
    text = str(value or "").strip().lower()
    text = text.replace("—", " ")
    text = text.replace("–", " ")
    text = re.sub(
        r"^\[[^\]]+\]\s*",
        "",
        text,
    )
    # Normalize separators before removing semantic prefixes. This makes
    # "SQL Challenge: Solve X" equivalent to "Solve X".
    text = re.sub(
        r"[:|/\\-]+",
        " ",
        text,
    )
    text = " ".join(
        text.split()
    )

    category_key = str(
        category or ""
    ).strip().lower()
    prefixes = list(
        _ACTIVITY_PREFIXES
    )
    prefixes.extend(
        _CATEGORY_PREFIXES.get(
            category_key,
            (),
        )
    )

    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[
                    len(prefix):
                ].strip()
                changed = True

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )
    return " ".join(
        text.split()
    )


def activity_identity(
    category,
    label,
):
    category_key = str(
        category or "General"
    ).strip().lower()
    return (
        category_key,
        normalize_activity_label(
            label,
            category_key,
        ),
    )


def completed_project_rows(conn):
    return conn.execute(
        """SELECT id,label
           FROM project_tasks
           WHERE completed=1
           ORDER BY id"""
    ).fetchall()


def completed_task_rows(conn):
    return conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               m.category,
               tt.track_key
           FROM sprint_tasks s
           LEFT JOIN task_metadata m
             ON m.task_id=s.id
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.completed=1
           ORDER BY
               s.week,
               s.sort_order,
               s.id"""
    ).fetchall()


def task_category(row):
    track_key = str(
        row["track_key"]
        or ""
    ).strip().lower()
    if track_key == "sql":
        return "SQL"
    if track_key == "portfolio":
        return "Portfolio"
    return str(
        row["category"]
        or "General"
    )


def canonical_completed_activities(
    conn,
):
    """Return one canonical achievement row per logical accomplishment."""
    sql_rows = list(
        completed_sql_rows(
            conn
        )
    )
    project_rows = list(
        completed_project_rows(
            conn
        )
    )
    task_rows = list(
        completed_task_rows(
            conn
        )
    )

    canonical_identities = set()
    deduplicated_sql = []
    for row in sql_rows:
        identity = activity_identity(
            "SQL",
            row["title"],
        )
        if identity in canonical_identities:
            continue
        canonical_identities.add(
            identity
        )
        deduplicated_sql.append(
            row
        )

    deduplicated_projects = []
    for row in project_rows:
        identity = activity_identity(
            "Portfolio",
            row["label"],
        )
        if identity in canonical_identities:
            continue
        canonical_identities.add(
            identity
        )
        deduplicated_projects.append(
            row
        )

    deduplicated_tasks = []
    task_identities = set()

    for row in task_rows:
        category = task_category(
            row
        )
        identity = activity_identity(
            category,
            row["label"],
        )

        # Canonical SQL and project records take precedence over a generic
        # roadmap-task record for the same work.
        if identity in canonical_identities:
            continue

        # Duplicate sprint rows with the same logical label also collapse to
        # one achievement.
        if identity in task_identities:
            continue

        task_identities.add(
            identity
        )
        canonical_identities.add(
            identity
        )
        deduplicated_tasks.append(
            row
        )

    return {
        "tasks": deduplicated_tasks,
        "sql": deduplicated_sql,
        "projects": deduplicated_projects,
        "task_logical_count": len(
            {
                activity_identity(
                    task_category(
                        row
                    ),
                    row["label"],
                )
                for row in task_rows
            }
        ),
    }


def duplicate_activity_groups(conn):
    """Return remaining duplicate managed achievements for diagnostics."""
    rows = conn.execute(
        """SELECT
               achievement_key,
               title,
               description
           FROM achievements
           ORDER BY id"""
    ).fetchall()

    groups = {}
    for row in rows:
        key = str(
            row["achievement_key"]
            or ""
        )
        if key.startswith(
            "sql-problem:"
        ):
            identity = activity_identity(
                "SQL",
                row["description"],
            )
        elif key.startswith(
            "project-task:"
        ):
            identity = activity_identity(
                "Portfolio",
                row["description"],
            )
        elif key.startswith(
            "task:"
        ):
            title = str(
                row["title"]
                or ""
            )
            category = (
                "SQL"
                if title.startswith(
                    "SQL Challenge:"
                )
                else "Portfolio"
                if title.startswith(
                    "Portfolio Milestone:"
                )
                else "Learning"
                if title.startswith(
                    "Learning Milestone:"
                )
                else "Review"
                if title.startswith(
                    "Weekly Reflection:"
                )
                else "General"
            )
            logical_label = (
                title.split(
                    ":",
                    1,
                )[1]
                if ":" in title
                else row["description"]
            )
            identity = activity_identity(
                category,
                logical_label,
            )
        else:
            continue

        groups.setdefault(
            identity,
            [],
        ).append(
            key
        )

    return {
        identity: keys
        for identity, keys in groups.items()
        if len(keys) > 1
    }



def completed_sql_rows(conn):
    return conn.execute(
        """SELECT id,title
           FROM sql_practice
           WHERE status='Completed'
           ORDER BY id"""
    ).fetchall()


def completed_sql_count(conn) -> int:
    row = conn.execute(
        """SELECT COUNT(*) AS total
           FROM sql_practice
           WHERE status='Completed'"""
    ).fetchone()
    return int(row["total"] or 0)


def reconcile(
    conn,
    valid_keys,
):
    """Delete managed achievements unsupported by current evidence."""
    valid = {
        str(key)
        for key in valid_keys
    }
    rows = conn.execute(
        """SELECT
               achievement_key,
               title
           FROM achievements"""
    ).fetchall()

    removed = []
    for row in rows:
        key = row["achievement_key"]
        if (
            is_managed_key(key)
            and key not in valid
        ):
            conn.execute(
                """DELETE FROM achievements
                   WHERE achievement_key=?""",
                (key,),
            )
            removed.append(
                {
                    "key": key,
                    "title": row["title"],
                }
            )

    return removed
