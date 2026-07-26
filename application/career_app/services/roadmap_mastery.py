from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

# Each passing cumulative check creates validated Academy evidence. The final
# readiness assessment also proves the Python/pandas requirement used by the
# portfolio phase.
MASTERED_ASSESSMENTS = {
    "week_2_spreadsheet_mastery": (
        ("roadmap.spreadsheet_mastery", "spreadsheet_mastery_project"),
        ("excel_analytics", "spreadsheet_mastery_project"),
    ),
    "week_6_sql_mastery": (
        ("roadmap.sql_mastery", "database_design"),
    ),
    "week_7_power_bi_mastery": (
        ("roadmap.power_bi_mastery", "powerbi_modeling"),
        ("power_bi", "powerbi_modeling"),
    ),
    "week_8_portfolio_readiness": (
        ("roadmap.portfolio_readiness", "pandas_foundations"),
        ("python_pandas", "pandas_foundations"),
    ),
}

WEEKLY_CHECKS = (
    (1, "week_1_spreadsheet_foundations_check", "Week 1 Cumulative Knowledge Check"),
    (2, "week_2_spreadsheet_mastery", "Week 2 Spreadsheet Mastery Assessment"),
    (3, "week_3_sql_foundations", "Week 3 Cumulative Knowledge Check"),
    (4, "week_4_relationships_joins", "Week 4 Cumulative Knowledge Check"),
    (5, "week_5_cleaning_ctes", "Week 5 Cumulative Knowledge Check"),
    (6, "week_6_sql_mastery", "Week 6 Spreadsheet & SQL Mastery Assessment"),
    (7, "week_7_power_bi_mastery", "Week 7 Power BI Mastery Assessment"),
    (8, "week_8_portfolio_readiness", "Week 8 Portfolio Readiness Assessment"),
)

# The spreadsheet track did not exist before v10.26.0. These lesson-level
# requirements let an existing learner catch up in sequence instead of seeing
# only the final assessments.
SPREADSHEET_LESSONS = (
    (1, "spreadsheet_structure", "Rows, Columns, Tables & Data Types", 35),
    (1, "spreadsheet_references", "Cell References, Sorting & Filtering", 35),
    (1, "conditional_formulas", "IF, AND, OR & Error Handling", 40),
    (1, "conditional_summaries", "COUNTIFS, SUMIFS & Variance", 40),
    (2, "spreadsheet_cleaning", "Text, Dates, Numbers & Duplicates", 45),
    (2, "spreadsheet_validation", "Validation Rules & Reconciliation", 45),
    (2, "spreadsheet_lookups", "Exact Lookups with XLOOKUP", 45),
    (2, "spreadsheet_relationships", "Matching Tables & Understanding Grain", 45),
    (2, "spreadsheet_pivots", "Pivot Tables, Dimensions & Measures", 45),
    (2, "spreadsheet_kpis", "KPI Summaries & Business Interpretation", 45),
    (2, "spreadsheet_workflow", "Plan a Reproducible Spreadsheet Workflow", 40),
    (2, "spreadsheet_mastery_review", "Spreadsheet Mastery Review", 45),
)

LESSON_ORDER = [lesson_id for _, lesson_id, _, _ in SPREADSHEET_LESSONS]
LESSON_TITLES = {lesson_id: title for _, lesson_id, title, _ in SPREADSHEET_LESSONS}


def _catchup_order_map() -> dict[str, int]:
    """Return a stable learning-order rank for the visible catch-up queue."""
    keys: list[str] = []
    for week in range(1, 9):
        keys.extend(
            f"lesson:{lesson_id}"
            for due_week, lesson_id, _title, _minutes in SPREADSHEET_LESSONS
            if due_week == week
        )
        keys.extend(
            f"duckdb:{number}"
            for number, item in sorted(DUCKDB_EXERCISES.items())
            if int(item.get("week", 99)) == week
        )
        keys.extend(
            f"sql:{title}"
            for title, due_week in SQL_PROBLEM_SCHEDULE.items()
            if int(due_week) == week
        )
        keys.extend(
            f"assessment:{assessment_id}"
            for due_week, assessment_id, _title in WEEKLY_CHECKS
            if int(due_week) == week
        )
    return {key: index for index, key in enumerate(keys)}


def catchup_sort_order(requirement_key: str) -> int:
    return -760000 + _catchup_order_map().get(str(requirement_key), 9000)

