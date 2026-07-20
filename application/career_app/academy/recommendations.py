from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogIndex, LessonLocation
from .models import ActivityDefinition, ProgressState
from .progress import ProgressRepository


@dataclass(frozen=True)
class AcademyRecommendation:
    kind: str
    title: str
    target_key: str
    estimated_minutes: int
    reason: str
    lesson_id: str | None = None
    activity_id: str | None = None


class RecommendationEngine:
    """Choose the next actionable node in the unified Academy journey.

    Lessons, practice, checkpoints, and projects remain separate domain types,
    but the learner receives one ordered stream of work.  Every lesson activity
    is a required interactive step unless the curriculum explicitly marks it as
    optional.
    """

    def __init__(self, index: CatalogIndex, progress: ProgressRepository):
        self.index = index
        self.progress = progress

    def lesson_unlocked(self, location: LessonLocation) -> tuple[bool, tuple[str, ...]]:
        mastered = self.progress.mastered_skills()
        missing = tuple(skill for skill in location.lesson.requires if skill not in mastered)
        return not missing, missing

    def activity_unlocked(
        self,
        location: LessonLocation,
        activity: ActivityDefinition,
    ) -> tuple[bool, str | None]:
        lesson_ready, missing = self.lesson_unlocked(location)
        if not lesson_ready:
            return False, "Master first: " + ", ".join(missing)
        for earlier in location.lesson.activities:
            if earlier.activity_id == activity.activity_id:
                break
            if not earlier.required_for_completion:
                continue
            row = self.progress.activity_row(location.lesson.lesson_id, earlier.activity_id)
            if row is None or row["state"] != "Passed":
                return False, f"Complete the earlier step: {earlier.title}"
        return True, None

    def assessment_passed(self, assessment_id: str) -> bool:
        return bool(
            self.progress.conn.execute(
                "SELECT 1 FROM academy_assessment_attempts WHERE assessment_id=? AND passed=1 LIMIT 1",
                (assessment_id,),
            ).fetchone()
        )

    def skills_lab_passed(self, lab_id: str) -> bool:
        return bool(
            self.progress.conn.execute(
                """SELECT 1 FROM academy_submissions
                   WHERE item_type='skills_lab' AND item_id=? AND validation_status='Passed' LIMIT 1""",
                (lab_id,),
            ).fetchone()
        )

    def next(self) -> AcademyRecommendation | None:
        mastered = self.progress.mastered_skills()
        activity_rows = self.progress.activity_rows()
        passed_assessments = {
            str(row[0])
            for row in self.progress.conn.execute(
                """SELECT DISTINCT assessment_id
                   FROM academy_assessment_attempts
                   WHERE passed=1"""
            ).fetchall()
        }
        passed_labs = {
            str(row[0])
            for row in self.progress.conn.execute(
                """SELECT DISTINCT item_id
                   FROM academy_submissions
                   WHERE item_type='skills_lab'
                     AND validation_status='Passed'"""
            ).fetchall()
        }

        # Finish each course's lessons, checkpoint, and applied project before
        # moving to the next course or track. All progress is read from the
        # snapshots above, so a large curriculum does not generate one SQLite
        # query per lesson step.
        for path in self.index.catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    for module in course.modules:
                        for lesson in module.lessons:
                            location = self.index.lesson(lesson.lesson_id)
                            missing_lesson = tuple(
                                skill for skill in lesson.requires
                                if skill not in mastered
                            )
                            if missing_lesson:
                                continue
                            for step_index, activity in enumerate(
                                lesson.activities, start=1
                            ):
                                if not activity.required_for_completion:
                                    continue
                                row = activity_rows.get(
                                    (lesson.lesson_id, activity.activity_id)
                                )
                                passed = bool(row and row["state"] == "Passed")
                                mastery_assisted = bool(
                                    passed
                                    and activity.required_for_mastery
                                    and row["last_attempt_solution_assisted"]
                                )
                                if not passed or mastery_assisted:
                                    return AcademyRecommendation(
                                        kind="lesson_step",
                                        title=f"{lesson.title} — {activity.title}",
                                        target_key=(
                                            f"academy:activity:{lesson.lesson_id}:"
                                            f"{activity.activity_id}"
                                        ),
                                        estimated_minutes=activity.estimated_minutes,
                                        reason=(
                                            f"Continue lesson step {step_index} of "
                                            f"{len(lesson.activities)}."
                                        ),
                                        lesson_id=lesson.lesson_id,
                                        activity_id=activity.activity_id,
                                    )

                    for assessment in course.assessments:
                        missing = tuple(
                            skill for skill in assessment.requires
                            if skill not in mastered
                        )
                        if (
                            not missing
                            and assessment.assessment_id not in passed_assessments
                        ):
                            return AcademyRecommendation(
                                kind="assessment",
                                title=assessment.title,
                                target_key=(
                                    f"academy:assessment:{assessment.assessment_id}"
                                ),
                                estimated_minutes=assessment.estimated_minutes,
                                reason=(
                                    "Complete the next checkpoint in the learning path."
                                ),
                            )

                    all_assessments_passed = all(
                        item.assessment_id in passed_assessments
                        for item in course.assessments
                    )
                    for lab in course.skills_labs:
                        missing = tuple(
                            skill for skill in lab.requires
                            if skill not in mastered
                        )
                        if (
                            all_assessments_passed
                            and not missing
                            and lab.lab_id not in passed_labs
                        ):
                            return AcademyRecommendation(
                                kind="skills_lab",
                                title=lab.title,
                                target_key=f"academy:skills_lab:{lab.lab_id}",
                                estimated_minutes=lab.estimated_minutes,
                                reason=(
                                    "Apply the completed course in an "
                                    "evidence-producing project."
                                ),
                            )
        return None
