from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class ProgressState(str, Enum):
    NOT_STARTED = "Not Started"
    LEARNING = "Learning"
    PRACTICED = "Practiced"
    MASTERED = "Mastered"

    @property
    def rank(self) -> int:
        return {
            ProgressState.NOT_STARTED: 0,
            ProgressState.LEARNING: 1,
            ProgressState.PRACTICED: 2,
            ProgressState.MASTERED: 3,
        }[self]


class ActivityType(str, Enum):
    RECOGNITION = "recognition"
    GUIDED = "guided"
    INDEPENDENT = "independent"
    DEBUGGING = "debugging"
    TRANSFER = "transfer"
    MASTERY = "mastery"


@dataclass(frozen=True)
class ActivityDefinition:
    activity_id: str
    title: str
    activity_type: ActivityType
    prompt: str
    runtime: str = "sql"
    starter: str = ""
    solution: str = ""
    hints: tuple[str, ...] = ()
    validator: Mapping[str, Any] = field(default_factory=dict)
    evidence_eligible: bool = False
    required_for_practice: bool = False
    required_for_mastery: bool = False
    difficulty: str = "beginner"
    answer_options: tuple[str, ...] = ()
    presentation: Mapping[str, Any] = field(default_factory=dict)
    estimated_minutes: int = 5


@dataclass(frozen=True)
class LessonDefinition:
    lesson_id: str
    title: str
    order: int
    difficulty: str
    content_markdown: str
    teaches: tuple[str, ...]
    requires: tuple[str, ...]
    activities: tuple[ActivityDefinition, ...]
    passing_score: float = 1.0
    description: str = ""
    objectives: tuple[str, ...] = ()
    key_takeaways: tuple[str, ...] = ()
    estimated_minutes: int = 25


@dataclass(frozen=True)
class ModuleDefinition:
    module_id: str
    title: str
    order: int
    lessons: tuple[LessonDefinition, ...]
    description: str = ""


@dataclass(frozen=True)
class AssessmentDefinition:
    assessment_id: str
    title: str
    order: int
    requires: tuple[str, ...]
    passing_score: float
    activities: tuple[ActivityDefinition, ...]
    description: str = ""
    instructions: tuple[str, ...] = ()
    estimated_minutes: int = 20


@dataclass(frozen=True)
class SkillsLabDefinition:
    lab_id: str
    title: str
    order: int
    description: str
    requires: tuple[str, ...]
    teaches: tuple[str, ...]
    dataset_id: str
    prompt: str
    deliverables: tuple[str, ...]
    activity: ActivityDefinition
    evidence: Mapping[str, Any] = field(default_factory=dict)
    brief_markdown: str = ""
    acceptance_criteria: tuple[str, ...] = ()
    reflection_questions: tuple[str, ...] = ()
    rubric: Mapping[str, Any] = field(default_factory=dict)
    estimated_minutes: int = 45


@dataclass(frozen=True)
class CourseDefinition:
    course_id: str
    title: str
    order: int
    description: str
    modules: tuple[ModuleDefinition, ...]
    assessments: tuple[AssessmentDefinition, ...] = ()
    skills_labs: tuple[SkillsLabDefinition, ...] = ()
    outcomes: tuple[str, ...] = ()
    estimated_minutes: int = 180


@dataclass(frozen=True)
class TrackDefinition:
    track_id: str
    title: str
    order: int
    description: str
    courses: tuple[CourseDefinition, ...]


@dataclass(frozen=True)
class PathDefinition:
    path_id: str
    title: str
    order: int
    description: str
    tracks: tuple[TrackDefinition, ...]


@dataclass(frozen=True)
class ProgramDefinition:
    program_id: str
    schema_version: int
    content_version: str
    brand: Mapping[str, str]
    learning: Mapping[str, str]
    paths: tuple[PathDefinition, ...]


@dataclass(frozen=True)
class DatasetTable:
    name: str
    csv_path: Path


@dataclass(frozen=True)
class DatasetDefinition:
    dataset_id: str
    title: str
    tables: tuple[DatasetTable, ...]


@dataclass(frozen=True)
class CurriculumCatalog:
    root: Path
    program: ProgramDefinition
    skills: Mapping[str, Mapping[str, Any]]
    datasets: Mapping[str, DatasetDefinition]
    content_hash: str

    def lessons(self) -> tuple[LessonDefinition, ...]:
        return tuple(
            lesson
            for path in self.program.paths
            for track in path.tracks
            for course in track.courses
            for module in course.modules
            for lesson in module.lessons
        )

    def courses(self) -> tuple[CourseDefinition, ...]:
        return tuple(
            course
            for path in self.program.paths
            for track in path.tracks
            for course in track.courses
        )

    def assessments(self) -> tuple[AssessmentDefinition, ...]:
        return tuple(item for course in self.courses() for item in course.assessments)

    def skills_labs(self) -> tuple[SkillsLabDefinition, ...]:
        return tuple(item for course in self.courses() for item in course.skills_labs)

    def lesson(self, lesson_id: str) -> LessonDefinition:
        for lesson in self.lessons():
            if lesson.lesson_id == lesson_id:
                return lesson
        raise KeyError(f"Unknown lesson: {lesson_id}")

    def assessment(self, assessment_id: str) -> AssessmentDefinition:
        for assessment in self.assessments():
            if assessment.assessment_id == assessment_id:
                return assessment
        raise KeyError(f"Unknown assessment: {assessment_id}")

    def skills_lab(self, lab_id: str) -> SkillsLabDefinition:
        for lab in self.skills_labs():
            if lab.lab_id == lab_id:
                return lab
        raise KeyError(f"Unknown Skills Lab: {lab_id}")
