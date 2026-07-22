from __future__ import annotations

import json
import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .catalog import CatalogIndex
from .loader import load_catalog
from .models import ActivityDefinition, ActivityType, AssessmentDefinition, LessonDefinition, SkillsLabDefinition
from .progress import ProgressRepository
from .recommendations import AcademyRecommendation, RecommendationEngine
from .schema import ensure_academy_schema
from .validators import SqlValidator, ValidationResult, validate_recognition


class AcademyService:
    """Application-facing facade for the generic curriculum engine."""

    TRACK_KEY = "academy"
    DESTINATION_INDEX = 12

    def __init__(self, conn: sqlite3.Connection, repository_root: str | Path):
        self.conn = conn
        self.repository_root = Path(repository_root).resolve()
        self.curriculum_root = self.repository_root / "curriculum" / "data"
        ensure_academy_schema(conn)
        self.catalog = load_catalog(self.curriculum_root)
        self.index = CatalogIndex(self.catalog)
        self.progress = ProgressRepository(
            conn,
            self.catalog.program.content_version,
            {lesson.lesson_id: lesson.teaches for lesson in self.catalog.lessons()},
        )
        self.recommendations = RecommendationEngine(self.index, self.progress)
        self._register_package()
        self._seed_progress()
        self.progress.reconcile_lessons(self.catalog.lessons())
        # Academy activity rows are the source of truth. Rebuild the adaptive
        # completion ledger and today's focus state from those rows before the
        # next recommendation is exposed to the legacy planner.
        self._reconcile_activity_events()
        self._reconcile_today_focus_progress()
        self._retire_datacamp_recommendations()
        self.sync_planner_task()


    @staticmethod
    def _activity_target_key(lesson_id: str, activity_id: str) -> str:
        return f"academy:activity:{lesson_id}:{activity_id}"

    def _activity_definition(self, lesson_id: str, activity_id: str):
        try:
            lesson = self.catalog.lesson(str(lesson_id))
        except Exception:
            return None, None
        activity = next(
            (item for item in lesson.activities if item.activity_id == str(activity_id)),
            None,
        )
        return lesson, activity

    def _activity_row_complete(self, lesson, activity, row) -> bool:
        if lesson is None or activity is None or row is None:
            return False
        if str(row["state"] or "") != "Passed":
            return False
        if activity.required_for_mastery and bool(row["last_attempt_solution_assisted"]):
            return False
        return True

    def _insert_activity_event(self, lesson, activity, row) -> None:
        """Record one adaptive completion for a passed Academy action.

        The event ledger powers Today/Week counters. It is intentionally
        separate from Demonstrated Evidence, which remains limited to projects,
        capstones, and labs.
        """
        if not activity.required_for_completion:
            return
        if not self._activity_row_complete(lesson, activity, row):
            return
        passed_at = str(row["passed_at"] or row["updated_at"] or "")
        completed_date = passed_at[:10] if len(passed_at) >= 10 else date.today().isoformat()
        target_key = self._activity_target_key(lesson.lesson_id, activity.activity_id)
        metadata = {
            "lesson_id": lesson.lesson_id,
            "activity_id": activity.activity_id,
            "target_key": target_key,
            "task_kind": "lesson_step",
        }
        self.conn.execute(
            """INSERT OR IGNORE INTO track_events
               (track_key,event_key,event_type,item_label,completed_date,metadata)
               VALUES('academy',?,'Completed',?,?,?)""",
            (
                target_key,
                f"{lesson.title} — {activity.title}",
                completed_date,
                json.dumps(metadata, sort_keys=True),
            ),
        )

    def _reconcile_activity_events(self) -> None:
        """Backfill missing Academy counters from durable passed activities."""
        try:
            rows = self.progress.activity_rows()
            for location in self.index.ordered_lessons():
                for activity in location.lesson.activities:
                    row = rows.get((location.lesson.lesson_id, activity.activity_id))
                    self._insert_activity_event(location.lesson, activity, row)
            self.conn.commit()
        except sqlite3.OperationalError:
            # Standalone curriculum tests may omit legacy adaptive tables.
            self.conn.rollback()

    def _target_is_complete(self, target_key: str) -> bool:
        parts = str(target_key or "").split(":", 3)
        if len(parts) != 4 or parts[:2] != ["academy", "activity"]:
            return False
        lesson, activity = self._activity_definition(parts[2], parts[3])
        if lesson is None or activity is None:
            return False
        row = self.progress.activity_row(lesson.lesson_id, activity.activity_id)
        return self._activity_row_complete(lesson, activity, row)

    def _reconcile_today_focus_progress(self) -> None:
        """Freeze completed Academy focus rows before the reusable task advances."""
        try:
            today = date.today().isoformat()
            rows = self.conn.execute(
                """SELECT id,target_key FROM daily_focus
                   WHERE focus_date=? AND completed_at IS NULL
                     AND (LOWER(COALESCE(track_key,''))='academy'
                          OR LOWER(COALESCE(source_key,''))='roadmap:academy')""",
                (today,),
            ).fetchall()
            for row in rows:
                if self._target_is_complete(str(row["target_key"] or "")):
                    self.conn.execute(
                        "UPDATE daily_focus SET completed_at=CURRENT_TIMESTAMP WHERE id=?",
                        (int(row["id"]),),
                    )
            self.conn.commit()
        except sqlite3.OperationalError:
            self.conn.rollback()

    def _adaptive_progress(self, weekly_target: int = 2) -> dict[str, int | str | bool]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        try:
            today_completed = int(
                self.conn.execute(
                    """SELECT COUNT(*) FROM track_events
                       WHERE track_key='academy' AND completed_date=?""",
                    (today.isoformat(),),
                ).fetchone()[0]
            )
            weekly_completed = int(
                self.conn.execute(
                    """SELECT COUNT(*) FROM track_events
                       WHERE track_key='academy' AND completed_date BETWEEN ? AND ?""",
                    (week_start.isoformat(), week_end.isoformat()),
                ).fetchone()[0]
            )
        except sqlite3.OperationalError:
            today_completed = 0
            weekly_completed = 0
        weekly_target = max(0, int(weekly_target or 0))
        today_target = (
            1
            if weekly_target > 0 and (weekly_completed < weekly_target or today_completed > 0)
            else 0
        )
        daily_complete = today_target == 0 or today_completed >= today_target
        weekly_complete = weekly_target > 0 and weekly_completed >= weekly_target
        return {
            "today_target": today_target,
            "today_completed": today_completed,
            "weekly_target": weekly_target,
            "weekly_completed": weekly_completed,
            "daily_goal_complete": daily_complete,
            "weekly_goal_complete": weekly_complete,
            "pace_status": (
                "Weekly goal complete" if weekly_complete
                else "Daily goal complete" if daily_complete
                else "Ready when you are"
            ),
        }


    def _retire_datacamp_recommendations(self) -> None:
        """Keep legacy completion history but remove DataCamp from active planning.

        DataCamp events and state remain available as external-learning history.
        Only generated adaptive tasks and daily-focus assignments are retired.
        """
        try:
            linked_rows = self.conn.execute(
                "SELECT task_id FROM track_tasks WHERE LOWER(track_key)='datacamp'"
            ).fetchall()
            task_ids = {int(row[0]) for row in linked_rows}
            generated_rows = self.conn.execute(
                """SELECT id FROM sprint_tasks
                   WHERE completed=0 AND sort_order<0
                     AND LOWER(label) LIKE '%datacamp%'"""
            ).fetchall()
            task_ids.update(int(row[0]) for row in generated_rows)

            removed_focus = self.conn.execute(
                """DELETE FROM daily_focus
                   WHERE LOWER(COALESCE(track_key,''))='datacamp'
                      OR LOWER(COALESCE(source_key,''))='roadmap:datacamp'
                      OR LOWER(COALESCE(title,'')) LIKE '%datacamp%'"""
            ).rowcount

            # Today's focus is derived data.  A snapshot created before the
            # Academy migration can otherwise stay frozen with an empty second
            # learning slot after DataCamp is removed.  Regenerate untouched
            # snapshots so Academy can take the replacement slot immediately.
            focus_date = date.today().isoformat()
            focus_rows = self.conn.execute(
                """SELECT track_key,source_key,completed_at
                   FROM daily_focus WHERE focus_date=?""",
                (focus_date,),
            ).fetchall()
            has_academy = any(
                str(row[0] or "").lower() == self.TRACK_KEY
                or str(row[1] or "").lower() == f"roadmap:{self.TRACK_KEY}"
                for row in focus_rows
            )
            has_completed_focus = any(row[2] for row in focus_rows)
            if removed_focus or (focus_rows and not has_academy and not has_completed_focus):
                self.conn.execute("DELETE FROM daily_focus WHERE focus_date=?", (focus_date,))

            self.conn.execute("DELETE FROM track_tasks WHERE LOWER(track_key)='datacamp'")
            if task_ids:
                placeholders = ",".join("?" for _ in task_ids)
                values = tuple(sorted(task_ids))
                self.conn.execute(
                    f"DELETE FROM task_metadata WHERE task_id IN ({placeholders})", values
                )
                self.conn.execute(
                    f"DELETE FROM sprint_tasks WHERE id IN ({placeholders})", values
                )

            row = self.conn.execute(
                "SELECT metadata FROM track_state WHERE track_key='datacamp'"
            ).fetchone()
            if row is not None:
                try:
                    metadata = json.loads(row[0] or "{}")
                except (TypeError, ValueError, json.JSONDecodeError):
                    metadata = {}
                metadata.update(
                    {
                        "active_recommendations": False,
                        "replacement_track": self.TRACK_KEY,
                        "history_preserved": True,
                    }
                )
                self.conn.execute(
                    """UPDATE track_state
                       SET weekly_target=0,status='External History',metadata=?,
                           updated_at=CURRENT_TIMESTAMP
                       WHERE track_key='datacamp'""",
                    (json.dumps(metadata),),
                )
            self.conn.commit()
        except sqlite3.OperationalError:
            self.conn.rollback()

    @property
    def labels(self) -> dict[str, str]:
        return dict(self.catalog.program.learning)

    def _register_package(self) -> None:
        program = self.catalog.program
        self.conn.execute("UPDATE academy_packages SET active=0")
        self.conn.execute(
            """INSERT INTO academy_packages
               (package_id,program_id,schema_version,content_version,content_hash,root_path,active)
               VALUES(?,?,?,?,?,?,1)
               ON CONFLICT(package_id) DO UPDATE SET
                   program_id=excluded.program_id,
                   schema_version=excluded.schema_version,
                   content_version=excluded.content_version,
                   content_hash=excluded.content_hash,
                   root_path=excluded.root_path,
                   installed_at=CURRENT_TIMESTAMP,
                   active=1""",
            (
                f"{program.program_id}:{program.content_version}",
                program.program_id,
                program.schema_version,
                program.content_version,
                self.catalog.content_hash,
                str(self.curriculum_root),
            ),
        )
        for path in program.paths:
            self.conn.execute(
                """INSERT INTO academy_enrollments(program_id,path_id,status)
                   VALUES(?,?,'Active')
                   ON CONFLICT(program_id,path_id) DO NOTHING""",
                (program.program_id, path.path_id),
            )
        self.conn.commit()

    def _seed_progress(self) -> None:
        for location in self.index.ordered_lessons():
            self.progress.seed_lesson(
                program_id=self.catalog.program.program_id,
                path_id=location.path.path_id,
                track_id=location.track.track_id,
                course_id=location.course.course_id,
                module_id=location.module.module_id,
                lesson=location.lesson,
            )

    def next_recommendation(self) -> AcademyRecommendation | None:
        return self.recommendations.next()

    def path_complete(self) -> bool:
        """Return completion from required progress, never from task availability."""

        return self.recommendations.is_complete()

    def open_lesson(self, lesson_id: str):
        return self.progress.open_lesson(lesson_id)

    def activity_progress(self, lesson_id: str, activity_id: str):
        return self.progress.activity_row(lesson_id, activity_id)

    def lesson_unlocked(self, lesson_id: str) -> tuple[bool, tuple[str, ...]]:
        return self.recommendations.lesson_unlocked(self.index.lesson(lesson_id))

    def activity_unlocked(
        self,
        lesson_id: str,
        activity_id: str,
    ) -> tuple[bool, str | None]:
        location = self.index.lesson(lesson_id)
        activity = next(
            (item for item in location.lesson.activities if item.activity_id == activity_id),
            None,
        )
        if activity is None:
            return False, "Unknown lesson step."
        return self.recommendations.activity_unlocked(location, activity)

    def activity_passed(self, lesson_id: str, activity_id: str) -> bool:
        row = self.progress.activity_row(lesson_id, activity_id)
        return bool(row and row["state"] == "Passed")

    def activity_complete(self, lesson_id: str, activity: ActivityDefinition) -> bool:
        row = self.progress.activity_row(lesson_id, activity.activity_id)
        if not row or row["state"] != "Passed":
            return False
        if activity.required_for_mastery and row["last_attempt_solution_assisted"]:
            return False
        return True

    def assessment_passed(self, assessment_id: str) -> bool:
        return self.recommendations.assessment_passed(assessment_id)

    def assessment_unlocked(self, assessment: AssessmentDefinition) -> tuple[bool, tuple[str, ...]]:
        missing = self._missing_skills(assessment.requires)
        return not missing, missing

    def skills_lab_unlocked(self, lab: SkillsLabDefinition) -> tuple[bool, tuple[str, ...]]:
        missing = list(self._missing_skills(lab.requires))
        for course in self.catalog.courses():
            if lab not in course.skills_labs:
                continue
            for assessment in course.assessments:
                if not self.assessment_passed(assessment.assessment_id):
                    missing.append(f"checkpoint:{assessment.title}")
        return not missing, tuple(missing)

    def remember_target(self, target_key: str) -> None:
        program = self.catalog.program
        if not program.paths:
            return
        self.conn.execute(
            """UPDATE academy_enrollments SET last_target_key=?
               WHERE program_id=? AND path_id=?""",
            (target_key, program.program_id, program.paths[0].path_id),
        )
        self.conn.commit()

    def last_target(self) -> str | None:
        program = self.catalog.program
        if not program.paths:
            return None
        row = self.conn.execute(
            """SELECT last_target_key FROM academy_enrollments
               WHERE program_id=? AND path_id=?""",
            (program.program_id, program.paths[0].path_id),
        ).fetchone()
        return str(row[0]) if row and row[0] else None

    def validate_activity(
        self,
        lesson: LessonDefinition,
        activity: ActivityDefinition,
        answer: str,
    ) -> ValidationResult:
        self.progress.save_answer(lesson.lesson_id, activity, answer)
        if activity.runtime == "recognition":
            result = validate_recognition(answer, dict(activity.validator))
        elif activity.runtime == "sql":
            dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
            dataset = self.catalog.datasets[dataset_id]
            result = SqlValidator(dataset).validate(answer, dict(activity.validator))
        else:
            result = ValidationResult(False, f"Unsupported activity runtime: {activity.runtime}")
        state = self.progress.record_validation(lesson, activity, answer, result.as_dict())
        # Record adaptive progress from the authoritative activity row. This is
        # not employer-facing evidence; it only powers Today/Week counters and
        # freezes the matching daily-focus assignment before the task advances.
        current_row = self.progress.activity_row(lesson.lesson_id, activity.activity_id)
        self._insert_activity_event(lesson, activity, current_row)
        self._reconcile_today_focus_progress()
        # Lesson and checkpoint progress demonstrate learning, but only
        # substantial Academy projects, capstones, and labs belong in the
        # employer-facing Demonstrated Evidence collection.
        self.sync_planner_task()
        return result

    def run_activity(self, activity: ActivityDefinition, answer: str) -> ValidationResult:
        if activity.runtime != "sql":
            return ValidationResult(False, "Run is available for executable activities.")
        dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
        return SqlValidator(self.catalog.datasets[dataset_id]).execute(answer)

    def activity_table_schemas(
        self,
        activity: ActivityDefinition,
    ) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
        """Return schemas for the tables referenced by a learning action.

        Curriculum authors normally declare ``presentation.table`` or
        ``presentation.tables``. A conservative text lookup is retained as a
        fallback for older packages so updated application code can still show
        useful schemas without breaking saved curriculum.
        """
        dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
        dataset = self.catalog.datasets.get(dataset_id)
        if dataset is None:
            return ()
        presentation = dict(activity.presentation)
        declared = presentation.get("tables", presentation.get("table"))
        if isinstance(declared, str):
            requested = [item.strip() for item in declared.split(",") if item.strip()]
        elif isinstance(declared, (list, tuple)):
            requested = [str(item).strip() for item in declared if str(item).strip()]
        else:
            requested = []
        known = {table.name for table in dataset.tables}
        requested = [name for name in requested if name in known]
        if not requested:
            searchable = " \n".join(
                (
                    activity.prompt,
                    activity.starter,
                    activity.solution,
                    str(presentation),
                    str(activity.instruction),
                )
            )
            requested = [
                table.name
                for table in dataset.tables
                if re.search(rf"(?<![A-Za-z0-9_]){re.escape(table.name)}(?![A-Za-z0-9_])", searchable)
            ]
        if not requested and len(dataset.tables) == 1:
            requested = [dataset.tables[0].name]
        validator = SqlValidator(dataset)
        return tuple((name, validator.table_schema(name)) for name in dict.fromkeys(requested))

    def save_assessment_draft(
        self,
        assessment_id: str,
        activity_id: str,
        answer: str,
        validation: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """INSERT INTO academy_assessment_drafts
               (assessment_id,activity_id,answer_text,validation_json,updated_at)
               VALUES(?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(assessment_id,activity_id) DO UPDATE SET
                   answer_text=excluded.answer_text,
                   validation_json=excluded.validation_json,
                   updated_at=CURRENT_TIMESTAMP""",
            (
                assessment_id,
                activity_id,
                answer,
                json.dumps(validation or {}, sort_keys=True, default=str),
            ),
        )
        self.conn.commit()

    def assessment_drafts(self, assessment_id: str) -> dict[str, str]:
        rows = self.conn.execute(
            """SELECT activity_id,answer_text FROM academy_assessment_drafts
               WHERE assessment_id=?""",
            (assessment_id,),
        ).fetchall()
        return {str(row["activity_id"]): str(row["answer_text"] or "") for row in rows}

    def validate_assessment_activity(
        self,
        assessment: AssessmentDefinition,
        activity: ActivityDefinition,
        answer: str,
    ) -> ValidationResult:
        unlocked, missing = self.assessment_unlocked(assessment)
        if not unlocked:
            return ValidationResult(False, "Prerequisites not yet mastered: " + ", ".join(missing))
        if activity.runtime == "recognition":
            result = validate_recognition(answer, dict(activity.validator))
        elif activity.runtime == "sql":
            dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
            result = SqlValidator(self.catalog.datasets[dataset_id]).validate(
                answer,
                dict(activity.validator),
            )
        else:
            result = ValidationResult(False, f"Unsupported activity runtime: {activity.runtime}")
        self.save_assessment_draft(
            assessment.assessment_id,
            activity.activity_id,
            answer,
            result.as_dict(),
        )
        return result

    def reveal_hint(self, lesson_id: str, activity: ActivityDefinition) -> tuple[int, str]:
        return self.progress.reveal_hint(lesson_id, activity)

    def reveal_solution(self, lesson_id: str, activity: ActivityDefinition) -> str:
        return self.progress.reveal_solution(lesson_id, activity)

    def _missing_skills(self, required: tuple[str, ...]) -> tuple[str, ...]:
        mastered = self.progress.mastered_skills()
        return tuple(skill for skill in required if skill not in mastered)

    def validate_assessment(
        self,
        assessment: AssessmentDefinition,
        answers: dict[str, str],
    ) -> dict[str, Any]:
        if not answers:
            answers = self.assessment_drafts(assessment.assessment_id)
        missing = self._missing_skills(assessment.requires)
        if missing:
            return {
                "passed": False,
                "score": 0.0,
                "results": {},
                "feedback": "Prerequisites not yet mastered: " + ", ".join(missing),
            }
        results: dict[str, dict[str, Any]] = {}
        earned = 0
        solution_assisted = False
        for activity in assessment.activities:
            answer = answers.get(activity.activity_id, "")
            if activity.runtime == "recognition":
                result = validate_recognition(answer, dict(activity.validator))
            else:
                dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
                result = SqlValidator(self.catalog.datasets[dataset_id]).validate(answer, dict(activity.validator))
            results[activity.activity_id] = result.as_dict()
            earned += int(result.passed)
        score = earned / max(1, len(assessment.activities))
        passed = score >= assessment.passing_score and not solution_assisted
        previous = self.conn.execute(
            "SELECT COALESCE(MAX(attempt_number),0) FROM academy_assessment_attempts WHERE assessment_id=?",
            (assessment.assessment_id,),
        ).fetchone()[0]
        self.conn.execute(
            """INSERT INTO academy_assessment_attempts
               (assessment_id,attempt_number,score,passed,solution_assisted,answers_json,result_json,completed_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                assessment.assessment_id,
                int(previous) + 1,
                score,
                int(passed),
                int(solution_assisted),
                json.dumps(answers, sort_keys=True),
                json.dumps(results, sort_keys=True, default=str),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
        self.sync_planner_task()
        return {
            "passed": passed,
            "score": score,
            "results": results,
            "feedback": (
                "Checkpoint passed. The course Skills Lab is now unlocked."
                if passed
                else "Checkpoint not yet passed. Review the missed questions and submit another attempt."
            ),
        }


    def save_skills_lab_progress(
        self,
        lab: SkillsLabDefinition,
        sql: str,
        notes: str,
    ) -> Path:
        """Persist an in-progress Skills Lab artifact without validating it."""
        result = ValidationResult(False, "Saved in progress.")
        return self._save_submission("skills_lab", lab.lab_id, lab.title, sql, notes, result)

    def validate_skills_lab(
        self,
        lab: SkillsLabDefinition,
        sql: str,
        notes: str,
    ) -> ValidationResult:
        unlocked, missing = self.skills_lab_unlocked(lab)
        if not unlocked:
            readable = [
                item.split(":", 1)[1] if item.startswith("checkpoint:") else item
                for item in missing
            ]
            return ValidationResult(False, "Complete these prerequisites first: " + ", ".join(readable))
        validator = SqlValidator(self.catalog.datasets[lab.dataset_id])
        result = validator.validate(sql, dict(lab.activity.validator))
        if result.passed and len([line for line in notes.splitlines() if line.strip()]) < 3:
            result = ValidationResult(
                False,
                "The submitted work is correct. Add at least three concise findings before submitting the project.",
                result.columns,
                result.rows,
                result.details,
            )
        artifact_path = self._save_submission("skills_lab", lab.lab_id, lab.title, sql, notes, result)
        if result.passed:
            source_type = str(
                lab.evidence.get("source_type")
                or ("Academy Capstone" if "capstone" in lab.lab_id.casefold() else "Academy Project")
            )
            relative_artifact = str(artifact_path.relative_to(self.repository_root))
            for skill in lab.teaches:
                self._insert_evidence(
                    skill=skill,
                    source_type=source_type,
                    source_id=lab.lab_id,
                    source_name=lab.title,
                    course_id=self._course_id_for_lab(lab.lab_id),
                    learning_item_id=lab.lab_id,
                    difficulty=lab.activity.difficulty,
                    dataset=lab.dataset_id,
                    submission_path=relative_artifact,
                    job_competency=str(lab.evidence.get("job_competency") or "Applied analysis"),
                    notes=notes,
                    metadata={"validation": result.as_dict(), "deliverables": list(lab.deliverables)},
                )
            self._record_project_evidence(
                lab=lab,
                source_type=source_type,
                artifact_path=relative_artifact,
                notes=notes,
            )
        self.sync_planner_task()
        return result

    def _save_submission(
        self,
        item_type: str,
        item_id: str,
        title: str,
        answer: str,
        notes: str,
        result: ValidationResult,
    ) -> Path:
        folder = self.repository_root / "workspaces" / "academy" / item_type
        folder.mkdir(parents=True, exist_ok=True)
        artifact = folder / f"{item_id}.sql"
        content = answer.rstrip() + "\n\n-- Findings / notes\n" + "\n".join(
            f"-- {line}" for line in notes.strip().splitlines()
        ) + "\n"
        artifact.write_text(content, encoding="utf-8")
        self.conn.execute(
            """INSERT INTO academy_submissions
               (item_type,item_id,title,answer_text,notes,artifact_path,validation_status,validation_json,updated_at)
               VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(item_type,item_id) DO UPDATE SET
                   title=excluded.title,
                   answer_text=excluded.answer_text,
                   notes=excluded.notes,
                   artifact_path=excluded.artifact_path,
                   validation_status=excluded.validation_status,
                   validation_json=excluded.validation_json,
                   updated_at=CURRENT_TIMESTAMP""",
            (
                item_type,
                item_id,
                title,
                answer,
                notes,
                str(artifact.relative_to(self.repository_root)),
                "Passed" if result.passed else "Needs Review",
                json.dumps(result.as_dict(), sort_keys=True, default=str),
            ),
        )
        self.conn.commit()
        return artifact

    def _course_id_for_lab(self, lab_id: str) -> str | None:
        for course in self.catalog.courses():
            if any(lab.lab_id == lab_id for lab in course.skills_labs):
                return course.course_id
        return None

    def _record_project_evidence(
        self,
        *,
        lab: SkillsLabDefinition,
        source_type: str,
        artifact_path: str,
        notes: str,
    ) -> None:
        display_skills = [
            str(self.catalog.skills.get(skill, {}).get("title") or skill)
            for skill in lab.teaches
        ]
        skill_summary = ", ".join(dict.fromkeys(display_skills)) or "Applied analysis"
        competency = str(lab.evidence.get("job_competency") or "Applied analysis")
        description = (
            f"Completed and validated {lab.title}. "
            f"Skills demonstrated: {skill_summary}. "
            f"Artifact: {artifact_path}."
        )
        if notes.strip():
            description += " Findings and notes are saved with the submission."
        self.conn.execute(
            """DELETE FROM evidence
               WHERE source_type=? AND source_name=?""",
            (source_type, lab.title),
        )
        self.conn.execute(
            """INSERT INTO evidence(skill,source_type,source_name,description)
               VALUES(?,?,?,?)""",
            (skill_summary, source_type, lab.title, description),
        )
        self.conn.commit()

    def _insert_evidence(
        self,
        *,
        skill: str,
        source_type: str,
        source_id: str,
        source_name: str,
        course_id: str | None,
        learning_item_id: str,
        difficulty: str | None,
        dataset: str | None,
        submission_path: str | None,
        job_competency: str,
        notes: str,
        metadata: dict[str, Any],
    ) -> None:
        program = self.catalog.program
        path_id = program.paths[0].path_id if program.paths else "default"
        self.conn.execute(
            """INSERT INTO academy_skill_evidence
               (program_id,path_id,course_id,learning_item_id,skill_key,source_type,source_id,
                difficulty,dataset,submission_path,evidence_level,validation_status,job_competency,
                evidence_notes,metadata)
               VALUES(?,?,?,?,?,?,?,?,?,?, 'demonstrated','passed',?,?,?)
               ON CONFLICT(skill_key,source_type,source_id) DO UPDATE SET
                   validation_status='passed',
                   submission_path=COALESCE(excluded.submission_path,academy_skill_evidence.submission_path),
                   evidence_notes=excluded.evidence_notes,
                   metadata=excluded.metadata,
                   demonstrated_at=CURRENT_TIMESTAMP""",
            (
                program.program_id,
                path_id,
                course_id,
                learning_item_id,
                skill,
                source_type,
                source_id,
                difficulty,
                dataset,
                submission_path,
                job_competency,
                notes,
                json.dumps(metadata, sort_keys=True, default=str),
            ),
        )
        # Keep the existing prerequisite inventory aware of Academy mastery.
        try:
            display = str(self.catalog.skills.get(skill, {}).get("title") or skill)
            self.conn.execute(
                """INSERT INTO skill_state(skill_key,display_name,status,source_track,evidence,updated_at)
                   VALUES(?,?,'Demonstrated','academy',?,CURRENT_TIMESTAMP)
                   ON CONFLICT(skill_key) DO UPDATE SET
                       display_name=excluded.display_name,
                       status='Demonstrated',
                       source_track='academy',
                       evidence=excluded.evidence,
                       updated_at=CURRENT_TIMESTAMP""",
                (skill, display, f"{source_type}: {source_name}"),
            )
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def evidence_rows(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT skill_key,source_type,source_id,difficulty,dataset,submission_path,
                      job_competency,reviewer_status,evidence_notes,demonstrated_at
               FROM academy_skill_evidence
               WHERE source_type IN ('Skills Lab','Academy Project','Academy Capstone')
               ORDER BY demonstrated_at DESC, id DESC"""
        ).fetchall()

    def completion_summary(self) -> dict[str, int]:
        rows = self.progress.lesson_rows()
        return {
            "total": len(rows),
            "learning": sum(row["state"] == "Learning" for row in rows),
            "practiced": sum(row["state"] == "Practiced" for row in rows),
            "mastered": sum(row["state"] == "Mastered" for row in rows),
        }

    def _sync_today_academy_focus(
        self,
        *,
        task_id: int,
        recommendation: AcademyRecommendation,
        current_week: int,
    ) -> None:
        """Keep today's Academy assignment aligned with the live next step.

        Academy reuses one adaptive task row. A completed or stale frozen focus
        row can therefore hide the newly unlocked lesson. This repair updates an
        active Academy row in place or appends the new step when today's prior
        Academy assignment is already complete. No focus plan is created when the
        learner has not opened/generated today's plan yet.
        """

        focus_date = date.today().isoformat()
        try:
            total_rows = int(
                self.conn.execute(
                    "SELECT COUNT(*) FROM daily_focus WHERE focus_date=?",
                    (focus_date,),
                ).fetchone()[0]
            )
            if total_rows <= 0:
                return
            rows = self.conn.execute(
                """SELECT id,target_key,completed_at,position
                   FROM daily_focus
                   WHERE focus_date=?
                     AND (LOWER(COALESCE(track_key,''))=?
                          OR LOWER(COALESCE(source_key,''))=?)
                   ORDER BY position""",
                (focus_date, self.TRACK_KEY, f"roadmap:{self.TRACK_KEY}"),
            ).fetchall()
            for row in rows:
                if (
                    not row["completed_at"]
                    and str(row["target_key"] or "") == recommendation.target_key
                ):
                    self.conn.execute(
                        """UPDATE daily_focus
                           SET task_id=?,title=?,estimated_minutes=?,track_key=?,
                               target_key=?,source_key=?,category='Learning'
                           WHERE id=?""",
                        (
                            task_id,
                            recommendation.title,
                            recommendation.estimated_minutes,
                            self.TRACK_KEY,
                            recommendation.target_key,
                            f"roadmap:{self.TRACK_KEY}",
                            int(row["id"]),
                        ),
                    )
                    return
            active = next((row for row in rows if not row["completed_at"]), None)
            if active is not None:
                self.conn.execute(
                    """UPDATE daily_focus
                       SET task_id=?,title=?,estimated_minutes=?,track_key=?,
                           target_key=?,source_key=?,category='Learning'
                       WHERE id=?""",
                    (
                        task_id,
                        recommendation.title,
                        recommendation.estimated_minutes,
                        self.TRACK_KEY,
                        recommendation.target_key,
                        f"roadmap:{self.TRACK_KEY}",
                        int(active["id"]),
                    ),
                )
                return
            position = int(
                self.conn.execute(
                    """SELECT COALESCE(MAX(position),0)+1
                       FROM daily_focus WHERE focus_date=?""",
                    (focus_date,),
                ).fetchone()[0]
            )
            self.conn.execute(
                """INSERT INTO daily_focus
                   (focus_date,week,position,task_id,source_key,category,title,
                    estimated_minutes,track_key,target_key,is_extra,completed_at)
                   VALUES(?,?,?,?,?,'Learning',?,?,?,?,0,NULL)""",
                (
                    focus_date,
                    current_week,
                    position,
                    task_id,
                    f"roadmap:{self.TRACK_KEY}",
                    recommendation.title,
                    recommendation.estimated_minutes,
                    self.TRACK_KEY,
                    recommendation.target_key,
                ),
            )
        except sqlite3.OperationalError:
            # Standalone engine tests may not include the legacy planner tables.
            return

    def sync_planner_task(self) -> None:
        """Expose the next prerequisite-ready Academy action to the existing planner."""
        recommendation = self.next_recommendation()
        try:
            current_week = int(
                self.conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone()[0]
            )
            system_name = self.labels.get("system_name", "Learning System")
            existing_state = self.conn.execute(
                "SELECT weekly_target FROM track_state WHERE track_key=?",
                (self.TRACK_KEY,),
            ).fetchone()
            weekly_target = int(existing_state[0]) if existing_state is not None else 2
            adaptive = self._adaptive_progress(weekly_target)
            initial_metadata = {
                "provider": "internal",
                "program_id": self.catalog.program.program_id,
                **adaptive,
            }
            status = (
                "Weekly Complete" if adaptive["weekly_goal_complete"]
                else "Daily Complete" if adaptive["daily_goal_complete"]
                else "Active"
            )
            self.conn.execute(
                """INSERT INTO track_state(track_key,display_name,position,subposition,weekly_target,status,metadata)
                   VALUES(?,?,0,0,?,?,?)
                   ON CONFLICT(track_key) DO UPDATE SET
                       display_name=excluded.display_name,
                       weekly_target=excluded.weekly_target,
                       status=excluded.status,
                       metadata=excluded.metadata,
                       updated_at=CURRENT_TIMESTAMP""",
                (
                    self.TRACK_KEY,
                    system_name,
                    int(adaptive["weekly_target"]),
                    status,
                    json.dumps(initial_metadata),
                ),
            )
            if recommendation is None and self.path_complete():
                existing = self.conn.execute(
                    "SELECT task_id FROM track_tasks WHERE track_key=?", (self.TRACK_KEY,)
                ).fetchone()
                if existing:
                    task_id = int(existing[0])
                    self.conn.execute(
                        "UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,)
                    )
                    self.conn.execute(
                        "UPDATE task_metadata SET status='Completed' WHERE task_id=?", (task_id,)
                    )
                self.conn.execute(
                    "UPDATE track_state SET status='Completed',updated_at=CURRENT_TIMESTAMP WHERE track_key=?",
                    (self.TRACK_KEY,),
                )
                self.conn.commit()
                return
            if recommendation is None:
                self.conn.execute(
                    "UPDATE track_state SET status='Active',updated_at=CURRENT_TIMESTAMP WHERE track_key=?",
                    (self.TRACK_KEY,),
                )
                self.conn.commit()
                return
            existing = self.conn.execute(
                "SELECT task_id,target_key FROM track_tasks WHERE track_key=?",
                (self.TRACK_KEY,),
            ).fetchone()
            if (
                existing is not None
                and str(existing["target_key"] or "") != recommendation.target_key
                and self._target_is_complete(str(existing["target_key"] or ""))
            ):
                completed_task_id = int(existing["task_id"])
                self.conn.execute(
                    "UPDATE sprint_tasks SET completed=1 WHERE id=?",
                    (completed_task_id,),
                )
                self.conn.execute(
                    """UPDATE task_metadata
                       SET status='Completed',deferred_until=NULL
                       WHERE task_id=?""",
                    (completed_task_id,),
                )
                self.conn.execute(
                    "DELETE FROM track_tasks WHERE track_key=?",
                    (self.TRACK_KEY,),
                )
                existing = None
            label = recommendation.title
            planner_metadata = {
                "provider": "internal",
                "program_id": self.catalog.program.program_id,
                "title": recommendation.title,
                "target_key": recommendation.target_key,
                "estimated_minutes": recommendation.estimated_minutes,
                **adaptive,
                "alignment": "Built-in Accelerator Academy learning",
            }
            self.conn.execute(
                """UPDATE track_state SET metadata=?,updated_at=CURRENT_TIMESTAMP
                   WHERE track_key=?""",
                (json.dumps(planner_metadata), self.TRACK_KEY),
            )
            if existing:
                task_id = int(existing[0])
                self.conn.execute(
                    "UPDATE sprint_tasks SET week=?,label=?,completed=0 WHERE id=?",
                    (current_week, label, task_id),
                )
                self.conn.execute(
                    """UPDATE task_metadata SET status='Not Started',priority=2,
                       estimated_minutes=?,energy='Normal',destination=?,category=?,
                       prerequisite_state='Ready',prerequisite_reason=NULL WHERE task_id=?""",
                    (recommendation.estimated_minutes, self.DESTINATION_INDEX, "Learning", task_id),
                )
                self.conn.execute(
                    """UPDATE track_tasks SET target_key=?,source_label=?,updated_at=CURRENT_TIMESTAMP
                       WHERE track_key=?""",
                    (recommendation.target_key, system_name, self.TRACK_KEY),
                )
            else:
                next_order = int(
                    self.conn.execute(
                        "SELECT COALESCE(MAX(sort_order),0)+1 FROM sprint_tasks WHERE week=?",
                        (current_week,),
                    ).fetchone()[0]
                )
                cursor = self.conn.execute(
                    "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,0)",
                    (current_week, next_order, label),
                )
                task_id = int(cursor.lastrowid)
                self.conn.execute(
                    """INSERT INTO task_metadata
                       (task_id,status,priority,estimated_minutes,energy,destination,category,prerequisite_state,prerequisite_reason)
                       VALUES(?,'Not Started',2,?,'Normal',?,?,'Ready',NULL)""",
                    (task_id, recommendation.estimated_minutes, self.DESTINATION_INDEX, "Learning"),
                )
                self.conn.execute(
                    """INSERT INTO track_tasks(track_key,task_id,target_key,source_label)
                       VALUES(?,?,?,?)""",
                    (self.TRACK_KEY, task_id, recommendation.target_key, system_name),
                )
            if not adaptive["daily_goal_complete"]:
                self._sync_today_academy_focus(
                    task_id=task_id,
                    recommendation=recommendation,
                    current_week=current_week,
                )
            else:
                # Remove only unfinished auto-generated Academy rows. Completed
                # rows stay frozen with the lesson title the learner actually did.
                self.conn.execute(
                    """DELETE FROM daily_focus
                       WHERE focus_date=? AND completed_at IS NULL AND is_extra=0
                         AND (LOWER(COALESCE(track_key,''))='academy'
                              OR LOWER(COALESCE(source_key,''))='roadmap:academy')""",
                    (date.today().isoformat(),),
                )
            self.conn.commit()
        except (sqlite3.OperationalError, TypeError, IndexError):
            # Standalone engine tests and future editions may not include the legacy planner tables.
            self.conn.rollback()
