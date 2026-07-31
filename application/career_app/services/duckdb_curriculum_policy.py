from __future__ import annotations

"""Cumulative DuckDB curriculum, prerequisite, scheduling, task-language, and startup-order audit.

Stable exercise IDs are preserved for progress and submissions. Learners see a
separate roadmap number whose order follows the actual SQL curriculum.
"""

from dataclasses import replace
from datetime import date, timedelta
from difflib import get_close_matches
from pathlib import Path
import re
from typing import Any

_INSTALLED = False

# Stable internal IDs in learner-facing roadmap order.
ROADMAP_INTERNAL_ORDER = (
    # SQL foundations: selecting, calculated fields, filtering, aggregation.
    1, 19, 20, 2,
    # Joining Data in SQL.
    21, 6, 22, 16, 13,
    # Subqueries, CASE, CTEs, and introductory window functions.
    23, 5, 7, 12, 24,
    # Window functions and PostgreSQL/DuckDB functions.
    25, 26, 15, 11, 27, 28, 14, 4, 3, 17,
    # Database design, integrated analysis, and final validation.
    29, 30, 31, 32, 33, 8, 9, 10, 18,
)

# Clear, action-oriented task names. These titles describe the actual work and
# avoid vague labels such as "mixed assessment" without context.
TITLE_BY_ID = {
    1: "Filter and sort support tickets",
    19: "Prepare a retail order review",
    20: "Filter support and feedback records",
    2: "Summarize retail orders with grouped metrics",
    21: "Join orders to customers",
    6: "Combine customers, orders, and payments",
    22: "Use outer, cross, and self joins",
    16: "Compare customer groups with set logic",
    13: "Check table grain and join cardinality",
    23: "Use subqueries in filters, sources, and calculations",
    5: "Group service results with CASE",
    7: "Analyze order profitability with subqueries and CTEs",
    12: "Refactor a complex query with readable CTEs",
    24: "Add row-level context with window functions",
    25: "Rank results and select top records",
    26: "Compare current values with prior and next rows",
    15: "Calculate running totals and moving averages",
    27: "Build subtotal and pivot-style summaries",
    28: "Inspect data types and work with list values",
    14: "Build monthly cohorts and retention metrics",
    4: "Calculate subscription KPIs",
    3: "Clean and standardize customer feedback",
    17: "Standardize messy text, dates, and numeric fields",
    11: "Explain join and window-function results",
    29: "Search text safely and inspect DuckDB extensions",
    30: "Profile tables for analytical storage decisions",
    31: "Reshape operational data into analytical tables",
    32: "Create reusable views and analytical snapshots",
    33: "Plan partitioning and access-safe outputs",
    8: "Analyze a VFX production snapshot",
    9: "Complete a timed product analysis",
    10: "Complete an end-to-end workforce SQL assessment",
    18: "Complete the final relational data-quality audit",
}

# Authored workplace context and task wording. These entries are deliberately
# written by hand instead of being generated from validation metadata.
SCENARIO_BY_ID = {
    1: (
        "A customer-support manager is preparing the daily service queue. The "
        "manager needs a clear ticket list, the most urgent open work, and a few "
        "simple views for follow-up."
    ),
    19: (
        "A retail operations manager is reviewing order data before it is used "
        "in a sales report. The manager needs a focused set of fields, clear "
        "report headings, and a quick check that stored revenue agrees with "
        "the order details."
    ),
    20: (
        "A support-operations analyst is checking service records before the "
        "weekly report is prepared. The analyst needs to identify active priority "
        "tickets, missing resolution times, and feedback submitted by email."
    ),
    2: (
        "A sales manager needs a short weekly summary of the retail order file. "
        "The report should show overall performance, regional results, channel "
        "volume, and discount patterns."
    ),
}
AUTHORED_TASK_BY_ID = {
    1: {
        1: (
            "Prepare the manager's basic ticket list. Return `ticket_id`, "
            "`customer_name`, and `status` for every ticket."
        ),
        2: "Find the tickets that are still open. Return only `ticket_id`.",
        3: (
            "Find active tickets that need the fastest attention. Return only "
            "`ticket_id` for tickets with High or Urgent priority whose status "
            "is Open or Pending."
        ),
        4: (
            "Find tickets created after June 15, 2026. Return only `ticket_id`."
        ),
        5: (
            "Review how long closed tickets took to resolve. Return `ticket_id` "
            "and `resolution_hours`, sorted from longest to shortest."
        ),
        6: (
            "Show the five closed tickets with the highest satisfaction scores. "
            "Return `ticket_id` and `satisfaction_score`; when scores tie, show "
            "the newest ticket first."
        ),
        7: (
            "Find open Billing tickets for follow-up. Return only `ticket_id`, "
            "sorted from oldest to newest."
        ),
    },
    19: {
        1: (
            "Check what each order would be worth before discounts. Return "
            "`order_id`, `quantity`, `unit_price`, and `quantity * unit_price` "
            "as `line_value`."
        ),
        2: (
            "Prepare a sales report with consistent headings. Return `order_id`; "
            "rename `region` to `sales_region`, `sales_channel` to `channel`, "
            "and `revenue` to `recorded_revenue`."
        ),
        3: (
            "Check whether the revenue stored for each order matches quantity "
            "multiplied by unit price. Return `order_id`, rename `revenue` to "
            "`recorded_revenue`, and calculate the difference as "
            "`revenue_difference`."
        ),
        4: (
            "List every region and sales-channel combination used by the business. "
            "Return unique `region` and `sales_channel` pairs, sorted by region "
            "and then sales channel."
        ),
    },
    20: {
        1: (
            "List the ticket statuses currently used by the support team. Return "
            "each unique `status` in alphabetical order."
        ),
        2: (
            "Find high-priority tickets that are still active. Return `ticket_id`, "
            "`priority`, and `status` for High or Urgent tickets that are not Closed."
        ),
        3: (
            "Find tickets that do not have a recorded resolution time. Return "
            "`ticket_id`, `status`, and `resolution_hours`."
        ),
        4: (
            "Find feedback submitted through email, even when the channel text "
            "uses different capitalization or extra spaces. Return `response_id` "
            "and `channel_raw`."
        ),
    },
    2: {
        1: "Count the orders in the sales file. Return the count as `orders`.",
        2: "Calculate the revenue recorded across all orders. Return it as `revenue`.",
        3: (
            "Calculate the average revenue per order. Return it as "
            "`average_revenue`."
        ),
        4: (
            "Show order volume and revenue for each region. Return `region`, the "
            "order count as `orders`, and total revenue as `revenue`."
        ),
        5: (
            "Find sales channels that handled more than five orders. Return "
            "`sales_channel` and the order count as `orders`."
        ),
        6: (
            "Calculate the average discount for each product category. Return "
            "`product_category` and the average as `average_discount`."
        ),
        7: (
            "Find the region that generated the most revenue. Return `region` "
            "and total `revenue`."
        ),
    },
}
# Exact terminal DataCamp chapter for each exercise. An exercise cannot appear
# as ready until this chapter and every preceding required chapter are complete.
# All four Week 3 foundation exercises intentionally wait for Intermediate SQL
# Chapter 4, as requested.
TERMINAL_CHAPTER_BY_ID = {
    1: "w03_intermediate_sql_04",
    19: "w03_intermediate_sql_04",
    20: "w03_intermediate_sql_04",
    2: "w03_intermediate_sql_04",
    21: "w03_joining_sql_01",
    6: "w04_joining_sql_02",
    22: "w04_joining_sql_02",
    16: "w04_joining_sql_03",
    13: "w04_joining_sql_03",
    23: "w04_joining_sql_04",
    5: "w04_manipulation_sql_01",
    7: "w04_manipulation_sql_03",
    12: "w04_manipulation_sql_03",
    24: "w04_manipulation_sql_04",
    25: "w05_window_sql_02",
    26: "w05_window_sql_03",
    15: "w05_window_sql_03",
    27: "w05_window_sql_04",
    28: "w05_functions_sql_01",
    14: "w05_functions_sql_02",
    4: "w05_functions_sql_02",
    3: "w05_functions_sql_03",
    17: "w05_functions_sql_03",
    11: "w05_window_sql_03",
    29: "w06_functions_sql_04",
    30: "w06_database_design_01",
    31: "w06_database_design_02",
    32: "w06_database_design_03",
    33: "w06_database_design_04",
    8: "w06_database_design_04",
    9: "w06_database_design_04",
    10: "w06_database_design_04",
    18: "w06_database_design_04",
}

