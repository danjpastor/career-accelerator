from __future__ import annotations

import re

from career_app.data.sql_challenge_practice import exercises as _challenge_exercises

# Stable internal IDs preserve existing progress, managed task keys, and submission ownership.
_DUCKDB_ROADMAP_INTERNAL_ORDER = (1, 19, 20, 2, 21, 6, 22, 16, 13, 23, 5, 7, 12, 24, 25, 26, 15, 11, 27, 28, 14, 4, 3, 17, 29, 30, 31, 32, 33, 8, 9, 10, 18)
DUCKDB_ROADMAP_NUMBER_BY_ID = {
    internal_id: display_number
    for display_number, internal_id in enumerate(_DUCKDB_ROADMAP_INTERNAL_ORDER, start=1)
}
DUCKDB_ID_BY_ROADMAP_NUMBER = {
    display_number: internal_id
    for internal_id, display_number in DUCKDB_ROADMAP_NUMBER_BY_ID.items()
}
_LEGACY_LABELS_BY_ID = {1: ['Complete DuckDB Exercise 01: Filter and sort support tickets', 'Practice SELECT, FROM, WHERE, ORDER BY, and LIMIT'], 2: ['Complete DuckDB Exercise 02: Summarize retail orders', 'Practice COUNT, SUM, AVG, GROUP BY, and HAVING'], 3: ['Complete DuckDB Exercise 16: Clean customer feedback', 'Practice NULL handling and CASE-based cleaning', 'Complete DuckDB Exercise 03: Clean customer feedback'], 4: ['Complete DuckDB Exercise 06: Calculate subscription KPIs', 'Practice business-metric calculations in SQL', 'Complete DuckDB Exercise 04: Calculate subscription KPIs'], 5: ['Complete DuckDB Exercise 07: Segment service performance', 'Practice CASE expressions and grouped summaries', 'Complete DuckDB Exercise 05: Segment service performance'], 6: ['Complete DuckDB Exercise 08: Join customers, orders, and payments', 'Practice INNER, LEFT, and multi-table joins', 'Complete DuckDB Exercise 06: Join customers, orders, and payments'], 7: ['Complete DuckDB Exercise 09: Analyze order profitability', 'Practice subqueries and common table expressions', 'Complete DuckDB Exercise 07: Analyze order profitability'], 8: ['Complete DuckDB Exercise 25: Analyze a VFX production snapshot', 'Complete the VFX production SQL challenge', 'Complete DuckDB Exercise 08: Analyze a VFX production snapshot'], 9: ['Complete DuckDB Exercise 26: Timed product challenge', 'Complete the timed DuckDB product challenge', 'Complete DuckDB Exercise 09: Timed product challenge'], 10: ['Complete DuckDB Exercise 27: Mixed workforce assessment', 'Complete the mixed DuckDB workforce assessment', 'Complete DuckDB Exercise 10: Mixed workforce assessment'], 11: ['Complete DuckDB Exercise 17: Explain joins and window functions', 'Explain joins and window functions in DuckDB', 'Complete DuckDB Exercise 11: Explain joins and window functions'], 12: ['Complete DuckDB Exercise 10: Refactor an unreadable analytics query', 'Refactor an unreadable DuckDB query', 'Complete DuckDB Exercise 12: Refactor an unreadable analytics query'], 13: ['Complete DuckDB Exercise 11: Audit table grain and join cardinality', 'Practice table grain, primary keys, join cardinality, pre-aggregation', 'Complete DuckDB Exercise 13: Audit table grain and join cardinality'], 14: ['Complete DuckDB Exercise 18: Build monthly cohorts and retention metrics', 'Practice DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation', 'Complete DuckDB Exercise 14: Build monthly cohorts and retention metrics'], 15: ['Complete DuckDB Exercise 19: Calculate running totals and moving averages', 'Practice window frames, ROWS BETWEEN, LAG, running totals, moving averages', 'Complete DuckDB Exercise 15: Calculate running totals and moving averages'], 16: ['Complete DuckDB Exercise 12: Compare customer populations with set and existence logic', 'Practice UNION, INTERSECT, EXCEPT, semi joins, anti joins', 'Complete DuckDB Exercise 16: Compare customer populations with set and existence logic'], 17: ['Complete DuckDB Exercise 20: Standardize messy text, dates, and numeric fields', 'Practice TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME', 'Complete DuckDB Exercise 17: Standardize messy text, dates, and numeric fields'], 18: ['Complete DuckDB Exercise 28: Complete a full relational data-quality audit', 'Practice grain, duplicates, NULLs, referential integrity, reconciliation, CTEs', 'Complete DuckDB Exercise 18: Complete a full relational data-quality audit'], 19: ['Complete DuckDB Exercise 03: Build clear selected fields and calculated columns', 'Practice selected fields, aliases, arithmetic expressions, and DISTINCT', 'Complete DuckDB Exercise 19: Build clear selected fields and calculated columns'], 20: ['Complete DuckDB Exercise 04: Filter patterns, ranges, and missing values', 'Practice compound filters, patterns, ranges, and missing values', 'Complete DuckDB Exercise 20: Filter patterns, ranges, and missing values'], 21: ['Complete DuckDB Exercise 05: Connect orders to customers with inner joins', 'Practice inner joins and qualified columns', 'Complete DuckDB Exercise 21: Connect orders to customers with inner joins'], 22: ['Complete DuckDB Exercise 13: Compare outer, cross, and self joins', 'Practice outer, cross, and self joins', 'Complete DuckDB Exercise 22: Compare outer, cross, and self joins'], 23: ['Complete DuckDB Exercise 14: Use subqueries in filters, sources, and calculations', 'Practice subqueries in WHERE, FROM, and SELECT', 'Complete DuckDB Exercise 23: Use subqueries in filters, sources, and calculations'], 24: ['Complete DuckDB Exercise 15: Add row-level context with window functions', 'Practice OVER, PARTITION BY, and window aggregates', 'Complete DuckDB Exercise 24: Add row-level context with window functions'], 25: ['Complete DuckDB Exercise 21: Rank results and select top records', 'Practice ROW_NUMBER, RANK, DENSE_RANK, and top-N logic', 'Complete DuckDB Exercise 25: Rank results and select top records'], 26: ['Complete DuckDB Exercise 22: Compare current values with prior and next rows', 'Practice LAG, LEAD, and period-over-period change', 'Complete DuckDB Exercise 26: Compare current values with prior and next rows'], 27: ['Complete DuckDB Exercise 23: Build subtotal and pivot-style summaries', 'Practice ROLLUP, CUBE, GROUPING SETS, and pivot-style summaries', 'Complete DuckDB Exercise 27: Build subtotal and pivot-style summaries'], 28: ['Complete DuckDB Exercise 24: Inspect data types and work with list values', 'Practice data types, LIST values, UNNEST, and type-safe calculations', 'Complete DuckDB Exercise 28: Inspect data types and work with list values'], 29: ['Complete DuckDB Exercise 29: Explore text search and extension-safe SQL', 'Practice text search and inspect available DuckDB extensions'], 30: ['Complete DuckDB Exercise 30: Profile tables for analytical storage decisions', 'Practice table profiling for analytical storage decisions'], 31: ['Complete DuckDB Exercise 31: Reshape operational data into analytical tables', 'Practice fact tables, dimensions, normalization, and star-schema joins'], 32: ['Complete DuckDB Exercise 32: Create reusable views and analytical snapshots', 'Practice views, reusable logic, and analytical snapshots'], 33: ['Complete DuckDB Exercise 33: Plan partitioning and access-safe outputs', 'Practice partition-key analysis and access-safe analytical outputs']}


