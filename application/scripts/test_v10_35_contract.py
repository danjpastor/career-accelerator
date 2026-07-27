from __future__ import annotations

"""Database-level regression checks for v10.35 planner and weekly gates."""

from datetime import date
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "application"))

from career_app import database  # noqa: E402
from career_app.services import (  # noqa: E402
    roadmap_mastery,
    task_workspace,
    unified_tasks,
    weekly_mastery,
)


def fresh_connection() -> tuple[sqlite3.Connection, Path]:
    folder = Path(tempfile.mkdtemp(prefix="dca-10350-"))
    path = folder / "test.db"
    database.DB_PATH = path
    conn = database.connect()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS academy_assessment_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            score REAL NOT NULL DEFAULT 0,
            passed INTEGER NOT NULL DEFAULT 0,
            solution_assisted INTEGER NOT NULL DEFAULT 0,
            answers_json TEXT NOT NULL DEFAULT '{}',
            result_json TEXT NOT NULL DEFAULT '{}',
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS roadmap_requirement_state (
            requirement_key TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            due_week INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Future',
            reason TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS academy_lesson_progress (
            lesson_id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'Not Started'
        );
        """
    )
    conn.execute("DELETE FROM sprint_tasks")
    conn.execute("DELETE FROM task_metadata")
    conn.execute("DELETE FROM track_tasks")
    conn.execute("DELETE FROM daily_focus")
    conn.execute("DELETE FROM settings")
    conn.execute("DELETE FROM academy_assessment_attempts")
    conn.commit()
    return conn, path


def add_task(conn: sqlite3.Connection, week: int, order: int, label: str) -> int:
    cursor = conn.execute(
        "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
        (week, order, label),
    )
    task_id = int(cursor.lastrowid)
    conn.execute(
        """INSERT INTO task_metadata
           (task_id,status,priority,estimated_minutes,energy,destination,category,
            prerequisite_state,description,definition_of_done)
           VALUES(?, 'Not Started', 2, 20, 'Normal', 0, 'General', 'Ready', '', '')""",
        (task_id,),
    )
    return task_id


def assert_daily_cap_and_rolling_catchup() -> None:
    conn, _path = fresh_connection()
    try:
        conn.execute(
            """INSERT INTO academy_assessment_attempts
               (assessment_id,attempt_number,score,passed,solution_assisted,completed_at)
               VALUES('week_1_spreadsheet_foundations_check',1,0.875,1,0,CURRENT_TIMESTAMP)"""
        )
        catchup_ids = [add_task(conn, 1, i, f"Catch-Up Task {i}") for i in range(1, 3)]
        current_ids = [add_task(conn, 2, i, f"Current Task {i}") for i in range(1, 8)]
        conn.commit()

        first = unified_tasks.daily_plan(conn, 2)
        assert [int(item["id"]) for item in first] == current_ids[:5], first
        assert all(not item.get("is_catch_up") for item in first)

        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (current_ids[0],))
        conn.commit()
        second = unified_tasks.daily_plan(conn, 2)
        assert [int(item["id"]) for item in second[:4]] == current_ids[1:5], second
        assert int(second[-1]["id"]) == catchup_ids[0], second
        assert second[-1].get("is_catch_up") is True
        assert unified_tasks.focus_context(second[-1], 2).startswith("Catch-Up •")

        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (catchup_ids[0],))
        conn.commit()
        third = unified_tasks.daily_plan(conn, 2)
        assert int(third[-1]["id"]) == catchup_ids[1], third

        conn.executemany(
            "UPDATE sprint_tasks SET completed=1 WHERE id=?",
            [(task_id,) for task_id in current_ids[:5] + catchup_ids],
        )
        conn.commit()
        final = unified_tasks.daily_plan(conn, 2)
        assert final == [], final
        # The two unassigned current-week tasks remain future queue items and
        # never replace the five frozen new assignments in Today's Focus.
        queued = unified_tasks.next_tasks(conn, 2, limit=10)
        assert [int(item["id"]) for item in queued[:2]] == current_ids[5:7], queued

        snapshot = conn.execute(
            "SELECT value FROM settings WHERE key=?",
            (f"daily_focus_snapshot_v2:{date.today().isoformat()}",),
        ).fetchone()
        assert snapshot is not None
    finally:
        conn.close()


def assert_knowledge_check_gate() -> None:
    conn, _path = fresh_connection()
    try:
        blocker = add_task(conn, 1, 1, "Required Week 1 Task")
        conn.commit()
        gate = weekly_mastery.knowledge_check_readiness(
            conn, "week_1_spreadsheet_foundations_check"
        )
        assert not gate.ready and "Required Week 1 Task" in " ".join(gate.missing), gate

        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (blocker,))
        conn.commit()
        gate = weekly_mastery.knowledge_check_readiness(
            conn, "week_1_spreadsheet_foundations_check"
        )
        assert gate.ready, gate

        next_gate = weekly_mastery.previous_week_gate(conn, 2)
        assert not next_gate.ready
        conn.execute(
            """INSERT INTO academy_assessment_attempts
               (assessment_id,attempt_number,score,passed,solution_assisted,completed_at)
               VALUES('week_1_spreadsheet_foundations_check',1,0.875,1,0,CURRENT_TIMESTAMP)"""
        )
        conn.commit()
        assert weekly_mastery.previous_week_gate(conn, 2).ready
    finally:
        conn.close()


def assert_overdue_academy_coursework_surfaces_before_check() -> None:
    """Reproduce the Week 1/Week 2 circular gate fixed in v10.35.3."""
    conn, _path = fresh_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO program_state
               (id,current_week,total_weeks,start_date,google_course,google_total_courses,
                google_module,current_project,total_projects,weekly_target_hours,sql_target)
               VALUES(1,2,12,'2026-07-13',7,9,1,1,3,18,100)"""
        )

        academy_task = add_task(
            conn, 1, -300000,
            "Understand Spreadsheet Structure — Learn — Understand Spreadsheet Structure",
        )
        conn.execute(
            "UPDATE task_metadata SET category='Learning' WHERE task_id=?",
            (academy_task,),
        )
        conn.execute(
            """INSERT INTO track_tasks(track_key,task_id,target_key,source_label)
               VALUES('academy',?,'academy:activity:academy2_spreadsheet_structure:learn',
                      'Accelerator Academy')""",
            (academy_task,),
        )

        # A stale static lesson row and a post-check retrospective must not be
        # invisible blockers for the weekly quiz.
        stale = add_task(conn, 2, 10, "Retired Static Academy Lesson")
        conn.execute(
            "UPDATE task_metadata SET managed_key=? WHERE task_id=?",
            ("roadmap_v1026:lesson:retired_static", stale),
        )
        retrospective = add_task(conn, 1, 12, "Complete the Week 1 Retrospective")
        conn.execute(
            """UPDATE task_metadata SET category='Review',managed_key='weekly_retrospective_01'
               WHERE task_id=?""",
            (retrospective,),
        )

        check = add_task(conn, 2, -759996, "Week 1 Knowledge Check")
        conn.execute(
            """UPDATE task_metadata
               SET managed_key='roadmap_v1026:assessment:week_1_spreadsheet_foundations_check',
                   starter_path='academy:assessment:week_1_spreadsheet_foundations_check'
               WHERE task_id=?""",
            (check,),
        )
        conn.execute(
            """INSERT OR REPLACE INTO roadmap_requirement_state
               (requirement_key,kind,title,due_week,source_id,status,reason)
               VALUES('assessment:week_1_spreadsheet_foundations_check','assessment',
                      'Week 1 Knowledge Check',1,'week_1_spreadsheet_foundations_check',
                      'Locked','Complete coursework')"""
        )
        conn.commit()

        focus = unified_tasks.daily_plan(conn, 2)
        assert any(int(item["id"]) == academy_task for item in focus), focus
        surfaced = next(item for item in focus if int(item["id"]) == academy_task)
        assert surfaced.get("is_catch_up") is True, surfaced
        assert surfaced.get("ready") is True, surfaced

        for lesson_id in roadmap_mastery.LESSON_ORDER[:4]:
            conn.execute(
                "INSERT OR REPLACE INTO academy_lesson_progress(lesson_id,state) VALUES(?, 'Mastered')",
                (lesson_id,),
            )
        conn.execute("DELETE FROM daily_focus WHERE task_id=?", (academy_task,))
        conn.execute("DELETE FROM track_tasks WHERE task_id=?", (academy_task,))
        conn.execute("DELETE FROM task_metadata WHERE task_id=?", (academy_task,))
        conn.execute("DELETE FROM sprint_tasks WHERE id=?", (academy_task,))
        conn.commit()

        gate = weekly_mastery.knowledge_check_readiness(
            conn, "week_1_spreadsheet_foundations_check"
        )
        assert gate.ready, gate
        checks = [
            item for item in unified_tasks.daily_plan(conn, 2)
            if int(item.get("id") or 0) == check
        ]
        assert checks and checks[0].get("ready") is True, checks
        assert checks[0].get("is_catch_up") is True, checks[0]
    finally:
        conn.close()



