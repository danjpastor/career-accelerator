"""v10.46.30 current DataCamp-track and task-metadata compatibility layer.

The legacy Career Accelerator reconciler can still materialize a retired Week 6
Database Design block followed immediately by Power BI (Week 7) and Python
(Week 8). This adapter runs after that reconciler and restores the current
Associate Data Analyst in SQL continuation:

Week 6: Introduction to Statistics -> Exploratory Data Analysis in SQL
Week 7: Data-Driven Decision Making in SQL -> Understanding Data Visualization
        -> Data Communication Concepts

Existing Power BI and Python chapter identities are preserved, but moved one
week later (to Weeks 8 and 9 respectively). Retired Database Design completion
is archived, never transferred to unrelated replacement coursework.
"""
from __future__ import annotations

import json
import re
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

PATCH_MARKER = "v10.46.35-datacamp-completion-and-focus-fix"
POST_CORE_SCHEDULE_MARKER = "v10.46.38-canonical-datacamp-schedule"


def _alignment_error_log() -> Path:
    # application/career_app/services/<this file> -> repository root
    return Path(__file__).resolve().parents[3] / "logs" / "datacamp-track-alignment-error.log"


def _log_alignment_error(exc: BaseException) -> None:
    """Record curriculum-realignment failures without taking down startup."""
    try:
        path = _alignment_error_log()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {PATCH_MARKER}\n")
            handle.write(f"{type(exc).__name__}: {exc}\n")
            handle.write(traceback.format_exc())
            if not traceback.format_exc().endswith("\n"):
                handle.write("\n")
    except Exception:
        # Logging must never become a second startup failure.
        pass


def _target(key, course, chapter, name, week, weekday, day_index, url, minutes=60):
    return {
        "key": key,
        "course": course,
        "chapter": int(chapter),
        "name": name,
        "week": int(week),
        "weekday": weekday,
        "day_index": int(day_index),
        "url": url,
        "minutes": int(minutes),
    }


STATS_URL = "https://www.datacamp.com/courses/introduction-to-statistics"
EDA_URL = "https://www.datacamp.com/courses/exploratory-data-analysis-in-sql"
DECISION_URL = "https://www.datacamp.com/courses/data-driven-decision-making-in-sql"
VIZ_URL = "https://www.datacamp.com/courses/understanding-data-visualization"
COMM_URL = "https://www.datacamp.com/courses/data-communication-concepts"

TARGETS = (
    _target("w06_intro_stats_01", "Introduction to Statistics", 1, "Summary Statistics", 6, "Tuesday", 1, STATS_URL),
    _target("w06_intro_stats_02", "Introduction to Statistics", 2, "Probability and distributions", 6, "Tuesday", 1, STATS_URL),
    _target("w06_intro_stats_03", "Introduction to Statistics", 3, "More Distributions and the Central Limit Theorem", 6, "Wednesday", 2, STATS_URL),
    _target("w06_intro_stats_04", "Introduction to Statistics", 4, "Correlation and Hypothesis Testing", 6, "Wednesday", 2, STATS_URL),
    _target("w06_eda_sql_01", "Exploratory Data Analysis in SQL", 1, "What's in the Database?", 6, "Thursday", 3, EDA_URL),
    _target("w06_eda_sql_02", "Exploratory Data Analysis in SQL", 2, "Summarizing and Aggregating Numeric Data", 6, "Thursday", 3, EDA_URL),
    _target("w06_eda_sql_03", "Exploratory Data Analysis in SQL", 3, "Exploring Categorical Data and Unstructured Text", 6, "Friday", 4, EDA_URL),
    _target("w06_eda_sql_04", "Exploratory Data Analysis in SQL", 4, "Working with Dates and Timestamps", 6, "Friday", 4, EDA_URL),
    _target("w07_decision_sql_01", "Data-Driven Decision Making in SQL", 1, "Introduction to business intelligence for a online movie rental database", 7, "Monday", 0, DECISION_URL),
    _target("w07_decision_sql_02", "Data-Driven Decision Making in SQL", 2, "Decision Making with simple SQL queries", 7, "Monday", 0, DECISION_URL),
    _target("w07_decision_sql_03", "Data-Driven Decision Making in SQL", 3, "Data Driven Decision Making with advanced SQL queries", 7, "Tuesday", 1, DECISION_URL),
    _target("w07_decision_sql_04", "Data-Driven Decision Making in SQL", 4, "Data Driven Decision Making with OLAP SQL queries", 7, "Tuesday", 1, DECISION_URL),
    _target("w07_data_viz_01", "Understanding Data Visualization", 1, "Visualizing distributions", 7, "Wednesday", 2, VIZ_URL),
    _target("w07_data_viz_02", "Understanding Data Visualization", 2, "Visualizing two variables", 7, "Wednesday", 2, VIZ_URL),
    _target("w07_data_viz_03", "Understanding Data Visualization", 3, "The color and the shape", 7, "Thursday", 3, VIZ_URL),
    _target("w07_data_viz_04", "Understanding Data Visualization", 4, "99 problems but a plot ain't one of them", 7, "Thursday", 3, VIZ_URL),
    _target("w07_data_communication_01", "Data Communication Concepts", 1, "Storytelling with Data", 7, "Thursday", 3, COMM_URL),
    _target("w07_data_communication_02", "Data Communication Concepts", 2, "Preparing to Communicate the Data", 7, "Friday", 4, COMM_URL),
    _target("w07_data_communication_03", "Data Communication Concepts", 3, "Structuring Written Reports", 7, "Friday", 4, COMM_URL),
    _target("w07_data_communication_04", "Data Communication Concepts", 4, "Building Compelling Oral Presentations", 7, "Friday", 4, COMM_URL),
)
TARGET_BY_KEY = {item["key"]: item for item in TARGETS}
TARGET_KEYS = tuple(TARGET_BY_KEY)

# Complete learner-facing metadata for every chapter introduced by the current
# DataCamp-track realignment.  Keep this separate from scheduling so a valid
# chapter can never display an "unavailable metadata" fallback simply because
# it is not present in the retired static chapter catalog.
LEARNING_FOCUS = {
    "w06_intro_stats_01": "Summarize numerical data with measures of center, spread, and distribution shape.",
    "w06_intro_stats_02": "Reason about probability, sampling, and common probability distributions.",
    "w06_intro_stats_03": "Connect sampling distributions and the central limit theorem to statistical inference.",
    "w06_intro_stats_04": "Interpret correlation and hypothesis tests without confusing association with causation.",
    "w06_eda_sql_01": "Inspect schemas, table structure, row counts, and data quality before analysis.",
    "w06_eda_sql_02": "Use summary statistics and grouped aggregates to explore numeric variables.",
    "w06_eda_sql_03": "Profile categorical values and unstructured text for patterns and data-quality issues.",
    "w06_eda_sql_04": "Explore dates and timestamps with SQL date/time functions and time-based summaries.",
    "w07_decision_sql_01": "Frame business questions and explore the movie-rental data with decision-focused SQL.",
    "w07_decision_sql_02": "Use filtering, aggregation, joins, and subqueries to answer business questions.",
    "w07_decision_sql_03": "Use advanced SQL patterns to compare groups and support data-driven decisions.",
    "w07_decision_sql_04": "Use OLAP-style aggregation to analyze data across multiple dimensions.",
    "w07_data_viz_01": "Choose charts that reveal distributions, variation, and unusual values.",
    "w07_data_viz_02": "Choose visual encodings that clearly show relationships between two variables.",
    "w07_data_viz_03": "Use color, shape, and other encodings intentionally without distorting the message.",
    "w07_data_viz_04": "Diagnose misleading or ineffective charts and choose a clearer visualization.",
    "w07_data_communication_01": "Build a data story around evidence, audience needs, and a clear takeaway.",
    "w07_data_communication_02": "Prepare communication around audience, purpose, evidence, and level of detail.",
    "w07_data_communication_03": "Structure written reports so findings, evidence, and recommendations are easy to follow.",
    "w07_data_communication_04": "Build oral presentations that lead with the decision and support it with evidence.",
}

