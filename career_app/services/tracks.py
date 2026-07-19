from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

from career_app.data.applied_exercises import (
    APPLIED_EXERCISES,
    APPLIED_SKILL_EVIDENCE,
    exercise_number_for_label as applied_exercise_number_for_label,
)
from career_app.services import achievements as achievement_service
from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES,
    exercise_for_label,
    exercise_number_for_label,
)
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
    "applied": {
        "display_name": "Applied Labs",
        "category": "Learning",
        "destination": 2,
        "priority": 3,
        "sort_band": -50000,
        "role": "Supplemental",
    },
}

TRACK_ORDER = (
    "google",
    "datacamp",
    "sql",
    "portfolio",
    "applied",
)


# Current English Google Data Analytics Professional Certificate curriculum.
# Progression must use course-specific module totals rather than assuming every
# course has the same number of modules.
GOOGLE_COURSE_MODULE_COUNTS = {
    1: 4,
    2: 4,
    3: 5,
    4: 6,
    5: 4,
    6: 4,
    7: 5,
    8: 4,
    9: 4,
}


def google_module_count(course):
    """Return the valid module count for a Google certificate course."""
    return int(GOOGLE_COURSE_MODULE_COUNTS.get(max(1, int(course)), 4))


def normalize_google_position(course, module):
    """Return a valid certificate checkpoint.

    Invalid legacy checkpoints (for example Course 5, Module 5 or 6) move to
    the first module of the next course. We intentionally do not carry an
    overflow count because the overflow modules never represented real work.
    """
    course = max(1, int(course))
    module = max(1, int(module))
    total_courses = max(GOOGLE_COURSE_MODULE_COUNTS)

    if course > total_courses:
        return total_courses, google_module_count(total_courses)

    if module > google_module_count(course):
        if course < total_courses:
            return course + 1, 1
        return course, google_module_count(course)

    return course, module


def next_google_position(course, module):
    """Advance one real module, rolling directly into the next course."""
    course, module = normalize_google_position(course, module)
    if module < google_module_count(course):
        return course, module + 1
    if course < max(GOOGLE_COURSE_MODULE_COUNTS):
        return course + 1, 1
    return course, module


