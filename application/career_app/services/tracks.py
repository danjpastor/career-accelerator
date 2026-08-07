from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

from career_app.data.applied_exercises import (
    APPLIED_EXERCISES,
    APPLIED_SKILL_EVIDENCE,
    CORE_APPLIED_LABS,
    exercise_number_for_label as applied_exercise_number_for_label,
)
from career_app.services import achievements as achievement_service
from career_app.services import completion_contract
from career_app.services import content_gates
from career_app.services import weekly_checks
from career_app.data.duckdb_exercises import (
    DUCKDB_EXERCISES,
    exercise_for_label,
    exercise_number_for_label,
    roadmap_number as duckdb_roadmap_number,
)
from career_app.data.roadmap import SQL_COMPANION
from career_app.data import google_certificate_curriculum as google_curriculum
from career_app.navigation import PAGE_LEARNING, PAGE_PORTFOLIO


def _coerce_task_id(value):
    try:
        text = str(value).strip()
        if not re.fullmatch(r"[+-]?\d+", text):
            return None
        return int(text)
    except (TypeError, ValueError, OverflowError):
        return None


TRACK_CONFIG = {
    "google": {
        "display_name": "Google Certificate",
        "category": "Learning",
        "destination": PAGE_LEARNING,
        "priority": 0,
        "sort_band": -400000,
        "role": "Primary",
    },
    "datacamp": {
        "display_name": "DataCamp",
        "category": "Learning",
        "destination": PAGE_LEARNING,
        "priority": 1,
        "sort_band": -300000,
        "role": "Supplemental",
    },
    "sql": {
        "display_name": "SQL Practice",
        "category": "SQL",
        "destination": PAGE_LEARNING,
        "priority": 1,
        "sort_band": -200000,
        "role": "Supplemental",
    },
    "portfolio": {
        "display_name": "Portfolio",
        "category": "Portfolio",
        "destination": PAGE_PORTFOLIO,
        "priority": 2,
        "sort_band": -100000,
        "role": "Application",
    },
}

TRACK_ORDER = (
    "google",
    "sql",
    "portfolio",
)


# Current English Google Data Analytics Professional Certificate curriculum.
# Progression must use course-specific module totals rather than assuming every
# course has the same number of modules.
GOOGLE_COURSE_MODULE_COUNTS = dict(google_curriculum.COURSE_MODULE_COUNTS)


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


APPLIED_BRANCHES = {'Google Sheets': (1,),
 'Statistics': (2, 5, 9, 12, 16, 22, 28),
 'SQL Quality': (3, 4, 7, 10),
 'Business Patterns': (6, 13, 17, 23),
 'Communication': (8, 27, 34),
 'Timed Requests': (11, 32, 35),
 'Power BI': (14, 15, 18, 19, 25, 26, 36),
 'pandas': (20, 21, 30, 31),
 'Data Workflow': (24, 29),
 'Responsible AI': (33,)}

APPLIED_BRANCH_ORDER = tuple(
    APPLIED_BRANCHES
)
CORE_APPLIED_BRANCH_ORDER = tuple(
    branch
    for branch, numbers in APPLIED_BRANCHES.items()
    if any(number in CORE_APPLIED_LABS for number in numbers)
)

APPLIED_REQUIRED_SKILLS = {15: {'power_query'},
 18: {'power_query'},
 19: {'dimensional_modeling'},
 25: {'power_bi'},
 26: {'report_design'},
 1: {'data_preparation'},
 21: {'python_pandas', 'data_cleaning'},
 31: {'sql_aggregation'},
 8: {'analysis_foundations'},
 3: {'sql_querying'},
 4: {'sql_joins'},
 7: {'sql_date_logic', 'sql_aggregation'},
 10: {'data_storytelling'},
 11: {'analyst_communication', 'sql_validation'},
 35: {'analyst_communication'},
 2: {'analysis_foundations'},
 5: {'data_preparation', 'descriptive_statistics'},
 9: {'sampling_bias', 'descriptive_statistics'},
 12: {'confidence_intervals'},
 16: {'hypothesis_testing', 'analyst_communication'},
 22: {'experiment_analysis'},
 28: {'python_pandas', 'causal_reasoning'},
 6: {'sql_aggregation', 'business_framing'},
 13: {'sql_aggregation', 'sql_date_logic', 'sql_ctes'},
 17: {'sql_date_logic', 'cohort_analysis', 'sql_joins'},
 23: {'sql_aggregation', 'analysis_foundations', 'churn_analysis'},
 24: {'python_pandas', 'data_preparation'},
 29: {'sql_ctes', 'api_ingestion', 'data_cleaning'},
 33: {'diagnostic_reasoning', 'analyst_communication', 'sql_validation'},
 36: {'power_bi_governance', 'report_design'}}