# These are durable skill-evidence mappings, not day locks.  They use only
# Career Accelerator's existing skill keys and intentionally preserve the
# conservative Chapter-4 gates for visualization/storytelling.
SKILL_EVIDENCE_BY_TARGET = {
    "w06_intro_stats_01": {"statistics_foundations", "descriptive_statistics"},
    "w06_intro_stats_02": {"statistics_foundations"},
    "w06_intro_stats_03": {"statistics_foundations", "inferential_statistics"},
    "w06_intro_stats_04": {"inferential_statistics", "hypothesis_testing"},
    "w06_eda_sql_01": {"sql_validation"},
    "w06_eda_sql_02": {"sql_aggregation"},
    "w06_eda_sql_03": {"data_cleaning", "sql_validation"},
    "w06_eda_sql_04": {"sql_date_logic", "sql_validation"},
    "w07_decision_sql_01": {"sql_querying", "sql_aggregation", "sql_date_logic"},
    "w07_decision_sql_02": {"sql_aggregation", "sql_joins", "sql_subqueries"},
    "w07_decision_sql_03": {"sql_subqueries", "sql_intermediate"},
    "w07_decision_sql_04": {"sql_aggregation", "sql_intermediate"},
    "w07_data_viz_04": {"visualization_foundations"},
    "w07_data_communication_04": {"data_storytelling"},
}

STALE_KEYS = tuple(f"w06_database_design_{number:02d}" for number in range(1, 5))

PRIMARY_REPLACEMENTS = {
    "w06_database_design_01": "w06_intro_stats_01",
    "w06_database_design_02": "w06_intro_stats_03",
    "w06_database_design_03": "w06_eda_sql_01",
    "w06_database_design_04": "w06_eda_sql_03",
}
CLONE_FROM = {
    "w06_intro_stats_02": "w06_database_design_01",
    "w06_intro_stats_04": "w06_database_design_02",
    "w06_eda_sql_02": "w06_database_design_03",
    "w06_eda_sql_04": "w06_database_design_04",
}

# Stable internal SQL IDs. Exercises 30-33 reinforce Data-Driven Decision
# Making Chapters 1-4 and are spaced Mon-Thu for retrieval practice.
SQL_SCHEDULE = {
    30: (6, 3), 31: (6, 3), 32: (6, 4), 33: (6, 4),
    8: (7, 0), 9: (7, 1), 10: (7, 2), 18: (7, 3),
}


