from __future__ import annotations

from datetime import date, timedelta


def _session_dates(conn):
    rows = conn.execute(
        """SELECT DISTINCT session_date
           FROM study_sessions
           ORDER BY session_date"""
    ).fetchall()

    dates = set()
    for row in rows:
        try:
            dates.add(date.fromisoformat(row["session_date"]))
        except (TypeError, ValueError):
            continue
    return dates


def week_bounds(reference=None):
    reference = reference or date.today()
    start = reference - timedelta(days=reference.weekday())
    return start, start + timedelta(days=6)


def streak(conn):
    dates = _session_dates(conn)
    if not dates:
        return 0

    today = date.today()
    cursor = today if today in dates else today - timedelta(days=1)

    count = 0
    while cursor in dates:
        count += 1
        cursor -= timedelta(days=1)
    return count


def best_streak(conn):
    dates = sorted(_session_dates(conn))
    if not dates:
        return 0

    best = 1
    current = 1

    for previous, current_date in zip(dates, dates[1:]):
        if current_date == previous + timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1

    return best


def week_activity(conn, reference=None):
    start, _ = week_bounds(reference)
    dates = _session_dates(conn)
    return [
        start + timedelta(days=offset) in dates
        for offset in range(7)
    ]


def weekly_hours(conn, reference=None):
    start, end = week_bounds(reference)
    row = conn.execute(
        """SELECT COALESCE(SUM(hours), 0) AS total
           FROM study_sessions
           WHERE session_date BETWEEN ? AND ?""",
        (start.isoformat(), end.isoformat()),
    ).fetchone()
    return float(row["total"] or 0)


def weekly_session_count(conn, reference=None):
    start, end = week_bounds(reference)
    row = conn.execute(
        """SELECT COUNT(*) AS total
           FROM study_sessions
           WHERE session_date BETWEEN ? AND ?""",
        (start.isoformat(), end.isoformat()),
    ).fetchone()
    return int(row["total"] or 0)


def weekly_sql_count(conn, reference=None):
    start, end = week_bounds(reference)
    row = conn.execute(
        """SELECT COUNT(*) AS total
           FROM sql_practice
           WHERE completed_date BETWEEN ? AND ?""",
        (start.isoformat(), end.isoformat()),
    ).fetchone()
    return int(row["total"] or 0)


def weekly_focus_score(conn, reference=None):
    start, end = week_bounds(reference)
    row = conn.execute(
        """SELECT AVG(productivity_score) AS average_score
           FROM study_sessions
           WHERE session_date BETWEEN ? AND ?
             AND productivity_score IS NOT NULL""",
        (start.isoformat(), end.isoformat()),
    ).fetchone()

    value = row["average_score"]
    if value is None:
        return None
    return round(float(value), 1)



def weekly_daily_hours(conn, reference=None):
    start, end = week_bounds(reference)
    rows = conn.execute(
        """SELECT session_date, SUM(hours) AS hours
           FROM study_sessions
           WHERE session_date BETWEEN ? AND ?
           GROUP BY session_date""",
        (start.isoformat(), end.isoformat()),
    ).fetchall()

    totals = {
        row["session_date"]: float(row["hours"] or 0)
        for row in rows
    }

    return [
        (
            (start + timedelta(days=offset)).isoformat(),
            totals.get(
                (start + timedelta(days=offset)).isoformat(),
                0.0,
            ),
        )
        for offset in range(7)
    ]

def readiness(conn, state):
    sql_count = conn.execute(
        """SELECT COUNT(*)
           FROM sql_practice
           WHERE status='Completed'"""
    ).fetchone()[0]
    hours = conn.execute(
        "SELECT COALESCE(SUM(hours),0) FROM study_sessions"
    ).fetchone()[0]
    applications = conn.execute(
        "SELECT COUNT(*) FROM private_data.applications"
    ).fetchone()[0]
    evidence_count = conn.execute(
        "SELECT COUNT(*) FROM evidence"
    ).fetchone()[0]

    project_scores = []
    for project_id in range(1, state["total_projects"] + 1):
        rows = conn.execute(
            "SELECT completed FROM project_tasks WHERE project_id=?",
            (project_id,),
        ).fetchall()
        project_scores.append(
            sum(int(row["completed"]) for row in rows)
            / len(rows)
            * 100
            if rows else 0
        )

    technical = min(
        100,
        (sql_count / max(1, state["sql_target"])) * 45
        + (
            (state["google_course"] - 1)
            / max(1, state["google_total_courses"])
        ) * 35
        + min(20, hours / 50 * 20),
    )
    portfolio = (
        sum(project_scores) / len(project_scores)
        if project_scores else 0
    )
    interview = min(
        100,
        evidence_count * 8 + sql_count / 50 * 40,
    )
    networking = min(
        100,
        applications / 25 * 70 + evidence_count * 3,
    )
    applications_score = min(
        100,
        applications / 25 * 100,
    )
    overall = (
        technical * 0.30
        + portfolio * 0.30
        + interview * 0.15
        + networking * 0.10
        + applications_score * 0.15
    )
    return {
        "Technical Skills": round(technical),
        "Portfolio": round(portfolio),
        "Interview Practice": round(interview),
        "Networking": round(networking),
        "Applications": round(applications_score),
        "Overall": round(overall),
    }


def daily_hours(conn, limit=7):
    limit = max(1, int(limit))
    today = date.today()
    start = today - timedelta(days=limit - 1)

    rows = conn.execute(
        """SELECT session_date, SUM(hours) AS hours
           FROM study_sessions
           WHERE session_date BETWEEN ? AND ?
           GROUP BY session_date""",
        (start.isoformat(), today.isoformat()),
    ).fetchall()

    totals = {
        row["session_date"]: float(row["hours"] or 0)
        for row in rows
    }

    return [
        (
            (start + timedelta(days=offset)).isoformat(),
            totals.get(
                (start + timedelta(days=offset)).isoformat(),
                0.0,
            ),
        )
        for offset in range(limit)
    ]
