from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogIndex, LessonLocation
from .models import ActivityDefinition, ProgressState
from .progress import ProgressRepository
from career_app.services import weekly_mastery


TRACK_GATE_ASSESSMENTS = {
    "sql_analyst": (
        "week_2_spreadsheet_mastery",
        "Week 2 Knowledge Check",
    ),
    "power_bi_analyst": (
        "week_6_sql_mastery",
        "Week 6 Knowledge Check",
    ),
    "python_analyst": (
        "week_7_power_bi_mastery",
        "Week 7 Knowledge Check",
    ),
    "program_mastery": (
        "week_8_portfolio_readiness",
        "Week 8 Knowledge Check",
    ),
}


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

    def track_unlocked(self, track_id: str) -> tuple[bool, tuple[str, ...]]:
        gate = TRACK_GATE_ASSESSMENTS.get(str(track_id))
        if gate is None:
            return True, ()
        assessment_id, title = gate
        if self.assessment_passed(assessment_id):
            return True, ()
        return False, (f"checkpoint:{title}",)

    def _activity_already_passed(
        self,
        lesson_id: str,
        activity_id: str,
    ) -> bool:
        row = self.progress.activity_row(lesson_id, activity_id)
        return bool(row and row["state"] == "Passed")

    def _lesson_already_completed(self, location: LessonLocation) -> bool:
        required = tuple(
            item for item in location.lesson.activities
            if item.required_for_completion
        )
        return bool(required) and all(
            self._activity_already_passed(location.lesson.lesson_id, item.activity_id)
            for item in required
        )

    def lesson_unlocked(self, location: LessonLocation) -> tuple[bool, tuple[str, ...]]:
        # Preserve access to lessons the learner already completed before the
        # roadmap migration, while preventing unfinished later-track work from
        # bypassing the new mastery gates.
        if self._lesson_already_completed(location):
            return True, ()
        track_ready, track_missing = self.track_unlocked(location.track.track_id)
        if not track_ready:
            return False, track_missing
        mastered = self.progress.mastered_skills()
        missing = tuple(skill for skill in location.lesson.requires if skill not in mastered)
        return not missing, missing

    def activity_unlocked(
        self,
        location: LessonLocation,
        activity: ActivityDefinition,
    ) -> tuple[bool, str | None]:
        # Previously passed steps remain reviewable after the migration. New or
        # unfinished steps obey both the track gate and the lesson prerequisites.
        if self._activity_already_passed(location.lesson.lesson_id, activity.activity_id):
            return True, None
        lesson_ready, missing = self.lesson_unlocked(location)
        if not lesson_ready:
            readable = [
                item.split(":", 1)[1] if item.startswith("checkpoint:") else item
                for item in missing
            ]
            return False, "Master first: " + ", ".join(readable)
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

    def _track_for_assessment(self, assessment_id: str):
        for path in self.index.catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    if any(
                        item.assessment_id == assessment_id
                        for item in course.assessments
                    ):
                        return track
        return None

    def _track_for_lab(self, lab_id: str):
        for path in self.index.catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    if any(item.lab_id == lab_id for item in course.skills_labs):
                        return track
        return None

    def assessment_unlocked(self, assessment_id: str) -> tuple[bool, tuple[str, ...]]:
        track = self._track_for_assessment(str(assessment_id))
        if track is None:
            return False, ("Academy assessment",)
        track_ready, track_missing = self.track_unlocked(track.track_id)
        weekly = weekly_mastery.knowledge_check_readiness(
            self.progress.conn, str(assessment_id)
        )
        missing = list(track_missing if not track_ready else ())
        if not weekly.ready:
            missing.extend(weekly.missing)
        return not missing, tuple(dict.fromkeys(missing))

    def skills_lab_unlocked(self, lab_id: str) -> tuple[bool, tuple[str, ...]]:
        track = self._track_for_lab(str(lab_id))
        if track is None:
            return False, ("Academy Skills Lab",)
        return self.track_unlocked(track.track_id)


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
                track_ready, _track_missing = self.track_unlocked(track.track_id)
                if not track_ready:
                    # The checkpoint that unlocks this track lives in an earlier
                    # track and is returned there. Never skip into unfinished SQL,
                    # Power BI, or Python content through the fallback traversal.
                    continue
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
                        if assessment.assessment_id in passed_assessments:
                            continue
                        missing = tuple(
                            skill for skill in assessment.requires
                            if skill not in mastered
                        )
                        gate_ready, _gate_missing = self.assessment_unlocked(
                            assessment.assessment_id
                        )
                        if missing:
                            prerequisite = self._prerequisite_recommendation(
                                missing, activity_rows
                            )
                            if prerequisite is not None:
                                return prerequisite
                            return None
                        if not gate_ready:
                            # A weekly check stays out of the task queue until
                            # the week's required and catch-up work is complete.
                            # Do not skip into a later course while it is locked.
                            return None
                        return AcademyRecommendation(
                            kind="assessment",
                            title=assessment.title,
                            target_key=(
                                f"academy:assessment:{assessment.assessment_id}"
                            ),
                            estimated_minutes=assessment.estimated_minutes,
                            reason=(
                                "Complete the next knowledge check in the learning path."
                            ),
                        )

                    for lab in course.skills_labs:
                        if lab.lab_id in passed_labs:
                            continue
                        missing = tuple(
                            skill for skill in lab.requires
                            if skill not in mastered
                        )
                        gate_ready, _gate_missing = self.skills_lab_unlocked(lab.lab_id)
                        if missing or not gate_ready:
                            return None
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
                track_ready, _track_missing = self.track_unlocked(location.track.track_id)
                if not track_ready:
                    continue
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

            for path in self.index.catalog.program.paths:
                for track in path.tracks:
                    track_ready, _track_missing = self.track_unlocked(track.track_id)
                    if not track_ready:
                        continue
                    for course in track.courses:
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
