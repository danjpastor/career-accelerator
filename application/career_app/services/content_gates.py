from __future__ import annotations

"""Explicit DataCamp prerequisites for every gated learning surface.

Skill evidence remains useful for explaining *why* a learner is ready, but it
must not allow another activity to bypass the assigned DataCamp curriculum.
This module is the single source for the chapter tasks required by DuckDB,
SQL interview practice, Applied Labs, and portfolio milestones.
"""

from collections.abc import Iterable
import sqlite3

from career_app.data.datacamp_curriculum import (
    CHAPTER_BY_KEY,
    DATACAMP_CHAPTERS,
    DataCampChapter,
)


_CHAPTER_INDEX = {chapter.key: index for index, chapter in enumerate(DATACAMP_CHAPTERS)}
_ALL_KEYS = tuple(chapter.key for chapter in DATACAMP_CHAPTERS)


def _ordered(keys: Iterable[str]) -> tuple[str, ...]:
    unique = {str(key) for key in keys if str(key) in CHAPTER_BY_KEY}
    return tuple(sorted(unique, key=lambda key: _CHAPTER_INDEX[key]))


def chapters_before_week(week: int) -> tuple[str, ...]:
    return tuple(chapter.key for chapter in DATACAMP_CHAPTERS if chapter.week < int(week))


def chapters_through(chapter_key: str) -> tuple[str, ...]:
    index = _CHAPTER_INDEX.get(str(chapter_key))
    if index is None:
        return ()
    return tuple(chapter.key for chapter in DATACAMP_CHAPTERS[: index + 1])


def all_required_chapters() -> tuple[str, ...]:
    return _ALL_KEYS


# A skill may have several accepted evidence sources, but these chapter gates
# are mandatory when that skill is used to unlock new content.
SKILL_TERMINAL_CHAPTER = {
    "analytics_foundations": "w01_intro_sheets_01",
    "business_framing": "w01_analysis_sheets_01",
    "data_preparation": "w01_analysis_sheets_02",
    "data_cleaning": "w05_functions_sql_03",
    "analysis_foundations": "w01_analysis_sheets_03",
    "visualization_foundations": "w07_visual_powerbi_01",
    "data_storytelling": "w07_churn_powerbi_03",
    "portfolio_delivery": "w08_pandas_04",
    "career_readiness": "w08_pandas_04",
    "excel_analytics": "w02_pivot_sheets_04",
    "power_query": "w07_prep_powerbi_04",
    "dimensional_modeling": "w07_model_powerbi_04",
    "dax_measures": "w07_dax_powerbi_03",
    "report_design": "w07_visual_powerbi_04",
    "power_bi_foundations": "w07_intro_powerbi_04",
    "power_bi": "w07_churn_powerbi_03",
    "power_bi_governance": "w07_churn_powerbi_03",
    "python_pandas": "w08_pandas_04",
    "analyst_communication": "w07_churn_powerbi_03",
    "analysis_governance": "w06_database_design_04",
    "sql_fundamentals": "w03_intro_sql_02",
    "sql_querying": "w03_intro_sql_02",
    "sql_aggregation": "w03_intermediate_sql_04",
    "sql_case": "w04_manipulation_sql_01",
    "sql_joins": "w04_joining_sql_03",
    "sql_subqueries": "w04_manipulation_sql_02",
    "sql_ctes": "w04_manipulation_sql_03",
    "sql_intermediate": "w04_manipulation_sql_03",
    "sql_window_functions": "w05_window_sql_03",
    "sql_date_logic": "w05_functions_sql_02",
    "sql_validation": "w06_database_design_04",
    "diagnostic_reasoning": "w06_database_design_04",
    "timed_analysis": "w06_database_design_04",
    "statistics_foundations": "w08_intro_python_04",
    "descriptive_statistics": "w08_intermediate_python_01",
    "sampling_bias": "w08_intermediate_python_05",
    "confidence_intervals": "w08_intermediate_python_05",
    "inferential_statistics": "w08_intermediate_python_05",
    "hypothesis_testing": "w08_intermediate_python_05",
    "experiment_analysis": "w08_intermediate_python_05",
    "causal_reasoning": "w08_intermediate_python_05",
    "regression_interpretation": "w08_pandas_04",
    "funnel_analysis": "w06_database_design_04",
    "cohort_analysis": "w06_database_design_04",
    "churn_analysis": "w07_churn_powerbi_03",
    "variance_analysis": "w08_pandas_04",
    "api_ingestion": "w08_pandas_01",
    "data_pipeline": "w08_pandas_04",
    "data_lineage": "w08_pandas_04",
    "ai_validation": "w08_pandas_04",
    "power_bi_performance": "w07_churn_powerbi_03",
    "roadmap.spreadsheet_mastery": "w02_pivot_sheets_04",
    "roadmap.sql_mastery": "w06_database_design_04",
    "roadmap.power_bi_mastery": "w07_churn_powerbi_03",
    "roadmap.portfolio_readiness": "w08_pandas_04",
}