def assert_visible_knowledge_check_task() -> None:
    conn, _path = fresh_connection()
    try:
        roadmap_mastery.ensure_schema(conn)
        # A retired static lesson row should be removed, but the weekly check
        # row must survive cleanup so the learner can see the gate.
        lesson_id = add_task(conn, 2, 10, "Retired Academy Lesson")
        check_id = add_task(conn, 3, 11, "Week 2 Knowledge Check")
        conn.execute(
            "UPDATE task_metadata SET managed_key=? WHERE task_id=?",
            ("roadmap_v1026:lesson:retired_lesson", lesson_id),
        )
        conn.execute(
            """UPDATE task_metadata
               SET managed_key=?,starter_path=?,prerequisite_state='Blocked',
                   prerequisite_reason=?
               WHERE task_id=?""",
            (
                "roadmap_v1026:assessment:week_2_spreadsheet_mastery",
                "academy:assessment:week_2_spreadsheet_mastery",
                "Complete All Week 2 Coursework to Unlock",
                check_id,
            ),
        )
        conn.execute(
            """INSERT OR REPLACE INTO roadmap_requirement_state
               (requirement_key,kind,title,due_week,source_id,status,reason)
               VALUES('assessment:week_2_spreadsheet_mastery','assessment',
                      'Week 2 Knowledge Check',2,'week_2_spreadsheet_mastery',
                      'Locked','Complete coursework')"""
        )
        conn.commit()

        retired = roadmap_mastery._retire_legacy_academy_planner_tasks(conn)
        assert retired == 1, retired
        assert conn.execute(
            "SELECT 1 FROM sprint_tasks WHERE id=?", (lesson_id,)
        ).fetchone() is None
        assert conn.execute(
            "SELECT 1 FROM sprint_tasks WHERE id=?", (check_id,)
        ).fetchone() is not None

        checks = [
            item for item in unified_tasks.all_tasks(conn, 3)
            if item.get("kind") == "knowledge_check"
        ]
        check = next(item for item in checks if item["label"] == "Week 2 Knowledge Check")
        assert check["week"] == 2
        assert check["prerequisite_reason"] == "Complete All Week 2 Coursework to Unlock"
        assert check["starter_path"] == "academy:assessment:week_2_spreadsheet_mastery"
    finally:
        conn.close()