SQL_PROBLEM_SCHEDULE = {
    "Data Science Skills": 3,
    "Pharmacy Analytics Part 1": 3,
    "Laptop vs. Mobile Viewership": 3,
    "Teams Power Users": 3,
    "Page With No Likes": 4,
    "Signup Activation Rate": 4,
    "Second Day Confirmation": 4,
    "Histogram of Tweets": 5,
    "Duplicate Job Listings": 5,
    "Second Highest Salary": 5,
    "Supercloud Customer": 5,
    "User's Third Transaction": 6,
    "Top Three Salaries": 6,
    "Odd and Even Measurements": 6,
    "Tweets' Rolling Averages": 7,
    "User Shopping Sprees": 7,
}

ASSESSMENT_PREREQUISITES = {
    "week_3_sql_foundations": {
        "prior_assessments": {"week_2_spreadsheet_mastery"},
        "all_of": {"roadmap.spreadsheet_mastery", "sql_querying", "sql_aggregation"},
        "any_of": set(),
    },
    "week_4_relationships_joins": {
        "prior_assessments": {"week_3_sql_foundations"},
        "all_of": {"roadmap.spreadsheet_mastery", "sql_joins"},
        "any_of": set(),
    },
    "week_5_cleaning_ctes": {
        "prior_assessments": {"week_4_relationships_joins"},
        "all_of": {"roadmap.spreadsheet_mastery", "sql_case"},
        "any_of": {"sql_subqueries", "sql_ctes"},
    },
    "week_6_sql_mastery": {
        "prior_assessments": {"week_5_cleaning_ctes"},
        "all_of": {"roadmap.spreadsheet_mastery", "sql_window_functions", "sql_date_logic"},
        "any_of": {"sql_subqueries", "sql_ctes"},
    },
    "week_7_power_bi_mastery": {
        "prior_assessments": {"week_6_sql_mastery"},
        "all_of": {"roadmap.sql_mastery"},
        "any_of": set(),
    },
    "week_8_portfolio_readiness": {
        "prior_assessments": {"week_7_power_bi_mastery"},
        "all_of": {"roadmap.sql_mastery", "roadmap.power_bi_mastery"},
        "any_of": set(),
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS roadmap_requirement_state (
    requirement_key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    due_week INTEGER NOT NULL,
    source_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Future',
    reason TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_roadmap_requirement_due
    ON roadmap_requirement_state(due_week,status);
"""


def ensure_schema(conn) -> None:
    conn.executescript(SCHEMA)


def _table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _program_state(conn):
    return conn.execute("SELECT * FROM program_state WHERE id=1").fetchone()


def assessment_passed(conn, assessment_id: str) -> bool:
    if not _table_exists(conn, "academy_assessment_attempts"):
        return False
    return conn.execute(
        "SELECT 1 FROM academy_assessment_attempts WHERE assessment_id=? AND passed=1 AND COALESCE(solution_assisted,0)=0 LIMIT 1",
        (assessment_id,),
    ).fetchone() is not None


def lesson_mastered(conn, lesson_id: str) -> bool:
    if not _table_exists(conn, "academy_lesson_progress"):
        return False
    return conn.execute(
        "SELECT 1 FROM academy_lesson_progress WHERE lesson_id=? AND state='Mastered' LIMIT 1",
        (lesson_id,),
    ).fetchone() is not None


def lesson_readiness(conn, lesson_id: str) -> dict:
    if lesson_id not in LESSON_ORDER:
        return {"ready": False, "missing": ["Academy lesson"], "reason": "The Academy lesson was not found."}
    index = LESSON_ORDER.index(lesson_id)
    if index == 0:
        return {"ready": True, "missing": [], "reason": ""}
    prior = LESSON_ORDER[index - 1]
    if lesson_mastered(conn, prior):
        return {"ready": True, "missing": [], "reason": ""}
    title = LESSON_TITLES[prior]
    return {
        "ready": False,
        "missing": [title],
        "reason": f"Complete the earlier spreadsheet lesson first: {title}.",
    }


def sync_mastery_evidence(conn) -> int:
    ensure_schema(conn)
    if not _table_exists(conn, "academy_skill_evidence"):
        return 0
    inserted = 0
    for assessment_id, awards in MASTERED_ASSESSMENTS.items():
        if not assessment_passed(conn, assessment_id):
            continue
        for skill_key, course_id in awards:
            before = conn.total_changes
            conn.execute(
                """INSERT INTO academy_skill_evidence
                   (program_id,path_id,course_id,learning_item_id,skill_key,
                    source_type,source_id,difficulty,evidence_level,
                    validation_status,evidence_notes,metadata)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(skill_key,source_type,source_id) DO UPDATE SET
                       validation_status='passed',
                       evidence_notes=excluded.evidence_notes,
                       metadata=excluded.metadata""",
                (
                    "data_career_accelerator",
                    "data_analytics",
                    course_id,
                    assessment_id,
                    skill_key,
                    "Weekly Mastery Check",
                    assessment_id,
                    "intermediate",
                    "mastered",
                    "passed",
                    "Awarded after an unassisted passing weekly mastery assessment.",
                    json.dumps(
                        {"roadmap_version": "10.26.1", "assessment_id": assessment_id},
                        sort_keys=True,
                    ),
                ),
            )
            inserted += int(conn.total_changes > before)
    conn.commit()
    return inserted


def approved_skill_evidence(conn) -> dict:
    sync_mastery_evidence(conn)
    from career_app.services import tracks

    state = _program_state(conn)
    if state is None:
        return {}
    return tracks.approved_skill_evidence(conn, state)


def has_mastery_skill(conn, skill_key: str) -> bool:
    return str(skill_key) in approved_skill_evidence(conn)


def _readiness_for_spec(conn, spec: dict) -> dict:
    spec = dict(spec or {})
    missing = []
    for prior in spec.get("prior_assessments", ()):
        if not assessment_passed(conn, str(prior)):
            missing.append(_assessment_title(str(prior)))
    evidence = approved_skill_evidence(conn)
    for skill in spec.get("all_of", ()):
        if str(skill) not in evidence:
            missing.append(_readable_skill(str(skill)))
    any_of = tuple(spec.get("any_of", ()))
    if any_of and not any(str(skill) in evidence for skill in any_of):
        missing.append(
            "one of: " + " or ".join(_readable_skill(str(skill)) for skill in any_of)
        )
    missing = list(dict.fromkeys(missing))
    return {
        "ready": not missing,
        "missing": missing,
        "reason": "" if not missing else "Complete " + ", ".join(missing) + " first.",
    }


def sql_problem_readiness(conn, title: str) -> dict:
    """Return the canonical readiness record for one interview problem.

    The legacy track module still supplies durable skill-evidence calculations,
    but every caller receives the same normalized result through this facade.
    """
    from career_app.services import tracks

    state = _program_state(conn)
    if state is None:
        return {
            "ready": False,
            "missing": ["program state"],
            "missing_names": ["Program progress"],
            "required_keys": [],
            "required_names": [],
            "required_all_of": [],
            "required_any_of": [],
            "evidence": {},
            "reason": "Program progress is unavailable.",
        }
    result = dict(tracks.sql_problem_readiness(conn, state, str(title)))
    missing = list(result.get("missing_names") or [])
    result["missing"] = missing
    result["reason"] = "" if not missing else "Complete " + ", ".join(missing) + " first."
    return result


def assessment_readiness(conn, assessment_id: str) -> dict:
    assessment_id = str(assessment_id)
    if assessment_id == "week_1_spreadsheet_foundations_check":
        required = LESSON_ORDER[:4]
        missing = [LESSON_TITLES[item] for item in required if not lesson_mastered(conn, item)]
        return {
            "ready": not missing,
            "missing": missing,
            "reason": "" if not missing else "Complete " + ", ".join(missing) + " first.",
        }
    if assessment_id == "week_2_spreadsheet_mastery":
        missing = [LESSON_TITLES[item] for item in LESSON_ORDER if not lesson_mastered(conn, item)]
        if not assessment_passed(conn, "week_1_spreadsheet_foundations_check"):
            missing.append(_assessment_title("week_1_spreadsheet_foundations_check"))
        return {
            "ready": not missing,
            "missing": missing,
            "reason": "" if not missing else "Complete " + ", ".join(missing) + " first.",
        }
    return _readiness_for_spec(conn, ASSESSMENT_PREREQUISITES.get(assessment_id, {}))


def duckdb_readiness(conn, number: int) -> dict:
    number = int(number)
    item = DUCKDB_EXERCISES[number]
    completed = conn.execute(
        "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=? AND status='Completed'",
        (number,),
    ).fetchone()
    if completed:
        return {"ready": True, "missing": [], "reason": "Already completed."}
    prereq = dict(item.get("prerequisites") or {})
    missing = []
    for prior in prereq.get("prior_exercises", ()):
        row = conn.execute(
            "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=? AND status='Completed'",
            (int(prior),),
        ).fetchone()
        if row is None:
            missing.append(f"DuckDB Exercise {int(prior):02d}")
    for check in prereq.get("mastery_checks", ()):
        if not assessment_passed(conn, str(check)):
            missing.append(_assessment_title(str(check)))
    evidence = approved_skill_evidence(conn)
    for skill in prereq.get("all_of", ()):
        if str(skill) not in evidence:
            missing.append(_readable_skill(str(skill)))
    any_of = tuple(prereq.get("any_of", ()))
    if any_of and not any(str(skill) in evidence for skill in any_of):
        missing.append(
            "one of: " + " or ".join(_readable_skill(str(skill)) for skill in any_of)
        )
    missing = list(dict.fromkeys(missing))
    return {
        "ready": not missing,
        "missing": missing,
        "reason": "" if not missing else "Complete " + ", ".join(missing) + " first.",
    }


def assert_duckdb_ready(conn, number: int) -> None:
    result = duckdb_readiness(conn, number)
    if not result["ready"]:
        raise PermissionError(result["reason"])


def assert_duckdb_ready_from_root(root: Path, number: int) -> None:
    db_path = Path(root) / "data" / "career_accelerator.db"
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert_duckdb_ready(conn, number)
    finally:
        conn.close()


def _assessment_title(assessment_id: str) -> str:
    for _, current, title in WEEKLY_CHECKS:
        if current == assessment_id:
            return title
    return assessment_id.replace("_", " ").title()


def _readable_skill(skill_key: str) -> str:
    labels = {
        "roadmap.spreadsheet_mastery": "Spreadsheet Mastery",
        "roadmap.sql_mastery": "Spreadsheet & SQL Mastery",
        "roadmap.power_bi_mastery": "Power BI Mastery",
        "roadmap.portfolio_readiness": "Portfolio Readiness",
    }
    if skill_key in labels:
        return labels[skill_key]
    try:
        from career_app.services import tracks

        definition = tracks.SKILL_DEFINITIONS.get(skill_key)
        if definition:
            return str(definition[0])
    except Exception:
        pass
    return skill_key.replace("roadmap.", "").replace("sql_", "SQL ").replace("_", " ").title()


def _upsert_requirement(conn, key, kind, title, due_week, source_id, status, reason):
    conn.execute(
        """INSERT INTO roadmap_requirement_state
           (requirement_key,kind,title,due_week,source_id,status,reason,updated_at)
           VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(requirement_key) DO UPDATE SET
             kind=excluded.kind,title=excluded.title,due_week=excluded.due_week,
             source_id=excluded.source_id,status=excluded.status,reason=excluded.reason,
             updated_at=CURRENT_TIMESTAMP""",
        (key, kind, title, int(due_week), source_id, status, reason),
    )


def _task_for_managed_key(conn, managed_key):
    return conn.execute(
        """SELECT s.id,s.completed FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key=? LIMIT 1""",
        (managed_key,),
    ).fetchone()


def _stage_existing_catchup_orders(conn) -> None:
    """Move existing managed rows out of the final ordering range before re-ranking.

    Earlier v10.26 builds assigned catch-up rows in creation order. Reordering
    them in place can temporarily collide with another row's unique
    ``(week, sort_order)`` value. A deterministic staging range makes the
    migration repeatable and collision-free.
    """
    rows = conn.execute(
        """SELECT s.id FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:%'
           ORDER BY s.id"""
    ).fetchall()
    for row in rows:
        task_id = int(row["id"] if hasattr(row, "keys") else row[0])
        conn.execute(
            "UPDATE sprint_tasks SET sort_order=? WHERE id=?",
            (-9000000 - task_id, task_id),
        )


def _create_or_update_catchup(
    conn,
    *,
    key,
    title,
    current_week,
    destination,
    category,
    reason,
    minutes,
    starter_path=None,
    prerequisite_state="Ready",
    prerequisite_reason=None,
):
    managed_key = f"roadmap_v1026:{key}"
    existing = _task_for_managed_key(conn, managed_key)
    sort_order = catchup_sort_order(key)
    if existing is None:
        cur = conn.execute(
            "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
            (current_week, sort_order, title),
        )
        task_id = int(cur.lastrowid)
        conn.execute(
            """INSERT INTO task_metadata
               (task_id,status,priority,estimated_minutes,energy,destination,category,
                prerequisite_state,prerequisite_reason,description,definition_of_done,
                starter_path,managed_key)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                task_id,
                "Not Started",
                0,
                int(minutes),
                "Normal",
                int(destination),
                category,
                prerequisite_state,
                prerequisite_reason,
                reason,
                "Complete and pass this overdue roadmap requirement.",
                starter_path,
                managed_key,
            ),
        )
        return task_id
    task_id = int(existing["id"])
    conn.execute(
        "UPDATE sprint_tasks SET week=?,sort_order=?,label=?,completed=0 WHERE id=?",
        (current_week, sort_order, title, task_id),
    )
    conn.execute(
        """UPDATE task_metadata SET status='Not Started',priority=0,estimated_minutes=?,
           destination=?,category=?,prerequisite_state=?,prerequisite_reason=?,description=?,
           definition_of_done=?,starter_path=?,managed_key=? WHERE task_id=?""",
        (
            int(minutes),
            int(destination),
            category,
            prerequisite_state,
            prerequisite_reason,
            reason,
            "Complete and pass this overdue roadmap requirement.",
            starter_path,
            managed_key,
            task_id,
        ),
    )
    return task_id


def _complete_catchup(conn, key):
    row = _task_for_managed_key(conn, f"roadmap_v1026:{key}")
    if row is None:
        return
    task_id = int(row["id"])
    conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
    conn.execute(
        "UPDATE task_metadata SET status='Completed',prerequisite_state='Ready',prerequisite_reason=NULL WHERE task_id=?",
        (task_id,),
    )


def requirement_complete(conn, requirement_key: str) -> bool:
    key = str(requirement_key)
    if key.startswith("lesson:"):
        return lesson_mastered(conn, key.split(":", 1)[1])
    if key.startswith("assessment:"):
        return assessment_passed(conn, key.split(":", 1)[1])
    if key.startswith("duckdb:"):
        number = int(key.split(":", 1)[1])
        row = conn.execute(
            "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=? AND status='Completed'",
            (number,),
        ).fetchone()
        return row is not None
    if key.startswith("sql:"):
        title = key.split(":", 1)[1]
        row = conn.execute(
            "SELECT 1 FROM sql_practice WHERE platform='DataLemur' AND title=? AND status='Completed'",
            (title,),
        ).fetchone()
        return row is not None
    return False


def assert_managed_task_complete(conn, task_id: int) -> None:
    row = conn.execute(
        "SELECT managed_key FROM task_metadata WHERE task_id=?", (int(task_id),)
    ).fetchone()
    managed = str(row["managed_key"] or "") if row else ""
    prefix = "roadmap_v1026:"
    if not managed.startswith(prefix):
        return
    requirement_key = managed[len(prefix) :]
    if requirement_complete(conn, requirement_key):
        return
    req = conn.execute(
        "SELECT title,status,reason FROM roadmap_requirement_state WHERE requirement_key=?",
        (requirement_key,),
    ).fetchone()
    title = str(req["title"] if req else requirement_key)
    reason = str(req["reason"] or "Open the linked learning workspace and complete the validated requirement first.") if req else "Open the linked learning workspace and complete the validated requirement first."
    raise ValueError(f"{title} cannot be checked off manually. {reason}")


def _retire_legacy_datacamp_tasks(conn) -> None:
    # Preserve historical learning records, but remove obsolete DataCamp tasks
    # from active schedules and prerequisite messages.
    rows = conn.execute(
        """SELECT s.id FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           LEFT JOIN track_tasks tt ON tt.task_id=s.id
           WHERE s.completed=0 AND (LOWER(s.label) LIKE '%datacamp%' OR LOWER(COALESCE(tt.track_key,''))='datacamp')"""
    ).fetchall()
    for row in rows:
        task_id = int(row["id"])
        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
        conn.execute(
            "UPDATE task_metadata SET status='Completed',prerequisite_state='Ready',prerequisite_reason=NULL WHERE task_id=?",
            (task_id,),
        )


def reconcile(conn, root=None) -> dict:
    ensure_schema(conn)
    sync_mastery_evidence(conn)
    _retire_legacy_datacamp_tasks(conn)
    _stage_existing_catchup_orders(conn)
    state = _program_state(conn)
    current_week = max(1, int(state["current_week"] if state else 1))
    overdue = []
    completed = []

    # New spreadsheet lessons are reconciled before their weekly assessments.
    for due_week, lesson_id, title, minutes in SPREADSHEET_LESSONS:
        done = lesson_mastered(conn, lesson_id)
        readiness = lesson_readiness(conn, lesson_id)
        status = "Completed" if done else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if done else (readiness["reason"] or f"Expected by Week {due_week}. Complete this Academy lesson before advancing.")
        key = f"lesson:{lesson_id}"
        _upsert_requirement(conn, key, "academy_lesson", title, due_week, lesson_id, status, reason)
        if done:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=title,
                current_week=current_week,
                destination=12,
                category="Learning",
                reason=f"Expected by Week {due_week}. Complete and master this spreadsheet lesson.",
                minutes=minutes,
                starter_path=f"academy:lesson:{lesson_id}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    for due_week, assessment_id, title in WEEKLY_CHECKS:
        passed = assessment_passed(conn, assessment_id)
        readiness = assessment_readiness(conn, assessment_id)
        status = "Completed" if passed else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if passed else (readiness["reason"] or f"Expected by Week {due_week}. This mastery check gates later learning.")
        key = f"assessment:{assessment_id}"
        _upsert_requirement(conn, key, "assessment", title, due_week, assessment_id, status, reason)
        if passed:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=title,
                current_week=current_week,
                destination=12,
                category="Learning",
                reason=f"Expected by Week {due_week}. This mastery check gates later learning.",
                minutes=45,
                starter_path=f"academy:assessment:{assessment_id}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    for number, item in DUCKDB_EXERCISES.items():
        due_week = int(item.get("week", 99))
        row = conn.execute(
            "SELECT status FROM duckdb_exercise_progress WHERE exercise_number=?",
            (int(number),),
        ).fetchone()
        done = bool(row and row["status"] == "Completed")
        readiness = duckdb_readiness(conn, number)
        status = "Completed" if done else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if done else (readiness["reason"] or f"Expected by Week {due_week}.")
        key = f"duckdb:{number}"
        _upsert_requirement(conn, key, "duckdb", item["title"], due_week, str(number), status, reason)
        if done:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=item["label"],
                current_week=current_week,
                destination=2,
                category="SQL",
                reason=f"Expected by Week {due_week}. Complete this skill-gated DuckDB exercise.",
                minutes=int(item.get("minutes", 40)),
                starter_path=f"duckdb:{number}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    for title, due_week in SQL_PROBLEM_SCHEDULE.items():
        row = conn.execute(
            "SELECT status FROM sql_practice WHERE platform='DataLemur' AND title=?",
            (title,),
        ).fetchone()
        done = bool(row and row["status"] == "Completed")
        key = f"sql:{title}"
        readiness = sql_problem_readiness(conn, title)
        status = "Completed" if done else (("Overdue" if readiness["ready"] else "Locked") if due_week <= current_week else "Future")
        reason = None if done else (readiness["reason"] or f"Expected by Week {due_week}; complete this interview problem.")
        _upsert_requirement(conn, key, "sql_problem", title, due_week, title, status, reason)
        if done:
            _complete_catchup(conn, key)
            completed.append(key)
        elif due_week <= current_week:
            _create_or_update_catchup(
                conn,
                key=key,
                title=f"Solve {title}",
                current_week=current_week,
                destination=4,
                category="SQL",
                reason=f"Expected by Week {due_week}. Complete this skill-gated SQL Companion problem.",
                minutes=35,
                starter_path=f"sql-problem:{title}",
                prerequisite_state="Ready" if readiness["ready"] else "Blocked",
                prerequisite_reason=None if readiness["ready"] else readiness["reason"],
            )
            overdue.append(key)

    # Today’s Focus is rebuilt by the unified planner after reconciliation.
    # Do not clear the snapshot here; doing so caused empty dashboards when a
    # later startup step failed before the planner regenerated it.
    conn.commit()
    return {"current_week": current_week, "overdue": overdue, "completed": completed}
