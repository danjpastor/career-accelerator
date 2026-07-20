from __future__ import annotations
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "career_accelerator.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS program_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_week INTEGER NOT NULL DEFAULT 1,
    total_weeks INTEGER NOT NULL DEFAULT 12,
    start_date TEXT NOT NULL,
    google_course INTEGER NOT NULL DEFAULT 1,
    google_total_courses INTEGER NOT NULL DEFAULT 9,
    google_module INTEGER NOT NULL DEFAULT 1,
    current_project INTEGER NOT NULL DEFAULT 1,
    total_projects INTEGER NOT NULL DEFAULT 3,
    weekly_target_hours REAL NOT NULL DEFAULT 18,
    sql_target INTEGER NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS sprint_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL,
    sort_order INTEGER NOT NULL,
    label TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(week, sort_order)
);

CREATE TABLE IF NOT EXISTS task_metadata (
    task_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'Not Started',
    priority INTEGER NOT NULL DEFAULT 2,
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    energy TEXT NOT NULL DEFAULT 'Normal',
    deferred_until TEXT,
    destination INTEGER NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT 'General',
    prerequisite_state TEXT NOT NULL DEFAULT 'Ready',
    prerequisite_reason TEXT,
    FOREIGN KEY(task_id) REFERENCES sprint_tasks(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS task_workspaces (
    workspace_key TEXT PRIMARY KEY,
    task_id INTEGER,
    task_label TEXT NOT NULL,
    track_key TEXT,
    target_key TEXT,
    workspace_type TEXT NOT NULL DEFAULT 'task_notes',
    document_path TEXT,
    content TEXT NOT NULL DEFAULT '',
    scheduled_for TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_workspace_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_key TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    label TEXT,
    is_managed INTEGER NOT NULL DEFAULT 0,
    source_key TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_key, artifact_path),
    FOREIGN KEY(workspace_key)
        REFERENCES task_workspaces(workspace_key)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_focus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    focus_date TEXT NOT NULL,
    week INTEGER NOT NULL,
    position INTEGER NOT NULL,
    task_id INTEGER,
    source_key TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    track_key TEXT,
    target_key TEXT,
    is_extra INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(focus_date, position),
    FOREIGN KEY(task_id) REFERENCES sprint_tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS project_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    sort_order INTEGER NOT NULL,
    stage TEXT NOT NULL DEFAULT 'Overview',
    label TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(project_id, sort_order)
);

CREATE TABLE IF NOT EXISTS project_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    section TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    UNIQUE(project_id, section)
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date TEXT NOT NULL,
    hours REAL NOT NULL,
    google_progress TEXT,
    datacamp_progress TEXT,
    sql_problems INTEGER NOT NULL DEFAULT 0,
    portfolio_progress TEXT,
    notes TEXT,
    productivity_score INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sql_practice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL DEFAULT 'DataLemur',
    title TEXT NOT NULL,
    difficulty TEXT,
    topic TEXT,
    concepts TEXT,
    status TEXT NOT NULL DEFAULT 'Completed',
    mastery INTEGER NOT NULL DEFAULT 1,
    review_date TEXT,
    completed_date TEXT,
    solution_path TEXT,
    notes TEXT,
    UNIQUE(platform, title)
);

