"""Detailed, solution-safe studio guidance for every Applied Lab.

The studio explains the decisions and validation process a learner must follow
without revealing the finished formula, SQL query, DAX measure, Python code, or
numeric answer.  Every lab receives its own persisted stage workspace even
though the visual shell is shared for consistency.
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


_TOOL_SETUP: dict[str, tuple[str, ...]] = {
    "SQL Validation": (
        "Create or open the provided SQL submission and read every starter comment before writing a query.",
        "List the tables you need, the grain of each table, and the key fields that connect them.",
        "Write down the expected grain of the final result before joining or aggregating anything.",
        "Plan small diagnostic queries that prove row counts, uniqueness, null behavior, and join cardinality before the final analysis.",
    ),
    "Broken Analysis": (
        "Run or inspect the broken analysis first and save its output as the before state.",
        "Separate the business-definition problem from the technical implementation problem.",
        "Identify the row grain before and after every join, grouping, filter, or calculation.",
        "Plan an independent reconciliation that does not reuse the same logic as the result being checked.",
    ),
    "Business Analysis": (
        "Rewrite the requested metric in plain language and identify the business decision it should support.",
        "Define the entity, time period, numerator, denominator, exclusions, and segmentation rules.",
        "Sketch the final table before building it so each row and column has a clear meaning.",
        "Choose at least one independent check that would reveal duplicated entities or inconsistent populations.",
    ),
    "Statistics": (
        "Identify the target population, observed sample, variables, measurement units, and outcome of interest.",
        "State the statistical question without assuming the result in advance.",
        "Check whether the method's assumptions are reasonable for the available data.",
        "Plan both a technical interpretation and a stakeholder-friendly interpretation of uncertainty.",
    ),
    "Power BI": (
        "Identify which work belongs in Power Query, the data model, DAX, and the report canvas before making changes.",
        "Document the intended table grain, relationship direction, and key fields before building the model.",
        "Keep raw imports separate from transformed queries and give every important step a readable name.",
        "Plan a validation table or card that can be compared with the source or an independent calculation.",
    ),
    "Python": (
        "Open the provided Python submission and identify the expected inputs, outputs, and required libraries.",
        "Load data without overwriting the raw object, then inspect shape, columns, data types, missing values, and duplicate keys.",
        "Break the work into small named transformations instead of one long expression.",
        "Plan assertions or comparison checks that prove the result has the intended rows, columns, and totals.",
    ),
    "Data Acquisition": (
        "Document the source, endpoint or file location, expected pagination behavior, and any access limitations.",
        "Inspect one response or file before designing the full ingestion process.",
        "Identify stable record keys and decide how nested fields will be represented.",
        "Plan retry, duplicate, missing-page, and schema-change checks before collecting the full dataset.",
    ),
    "Data Workflow": (
        "Draw the intended path from raw inputs to cleaned, validated, and analysis-ready outputs.",
        "Define what is allowed to change at each layer and what must remain immutable.",
        "Choose stable keys, naming rules, and validation checks before building transformations.",
        "Plan how another analyst could rerun the workflow without relying on undocumented manual steps.",
    ),
    "Communication": (
        "Identify the audience, decision, urgency, and level of technical detail that is appropriate.",
        "Separate confirmed findings, interpretations, recommendations, assumptions, and limitations.",
        "Choose the smallest amount of evidence needed to support the requested decision.",
        "Outline the message before drafting so the recommendation follows logically from the evidence.",
    ),
    "Timed Analysis": (
        "Read the request once for the business question and again for the deadline, scope, and required output.",
        "Timebox source inspection, analysis, validation, and communication before starting.",
        "Define the minimum defensible answer and avoid optional analysis until the core result is validated.",
        "Keep a short decision log so assumptions made under time pressure remain visible.",
    ),
    "Responsible AI": (
        "Separate AI-generated claims from facts that can be verified directly in the data or source material.",
        "List every calculation, citation, transformation, and recommendation that needs independent checking.",
        "Identify privacy, bias, hallucination, and overconfidence risks before editing the output.",
        "Define what evidence would be required before a stakeholder could safely act on the analysis.",
    ),
}


def _safe_text(value: Any) -> str:
    """Remove accidental solution-like syntax from catalog text used as guidance."""
    text = " ".join(str(value or "").split())
    # Catalog prose should not contain full code, but strip obvious assignment or
    # formula fragments if one is introduced later.
    if re.search(r"(?:SELECT\s+.+\s+FROM|=\s*[A-Z][A-Z0-9_]*\(|:=)", text, re.I):
        return "Complete this step using the relevant method taught in the prerequisite lessons."
    return text


def _action_detail(step: str, index: int) -> str:
    step = _safe_text(step).rstrip(".")
    return (
        f"{step}. Before you begin, identify which source fields and assumptions this step depends on. "
        "Complete the work in a clearly labeled section of the submission, then run a small check that "
        "would expose a missing row, duplicate entity, incorrect filter, or mismatched unit."
    )


def _category_setup(item: dict[str, Any]) -> tuple[str, ...]:
    category = str(item.get("category") or "")
    return _TOOL_SETUP.get(
        category,
        (
            "Open the starter and source material, then identify the required input, output, and audience.",
            "Record the grain or unit of analysis and the fields needed to complete the assignment.",
            "Break the work into small, named sections that can be validated independently.",
            "Choose at least one independent check before building the final result.",
        ),
    )


def studio_stages(number: int, item: dict[str, Any]) -> tuple[LabStage, ...]:
    objective = _safe_text(item.get("objective") or item.get("title"))
    concepts = _safe_text(item.get("concepts") or "the required concepts")
    steps = tuple(_safe_text(value) for value in item.get("steps", ()) if str(value).strip())
    deliverables = tuple(_safe_text(value) for value in item.get("deliverables", ()) if str(value).strip())
    validations = tuple(_safe_text(value) for value in item.get("validation", ()) if str(value).strip())
    setup = _category_setup(item)

    build_actions = tuple(_action_detail(step, index) for index, step in enumerate(steps, start=1))
    if not build_actions:
        build_actions = (
            "Build the required analysis in small, named steps. After each step, inspect the output before continuing.",
            "Keep raw inputs unchanged and make every transformation or calculation traceable.",
            "Do not type a final value manually when it can be derived from the source data.",
        )

    delivery_actions = tuple(
        f"Create the required deliverable: {value}. Make its purpose, scope, and source clear to a reviewer."
        for value in deliverables
    ) or (
        "Save the completed analysis artifact in the lab submission location.",
        "Include a concise explanation of the finding, its business meaning, and one limitation.",
    )

    validation_actions = tuple(
        f"Verify this requirement independently: {value}. Record how you checked it rather than only stating that it passed."
        for value in validations
    ) or (
        "Confirm that row counts and unique entity counts match the intended grain.",
        "Reconcile at least one total or rate using a second method.",
        "Test a boundary, missing-value, or duplicate-record case that could change the conclusion.",
    )

    return (
        LabStage(
            title="Frame the request and define success",
            purpose=(
                f"Turn the assignment into a clear analytical question before using a tool. The lab objective is to {objective[:1].lower() + objective[1:] if objective else 'complete the assigned analysis'}."
            ),
            actions=(
                "Read the business assignment, deliverables, and validation criteria from beginning to end before opening the starter.",
                "Rewrite the request as one question that names the audience, decision, entity being analyzed, and time period.",
                f"List the concepts you expect to use: {concepts}.",
                "Define what a trustworthy final result must contain and what would make the result unsafe to use.",
                "Create the submission and add a short assumptions section. Do not begin the final calculation yet.",
            ),
            output="A clearly stated business question, definition of done, and initial assumptions list inside the lab submission.",
            validation=(
                "The question can be answered with the supplied data and does not assume a result.",
                "The intended audience and decision are explicit.",
                "The definition of done matches the lab deliverables rather than adding portfolio-scale work.",
            ),
            evidence="Record the business question, intended decision, and the most important assumption you identified.",
            pitfalls=(
                "Starting calculations before deciding what one row or observation represents.",
                "Expanding the scope beyond the lab's requested decision.",
                "Treating an assumption as a confirmed fact.",
            ),
        ),
        LabStage(
            title="Inspect the sources and plan the method",
            purpose="Understand the data and choose a safe analysis path before building the result.",
            actions=setup + (
                "Use the source preview or tool profiler to record row counts, columns, data types, missing fields, duplicate candidates, date coverage, and measurement units.",
                "Identify the candidate key for each source and state what one row represents.",
                "Write a short plan that names the intermediate outputs you will create and the order in which you will validate them.",
                "Note any source limitation that could weaken the final conclusion.",
            ),
            output="A source inventory, grain statement, key map, and short analysis plan.",
            validation=(
                "Every source has a stated grain and candidate key or a documented reason that no unique key exists.",
                "The planned method uses only skills available from prerequisite coursework unless the guide explicitly introduces a new method.",
                "The plan includes at least one check that is independent of the final calculation.",
            ),
            evidence="Record the source grain, candidate key, row-count check, and one data-quality concern or limitation.",
            pitfalls=(
                "Joining or merging sources before checking whether the key is unique.",
                "Changing raw data instead of creating a traceable cleaned layer.",
                "Assuming dates, percentages, currency, or identifiers already use the correct type.",
            ),
        ),
        LabStage(
            title="Build the analysis in traceable steps",
            purpose="Apply the required skills while keeping each transformation and calculation understandable and testable.",
            actions=build_actions + (
                "Use comments, readable names, or labeled worksheet sections so another learner can follow the order of operations.",
                "After each major step, compare row counts and unique entity counts with the prior stage before moving on.",
                "Keep exact solutions out of notes copied from external sources; explain why the method fits this business question in your own words.",
            ),
            output=(
                "A working analysis that produces the requested intermediate and final outputs without manually typing calculated answers."
            ),
            validation=(
                "The output grain matches the grain defined in Stage 2.",
                "Filters, exclusions, and missing-value rules are visible and consistent.",
                "Calculated results update when the source or selected input changes.",
                "No step silently duplicates or removes entities without explanation.",
            ),
            evidence="Record the main sections you built, the method chosen for each, and one intermediate check that passed.",
            pitfalls=(
                "Building the entire answer in one expression that cannot be inspected.",
                "Using a row-level average when the business definition requires a weighted result.",
                "Hard-coding a total, date, category, or rate that should come from the data or a control.",
            ),
            hints=(
                "Start with the smallest intermediate table or calculation that can be checked independently.",
                "When multiple conditions are required, list each condition in words before selecting a function or clause.",
                "When a result looks plausible, test a deliberately narrow subset to confirm the logic.",
            ),
        ),
        LabStage(
            title="Validate, reconcile, and challenge the result",
            purpose="Prove that the analysis is structurally correct before interpreting it.",
            actions=validation_actions + (
                "Test at least one boundary condition, such as the first or last date, a missing value, a zero denominator, or an entity with multiple records.",
                "Compare the final result with a simpler independent calculation, source subtotal, or manually inspected sample.",
                "Investigate differences rather than changing valid logic merely to force agreement.",
                "Document every unresolved issue and explain whether it changes the strength of the conclusion.",
            ),
            output="A completed validation record showing what was checked, how it was checked, and any unresolved difference.",
            validation=(
                "The final row count and distinct-entity count are consistent with the intended grain.",
                "At least one total, rate, or distribution is reconciled independently.",
                "Boundary and missing-value behavior are tested rather than assumed.",
                "Unresolved differences remain visible and are not hidden by rounding or manual edits.",
            ),
            evidence="Record the validation checks, the comparison method, and the result of the most important boundary test.",
            pitfalls=(
                "Reusing the same calculation as its own validation.",
                "Checking only the final number and ignoring duplicated or missing rows.",
                "Forcing a reconciliation to zero without understanding the difference.",
            ),
        ),
        LabStage(
            title="Explain the finding and complete the handoff",
            purpose="Turn a validated result into a concise, responsible analytical deliverable.",
            actions=delivery_actions + (
                "Write a short takeaway that states the result in plain language, explains why it matters, and names a reasonable next action.",
                "Add at least one limitation or assumption that changes how confidently the result should be used.",
                "Remove unnecessary technical detail from the main takeaway while keeping validation evidence in the submission.",
                "Reopen the saved artifact and confirm that its tables, code, visuals, links, and notes are readable.",
                "Complete the Studio checklist and save stage evidence before marking the lab complete.",
            ),
            output="A saved, reopenable lab submission with a concise takeaway, supporting evidence, and visible limitations.",
            validation=(
                "Every requested deliverable is present and clearly labeled.",
                "The takeaway is supported by the validated result and does not claim causation or certainty without evidence.",
                "A reviewer can identify the source, method, assumptions, and remaining limitations.",
                "The artifact path or share link opens successfully.",
            ),
            evidence="Record the artifact location, final takeaway, requested next action, and most important limitation.",
            pitfalls=(
                "Repeating technical steps instead of explaining the business meaning.",
                "Making a recommendation that is not supported by the analysis.",
                "Marking the lab complete before reopening and checking the saved artifact.",
            ),
        ),
    )


def guide_markdown(number: int, item: dict[str, Any]) -> str:
    stages = studio_stages(number, item)
    lines = [
        f"# Applied Lab {int(number):02d}: {item['title']}",
        "",
        "> This guide tells you what decisions to make, what output to produce, and how to validate it. "
        "It intentionally does not provide the finished formula, query, measure, code, or numerical answer.",
        "",
        "## Assignment",
        "",
        _safe_text(item.get("objective") or item.get("title")),
        "",
        "## Skills you will apply",
        "",
        _safe_text(item.get("concepts")),
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
                *[f"{action_index}. {action}" for action_index, action in enumerate(stage.actions, start=1)],
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
            lines.extend(["### Progressive hints", "", *[f"- {value}" for value in stage.hints], ""])
    lines.extend(
        [
            "## Completion rule",
            "",
            "Complete every Studio stage, save a changed submission or linked artifact, record validation evidence, and finish the final handoff review. "
            "The main guide will not reveal the finished solution; use the prerequisite lessons and progressively stronger hints when you are stuck.",
            "",
        ]
    )
    return "\n".join(lines)
