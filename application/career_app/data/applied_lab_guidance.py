"""Compact, solution-safe guidance for Applied Labs.

Applied Labs are intentionally smaller than projects. Each lab has three stages:
understand the task, build the required result, and check/explain the result.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class LabStage:
    title: str
    purpose: str
    actions: tuple[str, ...]
    output: str
    validation: tuple[str, ...]
    evidence: str
    pitfalls: tuple[str, ...]
    hints: tuple[str, ...] = ()


def _safe_text(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if re.search(r"(?:SELECT\s+.+\s+FROM|=\s*[A-Z][A-Z0-9_]*\(|:=)", text, re.I):
        return "Complete this step using the method taught in the prerequisite lesson."
    return text


def _artifact_text(deliverables: tuple[str, ...]) -> str:
    if not deliverables:
        return "Save the completed lab result in the supplied submission location."
    if len(deliverables) == 1:
        return deliverables[0]
    return " ".join(deliverables)


def studio_stages(number: int, item: dict[str, Any]) -> tuple[LabStage, ...]:
    objective = _safe_text(item.get("objective") or item.get("title"))
    steps = tuple(_safe_text(value) for value in item.get("steps", ()) if str(value).strip())
    deliverables = tuple(
        _safe_text(value) for value in item.get("deliverables", ()) if str(value).strip()
    )
    validations = tuple(
        _safe_text(value) for value in item.get("validation", ()) if str(value).strip()
    )
    if not steps:
        steps = (
            "Create the requested result using the supplied data and the prerequisite lesson method.",
            "Save the result in the supplied submission location.",
        )
    if not validations:
        validations = (
            "The result uses the intended rows and fields.",
            "One independent check supports the result.",
        )

    return (
        LabStage(
            title="Understand the task",
            purpose="Define the small result you need before opening the analysis tool.",
            actions=(
                f"Read the assignment and restate the goal in one sentence: {objective}",
                "Identify the source table or file, what one row represents, and the fields needed for the result.",
                "Write down one quick check you can use to catch a missing row, duplicate, wrong filter, or incorrect total.",
            ),
            output="A one-sentence goal, a grain statement, and one planned validation check.",
            validation=(
                "The goal matches the requested output and does not add project-scale work.",
                "The source grain and required fields are clear.",
            ),
            evidence="Record the goal, source grain, and planned check in a few lines.",
            pitfalls=(
                "Expanding the lab into a dashboard, pipeline, report package, or portfolio case study.",
                "Starting with calculations before deciding what one row represents.",
            ),
        ),
        LabStage(
            title="Build the required result",
            purpose="Complete only the two-to-four actions listed in the lab brief.",
            actions=steps,
            output=_artifact_text(deliverables),
            validation=validations,
            evidence="Record what you created and the result of one intermediate check.",
            pitfalls=(
                "Adding extra analysis that is not required by the brief.",
                "Hard-coding a final answer instead of deriving it from the supplied data.",
                "Continuing after a row-count, key, filter, or total check does not make sense.",
            ),
            hints=(
                "Complete one listed action at a time and inspect its output before continuing.",
                "Use the smallest table, chart, query, formula, or script that satisfies the brief.",
            ),
        ),
        LabStage(
            title="Check and explain",
            purpose="Confirm the result is trustworthy and explain the main finding briefly.",
            actions=tuple(
                [f"Verify: {value}" for value in validations]
                + [
                    "Save or reopen the required artifact to confirm it is readable and reproducible.",
                    "Write a two-to-three-sentence takeaway: the result, why it matters, and one limitation or next question.",
                ]
            ),
            output="A checked artifact and a short evidence-based takeaway.",
            validation=(
                "At least one check is independent of the main calculation.",
                "The takeaway is supported by the result and includes a limitation or next question.",
                "The saved artifact can be reopened.",
            ),
            evidence="Record the validation result, artifact location, takeaway, and limitation.",
            pitfalls=(
                "Repeating technical steps instead of explaining the result.",
                "Claiming causation, certainty, or business impact that the data does not support.",
            ),
        ),
    )


def guide_markdown(number: int, item: dict[str, Any]) -> str:
    stages = studio_stages(number, item)
    optional_note = (
        "This is optional extended practice and does not block the roadmap."
        if item.get("optional")
        else "This is one of the five required integration labs in the roadmap."
    )
    lines = [
        f"# Applied Lab {int(number):02d}: {item['title']}",
        "",
        f"> {optional_note} The lab is designed for about {int(item['minutes'])} minutes and should not become a project.",
        "",
        "## Assignment",
        "",
        _safe_text(item.get("objective") or item.get("title")),
        "",
        "## Skills you will apply",
        "",
        _safe_text(item.get("concepts")),
        "",
        "## Scope guardrails",
        "",
        "- Use one tool and the supplied dataset.",
        "- Complete only the listed actions.",
        "- Produce one primary result plus a short takeaway.",
        "- Stop when the validation checks pass; do not expand the lab into a portfolio project.",
        "",
    ]
    for index, stage in enumerate(stages, start=1):
        lines.extend(
            [
                f"## Stage {index}: {stage.title}",
                "",
                stage.purpose,
                "",
                "### What to do",
                "",
                *[f"{n}. {value}" for n, value in enumerate(stage.actions, start=1)],
                "",
                "### Required output",
                "",
                stage.output,
                "",
                "### Check your work",
                "",
                *[f"- {value}" for value in stage.validation],
                "",
                "### Evidence to record",
                "",
                stage.evidence,
                "",
                "### Common mistakes",
                "",
                *[f"- {value}" for value in stage.pitfalls],
                "",
            ]
        )
        if stage.hints:
            lines.extend(["### Hints", "", *[f"- {value}" for value in stage.hints], ""])
    lines.extend(
        [
            "## Completion rule",
            "",
            "Complete the three Studio stages, save a changed artifact or linked result, pass the listed checks, and write a two-to-three-sentence takeaway. Extra analysis is not required.",
            "",
        ]
    )
    return "\n".join(lines)