# Prerequisites use stable internal IDs, but every learner-facing explanation is
# converted to the roadmap number. The practice path is deliberately linear:
# each exercise requires the immediately preceding learner-facing exercise.
# Exact DataCamp chapter gates separately ensure the SQL concept has been taught.
PRIOR_EXERCISES_BY_ID = {
    internal_id: (() if index == 0 else (ROADMAP_INTERNAL_ORDER[index - 1],))
    for index, internal_id in enumerate(ROADMAP_INTERNAL_ORDER)
}


_DISPLAY_BY_ID = {
    internal_id: display_number
    for display_number, internal_id in enumerate(ROADMAP_INTERNAL_ORDER, start=1)
}
_ID_BY_DISPLAY = {display: internal for internal, display in _DISPLAY_BY_ID.items()}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _row_value(row: Any, key: str, index: int = 0, default: Any = None) -> Any:
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        try:
            return row[index]
        except Exception:
            return default


def _table_exists(conn: Any, name: str) -> bool:
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (str(name),)
        ).fetchone() is not None
    except Exception:
        return False


def _apply_catalog_overlay() -> None:
    from career_app.data import duckdb_exercises as catalog
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY

    if set(catalog.DUCKDB_EXERCISES) != set(ROADMAP_INTERNAL_ORDER):
        missing = sorted(set(ROADMAP_INTERNAL_ORDER) - set(catalog.DUCKDB_EXERCISES))
        extra = sorted(set(catalog.DUCKDB_EXERCISES) - set(ROADMAP_INTERNAL_ORDER))
        raise RuntimeError(f"DuckDB catalog mismatch; missing={missing}, extra={extra}")
    unknown = sorted(set(TERMINAL_CHAPTER_BY_ID.values()) - set(CHAPTER_BY_KEY))
    if unknown:
        raise RuntimeError(f"Unknown DataCamp terminal chapters: {unknown}")

    catalog._DUCKDB_ROADMAP_INTERNAL_ORDER = tuple(ROADMAP_INTERNAL_ORDER)
    catalog.DUCKDB_ROADMAP_NUMBER_BY_ID.clear()
    catalog.DUCKDB_ROADMAP_NUMBER_BY_ID.update(_DISPLAY_BY_ID)
    catalog.DUCKDB_ID_BY_ROADMAP_NUMBER.clear()
    catalog.DUCKDB_ID_BY_ROADMAP_NUMBER.update(_ID_BY_DISPLAY)

    for internal_id in ROADMAP_INTERNAL_ORDER:
        item = catalog.DUCKDB_EXERCISES[internal_id]
        prior_label = str(item.get("label") or "").strip()
        legacy = item.setdefault("legacy_labels", [])
        if prior_label and prior_label not in legacy:
            legacy.append(prior_label)
        title = TITLE_BY_ID[internal_id]
        chapter = CHAPTER_BY_KEY[TERMINAL_CHAPTER_BY_ID[internal_id]]
        # Practice begins on the next Monday-Friday day after the terminal
        # chapter. A Friday chapter therefore places its exercise on Monday of
        # the following roadmap week instead of showing it early on Friday.
        practice_week = int(chapter.week) + (1 if int(chapter.weekday) >= 4 else 0)
        prerequisites = dict(item.get("prerequisites") or {})
        prerequisites["prior_exercises"] = list(PRIOR_EXERCISES_BY_ID[internal_id])
        item.update(
            {
                "title": title,
                "label": f"Complete DuckDB Exercise {_DISPLAY_BY_ID[internal_id]:02d}: {title}",
                "roadmap_number": _DISPLAY_BY_ID[internal_id],
                "week": practice_week,
                "terminal_chapter": TERMINAL_CHAPTER_BY_ID[internal_id],
                "prerequisites": prerequisites,
            }
        )

    # Single source of truth for chapter gates used by the runner, planner, and UI.
    from career_app.services import content_gates
    content_gates.DUCKDB_TERMINAL_CHAPTER.clear()
    content_gates.DUCKDB_TERMINAL_CHAPTER.update(TERMINAL_CHAPTER_BY_ID)


