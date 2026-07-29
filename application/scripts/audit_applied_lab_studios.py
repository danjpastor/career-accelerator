#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit all Applied Lab Studios and solution-safe guides.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "application"))

    from career_app.data.applied_exercises import APPLIED_EXERCISES
    from career_app.data.applied_lab_guidance import guide_markdown, studio_stages

    errors: list[str] = []
    if len(APPLIED_EXERCISES) != 36:
        errors.append(f"Expected 36 Applied Labs; found {len(APPLIED_EXERCISES)}")

    prohibited = (
        re.compile(r"(?m)^\s*=\s*(IF|SUMIF|SUMIFS|COUNTIF|COUNTIFS|VLOOKUP|XLOOKUP|AVERAGE|QUERY)\s*\(", re.I),
        re.compile(r"```\s*(sql|python|dax|gs|excel|javascript)", re.I),
        re.compile(r"(?mi)^\s*(SELECT|WITH|CREATE\s+TABLE|UPDATE|DELETE\s+FROM)\b.+$"),
        re.compile(r"(?i)expected\s+(answer|result|total)\s*[:=]"),
        re.compile(r"(?i)(copy|paste)\s+(this|the following)\s+(formula|query|code|measure)"),
    )
    required_phrases = (
        "Required output",
        "Check your work",
        "Evidence to record",
        "Common mistakes",
    )

    for number, item in sorted(APPLIED_EXERCISES.items()):
        slug = str(item["slug"])
        guide_path = root / "practice" / "applied" / "exercises" / slug / "README.md"
        if not guide_path.is_file():
            errors.append(f"Lab {number:02d} guide is missing: {slug}")
            continue
        text = guide_path.read_text(encoding="utf-8")
        if number == 1:
            stage_count = len(re.findall(r"(?m)^## Stage \d+", text))
            if stage_count != 4:
                errors.append(f"Lab 01 should have four beginner stages; found {stage_count}.")
        else:
            stages = studio_stages(number, item)
            if len(stages) != 5:
                errors.append(f"Lab {number:02d} should have five Studio stages; found {len(stages)}.")
            generated = guide_markdown(number, item)
            if generated.strip() != text.strip():
                errors.append(f"Lab {number:02d} README is not synchronized with its Studio guidance.")
            for index, stage in enumerate(stages, start=1):
                if len(stage.actions) < 4:
                    errors.append(f"Lab {number:02d} Stage {index} is not detailed enough.")
                if len(stage.validation) < 3:
                    errors.append(f"Lab {number:02d} Stage {index} lacks validation guidance.")
                if len(stage.pitfalls) < 3:
                    errors.append(f"Lab {number:02d} Stage {index} lacks common-mistake guidance.")

        for phrase in required_phrases:
            if phrase not in text:
                errors.append(f"Lab {number:02d} guide is missing section: {phrase}")
        for pattern in prohibited:
            if pattern.search(text):
                errors.append(f"Lab {number:02d} guide appears to reveal a completed solution ({pattern.pattern}).")
                break

    studio_source = root / "application" / "career_app" / "ui" / "applied_lab_studio.py"
    source = studio_source.read_text(encoding="utf-8") if studio_source.is_file() else ""
    for token in ("stage_evidence", "artifact_input", "takeaway_input", "final_checks", "completion_issues"):
        if token not in source:
            errors.append(f"Shared Studio is missing persisted workflow element: {token}")

    if errors:
        print("Applied Lab Studio audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Applied Lab Studio audit passed")
    print("- 36 active lab guides")
    print("- Lab 01 has four beginner stages")
    print("- Labs 02–36 have five persisted guided stages")
    print("- no finished formulas, queries, code, measures, or expected answers in primary guides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
