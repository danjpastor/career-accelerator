from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
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
        self.progress = ProgressRepository(conn, self.catalog.program.content_version)
        self.recommendations = RecommendationEngine(self.index, self.progress)
        self._register_package()
        self._seed_progress()
        self.sync_planner_task()

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

    def open_lesson(self, lesson_id: str):
        return self.progress.open_lesson(lesson_id)

    def activity_progress(self, lesson_id: str, activity_id: str):
        return self.progress.activity_row(lesson_id, activity_id)

    def lesson_unlocked(self, lesson_id: str) -> tuple[bool, tuple[str, ...]]:
        return self.recommendations.lesson_unlocked(self.index.lesson(lesson_id))

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
        if result.passed:
            self._record_activity_evidence(lesson, activity)
            if state.value == "Mastered":
                self._record_lesson_mastery(lesson)
        self.sync_planner_task()
        return result

    def run_activity(self, activity: ActivityDefinition, answer: str) -> ValidationResult:
        if activity.runtime != "sql":
            return ValidationResult(False, "Run Query is available for SQL activities.")
        dataset_id = str(activity.validator.get("dataset_id") or "sql_foundations")
        return SqlValidator(self.catalog.datasets[dataset_id]).execute(answer)

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
        return {"passed": passed, "score": score, "results": results}


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
        missing = self._missing_skills(lab.requires)
        if missing:
            return ValidationResult(False, "Prerequisites not yet mastered: " + ", ".join(missing))
        validator = SqlValidator(self.catalog.datasets[lab.dataset_id])
        result = validator.validate(sql, dict(lab.activity.validator))
        if result.passed and len([line for line in notes.splitlines() if line.strip()]) < 3:
            result = ValidationResult(
                False,
                "The SQL is correct. Add at least three concise findings before submitting the Skills Lab.",
                result.columns,
                result.rows,
                result.details,
            )
        artifact_path = self._save_submission("skills_lab", lab.lab_id, lab.title, sql, notes, result)
        if result.passed:
            for skill in lab.teaches:
                self._insert_evidence(
                    skill=skill,
                    source_type="Skills Lab",
                    source_id=lab.lab_id,
                    source_name=lab.title,
                    course_id=self.catalog.courses()[0].course_id,
                    learning_item_id=lab.lab_id,
                    difficulty=lab.activity.difficulty,
                    dataset=lab.dataset_id,
                    submission_path=str(artifact_path.relative_to(self.repository_root)),
                    job_competency=str(lab.evidence.get("job_competency") or "Applied analysis"),
                    notes=notes,
                    metadata={"validation": result.as_dict(), "deliverables": list(lab.deliverables)},
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

    def _record_activity_evidence(self, lesson: LessonDefinition, activity: ActivityDefinition) -> None:
        if not activity.evidence_eligible:
            return
        row = self.progress.activity_row(lesson.lesson_id, activity.activity_id)
        if row is None or row["solution_viewed_at"] or row["last_attempt_solution_assisted"]:
            return
        location = self.index.lesson(lesson.lesson_id)
        for skill in lesson.teaches:
            self._insert_evidence(
                skill=skill,
                source_type="Academy Practice",
                source_id=activity.activity_id,
                source_name=f"{lesson.title} — {activity.title}",
                course_id=location.course.course_id,
                learning_item_id=activity.activity_id,
                difficulty=activity.difficulty,
                dataset=str(activity.validator.get("dataset_id") or ""),
                submission_path=None,
                job_competency="Independent SQL problem solving",
                notes="Validated independent work completed without viewing the full solution.",
                metadata={"lesson_id": lesson.lesson_id, "activity_type": activity.activity_type.value},
            )

    def _record_lesson_mastery(self, lesson: LessonDefinition) -> None:
        location = self.index.lesson(lesson.lesson_id)
        for skill in lesson.teaches:
            self._insert_evidence(
                skill=skill,
                source_type="Academy Mastery",
                source_id=lesson.lesson_id,
                source_name=lesson.title,
                course_id=location.course.course_id,
                learning_item_id=lesson.lesson_id,
                difficulty=lesson.difficulty,
                dataset=None,
                submission_path=None,
                job_competency="Foundation query construction",
                notes="Lesson mastery requirements passed without solution assistance.",
                metadata={"state": "Mastered"},
            )

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
        # Project rich Academy evidence into the application's existing evidence surface.
        try:
            display = str(self.catalog.skills.get(skill, {}).get("title") or skill)
            self.conn.execute(
                """INSERT INTO evidence(skill,source_type,source_name,description)
                   VALUES(?,?,?,?)
                   ON CONFLICT(skill,source_type,source_name) DO UPDATE SET description=excluded.description""",
                (display, source_type, source_name, notes),
            )
        except sqlite3.OperationalError:
            pass
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

    def sync_planner_task(self) -> None:
        """Expose the next prerequisite-ready Academy action to the existing planner."""
        recommendation = self.next_recommendation()
        try:
            current_week = int(
                self.conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone()[0]
            )
            system_name = self.labels.get("system_name", "Learning System")
            self.conn.execute(
                """INSERT INTO track_state(track_key,display_name,position,subposition,weekly_target,status,metadata)
                   VALUES(?,?,0,0,2,'Active',?)
                   ON CONFLICT(track_key) DO UPDATE SET
                       display_name=excluded.display_name,
                       weekly_target=excluded.weekly_target,
                       status='Active',
                       metadata=excluded.metadata,
                       updated_at=CURRENT_TIMESTAMP""",
                (self.TRACK_KEY, system_name, json.dumps({"provider": "internal", "program_id": self.catalog.program.program_id})),
            )
            if recommendation is None:
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
            existing = self.conn.execute(
                "SELECT task_id FROM track_tasks WHERE track_key=?", (self.TRACK_KEY,)
            ).fetchone()
            label = f"[{system_name}] {recommendation.title}"
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
                    (recommendation.estimated_minutes, self.DESTINATION_INDEX, system_name, task_id),
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
                    (task_id, recommendation.estimated_minutes, self.DESTINATION_INDEX, system_name),
                )
                self.conn.execute(
                    """INSERT INTO track_tasks(track_key,task_id,target_key,source_label)
                       VALUES(?,?,?,?)""",
                    (self.TRACK_KEY, task_id, recommendation.target_key, system_name),
                )
            self.conn.commit()
        except (sqlite3.OperationalError, TypeError, IndexError):
            # Standalone engine tests and future editions may not include the legacy planner tables.
            self.conn.rollback()