def _tables(conn):
    return {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def _columns(conn, table):
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _row_dict(row):
    return {key: row[key] for key in row.keys()}


def _current_week(conn):
    if "program_state" not in _tables(conn):
        return None
    cols = set(_columns(conn, "program_state"))
    if "current_week" not in cols:
        return None
    row = conn.execute("SELECT current_week FROM program_state ORDER BY id LIMIT 1").fetchone()
    return int(row[0]) if row is not None and row[0] is not None else None


def _target_date(conn, week, day_index):
    current = _current_week(conn)
    if current is None:
        return None
    monday = date.today() - timedelta(days=date.today().weekday())
    return (monday + timedelta(days=(int(week) - current) * 7 + int(day_index))).isoformat()


def _insert_clone(conn, table, template, overrides):
    cols = _columns(conn, table)
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    pk_cols = {str(row[1]) for row in info if int(row[5] or 0) > 0}
    values = dict(template)
    values.update(overrides)
    use = [c for c in cols if c in values and (c not in pk_cols or c in overrides)]
    if not use:
        raise RuntimeError(f"Cannot clone {table}: no insertable columns")
    sql = f"INSERT INTO {table} ({','.join(use)}) VALUES ({','.join('?' for _ in use)})"
    cur = conn.execute(sql, tuple(values[c] for c in use))
    return int(cur.lastrowid) if cur.lastrowid is not None else None


def _progress_overrides(target, columns):
    result = {}
    focus = LEARNING_FOCUS[target["key"]]
    aliases = {
        "chapter_key": target["key"],
        "provider": "DataCamp",
        "source": "DataCamp",
        "source_label": f"DataCamp • {target['course']}",
        "course_name": target["course"],
        "course": target["course"],
        "chapter_number": target["chapter"],
        "chapter": target["chapter"],
        "chapter_count": 4,
        "chapter_name": target["name"],
        "title": target["name"],
        "description": focus,
        "learning_focus": focus,
        "estimated_minutes": target["minutes"],
        "minutes": target["minutes"],
        "week": target["week"],
        "scheduled_week": target["week"],
        "weekday": target["weekday"],
        "scheduled_day": target["weekday"],
        "day_index": target["day_index"],
        "url": target["url"],
        "starter_path": target["url"],
        "course_url": target["url"],
        "chapter_url": target["url"],
    }
    for key, value in aliases.items():
        if key in columns:
            result[key] = value
    if "status" in columns:
        result["status"] = "Not Started"
    for key in ("completed_date", "completed_at"):
        if key in columns:
            result[key] = None
    return result


def _archive_stale_progress(conn, stale):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS datacamp_track_alignment_archive (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               archived_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
               chapter_key TEXT NOT NULL,
               payload_json TEXT NOT NULL,
               reason TEXT NOT NULL
           )"""
    )
    for key, payload in stale.items():
        exists = conn.execute(
            "SELECT 1 FROM datacamp_track_alignment_archive WHERE chapter_key=? AND reason=? LIMIT 1",
            (key, PATCH_MARKER),
        ).fetchone()
        if exists is None:
            conn.execute(
                "INSERT INTO datacamp_track_alignment_archive(chapter_key,payload_json,reason) VALUES(?,?,?)",
                (key, json.dumps(payload, default=str), PATCH_MARKER),
            )


def _ensure_progress(conn):
    if "datacamp_chapter_progress" not in _tables(conn):
        return
    table = "datacamp_chapter_progress"
    cols = _columns(conn, table)
    if "chapter_key" not in cols:
        return
    stale = {
        str(row["chapter_key"]): _row_dict(row)
        for row in conn.execute(
            f"SELECT * FROM {table} WHERE chapter_key IN ({','.join('?' for _ in STALE_KEYS)})",
            STALE_KEYS,
        ).fetchall()
    }
    _archive_stale_progress(conn, stale)
    templates = dict(stale)
    if not templates:
        row = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        if row is not None:
            templates[STALE_KEYS[0]] = _row_dict(row)
    conn.execute(
        f"DELETE FROM {table} WHERE chapter_key IN ({','.join('?' for _ in STALE_KEYS)})",
        STALE_KEYS,
    )
    for target in TARGETS:
        existing = conn.execute(f"SELECT 1 FROM {table} WHERE chapter_key=?", (target["key"],)).fetchone()
        if existing is not None:
            # Keep completion, but repair descriptive/scheduling metadata if those columns exist.
            overrides = _progress_overrides(target, set(cols))
            overrides.pop("status", None)
            overrides.pop("completed_date", None)
            overrides.pop("completed_at", None)
            if overrides:
                conn.execute(
                    f"UPDATE {table} SET " + ",".join(f"{k}=?" for k in overrides) + " WHERE chapter_key=?",
                    tuple(overrides.values()) + (target["key"],),
                )
            continue
        source_key = next((old for old, new in PRIMARY_REPLACEMENTS.items() if new == target["key"]), None)
        source_key = source_key or CLONE_FROM.get(target["key"]) or STALE_KEYS[0]
        template = templates.get(source_key) or next(iter(templates.values()), {})
        if template:
            _insert_clone(conn, table, template, _progress_overrides(target, set(cols)))

    # v10.46.38: legacy chapter progress follows the canonical curriculum.
    try:
        from career_app.data.datacamp_curriculum import chapter_for_key
    except Exception:
        chapter_for_key = None

    if callable(chapter_for_key):
        rows = conn.execute(
            f"SELECT chapter_key FROM {table} ORDER BY chapter_key"
        ).fetchall()
        for row in rows:
            key = str(row[0])
            if key in TARGET_KEYS:
                continue
            chapter = chapter_for_key(key)
            if chapter is None:
                continue

            assignments = {}
            if "week" in cols:
                assignments["week"] = int(chapter.week)
            if "scheduled_week" in cols:
                assignments["scheduled_week"] = int(chapter.week)
            if "scheduled_date" in cols:
                assignments["scheduled_date"] = _target_date(
                    conn, int(chapter.week), int(chapter.weekday)
                )

            if assignments:
                conn.execute(
                    f"UPDATE {table} SET "
                    + ",".join(f"{name}=?" for name in assignments)
                    + " WHERE chapter_key=?",
                    tuple(assignments.values()) + (key,),
                )


def _task_rows(conn):
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return {}
    rows = conn.execute(
        """SELECT s.*,m.managed_key AS _managed_key
           FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
           WHERE m.managed_key IN (?,?,?,?)""",
        tuple(f"datacamp:{key}" for key in STALE_KEYS),
    ).fetchall()
    return {str(row["_managed_key"]).split(":", 1)[1]: _row_dict(row) for row in rows}


def _metadata_row(conn, task_id):
    row = conn.execute("SELECT * FROM task_metadata WHERE task_id=?", (int(task_id),)).fetchone()
    return _row_dict(row) if row is not None else {}


def _label(target):
    return f"DataCamp • {target['course']} — Chapter {target['chapter']}: {target['name']}"


def _item_value(item, key, default=None):
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(key, default)
    try:
        return item[key]
    except (KeyError, IndexError, TypeError):
        return default


def _target_from_managed(value):
    raw = str(value or "").strip()
    if raw.startswith("datacamp:"):
        raw = raw.split(":", 1)[1]
    return TARGET_BY_KEY.get(raw)


def _target_from_label(value):
    """Resolve a current chapter from course name + chapter number."""
    text = " ".join(
        str(value or "")
        .replace("\u2014", " - ")
        .replace("\u2013", " - ")
        .replace("\u2022", " ")
        .split()
    )
    if not text:
        return None
    folded = text.casefold()
    for candidate in TARGETS:
        if candidate["course"].casefold() not in folded:
            continue
        if re.search(
            rf"\bchapter\s*{int(candidate['chapter'])}\b",
            folded,
            flags=re.IGNORECASE,
        ):
            return candidate
    return None


def target_for_task(conn, task_id):
    """Resolve a current DataCamp chapter without depending on one DB key."""
    if conn is None:
        return None
    try:
        row = conn.execute(
            """SELECT m.managed_key,s.label
               FROM sprint_tasks s
               LEFT JOIN task_metadata m ON m.task_id=s.id
               WHERE s.id=?""",
            (int(task_id),),
        ).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    target = _target_from_managed(_item_value(row, "managed_key", ""))
    if target is not None:
        return target
    return _target_from_label(_item_value(row, "label", ""))


def target_for_item(conn, item):
    """Resolve a current chapter from all final planner task shapes."""
    for key in ("managed_key", "target_key", "chapter_key", "source_key"):
        target = _target_from_managed(_item_value(item, key))
        if target is not None:
            return target

    nested = _item_value(item, "metadata")
    if isinstance(nested, dict):
        for key in ("managed_key", "target_key", "chapter_key", "source_key"):
            target = _target_from_managed(nested.get(key))
            if target is not None:
                return target

    task_id = _item_value(item, "task_id", _item_value(item, "id"))
    if conn is not None and task_id is not None:
        target = target_for_task(conn, task_id)
        if target is not None:
            return target

    for key in ("label", "display_title", "title"):
        target = _target_from_label(_item_value(item, key, ""))
        if target is not None:
            return target
    return None


def metadata_for_target(target):
    """Return the complete normalized metadata contract for one current chapter."""
    focus = LEARNING_FOCUS[target["key"]]
    skills = sorted(SKILL_EVIDENCE_BY_TARGET.get(target["key"], set()))
    return {
        "provider": "DataCamp",
        "source": "DataCamp",
        "source_label": f"DataCamp • {target['course']}",
        "chapter_key": target["key"],
        "course": target["course"],
        "course_name": target["course"],
        "chapter": int(target["chapter"]),
        "chapter_number": int(target["chapter"]),
        "chapter_count": 4,
        "chapter_name": target["name"],
        "title": target["name"],
        "learning_focus": focus,
        "description": focus,
        "week": int(target["week"]),
        "scheduled_week": int(target["week"]),
        "weekday": target["weekday"],
        "scheduled_day": target["weekday"],
        "day_index": int(target["day_index"]),
        "estimated_minutes": int(target["minutes"]),
        "minutes": int(target["minutes"]),
        "url": target["url"],
        "course_url": target["url"],
        "chapter_url": target["url"],
        "starter_path": target["url"],
        "skills": skills,
    }


def metadata_for_task(conn, task_id):
    target = target_for_task(conn, task_id)
    return metadata_for_target(target) if target is not None else None


def detail_for_target(target):
    """Compact second-line text shared by Focus, Next Tasks, and sprint views."""
    return f"Chapter {target['chapter']} of 4 • {LEARNING_FOCUS[target['key']]}"


def _enrich_item(conn, item):
    """Replace stale/missing DataCamp presentation metadata in a planner item."""
    if not isinstance(item, dict):
        try:
            item = {key: item[key] for key in item.keys()}
        except Exception:
            return item

    enriched = dict(item)
    target = target_for_item(conn, enriched)
    if target is None:
        return enriched

    meta = metadata_for_target(target)
    enriched["display_source"] = detail_for_target(target)
    enriched["source_label"] = meta["source_label"]
    enriched["detail"] = detail_for_target(target)
    enriched["provider"] = "DataCamp"
    enriched["chapter_key"] = target["key"]
    enriched["course"] = target["course"]
    enriched["course_name"] = target["course"]
    enriched["chapter"] = int(target["chapter"])
    enriched["chapter_number"] = int(target["chapter"])
    enriched["chapter_count"] = 4
    enriched["chapter_name"] = target["name"]
    enriched["learning_focus"] = meta["learning_focus"]
    enriched["chapter_url"] = target["url"]
    enriched["course_url"] = target["url"]
    enriched["starter_path"] = target["url"]
    enriched["estimated_minutes"] = int(enriched.get("estimated_minutes") or target["minutes"])
    enriched.setdefault("metadata_label", "DataCamp")
    return enriched


def _enrich_result(conn, result):
    if isinstance(result, list):
        return [_enrich_result(conn, value) for value in result]
    if isinstance(result, tuple):
        return tuple(_enrich_result(conn, value) for value in result)
    if isinstance(result, dict):
        value = _enrich_item(conn, result)
        for key in ("tasks", "items", "ready", "upcoming", "coming_up"):
            if key in value and isinstance(value[key], (list, tuple, dict)):
                value[key] = _enrich_result(conn, value[key])
        return value
    return result


def _wrap_result_function(module, name):
    original = getattr(module, name, None)
    if not callable(original) or getattr(original, "_v104630_datacamp_metadata", False):
        return

    def wrapped(*args, **kwargs):
        result = original(*args, **kwargs)
        conn = kwargs.get("conn")
        if conn is None and args and hasattr(args[0], "execute"):
            conn = args[0]
        return _enrich_result(conn, result) if conn is not None else result

    wrapped._v104630_datacamp_metadata = True
    wrapped.__name__ = getattr(original, "__name__", name)
    wrapped.__doc__ = getattr(original, "__doc__", None)
    setattr(module, name, wrapped)


def _install_metadata_bridges():
    """Bridge current-track metadata across every active planner presentation path."""
    from career_app.services import completion_contract, tracks

    # Complete the skill-evidence catalog without rewriting the newer tracks.py
    # that may contain unrelated fixes made after the original realignment.
    evidence = getattr(tracks, "DATACAMP_SKILL_EVIDENCE", None)
    if isinstance(evidence, dict):
        for key, skills in SKILL_EVIDENCE_BY_TARGET.items():
            evidence.setdefault(key, set()).update(skills)

    original_focus_detail = getattr(completion_contract, "focus_detail", None)
    if callable(original_focus_detail) and not getattr(
        original_focus_detail, "_v104630_datacamp_metadata", False
    ):
        def focus_detail(conn, item, detail, state, *args, **kwargs):
            target = target_for_item(conn, item)
            if target is not None:
                return detail_for_target(target)
            return original_focus_detail(conn, item, detail, state, *args, **kwargs)

        focus_detail._v104630_datacamp_metadata = True
        completion_contract.focus_detail = focus_detail

    original_presentation = getattr(tracks, "focus_presentation", None)
    if callable(original_presentation) and not getattr(
        original_presentation, "_v104630_datacamp_metadata", False
    ):
        def focus_presentation(conn, item, *args, **kwargs):
            target = target_for_item(conn, item)
            if target is not None:
                return {
                    "style_category": "Learning",
                    "title": str(_item_value(item, "label", "") or _label(target)),
                    "detail": detail_for_target(target),
                }
            return original_presentation(conn, item, *args, **kwargs)

        focus_presentation._v104630_datacamp_metadata = True
        tracks.focus_presentation = focus_presentation

    original_source = getattr(tracks, "source_for_task", None)
    if callable(original_source) and not getattr(
        original_source, "_v104630_datacamp_metadata", False
    ):
        def source_for_task(conn, task_id, *args, **kwargs):
            target = target_for_task(conn, task_id)
            if target is not None:
                return detail_for_target(target)
            return original_source(conn, task_id, *args, **kwargs)

        source_for_task._v104630_datacamp_metadata = True
        tracks.source_for_task = source_for_task

    # Current/future day rows pass through sprint_day_planner before the final
    # daily policy is installed. Enrich them here so Next Tasks' explicit
    # display_source can never retain an old "metadata unavailable" string.
    try:
        from career_app.services import sprint_day_planner
        for name in ("current_sprint_day_groups", "promoted_tasks"):
            _wrap_result_function(sprint_day_planner, name)
    except Exception:
        pass

    # Cross-week catch-up and several secondary surfaces read unified_tasks
    # directly. These wrappers remain safe even when daily_task_policy later
    # replaces its daily_plan/next_tasks functions.
    try:
        from career_app.services import unified_tasks
        for name in ("all_tasks", "ready_tasks", "daily_plan", "next_tasks", "coming_up"):
            _wrap_result_function(unified_tasks, name)
    except Exception:
        pass

    # daily_task_policy is installed later in main.py. Wrapping its normalization
    # helper now makes every subsequently-created Today/Next/Coming Soon item
    # receive the same metadata, regardless of which queue built it.
    try:
        from career_app.services import daily_task_policy
        original_normalize = getattr(daily_task_policy, "_normalize_scheduled_task", None)
        if callable(original_normalize) and not getattr(
            original_normalize, "_v104630_datacamp_metadata", False
        ):
            def normalize_scheduled_task(task, *args, **kwargs):
                item = original_normalize(task, *args, **kwargs)
                return _enrich_item(None, item)

            normalize_scheduled_task._v104630_datacamp_metadata = True
            daily_task_policy._normalize_scheduled_task = normalize_scheduled_task
    except Exception:
        pass


def install_final_metadata_bridges():
    """Reapply adapters after every later runtime planner policy installs."""
    _install_metadata_bridges()
    try:
        from career_app.services import daily_task_policy
        cache = getattr(daily_task_policy, "_GROUP_CACHE", None)
        if isinstance(cache, dict):
            cache.clear()
    except Exception:
        pass


def _target_sort(target):
    return 9462400 + list(TARGET_BY_KEY).index(target["key"])


def _completed_target_keys(conn):
    if "datacamp_chapter_progress" not in _tables(conn):
        return set()
    cols = set(_columns(conn, "datacamp_chapter_progress"))
    if not {"chapter_key", "status"} <= cols:
        return set()
    return {
        str(row[0]) for row in conn.execute(
            "SELECT chapter_key FROM datacamp_chapter_progress WHERE status='Completed'"
        ).fetchall()
    }


def _prereq_for(key):
    keys = list(TARGET_BY_KEY)
    idx = keys.index(key)
    return keys[idx - 1] if idx > 0 else None


def _update_task(conn, task_id, target, *, preserve_completion=False):
    completed = None
    if preserve_completion:
        row = conn.execute("SELECT completed FROM sprint_tasks WHERE id=?", (int(task_id),)).fetchone()
        completed = int(row[0]) if row is not None and row[0] is not None else 0
    conn.execute(
        "UPDATE sprint_tasks SET week=?,label=?,sort_order=?,completed=? WHERE id=?",
        (int(target["week"]), _label(target), _target_sort(target), int(completed or 0), int(task_id)),
    )
    cols = set(_columns(conn, "task_metadata"))
    meta = metadata_for_target(target)
    assignments = {"managed_key": f"datacamp:{target['key']}"}
    if "status" in cols and not preserve_completion:
        assignments["status"] = "Not Started"

    optional = {
        "estimated_minutes": int(target["minutes"]),
        "category": "Learning",
        "priority": 1,
        "description": meta["learning_focus"],
        "definition_of_done": (
            f"Finish DataCamp {target['course']}, Chapter {target['chapter']} "
            f"({target['name']}), including its required exercises, then mark this task complete."
        ),
        "starter_path": target["url"],
        "source_label": meta["source_label"],
        "display_source": detail_for_target(target),
        "provider": "DataCamp",
        "course_name": target["course"],
        "chapter_number": int(target["chapter"]),
        "chapter_count": 4,
        "chapter_name": target["name"],
        "learning_focus": meta["learning_focus"],
        "url": target["url"],
        "course_url": target["url"],
        "chapter_url": target["url"],
    }
    for key, value in optional.items():
        if key in cols:
            assignments[key] = value

    if "deferred_until" in cols:
        assignments["deferred_until"] = _target_date(
            conn, target["week"], target["day_index"]
        )
    sql = "UPDATE task_metadata SET " + ",".join(f"{key}=?" for key in assignments) + " WHERE task_id=?"
    conn.execute(sql, tuple(assignments.values()) + (int(task_id),))


def _clone_task(conn, source_task_id, target):
    row = conn.execute("SELECT * FROM sprint_tasks WHERE id=?", (int(source_task_id),)).fetchone()
    if row is None:
        raise RuntimeError("Could not find source DataCamp task for clone")
    srow = _row_dict(row)
    srow.update({"week": int(target["week"]), "label": _label(target), "completed": 0})
    if "sort_order" in srow:
        srow["sort_order"] = _target_sort(target)
    new_id = _insert_clone(conn, "sprint_tasks", srow, {})
    if new_id is None:
        raise RuntimeError("Could not create DataCamp task")
    mrow = _metadata_row(conn, source_task_id)
    mrow["task_id"] = new_id
    if "managed_key" in mrow:
        mrow["managed_key"] = f"datacamp:{target['key']}"
    _insert_clone(
        conn,
        "task_metadata",
        mrow,
        {"task_id": new_id, "managed_key": f"datacamp:{target['key']}"},
    )
    _update_task(conn, new_id, target)
    return new_id


def _remove_task(conn, task_id):
    for table, column in (("daily_focus", "task_id"), ("track_tasks", "task_id"), ("task_sprint_schedule", "task_id")):
        if table in _tables(conn) and column in _columns(conn, table):
            conn.execute(f"DELETE FROM {table} WHERE {column}=?", (int(task_id),))
    conn.execute("DELETE FROM task_metadata WHERE task_id=?", (int(task_id),))
    conn.execute("DELETE FROM sprint_tasks WHERE id=?", (int(task_id),))


def _ensure_tasks(conn):
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return
    stale = _task_rows(conn)
    target_task_ids = {}
    for old_key, new_key in PRIMARY_REPLACEMENTS.items():
        row = stale.get(old_key)
        existing = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key=? ORDER BY task_id LIMIT 1",
            (f"datacamp:{new_key}",),
        ).fetchone()
        if existing is not None:
            target_task_ids[new_key] = int(existing[0])
        elif row is not None:
            task_id = int(row["id"])
            _update_task(conn, task_id, TARGET_BY_KEY[new_key])
            target_task_ids[new_key] = task_id

    for new_key, old_key in CLONE_FROM.items():
        existing = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (f"datacamp:{new_key}",)).fetchone()
        if existing is not None:
            target_task_ids[new_key] = int(existing[0])
            continue
        source = stale.get(old_key)
        source_id = int(source["id"]) if source is not None else target_task_ids.get(PRIMARY_REPLACEMENTS.get(old_key))
        if source_id is not None:
            target_task_ids[new_key] = _clone_task(conn, source_id, TARGET_BY_KEY[new_key])

    # Ensure all existing Week 6 replacement tasks have current metadata.
    for key in list(TARGET_BY_KEY)[:8]:
        row = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (f"datacamp:{key}",)).fetchone()
        if row is not None:
            target_task_ids[key] = int(row[0])
            _update_task(conn, int(row[0]), TARGET_BY_KEY[key], preserve_completion=True)

    # Build Week 7 current-track continuation from a canonical DataCamp task.
    source_id = next(iter(target_task_ids.values()), None)
    if source_id is None:
        row = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key LIKE 'datacamp:%' ORDER BY task_id LIMIT 1"
        ).fetchone()
        source_id = int(row[0]) if row is not None else None
    if source_id is not None:
        for target in TARGETS[8:]:
            row = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (f"datacamp:{target['key']}",)).fetchone()
            if row is None:
                target_task_ids[target["key"]] = _clone_task(conn, source_id, target)
            else:
                target_task_ids[target["key"]] = int(row[0])
                _update_task(conn, int(row[0]), target, preserve_completion=True)

    # Remove retired Database Design tasks that a legacy reconciler recreates.
    stale_managed = tuple(f"datacamp:{key}" for key in STALE_KEYS)
    rows = conn.execute(
        f"SELECT task_id FROM task_metadata WHERE managed_key IN ({','.join('?' for _ in stale_managed)})",
        stale_managed,
    ).fetchall()
    for row in rows:
        _remove_task(conn, int(row[0]))

    # v10.46.33: restore the complete current continuation from any surviving
    # canonical DataCamp task. This removes the old Database Design dependency.
    _ensure_all_current_tasks(conn)


def _schedule_row(conn, task_id, week, day_index):
    if "task_sprint_schedule" not in _tables(conn):
        return
    cols = set(_columns(conn, "task_sprint_schedule"))
    if "task_id" not in cols:
        return
    updates = {}
    target_date = _target_date(conn, week, day_index)
    if target_date:
        for name in ("scheduled_date", "assigned_date", "task_date", "date"):
            if name in cols:
                updates[name] = target_date
                break
    for name in ("week", "sprint_week"):
        if name in cols:
            updates[name] = int(week)
            break
    for name in ("day_index", "weekday_index"):
        if name in cols:
            updates[name] = int(day_index)
            break
    if not updates:
        return
    exists = conn.execute("SELECT 1 FROM task_sprint_schedule WHERE task_id=?", (int(task_id),)).fetchone()
    if exists is not None:
        conn.execute(
            "UPDATE task_sprint_schedule SET " + ",".join(f"{k}=?" for k in updates) + " WHERE task_id=?",
            tuple(updates.values()) + (int(task_id),),
        )


def _refresh_target_readiness(conn):
    if not {"task_metadata", "datacamp_chapter_progress"} <= _tables(conn):
        return
    cols = set(_columns(conn, "task_metadata"))
    if not ({"prerequisite_state", "prerequisite_reason"} & cols):
        return
    completed = _completed_target_keys(conn)
    for target in TARGETS:
        row = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (f"datacamp:{target['key']}",)).fetchone()
        if row is None:
            continue
        prereq = _prereq_for(target["key"])
        ready = prereq is None or prereq in completed
        assignments = {}
        if "prerequisite_state" in cols:
            assignments["prerequisite_state"] = "Ready" if ready else "Locked"
        if "prerequisite_reason" in cols:
            if ready:
                assignments["prerequisite_reason"] = None
            else:
                p = TARGET_BY_KEY[prereq]
                assignments["prerequisite_reason"] = f"Complete {p['course']} — Chapter {p['chapter']} first."
        if assignments:
            conn.execute(
                "UPDATE task_metadata SET " + ",".join(f"{k}=?" for k in assignments) + " WHERE task_id=?",
                tuple(assignments.values()) + (int(row[0]),),
            )


def _move_legacy_learning(conn):
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return

    try:
        from career_app.data.datacamp_curriculum import chapter_for_key
    except Exception:
        return

    target_managed = {f"datacamp:{key}" for key in TARGET_KEYS}
    rows = conn.execute(
        """SELECT m.task_id,m.managed_key,s.week,s.completed
           FROM task_metadata m
           JOIN sprint_tasks s ON s.id=m.task_id
           WHERE m.managed_key LIKE 'datacamp:%'
           ORDER BY m.task_id"""
    ).fetchall()

    legacy = []
    for row in rows:
        task_id = int(row[0])
        managed = str(row[1])
        if managed in target_managed:
            continue
        key = managed.split(":", 1)[1]
        chapter = chapter_for_key(key)
        if chapter is None:
            continue
        legacy.append((task_id, managed, int(row[2]), bool(row[3]), chapter))

    for idx, (task_id, _managed, current_week, completed, chapter) in enumerate(legacy):
        target_week = int(chapter.week)
        day_index = int(chapter.weekday)

        if (
            current_week != target_week
            and "sort_order" in _columns(conn, "sprint_tasks")
        ):
            conn.execute(
                "UPDATE sprint_tasks SET sort_order=? WHERE id=?",
                (9463000 + target_week * 1000 + idx, task_id),
            )

        conn.execute(
            "UPDATE sprint_tasks SET week=? WHERE id=?",
            (target_week, task_id),
        )

        if "deferred_until" in _columns(conn, "task_metadata"):
            conn.execute(
                "UPDATE task_metadata SET deferred_until=? WHERE task_id=?",
                (
                    None if completed else _target_date(conn, target_week, day_index),
                    task_id,
                ),
            )

        _schedule_row(conn, task_id, target_week, day_index)


def _realign_sql_schedule(conn):
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return
    for internal_id, (week, day_index) in SQL_SCHEDULE.items():
        managed = f"roadmap_v1026:duckdb:{internal_id}"
        row = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (managed,)).fetchone()
        if row is None:
            continue
        task_id = int(row[0])
        if "sort_order" in _columns(conn, "sprint_tasks"):
            conn.execute("UPDATE sprint_tasks SET sort_order=? WHERE id=?", (9465000 + internal_id, task_id))
        conn.execute("UPDATE sprint_tasks SET week=? WHERE id=?", (int(week), task_id))
        if "deferred_until" in _columns(conn, "task_metadata"):
            conn.execute("UPDATE task_metadata SET deferred_until=? WHERE task_id=?", (_target_date(conn, week, day_index), task_id))
        _schedule_row(conn, task_id, week, day_index)


def _schedule_targets(conn):
    if "task_metadata" not in _tables(conn):
        return
    for target in TARGETS:
        row = conn.execute("SELECT task_id FROM task_metadata WHERE managed_key=?", (f"datacamp:{target['key']}",)).fetchone()
        if row is not None:
            _schedule_row(conn, int(row[0]), target["week"], target["day_index"])



def _snapshot_rows(conn, table, column, values):
    """Capture exact rows for a small set of current-track identities."""
    if table not in _tables(conn):
        return []
    cols = set(_columns(conn, table))
    if column not in cols or not values:
        return []
    placeholders = ",".join("?" for _ in values)
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE {column} IN ({placeholders})",
        tuple(values),
    ).fetchall()
    return [_row_dict(row) for row in rows]


def _row_identity(conn, table, row):
    """Return stable identity columns for one captured SQLite row."""
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    primary = [str(item[1]) for item in info if int(item[5] or 0) > 0]
    if primary and all(name in row for name in primary):
        return primary
    for candidate in (
        ("task_id",),
        ("chapter_key",),
        ("id",),
        ("focus_date", "task_id"),
        ("promotion_date", "task_id"),
    ):
        if all(name in row and name in _columns(conn, table) for name in candidate):
            return list(candidate)
    return []


def _restore_snapshot_rows(conn, table, rows):
    """Update or insert captured rows without replacing unrelated records."""
    if table not in _tables(conn) or not rows:
        return
    columns = set(_columns(conn, table))
    for raw in rows:
        row = {key: value for key, value in raw.items() if key in columns}
        if not row:
            continue
        identity = _row_identity(conn, table, row)
        exists = None
        if identity:
            where = " AND ".join(f"{name}=?" for name in identity)
            exists = conn.execute(
                f"SELECT 1 FROM {table} WHERE {where} LIMIT 1",
                tuple(row[name] for name in identity),
            ).fetchone()
        if exists is not None:
            update_cols = [name for name in row if name not in identity]
            if update_cols:
                conn.execute(
                    f"UPDATE {table} SET "
                    + ",".join(f"{name}=?" for name in update_cols)
                    + " WHERE "
                    + " AND ".join(f"{name}=?" for name in identity),
                    tuple(row[name] for name in update_cols)
                    + tuple(row[name] for name in identity),
                )
            continue
        use = list(row)
        conn.execute(
            f"INSERT OR REPLACE INTO {table} ({','.join(use)}) "
            f"VALUES ({','.join('?' for _ in use)})",
            tuple(row[name] for name in use),
        )


def _capture_current_target_state(conn):
    """Preserve the exact 20 current chapters across the legacy retire pass."""
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return {}
    managed = tuple(f"datacamp:{key}" for key in TARGET_KEYS)
    placeholders = ",".join("?" for _ in managed)
    rows = conn.execute(
        f"SELECT task_id FROM task_metadata WHERE managed_key IN ({placeholders})",
        managed,
    ).fetchall()
    task_ids = tuple(int(row[0]) for row in rows)
    return {
        "task_ids": task_ids,
        "sprint_tasks": _snapshot_rows(conn, "sprint_tasks", "id", task_ids),
        "task_metadata": _snapshot_rows(conn, "task_metadata", "task_id", task_ids),
        "progress": _snapshot_rows(conn, "datacamp_chapter_progress", "chapter_key", TARGET_KEYS),
        "schedule": _snapshot_rows(conn, "task_sprint_schedule", "task_id", task_ids),
        "focus": _snapshot_rows(conn, "daily_focus", "task_id", task_ids),
        "promotions": _snapshot_rows(conn, "task_day_promotions", "task_id", task_ids),
    }


def _restore_current_target_state(conn, snapshot):
    """Restore target rows by their original IDs, then let realign refresh them."""
    if not snapshot:
        return
    _restore_snapshot_rows(conn, "sprint_tasks", snapshot.get("sprint_tasks", []))
    _restore_snapshot_rows(conn, "task_metadata", snapshot.get("task_metadata", []))
    _restore_snapshot_rows(conn, "datacamp_chapter_progress", snapshot.get("progress", []))
    _restore_snapshot_rows(conn, "task_sprint_schedule", snapshot.get("schedule", []))
    _restore_snapshot_rows(conn, "task_day_promotions", snapshot.get("promotions", []))
    _restore_snapshot_rows(conn, "daily_focus", snapshot.get("focus", []))


def _ensure_all_current_tasks(conn):
    """Materialize all 20 current chapters without relying on Database Design rows."""
    if not {"sprint_tasks", "task_metadata"} <= _tables(conn):
        return
    source_id = None
    for target in TARGETS:
        row = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key=? ORDER BY task_id LIMIT 1",
            (f"datacamp:{target['key']}",),
        ).fetchone()
        if row is not None:
            source_id = int(row[0])
            break
    if source_id is None:
        row = conn.execute(
            "SELECT task_id FROM task_metadata "
            "WHERE managed_key LIKE 'datacamp:%' ORDER BY task_id LIMIT 1"
        ).fetchone()
        source_id = int(row[0]) if row is not None else None
    if source_id is None:
        return

    for target in TARGETS:
        row = conn.execute(
            "SELECT task_id FROM task_metadata WHERE managed_key=? ORDER BY task_id LIMIT 1",
            (f"datacamp:{target['key']}",),
        ).fetchone()
        if row is not None:
            task_id = int(row[0])
            _update_task(conn, task_id, target, preserve_completion=True)
            continue
        task_id = _clone_task(conn, source_id, target)
        source_id = task_id


def _current_target_task_count(conn):
    if "task_metadata" not in _tables(conn):
        return 0
    managed = tuple(f"datacamp:{key}" for key in TARGET_KEYS)
    placeholders = ",".join("?" for _ in managed)
    row = conn.execute(
        f"SELECT COUNT(DISTINCT managed_key) FROM task_metadata "
        f"WHERE managed_key IN ({placeholders})",
        managed,
    ).fetchone()
    return int(row[0]) if row is not None else 0

def realign(conn):
    """Apply the track migration atomically. Caller decides whether failure is fatal."""
    savepoint = "v104625_datacamp_track_alignment"
    conn.execute(f"SAVEPOINT {savepoint}")
    try:
        _ensure_progress(conn)
        _ensure_tasks(conn)
        _move_legacy_learning(conn)
        _schedule_targets(conn)
        _refresh_target_readiness(conn)
        _realign_sql_schedule(conn)
        conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        conn.commit()
    except Exception:
        try:
            conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        except Exception:
            # Preserve the original exception; the wrapper will log it.
            pass
        raise


def install(datacamp_module):
    """Install the current-track scheduler plus complete task-metadata bridges."""
    if getattr(datacamp_module, "_v104630_datacamp_metadata_bridge", False):
        return

    # If this process has not already installed the v10.46.24/25 reconciliation
    # wrapper, install it now. A fresh application process normally reaches this
    # branch exactly once.
    if not getattr(datacamp_module, "_v104624_track_alignment", False):
        original_reconcile = getattr(datacamp_module, "reconcile", None)
        if callable(original_reconcile):
            def wrapped_reconcile(conn, *args, **kwargs):
                # The legacy provider catalog still treats the 20 current-track
                # keys as noncanonical. Snapshot them before that retire pass.
                target_snapshot = _capture_current_target_state(conn)
                result = original_reconcile(conn, *args, **kwargs)
                try:
                    _restore_current_target_state(conn, target_snapshot)
                    realign(conn)
                    if _current_target_task_count(conn) != len(TARGET_KEYS):
                        raise RuntimeError(
                            f"Current DataCamp track restored "
                            f"{_current_target_task_count(conn)}/{len(TARGET_KEYS)} tasks"
                        )
                except Exception as exc:
                    # Preserve startup, but record a precise recovery failure.
                    _log_alignment_error(exc)
                return result
            wrapped_reconcile._v104633_current_track_preservation = True
            datacamp_module.reconcile = wrapped_reconcile

        original_url = getattr(datacamp_module, "chapter_url_for_task", None)
        if callable(original_url):
            def wrapped_url(conn, task_id, *args, **kwargs):
                target = target_for_task(conn, task_id)
                if target is not None:
                    return target["url"]
                return original_url(conn, task_id, *args, **kwargs)
            datacamp_module.chapter_url_for_task = wrapped_url

        datacamp_module._v104624_track_alignment = True

    _install_metadata_bridges()

    # Publish normalized metadata accessors on the provider service so future UI
    # code can use the current-track source directly instead of reintroducing a
    # dependency on the retired static catalog.
    # Current replacement chapters are not members of the retired static
    # datacamp_curriculum catalog. Resolve their readiness from durable task
    # metadata instead of falling back to "metadata is unavailable".
    original_readiness = getattr(datacamp_module, "readiness", None)
    if callable(original_readiness) and not getattr(original_readiness, "_v104633_current_track_readiness", False):
        def wrapped_readiness(conn, task, *args, **kwargs):
            target = target_for_item(conn, task)
            if target is None:
                return original_readiness(conn, task, *args, **kwargs)
            task_id = _item_value(task, "task_id", _item_value(task, "id"))
            if task_id is None:
                row = conn.execute(
                    "SELECT task_id FROM task_metadata WHERE managed_key=?",
                    (f"datacamp:{target['key']}",),
                ).fetchone()
                task_id = int(row[0]) if row is not None else None
            if task_id is None:
                return False, "DataCamp task state is unavailable."
            row = conn.execute(
                "SELECT s.completed,m.prerequisite_state,m.prerequisite_reason "
                "FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id "
                "WHERE s.id=?",
                (int(task_id),),
            ).fetchone()
            if row is None:
                return False, "DataCamp task state is unavailable."
            if bool(row[0]):
                return True, ""
            state = str(row[1] or "Ready").strip().casefold()
            reason = str(row[2] or "").strip()
            if state in {"ready", "open", "available"}:
                return True, ""
            return False, reason or "Complete the prerequisite first."
        wrapped_readiness._v104633_current_track_readiness = True
        datacamp_module.readiness = wrapped_readiness

    original_current_ready = getattr(datacamp_module, "current_ready_task", None)
    if callable(original_current_ready) and not getattr(original_current_ready, "_v104633_current_track_ready_task", False):
        def wrapped_current_ready_task(conn, *args, **kwargs):
            managed = tuple(f"datacamp:{key}" for key in TARGET_KEYS)
            placeholders = ",".join("?" for _ in managed)
            row = conn.execute(
                f"SELECT s.id,s.week,s.sort_order,s.label,s.completed,m.* "
                f"FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id "
                f"WHERE m.managed_key IN ({placeholders}) "
                "AND s.completed=0 "
                "AND COALESCE(m.prerequisite_state,'Ready')='Ready' "
                "AND (m.deferred_until IS NULL OR m.deferred_until<=?) "
                "ORDER BY s.week,s.sort_order,s.id LIMIT 1",
                managed + (date.today().isoformat(),),
            ).fetchone()
            if row is not None:
                return row
            return original_current_ready(conn, *args, **kwargs)
        wrapped_current_ready_task._v104633_current_track_ready_task = True
        datacamp_module.current_ready_task = wrapped_current_ready_task

    # v10.46.35: v10.46.33 taught the provider how to display, schedule,
    # and reconcile the replacement chapters, but the provider's completion
    # functions still resolve only the retired static chapter catalog. Persist
    # completion evidence for current-track keys directly so tracks.sync_all()
    # cannot mistake a legitimate checkbox completion for a detached false
    # completion.
    original_mark_complete = getattr(datacamp_module, "mark_task_complete", None)
    if callable(original_mark_complete) and not getattr(
        original_mark_complete,
        "_v104635_current_track_completion",
        False,
    ):
        def wrapped_mark_task_complete(conn, task_id, *args, **kwargs):
            target = target_for_task(conn, int(task_id))
            if target is None:
                return original_mark_complete(conn, task_id, *args, **kwargs)

            _ensure_progress(conn)
            progress_cols = set(_columns(conn, "datacamp_chapter_progress"))
            task_cols = set(_columns(conn, "task_metadata"))

            assignments = {"status": "Completed"}
            if "task_id" in progress_cols:
                assignments["task_id"] = int(task_id)
            if "completed_date" in progress_cols:
                assignments["completed_date"] = date.today().isoformat()
            if "completed_at" in progress_cols:
                assignments["completed_at"] = datetime.now().isoformat(timespec="seconds")
            if "updated_at" in progress_cols:
                assignments["updated_at"] = datetime.now().isoformat(timespec="seconds")

            conn.execute(
                "UPDATE datacamp_chapter_progress SET "
                + ",".join(f"{name}=?" for name in assignments)
                + " WHERE chapter_key=?",
                tuple(assignments.values()) + (target["key"],),
            )
            conn.execute(
                "UPDATE sprint_tasks SET completed=1 WHERE id=?",
                (int(task_id),),
            )

            metadata = {"status": "Completed"}
            if "deferred_until" in task_cols:
                metadata["deferred_until"] = None
            if "prerequisite_state" in task_cols:
                metadata["prerequisite_state"] = "Ready"
            if "prerequisite_reason" in task_cols:
                metadata["prerequisite_reason"] = None

            conn.execute(
                "UPDATE task_metadata SET "
                + ",".join(f"{name}=?" for name in metadata)
                + " WHERE task_id=?",
                tuple(metadata.values()) + (int(task_id),),
            )

            _refresh_target_readiness(conn)
            conn.commit()
            return None

        wrapped_mark_task_complete._v104635_current_track_completion = True
        datacamp_module.mark_task_complete = wrapped_mark_task_complete

    original_mark_incomplete = getattr(datacamp_module, "mark_task_incomplete", None)
    if callable(original_mark_incomplete) and not getattr(
        original_mark_incomplete,
        "_v104635_current_track_completion",
        False,
    ):
        def wrapped_mark_task_incomplete(
            conn,
            task_id,
            *args,
            enforce_sequence=False,
            **kwargs,
        ):
            target = target_for_task(conn, int(task_id))
            if target is None:
                return original_mark_incomplete(
                    conn,
                    task_id,
                    *args,
                    enforce_sequence=enforce_sequence,
                    **kwargs,
                )

            if enforce_sequence:
                index = TARGET_KEYS.index(target["key"])
                later_keys = TARGET_KEYS[index + 1:]
                if later_keys:
                    placeholders = ",".join("?" for _ in later_keys)
                    later = conn.execute(
                        f"SELECT chapter_key FROM datacamp_chapter_progress "
                        f"WHERE chapter_key IN ({placeholders}) "
                        "AND status='Completed' LIMIT 1",
                        tuple(later_keys),
                    ).fetchone()
                    if later is not None:
                        raise ValueError(
                            "Undo later DataCamp chapter completions first so "
                            "the current-track sequence remains valid."
                        )

            progress_cols = set(_columns(conn, "datacamp_chapter_progress"))
            task_cols = set(_columns(conn, "task_metadata"))

            progress = {"status": "Not Started"}
            if "completed_date" in progress_cols:
                progress["completed_date"] = None
            if "completed_at" in progress_cols:
                progress["completed_at"] = None
            if "updated_at" in progress_cols:
                progress["updated_at"] = datetime.now().isoformat(timespec="seconds")

            conn.execute(
                "UPDATE datacamp_chapter_progress SET "
                + ",".join(f"{name}=?" for name in progress)
                + " WHERE chapter_key=?",
                tuple(progress.values()) + (target["key"],),
            )
            conn.execute(
                "UPDATE sprint_tasks SET completed=0 WHERE id=?",
                (int(task_id),),
            )

            metadata = {"status": "Not Started"}
            if "deferred_until" in task_cols:
                metadata["deferred_until"] = _target_date(
                    conn,
                    int(target["week"]),
                    int(target["day_index"]),
                )
            conn.execute(
                "UPDATE task_metadata SET "
                + ",".join(f"{name}=?" for name in metadata)
                + " WHERE task_id=?",
                tuple(metadata.values()) + (int(task_id),),
            )

            _refresh_target_readiness(conn)
            conn.commit()
            return None

        wrapped_mark_task_incomplete._v104635_current_track_completion = True
        datacamp_module.mark_task_incomplete = wrapped_mark_task_incomplete

    datacamp_module.current_track_metadata_for_task = metadata_for_task
    datacamp_module.current_track_target_for_task = target_for_task
    datacamp_module._v104635_current_track_completion = True
    datacamp_module._v104633_canonical_reconcile_fix = True
    datacamp_module._v104630_datacamp_metadata_bridge = True
