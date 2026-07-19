from career_app.services.analytics import readiness

def recommendations(conn, state):
    result = readiness(conn, state)
    sql_count = conn.execute(
        """SELECT COUNT(*)
           FROM sql_practice
           WHERE status='Completed'"""
    ).fetchone()[0]
    hours = conn.execute("SELECT COALESCE(SUM(hours),0) FROM study_sessions").fetchone()[0]
    project_rows = conn.execute(
        "SELECT completed FROM project_tasks WHERE project_id=?",
        (state["current_project"],),
    ).fetchall()
    project_pct = (
        sum(int(row["completed"]) for row in project_rows) / len(project_rows) * 100
        if project_rows else 0
    )

    messages = []
    if project_pct < 25:
        messages.append(
            "Finish the discovery and dataset milestones for the active portfolio project. "
            "This is currently the highest-impact employability gain."
        )
    if sql_count < 10:
        messages.append(
            "Continue easy SQL problems until aggregation and joins feel routine."
        )
    elif sql_count < 25:
        messages.append(
            "Shift SQL practice toward joins, CTEs, and window functions."
        )
    if hours < 10:
        messages.append(
            "Protect consistency over intensity. A 60–90 minute focused session is enough today."
        )
    weakest = min(
        (key for key in result if key != "Overall"),
        key=lambda key: result[key],
    )
    messages.append(f"Current weakest readiness area: {weakest}.")
    return messages[:4]