CREATE TABLE IF NOT EXISTS applied_exercise_progress (
    exercise_number INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'Not Started',
    submission_path TEXT,
    notes TEXT,
    completed_date TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS duckdb_exercise_progress (
    exercise_number INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'Not Started',
    submission_path TEXT,
    notes TEXT,
    completed_date TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exercise_pack_progress (
    pack_id TEXT NOT NULL,
    exercise_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Not Started',
    answer_sql TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    updated_at TEXT,
    completed_at TEXT,
    PRIMARY KEY (pack_id, exercise_id)
);

CREATE TABLE IF NOT EXISTS task_concept_tags (
    task_id INTEGER NOT NULL,
    concept TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence INTEGER NOT NULL DEFAULT 100,
    updated_at TEXT,
    PRIMARY KEY (task_id, concept)
);

CREATE TABLE IF NOT EXISTS retrospective_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL,
    section TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week INTEGER NOT NULL UNIQUE,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hours REAL NOT NULL DEFAULT 0,
    tasks_completed INTEGER NOT NULL DEFAULT 0,
    tasks_total INTEGER NOT NULL DEFAULT 0,
    sql_completed INTEGER NOT NULL DEFAULT 0,
    summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applied_date TEXT NOT NULL,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    location TEXT,
    source TEXT,
    status TEXT NOT NULL DEFAULT 'Wishlist',
    follow_up_date TEXT,
    resume_version TEXT,
    contact TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    description TEXT,
    UNIQUE(skill, source_type, source_name)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS track_state (
    track_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    subposition INTEGER NOT NULL DEFAULT 0,
    weekly_target INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Active',
    metadata TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS track_tasks (
    track_key TEXT PRIMARY KEY,
    task_id INTEGER NOT NULL UNIQUE,
    target_key TEXT NOT NULL,
    source_label TEXT NOT NULL,
    linked_entity_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id)
        REFERENCES sprint_tasks(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS track_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_key TEXT NOT NULL,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL DEFAULT 'Completed',
    item_label TEXT NOT NULL,
    completed_date TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS skill_state (
    skill_key TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Locked',
    source_track TEXT,
    evidence TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _ensure_columns(conn)
    conn.commit()
    return conn

def _ensure_columns(conn):
    additions = {
        "task_metadata": [
            ("category", "TEXT NOT NULL DEFAULT 'General'"),
            (
                "prerequisite_state",
                "TEXT NOT NULL DEFAULT 'Ready'",
            ),
            ("prerequisite_reason", "TEXT"),
        ],
        "project_tasks": [
            ("stage", "TEXT NOT NULL DEFAULT 'Overview'"),
        ],
        "study_sessions": [
            ("notes", "TEXT"),
            ("productivity_score", "INTEGER"),
            ("task_id", "INTEGER"),
            ("workspace_key", "TEXT"),
            ("task_label_snapshot", "TEXT"),
        ],
        "task_workspace_artifacts": [
            ("is_managed", "INTEGER NOT NULL DEFAULT 0"),
            ("source_key", "TEXT"),
        ],
        "daily_focus": [
            ("track_key", "TEXT"),
            ("target_key", "TEXT"),
            ("is_extra", "INTEGER NOT NULL DEFAULT 0"),
            ("completed_at", "TEXT"),
        ],
        "task_workspaces": [
            ("task_id", "INTEGER"),
            ("task_label", "TEXT NOT NULL DEFAULT ''"),
            ("track_key", "TEXT"),
            ("target_key", "TEXT"),
            ("workspace_type", "TEXT NOT NULL DEFAULT 'task_notes'"),
            ("document_path", "TEXT"),
            ("content", "TEXT NOT NULL DEFAULT ''"),
            ("scheduled_for", "TEXT"),
            ("created_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"),
            ("last_opened_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ],
        "sql_practice": [
            ("topic", "TEXT"),
            ("status", "TEXT NOT NULL DEFAULT 'Completed'"),
            ("mastery", "INTEGER NOT NULL DEFAULT 1"),
            ("review_date", "TEXT"),
        ],
        "applications": [
            ("resume_version", "TEXT"),
            ("contact", "TEXT"),
        ],
    }
    for table, columns in additions.items():
        existing = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, definition in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def ensure_default_state(conn, start_date):
    if not conn.execute("SELECT 1 FROM program_state WHERE id=1").fetchone():
        conn.execute(
            """INSERT INTO program_state
               (id,start_date,current_week,total_weeks,google_course,
                google_total_courses,google_module,current_project,total_projects,
                weekly_target_hours,sql_target)
               VALUES (1,?,1,12,1,9,1,1,3,18,100)""",
            (start_date,),
        )
        conn.commit()

def state(conn):
    return conn.execute("SELECT * FROM program_state WHERE id=1").fetchone()

def update_state(conn, **fields):
    allowed = {
        "current_week", "google_course", "google_module",
        "current_project", "weekly_target_hours",
    }
    items = [(key, value) for key, value in fields.items() if key in allowed]
    if not items:
        return
    clause = ", ".join(f"{key}=?" for key, _ in items)
    conn.execute(
        f"UPDATE program_state SET {clause} WHERE id=1",
        [value for _, value in items],
    )
    conn.commit()

def setting(conn, key, default=None):
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def save_setting(conn, key, value):
    conn.execute(
        """INSERT INTO settings(key,value) VALUES(?,?)
           ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
        (key, str(value)),
    )
    conn.commit()

def factory_reset(conn, start_date):
    """Clear all user progress and rebuild a clean Course 1 state.

    Application preferences in the settings table and backup files on disk
    are intentionally preserved.
    """
    progress_tables = [
        "daily_focus",
        "task_workspace_artifacts",
        "task_workspaces",
        "achievements",
        "weekly_summaries",
        "retrospective_notes",
        "study_sessions",
        "sql_practice",
        "task_concept_tags",
        "exercise_pack_progress",
        "applications",
        "evidence",
        "project_notes",
        "task_metadata",
        "sprint_tasks",
        "project_tasks",
        "program_state",
        "track_tasks",
        "track_events",
        "track_state",
        "skill_state",
        "academy_skill_evidence",
        "academy_submissions",
        "academy_assessment_attempts",
        "academy_activity_progress",
        "academy_lesson_progress",
        "academy_enrollments",
        "academy_packages",
        "external_learning_history",
    ]

    with conn:
        for table in progress_tables:
            conn.execute(f"DELETE FROM {table}")

        conn.execute(
            """INSERT INTO program_state
               (id,start_date,current_week,total_weeks,google_course,
                google_total_courses,google_module,current_project,total_projects,
                weekly_target_hours,sql_target)
               VALUES (1,?,1,12,1,9,1,1,3,18,100)""",
            (start_date,),
        )

        sequence_tables = [
            table
            for table in progress_tables
            if table not in {
                "program_state",
                "task_metadata",
            }
        ]
        placeholders = ",".join("?" for _ in sequence_tables)
        conn.execute(
            f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})",
            sequence_tables,
        )
        conn.execute(
            """DELETE FROM settings
               WHERE key='current_google_task_id'
                  OR key LIKE 'track_%'"""
        )

