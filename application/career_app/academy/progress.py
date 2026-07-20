from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from .models import ActivityDefinition, LessonDefinition, ProgressState
from .schema import ensure_academy_schema


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class ProgressRepository:
    def __init__(self, conn: sqlite3.Connection, content_version: str):
        self.conn = conn
        self.content_version = content_version
        ensure_academy_schema(conn)

    def seed_lesson(
        self,
        *,
        program_id: str,
        path_id: str,
        track_id: str,
        course_id: str,
        module_id: str,
        lesson: LessonDefinition,
    ) -> None:
        existing = self.conn.execute(
            "SELECT content_version,state FROM academy_lesson_progress WHERE lesson_id=?",
            (lesson.lesson_id,),
        ).fetchone()
        version_changed = bool(existing and str(existing["content_version"] or "") != self.content_version)
        self.conn.execute(
            """INSERT INTO academy_lesson_progress
               (program_id,path_id,track_id,course_id,module_id,lesson_id,content_version,state)
               VALUES(?,?,?,?,?,?,?,'Not Started')
               ON CONFLICT(lesson_id) DO UPDATE SET
                   content_version=excluded.content_version,
                   program_id=excluded.program_id,
                   path_id=excluded.path_id,
                   track_id=excluded.track_id,
                   course_id=excluded.course_id,
                   module_id=excluded.module_id""",
            (program_id, path_id, track_id, course_id, module_id, lesson.lesson_id, self.content_version),
        )
        for activity in lesson.activities:
            self.conn.execute(
                """INSERT INTO academy_activity_progress
                   (lesson_id,activity_id,activity_type)
                   VALUES(?,?,?)
                   ON CONFLICT(lesson_id,activity_id) DO UPDATE SET
                       activity_type=excluded.activity_type""",
                (lesson.lesson_id, activity.activity_id, activity.activity_type.value),
            )
        if version_changed:
            self._reconcile_version_change(lesson)
        self.conn.commit()

    def _current_requirement_status(self, lesson: LessonDefinition) -> tuple[bool, bool, bool]:
        rows = {
            row["activity_id"]: row
            for row in self.conn.execute(
                "SELECT * FROM academy_activity_progress WHERE lesson_id=?", (lesson.lesson_id,)
            ).fetchall()
        }
        # In the unified Academy player every curriculum step contains an
        # interaction.  A learner therefore completes the lesson sequence by
        # passing every step marked ``required_for_completion`` rather than by
        # skipping directly to one guided and one mastery activity.
        completion_required = [a for a in lesson.activities if a.required_for_completion]
        practice_required = [a for a in completion_required if not a.required_for_mastery]
        mastery_required = [a for a in completion_required if a.required_for_mastery]
        practiced = bool(practice_required) and all(
            rows.get(a.activity_id) is not None and rows[a.activity_id]["state"] == "Passed"
            for a in practice_required
        )
        mastered = practiced and bool(mastery_required) and all(
            rows.get(a.activity_id) is not None
            and rows[a.activity_id]["state"] == "Passed"
            and not rows[a.activity_id]["last_attempt_solution_assisted"]
            for a in mastery_required
        )
        has_activity_progress = any(
            row["state"] not in (None, "Not Started")
            or bool(row["answer_text"])
            or int(row["attempt_count"] or 0) > 0
            for row in rows.values()
        )
        return practiced, mastered, has_activity_progress

    def _reconcile_version_change(self, lesson: LessonDefinition) -> ProgressState:
        """Re-evaluate a lesson when its content contract changes.

        Existing activity answers and passed activities are preserved. A previously
        mastered lesson is lowered only when the new content version introduces
        current practice or mastery requirements that have not yet been satisfied.
        """
        practiced, mastered, has_activity_progress = self._current_requirement_status(lesson)
        existing = self.conn.execute(
            "SELECT state,started_at FROM academy_lesson_progress WHERE lesson_id=?",
            (lesson.lesson_id,),
        ).fetchone()
        previously_started = bool(existing and (existing["state"] != "Not Started" or existing["started_at"]))
        if mastered:
            target = ProgressState.MASTERED
        elif practiced:
            target = ProgressState.PRACTICED
        elif previously_started or has_activity_progress:
            target = ProgressState.LEARNING
        else:
            target = ProgressState.NOT_STARTED
        now = _now()
        self.conn.execute(
            """UPDATE academy_lesson_progress SET
                   state=?,
                   content_version=?,
                   started_at=CASE WHEN ?='Not Started' THEN started_at ELSE COALESCE(started_at,?) END,
                   practiced_at=CASE WHEN ? IN ('Practiced','Mastered') THEN practiced_at ELSE NULL END,
                   mastered_at=CASE WHEN ?='Mastered' THEN mastered_at ELSE NULL END,
                   updated_at=?
               WHERE lesson_id=?""",
            (
                target.value,
                self.content_version,
                target.value,
                now,
                target.value,
                target.value,
                now,
                lesson.lesson_id,
            ),
        )
        return target

    def open_lesson(self, lesson_id: str) -> ProgressState:
        now = _now()
        self.conn.execute(
            """UPDATE academy_lesson_progress
               SET state=CASE WHEN state='Not Started' THEN 'Learning' ELSE state END,
                   started_at=COALESCE(started_at,?),
                   last_opened_at=?,updated_at=?
               WHERE lesson_id=?""",
            (now, now, now, lesson_id),
        )
        self.conn.commit()
        return self.lesson_state(lesson_id)

    def lesson_state(self, lesson_id: str) -> ProgressState:
        row = self.conn.execute(
            "SELECT state FROM academy_lesson_progress WHERE lesson_id=?", (lesson_id,)
        ).fetchone()
        return ProgressState(row[0]) if row else ProgressState.NOT_STARTED

    def lesson_rows(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM academy_lesson_progress ORDER BY rowid"
        ).fetchall()

    def activity_row(self, lesson_id: str, activity_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            """SELECT * FROM academy_activity_progress
               WHERE lesson_id=? AND activity_id=?""",
            (lesson_id, activity_id),
        ).fetchone()

    def activity_rows(self) -> dict[tuple[str, str], sqlite3.Row]:
        """Return all Academy activity progress in one indexed snapshot."""
        return {
            (str(row["lesson_id"]), str(row["activity_id"])): row
            for row in self.conn.execute(
                "SELECT * FROM academy_activity_progress"
            ).fetchall()
        }

    def save_answer(self, lesson_id: str, activity: ActivityDefinition, answer: str, notes: str = "") -> None:
        now = _now()
        self.conn.execute(
            """INSERT INTO academy_activity_progress
               (lesson_id,activity_id,activity_type,state,answer_text,notes,updated_at)
               VALUES(?,?,?,'In Progress',?,?,?)
               ON CONFLICT(lesson_id,activity_id) DO UPDATE SET
                   state=CASE WHEN academy_activity_progress.state='Passed' THEN 'Passed' ELSE 'In Progress' END,
                   answer_text=excluded.answer_text,
                   notes=excluded.notes,
                   updated_at=excluded.updated_at""",
            (lesson_id, activity.activity_id, activity.activity_type.value, answer, notes, now),
        )
        self.conn.commit()

    def reveal_hint(self, lesson_id: str, activity: ActivityDefinition) -> tuple[int, str]:
        row = self.activity_row(lesson_id, activity.activity_id)
        current = int(row["hint_level"]) if row else 0
        next_level = min(len(activity.hints), current + 1)
        self.conn.execute(
            """INSERT INTO academy_activity_progress
               (lesson_id,activity_id,activity_type,state,hint_level,updated_at)
               VALUES(?,?,?,'In Progress',?,?)
               ON CONFLICT(lesson_id,activity_id) DO UPDATE SET
                   hint_level=excluded.hint_level,
                   state=CASE WHEN academy_activity_progress.state='Passed' THEN 'Passed' ELSE 'In Progress' END,
                   updated_at=excluded.updated_at""",
            (lesson_id, activity.activity_id, activity.activity_type.value, next_level, _now()),
        )
        self.conn.commit()
        if not activity.hints:
            return 0, "No hints are available for this activity."
        return next_level, activity.hints[next_level - 1]

    def reveal_solution(self, lesson_id: str, activity: ActivityDefinition) -> str:
        now = _now()
        self.conn.execute(
            """INSERT INTO academy_activity_progress
               (lesson_id,activity_id,activity_type,state,solution_viewed_at,updated_at)
               VALUES(?,?,?,'In Progress',?,?)
               ON CONFLICT(lesson_id,activity_id) DO UPDATE SET
                   solution_viewed_at=COALESCE(academy_activity_progress.solution_viewed_at,excluded.solution_viewed_at),
                   state=CASE WHEN academy_activity_progress.state='Passed' THEN 'Passed' ELSE 'In Progress' END,
                   updated_at=excluded.updated_at""",
            (lesson_id, activity.activity_id, activity.activity_type.value, now, now),
        )
        self.conn.execute(
            "UPDATE academy_lesson_progress SET solution_viewed=1,updated_at=? WHERE lesson_id=?",
            (now, lesson_id),
        )
        self.conn.commit()
        return activity.solution

    def record_validation(
        self,
        lesson: LessonDefinition,
        activity: ActivityDefinition,
        answer: str,
        result: dict[str, Any],
    ) -> ProgressState:
        now = _now()
        passed = bool(result.get("passed"))
        current = self.activity_row(lesson.lesson_id, activity.activity_id)
        solution_assisted = bool(current and current["solution_viewed_at"])
        self.conn.execute(
            """INSERT INTO academy_activity_progress
               (lesson_id,activity_id,activity_type,state,answer_text,attempt_count,last_validation_json,
                passed_at,solution_viewed_at,last_attempt_solution_assisted,updated_at)
               VALUES(?,?,?,?,?,1,?,?,NULL,?,?)
               ON CONFLICT(lesson_id,activity_id) DO UPDATE SET
                   state=excluded.state,
                   answer_text=excluded.answer_text,
                   attempt_count=academy_activity_progress.attempt_count+1,
                   last_validation_json=excluded.last_validation_json,
                   passed_at=CASE WHEN excluded.state='Passed' THEN COALESCE(academy_activity_progress.passed_at,excluded.passed_at) ELSE academy_activity_progress.passed_at END,
                   solution_viewed_at=NULL,
                   last_attempt_solution_assisted=excluded.last_attempt_solution_assisted,
                   updated_at=excluded.updated_at""",
            (
                lesson.lesson_id,
                activity.activity_id,
                activity.activity_type.value,
                "Passed" if passed else "Needs Review",
                answer,
                json.dumps(result, sort_keys=True, default=str),
                now if passed else None,
                int(solution_assisted),
                now,
            ),
        )
        self.conn.execute(
            "UPDATE academy_lesson_progress SET attempt_count=attempt_count+1,updated_at=? WHERE lesson_id=?",
            (now, lesson.lesson_id),
        )
        state = self._recompute_lesson(lesson)
        self.conn.commit()
        return state

    def _recompute_lesson(self, lesson: LessonDefinition) -> ProgressState:
        practiced, mastered, _ = self._current_requirement_status(lesson)
        old = self.lesson_state(lesson.lesson_id)
        target = old
        if mastered:
            target = ProgressState.MASTERED
        elif practiced and old.rank < ProgressState.PRACTICED.rank:
            target = ProgressState.PRACTICED
        elif old == ProgressState.NOT_STARTED:
            target = ProgressState.LEARNING
        now = _now()
        self.conn.execute(
            """UPDATE academy_lesson_progress SET
                   state=?,
                   started_at=COALESCE(started_at,?),
                   practiced_at=CASE WHEN ? IN ('Practiced','Mastered') THEN COALESCE(practiced_at,?) ELSE practiced_at END,
                   mastered_at=CASE WHEN ?='Mastered' THEN COALESCE(mastered_at,?) ELSE mastered_at END,
                   updated_at=?
               WHERE lesson_id=?""",
            (target.value, now, target.value, now, target.value, now, now, lesson.lesson_id),
        )
        return target

    def mastered_skills(self) -> set[str]:
        rows = self.conn.execute(
            """SELECT DISTINCT skill_key FROM academy_skill_evidence
               WHERE validation_status IN ('passed','mastered')"""
        ).fetchall()
        return {row[0] for row in rows}