def assert_weekly_retrospective_save() -> None:
    conn, path = fresh_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO program_state
               (id,current_week,total_weeks,start_date,google_course,google_total_courses,
                google_module,current_project,total_projects,weekly_target_hours,sql_target)
               VALUES(1,2,12,'2026-07-13',5,9,1,1,3,18,100)"""
        )
        task_id = add_task(conn, 2, 21, "Week 2 Retrospective")
        conn.execute(
            """UPDATE task_metadata SET category='Review',starter_path=?,managed_key=?
               WHERE task_id=?""",
            ("weeks/week-02/README.md", "retrospective:2", task_id),
        )
        conn.execute(
            """INSERT INTO task_workspaces
               (workspace_key,task_id,task_label,workspace_type,document_path,content)
               VALUES('retro-week-2',?,'Week 2 Retrospective','retrospective',
                      'weeks/week-02/RETROSPECTIVE.md','')""",
            (task_id,),
        )
        conn.commit()
        values = {
            "biggest_win": "Completed the spreadsheet coursework.",
            "blocker": "None",
            "learning": "I learned how fixed references behave.",
        }
        record = task_workspace.save_retrospective(
            conn, path.parent, "retro-week-2", task_id, values
        )
        assert not task_workspace.retrospective_completion_issues(conn, task_id)
        assert "Learning Progress This Week" in record["content"]
        assert "Evidence Created This Week" in record["content"]
    finally:
        conn.close()


def main() -> int:
    assert_daily_cap_and_rolling_catchup()
    assert_knowledge_check_gate()
    assert_overdue_academy_coursework_surfaces_before_check()
    assert_visible_knowledge_check_task()
    assert_weekly_retrospective_save()
    print("v10.35.3 planner, Academy catch-up, knowledge-check, and retrospective contract: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
