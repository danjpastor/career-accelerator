from __future__ import annotations

import sqlite3


ACADEMY_SCHEMA = """
CREATE TABLE IF NOT EXISTS academy_packages (
    package_id TEXT PRIMARY KEY,
    program_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    content_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    root_path TEXT NOT NULL,
    installed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS academy_enrollments (
    program_id TEXT NOT NULL,
    path_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    PRIMARY KEY (program_id, path_id)
);

CREATE TABLE IF NOT EXISTS academy_lesson_progress (
    program_id TEXT NOT NULL,
    path_id TEXT NOT NULL,
    track_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    lesson_id TEXT PRIMARY KEY,
    content_version TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'Not Started'
        CHECK(state IN ('Not Started','Learning','Practiced','Mastered')),
    started_at TEXT,
    practiced_at TEXT,
    mastered_at TEXT,
    last_opened_at TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    solution_viewed INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS academy_activity_progress (
    lesson_id TEXT NOT NULL,
    activity_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'Not Started',
    answer_text TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    hint_level INTEGER NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_validation_json TEXT NOT NULL DEFAULT '{}',
    passed_at TEXT,
    solution_viewed_at TEXT,
    last_attempt_solution_assisted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lesson_id, activity_id)
);

CREATE TABLE IF NOT EXISTS academy_assessment_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    solution_assisted INTEGER NOT NULL DEFAULT 0,
    answers_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    UNIQUE(assessment_id, attempt_number)
);

CREATE TABLE IF NOT EXISTS academy_skill_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id TEXT NOT NULL,
    path_id TEXT NOT NULL,
    course_id TEXT,
    learning_item_id TEXT NOT NULL,
    skill_key TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    difficulty TEXT,
    dataset TEXT,
    submission_path TEXT,
    evidence_level TEXT NOT NULL DEFAULT 'demonstrated',
    validation_status TEXT NOT NULL DEFAULT 'passed',
    job_competency TEXT,
    reviewer_status TEXT NOT NULL DEFAULT 'Unreviewed',
    evidence_notes TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    demonstrated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(skill_key, source_type, source_id)
);

CREATE TABLE IF NOT EXISTS academy_submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    title TEXT NOT NULL,
    answer_text TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    artifact_path TEXT,
    validation_status TEXT NOT NULL DEFAULT 'Not Submitted',
    validation_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_type, item_id)
);

CREATE TABLE IF NOT EXISTS external_learning_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    external_item_id TEXT,
    external_item_name TEXT NOT NULL,
    completion_status TEXT NOT NULL DEFAULT 'Recorded',
    completion_date TEXT,
    mapped_skills TEXT NOT NULL DEFAULT '[]',
    mapping_confidence REAL,
    diagnostic_status TEXT NOT NULL DEFAULT 'Not Assessed',
    metadata TEXT NOT NULL DEFAULT '{}',
    UNIQUE(provider, external_item_name)
);

CREATE INDEX IF NOT EXISTS idx_academy_lesson_state
    ON academy_lesson_progress(state);
CREATE INDEX IF NOT EXISTS idx_academy_activity_lesson
    ON academy_activity_progress(lesson_id, state);
CREATE INDEX IF NOT EXISTS idx_academy_skill_key
    ON academy_skill_evidence(skill_key, validation_status);
"""


def _ensure_columns(conn: sqlite3.Connection) -> None:
    additions = {
        "academy_activity_progress": [
            ("last_attempt_solution_assisted", "INTEGER NOT NULL DEFAULT 0"),
        ],
    }
    for table, columns in additions.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, definition in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def ensure_academy_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(ACADEMY_SCHEMA)
    _ensure_columns(conn)
    conn.commit()