def _program_start(conn: Any) -> date:
    if _table_exists(conn, "program_state"):
        row = conn.execute("SELECT start_date FROM program_state WHERE id=1").fetchone()
        raw = _row_value(row, "start_date", 0, None)
        try:
            return date.fromisoformat(str(raw))
        except (TypeError, ValueError):
            pass
    today = date.today()
    return today - timedelta(days=today.weekday())


def _next_weekday(value: date) -> date:
    result = value + timedelta(days=1)
    while result.weekday() > 4:
        result += timedelta(days=1)
    return result


def scheduled_date(conn: Any, internal_id: int) -> date:
    """Return the first weekday after the exercise's terminal chapter."""
    from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY

    chapter = CHAPTER_BY_KEY[TERMINAL_CHAPTER_BY_ID[int(internal_id)]]
    chapter_day = chapter.scheduled_date(_program_start(conn))
    return _next_weekday(chapter_day)


def _display_prerequisite_name(internal_id: int) -> str:
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

    internal_id = int(internal_id)
    return (
        f"DuckDB Exercise {_DISPLAY_BY_ID[internal_id]:02d}: "
        f"{DUCKDB_EXERCISES[internal_id]['title']}"
    )


def _rewrite_readiness_result(result: dict[str, Any]) -> dict[str, Any]:
    rewritten = dict(result)
    missing: list[str] = []
    for value in list(result.get("missing") or []):
        text = str(value)
        match = re.fullmatch(r"DuckDB Exercise\s+(\d+)(?::.*)?", text, re.I)
        if match:
            internal = int(match.group(1))
            if internal in _DISPLAY_BY_ID:
                text = _display_prerequisite_name(internal)
        missing.append(text)
    missing = list(dict.fromkeys(missing))
    rewritten["missing"] = missing
    rewritten["ready"] = not missing
    rewritten["reason"] = "" if not missing else "Complete " + ", ".join(missing) + " first."
    return rewritten


def _task_internal_id(task: dict[str, Any]) -> int | None:
    for value in (
        task.get("starter_path"),
        task.get("managed_key"),
        task.get("target_key"),
        task.get("source_key"),
    ):
        match = re.search(r"(?:roadmap_v1026:)?duckdb:(\d+)", str(value or ""), re.I)
        if match:
            candidate = int(match.group(1))
            if candidate in _DISPLAY_BY_ID:
                return candidate
    label = str(task.get("label") or "")
    try:
        from career_app.data.duckdb_exercises import exercise_number_for_label
        candidate = exercise_number_for_label(label)
    except Exception:
        candidate = None
    return int(candidate) if candidate in _DISPLAY_BY_ID else None


def _weekday_schedule_ready(conn: Any, internal_id: int, *, today: date | None = None) -> tuple[bool, str]:
    today = today or date.today()
    scheduled = scheduled_date(conn, internal_id)
    if today < scheduled:
        return False, (
            "Scheduled for "
            + scheduled.strftime("%A, %B %d")
            + " after the required DataCamp chapter."
        )
    if today.weekday() > 4:
        return False, "DuckDB practice is scheduled Monday through Friday; weekends are reserved for projects."
    return True, "Available for weekday DuckDB practice."


def _clear_stale_focus(conn: Any, internal_ids: set[int] | None = None) -> None:
    if not _table_exists(conn, "daily_focus") or not _table_exists(conn, "task_metadata"):
        return
    rows = conn.execute(
        """SELECT s.id,s.label,m.managed_key,m.starter_path
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE s.completed=0"""
    ).fetchall()
    stale_ids: list[int] = []
    for row in rows:
        task = {
            "label": _row_value(row, "label", 1, ""),
            "managed_key": _row_value(row, "managed_key", 2, ""),
            "starter_path": _row_value(row, "starter_path", 3, ""),
        }
        internal = _task_internal_id(task)
        if internal is None or (internal_ids is not None and internal not in internal_ids):
            continue
        schedule_ready, _ = _weekday_schedule_ready(conn, internal)
        # A calendar-eligible exercise may remain in Today's Focus as a grey,
        # locked preview until its exact chapter or prior exercise is complete.
        # Remove only rows that are early or fall on a project weekend.
        if not schedule_ready:
            stale_ids.append(_safe_int(_row_value(row, "id", 0, 0)))
    if stale_ids:
        placeholders = ",".join("?" for _ in stale_ids)
        conn.execute(
            f"DELETE FROM daily_focus WHERE task_id IN ({placeholders}) AND completed_at IS NULL",
            tuple(stale_ids),
        )
        if _table_exists(conn, "settings"):
            conn.execute(
                "DELETE FROM settings WHERE key LIKE 'daily_focus_snapshot_v2:%'"
            )


