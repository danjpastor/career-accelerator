from pathlib import Path

def publish(conn, root: Path, state, project_names, readiness):
    sql_count = conn.execute("SELECT COUNT(*) FROM sql_practice").fetchone()[0]
    hours = conn.execute("SELECT COALESCE(SUM(hours),0) FROM study_sessions").fetchone()[0]
    applications = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    summary = f"""# Career Accelerator Progress Snapshot

## Current State

- Week: {state['current_week']} / {state['total_weeks']}
- Google Certificate: Course {state['google_course']} / {state['google_total_courses']}
- SQL Problems: {sql_count} / {state['sql_target']}
- Study Hours: {hours:g}
- Active Project: {project_names[state['current_project']]}
- Applications: {applications}
- Overall Job Readiness: {readiness['Overall']}%

## Readiness

| Area | Score |
|---|---:|
"""
    for key, value in readiness.items():
        if key != "Overall":
            summary += f"| {key} | {value}% |\n"

    snapshot_path = root / "documentation" / "PROGRESS_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(summary, encoding="utf-8")
