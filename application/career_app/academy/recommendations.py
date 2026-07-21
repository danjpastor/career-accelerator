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


    def is_complete(self) -> bool:
        """Return True only when every required journey node has passed.

        A missing recommendation is not itself proof of completion: it can also
        indicate a broken prerequisite chain. This explicit check prevents the UI
        and planner from announcing a finished pathway while unfinished work remains.
        """

        activity_rows = self.progress.activity_rows()
        for location in self.index.ordered_lessons():
            for activity in location.lesson.activities:
                if not activity.required_for_completion:
                    continue
                row = activity_rows.get(
                    (location.lesson.lesson_id, activity.activity_id)
                )
                if row is None or row["state"] != "Passed":
                    return False
                if (
                    activity.required_for_mastery
                    and bool(row["last_attempt_solution_assisted"])
                ):
                    return False

        for course in self.index.catalog.courses():
            for assessment in course.assessments:
                if not self.assessment_passed(assessment.assessment_id):
                    return False
            for lab in course.skills_labs:
                if not self.skills_lab_passed(lab.lab_id):
                    return False
        return True

    def _lesson_step_recommendation(
        self,
        location: LessonLocation,
        activity: ActivityDefinition,
        step_index: int,
        *,
        reason: str | None = None,
    ) -> AcademyRecommendation:
        return AcademyRecommendation(
            kind="lesson_step",
            title=f"{location.lesson.title} — {activity.title}",
            target_key=(
                f"academy:activity:{location.lesson.lesson_id}:"
                f"{activity.activity_id}"
            ),
            estimated_minutes=activity.estimated_minutes,
            reason=(
                reason
                or f"Continue lesson step {step_index} of "
                f"{len(location.lesson.activities)}."
            ),
            lesson_id=location.lesson.lesson_id,
            activity_id=activity.activity_id,
        )

    def _prerequisite_recommendation(
        self,
        missing_skills: tuple[str, ...],
        activity_rows: dict[tuple[str, str], object],
    ) -> AcademyRecommendation | None:
        """Return unfinished work that teaches a missing prerequisite."""

        for missing_skill in missing_skills:
            for producer in self.index.ordered_lessons():
                if missing_skill not in producer.lesson.teaches:
                    continue
                for step_index, activity in enumerate(
                    producer.lesson.activities, start=1
                ):
                    if not activity.required_for_completion:
                        continue
                    row = activity_rows.get(
                        (producer.lesson.lesson_id, activity.activity_id)
                    )
                    complete = bool(row and row["state"] == "Passed") and not (
                        activity.required_for_mastery
                        and bool(row["last_attempt_solution_assisted"])
                    )
                    if not complete:
                        return self._lesson_step_recommendation(
                            producer,
                            activity,
                            step_index,
                            reason=(
                                f"Finish this lesson to unlock the next skill: "
                                f"{missing_skill}."
                            ),
                        )
        return None

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
                                prerequisite = self._prerequisite_recommendation(
                                    missing_lesson, activity_rows
                                )
                                if prerequisite is not None:
                                    return prerequisite
                                # Do not skip ahead to a later lesson when the
                                # current sequence has an unresolved prerequisite.
                                first_required = next(
                                    (
                                        item for item in lesson.activities
                                        if item.required_for_completion
                                    ),
                                    lesson.activities[0],
                                )
                                return self._lesson_step_recommendation(
                                    location,
                                    first_required,
                                    1,
                                    reason=(
                                        "This lesson is waiting on prerequisite mastery: "
                                        + ", ".join(missing_lesson)
                                    ),
                                )
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
                                    return self._lesson_step_recommendation(
                                        location, activity, step_index
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
        # ``None`` is reserved for a genuinely finished pathway. If the
        # curriculum is incomplete but no prerequisite-ready node was found, keep
        # the path active and direct the learner to the first unfinished step.
        if not self.is_complete():
            for location in self.index.ordered_lessons():
                for step_index, activity in enumerate(
                    location.lesson.activities, start=1
                ):
                    if not activity.required_for_completion:
                        continue
                    row = activity_rows.get(
                        (location.lesson.lesson_id, activity.activity_id)
                    )
                    complete = bool(row and row["state"] == "Passed") and not (
                        activity.required_for_mastery
                        and bool(row["last_attempt_solution_assisted"])
                    )
                    if complete:
                        continue
                    missing = tuple(
                        skill for skill in location.lesson.requires
                        if skill not in mastered
                    )
                    reason = (
                        "Review the prerequisite path before continuing: "
                        + ", ".join(missing)
                        if missing
                        else f"Continue lesson step {step_index} of "
                        f"{len(location.lesson.activities)}."
                    )
                    return self._lesson_step_recommendation(
                        location, activity, step_index, reason=reason
                    )

            for course in self.index.catalog.courses():
                for assessment in course.assessments:
                    if self.assessment_passed(assessment.assessment_id):
                        continue
                    missing = tuple(
                        skill for skill in assessment.requires
                        if skill not in mastered
                    )
                    prerequisite = self._prerequisite_recommendation(
                        missing, activity_rows
                    )
                    if prerequisite is not None:
                        return prerequisite
                    return AcademyRecommendation(
                        kind="assessment",
                        title=assessment.title,
                        target_key=f"academy:assessment:{assessment.assessment_id}",
                        estimated_minutes=assessment.estimated_minutes,
                        reason=(
                            "Review the prerequisite path before starting this checkpoint: "
                            + ", ".join(missing)
                            if missing
                            else "Complete the next checkpoint in the learning path."
                        ),
                    )

                for lab in course.skills_labs:
                    if self.skills_lab_passed(lab.lab_id):
                        continue
                    missing = tuple(
                        skill for skill in lab.requires
                        if skill not in mastered
                    )
                    prerequisite = self._prerequisite_recommendation(
                        missing, activity_rows
                    )
                    if prerequisite is not None:
                        return prerequisite
                    return AcademyRecommendation(
                        kind="skills_lab",
                        title=lab.title,
                        target_key=f"academy:skills_lab:{lab.lab_id}",
                        estimated_minutes=lab.estimated_minutes,
                        reason=(
                            "Review the prerequisite path before starting this project: "
                            + ", ".join(missing)
                            if missing
                            else "Complete the next applied project in the learning path."
                        ),
                    )
        return None