def _stage_duckdb_task_orders(conn: Any) -> int:
    """Move existing DuckDB task rows to collision-free temporary slots.

    SQLite enforces ``UNIQUE(week, sort_order)`` after every individual UPDATE.
    Re-numbering tasks directly can therefore fail when one exercise moves into
    a slot still occupied by another exercise. Stage every managed DuckDB task
    below the current minimum for its week before assigning final roadmap order.
    """
    if not (_table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata")):
        return 0
    rows = conn.execute(
        """SELECT s.id,s.week
           FROM sprint_tasks s
           JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key LIKE 'roadmap_v1026:duckdb:%'
              OR m.starter_path LIKE 'duckdb:%'
           ORDER BY s.week,s.id"""
    ).fetchall()
    if not rows:
        return 0

    by_week: dict[int, list[int]] = {}
    for row in rows:
        task_id = _safe_int(_row_value(row, "id", 0, 0))
        week = _safe_int(_row_value(row, "week", 1, 1), 1)
        if task_id > 0:
            by_week.setdefault(week, []).append(task_id)

    staged = 0
    for week, task_ids in by_week.items():
        minimum_row = conn.execute(
            "SELECT MIN(sort_order) AS minimum_order FROM sprint_tasks WHERE week=?",
            (int(week),),
        ).fetchone()
        current_minimum = _safe_int(
            _row_value(minimum_row, "minimum_order", 0, 0), 0
        )
        # Leave a generous gap below every existing task in this week. Each
        # staged value is unique, so no intermediate UPDATE can hit the index.
        base = min(current_minimum, -1000000) - len(task_ids) - 1000
        for offset, task_id in enumerate(task_ids, start=1):
            conn.execute(
                "UPDATE sprint_tasks SET sort_order=? WHERE id=?",
                (int(base - offset), int(task_id)),
            )
            staged += 1
    return staged


def _available_task_sort_order(
    conn: Any, *, week: int, preferred: int, task_id: int, after: int | None = None
) -> int:
    """Return an unused order while preserving learner-facing sequence."""
    candidate = int(preferred)
    if after is not None:
        candidate = max(candidate, int(after) + 1)
    while True:
        occupied = conn.execute(
            "SELECT id FROM sprint_tasks WHERE week=? AND sort_order=? AND id<>? LIMIT 1",
            (int(week), int(candidate), int(task_id)),
        ).fetchone()
        if occupied is None:
            return candidate
        candidate += 1


def _sync_task_metadata(conn: Any) -> None:
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES
    from career_app.services import roadmap_mastery

    if not (_table_exists(conn, "sprint_tasks") and _table_exists(conn, "task_metadata")):
        return
    _stage_duckdb_task_orders(conn)
    last_sort_by_week: dict[int, int] = {}
    for internal_id in ROADMAP_INTERNAL_ORDER:
        item = DUCKDB_EXERCISES[internal_id]
        managed = f"roadmap_v1026:duckdb:{internal_id}"
        row = conn.execute(
            """SELECT s.id,s.completed FROM sprint_tasks s
               JOIN task_metadata m ON m.task_id=s.id
               WHERE m.managed_key=? LIMIT 1""",
            (managed,),
        ).fetchone()
        if row is None:
            continue
        task_id = _safe_int(_row_value(row, "id", 0, 0))
        completed = bool(_safe_int(_row_value(row, "completed", 1, 0)))
        readiness = roadmap_mastery.duckdb_readiness(conn, internal_id)
        schedule_day = scheduled_date(conn, internal_id)
        schedule_ready, schedule_reason = _weekday_schedule_ready(conn, internal_id)
        ready = completed or (bool(readiness.get("ready")) and schedule_ready)
        if ready:
            reason = None
        elif not schedule_ready:
            reason = schedule_reason
        else:
            reason = readiness.get("reason") or schedule_reason
        target_week = int(item["week"])
        target_sort = _available_task_sort_order(
            conn,
            week=target_week,
            preferred=-760000 + _DISPLAY_BY_ID[internal_id] * 10,
            task_id=task_id,
            after=last_sort_by_week.get(target_week),
        )
        last_sort_by_week[target_week] = target_sort
        conn.execute(
            "UPDATE sprint_tasks SET week=?,sort_order=?,label=? WHERE id=?",
            (target_week, target_sort, str(item["label"]), task_id),
        )
        conn.execute(
            """UPDATE task_metadata
               SET prerequisite_state=?,prerequisite_reason=?,deferred_until=?,
                   description=?,definition_of_done=?,starter_path=?,category='SQL'
               WHERE task_id=?""",
            (
                "Ready" if ready else "Blocked",
                reason,
                None if completed or date.today() >= schedule_day else schedule_day.isoformat(),
                (
                    f"Weekday DuckDB practice aligned to "
                    f"{TERMINAL_CHAPTER_BY_ID[internal_id]}. "
                    "Complete the exact DataCamp chapter and listed earlier exercises first."
                ),
                "Complete every task, pass each result check, and save the completed SQL submission.",
                f"duckdb:{internal_id}",
                task_id,
            ),
        )
        if _table_exists(conn, "roadmap_requirement_state"):
            conn.execute(
                """UPDATE roadmap_requirement_state
                   SET title=?,due_week=?,reason=?,updated_at=CURRENT_TIMESTAMP
                   WHERE requirement_key=?""",
                (
                    item["title"], int(item["week"]), reason,
                    f"duckdb:{internal_id}",
                ),
            )
    _clear_stale_focus(conn)


def _validation_columns(markdown: str) -> dict[int, tuple[int | None, tuple[str, ...]]]:
    sections: dict[int, tuple[int | None, tuple[str, ...]]] = {}
    heading = re.compile(r"(?mi)^\s*##+\s*Q(?:uestion\s*)?(\d+)\b[^\n]*$")
    matches = list(heading.finditer(str(markdown or "")))
    for index, match in enumerate(matches):
        number = int(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        section = markdown[match.end():end]
        row_match = re.search(r"(?im)Expected\s+rows?\s*:\s*\**\s*(\d+)", section)
        expected_rows = int(row_match.group(1)) if row_match else None
        columns: tuple[str, ...] = ()
        for raw in section.splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "_", "- ", "* ", ">")):
                continue
            if "|" in line:
                parts = tuple(part.strip() for part in line.strip("|").split("|"))
                if parts and not all(re.fullmatch(r":?-{2,}:?", part or "") for part in parts):
                    columns = parts
                    break
        sections[number] = (expected_rows, columns)
    return sections


