"""v10.46.24 current DataCamp-track compatibility layer.

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
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

PATCH_MARKER = "v10.46.25-datacamp-track-realignment"


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
    aliases = {
        "chapter_key": target["key"], "course_name": target["course"],
        "course": target["course"], "chapter_number": target["chapter"],
        "chapter": target["chapter"], "chapter_name": target["name"],
        "title": target["name"], "week": target["week"],
        "scheduled_week": target["week"], "url": target["url"],
        "course_url": target["url"], "chapter_url": target["url"],
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

    # Preserve old Power BI/Python chapter identities/completion while moving their
    # scheduled week after the newly restored SQL-track continuation.
    for prefix, target_week in (("w07_", 8), ("w08_", 9)):
        assignments = []
        values = []
        for col in ("week", "scheduled_week"):
            if col in cols:
                assignments.append(f"{col}=?")
                values.append(target_week)
        if assignments:
            placeholders = ",".join("?" for _ in TARGET_KEYS)
            conn.execute(
                f"UPDATE {table} SET {','.join(assignments)} WHERE chapter_key LIKE ? "
                f"AND chapter_key NOT IN ({placeholders})",
                tuple(values) + (prefix + "%",) + TARGET_KEYS,
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
    assignments = {"managed_key": f"datacamp:{target['key']}"}
    if "status" in cols and not preserve_completion:
        assignments["status"] = "Not Started"
    if "estimated_minutes" in cols: assignments["estimated_minutes"] = int(target["minutes"])
    if "category" in cols: assignments["category"] = "Learning"
    if "priority" in cols: assignments["priority"] = 1
    if "description" in cols: assignments["description"] = f"Complete {target['course']}, Chapter {target['chapter']}: {target['name']}."
    if "definition_of_done" in cols: assignments["definition_of_done"] = "Mark the matching DataCamp chapter complete after finishing it."
    if "deferred_until" in cols: assignments["deferred_until"] = _target_date(conn, target["week"], target["day_index"])
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
    target_managed = {f"datacamp:{key}" for key in TARGET_KEYS}
    for prefix, target_week in (("datacamp:w08_", 9), ("datacamp:w07_", 8)):
        rows = conn.execute(
            """SELECT m.task_id,m.managed_key
               FROM task_metadata m
               WHERE m.managed_key LIKE ?
               ORDER BY m.task_id""",
            (prefix + "%",),
        ).fetchall()
        legacy = [(int(r[0]), str(r[1])) for r in rows if str(r[1]) not in target_managed]
        if not legacy:
            continue
        for idx, (task_id, _managed) in enumerate(legacy):
            # Assign a reserved sort band before moving weeks so a repository with
            # UNIQUE(week, sort_order) cannot collide during the move.
            if "sort_order" in _columns(conn, "sprint_tasks"):
                conn.execute("UPDATE sprint_tasks SET sort_order=? WHERE id=?", (9463000 + target_week * 1000 + idx, task_id))
            conn.execute("UPDATE sprint_tasks SET week=? WHERE id=?", (target_week, task_id))
            if "deferred_until" in _columns(conn, "task_metadata"):
                day_index = idx % 5
                conn.execute("UPDATE task_metadata SET deferred_until=? WHERE task_id=?", (_target_date(conn, target_week, day_index), task_id))
            _schedule_row(conn, task_id, target_week, idx % 5)


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
    """Install an idempotent post-reconcile adapter on the existing module."""
    if getattr(datacamp_module, "_v104624_track_alignment", False):
        return
    original_reconcile = getattr(datacamp_module, "reconcile", None)
    if callable(original_reconcile):
        def wrapped_reconcile(conn, *args, **kwargs):
            result = original_reconcile(conn, *args, **kwargs)
            try:
                realign(conn)
            except Exception as exc:
                # Curriculum repair is supplementary. A local schema/data edge case
                # must not terminate the entire Career Accelerator application.
                _log_alignment_error(exc)
            return result
        datacamp_module.reconcile = wrapped_reconcile

    original_url = getattr(datacamp_module, "chapter_url_for_task", None)
    if callable(original_url):
        def wrapped_url(conn, task_id, *args, **kwargs):
            try:
                row = conn.execute("SELECT managed_key FROM task_metadata WHERE task_id=?", (int(task_id),)).fetchone()
                managed = str(row[0] or "") if row is not None else ""
                if managed.startswith("datacamp:"):
                    target = TARGET_BY_KEY.get(managed.split(":", 1)[1])
                    if target:
                        return target["url"]
            except Exception:
                pass
            return original_url(conn, task_id, *args, **kwargs)
        datacamp_module.chapter_url_for_task = wrapped_url
    datacamp_module._v104624_track_alignment = True
