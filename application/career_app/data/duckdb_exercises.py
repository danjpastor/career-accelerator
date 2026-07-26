from __future__ import annotations

import re

DUCKDB_EXERCISES = {1: {'week': 3,
     'slug': '01_select_filter_sort_limit',
     'title': 'Filter and sort support tickets',
     'concepts': 'SELECT, FROM, WHERE, ORDER BY, LIMIT',
     'minutes': 35,
     'priority': 3,
     'old_label': 'Practice SELECT, FROM, WHERE, ORDER BY, and LIMIT',
     'label': 'Complete DuckDB Exercise 01: Filter and sort support tickets',
     'prerequisites': {'all_of': ['sql_querying'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery'],
                       'prior_exercises': []}},
 2: {'week': 3,
     'slug': '02_aggregations_grouping_having',
     'title': 'Summarize retail orders',
     'concepts': 'COUNT, SUM, AVG, GROUP BY, HAVING',
     'minutes': 40,
     'priority': 3,
     'old_label': 'Practice COUNT, SUM, AVG, GROUP BY, and HAVING',
     'label': 'Complete DuckDB Exercise 02: Summarize retail orders',
     'prerequisites': {'all_of': ['sql_aggregation'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery'],
                       'prior_exercises': [1]}},
 3: {'week': 5,
     'slug': '03_nulls_case_cleaning',
     'title': 'Clean customer feedback',
     'concepts': 'NULLIF, TRIM, COALESCE, TRY_CAST, CASE',
     'minutes': 45,
     'priority': 3,
     'old_label': 'Practice NULL handling and CASE-based cleaning',
     'label': 'Complete DuckDB Exercise 03: Clean customer feedback',
     'prerequisites': {'all_of': ['sql_case', 'data_cleaning'],
                       'any_of': ['sql_ctes', 'sql_subqueries'],
                       'mastery_checks': ['week_2_spreadsheet_mastery', 'week_4_relationships_joins'],
                       'prior_exercises': [2]}},
 4: {'week': 4,
     'slug': '04_business_metrics',
     'title': 'Calculate subscription KPIs',
     'concepts': 'ratios, conditional aggregation, date filters',
     'minutes': 45,
     'priority': 1,
     'old_label': 'Practice business-metric calculations in SQL',
     'label': 'Complete DuckDB Exercise 04: Calculate subscription KPIs',
     'prerequisites': {'all_of': ['sql_aggregation', 'sql_date_logic', 'sql_case'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery', 'week_3_sql_foundations'],
                       'prior_exercises': [2]}},
 5: {'week': 3,
     'slug': '05_case_grouped_summaries',
     'title': 'Segment service performance',
     'concepts': 'CASE expressions, SLA logic, grouped summaries',
     'minutes': 40,
     'priority': 3,
     'old_label': 'Practice CASE expressions and grouped summaries',
     'label': 'Complete DuckDB Exercise 05: Segment service performance',
     'prerequisites': {'all_of': ['sql_aggregation', 'sql_case'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery'],
                       'prior_exercises': [2]}},
 6: {'week': 4,
     'slug': '06_joins',
     'title': 'Join customers, orders, and payments',
     'concepts': 'INNER JOIN, LEFT JOIN, multi-table joins',
     'minutes': 45,
     'priority': 3,
     'old_label': 'Practice INNER, LEFT, and multi-table joins',
     'label': 'Complete DuckDB Exercise 06: Join customers, orders, and payments',
     'prerequisites': {'all_of': ['sql_joins', 'sql_validation'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery', 'week_3_sql_foundations'],
                       'prior_exercises': [1, 2]}},
 7: {'week': 5,
     'slug': '07_ctes_subqueries',
     'title': 'Analyze order profitability',
     'concepts': 'subqueries, CTEs, layered analysis',
     'minutes': 50,
     'priority': 3,
     'old_label': 'Practice subqueries and common table expressions',
     'label': 'Complete DuckDB Exercise 07: Analyze order profitability',
     'prerequisites': {'all_of': ['sql_aggregation'],
                       'any_of': ['sql_ctes', 'sql_subqueries'],
                       'mastery_checks': ['week_2_spreadsheet_mastery', 'week_4_relationships_joins'],
                       'prior_exercises': [4, 6]}},
 8: {'week': 6,
     'slug': '08_vfx_production_snapshot',
     'title': 'Analyze a VFX production snapshot',
     'concepts': 'joins, CTEs, CASE, window functions, business interpretation',
     'minutes': 60,
     'priority': 1,
     'old_label': 'Complete the VFX production SQL challenge',
     'label': 'Complete DuckDB Exercise 08: Analyze a VFX production snapshot',
     'prerequisites': {'all_of': ['sql_joins', 'sql_ctes', 'sql_window_functions', 'sql_validation'],
                       'any_of': [],
                       'mastery_checks': ['week_2_spreadsheet_mastery', 'week_5_cleaning_ctes'],
                       'prior_exercises': [3, 4, 5, 6, 7, 12]}},
 9: {'week': 7,
     'slug': '09_timed_product_challenge',
     'title': 'Timed product challenge',
     'concepts': 'timed SQL analysis, joins, CTEs, business metrics',
     'minutes': 50,
     'priority': 2,
     'old_label': 'Complete the timed DuckDB product challenge',
     'label': 'Complete DuckDB Exercise 09: Timed product challenge',
     'prerequisites': {'all_of': ['roadmap.sql_mastery'],
                       'any_of': [],
                       'mastery_checks': ['week_6_sql_mastery'],
                       'prior_exercises': [8]}},
 10: {'week': 8,
      'slug': '10_mixed_workforce_assessment',
      'title': 'Mixed workforce assessment',
      'concepts': 'joins, CTEs, window functions, QA, explanation',
      'minutes': 60,
      'priority': 2,
      'old_label': 'Complete the mixed DuckDB workforce assessment',
      'label': 'Complete DuckDB Exercise 10: Mixed workforce assessment',
      'prerequisites': {'all_of': ['roadmap.sql_mastery'],
                        'any_of': [],
                        'mastery_checks': ['week_6_sql_mastery', 'week_7_power_bi_mastery'],
                        'prior_exercises': [8, 9, 11]}},
 11: {'week': 6,
      'slug': '11_explain_joins_windows',
      'title': 'Explain joins and window functions',
      'concepts': 'join reasoning, window reasoning, analyst communication',
      'minutes': 45,
      'priority': 2,
      'old_label': 'Explain joins and window functions in DuckDB',
      'label': 'Complete DuckDB Exercise 11: Explain joins and window functions',
      'prerequisites': {'all_of': ['sql_joins', 'sql_window_functions', 'analyst_communication'],
                        'any_of': [],
                        'mastery_checks': ['week_5_cleaning_ctes'],
                        'prior_exercises': [6]}},
 12: {'week': 5,
      'slug': '12_query_refactor',
      'title': 'Refactor an unreadable analytics query',
      'concepts': 'CTEs, aliases, formatting, validation',
      'minutes': 45,
      'priority': 2,
      'old_label': 'Refactor an unreadable DuckDB query',
      'label': 'Complete DuckDB Exercise 12: Refactor an unreadable analytics query',
      'prerequisites': {'all_of': ['sql_ctes', 'sql_validation'],
                        'any_of': [],
                        'mastery_checks': ['week_4_relationships_joins'],
                        'prior_exercises': [7]}}}


def exercise_number_for_label(label):
    text = str(label or "").strip()
    for number, item in DUCKDB_EXERCISES.items():
        if text in {item["label"], item["old_label"]}:
            return number
    match = re.search(r"DuckDB Exercise\s+(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match and int(match.group(1)) in DUCKDB_EXERCISES else None


def exercise_for_label(label):
    number = exercise_number_for_label(label)
    return DUCKDB_EXERCISES.get(number) if number is not None else None


def exercise_source(value):
    """Return the display source for a DuckDB exercise label or number.

    Dashboard routing asks this helper about every task label.  Non-DuckDB
    labels must therefore return ``None`` instead of being coerced with
    ``int(...)``.
    """
    number = None
    if isinstance(value, int):
        number = value
    else:
        text = str(value or "").strip()
        if text.isdigit():
            number = int(text)
        else:
            number = exercise_number_for_label(text)
    if number not in DUCKDB_EXERCISES:
        return None
    item = DUCKDB_EXERCISES[number]
    return f"DuckDB Exercise {number:02d}: {item['title']}"
