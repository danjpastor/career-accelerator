from __future__ import annotations

import re

DUCKDB_EXERCISES = {
    1: {
        "week": 1,
        "slug": '01_select_filter_sort_limit',
        "title": 'Filter and sort support tickets',
        "concepts": 'SELECT, FROM, WHERE, ORDER BY, LIMIT',
        "minutes": 35,
        "priority": 3,
        "old_label": 'Practice SELECT, FROM, WHERE, ORDER BY, and LIMIT',
        "label": 'Complete DuckDB Exercise 01: Filter and sort support tickets',
    },
    2: {
        "week": 2,
        "slug": '02_aggregations_grouping_having',
        "title": 'Summarize retail orders',
        "concepts": 'COUNT, SUM, AVG, GROUP BY, HAVING',
        "minutes": 40,
        "priority": 3,
        "old_label": 'Practice COUNT, SUM, AVG, GROUP BY, and HAVING',
        "label": 'Complete DuckDB Exercise 02: Summarize retail orders',
    },
    3: {
        "week": 4,
        "slug": '03_nulls_case_cleaning',
        "title": 'Clean customer feedback',
        "concepts": 'NULLIF, TRIM, COALESCE, TRY_CAST, CASE',
        "minutes": 45,
        "priority": 3,
        "old_label": 'Practice NULL handling and CASE-based cleaning',
        "label": 'Complete DuckDB Exercise 03: Clean customer feedback',
    },
    4: {
        "week": 5,
        "slug": '04_business_metrics',
        "title": 'Calculate subscription KPIs',
        "concepts": 'ratios, conditional aggregation, date filters',
        "minutes": 45,
        "priority": 1,
        "old_label": 'Practice business-metric calculations in SQL',
        "label": 'Complete DuckDB Exercise 04: Calculate subscription KPIs',
    },
    5: {
        "week": 5,
        "slug": '05_case_grouped_summaries',
        "title": 'Segment service performance',
        "concepts": 'CASE expressions, SLA logic, grouped summaries',
        "minutes": 40,
        "priority": 3,
        "old_label": 'Practice CASE expressions and grouped summaries',
        "label": 'Complete DuckDB Exercise 05: Segment service performance',
    },
    6: {
        "week": 6,
        "slug": '06_joins',
        "title": 'Join customers, orders, and payments',
        "concepts": 'INNER JOIN, LEFT JOIN, multi-table joins',
        "minutes": 45,
        "priority": 3,
        "old_label": 'Practice INNER, LEFT, and multi-table joins',
        "label": 'Complete DuckDB Exercise 06: Join customers, orders, and payments',
    },
    7: {
        "week": 6,
        "slug": '07_ctes_subqueries',
        "title": 'Analyze order profitability',
        "concepts": 'subqueries, CTEs, multi-step analysis',
        "minutes": 50,
        "priority": 3,
        "old_label": 'Practice CTEs and subqueries',
        "label": 'Complete DuckDB Exercise 07: Analyze order profitability',
    },
    8: {
        "week": 9,
        "slug": '08_integrated_vfx_review',
        "title": 'Analyze a VFX production snapshot',
        "concepts": 'filtering, joins, aggregation, CASE, CTEs, ranking',
        "minutes": 60,
        "priority": 1,
        "old_label": 'Complete an integrated SQL review session',
        "label": 'Complete DuckDB Exercise 08: Analyze a VFX production snapshot',
    },
    9: {
        "week": 11,
        "slug": '09_timed_sql_challenge',
        "title": 'Complete a 30-minute product challenge',
        "concepts": 'timed aggregation, joins, CASE, CTEs',
        "minutes": 30,
        "priority": 1,
        "old_label": 'Complete one timed SQL practice set',
        "label": 'Complete DuckDB Exercise 09: 30-minute product challenge',
    },
    10: {
        "week": 12,
        "slug": '10_mixed_sql_assessment',
        "title": 'Complete a mixed workforce assessment',
        "concepts": 'NULLs, joins, aggregation, CTEs, ranking',
        "minutes": 45,
        "priority": 1,
        "old_label": 'Complete a mixed timed SQL review',
        "label": 'Complete DuckDB Exercise 10: Mixed workforce assessment',
    },
    11: {
        "week": 12,
        "slug": '11_explain_joins_windows',
        "title": 'Explain joins and window functions',
        "concepts": 'LEFT JOIN, ROW_NUMBER, DENSE_RANK, rolling averages',
        "minutes": 45,
        "priority": 3,
        "old_label": 'Practice explaining joins and window functions',
        "label": 'Complete DuckDB Exercise 11: Explain joins and window functions',
    },
    12: {
        "week": 6,
        "slug": '12_query_readability',
        "title": 'Refactor an unreadable analytics query',
        "concepts": 'aliases, formatting, comments, CTE refactoring',
        "minutes": 30,
        "priority": 3,
        "old_label": 'Review every query for readability',
        "label": 'Complete DuckDB Exercise 12: Refactor an analytics query',
    },
}

EXERCISE_PATTERN = re.compile(
    r"^Complete DuckDB Exercise (\d{2}):",
    re.IGNORECASE,
)


def exercise_number_for_label(label):
    text = str(label or "").strip()
    match = EXERCISE_PATTERN.match(text)
    if match:
        number = int(match.group(1))
        return number if number in DUCKDB_EXERCISES else None

    for number, exercise in DUCKDB_EXERCISES.items():
        if text in {exercise["old_label"], exercise["label"]}:
            return number
    return None


def exercise_for_label(label):
    number = exercise_number_for_label(label)
    return DUCKDB_EXERCISES.get(number) if number is not None else None


def exercise_source(label):
    exercise = exercise_for_label(label)
    if exercise is None:
        return None
    number = next(
        key
        for key, value in DUCKDB_EXERCISES.items()
        if value is exercise
    )
    return (
        f"DuckDB Practice • Exercise {number:02d} • "
        f"practice/duckdb/exercises/{exercise['slug']}"
    )
