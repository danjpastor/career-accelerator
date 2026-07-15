"""Derived achievement reconciliation helpers."""

from __future__ import annotations


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
