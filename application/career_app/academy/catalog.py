from __future__ import annotations

from dataclasses import dataclass

from .models import CourseDefinition, CurriculumCatalog, LessonDefinition, ModuleDefinition, PathDefinition, TrackDefinition


@dataclass(frozen=True)
class LessonLocation:
    path: PathDefinition
    track: TrackDefinition
    course: CourseDefinition
    module: ModuleDefinition
    lesson: LessonDefinition


class CatalogIndex:
    def __init__(self, catalog: CurriculumCatalog):
        self.catalog = catalog
        self._lessons: dict[str, LessonLocation] = {}
        for path in catalog.program.paths:
            for track in path.tracks:
                for course in track.courses:
                    for module in course.modules:
                        for lesson in module.lessons:
                            self._lessons[lesson.lesson_id] = LessonLocation(path, track, course, module, lesson)

    def lesson(self, lesson_id: str) -> LessonLocation:
        try:
            return self._lessons[lesson_id]
        except KeyError as exc:
            raise KeyError(f"Unknown lesson: {lesson_id}") from exc

    def ordered_lessons(self) -> tuple[LessonLocation, ...]:
        return tuple(self._lessons.values())
