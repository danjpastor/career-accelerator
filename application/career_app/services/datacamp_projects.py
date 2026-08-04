from __future__ import annotations

from datetime import date, timedelta
import sqlite3
from typing import Any, Iterable

WEEKLY_TARGET_MINUTES = 18 * 60

# The task title intentionally omits a repeated "DataCamp —" prefix. The source
# line and dedicated icon identify the provider without making task titles noisy.
PROJECTS: tuple[dict[str, Any], ...] = (
    {
        "key": "w2_excel_customer_churn",
        "week": 2,
        "role": "primary",
        "title": "Case Study: Analyzing Customer Churn in Excel",
        "url": "https://www.datacamp.com/courses/case-study-analyzing-customer-churn-in-excel",
        "minutes": 60,
        "tool": "Excel",
        "prerequisite": "Complete this week's spreadsheet analysis coursework.",
    },
    {
        "key": "w2_excel_net_revenue",
        "week": 2,
        "role": "supplemental",
        "title": "Case Study: Net Revenue Management in Excel",
        "url": "https://www.datacamp.com/courses/case-study-net-revenue-management-in-excel",
        "minutes": 240,
        "tool": "Excel",
        "prerequisite": "Complete the primary Excel case study first.",
    },
    {
        "key": "w3_sql_student_mental_health",
        "week": 3,
        "role": "primary",
        "title": "Analyzing Students' Mental Health",
        "url": "https://www.datacamp.com/projects/1593",
        "minutes": 60,
        "tool": "SQL",
        "prerequisite": "Complete Introduction to SQL and Intermediate SQL.",
    },
    {
        "key": "w3_sql_international_debt",
        "week": 3,
        "role": "supplemental",
        "title": "Analyze International Debt Statistics",
        "url": "https://www.datacamp.com/projects/1906",
        "minutes": 30,
        "tool": "SQL",
        "prerequisite": "Complete the primary Week 3 SQL project first.",
    },
    {
        "key": "w4_sql_golden_era_games",
        "week": 4,
        "role": "primary",
        "title": "When Was the Golden Era of Video Games?",
        "url": "https://www.datacamp.com/projects/2670",
        "minutes": 30,
        "tool": "SQL",
        "prerequisite": "Complete Joining Data in SQL.",
    },
    {
        "key": "w4_sql_carbon_emissions",
        "week": 4,
        "role": "supplemental",
        "title": "Analyzing Industry Carbon Emissions",
        "url": "https://www.datacamp.com/projects/1590",
        "minutes": 30,
        "tool": "SQL",
        "prerequisite": "Complete the primary Week 4 SQL project first.",
    },
    {
        "key": "w5_sql_student_performance",
        "week": 5,
        "role": "primary",
        "title": "Factors that Fuel Student Performance",
        "url": "https://www.datacamp.com/projects/2623",
        "minutes": 30,
        "tool": "SQL",
        "prerequisite": "Complete Data Manipulation in SQL.",
    },
    {
        "key": "w5_sql_baby_names",
        "week": 5,
        "role": "supplemental",
        "title": "Exploring Trends in American Baby Names",
        "url": "https://www.datacamp.com/projects/2588",
        "minutes": 45,
        "tool": "SQL",
        "prerequisite": "Complete the primary Week 5 SQL project first.",
    },
    {
        "key": "w6_sql_goodthought",
        "week": 6,
        "role": "primary",
        "title": "Impact Analysis of GoodThought NGO Initiatives",
        "url": "https://www.datacamp.com/projects/2190",
        "minutes": 60,
        "tool": "SQL",
        "prerequisite": "Complete summary statistics and SQL window functions.",
    },
    {
        "key": "w6_sql_manufacturing",
        "week": 6,
        "role": "supplemental",
        "title": "Evaluate a Manufacturing Process",
        "url": "https://www.datacamp.com/projects/2044",
        "minutes": 60,
        "tool": "SQL",
        "prerequisite": "Complete the primary Week 6 SQL project first.",
    },
    {
        "key": "w7_tableau_job_market",
        "week": 7,
        "role": "primary",
        "title": "Case Study: Analyzing Job Market Data in Tableau",
        "url": "https://www.datacamp.com/courses/case-study-analyzing-job-market-data-in-tableau",
        "minutes": 180,
        "tool": "Tableau",
        "prerequisite": "Complete the Google Certificate Tableau coursework assigned this week.",
    },
    {
        "key": "w7_powerbi_job_market",
        "week": 7,
        "role": "supplemental",
        "title": "Case Study: Analyzing Job Market Data in Power BI",
        "url": "https://www.datacamp.com/courses/case-study-analyzing-job-market-data-in-power-bi",
        "minutes": 240,
        "tool": "Power BI",
        "prerequisite": "Complete the Tableau capstone and this week's Power BI foundations.",
    },
    {
        "key": "w8_python_nyc_schools",
        "week": 8,
        "role": "primary",
        "title": "Exploring NYC Public School Test Result Scores",
        "url": "https://www.datacamp.com/projects/1596",
        "minutes": 30,
        "tool": "Python",
        "prerequisite": "Complete Data Manipulation with pandas.",
    },
    {
        "key": "w8_python_market_analysis",
        "week": 8,
        "role": "supplemental",
        "title": "Data-Driven Product Management: Conducting a Market Analysis",
        "url": "https://www.datacamp.com/projects/1684",
        "minutes": 60,
        "tool": "Python",
        "prerequisite": "Complete the primary Week 8 Python project first.",
    },
    {
        "key": "w9_python_netflix",
        "week": 9,
        "role": "supplemental",
        "title": "Investigating Netflix Movies",
        "url": "https://www.datacamp.com/projects/1674",
        "minutes": 60,
        "tool": "Python",
        "prerequisite": "Complete the current portfolio milestone and Intermediate Python before adding extra practice.",
    },
    {
        "key": "w10_powerbi_hr",
        "week": 10,
        "role": "supplemental",
        "title": "Case Study: HR Analytics in Power BI",
        "url": "https://www.datacamp.com/courses/case-study-hr-analytics-in-power-bi",
        "minutes": 180,
        "tool": "Power BI",
        "prerequisite": "Complete the current portfolio milestone before adding extra practice.",
    },
    {
        "key": "w11_python_crime",
        "week": 11,
        "role": "supplemental",
        "title": "Analyzing Crime in Los Angeles",
        "url": "https://www.datacamp.com/projects/1876",
        "minutes": 45,
        "tool": "Python",
        "prerequisite": "Complete the current portfolio milestone before adding extra practice.",
    },
)