APPLIED_WEEK_BRANCH_PRIORITY = {1: ('Statistics',
     'Business Patterns',
     'SQL Quality',
     'Google Sheets',
     'Power BI',
     'pandas',
     'Communication',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 2: ('Statistics',
     'Business Patterns',
     'SQL Quality',
     'Google Sheets',
     'Power BI',
     'pandas',
     'Communication',
     'Data Workflow',
     'Responsible AI',
     'Timed Requests'),
 3: ('Google Sheets',
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
     'Google Sheets',
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
     'Google Sheets',
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
     'Google Sheets',
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
     'Google Sheets',
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
     'Google Sheets',
     'Responsible AI'),
 9: ('Statistics',
     'Business Patterns',
     'Data Workflow',
     'Power BI',
     'Communication',
     'pandas',
     'SQL Quality',
     'Timed Requests',
     'Google Sheets',
     'Responsible AI'),
 10: ('Statistics',
      'Data Workflow',
      'Business Patterns',
      'pandas',
      'Timed Requests',
      'Communication',
      'Power BI',
      'SQL Quality',
      'Google Sheets',
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
      'Google Sheets'),
 12: ('Responsible AI',
      'Data Workflow',
      'Statistics',
      'Business Patterns',
      'Timed Requests',
      'Communication',
      'Power BI',
      'pandas',
      'SQL Quality',
      'Google Sheets')}


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
        "Complete the DataCamp Power BI foundations course and practical checks",
    ),
    "power_bi": (
        "Power BI Modeling and DAX",
        "Complete the DataCamp Power BI modeling and DAX practical checks",
    ),
    "python_pandas": (
        "Python and pandas",
        "Complete the DataCamp Python and pandas practical checks",
    ),
    "roadmap.spreadsheet_mastery": (
        "Spreadsheet Mastery",
        "Pass the Week 2 Knowledge Check",
    ),
    "roadmap.sql_mastery": (
        "Spreadsheet & SQL Mastery",
        "Pass the Week 6 Knowledge Check",
    ),
    "roadmap.power_bi_mastery": (
        "Power BI Mastery",
        "Pass the Week 7 Knowledge Check",
    ),
    "roadmap.portfolio_readiness": (
        "Portfolio Readiness",
        "Pass the Week 8 Knowledge Check",
    ),
    "portfolio_delivery": (
        "Portfolio Case Study Delivery",
        "Google capstone progress",
    ),
    "career_readiness": (
        "Career Readiness",
        "Google career course",
    ),
    "excel_analytics": ("Google Sheets Analysis and Controls", "Complete the Google Sheets analyst spreadsheet lab"),
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
    "descriptive_statistics": ('Descriptive Statistics and Distributions', 'Complete Applied Lab 02'),
    "sampling_bias": ('Sampling and Bias Evaluation', 'Complete Applied Lab 05'),
    "confidence_intervals": ('Confidence Intervals and Margin of Error', 'Complete Applied Lab 09'),
    "inferential_statistics": ('Inferential Statistics', 'Complete approved confidence-interval or hypothesis-testing work'),
    "hypothesis_testing": ('Hypothesis Testing', 'Complete Applied Lab 12'),
    "experiment_analysis": ('A/B-Test and Experiment Analysis', 'Complete Applied Lab 16'),
    "causal_reasoning": ('Correlation and Causal Reasoning', 'Complete Applied Lab 22'),
    "regression_interpretation": ('Linear Regression Interpretation', 'Complete Applied Lab 28'),
    "funnel_analysis": ('Conversion Funnel Analysis', 'Complete Applied Lab 06'),
    "cohort_analysis": ('Cohort and Retention Analysis', 'Complete Applied Lab 13'),
    "churn_analysis": ('Customer and Revenue Churn Analysis', 'Complete Applied Lab 17'),
    "variance_analysis": ('Forecast and Variance Analysis', 'Complete Applied Lab 23'),
    "api_ingestion": ('REST API and JSON Ingestion', 'Complete Applied Lab 24'),
    "data_pipeline": ('Reproducible Analytics Pipeline', 'Complete Applied Lab 29'),
    "data_lineage": ('Data Lineage and Layered Modeling', 'Complete Applied Lab 29'),
    "ai_validation": ('Responsible AI-Assisted Analysis Validation', 'Complete Applied Lab 33'),
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
    "Histogram of Tweets": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Data Science Skills": {"all_of": {"roadmap.spreadsheet_mastery", "sql_querying", "sql_aggregation"}, "any_of": set()},
    "Page With No Likes": {"all_of": {"roadmap.spreadsheet_mastery", "sql_joins", "sql_querying"}, "any_of": set()},
    "Laptop vs. Mobile Viewership": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation", "sql_case"}, "any_of": set()},
    "Duplicate Job Listings": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation"}, "any_of": set()},
    "Teams Power Users": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation", "sql_date_logic"}, "any_of": set()},
    "Pharmacy Analytics Part 1": {"all_of": {"roadmap.spreadsheet_mastery", "sql_querying"}, "any_of": set()},
    "Signup Activation Rate": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation", "sql_joins", "sql_case"}, "any_of": set()},
    "User's Third Transaction": {"all_of": {"roadmap.spreadsheet_mastery", "sql_window_functions"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Second Highest Salary": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation", "sql_window_functions"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Top Three Salaries": {"all_of": {"roadmap.spreadsheet_mastery", "sql_joins", "sql_window_functions"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Tweets' Rolling Averages": {"all_of": {"roadmap.spreadsheet_mastery", "sql_window_functions"}, "any_of": set()},
    "Odd and Even Measurements": {"all_of": {"roadmap.spreadsheet_mastery", "sql_window_functions", "sql_date_logic", "sql_case"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "User Shopping Sprees": {"all_of": {"roadmap.spreadsheet_mastery", "sql_joins", "sql_date_logic"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Supercloud Customer": {"all_of": {"roadmap.spreadsheet_mastery", "sql_aggregation", "sql_joins"}, "any_of": {"sql_subqueries", "sql_ctes"}},
    "Second Day Confirmation": {"all_of": {"roadmap.spreadsheet_mastery", "sql_joins", "sql_date_logic"}, "any_of": set()},
}

SQL_INTERVIEW_SEQUENCE = tuple(item[0] for item in SQL_COMPANION)

SQL_PROBLEM_PREREQUISITES = {
    title: (SQL_INTERVIEW_SEQUENCE[index - 1],)
    for index, title in enumerate(SQL_INTERVIEW_SEQUENCE)
    if index > 0
}


SQL_PROBLEM_WEEK = {
    "Data Science Skills": 3,
    "Pharmacy Analytics Part 1": 3,
    "Histogram of Tweets": 4,
    "Duplicate Job Listings": 3,
    "Laptop vs. Mobile Viewership": 4,
    "Page With No Likes": 4,
    "Signup Activation Rate": 4,
    "Second Day Confirmation": 5,
    "Supercloud Customer": 4,
    "Teams Power Users": 5,
    "Second Highest Salary": 5,
    "User's Third Transaction": 5,
    "Top Three Salaries": 5,
    "Odd and Even Measurements": 5,
    "Tweets' Rolling Averages": 5,
    "User Shopping Sprees": 5,
}

SQL_SKILL_ACCEPTED_EVIDENCE = {
    "sql_fundamentals": (
        "Complete DataCamp SQL foundations, SQL Challenge 01, "
        "or validated introductory SQL practice"
    ),
    "sql_querying": (
        "Complete DataCamp selection, filtering, sorting, DISTINCT, and LIMIT lessons, "
        "SQL Challenge 01, or validated querying practice"
    ),
    "sql_aggregation": (
        "Complete DataCamp aggregation and grouping lessons, SQL Challenge 03/09/13, "
        "or a validated aggregation problem"
    ),
    "sql_date_logic": (
        "Complete DataCamp date and time functions, SQL Challenge 18/21/22, "
        "or a validated date-logic problem"
    ),
    "sql_case": (
        "Complete DataCamp CASE and conditional aggregation lessons, SQL Challenge 11/19/30, "
        "or a validated CASE problem"
    ),
    "sql_joins": (
        "Complete DataCamp joins and relationship lessons, SQL Challenge 05/06/07/29, "
        "or a validated join problem"
    ),
    "sql_subqueries": (
        "Complete the DataCamp subqueries lesson, SQL Challenge 10/12, "
        "or validated subquery practice"
    ),
    "sql_ctes": (
        "Complete the DataCamp CTE lesson, SQL Challenge 13/17/22, "
        "or validated CTE practice"
    ),
    "sql_window_functions": (
        "Complete DataCamp window-function lessons, SQL Challenge 14–19, "
        "or a validated window-function problem"
    ),
    "sql_intermediate": (
        "Complete validated subquery, CTE, or window-function learning and practice"
    ),
    "roadmap.spreadsheet_mastery": "Pass the Week 2 Knowledge Check",
    "roadmap.sql_mastery": "Pass the Week 6 Knowledge Check",
    "roadmap.power_bi_mastery": "Pass the Week 7 Knowledge Check",
    "roadmap.portfolio_readiness": "Pass the Week 8 Knowledge Check",
}

DUCKDB_SKILL_EVIDENCE = {
    1: {"sql_fundamentals", "sql_querying"},
    19: {"sql_fundamentals", "sql_querying"},
    20: {"sql_aggregation"},
    2: {"sql_querying"},
    21: {"sql_joins"},
    6: {"sql_joins"},
    22: {"sql_joins"},
    16: {"sql_querying", "sql_intermediate"},
    13: {"sql_aggregation", "sql_joins", "sql_validation"},
    23: {"sql_subqueries", "sql_intermediate"},
    5: {"sql_case"},
    7: {"sql_subqueries", "sql_intermediate"},
    12: {"sql_aggregation", "sql_ctes", "sql_intermediate"},
    24: {"sql_window_functions"},
    25: {"sql_window_functions"},
    26: {"sql_window_functions", "sql_intermediate"},
    15: {"sql_ctes", "sql_window_functions", "sql_date_logic", "sql_intermediate"},
    11: {"sql_window_functions", "sql_date_logic", "sql_intermediate"},
    27: {"sql_aggregation", "sql_case", "sql_window_functions", "sql_intermediate"},
    28: {"data_cleaning", "sql_validation"},
    14: {"sql_date_logic"},
    4: {"sql_aggregation", "sql_ctes", "sql_date_logic", "cohort_analysis"},
    3: {"data_cleaning", "sql_validation"},
    17: {"data_cleaning", "sql_querying"},
    29: {"data_cleaning", "sql_querying"},
    30: {"sql_aggregation", "sql_validation"},
    31: {"sql_aggregation", "sql_validation"},
    32: {"sql_querying", "sql_validation"},
    33: {"sql_joins", "sql_validation"},
    8: {"sql_aggregation", "sql_case", "sql_joins", "sql_intermediate"},
    9: {"sql_aggregation", "timed_analysis"},
    10: {"sql_aggregation", "sql_joins", "sql_intermediate"},
    18: {
        "sql_fundamentals", "sql_querying", "sql_aggregation", "sql_case",
        "sql_joins", "sql_ctes", "sql_window_functions", "sql_date_logic",
        "sql_validation", "sql_intermediate"
    },
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
        "sql_fundamentals", "sql_querying", "sql_intermediate"
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
    "excel_analytics": "Google Sheets",
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


def _sql_requirement_groups(title, topic):
    spec = SQL_PROBLEM_REQUIREMENTS.get(title)
    if spec is None:
        return {"all_of": set(SQL_REQUIREMENTS.get(topic, {"sql_querying"})), "any_of": set()}
    if isinstance(spec, dict):
        return {"all_of": set(spec.get("all_of", set())), "any_of": set(spec.get("any_of", set()))}
    return {"all_of": set(spec), "any_of": set()}


def _sql_requirements(title, topic):
    groups = _sql_requirement_groups(title, topic)
    return set(groups["all_of"]) | set(groups["any_of"])


def _sql_requirement_status(title, topic, unlocked):
    """Evaluate all-of and alternative SQL prerequisites consistently.

    ``any_of`` requirements represent accepted solution paths.  They must not be
    flattened into a set that falsely requires every alternative.
    """
    groups = _sql_requirement_groups(title, topic)
    unlocked = set(unlocked)
    missing_all = set(groups["all_of"]) - unlocked
    missing_any = set()
    if groups["any_of"] and not (set(groups["any_of"]) & unlocked):
        missing_any = set(groups["any_of"])
    required = set(groups["all_of"]) | set(groups["any_of"])
    missing_names = [
        SKILL_DEFINITIONS[skill][0]
        for skill in sorted(missing_all)
    ]
    if missing_any:
        missing_names.append(
            "One of: "
            + " or ".join(
                SKILL_DEFINITIONS[skill][0]
                for skill in sorted(missing_any)
            )
        )
    return {
        "ready": not missing_all and not missing_any,
        "required": required,
        "missing_all": missing_all,
        "missing_any": missing_any,
        "missing": missing_all | missing_any,
        "missing_names": missing_names,
    }

PORTFOLIO_PREPARATION_LABELS = {
    "Review and approve project brief",
    "Approve data source and specification",
    "Create or acquire raw dataset",
    "Validate Relationships",
    "Review and finalize data dictionary",
    "Finalize business problem",
    "Finalize stakeholders",
    "Finalize KPIs",
    "Finalize business questions",
    "Create synthetic data specification",
    "Generate dataset",
    "Validate relationships",
    "Complete data dictionary",
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


ADAPTIVE_SCHEDULE_TABLE = "adaptive_track_schedule"


def _create_adaptive_schedule_store(conn):
    conn.execute(
        f"""CREATE TABLE IF NOT EXISTS {ADAPTIVE_SCHEDULE_TABLE} (
            track_key TEXT PRIMARY KEY,
            target_key TEXT NOT NULL,
            recommended_date TEXT NOT NULL,
            assigned_week INTEGER NOT NULL,
            assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )


def _recommended_target_date(
    *,
    weekly_target,
    weekly_completed,
    reference=None,
):
    """Return the recommended weekday for the next sequential track item.

    Weekly targets are spread across Monday through Friday.  When this week's
    quota is already complete, the next item is scheduled for next Monday.
    """
    current = reference or date.today()
    week_start = current - timedelta(days=current.weekday())
    weekly_target = max(0, int(weekly_target or 0))
    ordinal = max(1, int(weekly_completed or 0) + 1)

    if weekly_target <= 0 or ordinal > weekly_target:
        return week_start + timedelta(days=7)

    offset = max(
        0,
        min(
            4,
            math.ceil(ordinal * 5 / weekly_target) - 1,
        ),
    )
    return week_start + timedelta(days=offset)


def _ensure_target_schedule(
    conn,
    *,
    track_key,
    target_key,
    week,
    weekly_target,
    weekly_completed,
):
    _create_adaptive_schedule_store(conn)
    row = conn.execute(
        f"""SELECT target_key,recommended_date
            FROM {ADAPTIVE_SCHEDULE_TABLE}
            WHERE track_key=?""",
        (str(track_key),),
    ).fetchone()

    if row is not None and str(row["target_key"]) == str(target_key):
        try:
            return date.fromisoformat(str(row["recommended_date"]))
        except (TypeError, ValueError):
            pass

    recommended = _recommended_target_date(
        weekly_target=weekly_target,
        weekly_completed=weekly_completed,
    )
    conn.execute(
        f"""INSERT INTO {ADAPTIVE_SCHEDULE_TABLE}
            (track_key,target_key,recommended_date,assigned_week)
            VALUES(?,?,?,?)
            ON CONFLICT(track_key) DO UPDATE SET
                target_key=excluded.target_key,
                recommended_date=excluded.recommended_date,
                assigned_week=excluded.assigned_week,
                assigned_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP""",
        (
            str(track_key),
            str(target_key),
            recommended.isoformat(),
            int(week),
        ),
    )
    return recommended


def _clear_target_schedule(conn, track_key):
    _create_adaptive_schedule_store(conn)
    conn.execute(
        f"DELETE FROM {ADAPTIVE_SCHEDULE_TABLE} WHERE track_key=?",
        (str(track_key),),
    )


def _remove_active_track_task(conn, track_key):
    """Remove an uncompleted generated task when its roadmap topic is not active."""
    row = conn.execute(
        "SELECT task_id FROM track_tasks WHERE track_key=?",
        (str(track_key),),
    ).fetchone()
    if row is None:
        return None
    task_id = int(row["task_id"])
    completed = conn.execute(
        "SELECT completed FROM sprint_tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    if completed is not None and bool(completed["completed"]):
        conn.execute("DELETE FROM track_tasks WHERE track_key=?", (str(track_key),))
        return task_id
    conn.execute("UPDATE task_workspaces SET task_id=NULL WHERE task_id=?", (task_id,))
    conn.execute("UPDATE study_sessions SET task_id=NULL WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM daily_focus WHERE task_id=?", (task_id,))
    conn.execute("DELETE FROM track_tasks WHERE track_key=?", (str(track_key),))
    conn.execute("DELETE FROM sprint_tasks WHERE id=?", (task_id,))
    return task_id


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
    # Applied Labs are phase-end integration checks, not a parallel project
    # workload. At most one core lab is assigned in a week.
    applied_target = 0

    return {
        "google": {
            "weekly_target": google_target,
            "allocation_percent": 67,
            "allocation_minutes": google_minutes,
        },
        "sql": {
            "weekly_target": sql_target,
            "allocation_percent": 13,
            "allocation_minutes": int(
                hours * 60 * 0.13
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
            "weekly_target": 0,
            "allocation_percent": 0,
            "allocation_minutes": 0,
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
    description=None,
    definition_of_done=None,
    starter_path=None,
    managed_key=None,
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
                   description=COALESCE(?,description),
                   definition_of_done=COALESCE(?,definition_of_done),
                   starter_path=COALESCE(?,starter_path),
                   managed_key=COALESCE(?,managed_key),
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
                description,
                definition_of_done,
                starter_path,
                managed_key,
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
               prerequisite_reason,
               description,
               definition_of_done,
               starter_path,
               managed_key
           )
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
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
               prerequisite_reason=NULL,
               description=CASE
                   WHEN TRIM(excluded.description)<>'' THEN excluded.description
                   ELSE task_metadata.description
               END,
               definition_of_done=CASE
                   WHEN TRIM(excluded.definition_of_done)<>'' THEN excluded.definition_of_done
                   ELSE task_metadata.definition_of_done
               END,
               starter_path=COALESCE(excluded.starter_path,task_metadata.starter_path),
               managed_key=COALESCE(excluded.managed_key,task_metadata.managed_key)""",
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
            "" if description is None else str(description),
            "" if definition_of_done is None else str(definition_of_done),
            starter_path,
            managed_key,
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
    """Return the next sequential Google module when its topic week is active.

    Google remains the highest-priority track, but future-topic modules are held
    outside the task queue.  This prevents Python, portfolio, or career modules
    from displacing the spreadsheet and SQL work that prepares the learner for
    them.
    """
    course, module = normalize_google_position(
        state["google_course"],
        state["google_module"],
    )
    item = google_curriculum.module_or_none(course, module)
    if item is None:
        return None

    current_week = max(1, int(state.get("current_week", 1)))
    alignment = GOOGLE_ALIGNMENT.get(
        course,
        "the current certificate material",
    )
    metadata = {
        "course": course,
        "module": module,
        "course_name": item.course_name,
        "module_name": item.module_name,
        "scheduled_week": item.week,
        "assigned_week": item.week,
        "alignment": alignment,
        "primary_goal": (
            "Complete this module before lower-priority work once its topic "
            "week is active."
        ),
        "description": (
            f"Complete Course {course}, Module {module}: {item.module_name}. "
            f"This module is aligned to Week {item.week} of the roadmap."
        ),
        "definition_of_done": (
            "Finish the complete Coursera module, including its required "
            "activities and module assessment, then mark this task complete."
        ),
        "starter_path": item.url,
        "managed_key": f"google:{item.key}",
    }
    metadata.update(pace)

    target = {
        "target_key": item.key,
        "label": item.task_label,
        "source_label": item.source_label,
        "estimate": item.estimated_minutes,
        "position": course,
        "subposition": module,
        "assigned_week": item.week,
        "metadata": metadata,
    }
    if item.week > current_week:
        target.update(
            {
                "locked": True,
                "metadata": {
                    **metadata,
                    "lock_reason": (
                        f"Scheduled for Week {item.week}, when the roadmap "
                        f"covers {alignment}."
                    ),
                    "future_topic": True,
                },
            }
        )
    return target


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


def _datacamp_target(conn, state, pace):
    """Legacy compatibility hook. DataCamp is no longer an active roadmap track."""
    return None


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


DATACAMP_SKILL_EVIDENCE = {
    "w03_intro_sql_02": {"sql_fundamentals", "sql_querying"},
    "w03_intermediate_sql_03": {"sql_aggregation"},
    "w03_intermediate_sql_04": {"sql_aggregation"},
    "w04_joining_sql_02": {"sql_joins"},
    "w04_manipulation_sql_01": {"sql_case"},
    "w04_manipulation_sql_02": {"sql_intermediate"},
    "w04_manipulation_sql_03": {"sql_subqueries", "sql_ctes", "sql_intermediate"},
    "w04_manipulation_sql_04": {"sql_window_functions", "sql_intermediate"},
    "w05_window_sql_03": {"sql_window_functions", "sql_intermediate"},
    "w05_functions_sql_02": {"sql_date_logic"},
    "w05_functions_sql_03": {"data_cleaning", "sql_validation"},
    "w06_database_design_04": {"sql_validation"},
    "w07_intro_powerbi_04": {"power_bi_foundations"},
    "w07_model_powerbi_04": {"power_bi_foundations"},
    "w07_dax_powerbi_03": {"power_bi"},
    "w07_visual_powerbi_04": {"power_bi"},
    "w08_intermediate_python_05": {"python_pandas"},
    "w08_pandas_04": {"python_pandas"},
}


def _datacamp_skill_evidence(conn):
    tables = {
        row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "datacamp_chapter_progress" not in tables:
        return {}

    completed_rows = conn.execute(
        """SELECT chapter_key,course_name,chapter_number,chapter_name
           FROM datacamp_chapter_progress WHERE status='Completed'"""
    ).fetchall()
    completed = {str(row["chapter_key"]): row for row in completed_rows}
    evidence = {}
    for key, skills in DATACAMP_SKILL_EVIDENCE.items():
        row = completed.get(key)
        if row is None:
            continue
        source = (
            f"DataCamp: {row['course_name']}, "
            f"Chapter {row['chapter_number']} — {row['chapter_name']}"
        )
        for skill_key in skills:
            _append_evidence(evidence, skill_key, source)

    spreadsheet_keys = {
        str(row["chapter_key"]) for row in completed_rows
        if str(row["chapter_key"]).startswith(("w01_", "w02_"))
    }
    required_spreadsheets = {
        str(row["chapter_key"]) for row in conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress "
            "WHERE chapter_key LIKE 'w01_%' OR chapter_key LIKE 'w02_%'"
        ).fetchall()
    }
    if required_spreadsheets and required_spreadsheets <= spreadsheet_keys:
        _append_evidence(evidence, "roadmap.spreadsheet_mastery", "Completed required DataCamp spreadsheet chapters")

    ex18 = conn.execute(
        "SELECT 1 FROM duckdb_exercise_progress WHERE exercise_number=18 AND status='Completed'"
    ).fetchone()
    required_sql = {
        str(row["chapter_key"]) for row in conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress "
            "WHERE chapter_key LIKE 'w03_%' OR chapter_key LIKE 'w04_%' "
            "OR chapter_key LIKE 'w05_%' OR chapter_key LIKE 'w06_%'"
        ).fetchall()
    }
    if ex18 and required_sql and required_sql <= set(completed):
        _append_evidence(evidence, "roadmap.sql_mastery", "Completed DataCamp SQL curriculum and SQL Challenge 33")

    required_powerbi = {
        str(row["chapter_key"]) for row in conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress WHERE chapter_key LIKE 'w07_%'"
        ).fetchall()
    }
    if required_powerbi and required_powerbi <= set(completed):
        _append_evidence(evidence, "roadmap.power_bi_mastery", "Completed required DataCamp Power BI chapters")

    required_all = {str(row["chapter_key"]) for row in conn.execute(
        "SELECT chapter_key FROM datacamp_chapter_progress"
    ).fetchall()}
    if ex18 and required_all and required_all <= set(completed):
        _append_evidence(evidence, "roadmap.portfolio_readiness", "Completed required DataCamp curriculum and final SQL Challenge audit")
    return evidence


def _skill_evidence(conn, state):
    course = int(state["google_course"])
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


    for skill_key, sources in _datacamp_skill_evidence(conn).items():
        for source in sources:
            _append_evidence(evidence, skill_key, source)

    for number in sorted(_completed_duckdb_exercises(conn)):
        exercise = DUCKDB_EXERCISES[number]
        source = f"SQL Challenge {duckdb_roadmap_number(number):02d}: {exercise['title']}"
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
        for skill_key in _sql_requirement_groups(title, item[2])["all_of"]:
            # Interview completion can demonstrate SQL concepts, but it may not
            # manufacture a weekly mastery-gate credential.
            if skill_key.startswith("roadmap."):
                continue
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


def approved_skill_evidence(conn, state):
    """Return the canonical validated evidence used by every skill lockout."""
    return _skill_evidence(conn, state)


def approved_skills(conn, state):
    return set(approved_skill_evidence(conn, state))


def _derived_skills(conn, state):
    return approved_skills(conn, state)

def _evidence_source_track(evidence_items, skill_key):
    sources = set()
    for item in evidence_items:
        if item.startswith("Completed Google"):
            sources.add("google")
        elif item.startswith("DataCamp:"):
            sources.add("datacamp")
        elif item.startswith("SQL Challenge"):
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
        requirements = set(PROJECT_EXACT_REQUIREMENTS[label])
        if label not in PORTFOLIO_PREPARATION_LABELS:
            requirements.add("roadmap.portfolio_readiness")
        return requirements

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
        requirements.add("analytics_foundations")

    if label not in PORTFOLIO_PREPARATION_LABELS:
        requirements.add("roadmap.portfolio_readiness")

    return requirements


def portfolio_task_readiness(
    conn,
    state,
    label,
    stage=None,
):
    required = _requirements_for_project(label, stage)
    unlocked = _derived_skills(conn, state)
    missing_skill_names = _missing_skill_names(required, unlocked)
    execution = str(label) not in PORTFOLIO_PREPARATION_LABELS
    datacamp_gate = content_gates.gate_status(
        conn,
        content_gates.requirements_for_portfolio(
            required,
            execution=execution,
        ),
    )
    execution_too_early = execution and int(state["current_week"]) < 9
    missing_names = list(missing_skill_names)
    if not datacamp_gate["ready"]:
        missing_names.append(datacamp_gate["summary"])
    if execution_too_early:
        missing_names.insert(
            0,
            "Scheduled for Week 9 after the learning phase",
        )
    return {
        "ready": not missing_names,
        "required_skills": sorted(required),
        "missing_skills": missing_skill_names,
        "required_datacamp_keys": datacamp_gate["required_keys"],
        "required_datacamp_names": datacamp_gate["required_names"],
        "missing_datacamp_keys": datacamp_gate["missing_keys"],
        "missing_datacamp_names": datacamp_gate["missing_names"],
        "missing": missing_names,
        "execution": execution,
        "execution_too_early": execution_too_early,
    }


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

        requirement_status = sql_problem_readiness(
            conn,
            state,
            title,
        )
        required = set(requirement_status["required_keys"])
        if not requirement_status["ready"]:
            locked_candidates.append(
                (
                    index,
                    title,
                    difficulty,
                    topic,
                    concepts,
                    estimate,
                    required,
                    set(requirement_status["missing_keys"]),
                    list(requirement_status["missing_names"]),
                    list(requirement_status["required_datacamp_keys"]),
                    list(requirement_status["missing_datacamp_keys"]),
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
            "required_datacamp_keys": list(requirement_status["required_datacamp_keys"]),
            "missing_datacamp_keys": [],
            "description": (
                f"Open {title} in Learning Practice, write and save your own SQL "
                "solution, then mark the problem complete. Use the notes area "
                "to record your approach, checks, or anything you want to review."
            ),
            "definition_of_done": (
                "A non-template SQL query is saved for the problem, the SQL "
                "practice record is marked Completed, and the linked roadmap "
                "task advances to the next eligible interview problem."
            ),
            "managed_key": f"sql-problem:{title}",
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
            missing_names,
            required_datacamp_keys,
            missing_datacamp_keys,
        ) = locked_candidates[0]
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
            "required_datacamp_keys": required_datacamp_keys,
            "missing_datacamp_keys": missing_datacamp_keys,
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
        """SELECT id,sort_order,stage,label,description,
                  definition_of_done,starter_path,estimated_minutes
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

    readiness = portfolio_task_readiness(
        conn,
        state,
        row["label"],
        row["stage"],
    )
    required = set(readiness["required_skills"])
    missing_names = list(readiness["missing"])
    execution_too_early = bool(readiness["execution_too_early"])

    metadata = {
        "project_id": project_id,
        "stage": row["stage"],
        "milestone": row["label"],
        "completed": completed,
        "total": total,
        "required_skills": sorted(
            required
        ),
        "missing_skills": readiness["missing_skills"],
        "required_datacamp_keys": readiness["required_datacamp_keys"],
        "missing_datacamp_keys": readiness["missing_datacamp_keys"],
        "description": str(row["description"] or ""),
        "definition_of_done": str(row["definition_of_done"] or ""),
        "starter_path": str(row["starter_path"] or ""),
        "estimated_minutes": int(row["estimated_minutes"] or 45),
        "managed_key": f"portfolio:{project_id}:{int(row['id'])}",
    }
    metadata.update(pace)

    if missing_names or execution_too_early:
        metadata["blocked_reason"] = "Unlock first: " + "; ".join(missing_names)
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
        "estimate": int(row["estimated_minutes"] or 45),
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
        or value in CORE_APPLIED_BRANCH_ORDER
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
    if 25 in completed:
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
            "required_datacamp_keys": list(content_gates.requirements_for_applied_lab(number)),
            "required_datacamp_names": [
                content_gates.chapter_name(key)
                for key in content_gates.requirements_for_applied_lab(number)
            ],
            "missing_datacamp_keys": [],
            "missing_datacamp_names": [],
            "roadmap_week": int(
                item["week"]
            ),
        }

    numbers = APPLIED_BRANCHES.get(
        branch,
        (number,),
    )
    position = numbers.index(number) if number in numbers else 0
    missing_labs = [
        previous
        for previous in numbers[:position]
        if previous in CORE_APPLIED_LABS
        and previous not in completed
    ]
    if item.get("optional"):
        missing_labs = []

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

    datacamp_gate = content_gates.gate_status(
        conn,
        content_gates.requirements_for_applied_lab(number),
    )
    if not datacamp_gate["ready"]:
        missing.append(datacamp_gate["summary"])

    lab_week = int(item["week"])
    if lab_week > 1 and not weekly_checks.passed(conn, lab_week - 1):
        missing.append(f"Pass {weekly_checks.title(lab_week - 1)}")

    if (
        number == 27
        and not _has_dashboard_artifact(
            conn,
            completed,
        )
    ):
        missing.append(
            (
                "Complete a dashboard artifact "
                "(Applied Lab 25 or equivalent)"
            )
        )

    # Timed requests are deliberately cross-functional.
    if number == 11:
        if 8 not in completed and (
            "analyst_communication"
            not in unlocked
        ):
            missing.append(
                (
                    "Complete Applied Lab 08 "
                    "or equivalent communication evidence"
                )
            )
        if 3 not in completed and (
            "sql_validation"
            not in unlocked
        ):
            missing.append(
                (
                    "Complete Applied Lab 03 "
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
        "required_datacamp_keys": datacamp_gate["required_keys"],
        "required_datacamp_names": datacamp_gate["required_names"],
        "missing_datacamp_keys": datacamp_gate["missing_keys"],
        "missing_datacamp_names": datacamp_gate["missing_names"],
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
        "total_items": len(CORE_APPLIED_LABS),
        "completed_items": len(
            set(completed).intersection(CORE_APPLIED_LABS)
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
            and active_number in CORE_APPLIED_LABS
            and active_number not in completed
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
                if number in CORE_APPLIED_LABS
                and number not in completed
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
            "total_items": len(CORE_APPLIED_LABS),
            "completed_items": len(
                set(completed).intersection(CORE_APPLIED_LABS)
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
    active_tracks = {
        int(row["task_id"]): str(row["track_key"])
        for row in conn.execute(
            "SELECT task_id,track_key FROM track_tasks"
        ).fetchall()
    }

    sql_lookup = {
        item[0]: item
        for item in SQL_COMPANION
    }

    rows = conn.execute(
        """SELECT
               s.id,s.week,s.sort_order,s.label,s.completed,
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

        # Google is the only adaptive track that does not have a separate
        # content-gate service. SQL, Portfolio, and Applied tasks must be
        # re-evaluated here even when they are currently linked as active.
        if active_tracks.get(task_id) == "google":
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
        explicit_missing = None
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
            if not readiness["ready"]:
                reason = (
                    "Unlock first: "
                    + "; ".join(readiness["missing"])
                )
            elif active_tracks.get(task_id) == "applied":
                # The adaptive track has selected this exact lab and every
                # content gate is satisfied. Do not immediately re-block the
                # active task with the generic branch-waiting message.
                reason = None
            else:
                reason = (
                    "Waiting for the Applied Labs "
                    "adaptive track to select this branch."
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
            reason = "Legacy external-learning task retired."

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
                readiness = sql_problem_readiness(
                    conn,
                    state,
                    title,
                )
                required = set(readiness["required_keys"])
                explicit_missing = list(readiness["missing_names"])

        elif (
            applied_number is None
            and row["category"] == "Portfolio"
        ):
            readiness = portfolio_task_readiness(
                conn,
                state,
                label,
            )
            required = set(readiness["required_skills"])
            explicit_missing = list(readiness["missing"])
            if readiness["execution_too_early"] and int(row["week"]) < 9:
                conn.execute(
                    "UPDATE sprint_tasks SET week=?,sort_order=? WHERE id=?",
                    (9, _next_sort_order(conn, 9, "portfolio"), task_id),
                )

        missing = (
            list(explicit_missing)
            if explicit_missing is not None
            else _missing_skill_names(
                required,
                unlocked,
            )
        )
        if missing:
            skill_reason = "Learn first: " + ", ".join(missing)
            reason = (
                reason + " " + skill_reason
                if reason
                else skill_reason
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

    active_tracks = {
        int(row["task_id"]): str(row["track_key"])
        for row in conn.execute(
            "SELECT task_id,track_key FROM track_tasks"
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
        if task_id in active_tracks:
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
    state = completion_contract.prepare_state(conn, state)
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
    allocations = completion_contract.deadline_allocations(
        conn,
        state,
        adaptive_targets(state, portfolio_ready=portfolio_ready),
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
            if track_key == "google":
                _remove_active_track_task(conn, track_key)
            else:
                conn.execute(
                    """DELETE FROM track_tasks
                       WHERE track_key=?""",
                    (track_key,),
                )
            _clear_target_schedule(conn, track_key)
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
            _clear_target_schedule(conn, track_key)
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
            _clear_target_schedule(conn, track_key)
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

        assigned_week = int(target.get("assigned_week", week))
        recommended_date = _ensure_target_schedule(
            conn,
            track_key=track_key,
            target_key=target["target_key"],
            week=assigned_week,
            weekly_target=allocations[track_key]["weekly_target"],
            weekly_completed=weekly[track_key],
        )
        due_now = recommended_date <= date.today()

        track_status = "Active"
        if (
            pace[track_key]["weekly_goal_complete"]
            and not due_now
        ):
            track_status = "Weekly Complete"
        elif (
            pace[track_key]["daily_goal_complete"]
            and not due_now
        ):
            track_status = "Daily Complete"

        target_metadata = dict(target["metadata"] or {})
        target_metadata["recommended_date"] = recommended_date.isoformat()
        target_metadata["due_today"] = recommended_date == date.today()
        target_metadata["overdue"] = recommended_date < date.today()

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
            metadata=target_metadata,
        )
        _ensure_task(
            conn,
            track_key=track_key,
            week=assigned_week,
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
            description=target.get("metadata", {}).get("description"),
            definition_of_done=target.get("metadata", {}).get("definition_of_done"),
            starter_path=target.get("metadata", {}).get("starter_path"),
            managed_key=target.get("metadata", {}).get("managed_key"),
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

    # Canonical DataCamp chapters are durable sprint tasks rather than active
    # track_tasks rows. Their chapter-progress record is the completion evidence
    # that prevents repair_track_links() from resetting a legitimate checkbox.
    metadata = conn.execute(
        "SELECT managed_key FROM task_metadata WHERE task_id=?",
        (int(task_id),),
    ).fetchone()
    managed_key = str(metadata["managed_key"] or "") if metadata is not None else ""

    # Managed DuckDB roadmap rows use negative sort orders and are intentionally
    # detached from the adaptive SQL track.  repair_track_links() must therefore
    # consult the exercise's durable completion records before treating a
    # completed row as a false completion.  Without this branch, every launch
    # reset the sprint row to incomplete even though the submitted exercise was
    # still completed in duckdb_exercise_progress / duckdb_completion_evidence.
    duckdb_number = None
    match = re.fullmatch(r"roadmap_v1026:duckdb:(\d+)", managed_key.casefold())
    if match:
        duckdb_number = int(match.group(1))
    if duckdb_number is None:
        duckdb_number = exercise_number_for_label(label)
    if duckdb_number is not None:
        progress = conn.execute(
            """SELECT 1
               FROM duckdb_exercise_progress
               WHERE exercise_number=? AND status='Completed'
               UNION ALL
               SELECT 1
               FROM duckdb_completion_evidence
               WHERE exercise_number=?
               LIMIT 1""",
            (int(duckdb_number), int(duckdb_number)),
        ).fetchone()
        if progress is not None:
            return True

    if managed_key.casefold().startswith("datacamp:"):
        chapter_key = managed_key.split(":", 1)[1]
        progress = conn.execute(
            """SELECT 1 FROM datacamp_chapter_progress
               WHERE chapter_key=? AND status='Completed'""",
            (chapter_key,),
        ).fetchone()
        if progress is not None:
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
               m.status,
               m.managed_key
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
        managed_key = str(row["managed_key"] or "")
        is_datacamp = managed_key.casefold().startswith("datacamp:")
        event_track = (
            event["track_key"]
            if event is not None
            else ("datacamp" if is_datacamp else None)
        )
        completed_date = (
            event["completed_date"]
            if event is not None
            else None
        )
        if is_datacamp:
            chapter_key = managed_key.split(":", 1)[1]
            chapter_row = conn.execute(
                """SELECT completed_date FROM datacamp_chapter_progress
                   WHERE chapter_key=? AND status='Completed'""",
                (chapter_key,),
            ).fetchone()
            if chapter_row is not None:
                completed_date = chapter_row["completed_date"] or completed_date

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
                    f"Learning Practice: "
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
                   m.category,
                   m.managed_key
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

    managed_key = (
        str(task_row["managed_key"] or "")
        if task_row is not None and "managed_key" in task_row.keys()
        else ""
    )
    is_datacamp_task = managed_key.casefold().startswith("datacamp:")
    track_key = (
        event["track_key"]
        if event is not None
        else (
            "datacamp"
            if is_datacamp_task
            else ("sql" if sql_title else None)
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

    if is_datacamp_task:
        from career_app.services import datacamp

        datacamp.mark_task_incomplete(
            conn,
            int(task_id),
            enforce_sequence=True,
        )

    if task_row is not None and not is_datacamp_task:
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
        # Canonical chapter progress was reset above. Reconcile after the
        # generic completion evidence is removed so every planning view agrees.
        pass

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
            "DELETE FROM duckdb_completion_evidence WHERE exercise_number=?",
            (duckdb_number,),
        )
        conn.execute(
            "DELETE FROM duckdb_task_validation WHERE exercise_number=?",
            (duckdb_number,),
        )
        conn.execute(
            """DELETE FROM evidence
               WHERE source_type='SQL Practice'
                 AND source_name=?""",
            (
                f"SQL Challenge "
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

    if is_datacamp_task:
        from career_app.services import datacamp

        datacamp.reconcile(conn)
    else:
        conn.commit()

    label = (
        task_row["label"]
        if task_row is not None
        else f"Learning Practice: {sql_title}"
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
               tt.target_key,
               m.managed_key
           FROM sprint_tasks s
           LEFT JOIN track_tasks tt
             ON tt.task_id=s.id
           LEFT JOIN task_metadata m
             ON m.task_id=s.id
           WHERE s.id=?""",
        (int(task_id),),
    ).fetchone()

    if row is None:
        return None

    track_key = row["track_key"]
    target_key = row["target_key"]
    managed_key = str(row["managed_key"] or "")
    if managed_key.casefold().startswith("datacamp:"):
        track_key = "datacamp"
        target_key = managed_key

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

    if str(track_key or "").casefold() == "datacamp" and str(target_key or "").startswith("datacamp:"):
        row = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key=?",
            (target_key,),
        ).fetchone()
        if row is not None:
            return int(row["task_id"])

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


def sql_problem_progress(conn, reference=None):
    """Return catalog-based SQL interview-problem progress.

    The consolidated Learning Practice catalog is the source of truth. This
    avoids stale program-state targets and excludes unrelated historical SQL
    rows from the visible progress meter.
    """
    titles = tuple(str(item[0]) for item in SQL_COMPANION)
    if not titles:
        return {
            "completed": 0,
            "target": 0,
            "weekly_completed": 0,
        }

    placeholders = ",".join("?" for _ in titles)
    completed = int(
        conn.execute(
            f"""SELECT COUNT(DISTINCT title)
                 FROM sql_practice
                 WHERE platform='DataLemur'
                   AND status='Completed'
                   AND title IN ({placeholders})""",
            titles,
        ).fetchone()[0]
        or 0
    )

    reference_day = reference or date.today()
    if isinstance(reference_day, str):
        reference_day = date.fromisoformat(reference_day)
    week_start = reference_day - timedelta(days=reference_day.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_completed = int(
        conn.execute(
            f"""SELECT COUNT(DISTINCT title)
                 FROM sql_practice
                 WHERE platform='DataLemur'
                   AND status='Completed'
                   AND completed_date BETWEEN ? AND ?
                   AND title IN ({placeholders})""",
            (week_start.isoformat(), week_end.isoformat(), *titles),
        ).fetchone()[0]
        or 0
    )
    return {
        "completed": completed,
        "target": len(titles),
        "weekly_completed": weekly_completed,
    }


def focus_presentation(conn, item):
    """Build one uniform Today’s Focus title and detail."""
    category = str(
        item.get("category")
        or "General"
    )
    label = _clean_focus_text(
        item.get("label")
    )
    task_id = _coerce_task_id(item.get("task_id"))

    if item.get("roadmap_fallback"):
        # Unified roadmap items should stay actionable on the dashboard.
        # The task label is the primary title; a concise action reason belongs
        # on the supporting line.
        title = label or item.get(
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

        task_description = ""
        if task_id is not None:
            detail_row = conn.execute(
                "SELECT description FROM task_metadata WHERE task_id=?",
                (int(task_id),),
            ).fetchone()
            if detail_row is not None:
                task_description = _clean_focus_text(
                    detail_row["description"]
                )

        source = _clean_focus_text(
            item.get("display_source")
            or item.get("source_label")
            or category
        )
        # The task title already provides the destination context. Keep the
        # visible supporting line concise and action-oriented; use the source
        # only as a fallback when no useful detail exists.
        reason = _clean_focus_text(
            item.get("detail")
            or task_description
            or label
        )
        return {
            "style_category": category,
            "title": title,
            "detail": reason or source or label,
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

    task_description = ""
    if task_id is not None:
        detail_row = conn.execute(
            "SELECT description FROM task_metadata WHERE task_id=?",
            (int(task_id),),
        ).fetchone()
        if detail_row is not None:
            task_description = _clean_focus_text(detail_row["description"])

    return {
        "style_category": display_category,
        "title": title,
        "detail": " • ".join(
            [task_description or label, *metadata]
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

    # Completion controls are guarded in the UI, but the track service is the
    # final authority.  Enforce the same prerequisite contract here so a stale
    # checkbox, deep link, or alternate workspace cannot bypass a lockout.
    if track_key == "sql":
        title = str(link["target_key"] or "").split("problem:", 1)[-1].strip()
        readiness = sql_problem_readiness(conn, state, title)
        already_completed = conn.execute(
            "SELECT 1 FROM sql_practice WHERE platform='DataLemur' AND title=? AND status='Completed'",
            (title,),
        ).fetchone()
        if not readiness["ready"] and already_completed is None:
            raise PermissionError(
                "This SQL interview problem is locked. Complete "
                + ", ".join(readiness["missing_names"])
                + " first."
            )
    elif track_key == "portfolio":
        project_task = None
        if link["linked_entity_id"] is not None:
            project_task = conn.execute(
                "SELECT label,stage FROM project_tasks WHERE id=?",
                (int(link["linked_entity_id"]),),
            ).fetchone()
        project_label = str(project_task["label"] if project_task else label)
        project_stage = str(project_task["stage"] if project_task else "")
        readiness = portfolio_task_readiness(
            conn,
            state,
            project_label,
            project_stage,
        )
        if not readiness["ready"]:
            raise PermissionError(
                "This portfolio milestone is locked. Complete "
                + ", ".join(readiness["missing"])
                + " first."
            )

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

    datacamp_row = _state_row(conn, "datacamp")
    if datacamp_row is not None:
        try:
            datacamp_metadata = json.loads(datacamp_row["metadata"] or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            datacamp_metadata = {}
        result["datacamp"] = {
            "track_key": "datacamp",
            "display_name": "DataCamp",
            "position": int(datacamp_row["position"]),
            "subposition": int(datacamp_row["subposition"]),
            "weekly_target": int(datacamp_row["weekly_target"]),
            "weekly_completed": int(datacamp_metadata.get("weekly_completed", 0)),
            "status": datacamp_row["status"],
            "metadata": datacamp_metadata,
            "task_id": None,
            "task_label": datacamp_metadata.get("next_chapter"),
            "source_label": datacamp_metadata.get("next_course"),
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
        5: {"analysis_foundations"},
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
                f"SQL Challenge {duckdb_roadmap_number(number):02d}: {exercise['title']} in progress",
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
            "required_all_of": [],
            "required_any_of": [],
            "missing_keys": [],
            "missing_names": [
                "Problem is not in the SQL catalog"
            ],
        }

    unlocked = _derived_skills(
        conn,
        state,
    )
    groups = _sql_requirement_groups(title, item[2])
    required = set(groups["all_of"]) | set(groups["any_of"])
    missing_all = set(groups["all_of"]) - set(unlocked)
    missing_any = set()
    if groups["any_of"] and not (set(groups["any_of"]) & set(unlocked)):
        missing_any = set(groups["any_of"])
    missing = missing_all | missing_any
    completed_problems = _completed_sql(conn)
    required_problem_titles = list(SQL_PROBLEM_PREREQUISITES.get(title, ()))
    missing_problem_titles = [
        problem_title
        for problem_title in required_problem_titles
        if problem_title not in completed_problems
    ]
    missing_names = [
        SKILL_DEFINITIONS[key][0]
        for key in sorted(missing_all)
    ]
    if missing_any:
        missing_names.append(
            "One of: "
            + " or ".join(
                SKILL_DEFINITIONS[key][0]
                for key in sorted(missing_any)
            )
        )
    missing_names.extend(
        f"SQL Interview Problem: {problem_title}"
        for problem_title in missing_problem_titles
    )

    datacamp_gate = content_gates.gate_status(
        conn,
        content_gates.requirements_for_sql_problem(
            required,
            roadmap_week=SQL_PROBLEM_WEEK.get(title),
        ),
    )
    if not datacamp_gate["ready"]:
        missing_names.append(datacamp_gate["summary"])

    problem_week = int(SQL_PROBLEM_WEEK.get(title) or 1)
    prior_check_ready = problem_week <= 1 or weekly_checks.passed(conn, problem_week - 1)
    if not prior_check_ready:
        missing_names.append(f"Pass {weekly_checks.title(problem_week - 1)}")

    evidence_map = _skill_evidence(conn, state)

    return {
        "ready": (
            not missing
            and not missing_problem_titles
            and datacamp_gate["ready"]
            and prior_check_ready
        ),
        "required_keys": sorted(required),
        "required_names": [
            SKILL_DEFINITIONS[key][0]
            for key in sorted(required)
        ],
        "required_all_of": sorted(groups["all_of"]),
        "required_any_of": sorted(groups["any_of"]),
        "missing_keys": sorted(missing),
        "missing_names": missing_names,
        "missing_all_of": sorted(missing_all),
        "missing_any_of": sorted(missing_any),
        "required_problem_titles": required_problem_titles,
        "missing_problem_titles": missing_problem_titles,
        "required_datacamp_keys": datacamp_gate["required_keys"],
        "required_datacamp_names": datacamp_gate["required_names"],
        "missing_datacamp_keys": datacamp_gate["missing_keys"],
        "missing_datacamp_names": datacamp_gate["missing_names"],
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
        if state is not None:
            readiness = sql_problem_readiness(conn, state, title)
            if not readiness["ready"]:
                continue
            if int(SQL_PROBLEM_WEEK.get(title, 99)) > int(state["current_week"]):
                continue
        else:
            groups = _sql_requirement_groups(title, item[2])
            if not set(groups["all_of"]).issubset(unlocked):
                continue
            if groups["any_of"] and not (set(groups["any_of"]) & set(unlocked)):
                continue
        titles.append(title)
        if len(titles) >= max(
            1,
            int(limit),
        ):
            break

    return titles