def _slug(display: int, title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", str(title).casefold()).strip("_")
    return f"{display:02d}_{value}"


DUCKDB_EXERCISES: dict[int, dict] = {}
for _challenge in _challenge_exercises():
    _display = int(_challenge["display_number"])
    _internal = int(_challenge["internal_id"])
    _title = str(_challenge["title"])
    _legacy = [
        str(value).strip()
        for value in _LEGACY_LABELS_BY_ID.get(_internal, ())
        if str(value).strip()
    ]
    DUCKDB_EXERCISES[_internal] = {
        "title": _title,
        "label": f"Complete SQL Challenge {_display:02d}: {_title}",
        "old_label": _legacy[0] if _legacy else "",
        "legacy_labels": list(dict.fromkeys(_legacy)),
        "concepts": str(_challenge["concept"]),
        "minutes": int(_challenge.get("estimated_minutes", 25)),
        "priority": 3 if _display < 30 else 2,
        "slug": _slug(_display, _title),
        "week": int(_challenge["gate"]["week"]),
        "roadmap_number": _display,
        "terminal_chapter": str(_challenge["terminal_chapter"]),
        "source_provider": str(_challenge["source"]["provider"]),
        "source_challenge": str(_challenge["source"]["challenge"]),
        "source_url": str(_challenge["source"]["url"]),
        "prerequisites": {
            "all_of": [],
            "any_of": [],
            "mastery_checks": [],
            "prior_exercises": [
                DUCKDB_ID_BY_ROADMAP_NUMBER[int(value)]
                for value in _challenge.get("prerequisite_exercises", ())
            ],
        },
    }


def roadmap_number(number: int) -> int:
    number = int(number)
    if number not in DUCKDB_ROADMAP_NUMBER_BY_ID:
        raise ValueError(f"SQL challenge ID {number} is not in the catalog.")
    return DUCKDB_ROADMAP_NUMBER_BY_ID[number]


def internal_number_for_roadmap_number(number: int) -> int | None:
    return DUCKDB_ID_BY_ROADMAP_NUMBER.get(int(number))


def exercise_labels(number: int) -> tuple[str, ...]:
    item = DUCKDB_EXERCISES[int(number)]
    display = roadmap_number(number)
    values = [
        item["label"],
        f"Complete DuckDB Exercise {display:02d}: {item['title']}",
        item.get("old_label", ""),
        *item.get("legacy_labels", []),
    ]
    return tuple(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def exercise_number_for_label(label):
    text = str(label or "").strip()
    if not text:
        return None
    for number in ordered_exercise_numbers():
        if text in exercise_labels(number):
            return number
    title_text = text.split(":", 1)[1].strip().casefold() if ":" in text else ""
    if title_text:
        for number, item in DUCKDB_EXERCISES.items():
            if str(item["title"]).strip().casefold() == title_text:
                return int(number)
    match = re.search(r"(?:SQL Challenge|DuckDB Exercise)\s+(\d+)", text, re.IGNORECASE)
    if match:
        return internal_number_for_roadmap_number(int(match.group(1)))
    return None


def exercise_for_label(label):
    number = exercise_number_for_label(label)
    return DUCKDB_EXERCISES.get(number) if number is not None else None


def ordered_exercise_numbers():
    return _DUCKDB_ROADMAP_INTERNAL_ORDER


def exercise_source(value):
    number = None
    if isinstance(value, int):
        number = value
    else:
        text = str(value or "").strip()
        if text.isdigit():
            candidate = int(text)
            number = candidate if candidate in DUCKDB_EXERCISES else internal_number_for_roadmap_number(candidate)
        else:
            number = exercise_number_for_label(text)
    if number not in DUCKDB_EXERCISES:
        return None
    item = DUCKDB_EXERCISES[number]
    return f"SQL Challenge {roadmap_number(number):02d}: {item['title']}"