def _csv_schema_columns(dataset_folder: Path) -> set[str]:
    import csv

    columns: set[str] = set()
    if not dataset_folder.exists():
        return columns
    for path in dataset_folder.rglob("*.csv"):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                columns.update(str(value).strip() for value in next(csv.reader(handle), []) if str(value).strip())
        except (OSError, UnicodeError, csv.Error, StopIteration):
            continue
    return columns


def _base_prompt(prompt: str) -> str:
    """Recover the learner action from legacy or v10.41 enriched text."""
    text = re.sub(r"\s+", " ", str(prompt or "").strip())
    text = re.sub(r"^(?:Task|Question)\s*:\s*", "", text, flags=re.I)
    # v10.41 placed validation details inside the task paragraph. Remove those
    # generated details so the action can be displayed on its own again.
    markers = (
        r"\s+Required output\s*:",
        r"\s+Return columns?\s*:",
        r"\s+Use these exact names for calculated or summarized columns\s*:",
        r"\s+A correct result contains\s+\d+\s+rows?\b",
        r"\s+Expected rows?\s*:",
        r"\s+Do not include extra columns\b",
    )
    for marker in markers:
        text = re.split(marker, text, maxsplit=1, flags=re.I)[0]
    return text.strip().rstrip(" .")


def _task_sentence(prompt: str) -> str:
    """Return one direct, plain-language instruction without validation prose."""
    text = _base_prompt(prompt)
    text = re.sub(
        r"^(?:For this (?:question|task),?\s*|Please\s+|"
        r"Write (?:a|one) (?:SQL )?query (?:that|to)\s+|"
        r"Create (?:a|one) (?:SQL )?query (?:that|to)\s+|"
        r"Use (?:SQL|a SQL query) to\s+)",
        "",
        text,
        flags=re.I,
    ).strip()
    verb_normalizations = (
        (r"^returns?\s+all\b", "Return all"),
        (r"^returns?\b", "Return"),
        (r"^selects?\b", "Select"),
        (r"^calculates?\b", "Calculate"),
        (r"^counts?\b", "Count"),
        (r"^finds?\b", "Find"),
        (r"^lists?\b", "List"),
        (r"^shows?\b", "Show"),
        (r"^identifies?\b", "Identify"),
        (r"^compares?\b", "Compare"),
        (r"^creates?\b", "Create"),
        (r"^builds?\b", "Build"),
    )
    for pattern, replacement in verb_normalizations:
        if re.match(pattern, text, flags=re.I):
            text = re.sub(pattern, replacement, text, count=1, flags=re.I)
            break
    if text:
        text = text[0].upper() + text[1:]
    else:
        text = "Complete the requested analysis"
    if text[-1] not in ".?!":
        text += "."
    return text


def _correct_backticked_columns(prompt: str, source_columns: set[str], expected_columns: set[str]) -> str:
    if not source_columns:
        return prompt
    allowed = {value.casefold(): value for value in source_columns | expected_columns}
    sql_terms = {
        "open", "closed", "pending", "high", "urgent", "billing", "null",
        "inner", "left", "right", "full", "cross", "case", "select", "where",
    }

    def replace_token(match: re.Match[str]) -> str:
        token = match.group(1).strip()
        folded = token.casefold()
        if folded in allowed or folded in sql_terms or " " in token:
            return match.group(0)
        candidates = get_close_matches(folded, list(allowed), n=1, cutoff=0.72)
        if not candidates:
            return match.group(0)
        return f"`{allowed[candidates[0]]}`"

    return re.sub(r"`([^`]+)`", replace_token, prompt)


def _prompt_spec(
    prompt: str,
    *,
    expected_rows: int | None,
    expected_columns: tuple[str, ...],
    source_columns: set[str],
) -> dict[str, Any]:
    task = _correct_backticked_columns(
        _task_sentence(prompt), source_columns, set(expected_columns)
    )
    source_folded = {item.casefold() for item in source_columns}
    aliases = tuple(
        column for column in expected_columns
        if source_columns and column.casefold() not in source_folded
    )
    return {
        "task": task,
        "columns": tuple(expected_columns),
        "aliases": aliases,
        "rows": expected_rows,
    }


def _ui_prompt(spec: dict[str, Any]) -> str:
    """Format the Practice card as a short task plus scannable requirements."""
    lines = [str(spec["task"])]
    columns = tuple(spec.get("columns") or ())
    aliases = tuple(spec.get("aliases") or ())
    expected_rows = spec.get("rows")
    requirement_lines: list[str] = []
    if columns:
        requirement_lines.append(
            "Return columns: " + ", ".join(f"`{column}`" for column in columns) + "."
        )
    if aliases:
        requirement_lines.append(
            "Use these exact names for new columns: "
            + ", ".join(f"`{column}`" for column in aliases)
            + "."
        )
    if expected_rows is not None:
        requirement_lines.append(
            f"Expected rows: {expected_rows}."
        )
    if requirement_lines:
        lines.extend(["", "Result requirements", *[f"• {line}" for line in requirement_lines]])
    return "\n".join(lines)