PROJECT_BY_KEY = {project["key"]: project for project in PROJECTS}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS datacamp_project_tasks (
            project_key TEXT PRIMARY KEY,
            task_id INTEGER UNIQUE NOT NULL,
            project_week INTEGER NOT NULL,
            role TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            tool TEXT NOT NULL,
            estimated_minutes INTEGER NOT NULL,
            capacity_selected INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except Exception:
        return default


def _insert_dynamic(
    conn: sqlite3.Connection,
    table: str,
    values: dict[str, Any],
) -> int:
    columns = _columns(conn, table)
    usable = {key: value for key, value in values.items() if key in columns}
    if not usable:
        raise RuntimeError(f"No compatible columns were found in {table}.")
    names = list(usable)
    placeholders = ",".join("?" for _ in names)
    cursor = conn.execute(
        f"INSERT INTO {table} ({','.join(names)}) VALUES ({placeholders})",
        tuple(usable[name] for name in names),
    )
    return int(cursor.lastrowid)


def _update_dynamic(
    conn: sqlite3.Connection,
    table: str,
    values: dict[str, Any],
    where: str,
    where_values: Iterable[Any],
) -> None:
    columns = _columns(conn, table)
    usable = {key: value for key, value in values.items() if key in columns}
    if not usable:
        return
    names = list(usable)
    assignments = ",".join(f"{name}=?" for name in names)
    conn.execute(
        f"UPDATE {table} SET {assignments} WHERE {where}",
        tuple(usable[name] for name in names) + tuple(where_values),
    )


def _existing_task_for_project(conn: sqlite3.Connection, project: dict[str, Any]) -> int | None:
    row = conn.execute(
        "SELECT task_id FROM datacamp_project_tasks WHERE project_key=?",
        (project["key"],),
    ).fetchone()
    if row is not None:
        task_id = int(_row_value(row, "task_id", row[0]))
        exists = conn.execute(
            "SELECT 1 FROM sprint_tasks WHERE id=?",
            (task_id,),
        ).fetchone()
        if exists is not None:
            return task_id

    # Compatibility recovery for a prior partial install.
    if _table_exists(conn, "sprint_tasks"):
        columns = _columns(conn, "sprint_tasks")
        if {"id", "week", "label"}.issubset(columns):
            row = conn.execute(
                "SELECT id FROM sprint_tasks WHERE week=? AND label=? ORDER BY id LIMIT 1",
                (int(project["week"]), str(project["title"])),
            ).fetchone()
            if row is not None:
                return int(_row_value(row, "id", row[0]))
    return None


def _next_sort_order(conn: sqlite3.Connection, week: int, role: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM sprint_tasks WHERE week=?",
        (int(week),),
    ).fetchone()
    base = int(row[0] or 0)
    return max(base + 1, 700 if role == "primary" else 750)


def _ensure_task(conn: sqlite3.Connection, project: dict[str, Any]) -> int:
    task_id = _existing_task_for_project(conn, project)
    if task_id is None:
        task_id = _insert_dynamic(
            conn,
            "sprint_tasks",
            {
                "week": int(project["week"]),
                "sort_order": _next_sort_order(conn, int(project["week"]), str(project["role"])),
                "label": str(project["title"]),
                "completed": 0,
            },
        )

    _update_dynamic(
        conn,
        "sprint_tasks",
        {
            "week": int(project["week"]),
            "label": str(project["title"]),
        },
        "id=?",
        (task_id,),
    )

    metadata_exists = conn.execute(
        "SELECT 1 FROM task_metadata WHERE task_id=?",
        (task_id,),
    ).fetchone()
    metadata_values = {
        "task_id": task_id,
        "status": "Not Started",
        "priority": 5 if project["role"] == "primary" else 7,
        "estimated_minutes": int(project["minutes"]),
        "energy": "Normal",
        "destination": 0,
        "category": "Learning",
        "prerequisite_state": "Blocked",
        "prerequisite_reason": str(project["prerequisite"]),
        "icon_key": "datacamp_project",
        "task_icon": "datacamp_project",
        "source": f"DataCamp Project • {project['tool']}",
    }
    if metadata_exists is None:
        _insert_dynamic(conn, "task_metadata", metadata_values)
    else:
        # Preserve completion and in-progress state; refresh only stable metadata.
        _update_dynamic(
            conn,
            "task_metadata",
            {
                "priority": metadata_values["priority"],
                "estimated_minutes": metadata_values["estimated_minutes"],
                "energy": metadata_values["energy"],
                "destination": metadata_values["destination"],
                "category": metadata_values["category"],
                "icon_key": metadata_values["icon_key"],
                "task_icon": metadata_values["task_icon"],
                "source": metadata_values["source"],
            },
            "task_id=?",
            (task_id,),
        )

    conn.execute(
        """
        INSERT INTO datacamp_project_tasks
            (project_key,task_id,project_week,role,title,url,tool,estimated_minutes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(project_key) DO UPDATE SET
            task_id=excluded.task_id,
            project_week=excluded.project_week,
            role=excluded.role,
            title=excluded.title,
            url=excluded.url,
            tool=excluded.tool,
            estimated_minutes=excluded.estimated_minutes,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            project["key"],
            task_id,
            int(project["week"]),
            project["role"],
            project["title"],
            project["url"],
            project["tool"],
            int(project["minutes"]),
        ),
    )
    return task_id


def _completed(conn: sqlite3.Connection, task_id: int) -> bool:
    row = conn.execute(
        "SELECT completed FROM sprint_tasks WHERE id=?",
        (int(task_id),),
    ).fetchone()
    return bool(row and int(row[0] or 0))


def _primary_for_week(week: int) -> dict[str, Any] | None:
    return next(
        (
            project
            for project in PROJECTS
            if int(project["week"]) == int(week) and project["role"] == "primary"
        ),
        None,
    )


def _task_id_for_key(conn: sqlite3.Connection, key: str) -> int | None:
    row = conn.execute(
        "SELECT task_id FROM datacamp_project_tasks WHERE project_key=?",
        (str(key),),
    ).fetchone()
    return int(row[0]) if row is not None else None


def _coursework_ready(conn: sqlite3.Connection, week: int) -> tuple[bool, str]:
    """Use current task metadata as the prerequisite source of truth.

    Projects unlock after the week's required Learning/SQL coursework is done.
    Review, portfolio, and the project task itself do not block the capstone.
    """
    project_ids = {
        int(row[0])
        for row in conn.execute(
            "SELECT task_id FROM datacamp_project_tasks WHERE project_week=?",
            (int(week),),
        ).fetchall()
    }
    placeholders = ",".join("?" for _ in project_ids)
    exclusion = f"AND s.id NOT IN ({placeholders})" if project_ids else ""
    parameters: list[Any] = [int(week)] + sorted(project_ids)
    rows = conn.execute(
        f"""
        SELECT s.label,s.completed,m.status,m.category,m.priority
        FROM sprint_tasks s
        JOIN task_metadata m ON m.task_id=s.id
        WHERE s.week=?
          {exclusion}
          AND COALESCE(m.category,'General') IN ('Learning','SQL','Spreadsheet','Power BI','Python','pandas','Tableau')
          AND COALESCE(m.priority,3) <= 4
          AND s.sort_order >= 0
        """,
        tuple(parameters),
    ).fetchall()
    incomplete = [
        str(_row_value(row, "label", row[0]))
        for row in rows
        if not bool(_row_value(row, "completed", row[1]))
        and str(_row_value(row, "status", row[2]) or "") != "Completed"
    ]
    if not incomplete:
        return True, "Ready after this week's coursework."
    first = incomplete[0]
    extra = len(incomplete) - 1
    reason = f"Complete {first} first."
    if extra > 0:
        reason = f"Complete {first} and {extra} more required task{'s' if extra != 1 else ''} first."
    return False, reason


def planned_non_project_minutes(conn: sqlite3.Connection, week: int) -> int:
    ids = [
        int(row[0])
        for row in conn.execute(
            "SELECT task_id FROM datacamp_project_tasks WHERE project_week=?",
            (int(week),),
        ).fetchall()
    ]
    placeholders = ",".join("?" for _ in ids)
    exclusion = f"AND s.id NOT IN ({placeholders})" if ids else ""
    parameters: list[Any] = [int(week)] + ids
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(COALESCE(m.estimated_minutes,0)),0)
        FROM sprint_tasks s
        JOIN task_metadata m ON m.task_id=s.id
        WHERE s.week=?
          {exclusion}
          AND s.sort_order >= 0
          AND COALESCE(m.status,'Not Started') <> 'Archived'
        """,
        tuple(parameters),
    ).fetchone()
    return int(row[0] or 0)


def _capacity_selected_keys(conn: sqlite3.Connection, week: int) -> set[str]:
    week_projects = [project for project in PROJECTS if int(project["week"]) == int(week)]
    primary = next((project for project in week_projects if project["role"] == "primary"), None)
    selected: set[str] = set()
    total = planned_non_project_minutes(conn, week)
    if primary is not None:
        total += int(primary["minutes"])
    for project in week_projects:
        if project["role"] != "supplemental":
            continue
        if total >= WEEKLY_TARGET_MINUTES:
            break
        selected.add(str(project["key"]))
        total += int(project["minutes"])
    return selected


def _portfolio_milestones_ready(conn: sqlite3.Connection, week: int) -> tuple[bool, str]:
    rows = conn.execute(
        """
        SELECT s.label,s.completed,m.status
        FROM sprint_tasks s
        JOIN task_metadata m ON m.task_id=s.id
        WHERE s.week=?
          AND COALESCE(m.category,'General')='Portfolio'
          AND COALESCE(m.priority,3) <= 4
          AND s.sort_order >= 0
        ORDER BY s.sort_order
        """,
        (int(week),),
    ).fetchall()
    incomplete = [
        str(_row_value(row, "label", row[0]))
        for row in rows
        if not bool(_row_value(row, "completed", row[1]))
        and str(_row_value(row, "status", row[2]) or "") != "Completed"
    ]
    if not incomplete:
        return True, "Ready after this week's portfolio milestone."
    return False, f"Complete {incomplete[0]} before adding extra platform practice."


def _set_readiness(
    conn: sqlite3.Connection,
    task_id: int,
    *,
    ready: bool,
    reason: str,
) -> None:
    row = conn.execute(
        "SELECT completed FROM sprint_tasks WHERE id=?",
        (int(task_id),),
    ).fetchone()
    if row is not None and bool(int(row[0] or 0)):
        _update_dynamic(
            conn,
            "task_metadata",
            {
                "status": "Completed",
                "prerequisite_state": "Ready",
                "prerequisite_reason": "Completed.",
            },
            "task_id=?",
            (task_id,),
        )
        return

    metadata = conn.execute(
        "SELECT status FROM task_metadata WHERE task_id=?",
        (int(task_id),),
    ).fetchone()
    current_status = str(metadata[0] or "Not Started") if metadata else "Not Started"
    status = current_status if current_status in {"In Progress", "Deferred"} else "Not Started"
    _update_dynamic(
        conn,
        "task_metadata",
        {
            "status": status,
            "prerequisite_state": "Ready" if ready else "Blocked",
            "prerequisite_reason": reason,
        },
        "task_id=?",
        (task_id,),
    )


def sync_tasks(conn: sqlite3.Connection, state: Any | None = None) -> int:
    if not (_table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata")):
        return 0
    ensure_schema(conn)
    created_or_updated = 0
    task_ids: dict[str, int] = {}
    for project in PROJECTS:
        task_ids[project["key"]] = _ensure_task(conn, project)
        created_or_updated += 1

    for week in sorted({int(project["week"]) for project in PROJECTS}):
        coursework_ready, coursework_reason = _coursework_ready(conn, week)
        selected = _capacity_selected_keys(conn, week)
        conn.execute(
            "UPDATE datacamp_project_tasks SET capacity_selected=0 WHERE project_week=?",
            (week,),
        )
        for project in [item for item in PROJECTS if int(item["week"]) == week]:
            task_id = task_ids[project["key"]]
            if project["role"] == "primary":
                _set_readiness(
                    conn,
                    task_id,
                    ready=coursework_ready,
                    reason=(
                        "Ready — this week's prerequisite coursework is complete."
                        if coursework_ready
                        else coursework_reason
                    ),
                )
                continue

            primary = _primary_for_week(week)
            primary_complete = True
            no_primary_reason = ""
            if primary is not None:
                primary_id = task_ids.get(primary["key"])
                primary_complete = bool(primary_id and _completed(conn, primary_id))
            else:
                primary_complete, no_primary_reason = _portfolio_milestones_ready(conn, week)

            capacity_selected = project["key"] in selected
            conn.execute(
                "UPDATE datacamp_project_tasks SET capacity_selected=? WHERE project_key=?",
                (1 if capacity_selected else 0, project["key"]),
            )
            if not primary_complete:
                reason = (
                    f"Complete {primary['title']} first."
                    if primary is not None
                    else (no_primary_reason or str(project["prerequisite"]))
                )
                _set_readiness(conn, task_id, ready=False, reason=reason)
            elif capacity_selected:
                _set_readiness(
                    conn,
                    task_id,
                    ready=True,
                    reason="Scheduled to bring this week's planned workload closer to 18 hours.",
                )
            else:
                _set_readiness(
                    conn,
                    task_id,
                    ready=False,
                    reason=(
                        "Reserve practice — this week's planned work already reaches 18 hours. "
                        "It will be recommended on the Home screen after 18 logged hours."
                    ),
                )

    conn.commit()
    return created_or_updated


def project_for_task(conn: sqlite3.Connection, task_id: int | None) -> dict[str, Any] | None:
    if task_id is None or not _table_exists(conn, "datacamp_project_tasks"):
        return None
    row = conn.execute(
        """
        SELECT project_key,task_id,project_week,role,title,url,tool,
               estimated_minutes,capacity_selected
        FROM datacamp_project_tasks
        WHERE task_id=?
        """,
        (int(task_id),),
    ).fetchone()
    if row is None:
        return None
    keys = (
        "project_key",
        "task_id",
        "project_week",
        "role",
        "title",
        "url",
        "tool",
        "estimated_minutes",
        "capacity_selected",
    )
    if hasattr(row, "keys"):
        return {key: row[key] for key in keys}
    return dict(zip(keys, row))


def source_for_task(conn: sqlite3.Connection, task_id: int | None) -> str | None:
    project = project_for_task(conn, task_id)
    if project is None:
        return None
    return f"🧩 DataCamp Project • {project['tool']}"


def current_week_hours(conn: sqlite3.Connection, today: date | None = None) -> float:
    if not _table_exists(conn, "study_sessions"):
        return 0.0
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    columns = _columns(conn, "study_sessions")
    date_column = "session_date" if "session_date" in columns else ("date" if "date" in columns else None)
    hours_column = "hours" if "hours" in columns else None
    if date_column is None or hours_column is None:
        return 0.0
    row = conn.execute(
        f"SELECT COALESCE(SUM({hours_column}),0) FROM study_sessions WHERE {date_column} BETWEEN ? AND ?",
        (monday.isoformat(), sunday.isoformat()),
    ).fetchone()
    return float(row[0] or 0.0)


def optional_practice_recommendation(
    conn: sqlite3.Connection,
    current_week: int,
    *,
    today: date | None = None,
) -> dict[str, Any] | None:
    if current_week_hours(conn, today=today) < 18.0:
        return None
    if not _table_exists(conn, "datacamp_project_tasks"):
        return None

    primary = _primary_for_week(int(current_week))
    if primary is not None:
        primary_id = _task_id_for_key(conn, str(primary["key"]))
        if primary_id is not None and not _completed(conn, primary_id):
            return None

    rows = conn.execute(
        """
        SELECT d.project_key,d.task_id,d.project_week,d.role,d.title,d.url,d.tool,
               d.estimated_minutes,d.capacity_selected,s.completed
        FROM datacamp_project_tasks d
        JOIN sprint_tasks s ON s.id=d.task_id
        WHERE d.project_week=?
          AND d.role='supplemental'
          AND COALESCE(s.completed,0)=0
        ORDER BY d.task_id
        """,
        (int(current_week),),
    ).fetchall()
    if not rows:
        return None
    row = rows[0]
    keys = (
        "project_key",
        "task_id",
        "project_week",
        "role",
        "title",
        "url",
        "tool",
        "estimated_minutes",
        "capacity_selected",
        "completed",
    )
    result = {key: row[key] for key in keys} if hasattr(row, "keys") else dict(zip(keys, row))
    result["weekly_hours"] = current_week_hours(conn, today=today)
    return result


def catalog_for_week(week: int) -> list[dict[str, Any]]:
    return [dict(project) for project in PROJECTS if int(project["week"]) == int(week)]

# BEGIN DATACAMP EXACT PROJECT PREREQUISITES v10.40.2
# Projects use exact DataCamp chapter prerequisites and weekend scheduling.
# A week number alone can never unlock a project.
_WEEKEND_PROJECT_POLICY = {
    "w2_excel_customer_churn": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w02_intermediate_sheets_02", "w02_intermediate_sheets_03",
            "w02_intermediate_sheets_04", "w02_pivot_sheets_01",
            "w02_pivot_sheets_02", "w02_pivot_sheets_03",
            "w02_pivot_sheets_04",
        ),
    },
    "w2_excel_net_revenue": {"scheduled_weekday": 6, "required_chapters": ()},
    "w3_sql_student_mental_health": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w03_intro_sql_01", "w03_intro_sql_02",
            "w03_intermediate_sql_01", "w03_intermediate_sql_02",
            "w03_intermediate_sql_03", "w03_intermediate_sql_04",
        ),
    },
    "w3_sql_international_debt": {"scheduled_weekday": 6, "required_chapters": ()},
    "w4_sql_golden_era_games": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w03_joining_sql_01", "w04_joining_sql_02",
        ),
    },
    "w4_sql_carbon_emissions": {"scheduled_weekday": 6, "required_chapters": ()},
    "w5_sql_student_performance": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w04_manipulation_sql_01", "w04_manipulation_sql_02",
            "w04_manipulation_sql_03", "w04_manipulation_sql_04",
        ),
    },
    "w5_sql_baby_names": {"scheduled_weekday": 6, "required_chapters": ()},
    "w6_sql_goodthought": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w05_window_sql_01", "w05_window_sql_02",
            "w05_window_sql_03", "w05_window_sql_04",
        ),
    },
    "w6_sql_manufacturing": {"scheduled_weekday": 6, "required_chapters": ()},
    "w7_tableau_job_market": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w07_intro_powerbi_01", "w07_intro_powerbi_02",
            "w07_prep_powerbi_01", "w07_intro_powerbi_03",
            "w07_intro_powerbi_04", "w07_prep_powerbi_02",
            "w07_prep_powerbi_03", "w07_prep_powerbi_04",
            "w07_model_powerbi_01", "w07_model_powerbi_02",
            "w07_model_powerbi_03", "w07_dax_powerbi_01",
            "w07_model_powerbi_04", "w07_dax_powerbi_02",
            "w07_visual_powerbi_01", "w07_dax_powerbi_03",
            "w07_visual_powerbi_02", "w07_visual_powerbi_03",
            "w07_churn_powerbi_01", "w07_visual_powerbi_04",
            "w07_churn_powerbi_02", "w07_churn_powerbi_03",
        ),
    },
    "w7_powerbi_job_market": {"scheduled_weekday": 6, "required_chapters": ()},
    "w8_python_nyc_schools": {
        "scheduled_weekday": 5,
        "required_chapters": (
            "w08_pandas_01", "w08_pandas_02",
            "w08_pandas_03", "w08_pandas_04",
        ),
    },
    "w8_python_market_analysis": {"scheduled_weekday": 6, "required_chapters": ()},
    "w9_python_netflix": {"scheduled_weekday": 5, "required_chapters": ()},
    "w10_powerbi_hr": {"scheduled_weekday": 5, "required_chapters": ()},
    "w11_python_crime": {"scheduled_weekday": 5, "required_chapters": ()},
}