def _google_position_from_text(value):
    match = re.search(
        r"course\s*:?\s*(\d+).*module\s*:?\s*(\d+)",
        str(value or ""),
        re.IGNORECASE,
    )
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _google_event_details(row):
    try:
        metadata = json.loads(row["metadata"] or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        metadata = {}

    course = metadata.get("course")
    module = metadata.get("module")
    try:
        if course is not None and module is not None:
            position = (int(course), int(module))
        else:
            position = None
    except (TypeError, ValueError):
        position = None

    if position is None:
        position = _google_position_from_text(row["event_key"])
    if position is None:
        position = _google_position_from_text(row["item_label"])

    task_id = metadata.get("task_id")
    try:
        task_id = int(task_id) if task_id is not None else None
    except (TypeError, ValueError):
        task_id = None
    return position, task_id


def _invalid_google_position(position):
    if position is None:
        return False
    course, module = position
    if course not in GOOGLE_COURSE_MODULE_COUNTS:
        return True
    return module < 1 or module > google_module_count(course)


def repair_invalid_google_progress(conn):
    """Remove legacy completions for certificate modules that never existed.

    Earlier builds could generate Course 5 Modules 5 and 6. Those events must
    not count toward the weekly quota, completion history, or today's frozen
    focus plan. The repair preserves any learner notes by detaching task
    workspaces before removing the invalid generated task rows.
    """
    event_rows = conn.execute(
        """SELECT id,event_key,item_label,metadata
           FROM track_events
           WHERE track_key='google'"""
    ).fetchall()

    invalid_event_ids = []
    invalid_target_keys = set()
    invalid_task_ids = set()
    for row in event_rows:
        position, task_id = _google_event_details(row)
        if not _invalid_google_position(position):
            continue
        invalid_event_ids.append(int(row["id"]))
        invalid_target_keys.add(str(row["event_key"]))
        if task_id is not None:
            invalid_task_ids.add(task_id)

    # Also catch an invalid active task or an old generated task whose event
    # metadata did not contain its task id.
    generated_rows = conn.execute(
        """SELECT id,label
           FROM sprint_tasks
           WHERE sort_order<=?
             AND sort_order>?
             AND LOWER(label) LIKE 'continue google course%, module%'""",
        (
            TRACK_CONFIG["google"]["sort_band"],
            TRACK_CONFIG["google"]["sort_band"] - 99999,
        ),
    ).fetchall()
    for row in generated_rows:
        position = _google_position_from_text(row["label"])
        if _invalid_google_position(position):
            invalid_task_ids.add(int(row["id"]))
            if position is not None:
                invalid_target_keys.add(
                    f"course:{position[0]}:module:{position[1]}"
                )

    active = conn.execute(
        """SELECT task_id,target_key
           FROM track_tasks
           WHERE track_key='google'"""
    ).fetchone()
    if active is not None:
        position = _google_position_from_text(active["target_key"])
        if _invalid_google_position(position):
            invalid_task_ids.add(int(active["task_id"]))
            invalid_target_keys.add(str(active["target_key"]))

    if not invalid_event_ids and not invalid_task_ids and not invalid_target_keys:
        return {
            "events_removed": 0,
            "tasks_removed": 0,
            "snapshot_rebuilt": False,
        }

    if invalid_event_ids:
        placeholders = ",".join("?" for _ in invalid_event_ids)
        conn.execute(
            f"DELETE FROM track_events WHERE id IN ({placeholders})",
            tuple(invalid_event_ids),
        )

    if invalid_target_keys:
        placeholders = ",".join("?" for _ in invalid_target_keys)
        values = tuple(sorted(invalid_target_keys))
        conn.execute(
            f"""DELETE FROM daily_focus
                WHERE track_key='google'
                  AND target_key IN ({placeholders})""",
            values,
        )
        conn.execute(
            f"""DELETE FROM track_tasks
                WHERE track_key='google'
                  AND target_key IN ({placeholders})""",
            values,
        )

    if invalid_task_ids:
        task_ids = tuple(sorted(invalid_task_ids))
        placeholders = ",".join("?" for _ in task_ids)
        # Keep notes and study-session history, but remove their stale task link.
        conn.execute(
            f"UPDATE task_workspaces SET task_id=NULL WHERE task_id IN ({placeholders})",
            task_ids,
        )
        conn.execute(
            f"UPDATE study_sessions SET task_id=NULL WHERE task_id IN ({placeholders})",
            task_ids,
        )
        conn.execute(
            f"DELETE FROM daily_focus WHERE task_id IN ({placeholders})",
            task_ids,
        )
        conn.execute(
            f"DELETE FROM sprint_tasks WHERE id IN ({placeholders})",
            task_ids,
        )

    # Today's plan was calculated from the now-invalid weekly count. Remove the
    # derived snapshot so the normal refresh path rebuilds it from clean data.
    conn.execute(
        "DELETE FROM daily_focus WHERE focus_date=?",
        (date.today().isoformat(),),
    )
    conn.execute(
        "DELETE FROM track_tasks WHERE track_key='google'"
    )
    conn.execute(
        "DELETE FROM settings WHERE key='current_google_task_id'"
    )
    conn.execute(
        """UPDATE track_state
           SET status='Active',metadata='{}',updated_at=CURRENT_TIMESTAMP
           WHERE track_key='google'"""
    )
    conn.commit()
    return {
        "events_removed": len(invalid_event_ids),
        "tasks_removed": len(invalid_task_ids),
        "snapshot_rebuilt": True,
    }


def normalize_google_checkpoint(conn, state):
    """Repair invalid stored Google checkpoints before adaptive planning."""
    repair_invalid_google_progress(conn)

    current_course = int(state["google_course"])
    current_module = int(state["google_module"])
    course, module = normalize_google_position(current_course, current_module)
    normalized = dict(state)
    normalized["google_course"] = course
    normalized["google_module"] = module

    if (course, module) == (current_course, current_module):
        return normalized

    conn.execute(
        """UPDATE program_state
           SET google_course=?,google_module=?
           WHERE id=1""",
        (course, module),
    )
    # Remove the stale adaptive link so sync_all builds the corrected target.
    conn.execute(
        "DELETE FROM track_tasks WHERE track_key='google'"
    )
    conn.execute(
        "DELETE FROM settings WHERE key='current_google_task_id'"
    )
    conn.commit()
    return normalized


APPLIED_BRANCHES = {'Power BI': (1, 2, 3, 4, 5, 6, 36),
 'Excel': (7,),
 'pandas': (8, 9, 10, 11),
 'Communication': (12, 13, 14),
 'SQL Quality': (15, 16, 17, 18),
 'Timed Requests': (19, 20, 21),
 'Statistics': (22, 23, 24, 25, 26, 27, 28),
 'Business Patterns': (29, 30, 31, 32),
 'Data Workflow': (33, 34),
 'Responsible AI': (35,)}

APPLIED_BRANCH_ORDER = tuple(
    APPLIED_BRANCHES
)

APPLIED_REQUIRED_SKILLS = {2: {'power_query'},
 3: {'power_query'},
 4: {'dimensional_modeling'},
 5: {'dax_measures'},
 6: {'report_design'},
 7: {'data_preparation'},
 11: {'sql_aggregation'},
 12: {'analysis_foundations'},
 15: {'sql_querying'},
 16: {'sql_joins'},
 17: {'sql_aggregation', 'sql_date_logic'},
 18: {'data_storytelling'},
 19: {'sql_validation', 'analyst_communication'},
 21: {'analyst_communication'},
 22: {'analysis_foundations'},
 23: {'descriptive_statistics', 'data_preparation'},
 24: {'sampling_bias', 'descriptive_statistics'},
 25: {'confidence_intervals'},
 26: {'hypothesis_testing', 'analyst_communication'},
 27: {'experiment_analysis'},
 28: {'causal_reasoning', 'python_pandas'},
 29: {'business_framing', 'sql_aggregation'},
 30: {'sql_date_logic', 'sql_ctes', 'funnel_analysis'},
 31: {'cohort_analysis', 'sql_date_logic', 'sql_joins'},
 32: {'analysis_foundations', 'sql_aggregation', 'churn_analysis'},
 33: {'python_pandas', 'data_preparation'},
 34: {'api_ingestion', 'data_cleaning', 'sql_ctes'},
 35: {'diagnostic_reasoning', 'analyst_communication', 'sql_validation'},
 36: {'power_bi_governance', 'report_design'}}

APPLIED_WEEK_BRANCH_PRIORITY = {1: ('Statistics',
     'Business Patterns',
     'SQL Quality',
     'Excel',
     'Power BI',
     'pandas',
     'Communication',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 2: ('Statistics',
     'Business Patterns',
     'SQL Quality',
     'Excel',
     'Power BI',
     'pandas',
     'Communication',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 3: ('Excel',
     'SQL Quality',
     'Statistics',
     'Communication',
     'Business Patterns',
     'Power BI',
     'pandas',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 4: ('Statistics',
     'SQL Quality',
     'Excel',
     'Communication',
     'Business Patterns',
     'Power BI',
     'pandas',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 5: ('Statistics',
     'Business Patterns',
     'SQL Quality',
     'Communication',
     'Excel',
     'Power BI',
     'pandas',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 6: ('Statistics',
     'SQL Quality',
     'Business Patterns',
     'Timed Requests',
     'Communication',
     'Excel',
     'Power BI',
     'pandas',
     'Data Workflow',
     'Responsible AI'),
 7: ('Statistics',
     'Business Patterns',
     'Power BI',
     'Communication',
     'SQL Quality',
     'Timed Requests',
     'Excel',
     'pandas',
     'Data Workflow',
     'Responsible AI'),
 8: ('Statistics',
     'Business Patterns',
     'Power BI',
     'pandas',
     'Communication',
     'SQL Quality',
     'Timed Requests',
     'Data Workflow',
     'Excel',
     'Responsible AI'),
 9: ('Statistics',
     'Business Patterns',
     'Data Workflow',
     'Power BI',
     'Communication',
     'pandas',
     'SQL Quality',
     'Timed Requests',
     'Excel',
     'Responsible AI'),
 10: ('Statistics',
      'Data Workflow',
      'Business Patterns',
      'pandas',
      'Timed Requests',
      'Communication',
      'Power BI',
      'SQL Quality',
      'Excel',
      'Responsible AI'),
 11: ('Responsible AI',
      'Data Workflow',
      'Communication',
      'Timed Requests',
      'Statistics',
      'Business Patterns',
      'pandas',
      'Power BI',
      'SQL Quality',
      'Excel'),
 12: ('Responsible AI',
      'Data Workflow',
      'Statistics',
      'Business Patterns',
      'Timed Requests',
      'Communication',
      'Power BI',
      'pandas',
      'SQL Quality',
      'Excel')}


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
        "Approved SQL learning or practice evidence",
    ),
    "sql_querying": (
        "SELECT, filtering, sorting, and limiting",
        "Approved SQL learning or practice evidence",
    ),
    "sql_aggregation": (
        "SQL Aggregation and HAVING",
        "Approved aggregation evidence",
    ),
    "sql_date_logic": (
        "SQL Date Filtering",
        "Approved SQL date-logic evidence",
    ),
    "sql_case": (
        "SQL Conditional Operations",
        "Approved CASE-expression evidence",
    ),
    "sql_joins": (
        "SQL Joins",
        "Approved join evidence",
    ),
    "sql_subqueries": (
        "SQL Subqueries",
        "Approved subquery evidence",
    ),
    "sql_ctes": (
        "Subqueries and Common Table Expressions",
        "Approved CTE evidence",
    ),
    "sql_window_functions": (
        "SQL Window Functions",
        "Approved window-function evidence",
    ),
    "sql_intermediate": (
        "Intermediate SQL",
        "Approved advanced SQL evidence",
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
    "excel_analytics": ("Excel Analysis and Controls", "Complete the Excel analyst workbook lab"),
    "power_query": ("Power Query Data Preparation", "Complete an approved Power Query lab"),
    "dimensional_modeling": ("Dimensional Modeling", "Complete the Power BI star-schema lab"),
    "dax_measures": ("DAX Measure Development", "Complete the DAX measures lab"),
    "report_design": ("Dashboard and Report Design", "Complete the executive report lab"),
    "power_bi_governance": ("Power BI Deployment and Governance", "Complete the publishing and security lab"),
    "analyst_communication": ("Analyst Communication", "Complete an executive-summary, walkthrough, or stakeholder-response lab"),
    "analysis_governance": ("Analytical Decisions and Limitations", "Complete a decision-log or responsible-metric lab"),
    "sql_validation": ("SQL Validation and Reconciliation", "Complete an approved validation or reconciliation lab"),
    "diagnostic_reasoning": ("Diagnosing Broken Analyses", "Complete a broken-analysis diagnostic lab"),
    "timed_analysis": ("Timed Analytical Problem Solving", "Complete a timed analyst request"),
    "statistics_foundations": ('Statistics Foundations', 'Complete the descriptive-statistics and sampling labs'),
    "descriptive_statistics": ('Descriptive Statistics and Distributions', 'Complete Applied Lab 22'),
    "sampling_bias": ('Sampling and Bias Evaluation', 'Complete Applied Lab 23'),
    "confidence_intervals": ('Confidence Intervals and Margin of Error', 'Complete Applied Lab 24'),
    "inferential_statistics": ('Inferential Statistics', 'Complete approved confidence-interval or hypothesis-testing work'),
    "hypothesis_testing": ('Hypothesis Testing', 'Complete Applied Lab 25'),
    "experiment_analysis": ('A/B-Test and Experiment Analysis', 'Complete Applied Lab 26'),
    "causal_reasoning": ('Correlation and Causal Reasoning', 'Complete Applied Lab 27'),
    "regression_interpretation": ('Linear Regression Interpretation', 'Complete Applied Lab 28'),
    "funnel_analysis": ('Conversion Funnel Analysis', 'Complete Applied Lab 29'),
    "cohort_analysis": ('Cohort and Retention Analysis', 'Complete Applied Lab 30'),
    "churn_analysis": ('Customer and Revenue Churn Analysis', 'Complete Applied Lab 31'),
    "variance_analysis": ('Forecast and Variance Analysis', 'Complete Applied Lab 32'),
    "api_ingestion": ('REST API and JSON Ingestion', 'Complete Applied Lab 33'),
    "data_pipeline": ('Reproducible Analytics Pipeline', 'Complete Applied Lab 34'),
    "data_lineage": ('Data Lineage and Layered Modeling', 'Complete Applied Lab 34'),
    "ai_validation": ('Responsible AI-Assisted Analysis Validation', 'Complete Applied Lab 35'),
    "power_bi_performance": ('Power BI Performance Optimization', 'Complete optional Applied Lab 36'),

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
    "Aggregation": {"sql_aggregation"},
    "Multi-step Aggregation": {
        "sql_aggregation",
        "sql_ctes",
    },
    "Conditional Logic": {
        "sql_aggregation",
        "sql_case",
    },
    "Joins": {"sql_joins"},
    "Arithmetic": {
        "analysis_foundations",
        "sql_aggregation",
    },
    "Window Functions": {
        "sql_window_functions",
    },
    "Ranking": {
        "sql_window_functions",
    },
    "Date Logic": {
        "sql_aggregation",
        "sql_date_logic",
    },
    "Relational Division": {
        "sql_aggregation",
        "sql_joins",
    },
}


SQL_PROBLEM_REQUIREMENTS = {
    "Histogram of Tweets": {
        "sql_aggregation",
        "sql_ctes",
    },
    "Data Science Skills": {
        "sql_aggregation",
    },
    "Page With No Likes": {
        "sql_joins",
    },
    "Laptop vs. Mobile Viewership": {
        "sql_aggregation",
        "sql_case",
    },
    "Duplicate Job Listings": {
        "sql_aggregation",
    },
    "Teams Power Users": {
        "sql_aggregation",
    },
    "Pharmacy Analytics Part 1": {
        "analysis_foundations",
        "sql_aggregation",
    },
    "Signup Activation Rate": {
        "sql_aggregation",
        "sql_joins",
    },
    "User's Third Transaction": {
        "sql_window_functions",
    },
    "Second Highest Salary": {
        "sql_window_functions",
    },
    "Top Three Salaries": {
        "sql_joins",
        "sql_window_functions",
    },
    "Tweets' Rolling Averages": {
        "sql_window_functions",
    },
    "Odd and Even Measurements": {
        "sql_ctes",
        "sql_window_functions",
    },
    "User Shopping Sprees": {
        "sql_aggregation",
        "sql_date_logic",
    },
    "Supercloud Customer": {
        "sql_aggregation",
        "sql_joins",
    },
    "Second Day Confirmation": {
        "sql_date_logic",
        "sql_joins",
    },
}



SQL_SKILL_ACCEPTED_EVIDENCE = {
    "sql_fundamentals": (
        "DataCamp Introduction to SQL, completed Google Course 5, "
        "DuckDB Exercise 01, or completed SQL practice"
    ),
    "sql_querying": (
        "DataCamp Introduction to SQL, completed Google Course 5, "
        "DuckDB Exercise 01, or completed querying practice"
    ),
    "sql_aggregation": (
        "DataCamp Intermediate SQL: Data Aggregation, completed Google Course 5, "
        "DuckDB Exercise 02/04/05, or a completed aggregation problem"
    ),
    "sql_date_logic": (
        "DataCamp Intermediate SQL: Data Filtering, DuckDB Exercise 04, "
        "or a completed date-logic problem"
    ),
    "sql_case": (
        "DataCamp Intermediate SQL: Conditional Operations, DuckDB Exercise "
        "03/04/05, or a completed CASE problem"
    ),
    "sql_joins": (
        "DataCamp Joining Data in SQL, DuckDB Exercise 06, "
        "or a completed join problem"
    ),
    "sql_subqueries": (
        "DataCamp Data Manipulation in SQL: Subqueries, DuckDB Exercise 07, "
        "or completed subquery practice"
    ),
    "sql_ctes": (
        "DataCamp Data Manipulation in SQL: CTEs, DuckDB Exercise "
        "07/08/09/10/12, or a completed CTE problem"
    ),
    "sql_window_functions": (
        "DataCamp Data Manipulation in SQL: Window Functions, DuckDB Exercise "
        "08/10/11, or a completed window-function problem"
    ),
    "sql_intermediate": (
        "Completed subquery, CTE, or window-function learning and practice"
    ),
}

DUCKDB_SKILL_EVIDENCE = {
    1: {"sql_fundamentals", "sql_querying"},
    2: {"sql_aggregation"},
    3: {"sql_case"},
    4: {"sql_aggregation", "sql_date_logic", "sql_case"},
    5: {"sql_aggregation", "sql_case"},
    6: {"sql_joins"},
    7: {"sql_subqueries", "sql_ctes", "sql_intermediate"},
    8: {
        "sql_aggregation", "sql_case", "sql_joins", "sql_ctes",
        "sql_window_functions", "sql_intermediate"
    },
    9: {
        "sql_aggregation", "sql_case", "sql_joins", "sql_ctes",
        "sql_intermediate"
    },
    10: {
        "sql_aggregation", "sql_joins", "sql_ctes",
        "sql_window_functions", "sql_intermediate"
    },
    11: {"sql_joins", "sql_window_functions", "sql_intermediate"},
    12: {"sql_ctes", "sql_intermediate"},
}

DATACAMP_SKILL_THRESHOLDS = {
    "sql_fundamentals": 2,
    "sql_querying": 2,
    "sql_aggregation": 3,
    "sql_date_logic": 5,
    "sql_case": 6,
    "sql_joins": 8,
    "sql_subqueries": 10,
    "sql_ctes": 11,
    "sql_window_functions": 12,
    "sql_intermediate": 12,
    "power_bi_foundations": 16,
    "power_bi": 20,
    "python_pandas": 28,
}

SQL_SKILL_HIERARCHY = {
    "sql_aggregation": {"sql_fundamentals", "sql_querying"},
    "sql_date_logic": {"sql_fundamentals", "sql_querying"},
    "sql_case": {"sql_fundamentals", "sql_querying"},
    "sql_joins": {"sql_fundamentals", "sql_querying"},
    "sql_subqueries": {
        "sql_fundamentals", "sql_querying", "sql_intermediate"
    },
    "sql_ctes": {
        "sql_fundamentals", "sql_querying",
        "sql_subqueries", "sql_intermediate"
    },
    "sql_window_functions": {
        "sql_fundamentals", "sql_querying", "sql_intermediate"
    },
}

SKILL_CATEGORY = {
    "analytics_foundations": "Analytics",
    "business_framing": "Analytics",
    "data_preparation": "Data Management",
    "data_cleaning": "Data Management",
    "analysis_foundations": "Analytics",
    "visualization_foundations": "Visualization",
    "data_storytelling": "Visualization",
    "power_bi_foundations": "Power BI",
    "power_bi": "Power BI",
    "python_pandas": "Python",
    "portfolio_delivery": "Portfolio",
    "career_readiness": "Career",
    "excel_analytics": "Excel",
    "power_query": "Power BI",
    "dimensional_modeling": "Power BI",
    "dax_measures": "Power BI",
    "report_design": "Power BI",
    "power_bi_governance": "Power BI",
    "analyst_communication": "Communication",
    "analysis_governance": "Communication",
    "sql_validation": "SQL",
    "diagnostic_reasoning": "Analytics",
    "timed_analysis": "Analytics",
    "statistics_foundations": 'Statistics',
    "descriptive_statistics": 'Statistics',
    "sampling_bias": 'Statistics',
    "confidence_intervals": 'Statistics',
    "inferential_statistics": 'Statistics',
    "hypothesis_testing": 'Statistics',
    "experiment_analysis": 'Statistics',
    "causal_reasoning": 'Statistics',
    "regression_interpretation": 'Statistics',
    "funnel_analysis": 'Business Analysis',
    "cohort_analysis": 'Business Analysis',
    "churn_analysis": 'Business Analysis',
    "variance_analysis": 'Business Analysis',
    "api_ingestion": 'Data Acquisition',
    "data_pipeline": 'Data Workflow',
    "data_lineage": 'Data Workflow',
    "ai_validation": 'Responsible AI',
    "power_bi_performance": 'Power BI',

}


def _sql_requirements(
    title,
    topic,
):
    return set(
        SQL_PROBLEM_REQUIREMENTS.get(
            title,
            SQL_REQUIREMENTS.get(
                topic,
                {"sql_querying"},
            ),
        )
    )


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


def _daily_completed(conn, track_key):
    return conn.execute(
        """SELECT COUNT(*)
           FROM track_events
           WHERE track_key=?
             AND completed_date=?""",
        (
            track_key,
            date.today().isoformat(),
        ),
    ).fetchone()[0]


def adaptive_targets(
    state,
    *,
    portfolio_ready=True,
):
    """Allocate the weekly study budget with certificate-first priority."""
    hours = max(
        1.0,
        float(state["weekly_target_hours"]),
    )
    current_week = max(
        1,
        int(state["current_week"]),
    )

    google_minutes = int(
        hours * 60 * 0.67
    )
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
    applied_target = (
        3
        if (
            hours >= 20
            and current_week
            in {7, 8, 9, 10}
        )
        else 2
        if (
            hours >= 15
            and current_week >= 4
        )
        else 1
        if hours >= 10
        else 0
    )

    return {
        "google": {
            "weekly_target": google_target,
            "allocation_percent": 67,
            "allocation_minutes": google_minutes,
        },
        "datacamp": {
            "weekly_target": datacamp_target,
            "allocation_percent": 10,
            "allocation_minutes": int(
                hours * 60 * 0.10
            ),
        },
        "sql": {
            "weekly_target": sql_target,
            "allocation_percent": 8,
            "allocation_minutes": int(
                hours * 60 * 0.08
            ),
        },
        "portfolio": {
            "weekly_target": portfolio_target,
            "allocation_percent": 7,
            "allocation_minutes": int(
                hours * 60 * 0.07
            ),
        },
        "applied": {
            "weekly_target": applied_target,
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
    daily_completed,
    role,
    allocation_percent,
):
    weekly_target = int(weekly_target)
    weekly_completed = int(weekly_completed)
    daily_completed = int(daily_completed)

    days_left = _days_remaining()
    remaining = max(
        0,
        weekly_target - weekly_completed,
    )

    # Base today's quota on progress completed before today. This prevents a
    # two-item catch-up target from shrinking after the first completion.
    completed_before_today = max(
        0,
        weekly_completed - daily_completed,
    )
    remaining_at_start_today = max(
        0,
        weekly_target - completed_before_today,
    )
    today_target = (
        math.ceil(
            remaining_at_start_today / days_left
        )
        if remaining_at_start_today
        else 0
    )
    remaining_today = max(
        0,
        today_target - daily_completed,
    )

    weekly_goal_complete = (
        weekly_target > 0
        and weekly_completed >= weekly_target
    )
    daily_goal_complete = (
        weekly_target > 0
        and today_target > 0
        and daily_completed >= today_target
    )

    elapsed_before_today = max(
        0,
        date.today().weekday(),
    )
    expected_before_today = math.floor(
        weekly_target
        * elapsed_before_today
        / 7
    )
    behind = max(
        0,
        expected_before_today
        - completed_before_today,
    )

    if weekly_target <= 0:
        pace_status = "Paused for certificate focus"
    elif weekly_goal_complete:
        pace_status = "Weekly goal complete"
    elif daily_goal_complete:
        pace_status = "Daily goal complete"
    elif behind:
        pace_status = f"Catch up by {behind}"
    else:
        pace_status = "On pace"

    return {
        "role": role,
        "weekly_target": weekly_target,
        "weekly_completed": weekly_completed,
        "remaining_this_week": remaining,
        "today_target": today_target,
        "today_completed": daily_completed,
        "remaining_today": remaining_today,
        "daily_goal_complete": daily_goal_complete,
        "weekly_goal_complete": weekly_goal_complete,
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
    priority=None,
    energy=None,
    destination=None,
    category=None,
):
    config = TRACK_CONFIG[
        track_key
    ]
    effective_priority = (
        config["priority"]
        if priority is None
        else int(priority)
    )
    effective_energy = (
        "Normal"
        if energy is None
        else str(energy)
    )
    effective_destination = (
        config["destination"]
        if destination is None
        else int(destination)
    )
    effective_category = (
        config["category"]
        if category is None
        else str(category)
    )

    active = _active_link(
        conn,
        track_key,
    )

    if (
        active
        and active["target_key"]
        == target_key
    ):
        task_id = int(
            active["task_id"]
        )
        row_changed = (
            int(active["week"])
            != int(week)
            or active["label"] != label
        )

        if row_changed:
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

        # A target with the same target_key is the same assignment even when
        # it carries into a new week. Preserve user status, duration, energy,
        # priority, and deferral while refreshing system-owned fields.
        conn.execute(
            """UPDATE task_metadata
               SET status=CASE
                       WHEN status='Completed'
                       THEN 'In Progress'
                       ELSE status
                   END,
                   destination=?,
                   category=?,
                   prerequisite_state=CASE
                       WHEN status='Blocked'
                       THEN prerequisite_state
                       ELSE 'Ready'
                   END,
                   prerequisite_reason=CASE
                       WHEN status='Blocked'
                       THEN prerequisite_reason
                       ELSE NULL
                   END
               WHERE task_id=?""",
            (
                effective_destination,
                effective_category,
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
        task_id = int(
            cursor.lastrowid
        )
    else:
        task_id = int(task_id)
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
           (
               task_id,status,priority,
               estimated_minutes,energy,
               destination,category,
               prerequisite_state,
               prerequisite_reason
           )
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
            effective_priority,
            int(estimate),
            effective_energy,
            effective_destination,
            effective_category,
            "Ready",
            None,
        ),
    )

    conn.execute(
        """INSERT INTO track_tasks
           (
               track_key,task_id,target_key,
               source_label,linked_entity_id,
               updated_at
           )
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
    course, module = normalize_google_position(
        state["google_course"],
        state["google_module"],
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

    course_name, chapter, estimate = (
        DATACAMP_TRACK[position]
    )
    metadata = {
        "course": course_name,
        "lesson": chapter,
        "chapter": chapter,
        "curriculum_position": position + 1,
        "estimated_minutes": estimate,
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
            f"Complete DataCamp: {course_name} — "
            f"{chapter}"
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


def _append_evidence(evidence, skill_key, source):
    bucket = evidence.setdefault(skill_key, [])
    if source not in bucket:
        bucket.append(source)


def _completed_duckdb_exercises(conn):
    numbers = set()

    rows = conn.execute(
        """SELECT s.label
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.completed=1
              OR m.status='Completed'"""
    ).fetchall()
    for row in rows:
        number = exercise_number_for_label(
            row["label"]
        )
        if number is not None:
            numbers.add(number)

    progress_rows = conn.execute(
        """SELECT exercise_number
           FROM duckdb_exercise_progress
           WHERE status='Completed'"""
    ).fetchall()
    numbers.update(
        int(row["exercise_number"])
        for row in progress_rows
    )

    return numbers


def _completed_applied_exercises(conn):
    numbers = set()
    rows = conn.execute(
        """SELECT s.label FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=1 OR m.status='Completed'"""
    ).fetchall()
    for row in rows:
        number = applied_exercise_number_for_label(row["label"])
        if number is not None:
            numbers.add(number)
    progress_rows = conn.execute(
        "SELECT exercise_number FROM applied_exercise_progress WHERE status='Completed'"
    ).fetchall()
    numbers.update(int(row["exercise_number"]) for row in progress_rows)
    return numbers


def completed_applied_numbers(conn):
    """Return all labs completed through either tasks or the lab workspace."""
    return sorted(
        _completed_applied_exercises(
            conn
        )
    )


def _skill_evidence(conn, state):
    course = int(state["google_course"])
    datacamp = _state_row(conn, "datacamp")
    data_position = int(datacamp["position"]) if datacamp else 0
    evidence = {}

    google_thresholds = {
        "analytics_foundations": 1,
        "business_framing": 2,
        "data_preparation": 3,
        "data_cleaning": 4,
        "analysis_foundations": 5,
        "visualization_foundations": 6,
        "data_storytelling": 6,
        "portfolio_delivery": 8,
        "career_readiness": 9,
    }
    for skill_key, completed_course in google_thresholds.items():
        if course > completed_course:
            _append_evidence(
                evidence,
                skill_key,
                f"Completed Google Course {completed_course}",
            )

    if course > 5:
        source = "Completed Google Course 5 analysis and SQL work"
        for skill_key in {
            "sql_fundamentals", "sql_querying", "sql_aggregation"
        }:
            _append_evidence(evidence, skill_key, source)

    for skill_key, threshold in DATACAMP_SKILL_THRESHOLDS.items():
        if data_position >= threshold:
            course_name, chapter, _ = DATACAMP_TRACK[threshold - 1]
            _append_evidence(
                evidence,
                skill_key,
                f"DataCamp: {course_name} — {chapter}",
            )

    for number in sorted(_completed_duckdb_exercises(conn)):
        exercise = DUCKDB_EXERCISES[number]
        source = f"DuckDB Exercise {number:02d}: {exercise['title']}"
        for skill_key in DUCKDB_SKILL_EVIDENCE.get(number, set()):
            _append_evidence(evidence, skill_key, source)

    for number in sorted(_completed_applied_exercises(conn)):
        item = APPLIED_EXERCISES[number]
        source = f"Applied Lab {number:02d}: {item['title']}"
        for skill_key in APPLIED_SKILL_EVIDENCE.get(number, set()):
            _append_evidence(evidence, skill_key, source)

    for title in sorted(_completed_sql(conn)):
        item = _sql_item(title)
        if item is None:
            continue
        source = f"Completed SQL problem: {title}"
        for skill_key in _sql_requirements(title, item[2]):
            if skill_key in SQL_SKILL_ACCEPTED_EVIDENCE:
                _append_evidence(evidence, skill_key, source)

    changed = True
    while changed:
        changed = False
        for advanced_skill, implied_skills in SQL_SKILL_HIERARCHY.items():
            sources = evidence.get(advanced_skill, [])
            if not sources:
                continue
            for implied_skill in implied_skills:
                before = len(evidence.get(implied_skill, []))
                for source in sources:
                    _append_evidence(evidence, implied_skill, source)
                if len(evidence.get(implied_skill, [])) > before:
                    changed = True

    return evidence


def _derived_skills(conn, state):
    return set(_skill_evidence(conn, state))

def _evidence_source_track(evidence_items, skill_key):
    sources = set()
    for item in evidence_items:
        if item.startswith("Completed Google"):
            sources.add("google")
        elif item.startswith("DataCamp:"):
            sources.add("datacamp")
        elif item.startswith("DuckDB"):
            sources.add("duckdb")
        elif item.startswith("Completed SQL"):
            sources.add("sql")

    if len(sources) > 1:
        return "multiple"
    if sources:
        return next(iter(sources))
    if skill_key in {
        "analytics_foundations", "business_framing", "data_preparation",
        "data_cleaning", "analysis_foundations", "visualization_foundations",
        "data_storytelling", "portfolio_delivery", "career_readiness",
    }:
        return "google"
    return "concept_evidence"


def _sync_skill_state(conn, state):
    evidence_map = _skill_evidence(conn, state)
    unlocked = set(evidence_map)

    for skill_key, (display_name, default_evidence) in SKILL_DEFINITIONS.items():
        evidence_items = evidence_map.get(skill_key, [])
        status = "Unlocked" if evidence_items else "Locked"
        evidence_text = (
            " • ".join(evidence_items)
            if evidence_items
            else SQL_SKILL_ACCEPTED_EVIDENCE.get(
                skill_key,
                default_evidence,
            )
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
                _evidence_source_track(evidence_items, skill_key),
                evidence_text,
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

        required = _sql_requirements(
            title,
            topic,
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


def _setting_value(
    conn,
    key,
    default,
):
    row = conn.execute(
        """SELECT value
           FROM settings
           WHERE key=?""",
        (key,),
    ).fetchone()
    return (
        row["value"]
        if row is not None
        else default
    )


def applied_branch_pin(conn):
    value = _setting_value(
        conn,
        "applied_branch_pin",
        "Auto",
    )
    return (
        value
        if value == "Auto"
        or value in APPLIED_BRANCHES
        else "Auto"
    )


def _applied_branch_for_number(
    number,
):
    number = int(number)
    for (
        branch,
        numbers,
    ) in APPLIED_BRANCHES.items():
        if number in numbers:
            return branch
    return None


def _applied_number_from_target_key(
    target_key,
):
    text = str(
        target_key or ""
    )
    if not text.startswith("lab:"):
        return None
    try:
        number = int(
            text.split(":", 1)[1]
        )
    except (TypeError, ValueError):
        return None
    return (
        number
        if number in APPLIED_EXERCISES
        else None
    )


def _applied_progress_status(
    conn,
    number,
):
    row = conn.execute(
        """SELECT status
           FROM applied_exercise_progress
           WHERE exercise_number=?""",
        (int(number),),
    ).fetchone()
    return (
        row["status"]
        if row is not None
        else "Not Started"
    )


def _has_dashboard_artifact(
    conn,
    completed,
):
    if 5 in completed:
        return True

    row = conn.execute(
        """SELECT 1
           FROM evidence
           WHERE LOWER(skill)
                     LIKE '%dashboard%'
              OR LOWER(skill)
                     LIKE '%report design%'
              OR LOWER(source_name)
                     LIKE '%dashboard%'
              OR LOWER(source_name)
                     LIKE '%power bi report%'
           LIMIT 1"""
    ).fetchone()
    return row is not None


def applied_lab_readiness(
    conn,
    state,
    number,
    unlocked=None,
):
    number = int(number)
    item = APPLIED_EXERCISES[
        number
    ]
    branch = _applied_branch_for_number(
        number
    )
    completed = (
        _completed_applied_exercises(
            conn
        )
    )

    if number in completed:
        return {
            "ready": True,
            "branch": branch,
            "missing": [],
            "missing_skills": [],
            "missing_labs": [],
            "roadmap_week": int(
                item["week"]
            ),
        }

    numbers = APPLIED_BRANCHES[
        branch
    ]
    position = numbers.index(
        number
    )
    missing_labs = [
        previous
        for previous in numbers[
            :position
        ]
        if previous not in completed
    ]

    if unlocked is None:
        unlocked = _derived_skills(
            conn,
            state,
        )
    unlocked = set(unlocked)

    required_skills = set(
        APPLIED_REQUIRED_SKILLS.get(
            number,
            set(),
        )
    )
    missing_skill_keys = sorted(
        required_skills - unlocked
    )
    missing = [
        (
            f"Complete Applied Lab "
            f"{lab_number:02d}: "
            f"{APPLIED_EXERCISES[lab_number]['title']}"
        )
        for lab_number in missing_labs
    ]
    missing.extend(
        SKILL_DEFINITIONS[
            skill_key
        ][0]
        for skill_key in missing_skill_keys
    )

    datacamp = _state_row(
        conn,
        "datacamp",
    )
    datacamp_position = (
        int(datacamp["position"])
        if datacamp is not None
        else 0
    )

    if (
        number == 1
        and "power_bi_foundations"
        not in unlocked
        and datacamp_position < 13
        and int(
            state["google_course"]
        ) < 6
    ):
        missing.append(
            (
                "Begin Power BI instruction "
                "or reach Google Course 6"
            )
        )

    if (
        number == 8
        and "python_pandas"
        not in unlocked
        and datacamp_position < 21
    ):
        missing.append(
            (
                "Begin the DataCamp Python "
                "or pandas curriculum"
            )
        )

    if (
        number == 13
        and not _has_dashboard_artifact(
            conn,
            completed,
        )
    ):
        missing.append(
            (
                "Complete a dashboard artifact "
                "(Applied Lab 05 or equivalent)"
            )
        )

    # Timed requests are deliberately cross-functional.
    if number == 19:
        if 12 not in completed and (
            "analyst_communication"
            not in unlocked
        ):
            missing.append(
                (
                    "Complete Applied Lab 12 "
                    "or equivalent communication evidence"
                )
            )
        if 15 not in completed and (
            "sql_validation"
            not in unlocked
        ):
            missing.append(
                (
                    "Complete Applied Lab 15 "
                    "or equivalent validation evidence"
                )
            )

    # Preserve order while removing duplicate reasons.
    missing = list(
        dict.fromkeys(missing)
    )

    return {
        "ready": not missing,
        "branch": branch,
        "missing": missing,
        "missing_skills": missing_skill_keys,
        "missing_labs": missing_labs,
        "roadmap_week": int(
            item["week"]
        ),
    }


def _applied_target_payload(
    *,
    number,
    pace,
    completed,
    pin,
    carryover=False,
):
    item = APPLIED_EXERCISES[
        int(number)
    ]
    branch = _applied_branch_for_number(
        number
    )

    metadata = {
        "lab_number": int(number),
        "title": item["title"],
        "branch": branch,
        "category": item["category"],
        "task_category": item[
            "task_category"
        ],
        "concepts": item["concepts"],
        "assigned_week": int(
            item["week"]
        ),
        "total_items": len(
            APPLIED_EXERCISES
        ),
        "completed_items": len(
            completed
        ),
        "pin": pin,
        "optional": bool(
            item.get(
                "optional",
                False,
            )
        ),
        "carryover": bool(
            carryover
        ),
        "alignment": (
            f"{branch} branch • "
            "supplemental applied practice"
        ),
    }
    metadata.update(pace)

    return {
        "target_key": (
            f"lab:{int(number)}"
        ),
        "label": item["label"],
        "source_label": (
            f"Applied Labs • {branch}"
        ),
        "estimate": int(
            item["minutes"]
        ),
        "position": len(completed),
        "subposition": int(number),
        "linked_entity_id": int(number),
        "priority": int(
            item["priority"]
        ),
        "energy": item["energy"],
        "destination": int(
            item["destination"]
        ),
        "category": item[
            "task_category"
        ],
        "metadata": metadata,
    }


def _applied_branch_rank(
    current_week,
    branch,
):
    order = (
        APPLIED_WEEK_BRANCH_PRIORITY.get(
            int(current_week),
            APPLIED_BRANCH_ORDER,
        )
    )
    try:
        return order.index(
            branch
        )
    except ValueError:
        return len(order) + (
            APPLIED_BRANCH_ORDER.index(
                branch
            )
            if branch
            in APPLIED_BRANCH_ORDER
            else 99
        )


def _applied_target(
    conn,
    state,
    pace,
    unlocked,
):
    completed = (
        _completed_applied_exercises(
            conn
        )
    )
    pin = applied_branch_pin(
        conn
    )
    current_week = max(
        1,
        int(state["current_week"]),
    )

    # Carry the exact unfinished assignment across week boundaries instead of
    # replacing it with a new branch merely because the calendar advanced.
    active = _active_link(
        conn,
        "applied",
    )
    if active is not None:
        active_number = (
            _applied_number_from_target_key(
                active["target_key"]
            )
        )
        if (
            active_number is not None
            and active_number
            not in completed
        ):
            active_branch = (
                _applied_branch_for_number(
                    active_number
                )
            )
            readiness = (
                applied_lab_readiness(
                    conn,
                    state,
                    active_number,
                    unlocked,
                )
            )
            if (
                readiness["ready"]
                and (
                    pin == "Auto"
                    or pin
                    == active_branch
                )
            ):
                return _applied_target_payload(
                    number=active_number,
                    pace=pace,
                    completed=completed,
                    pin=pin,
                    carryover=True,
                )

    candidates = []
    locked_candidates = []

    branches = (
        (pin,)
        if pin != "Auto"
        else APPLIED_BRANCH_ORDER
    )

    for branch in branches:
        numbers = APPLIED_BRANCHES[
            branch
        ]
        next_number = next(
            (
                number
                for number in numbers
                if number not in completed
            ),
            None,
        )
        if next_number is None:
            continue

        item = APPLIED_EXERCISES[
            next_number
        ]
        readiness = (
            applied_lab_readiness(
                conn,
                state,
                next_number,
                unlocked,
            )
        )

        scheduled = (
            int(item["week"])
            <= current_week
            or pin == branch
        )
        missing = list(
            readiness["missing"]
        )
        if not scheduled:
            missing.append(
                (
                    f"Scheduled for roadmap "
                    f"Week {item['week']}"
                )
            )

        candidate = {
            "number": next_number,
            "branch": branch,
            "item": item,
            "readiness": readiness,
            "missing": missing,
            "status": (
                _applied_progress_status(
                    conn,
                    next_number,
                )
            ),
        }

        if readiness["ready"] and scheduled:
            candidates.append(
                candidate
            )
        else:
            locked_candidates.append(
                candidate
            )

    if candidates:
        chosen = min(
            candidates,
            key=lambda candidate: (
                0
                if candidate["status"]
                == "In Progress"
                else 1,
                _applied_branch_rank(
                    current_week,
                    candidate[
                        "branch"
                    ],
                ),
                max(
                    0,
                    current_week
                    - int(
                        candidate[
                            "item"
                        ]["week"]
                    ),
                ),
                int(
                    candidate["number"]
                ),
            ),
        )
        return _applied_target_payload(
            number=chosen["number"],
            pace=pace,
            completed=completed,
            pin=pin,
        )

    if locked_candidates:
        blocked = min(
            locked_candidates,
            key=lambda candidate: (
                _applied_branch_rank(
                    current_week,
                    candidate[
                        "branch"
                    ],
                ),
                abs(
                    current_week
                    - int(
                        candidate[
                            "item"
                        ]["week"]
                    )
                ),
                int(
                    candidate["number"]
                ),
            ),
        )
        item = blocked["item"]
        metadata = {
            "lab_number": int(
                blocked["number"]
            ),
            "title": item["title"],
            "branch": blocked[
                "branch"
            ],
            "category": item[
                "category"
            ],
            "task_category": item[
                "task_category"
            ],
            "concepts": item[
                "concepts"
            ],
            "assigned_week": int(
                item["week"]
            ),
            "total_items": len(
                APPLIED_EXERCISES
            ),
            "completed_items": len(
                completed
            ),
            "pin": pin,
            "missing": blocked[
                "missing"
            ],
            "blocked_reason": (
                "Unlock next: "
                + "; ".join(
                    blocked["missing"]
                )
            ),
        }
        metadata.update(pace)
        return {
            "locked": True,
            "position": len(
                completed
            ),
            "subposition": int(
                blocked["number"]
            ),
            "metadata": metadata,
        }

    return None


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

        applied_number = (
            applied_exercise_number_for_label(
                label
            )
        )
        if applied_number is not None:
            readiness = applied_lab_readiness(
                conn,
                state,
                applied_number,
                unlocked,
            )
            reason = (
                (
                    "Unlock first: "
                    + "; ".join(
                        readiness["missing"]
                    )
                )
                if not readiness["ready"]
                else (
                    "Waiting for the Applied Labs "
                    "adaptive track to select this branch."
                )
            )

        google_match = re.match(
            r"^\[Google Course (\d+)\]",
            label,
            re.IGNORECASE,
        )
        managed_google = (
            google_match is not None
            or "google course" in lower
            or "google certificate" in lower
        )
        if (
            applied_number is None
            and managed_google
        ):
            reason = (
                "Managed by the independent "
                "Google Certificate track."
            )

        elif (
            applied_number is None
            and "datacamp" in lower
        ):
            reason = (
                "Managed by the independent "
                "DataCamp track."
            )

        elif (
            applied_number is None
            and row["category"] == "SQL"
        ):
            title = re.sub(
                r"^Solve\s+",
                "",
                label,
                flags=re.IGNORECASE,
            )
            item = sql_lookup.get(title)
            if item:
                required = (
                    _sql_requirements(
                        title,
                        item[2],
                    )
                )

        elif (
            applied_number is None
            and row["category"] == "Portfolio"
        ):
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

    # Earlier versions treated detached negative-sort adaptive tasks as
    # completed. Restore any such task that has no actual completion evidence.
    false_completion_rows = conn.execute(
        """SELECT s.id,s.label
           FROM sprint_tasks s
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.sort_order<0
             AND tt.task_id IS NULL
             AND s.completed=1"""
    ).fetchall()

    for row in false_completion_rows:
        if _has_completion_evidence(
            conn,
            task_id=int(row["id"]),
            label=row["label"],
        ):
            continue

        conn.execute(
            """UPDATE sprint_tasks
               SET completed=0
               WHERE id=?""",
            (int(row["id"]),),
        )
        conn.execute(
            """UPDATE task_metadata
               SET status='Blocked',
                   prerequisite_state='Blocked',
                   prerequisite_reason=?
               WHERE task_id=?""",
            (
                (
                    "Restored because no matching "
                    "completion record was found."
                ),
                int(row["id"]),
            ),
        )

    # Detached adaptive tasks remain unfinished and blocked until sync_all()
    # either reuses them for the exact target or leaves them in the backlog.
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
            """UPDATE task_metadata
               SET status='Blocked',
                   prerequisite_state='Blocked',
                   prerequisite_reason=COALESCE(
                       prerequisite_reason,
                       'Adaptive task is not currently eligible.'
                   )
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

    focus_duplicates = conn.execute(
        """SELECT COUNT(*)
           FROM (
               SELECT
                   CASE
                       WHEN COALESCE(f.is_extra,0)=1
                            AND COALESCE(
                                f.track_key,
                                tt.track_key
                            ) IS NOT NULL
                           THEN
                               'extra:'
                               || COALESCE(
                                   f.track_key,
                                   tt.track_key
                               )
                               || ':'
                               || COALESCE(
                                   f.target_key,
                                   f.source_key
                               )
                       WHEN COALESCE(
                                f.track_key,
                                tt.track_key
                            ) IS NOT NULL
                           THEN
                               'track:'
                               || COALESCE(
                                   f.track_key,
                                   tt.track_key
                               )
                       WHEN f.source_key LIKE 'roadmap:%'
                           THEN 'track:' || SUBSTR(f.source_key,10)
                       ELSE f.source_key
                   END AS logical_key
               FROM daily_focus f
               LEFT JOIN track_tasks tt
                 ON tt.task_id=f.task_id
               WHERE f.focus_date=?
               GROUP BY logical_key
               HAVING COUNT(*)>1
           )""",
        (date.today().isoformat(),),
    ).fetchone()[0]
    if focus_duplicates:
        issues.append(
            "duplicate logical items in today's focus"
        )

    external_workspace_count = conn.execute(
        """SELECT COUNT(*)
           FROM task_workspaces
           WHERE LOWER(COALESCE(track_key,''))
                     IN ('google','datacamp')
              OR LOWER(task_label) LIKE '%datacamp%'
              OR LOWER(task_label) LIKE '%google course%'
              OR LOWER(task_label) LIKE '%google certificate%'"""
    ).fetchone()[0]
    if external_workspace_count:
        issues.append(
            "external learning tasks stored as workspaces"
        )

    duplicate_achievements = (
        achievement_service.duplicate_activity_groups(
            conn
        )
    )
    if duplicate_achievements:
        issues.append(
            (
                f"{len(duplicate_achievements)} duplicate "
                "achievement accomplishment group(s)"
            )
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
        "applied": (
            len(
                _completed_applied_exercises(
                    conn
                )
            ),
            0,
        ),
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
    state = normalize_google_checkpoint(conn, state)
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
    daily = {
        track_key: _daily_completed(
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
            daily_completed=daily[
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
        "applied": _applied_target(
            conn,
            state,
            pace["applied"],
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

        track_status = "Active"
        if pace[track_key][
            "weekly_goal_complete"
        ]:
            track_status = "Weekly Complete"
        elif pace[track_key][
            "daily_goal_complete"
        ]:
            track_status = "Daily Complete"

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
            status=track_status,
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
            priority=target.get(
                "priority"
            ),
            energy=target.get(
                "energy"
            ),
            destination=target.get(
                "destination"
            ),
            category=target.get(
                "category"
            ),
        )

    _sync_sprint_prerequisites(
        conn,
        state,
        unlocked,
    )
    conn.commit()


def _sql_title_from_task_label(label):
    text = str(label or "").strip()
    prefix = "Solve "
    if text.startswith(prefix):
        title = text[len(prefix):].strip()
        return title if _sql_item(title) else None
    return None


def active_sql_task_for_title(
    conn,
    title,
):
    """Return the active SQL task only when its exact target key matches."""
    return conn.execute(
        """SELECT tt.*,s.label,s.completed
           FROM track_tasks tt
           JOIN sprint_tasks s
             ON s.id=tt.task_id
           WHERE tt.track_key='sql'
             AND tt.target_key=?
             AND s.label=?
             AND s.completed=0""",
        (
            f"problem:{title}",
            f"Solve {title}",
        ),
    ).fetchone()


def _event_metadata(row):
    if row is None:
        return {}
    try:
        return json.loads(
            row["metadata"]
            or "{}"
        )
    except (TypeError, ValueError):
        return {}


def _completion_event_for_task(
    conn,
    *,
    task_id,
    label,
):
    rows = conn.execute(
        """SELECT *
           FROM track_events
           ORDER BY id DESC"""
    ).fetchall()

    sql_title = _sql_title_from_task_label(
        label
    )
    sql_event_key = (
        f"problem:{sql_title}"
        if sql_title
        else None
    )

    for row in rows:
        metadata = _event_metadata(row)
        if int(
            metadata.get(
                "task_id",
                -1,
            )
        ) == int(task_id):
            return row

        if (
            sql_event_key
            and row["track_key"] == "sql"
            and row["event_key"]
            == sql_event_key
        ):
            return row

        if row["item_label"] == label:
            return row

    return None


def _has_completion_evidence(
    conn,
    *,
    task_id,
    label,
):
    event = _completion_event_for_task(
        conn,
        task_id=task_id,
        label=label,
    )
    if event is not None:
        return True

    sql_title = _sql_title_from_task_label(
        label
    )
    if sql_title:
        row = conn.execute(
            """SELECT 1
               FROM sql_practice
               WHERE platform='DataLemur'
                 AND title=?
                 AND status='Completed'""",
            (sql_title,),
        ).fetchone()
        return row is not None

    return False


def task_has_completion_evidence(
    conn,
    task_id,
):
    """Return True when any completion layer still marks this task complete."""
    row = conn.execute(
        """SELECT
               s.completed,
               s.label,
               m.status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.id=?""",
        (int(task_id),),
    ).fetchone()
    if row is None:
        return False

    if bool(row["completed"]):
        return True
    if row["status"] == "Completed":
        return True

    return _has_completion_evidence(
        conn,
        task_id=int(task_id),
        label=row["label"],
    )


def completion_history(conn):
    """Return completed roadmap tasks and SQL-only completions."""
    history = []
    seen_sql = set()

    task_rows = conn.execute(
        """SELECT
               s.id,
               s.week,
               s.sort_order,
               s.label,
               m.category,
               m.status
           FROM sprint_tasks s
           JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.completed=1
              OR m.status='Completed'
           ORDER BY s.week DESC,
                    s.sort_order DESC,
                    s.id DESC"""
    ).fetchall()

    for row in task_rows:
        task_id = int(row["id"])
        label = row["label"]
        event = _completion_event_for_task(
            conn,
            task_id=task_id,
            label=label,
        )
        event_track = (
            event["track_key"]
            if event is not None
            else None
        )
        completed_date = (
            event["completed_date"]
            if event is not None
            else None
        )

        sql_title = _sql_title_from_task_label(
            label
        )
        if sql_title:
            sql_row = conn.execute(
                """SELECT completed_date
                   FROM sql_practice
                   WHERE platform='DataLemur'
                     AND title=?
                     AND status='Completed'""",
                (sql_title,),
            ).fetchone()
            if sql_row is not None:
                seen_sql.add(sql_title)
                completed_date = (
                    completed_date
                    or sql_row["completed_date"]
                )

        history.append(
            {
                "kind": "task",
                "task_id": task_id,
                "week": int(row["week"]),
                "label": label,
                "category": (
                    row["category"]
                    or "General"
                ),
                "track_key": event_track,
                "completed_date": completed_date,
                "sql_title": sql_title,
            }
        )

    sql_rows = conn.execute(
        """SELECT title,completed_date
           FROM sql_practice
           WHERE platform='DataLemur'
             AND status='Completed'
           ORDER BY completed_date DESC,
                    title"""
    ).fetchall()

    for row in sql_rows:
        if row["title"] in seen_sql:
            continue
        history.append(
            {
                "kind": "sql",
                "task_id": None,
                "week": None,
                "label": (
                    f"SQL Companion: "
                    f"{row['title']}"
                ),
                "category": "SQL",
                "track_key": "sql",
                "completed_date": (
                    row["completed_date"]
                ),
                "sql_title": row["title"],
            }
        )

    return sorted(
        history,
        key=lambda item: (
            item.get("completed_date")
            or "",
            int(item.get("week") or 0),
            item["label"],
        ),
        reverse=True,
    )


def _latest_track_event_id(
    conn,
    track_key,
):
    row = conn.execute(
        """SELECT id
           FROM track_events
           WHERE track_key=?
           ORDER BY id DESC
           LIMIT 1""",
        (track_key,),
    ).fetchone()
    return (
        int(row["id"])
        if row is not None
        else None
    )


def undo_completion(
    conn,
    state,
    *,
    task_id=None,
    sql_title=None,
):
    """Undo one exact completion and reverse its adaptive evidence."""
    task_row = None
    event = None

    if task_id is not None:
        task_row = conn.execute(
            """SELECT
                   s.id,
                   s.week,
                   s.label,
                   s.completed,
                   m.status,
                   m.category
               FROM sprint_tasks s
               JOIN task_metadata m
                 ON m.task_id=s.id
               WHERE s.id=?""",
            (int(task_id),),
        ).fetchone()
        if task_row is None:
            raise ValueError(
                "The selected task no longer exists."
            )

        event = _completion_event_for_task(
            conn,
            task_id=int(task_id),
            label=task_row["label"],
        )
        sql_title = (
            sql_title
            or _sql_title_from_task_label(
                task_row["label"]
            )
        )

    if (
        task_row is None
        and not sql_title
    ):
        raise ValueError(
            "Select a completed task or SQL problem."
        )

    track_key = (
        event["track_key"]
        if event is not None
        else (
            "sql"
            if sql_title
            else None
        )
    )

    applied_number_for_undo = (
        applied_exercise_number_for_label(
            task_row["label"]
        )
        if task_row is not None
        else (
            int(
                _event_metadata(
                    event
                ).get(
                    "lab_number"
                )
            )
            if (
                event is not None
                and _event_metadata(
                    event
                ).get(
                    "lab_number"
                )
                is not None
            )
            else None
        )
    )

    if (
        applied_number_for_undo
        is not None
    ):
        branch = _applied_branch_for_number(
            applied_number_for_undo
        )
        numbers = APPLIED_BRANCHES[
            branch
        ]
        position = numbers.index(
            applied_number_for_undo
        )
        completed_applied = (
            _completed_applied_exercises(
                conn
            )
        )
        later_completed = [
            number
            for number in numbers[
                position + 1:
            ]
            if number
            in completed_applied
        ]
        if later_completed:
            latest = later_completed[-1]
            raise ValueError(
                (
                    f"Undo Applied Lab "
                    f"{latest:02d} first. "
                    f"The {branch} branch must "
                    "remain sequential."
                )
            )

    if (
        event is not None
        and track_key
        in {
            "google",
            "datacamp",
            "portfolio",
        }
    ):
        latest_id = _latest_track_event_id(
            conn,
            track_key,
        )
        if latest_id != int(event["id"]):
            display_name = TRACK_CONFIG[
                track_key
            ]["display_name"]
            raise ValueError(
                f"Only the most recent {display_name} "
                "completion can be undone. Undo later "
                "items first so the sequence remains valid."
            )

    if task_row is not None:
        conn.execute(
            """UPDATE sprint_tasks
               SET completed=0
               WHERE id=?""",
            (int(task_id),),
        )
        conn.execute(
            """UPDATE task_metadata
               SET status='Not Started',
                   deferred_until=NULL,
                   prerequisite_state='Ready',
                   prerequisite_reason=NULL
               WHERE task_id=?""",
            (int(task_id),),
        )

    metadata = _event_metadata(event)

    if track_key == "google":
        course = int(
            metadata.get(
                "course",
                state["google_course"],
            )
        )
        module = int(
            metadata.get(
                "module",
                max(
                    1,
                    int(
                        state[
                            "google_module"
                        ]
                    )
                    - 1,
                ),
            )
        )
        conn.execute(
            """UPDATE program_state
               SET google_course=?,
                   google_module=?
               WHERE id=1""",
            (
                course,
                module,
            ),
        )

    elif track_key == "datacamp":
        position = int(
            metadata.get(
                "position",
                0,
            )
        )
        conn.execute(
            """UPDATE track_state
               SET position=?,
                   subposition=0,
                   status='Active',
                   metadata='{}',
                   updated_at=CURRENT_TIMESTAMP
               WHERE track_key='datacamp'""",
            (position,),
        )

    elif track_key == "portfolio":
        project_task_id = metadata.get(
            "project_task_id"
        )
        if project_task_id is not None:
            conn.execute(
                """UPDATE project_tasks
                   SET completed=0
                   WHERE id=?""",
                (int(project_task_id),),
            )

    if sql_title:
        conn.execute(
            """UPDATE sql_practice
               SET status='Not Started',
                   completed_date=NULL
               WHERE platform='DataLemur'
                 AND title=?""",
            (sql_title,),
        )

        conn.execute(
            """DELETE FROM evidence
               WHERE source_type='Interview Problem'
                 AND source_name=?""",
            (f"Interview Problem: {sql_title}",),
        )

    applied_number = (
        applied_number_for_undo
    )
    if applied_number is not None:
        item = APPLIED_EXERCISES[applied_number]
        conn.execute(
            """UPDATE applied_exercise_progress
               SET status='Not Started',completed_date=NULL,updated_at=CURRENT_TIMESTAMP
               WHERE exercise_number=?""",
            (applied_number,),
        )
        conn.execute(
            "DELETE FROM evidence WHERE source_name=?",
            (f"Applied Lab {applied_number:02d}: {item['title']}",),
        )

    duckdb_number = (
        exercise_number_for_label(
            task_row["label"]
        )
        if task_row is not None
        else None
    )
    if duckdb_number is not None:
        item = DUCKDB_EXERCISES[
            duckdb_number
        ]
        conn.execute(
            """UPDATE duckdb_exercise_progress
               SET status='Not Started',
                   completed_date=NULL,
                   updated_at=CURRENT_TIMESTAMP
               WHERE exercise_number=?""",
            (duckdb_number,),
        )
        conn.execute(
            """DELETE FROM evidence
               WHERE source_type='SQL Practice'
                 AND source_name=?""",
            (
                f"DuckDB Exercise "
                f"{duckdb_number:02d}: "
                f"{item['title']}",
            ),
        )

    if event is not None:
        conn.execute(
            """DELETE FROM track_events
               WHERE id=?""",
            (int(event["id"]),),
        )

    if track_key:
        conn.execute(
            """DELETE FROM track_tasks
               WHERE track_key=?""",
            (track_key,),
        )

    conn.commit()

    label = (
        task_row["label"]
        if task_row is not None
        else f"SQL Companion: {sql_title}"
    )
    return {
        "message": (
            f"Completion restored to unfinished: "
            f"{label}"
        ),
        "track_key": track_key,
        "task_id": (
            int(task_id)
            if task_id is not None
            else None
        ),
        "sql_title": sql_title,
    }


def task_edit_identity(
    conn,
    task_id,
):
    """Capture stable task identity, including completed adaptive tasks."""
    row = conn.execute(
        """SELECT
               s.id,
               s.label,
               tt.track_key,
               tt.target_key
           FROM sprint_tasks s
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           WHERE s.id=?""",
        (int(task_id),),
    ).fetchone()

    if row is None:
        return None

    track_key = row["track_key"]
    target_key = row["target_key"]

    # Completed adaptive tasks normally have no active track_tasks row. Recover
    # their exact identity from the completion event before undoing it.
    if not track_key or not target_key:
        event = _completion_event_for_task(
            conn,
            task_id=int(row["id"]),
            label=row["label"],
        )
        if event is not None:
            track_key = event["track_key"]
            target_key = event["event_key"]

    # Older SQL rows may have a sql_practice completion but no event metadata.
    if not track_key or not target_key:
        sql_title = _sql_title_from_task_label(
            row["label"]
        )
        if sql_title:
            sql_row = conn.execute(
                """SELECT 1
                   FROM sql_practice
                   WHERE platform='DataLemur'
                     AND title=?
                     AND status='Completed'""",
                (sql_title,),
            ).fetchone()
            if sql_row is not None:
                track_key = "sql"
                target_key = (
                    f"problem:{sql_title}"
                )

    return {
        "task_id": int(row["id"]),
        "label": row["label"],
        "track_key": track_key,
        "target_key": target_key,
    }


def resolve_task_edit_target(
    conn,
    identity,
):
    """Resolve the task row representing the same assignment after sync."""
    if not identity:
        return None

    track_key = identity.get(
        "track_key"
    )
    target_key = identity.get(
        "target_key"
    )

    if track_key and target_key:
        row = conn.execute(
            """SELECT task_id
               FROM track_tasks
               WHERE track_key=?
                 AND target_key=?""",
            (
                track_key,
                target_key,
            ),
        ).fetchone()
        if row is not None:
            return int(row["task_id"])

    original_id = int(
        identity["task_id"]
    )
    exists = conn.execute(
        """SELECT 1
           FROM sprint_tasks
           WHERE id=?""",
        (original_id,),
    ).fetchone()
    return (
        original_id
        if exists is not None
        else None
    )


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


def _clean_focus_text(value):
    return str(value or "").strip().rstrip(".").strip()


def _course_number_from_alignment(alignment):
    match = re.search(
        r"\bCourse\s+(\d+)\b",
        str(alignment or ""),
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _looks_like_sql_fundamentals(label):
    lower_label = str(label or "").lower()
    sql_markers = (
        "select",
        " from ",
        "where",
        "order by",
        "group by",
        "having",
        "join",
        "subquery",
        "cte",
        "window function",
        "sql",
    )
    return (
        lower_label.startswith("practice ")
        and any(
            marker in f" {lower_label} "
            for marker in sql_markers
        )
    )


def task_detail(conn, task_id):
    """Return action-first pacing text for an adaptive track task."""
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
    today_completed = int(
        metadata.get(
            "today_completed",
            0,
        )
    )
    pace_status = _clean_focus_text(
        metadata.get(
            "pace_status",
            "On pace",
        )
    )
    track_key = link["track_key"]
    alignment = metadata.get(
        "alignment",
        "",
    )
    aligned_course = _course_number_from_alignment(
        alignment
    )

    if track_key == "google":
        specific_work = (
            f"Course {metadata.get('course', '?')}, "
            f"Module {metadata.get('module', '?')}"
        )
        context = pace_status
    elif track_key == "datacamp":
        data_course = metadata.get(
            "course",
            "DataCamp",
        )
        data_chapter = metadata.get(
            "chapter",
            metadata.get(
                "lesson",
                "Continue the current chapter",
            ),
        )
        specific_work = (
            f"{data_course} — {data_chapter}"
        )
        context = (
            f"Supports Course {aligned_course}"
            if aligned_course
            else "Supports certificate progress"
        )
    elif track_key == "sql":
        specific_work = metadata.get(
            "title",
            "Complete the current SQL problem",
        )
        context = (
            f"Reinforces Course {aligned_course}"
            if aligned_course
            else "Reinforces current SQL skills"
        )
    elif track_key == "applied":
        number = metadata.get(
            "lab_number",
            "?",
        )
        specific_work = (
            f"Lab {number}: "
            f"{metadata.get('title', 'Applied practice')}"
        )
        context = (
            f"{metadata.get('branch', 'Applied')} • "
            f"{pace_status}"
        )
    elif track_key == "portfolio":
        specific_work = metadata.get(
            "milestone",
            "Advance the current portfolio milestone",
        )
        context = (
            f"Applies Course {aligned_course}"
            if aligned_course
            else "Prerequisite skills ready"
        )
    else:
        task_row = conn.execute(
            """SELECT label
               FROM sprint_tasks
               WHERE id=?""",
            (task_id,),
        ).fetchone()
        specific_work = (
            task_row["label"]
            if task_row is not None
            else "Continue the current task"
        )
        context = pace_status

    return (
        f"{_clean_focus_text(specific_work)} • "
        f"Today {today_completed}/{today} • "
        f"Week {completed}/{target} • "
        f"{_clean_focus_text(context)}"
    )


def focus_presentation(conn, item):
    """Build one uniform Today’s Focus title and detail."""
    category = str(
        item.get("category")
        or "General"
    )
    label = _clean_focus_text(
        item.get("label")
    )
    task_id = item.get("task_id")

    if item.get("roadmap_fallback"):
        title = item.get(
            "display_title",
            {
                "Learning": "Learning",
                "SQL": "SQL Practice",
                "Portfolio": "Portfolio Project",
                "Review": "Weekly Review",
                "General": "Roadmap Task",
            }.get(
                category,
                "Roadmap Task",
            ),
        )
        action = _clean_focus_text(
            item.get(
                "detail",
                label,
            )
        )
        return {
            "style_category": category,
            "title": title,
            "detail": (
                f"{action} • Weekly roadmap"
            ),
        }

    link = (
        task_track(conn, int(task_id))
        if task_id is not None
        else None
    )
    if link is not None:
        track_key = link["track_key"]
        style_category = TRACK_CONFIG[
            track_key
        ]["category"]
        if track_key == "applied":
            state_row = _state_row(
                conn,
                "applied",
            )
            try:
                applied_meta = json.loads(
                    state_row["metadata"]
                    or "{}"
                )
            except (
                TypeError,
                ValueError,
            ):
                applied_meta = {}
            style_category = applied_meta.get(
                "task_category",
                style_category,
            )

        return {
            "style_category": style_category,
            "title": TRACK_CONFIG[
                track_key
            ]["display_name"],
            "detail": task_detail(
                conn,
                int(task_id),
            ),
        }

    display_category = category
    duckdb_exercise = exercise_for_label(label)
    if duckdb_exercise is not None:
        display_category = "SQL"
        title = "DuckDB Practice"
    elif (
        category == "General"
        and _looks_like_sql_fundamentals(label)
    ):
        display_category = "SQL"
        title = "SQL Fundamentals"
    elif category == "Learning":
        lower_label = label.lower()
        if "datacamp" in lower_label:
            title = "DataCamp"
        elif any(
            token in lower_label
            for token in (
                "google",
                "course",
                "module",
            )
        ):
            title = "Google Certificate"
        else:
            title = "Learning"
    else:
        title = {
            "SQL": "SQL Practice",
            "Portfolio": "Portfolio Project",
            "Review": "Weekly Review",
            "General": "Roadmap Task",
        }.get(
            category,
            "Roadmap Task",
        )

    metadata = []
    if item.get("carryover"):
        metadata.append(
            item.get("carryover_note")
            or "Missed yesterday"
        )
    elif str(
        item.get("status")
        or ""
    ) == "In Progress":
        metadata.append("In progress")

    metadata.append(
        f"Priority {int(item.get('priority') or 3)}"
    )

    return {
        "style_category": display_category,
        "title": title,
        "detail": " • ".join(
            [label, *metadata]
        ),
    }


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
                "task_id": int(task_id),
            },
        )
        next_course, next_module = next_google_position(
            course,
            module,
        )
        conn.execute(
            """UPDATE program_state
               SET google_course=?,google_module=?
               WHERE id=1""",
            (next_course, next_module),
        )
        if (next_course, next_module) == (course, module):
            message = "Google certificate progress is complete."
        else:
            message = (
                f"Google progress advanced to "
                f"Course {next_course}, "
                f"Module {next_module}."
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
                "task_id": int(task_id),
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
                "task_id": int(task_id),
            },
        )
        message = (
            f"SQL completed: {title}"
        )

    elif track_key == "applied":
        number = (
            _applied_number_from_target_key(
                link["target_key"]
            )
        )
        if number is None:
            raise ValueError(
                "The active Applied Lab could not be identified."
            )

        item = APPLIED_EXERCISES[
            number
        ]
        progress_row = conn.execute(
            """SELECT submission_path,notes
               FROM applied_exercise_progress
               WHERE exercise_number=?""",
            (number,),
        ).fetchone()
        submission_path = (
            progress_row[
                "submission_path"
            ]
            if progress_row is not None
            else None
        )
        notes = (
            progress_row["notes"]
            if progress_row is not None
            else ""
        )

        conn.execute(
            """INSERT INTO applied_exercise_progress
               (
                   exercise_number,status,
                   submission_path,notes,
                   completed_date,updated_at
               )
               VALUES(
                   ?,'Completed',?,?,?,
                   CURRENT_TIMESTAMP
               )
               ON CONFLICT(exercise_number)
               DO UPDATE SET
                   status='Completed',
                   submission_path=COALESCE(
                       excluded.submission_path,
                       applied_exercise_progress.submission_path
                   ),
                   notes=COALESCE(
                       excluded.notes,
                       applied_exercise_progress.notes
                   ),
                   completed_date=excluded.completed_date,
                   updated_at=CURRENT_TIMESTAMP""",
            (
                number,
                submission_path,
                notes,
                date.today().isoformat(),
            ),
        )

        source_name = (
            f"Applied Lab {number:02d}: "
            f"{item['title']}"
        )
        description = (
            f"Completed a guided "
            f"{item['category']} lab "
            f"demonstrating "
            f"{item['concepts']}."
        )
        if submission_path:
            description += (
                " Submission: "
                + submission_path
            )

        conn.execute(
            """INSERT INTO evidence
               (
                   skill,source_type,
                   source_name,description
               )
               VALUES(?,?,?,?)
               ON CONFLICT(
                   skill,source_type,source_name
               )
               DO UPDATE SET
                   description=excluded.description""",
            (
                item[
                    "evidence_skill"
                ],
                item[
                    "source_type"
                ],
                source_name,
                description,
            ),
        )

        branch = (
            _applied_branch_for_number(
                number
            )
        )
        _record_event(
            conn,
            "applied",
            f"lab:{number}",
            item["title"],
            metadata={
                "lab_number": number,
                "branch": branch,
                "task_id": int(
                    task_id
                ),
            },
        )
        message = (
            f"Applied Lab {number:02d} "
            f"completed: {item['title']}"
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
                    "task_id": int(task_id),
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


def active_applied_task_for_number(
    conn,
    number,
):
    row = conn.execute(
        """SELECT
               tt.task_id,
               tt.target_key
           FROM track_tasks tt
           WHERE tt.track_key='applied'"""
    ).fetchone()
    if row is None:
        return None

    active_number = (
        _applied_number_from_target_key(
            row["target_key"]
        )
    )
    return (
        row
        if active_number
        == int(number)
        else None
    )


def record_applied_change(
    conn,
    *,
    number,
    completed,
    task_id=None,
):
    number = int(number)
    item = APPLIED_EXERCISES[
        number
    ]
    event_key = (
        f"lab:{number}"
    )

    if completed:
        _record_event(
            conn,
            "applied",
            event_key,
            item["title"],
            metadata={
                "lab_number": number,
                "branch": (
                    _applied_branch_for_number(
                        number
                    )
                ),
                "task_id": (
                    int(task_id)
                    if task_id is not None
                    else None
                ),
            },
        )
    else:
        conn.execute(
            """DELETE FROM track_events
               WHERE track_key='applied'
                 AND event_key=?""",
            (event_key,),
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


def _skill_in_progress_sources(conn, state):
    sources = {}
    course = int(state["google_course"])

    google_current = {
        1: {"analytics_foundations"},
        2: {"business_framing"},
        3: {"data_preparation"},
        4: {"data_cleaning"},
        5: {
            "analysis_foundations", "sql_fundamentals",
            "sql_querying", "sql_aggregation"
        },
        6: {"visualization_foundations", "data_storytelling"},
        8: {"portfolio_delivery"},
        9: {"career_readiness"},
    }
    for skill_key in google_current.get(course, set()):
        _append_evidence(
            sources,
            skill_key,
            f"Google Course {course} in progress",
        )

    datacamp = _state_row(conn, "datacamp")
    data_position = int(datacamp["position"]) if datacamp else 0
    next_position = data_position + 1
    if next_position <= len(DATACAMP_TRACK):
        course_name, chapter, _ = DATACAMP_TRACK[next_position - 1]
        for skill_key, threshold in DATACAMP_SKILL_THRESHOLDS.items():
            if threshold == next_position:
                _append_evidence(
                    sources,
                    skill_key,
                    f"DataCamp: {course_name} — {chapter} in progress",
                )

    rows = conn.execute(
        """SELECT s.label
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=0 AND m.status='In Progress'"""
    ).fetchall()
    for row in rows:
        number = exercise_number_for_label(row["label"])
        if number is None:
            continue
        exercise = DUCKDB_EXERCISES[number]
        for skill_key in DUCKDB_SKILL_EVIDENCE.get(number, set()):
            _append_evidence(
                sources,
                skill_key,
                f"DuckDB Exercise {number:02d}: {exercise['title']} in progress",
            )
    applied_rows = conn.execute(
        """SELECT s.label FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=0 AND m.status='In Progress'"""
    ).fetchall()
    for row in applied_rows:
        number = applied_exercise_number_for_label(row["label"])
        if number is None:
            continue
        item = APPLIED_EXERCISES[number]
        for skill_key in APPLIED_SKILL_EVIDENCE.get(number, set()):
            _append_evidence(
                sources,
                skill_key,
                f"Applied Lab {number:02d}: {item['title']} in progress",
            )

    return sources


def skill_inventory(conn, state):
    evidence_map = _skill_evidence(conn, state)
    progress_map = _skill_in_progress_sources(conn, state)
    inventory = []

    for skill_key, (display_name, default_evidence) in SKILL_DEFINITIONS.items():
        evidence = list(evidence_map.get(skill_key, []))
        in_progress = list(progress_map.get(skill_key, []))

        if evidence:
            status = "Learned"
        elif in_progress:
            status = "In Progress"
        else:
            status = "Locked"

        category = (
            "SQL"
            if skill_key.startswith("sql_")
            else SKILL_CATEGORY.get(skill_key, "Analytics")
        )
        inventory.append(
            {
                "skill_key": skill_key,
                "display_name": display_name,
                "category": category,
                "status": status,
                "evidence": evidence,
                "in_progress": in_progress,
                "accepted_evidence": SQL_SKILL_ACCEPTED_EVIDENCE.get(
                    skill_key,
                    default_evidence,
                ),
            }
        )

    order = {"Learned": 0, "In Progress": 1, "Locked": 2}
    return sorted(
        inventory,
        key=lambda item: (
            order[item["status"]],
            item["category"],
            item["display_name"],
        ),
    )


def sql_problem_readiness(
    conn,
    state,
    title,
):
    item = _sql_item(title)
    if item is None:
        return {
            "ready": False,
            "required_keys": [],
            "required_names": [],
            "missing_keys": [],
            "missing_names": [
                "Problem is not in the SQL catalog"
            ],
        }

    unlocked = _derived_skills(
        conn,
        state,
    )
    required = _sql_requirements(
        title,
        item[2],
    )
    missing = set(required) - set(
        unlocked
    )

    evidence_map = _skill_evidence(conn, state)

    return {
        "ready": not missing,
        "required_keys": sorted(required),
        "required_names": [
            SKILL_DEFINITIONS[key][0]
            for key in sorted(required)
        ],
        "missing_keys": sorted(missing),
        "missing_names": [
            SKILL_DEFINITIONS[key][0]
            for key in sorted(missing)
        ],
        "evidence": {
            key: list(evidence_map.get(key, []))
            for key in sorted(required)
        },
        "accepted_evidence": {
            key: SQL_SKILL_ACCEPTED_EVIDENCE.get(
                key,
                SKILL_DEFINITIONS[key][1],
            )
            for key in sorted(missing)
        },
    }


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
        required = _sql_requirements(
            title,
            item[2],
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