def _parse_question_markers(sql: str) -> list[tuple[int, str]]:
    pattern = re.compile(r"(?mi)^\s*--\s*Q(?:uestion\s*)?(\d+)\s*[.):-]?\s*(.*?)\s*$")
    return [(int(match.group(1)), match.group(2).strip()) for match in pattern.finditer(sql)]


def _audited_prompt_specs(
    root: Path, internal_id: int, raw_starter: str, raw_validation: str
) -> dict[int, dict[str, Any]]:
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

    item = DUCKDB_EXERCISES[int(internal_id)]
    dataset_folder = root / "practice" / "duckdb" / "datasets" / item["slug"]
    source_columns = _csv_schema_columns(dataset_folder)
    checkpoints = _validation_columns(raw_validation)
    prompts: dict[int, dict[str, Any]] = {}
    for number, prompt in _parse_question_markers(raw_starter):
        expected_rows, expected_columns = checkpoints.get(number, (None, ()))
        spec = _prompt_spec(
            prompt,
            expected_rows=expected_rows,
            expected_columns=expected_columns,
            source_columns=source_columns,
        )
        authored = AUTHORED_TASK_BY_ID.get(int(internal_id), {}).get(int(number))
        if authored:
            spec["task"] = str(authored).strip()
        prompts[number] = spec
    return prompts


def _audited_prompts(root: Path, internal_id: int, raw_starter: str, raw_validation: str) -> dict[int, str]:
    return {
        number: _ui_prompt(spec)
        for number, spec in _audited_prompt_specs(
            root, internal_id, raw_starter, raw_validation
        ).items()
    }

def _rewrite_starter_text(root: Path, internal_id: int, text: str, validation: str) -> str:
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

    item = DUCKDB_EXERCISES[int(internal_id)]
    display = _DISPLAY_BY_ID[int(internal_id)]
    specs = _audited_prompt_specs(root, internal_id, text, validation)
    result = re.sub(
        r"(?m)^--\s*DuckDB Exercise\s+\d+\s*:[^\n]*$",
        f"-- DuckDB Exercise {display:02d}: {item['title']}",
        text,
        count=1,
    )

    def replace(match: re.Match[str]) -> str:
        number = int(match.group(1))
        spec = specs.get(number)
        prompt = str(spec["task"]) if spec else _task_sentence(match.group(2))
        return f"-- Q{number}. {prompt}"

    return re.sub(
        r"(?mi)^\s*--\s*Q(?:uestion\s*)?(\d+)\s*[.):-]?\s*(.*?)\s*$",
        replace,
        result,
    )


def _rewrite_readme_text(root: Path, internal_id: int, text: str, starter: str, validation: str) -> str:
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

    item = DUCKDB_EXERCISES[int(internal_id)]
    display = _DISPLAY_BY_ID[int(internal_id)]
    specs = _audited_prompt_specs(root, internal_id, starter, validation)
    result = re.sub(
        r"(?m)^#\s*DuckDB Exercise\s+\d+\s*:[^\n]*$",
        f"# DuckDB Exercise {display:02d}: {item['title']}",
        text,
        count=1,
    )
    result = re.sub(r"(?m)^\*\*Week:\*\*\s*\d+\s*$", f"**Week:** {item['week']}", result)
    result = re.sub(
        r"(?m)^\*\*Concepts:\*\*[^\n]*$",
        f"**Concepts:** {item.get('concepts', '')}",
        result,
    )
    scenario = str(SCENARIO_BY_ID.get(int(internal_id), "")).strip()
    if scenario:
        scenario_block = "## Scenario\n\n" + scenario + "\n\n"
        scenario_pattern = re.compile(r"(?ms)^##\s+Scenario\s*\n.*?(?=^##\s+|\Z)")
        if scenario_pattern.search(result):
            result = scenario_pattern.sub(scenario_block, result, count=1)
        else:
            tasks_heading = re.search(r"(?m)^##\s+(?:Questions|Tasks)\s*$", result)
            if tasks_heading:
                result = result[:tasks_heading.start()] + scenario_block + result[tasks_heading.start():]
            else:
                result = result.rstrip() + "\n\n" + scenario_block
    task_lines = ["## Tasks", ""]
    for number in sorted(specs):
        spec = specs[number]
        task_lines.extend([f"### Task {number}", "", str(spec["task"]), ""])
        requirements: list[str] = []
        columns = tuple(spec.get("columns") or ())
        aliases = tuple(spec.get("aliases") or ())
        expected_rows = spec.get("rows")
        if columns:
            requirements.append(
                "- **Return columns:** "
                + ", ".join(f"`{column}`" for column in columns)
            )
        if aliases:
            requirements.append(
                "- **Exact names for new columns:** "
                + ", ".join(f"`{column}`" for column in aliases)
            )
        if expected_rows is not None:
            requirements.append(f"- **Expected rows:** {expected_rows}")
        if requirements:
            task_lines.extend(["**Result requirements**", "", *requirements, ""])
    replacement = "\n".join(task_lines).rstrip() + "\n"
    pattern = re.compile(r"(?ms)^##\s+(?:Questions|Tasks)\s*\n.*?(?=^##\s+|\Z)")
    if pattern.search(result):
        result = pattern.sub(replacement, result, count=1)
    else:
        result = result.rstrip() + "\n\n" + replacement
    return result

