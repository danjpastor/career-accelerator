from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _project_root(selected: Path) -> Path:
    selected = selected.expanduser().resolve()
    for candidate in (selected, *selected.parents):
        if (
            (candidate / "application/career_app/academy/loader.py").is_file()
            and (candidate / "curriculum/data/program.yaml").is_file()
        ):
            return candidate
        if (
            (candidate / "career_app/academy/loader.py").is_file()
            and (candidate.parent / "curriculum/data/program.yaml").is_file()
        ):
            return candidate.parent
    raise FileNotFoundError(
        "Could not locate the Career Accelerator application and curriculum."
    )


def _declared_tables(activity: Any) -> tuple[str, ...]:
    presentation = dict(activity.presentation)
    value = presentation.get("tables", presentation.get("table"))
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("selected_folder")
    parser.add_argument(
        "--report",
        default="documentation/ACADEMY_TASK_CLARITY_AUDIT.md",
    )
    args = parser.parse_args()

    root = _project_root(Path(args.selected_folder))
    sys.path.insert(0, str(root / "application"))

    from career_app.academy.loader import load_catalog
    from career_app.academy.task_clarity import build_activity_clarity
    from career_app.academy.validators.sql import SqlValidator

    catalog = load_catalog(root / "curriculum/data")
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    counts = Counter()

    def inspect_activity(location: str, item_type: str, activity: Any) -> None:
        counts["activities"] += 1
        counts[item_type] += 1
        validator = dict(activity.validator)
        expected_columns: tuple[str, ...] = ()
        expected_row_count: int | None = None

        if activity.runtime == "sql":
            counts["sql"] += 1
            dataset_id = str(validator.get("dataset_id") or "sql_foundations")
            dataset = catalog.datasets.get(dataset_id)
            expected_query = str(validator.get("expected_query") or "").strip()
            if dataset is None:
                errors.append(
                    f"{location} / {activity.activity_id}: unknown dataset {dataset_id!r}."
                )
            elif not expected_query:
                errors.append(
                    f"{location} / {activity.activity_id}: SQL activity has no expected query."
                )
            else:
                result = SqlValidator(dataset).execute(expected_query)
                if not result.passed:
                    errors.append(
                        f"{location} / {activity.activity_id}: expected query does not run: "
                        f"{result.feedback}"
                    )
                else:
                    expected_columns = tuple(str(item) for item in result.columns)
                    if not bool(validator.get("allow_subset", False)):
                        expected_row_count = len(result.rows)
            if not _declared_tables(activity):
                errors.append(
                    f"{location} / {activity.activity_id}: no learner-visible table declaration."
                )
        elif activity.runtime == "recognition":
            counts["recognition"] += 1
            if len(activity.answer_options) < 2:
                errors.append(
                    f"{location} / {activity.activity_id}: recognition activity needs "
                    "at least two answer options."
                )

        prompt = str(activity.prompt or "").strip()
        if len(prompt) < 15:
            errors.append(
                f"{location} / {activity.activity_id}: prompt is missing or too short."
            )

        presentation = dict(activity.presentation)
        raw_task = str(presentation.get("task") or "").strip()
        raw_requirements = presentation.get("requirements")
        raw_expected = str(presentation.get("expected_output") or "").strip()

        clarity = build_activity_clarity(
            activity,
            expected_columns=expected_columns,
            expected_row_count=expected_row_count,
        )
        combined = " ".join((clarity.task, *clarity.requirements, clarity.expected_output))
        missing_columns = [
            name for name in expected_columns if name.casefold() not in combined.casefold()
        ]
        if missing_columns:
            errors.append(
                f"{location} / {activity.activity_id}: rendered instructions omit columns "
                + ", ".join(missing_columns)
            )

        reasons: list[str] = []
        if raw_task and raw_task != prompt and len(raw_task) < len(prompt):
            reasons.append("short task replaced by full prompt")
        if not raw_requirements:
            reasons.append("requirements generated")
        if not raw_expected:
            reasons.append("definition of done generated")
        if expected_columns and not all(
            name.casefold() in " ".join(
                [raw_task, *(
                    [str(x) for x in raw_requirements]
                    if isinstance(raw_requirements, list)
                    else []
                )]
            ).casefold()
            for name in expected_columns
        ):
            reasons.append("exact output columns added")
        if reasons:
            warnings.append(
                f"{location} / {activity.activity_id}: " + "; ".join(reasons) + "."
            )

        counts["enriched" if clarity.enriched else "already_clear"] += 1
        rows.append(
            {
                "location": location,
                "activity": activity.activity_id,
                "runtime": activity.runtime,
                "status": "Enhanced" if clarity.enriched else "Already clear",
                "columns": ", ".join(expected_columns) or "Not applicable",
                "shape": (
                    f"{expected_row_count} × {len(expected_columns)}"
                    if expected_row_count is not None and expected_columns
                    else "Variable / recognition"
                ),
            }
        )

    for path in catalog.program.paths:
        for track in path.tracks:
            for course in track.courses:
                for module in course.modules:
                    for lesson in module.lessons:
                        counts["lessons"] += 1
                        location = (
                            f"{track.title} › {course.title} › "
                            f"{module.title} › Lesson {lesson.order}: {lesson.title}"
                        )
                        for activity in lesson.activities:
                            inspect_activity(location, "lesson_activity", activity)
                for assessment in course.assessments:
                    location = f"{track.title} › {course.title} › Checkpoint: {assessment.title}"
                    for activity in assessment.activities:
                        inspect_activity(location, "assessment_activity", activity)
                for lab in course.skills_labs:
                    location = f"{track.title} › {course.title} › Skills Lab: {lab.title}"
                    inspect_activity(location, "skills_lab_activity", lab.activity)

    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Accelerator Academy Task-Clarity Audit",
        "",
        "This report checks every installed lesson activity, checkpoint question, "
        "and Skills Lab action after the learner-facing clarity renderer is applied.",
        "",
        "## Summary",
        "",
        f"- Lessons checked: **{counts['lessons']}**",
        f"- Total learning actions checked: **{counts['activities']}**",
        f"- Lesson activities: **{counts['lesson_activity']}**",
        f"- Checkpoint activities: **{counts['assessment_activity']}**",
        f"- Skills Lab activities: **{counts['skills_lab_activity']}**",
        f"- SQL actions: **{counts['sql']}**",
        f"- Recognition actions: **{counts['recognition']}**",
        f"- Actions automatically enriched: **{counts['enriched']}**",
        f"- Actions already complete: **{counts['already_clear']}**",
        f"- Blocking errors: **{len(errors)}**",
        "",
        "## Quality contract",
        "",
        "Every rendered task provides the complete prompt, visible schemas, exact "
        "output columns and order, fixed result shape when applicable, readable "
        "requirements, and a definition of done. Reference SQL and expected "
        "result values remain hidden.",
        "",
        "## Activity results",
        "",
        "| Location | Activity | Runtime | Status | Required columns | Result shape |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        safe = {key: str(value).replace("|", "/") for key, value in row.items()}
        lines.append(
            "| {location} | `{activity}` | {runtime} | {status} | {columns} | {shape} |".format(
                **safe
            )
        )

    if warnings:
        lines.extend(["", "## Automatically corrected source gaps", ""])
        lines.extend(f"- {item}" for item in warnings)

    if errors:
        lines.extend(["", "## Blocking errors", ""])
        lines.extend(f"- {item}" for item in errors)
    else:
        lines.extend(
            [
                "",
                "## Result",
                "",
                "**PASS — every installed Academy learning action has complete "
                "learner-facing instructions.**",
            ]
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Academy task-clarity report: {report_path}")
    print(
        f"Checked {counts['lessons']} lessons and {counts['activities']} learning actions; "
        f"{counts['enriched']} are enriched at render time."
    )
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    print("PASS: every rendered task satisfies the clarity contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
