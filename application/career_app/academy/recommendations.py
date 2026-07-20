from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogIndex, LessonLocation
from .models import ActivityDefinition, ActivityType, ProgressState
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
    def __init__(self, index: CatalogIndex, progress: ProgressRepository):
        self.index = index
        self.progress = progress

    def lesson_unlocked(self, location: LessonLocation) -> tuple[bool, tuple[str, ...]]:
        mastered = self.progress.mastered_skills()
        missing = tuple(skill for skill in location.lesson.requires if skill not in mastered)
        return not missing, missing

    def next(self) -> AcademyRecommendation | None:
        for location in self.index.ordered_lessons():
            unlocked, missing = self.lesson_unlocked(location)
            if not unlocked:
                continue
            state = self.progress.lesson_state(location.lesson.lesson_id)
            if state == ProgressState.NOT_STARTED:
                return AcademyRecommendation(
                    kind="instruction",
                    title=f"Learn: {location.lesson.title}",
                    target_key=f"academy:lesson:{location.lesson.lesson_id}",
                    estimated_minutes=location.lesson.estimated_minutes,
                    reason="This is the next prerequisite-ready lesson.",
                    lesson_id=location.lesson.lesson_id,
                )
            if state == ProgressState.LEARNING:
                activity = self._first_unpassed(location.lesson.activities, practice=True)
                if activity:
                    return self._activity_recommendation(location, activity, "Complete guided practice")
            if state == ProgressState.PRACTICED:
                activity = self._first_unpassed(location.lesson.activities, mastery=True)
                if activity:
                    return self._activity_recommendation(location, activity, "Demonstrate independent mastery")
        for course in self.index.catalog.courses():
            for assessment in course.assessments:
                passed = self.progress.conn.execute(
                    "SELECT 1 FROM academy_assessment_attempts WHERE assessment_id=? AND passed=1 LIMIT 1",
                    (assessment.assessment_id,),
                ).fetchone()
                missing = tuple(skill for skill in assessment.requires if skill not in self.progress.mastered_skills())
                if not passed and not missing:
                    return AcademyRecommendation(
                        kind="assessment",
                        title=assessment.title,
                        target_key=f"academy:assessment:{assessment.assessment_id}",
                        estimated_minutes=assessment.estimated_minutes,
                        reason="The course checkpoint consolidates the completed foundation lessons.",
                    )
            for lab in course.skills_labs:
                passed = self.progress.conn.execute(
                    "SELECT 1 FROM academy_submissions WHERE item_type='skills_lab' AND item_id=? AND validation_status='Passed' LIMIT 1",
                    (lab.lab_id,),
                ).fetchone()
                missing = tuple(skill for skill in lab.requires if skill not in self.progress.mastered_skills())
                if not passed and not missing:
                    return AcademyRecommendation(
                        kind="skills_lab",
                        title=lab.title,
                        target_key=f"academy:skills_lab:{lab.lab_id}",
                        estimated_minutes=lab.estimated_minutes,
                        reason="Apply the mastered foundation skills to an evidence-producing assignment.",
                    )
        return None

    def _first_unpassed(
        self,
        activities: tuple[ActivityDefinition, ...],
        *,
        practice: bool = False,
        mastery: bool = False,
    ) -> ActivityDefinition | None:
        candidates = [
            item for item in activities
            if (practice and item.required_for_practice) or (mastery and item.required_for_mastery)
        ]
        for item in candidates:
            for location in self.index.ordered_lessons():
                if item in location.lesson.activities:
                    row = self.progress.activity_row(location.lesson.lesson_id, item.activity_id)
                    if row is None or row["state"] != "Passed" or (mastery and row["last_attempt_solution_assisted"]):
                        return item
        return None

    @staticmethod
    def _activity_recommendation(
        location: LessonLocation,
        activity: ActivityDefinition,
        reason: str,
    ) -> AcademyRecommendation:
        minutes = activity.estimated_minutes
        return AcademyRecommendation(
            kind="practice",
            title=f"{location.lesson.title}: {activity.title}",
            target_key=f"academy:activity:{location.lesson.lesson_id}:{activity.activity_id}",
            estimated_minutes=minutes,
            reason=reason,
            lesson_id=location.lesson.lesson_id,
            activity_id=activity.activity_id,
        )
