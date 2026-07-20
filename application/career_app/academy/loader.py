from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from .models import (
    ActivityDefinition,
    ActivityType,
    AssessmentDefinition,
    CourseDefinition,
    CurriculumCatalog,
    DatasetDefinition,
    DatasetTable,
    LessonDefinition,
    ModuleDefinition,
    PathDefinition,
    ProgramDefinition,
    SkillsLabDefinition,
    TrackDefinition,
)


_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class CurriculumError(ValueError):
    pass


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CurriculumError(f"Missing curriculum file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CurriculumError(f"Expected a mapping in {path}")
    return data


def _safe_ref(base: Path, reference: str) -> Path:
    if not isinstance(reference, str) or not reference.strip():
        raise CurriculumError(f"Invalid empty curriculum reference under {base}")
    candidate = (base / reference).resolve()
    root = base.resolve()
    for parent in (base, *base.parents):
        if (parent / "program.yaml").is_file():
            root = parent.resolve()
            break
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CurriculumError(f"Curriculum reference escapes its package: {reference}") from exc
    return candidate


def _id(value: Any, field: str, source: Path) -> str:
    text = str(value or "").strip()
    if not _ID.fullmatch(text):
        raise CurriculumError(f"Invalid {field} {text!r} in {source}")
    return text


def _tuple_strings(value: Any, field: str, source: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CurriculumError(f"{field} must be a list of strings in {source}")
    return tuple(item.strip() for item in value if item.strip())


def _mapping(value: Any, field: str, source: Path) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise CurriculumError(f"{field} must be a mapping in {source}")
    return dict(value)


def _activity(raw: dict[str, Any], source: Path) -> ActivityDefinition:
    try:
        kind = ActivityType(str(raw["type"]).strip().lower())
    except (KeyError, ValueError) as exc:
        raise CurriculumError(f"Unknown activity type in {source}: {raw.get('type')!r}") from exc
    validator = raw.get("validator") or {}
    if not isinstance(validator, dict):
        raise CurriculumError(f"validator must be a mapping in {source}")
    return ActivityDefinition(
        activity_id=_id(raw.get("activity_id"), "activity_id", source),
        title=str(raw.get("title") or "Untitled activity").strip(),
        activity_type=kind,
        prompt=str(raw.get("prompt") or "").strip(),
        runtime=str(raw.get("runtime") or "sql").strip().lower(),
        starter=str(raw.get("starter") or ""),
        solution=str(raw.get("solution") or ""),
        hints=_tuple_strings(raw.get("hints", []), "hints", source),
        validator=validator,
        evidence_eligible=bool(raw.get("evidence_eligible", False)),
        required_for_practice=bool(raw.get("required_for_practice", kind == ActivityType.GUIDED)),
        required_for_mastery=bool(raw.get("required_for_mastery", kind == ActivityType.MASTERY)),
        difficulty=str(raw.get("difficulty") or "beginner").strip(),
        answer_options=_tuple_strings(raw.get("answer_options", []), "answer_options", source),
        presentation=_mapping(raw.get("presentation"), "presentation", source),
        estimated_minutes=max(1, int(raw.get("estimated_minutes", 5))),
    )


def _lesson(path: Path) -> LessonDefinition:
    raw = _read_yaml(path)
    activities_raw = raw.get("activities")
    if not isinstance(activities_raw, list) or not activities_raw:
        raise CurriculumError(f"Lesson must contain activities: {path}")
    content_ref = str(raw.get("content") or "lesson.md")
    content_path = _safe_ref(path.parent, content_ref)
    if not content_path.is_file():
        raise CurriculumError(f"Missing lesson content: {content_path}")
    return LessonDefinition(
        lesson_id=_id(raw.get("lesson_id"), "lesson_id", path),
        title=str(raw.get("title") or "Untitled lesson").strip(),
        order=int(raw.get("order", 0)),
        difficulty=str(raw.get("difficulty") or "beginner").strip(),
        content_markdown=content_path.read_text(encoding="utf-8"),
        teaches=_tuple_strings(raw.get("teaches", []), "teaches", path),
        requires=_tuple_strings(raw.get("requires", []), "requires", path),
        activities=tuple(_activity(item, path) for item in activities_raw),
        passing_score=float((raw.get("mastery") or {}).get("passing_score", 1.0)),
        description=str(raw.get("description") or "").strip(),
        objectives=_tuple_strings(raw.get("objectives", []), "objectives", path),
        key_takeaways=_tuple_strings(raw.get("key_takeaways", []), "key_takeaways", path),
        estimated_minutes=max(1, int(raw.get("estimated_minutes", 25))),
    )


def _module(path: Path) -> ModuleDefinition:
    raw = _read_yaml(path)
    refs = raw.get("lessons") or []
    return ModuleDefinition(
        module_id=_id(raw.get("module_id"), "module_id", path),
        title=str(raw.get("title") or "Untitled module").strip(),
        order=int(raw.get("order", 0)),
        lessons=tuple(sorted((_lesson(_safe_ref(path.parent, ref)) for ref in refs), key=lambda item: item.order)),
        description=str(raw.get("description") or "").strip(),
    )


def _assessment(path: Path) -> AssessmentDefinition:
    raw = _read_yaml(path)
    activities = raw.get("activities") or []
    return AssessmentDefinition(
        assessment_id=_id(raw.get("assessment_id"), "assessment_id", path),
        title=str(raw.get("title") or "Untitled assessment").strip(),
        order=int(raw.get("order", 0)),
        requires=_tuple_strings(raw.get("requires", []), "requires", path),
        passing_score=float(raw.get("passing_score", 0.8)),
        activities=tuple(_activity(item, path) for item in activities),
        description=str(raw.get("description") or "").strip(),
        instructions=_tuple_strings(raw.get("instructions", []), "instructions", path),
        estimated_minutes=max(1, int(raw.get("estimated_minutes", 20))),
    )


def _lab(path: Path) -> SkillsLabDefinition:
    raw = _read_yaml(path)
    activity_raw = raw.get("activity")
    if not isinstance(activity_raw, dict):
        raise CurriculumError(f"Skills Lab requires one activity in {path}")
    evidence = raw.get("evidence") or {}
    if not isinstance(evidence, dict):
        raise CurriculumError(f"evidence must be a mapping in {path}")
    return SkillsLabDefinition(
        lab_id=_id(raw.get("lab_id"), "lab_id", path),
        title=str(raw.get("title") or "Untitled Skills Lab").strip(),
        order=int(raw.get("order", 0)),
        description=str(raw.get("description") or "").strip(),
        requires=_tuple_strings(raw.get("requires", []), "requires", path),
        teaches=_tuple_strings(raw.get("teaches", []), "teaches", path),
        dataset_id=_id(raw.get("dataset_id"), "dataset_id", path),
        prompt=str(raw.get("prompt") or "").strip(),
        deliverables=_tuple_strings(raw.get("deliverables", []), "deliverables", path),
        activity=_activity(activity_raw, path),
        evidence=evidence,
        brief_markdown=str(raw.get("brief_markdown") or "").strip(),
        acceptance_criteria=_tuple_strings(raw.get("acceptance_criteria", []), "acceptance_criteria", path),
        reflection_questions=_tuple_strings(raw.get("reflection_questions", []), "reflection_questions", path),
        rubric=_mapping(raw.get("rubric"), "rubric", path),
        estimated_minutes=max(1, int(raw.get("estimated_minutes", 45))),
    )


def _course(path: Path) -> CourseDefinition:
    raw = _read_yaml(path)
    modules = tuple(sorted((_module(_safe_ref(path.parent, ref)) for ref in raw.get("modules", [])), key=lambda x: x.order))
    assessments = tuple(sorted((_assessment(_safe_ref(path.parent, ref)) for ref in raw.get("assessments", [])), key=lambda x: x.order))
    labs = tuple(sorted((_lab(_safe_ref(path.parent, ref)) for ref in raw.get("skills_labs", [])), key=lambda x: x.order))
    return CourseDefinition(
        course_id=_id(raw.get("course_id"), "course_id", path),
        title=str(raw.get("title") or "Untitled course").strip(),
        order=int(raw.get("order", 0)),
        description=str(raw.get("description") or "").strip(),
        modules=modules,
        assessments=assessments,
        skills_labs=labs,
        outcomes=_tuple_strings(raw.get("outcomes", []), "outcomes", path),
        estimated_minutes=max(1, int(raw.get("estimated_minutes", 180))),
    )


def _track(path: Path) -> TrackDefinition:
    raw = _read_yaml(path)
    return TrackDefinition(
        track_id=_id(raw.get("track_id"), "track_id", path),
        title=str(raw.get("title") or "Untitled track").strip(),
        order=int(raw.get("order", 0)),
        description=str(raw.get("description") or "").strip(),
        courses=tuple(sorted((_course(_safe_ref(path.parent, ref)) for ref in raw.get("courses", [])), key=lambda x: x.order)),
    )


def _path(path: Path) -> PathDefinition:
    raw = _read_yaml(path)
    return PathDefinition(
        path_id=_id(raw.get("path_id"), "path_id", path),
        title=str(raw.get("title") or "Untitled path").strip(),
        order=int(raw.get("order", 0)),
        description=str(raw.get("description") or "").strip(),
        tracks=tuple(sorted((_track(_safe_ref(path.parent, ref)) for ref in raw.get("tracks", [])), key=lambda x: x.order)),
    )


def _datasets(root: Path) -> dict[str, DatasetDefinition]:
    manifest = _read_yaml(root / "datasets" / "datasets.yaml")
    result: dict[str, DatasetDefinition] = {}
    for raw in manifest.get("datasets", []):
        dataset_id = _id(raw.get("dataset_id"), "dataset_id", root / "datasets" / "datasets.yaml")
        tables: list[DatasetTable] = []
        for table in raw.get("tables", []):
            name = _id(table.get("name"), "table name", root / "datasets" / "datasets.yaml")
            csv_path = _safe_ref(root / "datasets", str(table.get("csv")))
            if not csv_path.is_file():
                raise CurriculumError(f"Missing dataset CSV: {csv_path}")
            tables.append(DatasetTable(name=name, csv_path=csv_path))
        result[dataset_id] = DatasetDefinition(
            dataset_id=dataset_id,
            title=str(raw.get("title") or dataset_id),
            tables=tuple(tables),
        )
    return result


def _hash_files(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise CurriculumError(f"Duplicate {label}: {', '.join(sorted(duplicates))}")


def load_catalog(root: str | Path) -> CurriculumCatalog:
    root_path = Path(root).resolve()
    program_path = root_path / "program.yaml"
    raw = _read_yaml(program_path)
    brand = raw.get("brand") or {}
    learning = raw.get("learning") or {}
    if not isinstance(brand, dict) or not isinstance(learning, dict):
        raise CurriculumError("brand and learning must be mappings")
    program = ProgramDefinition(
        program_id=_id(raw.get("program_id"), "program_id", program_path),
        schema_version=int(raw.get("schema_version", 1)),
        content_version=str(raw.get("content_version") or "0.0.0"),
        brand={str(k): str(v) for k, v in brand.items()},
        learning={str(k): str(v) for k, v in learning.items()},
        paths=tuple(sorted((_path(_safe_ref(root_path, ref)) for ref in raw.get("paths", [])), key=lambda x: x.order)),
    )
    skills_raw = _read_yaml(root_path / "skills.yaml")
    skills = skills_raw.get("skills") or {}
    if not isinstance(skills, dict):
        raise CurriculumError("skills must be a mapping")
    catalog = CurriculumCatalog(
        root=root_path,
        program=program,
        skills=skills,
        datasets=_datasets(root_path),
        content_hash=_hash_files(root_path),
    )
    _unique((lesson.lesson_id for lesson in catalog.lessons()), "lesson IDs")
    _unique((activity.activity_id for lesson in catalog.lessons() for activity in lesson.activities), "activity IDs")
    _unique((item.assessment_id for item in catalog.assessments()), "assessment IDs")
    _unique((item.lab_id for item in catalog.skills_labs()), "Skills Lab IDs")
    known_skills = set(skills)
    referenced = {
        skill
        for lesson in catalog.lessons()
        for skill in (*lesson.teaches, *lesson.requires)
    }
    referenced.update(skill for assessment in catalog.assessments() for skill in assessment.requires)
    referenced.update(skill for lab in catalog.skills_labs() for skill in (*lab.requires, *lab.teaches))
    unknown = referenced - known_skills
    if unknown:
        raise CurriculumError(f"Unknown skill references: {', '.join(sorted(unknown))}")
    for lab in catalog.skills_labs():
        if lab.dataset_id not in catalog.datasets:
            raise CurriculumError(f"Unknown dataset {lab.dataset_id!r} in Skills Lab {lab.lab_id}")
    return catalog