# The terminal chapter is the last chapter that must be complete for that lab.
# chapters_through() deliberately includes all earlier assigned DataCamp work,
# ensuring a lab cannot leapfrog previous weeks.
APPLIED_LAB_TERMINAL_CHAPTER = {14: 'w07_prep_powerbi_02',
 15: 'w07_prep_powerbi_04',
 18: 'w07_model_powerbi_04',
 19: 'w07_dax_powerbi_03',
 25: 'w07_churn_powerbi_03',
 26: 'w07_churn_powerbi_03',
 1: 'w02_pivot_sheets_04',
 20: 'w08_intermediate_python_02',
 21: 'w08_pandas_01',
 30: 'w08_pandas_02',
 31: 'w08_pandas_04',
 8: 'w04_manipulation_sql_04',
 27: 'w07_churn_powerbi_03',
 34: 'w08_pandas_04',
 3: 'w04_manipulation_sql_03',
 4: 'w04_joining_sql_03',
 7: 'w05_functions_sql_02',
 10: 'w06_database_design_04',
 11: 'w06_database_design_04',
 32: 'w08_pandas_04',
 35: 'w08_pandas_04',
 2: 'w03_intermediate_sql_04',
 5: 'w04_manipulation_sql_04',
 9: 'w05_functions_sql_02',
 12: 'w06_database_design_04',
 16: 'w07_churn_powerbi_03',
 22: 'w08_pandas_04',
 28: 'w08_pandas_04',
 6: 'w04_manipulation_sql_03',
 13: 'w06_database_design_04',
 17: 'w07_churn_powerbi_03',
 23: 'w08_pandas_04',
 24: 'w08_pandas_01',
 29: 'w08_pandas_04',
 33: 'w08_pandas_04',
 36: 'w07_churn_powerbi_03'}


DUCKDB_TERMINAL_CHAPTER = {
    1: "w03_intro_sql_02",
    2: "w03_intermediate_sql_03",
    3: "w04_manipulation_sql_01",
    4: "w04_manipulation_sql_01",
    5: "w04_manipulation_sql_01",
    6: "w04_joining_sql_02",
    7: "w04_manipulation_sql_03",
    8: "w05_window_sql_04",
    9: "w06_database_design_04",
    10: "w08_pandas_04",
    11: "w05_window_sql_02",
    12: "w04_manipulation_sql_03",
    13: "w04_joining_sql_02",
    14: "w05_functions_sql_02",
    15: "w05_window_sql_03",
    16: "w04_joining_sql_03",
    17: "w05_functions_sql_03",
    18: "w06_database_design_04",
}


def requirements_for_skills(skill_keys: Iterable[str]) -> tuple[str, ...]:
    keys: list[str] = []
    for skill in skill_keys:
        terminal = SKILL_TERMINAL_CHAPTER.get(str(skill))
        if terminal:
            keys.extend(chapters_through(terminal))
    return _ordered(keys)


def requirements_for_applied_lab(number: int) -> tuple[str, ...]:
    terminal = APPLIED_LAB_TERMINAL_CHAPTER.get(int(number))
    return chapters_through(terminal) if terminal else ()


def requirements_for_duckdb(number: int) -> tuple[str, ...]:
    terminal = DUCKDB_TERMINAL_CHAPTER.get(int(number))
    return chapters_through(terminal) if terminal else ()


