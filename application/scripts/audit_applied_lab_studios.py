#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


CORE_LABS = {1, 4, 13, 21, 25}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the compact Applied Lab library and required roadmap set."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "application"))

    from career_app.data.applied_exercises import APPLIED_EXERCISES, CORE_APPLIED_LABS
    from career_app.data.applied_lab_guidance import guide_markdown, studio_stages

    errors: list[str] = []
    if len(APPLIED_EXERCISES) != 36:
        errors.append(f"Expected 36 Applied Labs in the library; found {len(APPLIED_EXERCISES)}")
    if set(CORE_APPLIED_LABS) != CORE_LABS:
        errors.append(
            "Required roadmap labs must be exactly 01, 04, 13, 21, and 25; "
            f"found {tuple(CORE_APPLIED_LABS)}"
        )

    catalog_path = root / "practice" / "applied" / "exercise_catalog.json"
    try:
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raw_catalog = {}
        errors.append(f"Could not read exercise catalog: {exc}")
    if not isinstance(raw_catalog, dict) or len(raw_catalog) != 36:
        errors.append("exercise_catalog.json must contain 36 keyed lab records.")

    prohibited = (
        re.compile(r"(?m)^\s*=\s*(IF|SUMIF|SUMIFS|COUNTIF|COUNTIFS|VLOOKUP|XLOOKUP|AVERAGE|QUERY)\s*\(", re.I),
        re.compile(r"```\s*(sql|python|dax|gs|excel|javascript)", re.I),
        re.compile(r"(?mi)^\s*(SELECT|WITH|CREATE\s+TABLE|UPDATE|DELETE\s+FROM)\b.+$"),
        re.compile(r"(?i)expected\s+(answer|result|total)\s*[:=]"),
        re.compile(r"(?i)(copy|paste)\s+(this|the following)\s+(formula|query|code|measure)"),
    )
    required_phrases = (
        "Scope guardrails",
        "Required output",
        "Check your work",
        "Evidence to record",
        "Common mistakes",
        "Completion rule",
    )

    for number, item in sorted(APPLIED_EXERCISES.items()):
        expected_optional = number not in CORE_LABS
        if bool(item.get("optional")) != expected_optional:
            errors.append(
                f"Lab {number:02d} optional flag should be {expected_optional}; "
                f"found {bool(item.get('optional'))}."
            )
        minutes = int(item.get("minutes") or 0)
        if not 30 <= minutes <= 45:
            errors.append(f"Lab {number:02d} should be 30–45 minutes; found {minutes}.")
        steps = tuple(item.get("steps") or ())
        deliverables = tuple(item.get("deliverables") or ())
        validations = tuple(item.get("validation") or ())
        if not 2 <= len(steps) <= 4:
            errors.append(f"Lab {number:02d} should have 2–4 actions; found {len(steps)}.")
        if not 1 <= len(deliverables) <= 2:
            errors.append(f"Lab {number:02d} should have 1–2 deliverables; found {len(deliverables)}.")
        if not 2 <= len(validations) <= 3:
            errors.append(f"Lab {number:02d} should have 2–3 checks; found {len(validations)}.")

        slug = str(item["slug"])
        lab_dir = root / "practice" / "applied" / "exercises" / slug
        guide_path = lab_dir / "README.md"
        validation_path = lab_dir / "validation.md"
        starter_path = lab_dir / str(item.get("starter_filename") or "submission.md")
        for path, label in (
            (guide_path, "guide"),
            (validation_path, "validation guide"),
            (starter_path, "starter"),
        ):
            if not path.is_file():
                errors.append(f"Lab {number:02d} {label} is missing: {path.relative_to(root)}")

        if not guide_path.is_file():
            continue
        text = guide_path.read_text(encoding="utf-8")
        stages = studio_stages(number, item)
        if len(stages) != 3:
            errors.append(f"Lab {number:02d} should have three Studio stages; found {len(stages)}.")
        generated = guide_markdown(number, item)
        if generated.strip() != text.strip():
            errors.append(f"Lab {number:02d} README is not synchronized with Studio guidance.")
        stage_count = len(re.findall(r"(?m)^## Stage \d+", text))
        if stage_count != 3:
            errors.append(f"Lab {number:02d} README should show three stages; found {stage_count}.")
        for phrase in required_phrases:
            if phrase not in text:
                errors.append(f"Lab {number:02d} guide is missing section: {phrase}")
        for pattern in prohibited:
            if pattern.search(text):
                errors.append(
                    f"Lab {number:02d} guide appears to reveal a completed solution ({pattern.pattern})."
                )
                break

    studio_source = root / "application" / "career_app" / "ui" / "applied_lab_studio.py"
    source = studio_source.read_text(encoding="utf-8") if studio_source.is_file() else ""
    for token in ("stage_evidence", "artifact_input", "takeaway_input", "final_checks", "completion_issues"):
        if token not in source:
            errors.append(f"Shared Studio is missing persisted workflow element: {token}")

    if errors:
        print("Applied Lab audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Applied Lab audit passed")
    print("- 36 compact lab guides remain available")
    print("- 5 required roadmap labs: 01, 04, 13, 21, and 25")
    print("- 31 optional labs do not enter the adaptive planner")
    print("- every lab is 30–45 minutes with 2–4 actions and three Studio stages")
    print("- no finished formulas, queries, code, measures, or expected answers in primary guides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
