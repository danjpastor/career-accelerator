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

        # The learner follows one coherent course sequence.  Finish the current
        # course's lessons, checkpoint, and applied project before moving to the
        # next course or track.
        for path in self.index.catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    for module in course.modules:
                        for lesson in module.lessons:
                            location = self.index.lesson(lesson.lesson_id)
                            unlocked, _missing = self.lesson_unlocked(location)
                            if not unlocked:
                                continue
                            for step_index, activity in enumerate(lesson.activities, start=1):
                                if not activity.required_for_completion:
                                    continue
                                row = self.progress.activity_row(lesson.lesson_id, activity.activity_id)
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
                                            f"academy:activity:{lesson.lesson_id}:{activity.activity_id}"
                                        ),
                                        estimated_minutes=activity.estimated_minutes,
                                        reason=(
                                            f"Continue lesson step {step_index} of "
                                            f"{len(lesson.activities)}."
                                        ),
                                        lesson_id=lesson.lesson_id,
                                        activity_id=activity.activity_id,
                                    )

                    # Assessments are in the same journey and gate the applied
                    # project for this course.
                    for assessment in course.assessments:
                        missing = tuple(
                            skill for skill in assessment.requires if skill not in mastered
                        )
                        if not missing and not self.assessment_passed(assessment.assessment_id):
                            return AcademyRecommendation(
                                kind="assessment",
                                title=assessment.title,
                                target_key=f"academy:assessment:{assessment.assessment_id}",
                                estimated_minutes=assessment.estimated_minutes,
                                reason="Complete the next checkpoint in the learning path.",
                            )

                    all_assessments_passed = all(
                        self.assessment_passed(item.assessment_id)
                        for item in course.assessments
                    )
                    for lab in course.skills_labs:
                        missing = tuple(
                            skill for skill in lab.requires if skill not in mastered
                        )
                        if (
                            all_assessments_passed
                            and not missing
                            and not self.skills_lab_passed(lab.lab_id)
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