def requirements_for_sql_problem(
    required_skill_keys: Iterable[str],
    *,
    roadmap_week: int | None = None,
) -> tuple[str, ...]:
    keys = list(requirements_for_skills(required_skill_keys))
    if roadmap_week is not None:
        keys.extend(chapters_before_week(int(roadmap_week)))
    return _ordered(keys)


def requirements_for_portfolio(
    required_skill_keys: Iterable[str],
    *,
    execution: bool,
) -> tuple[str, ...]:
    if execution or "roadmap.portfolio_readiness" in set(required_skill_keys):
        return all_required_chapters()
    return requirements_for_skills(required_skill_keys)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def completed_chapter_keys(conn: sqlite3.Connection) -> set[str]:
    if not _table_exists(conn, "datacamp_chapter_progress"):
        return set()
    return {
        str(row["chapter_key"])
        for row in conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress WHERE status='Completed'"
        ).fetchall()
    }


def chapter_name(chapter_key: str) -> str:
    chapter = CHAPTER_BY_KEY.get(str(chapter_key))
    if chapter is None:
        return str(chapter_key)
    return (
        f"{chapter.course_name} — Chapter {chapter.chapter_number}: "
        f"{chapter.chapter_name}"
    )


def gate_status(conn: sqlite3.Connection, required_keys: Iterable[str]) -> dict:
    required = _ordered(required_keys)
    completed = completed_chapter_keys(conn)
    missing = tuple(key for key in required if key not in completed)
    required_names = [chapter_name(key) for key in required]
    missing_names = [chapter_name(key) for key in missing]
    if not missing_names:
        summary = ""
    elif len(missing_names) == 1:
        summary = f"DataCamp: {missing_names[0]}"
    else:
        summary = f"DataCamp: {missing_names[0]} (+{len(missing_names) - 1} more chapter tasks)"
    return {
        "ready": not missing,
        "required_keys": list(required),
        "required_names": required_names,
        "missing_keys": list(missing),
        "missing_names": missing_names,
        "summary": summary,
    }


def audit_contract() -> list[str]:
    """Return static configuration errors without opening the learner database."""
    errors: list[str] = []
    unknown_skill_terminals = {
        value for value in SKILL_TERMINAL_CHAPTER.values() if value not in CHAPTER_BY_KEY
    }
    if unknown_skill_terminals:
        errors.append(f"Unknown skill terminal chapters: {sorted(unknown_skill_terminals)}")

    unknown_lab_terminals = {
        value for value in APPLIED_LAB_TERMINAL_CHAPTER.values() if value not in CHAPTER_BY_KEY
    }
    if unknown_lab_terminals:
        errors.append(f"Unknown Applied Lab terminal chapters: {sorted(unknown_lab_terminals)}")

    unknown_duckdb_terminals = {
        value for value in DUCKDB_TERMINAL_CHAPTER.values() if value not in CHAPTER_BY_KEY
    }
    if unknown_duckdb_terminals:
        errors.append(f"Unknown DuckDB terminal chapters: {sorted(unknown_duckdb_terminals)}")

    if set(APPLIED_LAB_TERMINAL_CHAPTER) != set(range(1, 37)):
        missing = sorted(set(range(1, 37)) - set(APPLIED_LAB_TERMINAL_CHAPTER))
        extra = sorted(set(APPLIED_LAB_TERMINAL_CHAPTER) - set(range(1, 37)))
        errors.append(f"Applied Lab chapter map mismatch; missing={missing}, extra={extra}")

    if set(DUCKDB_TERMINAL_CHAPTER) != set(range(1, 19)):
        missing = sorted(set(range(1, 19)) - set(DUCKDB_TERMINAL_CHAPTER))
        extra = sorted(set(DUCKDB_TERMINAL_CHAPTER) - set(range(1, 19)))
        errors.append(f"DuckDB chapter map mismatch; missing={missing}, extra={extra}")

    # Lab 01 is the Google Sheets gate and requires all Week 1–2 spreadsheet chapters.
    expected_lab_07 = {
        chapter.key for chapter in DATACAMP_CHAPTERS if chapter.week in {1, 2}
    }
    actual_lab_01 = set(requirements_for_applied_lab(1))
    if expected_lab_07 != actual_lab_01:
        errors.append("Applied Lab 01 does not require every Week 1–2 DataCamp spreadsheet chapter.")

    return errors