def rewrite_static_content(root: Path) -> dict[str, Any]:
    """Rewrite all 33 exercise READMEs and starter prompts in place.

    Validation files and learner submissions are never changed. The validation
    checkpoint is used to state exact output columns, aliases, and row counts.
    """
    from career_app.data.duckdb_exercises import DUCKDB_EXERCISES

    root = Path(root)
    changed: list[str] = []
    errors: list[str] = []
    for internal_id in ROADMAP_INTERNAL_ORDER:
        item = DUCKDB_EXERCISES[internal_id]
        folder = root / "practice" / "duckdb" / "exercises" / item["slug"]
        readme = folder / "README.md"
        starter = folder / "starter.sql"
        validation = folder / "validation.md"
        if not (readme.is_file() and starter.is_file() and validation.is_file()):
            errors.append(f"Exercise {internal_id}: missing README.md, starter.sql, or validation.md")
            continue
        raw_readme = readme.read_text(encoding="utf-8-sig")
        raw_starter = starter.read_text(encoding="utf-8-sig")
        raw_validation = validation.read_text(encoding="utf-8-sig")
        prompts = _audited_prompts(root, internal_id, raw_starter, raw_validation)
        checkpoints = _validation_columns(raw_validation)
        if not prompts:
            errors.append(f"Exercise {internal_id}: no Q1/Q2 task markers found")
            continue
        missing_checkpoints = sorted(set(prompts) - set(checkpoints))
        if missing_checkpoints:
            errors.append(f"Exercise {internal_id}: missing validation checkpoints {missing_checkpoints}")
            continue
        new_starter = _rewrite_starter_text(root, internal_id, raw_starter, raw_validation)
        new_readme = _rewrite_readme_text(root, internal_id, raw_readme, raw_starter, raw_validation)
        if new_starter != raw_starter:
            starter.write_text(new_starter, encoding="utf-8", newline="\n")
            changed.append(str(starter.relative_to(root)))
        if new_readme != raw_readme:
            readme.write_text(new_readme, encoding="utf-8", newline="\n")
            changed.append(str(readme.relative_to(root)))
    return {"changed": changed, "errors": errors}