for _weekend_project in PROJECTS:
    _weekend_project.update(
        _WEEKEND_PROJECT_POLICY.get(
            str(_weekend_project.get("key") or ""),
            {"scheduled_weekday": 5, "required_chapters": ()},
        )
    )
PROJECT_BY_KEY = {project["key"]: project for project in PROJECTS}

_weekend_legacy_sync_tasks = sync_tasks
_weekend_legacy_project_for_task = project_for_task
_weekend_legacy_optional_recommendation = optional_practice_recommendation


def _weekend_row_value(row, key, index=0, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        try:
            return row[index]
        except Exception:
            return default


def _weekend_program_start(conn):
    row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
    raw = _weekend_row_value(row, "start_date", 0, None)
    try:
        return date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return date.today()


def _weekend_scheduled_date(conn, project):
    start = _weekend_program_start(conn)
    monday = start - timedelta(days=start.weekday())
    return monday + timedelta(
        days=(int(project["week"]) - 1) * 7 + int(project.get("scheduled_weekday", 5))
    )


def _weekend_chapter_label(key):
    try:
        from career_app.data.datacamp_curriculum import chapter_for_key
        chapter = chapter_for_key(key)
    except Exception:
        chapter = None
    if chapter is None:
        return str(key)
    return f"{chapter.course_name} — Chapter {chapter.chapter_number}: {chapter.chapter_name}"


def _weekend_chapter_complete(conn, key):
    if _table_exists(conn, "datacamp_chapter_progress"):
        row = conn.execute(
            "SELECT status,task_id FROM datacamp_chapter_progress WHERE chapter_key=?",
            (str(key),),
        ).fetchone()
        if row is not None:
            status = str(_weekend_row_value(row, "status", 0, "") or "")
            if status.casefold() == "completed":
                return True
            task_id = _weekend_row_value(row, "task_id", 1, None)
            if task_id is not None:
                task = conn.execute(
                    "SELECT completed FROM sprint_tasks WHERE id=?",
                    (int(task_id),),
                ).fetchone()
                if task is not None and bool(int(_weekend_row_value(task, "completed", 0, 0) or 0)):
                    return True
    if _table_exists(conn, "task_metadata"):
        row = conn.execute(
            """SELECT s.completed,m.status
               FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
               WHERE m.managed_key=? LIMIT 1""",
            (f"datacamp:{key}",),
        ).fetchone()
        if row is not None:
            return bool(int(_weekend_row_value(row, "completed", 0, 0) or 0)) or (
                str(_weekend_row_value(row, "status", 1, "") or "").casefold() == "completed"
            )
    return False


def _weekend_required_chapters_ready(conn, project):
    required = tuple(project.get("required_chapters") or ())
    missing = [key for key in required if not _weekend_chapter_complete(conn, key)]
    if not missing:
        return True, "Required DataCamp chapters are complete."
    first = _weekend_chapter_label(missing[0])
    remaining = len(missing) - 1
    if remaining:
        return False, f"Complete {first} and {remaining} more required chapter{'s' if remaining != 1 else ''} first."
    return False, f"Complete {first} first."


def _weekend_project_from_identity(conn, task_id=None, project_key=None):
    if project_key:
        return PROJECT_BY_KEY.get(str(project_key))
    if task_id:
        stored = _weekend_legacy_project_for_task(conn, int(task_id))
        if stored:
            return PROJECT_BY_KEY.get(str(stored.get("project_key") or ""))
    return None


def _weekend_google_coursework_ready(conn, week):
    if not (
        _table_exists(conn, "track_tasks")
        and _table_exists(conn, "task_metadata")
        and _table_exists(conn, "sprint_tasks")
    ):
        return True, "Required Google Certificate work is complete."
    rows = conn.execute(
        """SELECT s.label,s.completed,m.status
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           JOIN track_tasks tt ON tt.task_id=s.id
           WHERE s.week=? AND LOWER(COALESCE(tt.track_key,''))='google'
             AND s.sort_order >= 0""",
        (int(week),),
    ).fetchall()
    incomplete = [
        str(_weekend_row_value(row, "label", 0, "Google Certificate module"))
        for row in rows
        if not bool(int(_weekend_row_value(row, "completed", 1, 0) or 0))
        and str(_weekend_row_value(row, "status", 2, "") or "").casefold() != "completed"
    ]
    if not incomplete:
        return True, "Required Google Certificate work is complete."
    return False, f"Complete {incomplete[0]} before starting the weekend project."


def project_readiness(conn, task_id=None, project_key=None, today=None):
    today = today or date.today()
    project = _weekend_project_from_identity(
        conn, task_id=task_id, project_key=project_key
    )
    if project is None:
        return False, "This DataCamp project is not configured."

    resolved_task_id = _task_id_for_key(conn, str(project["key"]))
    if resolved_task_id is not None and _completed(conn, resolved_task_id):
        return False, "Already completed."

    prerequisites_ready, prerequisite_reason = _weekend_required_chapters_ready(conn, project)
    if not prerequisites_ready:
        return False, prerequisite_reason

    if str(project.get("role") or "") == "primary":
        google_ready, google_reason = _weekend_google_coursework_ready(
            conn, int(project["week"])
        )
        if not google_ready:
            return False, google_reason

    if str(project.get("role") or "") == "supplemental":
        primary = _primary_for_week(int(project["week"]))
        if primary is not None:
            primary_id = _task_id_for_key(conn, str(primary["key"]))
            if primary_id is None or not _completed(conn, primary_id):
                return False, f"Complete {primary['title']} first."
        else:
            portfolio_ready, portfolio_reason = _portfolio_milestones_ready(
                conn, int(project["week"])
            )
            if not portfolio_ready:
                return False, portfolio_reason

        row = conn.execute(
            "SELECT capacity_selected FROM datacamp_project_tasks WHERE project_key=?",
            (str(project["key"]),),
        ).fetchone()
        selected = bool(int(_weekend_row_value(row, "capacity_selected", 0, 0) or 0))
        if not selected:
            return False, (
                "Optional practice — this project is not needed to reach the 18-hour plan. "
                "It is recommended on Home after 18 logged hours."
            )

    scheduled = _weekend_scheduled_date(conn, project)
    if today < scheduled:
        return False, f"Scheduled for {scheduled.strftime('%A, %B %d')}."
    if today.weekday() <= 4:
        return False, "Weekend project — available Saturday or Sunday."
    if today.weekday() < int(project.get("scheduled_weekday", 5)):
        day_name = "Saturday" if int(project.get("scheduled_weekday", 5)) == 5 else "Sunday"
        return False, f"Scheduled for {day_name}."
    return True, "Ready for this weekend's project session."


def _weekend_ensure_project_columns(conn):
    ensure_schema(conn)
    columns = _columns(conn, "datacamp_project_tasks")
    additions = {
        "scheduled_weekday": "INTEGER NOT NULL DEFAULT 5",
        "scheduled_date": "TEXT",
        "required_chapters": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in additions.items():
        if name not in columns:
            conn.execute(
                f"ALTER TABLE datacamp_project_tasks ADD COLUMN {name} {definition}"
            )


def _weekend_update_project_task(conn, project):
    task_id = _task_id_for_key(conn, str(project["key"]))
    if task_id is None:
        return
    scheduled = _weekend_scheduled_date(conn, project)
    ready, reason = project_readiness(
        conn, task_id=task_id, today=date.today()
    )
    _set_readiness(conn, task_id, ready=ready, reason=reason)
    _update_dynamic(
        conn,
        "task_metadata",
        {
            "managed_key": f"datacamp_project:{project['key']}",
            "deferred_until": scheduled.isoformat(),
            "category": "Learning",
            "icon_key": "datacamp_project",
            "task_icon": "datacamp_project",
            "source": f"DataCamp Project • {project['tool']}",
            "description": (
                f"Weekend {project['tool']} project that applies the completed "
                "course chapters in a realistic analysis."
            ),
            "definition_of_done": "Complete the project on DataCamp and mark this task complete.",
        },
        "task_id=?",
        (task_id,),
    )
    conn.execute(
        """UPDATE datacamp_project_tasks
           SET scheduled_weekday=?,scheduled_date=?,required_chapters=?,updated_at=CURRENT_TIMESTAMP
           WHERE project_key=?""",
        (
            int(project.get("scheduled_weekday", 5)),
            scheduled.isoformat(),
            ",".join(project.get("required_chapters") or ()),
            str(project["key"]),
        ),
    )


def sync_tasks(conn, state=None):
    result = _weekend_legacy_sync_tasks(conn, state)
    _weekend_ensure_project_columns(conn)
    for project in PROJECTS:
        _weekend_update_project_task(conn, project)
    conn.commit()
    return result


def project_for_task(conn, task_id):
    result = _weekend_legacy_project_for_task(conn, task_id)
    if result is None:
        return None
    policy = PROJECT_BY_KEY.get(str(result.get("project_key") or ""), {})
    merged = dict(result)
    merged.update(
        {
            "scheduled_weekday": int(policy.get("scheduled_weekday", 5)),
            "required_chapters": tuple(policy.get("required_chapters") or ()),
        }
    )
    try:
        row = conn.execute(
            "SELECT scheduled_date FROM datacamp_project_tasks WHERE task_id=?",
            (int(task_id),),
        ).fetchone()
        merged["scheduled_date"] = _weekend_row_value(row, "scheduled_date", 0, None)
    except Exception:
        merged["scheduled_date"] = None
    return merged


def optional_practice_recommendation(conn, current_week, *, today=None):
    result = _weekend_legacy_optional_recommendation(
        conn, current_week, today=today
    )
    if result is None:
        return None
    policy = PROJECT_BY_KEY.get(str(result.get("project_key") or ""), {})
    merged = dict(result)
    merged["scheduled_weekday"] = int(policy.get("scheduled_weekday", 6))
    merged["weekend_label"] = "Sunday project practice"
    return merged
# END DATACAMP EXACT PROJECT PREREQUISITES v10.40.2

# BEGIN DATACAMP CATCH-UP PROJECT ACCESS v10.41.2
# The weekend restriction applies only to projects assigned to the active week.
# Once the roadmap advances, an unfinished earlier-week project is catch-up work
# and may be opened on any day after all real prerequisites are satisfied.
_catchup_legacy_project_readiness = project_readiness
_CATCHUP_TIMING_REASONS = (
    "Weekend project",
    "Scheduled for ",
)


def _catchup_active_week(conn):
    try:
        row = conn.execute(
            "SELECT current_week FROM program_state WHERE id=1"
        ).fetchone()
    except Exception:
        row = None
    value = _weekend_row_value(row, "current_week", 0, 1)
    try:
        return max(1, int(value or 1))
    except (TypeError, ValueError):
        return 1


def _catchup_is_earlier_week(conn, project):
    try:
        project_week = max(1, int(project.get("week") or 1))
    except (TypeError, ValueError):
        project_week = 1
    return project_week < _catchup_active_week(conn), project_week


def project_readiness(conn, task_id=None, project_key=None, today=None):
    project = _weekend_project_from_identity(
        conn, task_id=task_id, project_key=project_key
    )
    ready, reason = _catchup_legacy_project_readiness(
        conn, task_id=task_id, project_key=project_key, today=today
    )
    if project is None or ready:
        return ready, reason

    is_catch_up, project_week = _catchup_is_earlier_week(conn, project)
    timing_only = str(reason or "").startswith(_CATCHUP_TIMING_REASONS)
    if is_catch_up and timing_only:
        return True, f"Catch-up project from Week {project_week} — ready now."
    return ready, reason
# END DATACAMP CATCH-UP PROJECT ACCESS v10.41.2
