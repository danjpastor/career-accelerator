from __future__ import annotations

"""Release audit for the v10.35 program, curriculum, and planner contract.

Run from any directory:
    python application/scripts/audit_program_integrity.py <repository-root>

The script is intentionally dependency-light so the patch installer can run it
before the Career Accelerator virtual environment exists. It validates YAML,
Markdown, JSON, source contracts, prerequisite ordering, and retired paths.
"""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

EXPECTED_COUNTS = {
    "paths": 1,
    "tracks": 5,
    "courses": 18,
    "modules": 33,
    "lessons": 63,
    "assessments": 19,
    "skills_labs": 2,
    "activities": 573,
    "applied_labs": 36,
    "weekly_knowledge_checks": 12,
}
EXTERNAL_PREREQUISITES = {
    "roadmap.spreadsheet_mastery",
    "roadmap.sql_mastery",
    "roadmap.power_bi_mastery",
    "roadmap.portfolio_readiness",
}
RETIRED_ACTIVE_PHRASES = (
    "Rows, Columns, Tables & Data Types",
    "SQL Companion",
    "Next Sprint Adjustment 1",
    "Next Sprint Adjustment 2",
    "Confidence Reason",
    "Optional Practice",
)
RETIRED_PATHS = (
    "academy_workspace/spreadsheets/current-lesson-instructions.html",
    "application/career_app/ui/google_sheets_academy.py",
    "exercise_packs",
)
GUIDE_HEADINGS = (
    "## Scenario",
    "## Your assignment",
    "## Start here",
    "## Provided files",
    "## What you must produce",
    "## Guided workflow",
    "## Evidence to record",
    "## Definition of done",
    "## Common mistakes to avoid",
    "## Submission workflow",
    "## Interview-ready reflection",
)
CHECK_IDS = {
    1: "week_1_spreadsheet_foundations_check",
    2: "week_2_spreadsheet_mastery",
    3: "week_3_sql_foundations",
    4: "week_4_relationships_joins",
    5: "week_5_cleaning_ctes",
    6: "week_6_sql_mastery",
    7: "week_7_power_bi_mastery",
    8: "week_8_portfolio_readiness",
    9: "week_9_project_analysis_check",
    10: "week_10_reporting_publication_check",
    11: "week_11_portfolio_execution_check",
    12: "week_12_career_launch_check",
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover - installer diagnostic
        raise ValueError(f"Could not read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def resolve(base: Path, reference: str, root: Path, issues: list[str]) -> Path:
    candidate = (base / str(reference)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        issues.append(f"Reference escapes curriculum root: {reference}")
    if not candidate.is_file():
        issues.append(f"Missing referenced file: {candidate}")
    return candidate


def audit_curriculum(root: Path, issues: list[str]) -> tuple[dict[str, int], dict[str, dict]]:
    curriculum = root / "curriculum" / "data"
    program_path = curriculum / "program.yaml"
    program = load_yaml(program_path)
    counts = {key: 0 for key in EXPECTED_COUNTS if key not in {"applied_labs", "weekly_knowledge_checks"}}
    seen_ids: set[tuple[str, str]] = set()
    mastered = set(EXTERNAL_PREREQUISITES)
    assessments: dict[str, dict] = {}

    def unique(kind: str, value: str, source: Path) -> None:
        key = (kind, value)
        if not value:
            issues.append(f"Missing {kind} identifier in {source}")
        elif key in seen_ids:
            issues.append(f"Duplicate {kind} identifier {value} in {source}")
        seen_ids.add(key)

    for path_ref in program.get("paths") or []:
        path_file = resolve(curriculum, path_ref, curriculum, issues)
        path_data = load_yaml(path_file)
        counts["paths"] += 1
        unique("path", str(path_data.get("path_id") or ""), path_file)
        for track_ref in path_data.get("tracks") or []:
            track_file = resolve(path_file.parent, track_ref, curriculum, issues)
            track_data = load_yaml(track_file)
            counts["tracks"] += 1
            unique("track", str(track_data.get("track_id") or ""), track_file)
            for course_ref in track_data.get("courses") or []:
                course_file = resolve(track_file.parent, course_ref, curriculum, issues)
                course_data = load_yaml(course_file)
                counts["courses"] += 1
                unique("course", str(course_data.get("course_id") or ""), course_file)
                roadmap_week = course_data.get("roadmap_week")
                if not isinstance(roadmap_week, int) or not 1 <= roadmap_week <= 12:
                    issues.append(
                        f"Course {course_data.get('course_id')} has no valid roadmap_week in {course_file}"
                    )
                for module_ref in course_data.get("modules") or []:
                    module_file = resolve(course_file.parent, module_ref, curriculum, issues)
                    module_data = load_yaml(module_file)
                    counts["modules"] += 1
                    unique("module", str(module_data.get("module_id") or ""), module_file)
                    for lesson_ref in module_data.get("lessons") or []:
                        lesson_file = resolve(module_file.parent, lesson_ref, curriculum, issues)
                        lesson = load_yaml(lesson_file)
                        lesson_id = str(lesson.get("lesson_id") or "")
                        counts["lessons"] += 1
                        unique("lesson", lesson_id, lesson_file)
                        missing = [skill for skill in lesson.get("requires") or [] if skill not in mastered]
                        if missing:
                            issues.append(f"{lesson_id} requires unavailable or forward skills: {missing}")
                        activities = lesson.get("activities") or []
                        counts["activities"] += len(activities)
                        if not activities:
                            issues.append(f"{lesson_id} has no lesson activities")
                        activity_ids = [str(item.get("activity_id") or "") for item in activities]
                        if len(set(activity_ids)) != len(activity_ids):
                            issues.append(f"{lesson_id} contains duplicate activity IDs")
                        for index, activity in enumerate(activities):
                            if not str(activity.get("activity_id") or "").strip():
                                issues.append(f"{lesson_id} activity {index + 1} has no ID")
                            if index and not any(
                                bool(item.get("required_for_completion", True))
                                for item in activities[:index]
                            ):
                                issues.append(f"{lesson_id} activity {index + 1} has no required earlier step")
                        content_ref = str(lesson.get("content") or "lesson.md")
                        resolve(lesson_file.parent, content_ref, curriculum, issues)
                        mastered.update(str(skill) for skill in lesson.get("teaches") or [])

                for assessment_ref in course_data.get("assessments") or []:
                    assessment_file = resolve(course_file.parent, assessment_ref, curriculum, issues)
                    assessment = load_yaml(assessment_file)
                    assessment_id = str(assessment.get("assessment_id") or "")
                    counts["assessments"] += 1
                    unique("assessment", assessment_id, assessment_file)
                    if not assessment.get("requires"):
                        issues.append(f"{assessment_id} has no explicit prerequisites")
                    missing = [skill for skill in assessment.get("requires") or [] if skill not in mastered]
                    if missing:
                        issues.append(f"{assessment_id} requires unavailable or forward skills: {missing}")
                    counts["activities"] += len(assessment.get("activities") or [])
                    assessments[assessment_id] = assessment

                for lab_ref in course_data.get("skills_labs") or []:
                    lab_file = resolve(course_file.parent, lab_ref, curriculum, issues)
                    lab = load_yaml(lab_file)
                    lab_id = str(lab.get("lab_id") or "")
                    counts["skills_labs"] += 1
                    counts["activities"] += 1
                    unique("skills_lab", lab_id, lab_file)
                    if not lab.get("requires"):
                        issues.append(f"{lab_id} has no explicit prerequisites")
                    missing = [skill for skill in lab.get("requires") or [] if skill not in mastered]
                    if missing:
                        issues.append(f"{lab_id} requires unavailable or forward skills: {missing}")
                    mastered.update(str(skill) for skill in lab.get("teaches") or [])

    for key, expected in EXPECTED_COUNTS.items():
        if key in counts and counts[key] != expected:
            issues.append(f"Curriculum {key} count is {counts[key]}, expected {expected}")
    return counts, assessments


def audit_knowledge_checks(assessments: dict[str, dict], issues: list[str]) -> int:
    found = 0
    for week, assessment_id in CHECK_IDS.items():
        assessment = assessments.get(assessment_id)
        title = f"Week {week} Knowledge Check"
        if assessment is None:
            issues.append(f"Missing {title} ({assessment_id})")
            continue
        found += 1
        if str(assessment.get("title")) != title:
            issues.append(f"{assessment_id} title is not exactly {title}")
        if abs(float(assessment.get("passing_score", 0)) - 0.8) > 1e-9:
            issues.append(f"{title} does not require an 80% score")
        activities = assessment.get("activities") or []
        if len(activities) != 8:
            issues.append(f"{title} has {len(activities)} questions instead of 8")
        for number, activity in enumerate(activities, start=1):
            if activity.get("runtime") != "recognition":
                issues.append(f"{title} question {number} is not multiple choice")
            if len(activity.get("answer_options") or []) != 4:
                issues.append(f"{title} question {number} does not have four choices")
            if not str((activity.get("presentation") or {}).get("review_recommendation") or "").strip():
                issues.append(f"{title} question {number} lacks a missed-question recommendation")
    return found


def audit_applied_labs(root: Path, issues: list[str]) -> int:
    catalog_path = root / "practice" / "applied" / "exercise_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict):
        issues.append("Applied Lab catalog is not a JSON object")
        return 0
    all_numbers = {int(key) for key in catalog}
    if all_numbers != set(range(1, 37)):
        issues.append("Applied Lab catalog does not contain exactly Labs 01–36")
    for key, item in catalog.items():
        lab_root = root / "practice" / "applied" / "exercises" / str(item.get("slug") or "")
        guide = lab_root / "README.md"
        rubric = lab_root / "validation.md"
        starter = lab_root / str(item.get("starter_filename") or "")
        for required in (guide, rubric, starter):
            if not required.is_file():
                issues.append(f"Applied Lab {int(key):02d} is missing {required.name}")
        if not guide.is_file():
            continue
        text = guide.read_text(encoding="utf-8")
        missing = [heading for heading in GUIDE_HEADINGS if heading not in text]
        if missing:
            issues.append(f"Applied Lab {int(key):02d} guide is missing {missing}")
        if len(text.split()) < 700:
            issues.append(f"Applied Lab {int(key):02d} guide is too brief ({len(text.split())} words)")
    return len(catalog)


def audit_applied_lab_locks(root: Path, issues: list[str]) -> int:
    application = root / "application"
    if str(application) not in sys.path:
        sys.path.insert(0, str(application))
    from career_app.services import tracks  # type: ignore

    numbers = [
        int(number)
        for branch in tracks.APPLIED_BRANCH_ORDER
        for number in tracks.APPLIED_BRANCHES[branch]
    ]
    if sorted(numbers) != list(range(1, 37)):
        issues.append("Applied Lab branch locks do not cover Labs 01–36 exactly once")
    if len(numbers) != len(set(numbers)):
        issues.append("An Applied Lab appears in more than one prerequisite branch")
    catalog_numbers = set(int(number) for number in tracks.APPLIED_EXERCISES)
    if catalog_numbers != set(range(1, 37)):
        issues.append("Applied Lab runtime catalog does not contain Labs 01–36")
    for number, skills in tracks.APPLIED_REQUIRED_SKILLS.items():
        if int(number) not in catalog_numbers:
            issues.append(f"Applied Lab prerequisite map references missing Lab {number:02d}")
        unknown = sorted(set(skills) - set(tracks.SKILL_DEFINITIONS))
        if unknown:
            issues.append(f"Applied Lab {number:02d} requires undefined skills: {unknown}")
    return len(numbers)


def audit_portfolio_guidance(root: Path, issues: list[str]) -> int:
    application = root / "application"
    if str(application) not in sys.path:
        sys.path.insert(0, str(application))
    from career_app.data.portfolio_tasks import task_spec  # type: ignore

    checkbox = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$")
    count = 0
    for path in sorted((root / "projects").glob("*/TASKS.md")):
        project_match = re.search(r"project-(\d+)", path.parent.name)
        project_id = int(project_match.group(1)) if project_match else None
        for line in path.read_text(encoding="utf-8").splitlines():
            match = checkbox.match(line)
            if not match:
                continue
            count += 1
            label = match.group(1)
            if task_spec(label, project_id) is None:
                issues.append(f"Portfolio milestone lacks guided workspace metadata: {label}")
    return count


def audit_source_contracts(root: Path, issues: list[str]) -> None:
    main = (root / "application" / "career_app" / "main.py").read_text(encoding="utf-8")
    unified = (root / "application" / "career_app" / "services" / "unified_tasks.py").read_text(encoding="utf-8")
    weekly = (root / "application" / "career_app" / "services" / "weekly_mastery.py").read_text(encoding="utf-8")
    retrospective = (root / "application" / "career_app" / "services" / "task_workspace.py").read_text(encoding="utf-8")
    recommendation = (root / "application" / "career_app" / "academy" / "recommendations.py").read_text(encoding="utf-8")
    academy_service = (root / "application" / "career_app" / "academy" / "service.py").read_text(encoding="utf-8")

    required_hooks = {
        "Next Tasks has four slots": (main, "DASHBOARD_NEXT_TASK_LIMIT = 4"),
        "Next Tasks has no scroll area": (main, "Next Tasks is a fixed dashboard summary"),
        "Next Tasks rows expand": (main, "self.dashboard_tasks_layout.addWidget(task_row, 1)"),
        "five new task limit": (unified, "MAX_FOCUS_TASKS = 5"),
        "daily snapshot": (unified, "daily_focus_snapshot_v2:"),
        "rolling catch-up": (unified, "def _sync_active_catchup"),
        "Catch-Up second line": (unified, 'return f"Catch-Up • {detail}"'),
        "weekly gate": (weekly, "def knowledge_check_readiness"),
        "previous-week progression gate": (weekly, "def task_progression_gate"),
        "retrospective evidence auto-fill": (retrospective, "def retrospective_weekly_evidence"),
        "retrospective progress auto-fill": (retrospective, "def retrospective_weekly_milestones"),
        "lesson activity sequence lock": (recommendation, "Complete the earlier step:"),
        "assessment gate": (recommendation, "weekly_mastery.knowledge_check_readiness"),
        "Academy task keeps its roadmap week": (academy_service, "def _recommendation_week"),
        "weekly check has one durable task": (academy_service, "def _yield_to_weekly_knowledge_check"),
        "legacy lesson rows do not hide coursework": (weekly, 'managed.startswith("roadmap_v1026:lesson:")'),
        "retrospective follows the knowledge check": (weekly, "def _is_post_check_review"),
    }
    for label, (text, hook) in required_hooks.items():
        if hook not in text:
            issues.append(f"Missing source contract: {label}")

    weekly_fields = re.search(r"_WEEKLY_RETROSPECTIVE_FIELDS\s*=\s*\((.*?)\n\)", retrospective, re.S)
    field_text = weekly_fields.group(1) if weekly_fields else ""
    for key in ("biggest_win", "blocker", "learning"):
        if key not in field_text:
            issues.append(f"Weekly retrospective is missing {key}")
    for retired in ("adjustment_1", "adjustment_2", "confidence_reason", '"confidence"'):
        if retired in field_text:
            issues.append(f"Weekly retrospective still exposes {retired}")


def audit_titles_and_retired_content(root: Path, issues: list[str]) -> int:
    application = root / "application"
    sys.path.insert(0, str(application))
    from career_app.services.task_titles import title_case_task  # type: ignore

    count = 0
    checkbox = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$")
    # Weekly roadmap guides are program-owned. Portfolio TASKS.md files are
    # learner-owned after onboarding, so installed audits validate their mapped
    # workspace metadata without rewriting or enforcing presentation casing.
    for path in list((root / "weeks").glob("week-*/README.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = checkbox.match(line)
            if not match:
                continue
            count += 1
            label = match.group(1)
            expected = title_case_task(label)
            if label != expected:
                issues.append(f"Task title is not canonical Title Case in {path}: {label!r} -> {expected!r}")

    scan_roots = (root / "application", root / "curriculum", root / "weeks", root / "practice", root / "workspaces")
    for scan_root in scan_roots:
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".yaml", ".yml", ".md", ".json", ".txt"}:
                continue
            if "__pycache__" in path.parts or path.name == "audit_program_integrity.py":
                continue
            if path.name in {"migration.py", "legacy_planner.py"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for phrase in RETIRED_ACTIVE_PHRASES:
                if phrase in text:
                    issues.append(f"Retired active phrase {phrase!r} remains in {path.relative_to(root)}")
    for relative in RETIRED_PATHS:
        if (root / relative).exists():
            issues.append(f"Retired path still exists: {relative}")
    return count


def audit_weekly_retrospectives(root: Path, issues: list[str]) -> int:
    found = 0
    for week in range(1, 12):
        path = root / "weeks" / f"week-{week:02d}" / "README.md"
        expected = f"- [ ] Complete the Week {week} Retrospective"
        if expected not in path.read_text(encoding="utf-8"):
            issues.append(f"Week {week} is missing its weekly retrospective task")
        else:
            found += 1
    final_path = root / "weeks" / "week-12" / "README.md"
    if "Retrospective" not in final_path.read_text(encoding="utf-8"):
        issues.append("Week 12 is missing the final program retrospective")
    else:
        found += 1
    return found


def run(root: Path) -> dict[str, Any]:
    issues: list[str] = []
    counts, assessments = audit_curriculum(root, issues)
    counts["weekly_knowledge_checks"] = audit_knowledge_checks(assessments, issues)
    counts["applied_labs"] = audit_applied_labs(root, issues)
    counts["applied_lab_lock_nodes"] = audit_applied_lab_locks(root, issues)
    counts["portfolio_guided_tasks"] = audit_portfolio_guidance(root, issues)
    counts["weekly_retrospectives"] = audit_weekly_retrospectives(root, issues)
    audit_source_contracts(root, issues)
    counts["canonical_task_titles"] = audit_titles_and_retired_content(root, issues)
    return {
        "status": "passed" if not issues else "failed",
        "counts": counts,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    report = run(root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Program audit: {report['status'].upper()}")
        for key, value in report["counts"].items():
            print(f"  {key}: {value}")
        for issue in report["issues"]:
            print(f"ERROR: {issue}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