def audit_contract(root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if set(ROADMAP_INTERNAL_ORDER) != set(range(1, 34)):
        errors.append("Roadmap order must include every stable DuckDB ID exactly once.")
    if set(TITLE_BY_ID) != set(ROADMAP_INTERNAL_ORDER):
        errors.append("Title map does not cover every DuckDB exercise.")
    for internal_id, tasks in AUTHORED_TASK_BY_ID.items():
        if internal_id not in ROADMAP_INTERNAL_ORDER:
            errors.append(f"Authored tasks reference unknown exercise {internal_id}.")
        for number, task in tasks.items():
            if not str(task).strip():
                errors.append(f"Exercise {internal_id} task {number} has empty authored wording.")
            lowered = str(task).casefold()
            if "concise aliases" in lowered or "pre-discount line value" in lowered:
                errors.append(f"Exercise {internal_id} task {number} retains confusing wording.")
    if set(TERMINAL_CHAPTER_BY_ID) != set(ROADMAP_INTERNAL_ORDER):
        errors.append("Terminal chapter map does not cover every DuckDB exercise.")
    if set(PRIOR_EXERCISES_BY_ID) != set(ROADMAP_INTERNAL_ORDER):
        errors.append("Prior-exercise map does not cover every DuckDB exercise.")
    for internal, priors in PRIOR_EXERCISES_BY_ID.items():
        for prior in priors:
            if prior not in _DISPLAY_BY_ID:
                errors.append(f"Exercise {internal} references unknown prior exercise {prior}.")
            elif _DISPLAY_BY_ID[prior] >= _DISPLAY_BY_ID[internal]:
                errors.append(
                    f"Exercise {_DISPLAY_BY_ID[internal]:02d} has a forward prerequisite "
                    f"Exercise {_DISPLAY_BY_ID[prior]:02d}."
                )
    for index, internal in enumerate(ROADMAP_INTERNAL_ORDER):
        expected = () if index == 0 else (ROADMAP_INTERNAL_ORDER[index - 1],)
        if tuple(PRIOR_EXERCISES_BY_ID.get(internal, ())) != expected:
            errors.append(
                f"Exercise {_DISPLAY_BY_ID[internal]:02d} must require only the "
                "immediately preceding roadmap exercise."
            )
    if ROADMAP_INTERNAL_ORDER[:4] != (1, 19, 20, 2):
        errors.append(
            "The Week 3 foundation order must be SELECT, aliases/calculations, "
            "compound filters, then grouped metrics."
        )
    try:
        from career_app.data.datacamp_curriculum import CHAPTER_BY_KEY
        previous = None
        for internal in ROADMAP_INTERNAL_ORDER:
            chapter = CHAPTER_BY_KEY[TERMINAL_CHAPTER_BY_ID[internal]]
            position = (
                int(chapter.week), int(chapter.weekday), int(chapter.order_in_day)
            )
            if previous is not None and position < previous:
                errors.append(
                    f"Exercise {_DISPLAY_BY_ID[internal]:02d} is mapped before the "
                    "DataCamp chapter used by the preceding exercise."
                )
            previous = position
    except Exception as exc:
        errors.append(f"Could not validate DataCamp chapter order: {exc}")
    for internal in ROADMAP_INTERNAL_ORDER[:4]:
        if TERMINAL_CHAPTER_BY_ID[internal] != "w03_intermediate_sql_04":
            errors.append("Week 3 foundation exercises must wait for Intermediate SQL Chapter 4.")
    if root is not None:
        result = rewrite_static_content(Path(root))
        errors.extend(result["errors"])
    return errors


def _install_runner_prompt_audit() -> None:
    from career_app.services import duckdb_exercise_runner as runner

    if getattr(runner, "_duckdb_prompt_audit_installed", False):
        return
    original_starter = runner.starter_sql
    original_instructions = runner.instructions_markdown
    original_validation = runner.validation_markdown

    def starter_sql(root: Path, number: int) -> str:
        root = Path(root)
        raw = original_starter(root, int(number))
        validation = original_validation(root, int(number))
        return _rewrite_starter_text(root, int(number), raw, validation)

    def question_definitions(root: Path, number: int):
        root = Path(root)
        internal_id = int(number)
        raw_starter = original_starter(root, internal_id)
        validation = original_validation(root, internal_id)
        questions = runner.parse_questions(starter_sql(root, internal_id))
        if not questions:
            raise runner.DuckDBExerciseRunnerError(
                "The starter SQL does not contain any Q1, Q2, ... task sections."
            )
        prompts = _audited_prompts(root, internal_id, raw_starter, validation)
        return [
            replace(question, prompt=prompts.get(question.number, question.prompt))
            for question in questions
        ]

    def instructions_markdown(root: Path, number: int) -> str:
        root = Path(root)
        raw = original_instructions(root, int(number))
        raw_starter = original_starter(root, int(number))
        validation = original_validation(root, int(number))
        return _rewrite_readme_text(root, int(number), raw, raw_starter, validation).strip()

    runner.starter_sql = starter_sql
    runner.question_definitions = question_definitions
    runner.instructions_markdown = instructions_markdown
    runner._duckdb_prompt_audit_installed = True


def _install_readiness_and_sync() -> None:
    from career_app.services import roadmap_mastery

    if getattr(roadmap_mastery, "_duckdb_curriculum_audit_installed", False):
        return
    original_readiness = roadmap_mastery.duckdb_readiness
    original_reconcile = roadmap_mastery.reconcile

    def duckdb_readiness(conn: Any, number: int) -> dict[str, Any]:
        result = original_readiness(conn, int(number))
        return _rewrite_readiness_result(result)

    def reconcile(conn: Any, root: Any = None) -> dict[str, Any]:
        result = original_reconcile(conn, root)
        _sync_task_metadata(conn)
        conn.commit()
        return result

    roadmap_mastery.duckdb_readiness = duckdb_readiness
    roadmap_mastery.reconcile = reconcile
    roadmap_mastery._duckdb_curriculum_audit_installed = True


def _install_unified_task_policy() -> None:
    from career_app.services import unified_tasks
    from career_app.services import roadmap_mastery

    if getattr(unified_tasks, "_duckdb_curriculum_policy_installed", False):
        return
    original_readiness = unified_tasks._readiness
    original_ready_tasks = unified_tasks.ready_tasks
    original_daily_plan = unified_tasks.daily_plan
    original_snapshot = unified_tasks._ensure_daily_snapshot

    def readiness(conn: Any, task: dict[str, Any], current_week: int):
        internal = _task_internal_id(task)
        if internal is None:
            return original_readiness(conn, task, current_week)
        result = roadmap_mastery.duckdb_readiness(conn, internal)
        schedule_ready, schedule_reason = _weekday_schedule_ready(conn, internal)
        ready = bool(result.get("ready")) and schedule_ready
        reason = "" if ready else (result.get("reason") or schedule_reason)
        return unified_tasks.Readiness(ready, str(reason))

    def ready_tasks(conn: Any, current_week: int) -> list[dict[str, Any]]:
        rows = list(original_ready_tasks(conn, current_week))
        result: list[dict[str, Any]] = []
        for task in rows:
            internal = _task_internal_id(task)
            if internal is None:
                result.append(task)
                continue
            state = readiness(conn, task, current_week)
            if bool(state.ready):
                result.append(task)
        return result

    def ensure_snapshot(conn: Any, current_week: int, max_items: int, tasks: list[dict[str, Any]]):
        eligible: list[dict[str, Any]] = []
        for task in tasks:
            internal = _task_internal_id(task)
            if internal is None:
                eligible.append(task)
                continue
            calendar_ready, _ = _weekday_schedule_ready(conn, internal)
            # Once its scheduled weekday arrives, keep the exercise in the
            # candidate pool even when its prerequisite is incomplete. The
            # existing planner will show it grey and locked with the exact
            # reason. Before that date, it cannot enter Today's Focus.
            if calendar_ready:
                eligible.append(task)
        _clear_stale_focus(conn)
        return original_snapshot(conn, current_week, max_items, eligible)

    def daily_plan(conn: Any, current_week: int, max_items: int = 5) -> list[dict[str, Any]]:
        rows = list(original_daily_plan(conn, current_week, max_items))
        filtered: list[dict[str, Any]] = []
        changed = False
        for task in rows:
            internal = _task_internal_id(task)
            if internal is not None:
                calendar_ready, _ = _weekday_schedule_ready(conn, internal)
                if not calendar_ready:
                    changed = True
                    continue
            filtered.append(task)
        if changed:
            _clear_stale_focus(conn)
            conn.commit()
        return filtered

    unified_tasks._readiness = readiness
    unified_tasks.ready_tasks = ready_tasks
    unified_tasks._ensure_daily_snapshot = ensure_snapshot
    unified_tasks.daily_plan = daily_plan
    unified_tasks._duckdb_curriculum_policy_installed = True


def install(CareerAccelerator: type | None = None) -> None:
    """Install the cumulative policy exactly once."""
    del CareerAccelerator
    global _INSTALLED
    if _INSTALLED:
        return
    _apply_catalog_overlay()
    _install_readiness_and_sync()
    _install_unified_task_policy()
    _install_runner_prompt_audit()
    _INSTALLED = True
