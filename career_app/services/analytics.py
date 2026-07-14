from datetime import date, timedelta

def streak(conn):
    rows = conn.execute(
        "SELECT DISTINCT session_date FROM study_sessions ORDER BY session_date DESC"
    ).fetchall()
    dates = {date.fromisoformat(row["session_date"]) for row in rows}
    if not dates:
        return 0
    today = date.today()
    cursor = today if today in dates else today - timedelta(days=1)
    count = 0
    while cursor in dates:
        count += 1
        cursor -= timedelta(days=1)
    return count

def readiness(conn, state):
    sql_count = conn.execute("SELECT COUNT(*) FROM sql_practice").fetchone()[0]
    hours = conn.execute("SELECT COALESCE(SUM(hours),0) FROM study_sessions").fetchone()[0]
    applications = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    evidence_count = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]

    project_scores = []
    for project_id in range(1, state["total_projects"] + 1):
        rows = conn.execute(
            "SELECT completed FROM project_tasks WHERE project_id=?", (project_id,)
        ).fetchall()
        project_scores.append(
            sum(int(row["completed"]) for row in rows) / len(rows) * 100
            if rows else 0
        )

    technical = min(
        100,
        (sql_count / max(1, state["sql_target"])) * 45
        + ((state["google_course"] - 1) / max(1, state["google_total_courses"])) * 35
        + min(20, hours / 50 * 20),
    )
    portfolio = sum(project_scores) / len(project_scores) if project_scores else 0
    interview = min(100, evidence_count * 8 + sql_count / 50 * 40)
    networking = min(100, applications / 25 * 70 + evidence_count * 3)
    applications_score = min(100, applications / 25 * 100)
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
    rows = conn.execute(
        """SELECT session_date,SUM(hours) hours
           FROM study_sessions
           GROUP BY session_date
           ORDER BY session_date DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return list(reversed([(row["session_date"], float(row["hours"])) for row in rows]))
