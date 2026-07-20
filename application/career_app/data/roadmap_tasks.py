"""Curated cross-track roadmap tasks.

The adaptive tracks own learning, Academy, SQL practice, Applied Labs, and
portfolio milestones.  This module defines only the cross-track career tasks
that still belong on the weekly roadmap after those systems are synchronized.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RoadmapTaskSpec:
    key: str
    description: str
    definition_of_done: str
    starter_path: str
    category: str = "General"
    destination: int = 6
    estimated_minutes: int = 35
    priority: int = 2
    energy: str = "Normal"


_WEEKLY_RETROSPECTIVE = RoadmapTaskSpec(
    key="weekly_retrospective",
    description=(
        "Review the week honestly, capture what moved forward, record blockers, "
        "and choose specific adjustments for the next sprint."
    ),
    definition_of_done=(
        "Record study time and major completions; list at least one win, one "
        "blocker, and one lesson; identify any evidence created; and write two "
        "specific changes for next week."
    ),
    starter_path="roadmap_starters/weekly_retrospective.md",
    category="Review",
    destination=8,
    estimated_minutes=20,
    priority=2,
    energy="Low",
)


EXACT_TASK_SPECS: dict[str, RoadmapTaskSpec] = {
    "Explain one completed SQL solution aloud": RoadmapTaskSpec(
        key="explain_sql_solution",
        description=(
            "Practice explaining a completed SQL solution as though an interviewer "
            "asked you to walk through your reasoning."
        ),
        definition_of_done=(
            "Choose one completed interview problem, explain the problem, result "
            "grain, approach, key clauses, validation, and one alternative; then "
            "record brief notes on what was unclear."
        ),
        starter_path="roadmap_starters/sql_solution_explanation.md",
        category="General",
        destination=6,
        estimated_minutes=25,
        priority=2,
    ),
    "Add Project 1 to the résumé": RoadmapTaskSpec(
        key="project_1_resume_entry",
        description=(
            "Turn Project 1 into a concise résumé entry that communicates the "
            "business problem, analytical work, tools, and measurable result."
        ),
        definition_of_done=(
            "Draft a project title, one-line context statement, and two or three "
            "impact-focused bullets; verify every claim against the project files; "
            "and save the approved wording in the résumé source document."
        ),
        starter_path="roadmap_starters/project_resume_entry.md",
        category="General",
        destination=6,
        estimated_minutes=40,
        priority=2,
    ),
    "Draft a Project 1 interview walkthrough": RoadmapTaskSpec(
        key="project_1_interview_walkthrough",
        description=(
            "Prepare a structured explanation of Project 1 that can be delivered in "
            "a screening or technical interview."
        ),
        definition_of_done=(
            "Write a two-minute overview plus detailed notes for the problem, data, "
            "method, validation, findings, recommendation, limitation, and one "
            "follow-up question; rehearse it once aloud."
        ),
        starter_path="roadmap_starters/project_interview_walkthrough.md",
        category="General",
        destination=6,
        estimated_minutes=45,
        priority=2,
    ),
    "Update LinkedIn project evidence": RoadmapTaskSpec(
        key="linkedin_project_evidence",
        description=(
            "Add Project 1 to LinkedIn in a way that makes the analytical work easy "
            "for recruiters and hiring managers to understand."
        ),
        definition_of_done=(
            "Create or update the project entry, include the problem, tools, outcome, "
            "repository link, and a strong visual; then review the public profile for "
            "clarity and broken links."
        ),
        starter_path="roadmap_starters/linkedin_project_update.md",
        category="General",
        destination=6,
        estimated_minutes=35,
        priority=2,
    ),
    "Draft a Project 2 résumé bullet": RoadmapTaskSpec(
        key="project_2_resume_entry",
        description=(
            "Create evidence-based résumé wording for Project 2 without repeating the "
            "same value proposition as Project 1."
        ),
        definition_of_done=(
            "Draft two or three bullets that emphasize the distinct business problem, "
            "methods, and result; verify the claims; and save the final wording in the "
            "résumé source document."
        ),
        starter_path="roadmap_starters/project_resume_entry.md",
        category="General",
        destination=6,
        estimated_minutes=35,
        priority=2,
    ),
    "Practice two project interview answers": RoadmapTaskSpec(
        key="project_interview_practice",
        description=(
            "Rehearse two common project interview questions using concrete examples "
            "from your portfolio."
        ),
        definition_of_done=(
            "Answer two prompts aloud, keep each answer under three minutes, include "
            "specific evidence and validation, and record one improvement for each "
            "answer."
        ),
        starter_path="roadmap_starters/project_interview_practice.md",
        category="General",
        destination=6,
        estimated_minutes=35,
        priority=2,
    ),
    "Review the portfolio for missing evidence": RoadmapTaskSpec(
        key="portfolio_evidence_audit",
        description=(
            "Audit the portfolio for missing proof, unclear claims, broken links, and "
            "skills that are asserted without a concrete artifact."
        ),
        definition_of_done=(
            "Review each project against the checklist, identify every missing or weak "
            "artifact, assign an owner and next action, and resolve all high-priority "
            "gaps or schedule them explicitly."
        ),
        starter_path="roadmap_starters/portfolio_evidence_audit.md",
        category="General",
        destination=6,
        estimated_minutes=45,
        priority=2,
    ),
    "Polish Project 1 and Project 2 repositories": RoadmapTaskSpec(
        key="portfolio_repository_polish",
        description=(
            "Perform a final employer-facing quality pass on the first two project "
            "repositories."
        ),
        definition_of_done=(
            "Confirm both repositories open cleanly, explain the business problem, "
            "include reproducible setup steps, contain final visuals and artifacts, "
            "and have no broken links, placeholders, or private files."
        ),
        starter_path="roadmap_starters/repository_polish_checklist.md",
        category="General",
        destination=6,
        estimated_minutes=60,
        priority=1,
    ),
    "Finalize the data-analyst résumé": RoadmapTaskSpec(
        key="finalize_resume",
        description=(
            "Complete a targeted, evidence-based résumé for junior data analyst roles."
        ),
        definition_of_done=(
            "Resolve every checklist item, verify dates and claims, include the strongest "
            "projects and tools, remove placeholders, export a clean PDF, and save the "
            "editable source and version name."
        ),
        starter_path="roadmap_starters/resume_final_review.md",
        category="General",
        destination=6,
        estimated_minutes=75,
        priority=1,
        energy="High",
    ),
    "Finalize the LinkedIn profile": RoadmapTaskSpec(
        key="finalize_linkedin",
        description=(
            "Complete an employer-facing LinkedIn profile aligned with the résumé and "
            "portfolio."
        ),
        definition_of_done=(
            "Update the headline, About section, experience, skills, featured projects, "
            "location and job preferences; verify all links; and review the public view."
        ),
        starter_path="roadmap_starters/linkedin_final_review.md",
        category="General",
        destination=6,
        estimated_minutes=60,
        priority=1,
    ),
    "Prepare five STAR stories": RoadmapTaskSpec(
        key="star_story_bank",
        description=(
            "Build a reusable bank of five concise STAR stories for behavioral interviews."
        ),
        definition_of_done=(
            "Document five distinct stories covering leadership, conflict, ambiguity, "
            "failure or learning, and analytical impact; quantify results where possible; "
            "and rehearse each story aloud."
        ),
        starter_path="roadmap_starters/star_story_bank.md",
        category="General",
        destination=6,
        estimated_minutes=75,
        priority=1,
        energy="High",
    ),
    "Create a reusable application tracking workflow": RoadmapTaskSpec(
        key="application_tracking_workflow",
        description=(
            "Set up a repeatable process for finding, tailoring, submitting, and following "
            "up on job applications."
        ),
        definition_of_done=(
            "Define the workflow stages, required fields, naming conventions, weekly cadence, "
            "follow-up rules, and review routine; then create the first usable tracker or "
            "confirm the Applications CRM contains every required field."
        ),
        starter_path="roadmap_starters/application_tracking_workflow.md",
        category="General",
        destination=7,
        estimated_minutes=45,
        priority=1,
    ),
    "Submit the first targeted applications": RoadmapTaskSpec(
        key="first_targeted_applications",
        description=(
            "Submit the first small batch of carefully selected applications using tailored "
            "materials rather than a high-volume generic approach."
        ),
        definition_of_done=(
            "Select at least three suitable roles, tailor the résumé or supporting note for "
            "each, submit the applications, and record every role, source, date, status, and "
            "follow-up date in the Applications CRM."
        ),
        starter_path="roadmap_starters/targeted_application_batch.md",
        category="General",
        destination=7,
        estimated_minutes=90,
        priority=1,
        energy="High",
    ),
    "Schedule follow-up dates": RoadmapTaskSpec(
        key="application_followups",
        description=(
            "Create realistic follow-up dates and actions for active applications."
        ),
        definition_of_done=(
            "Every submitted application has a next-review or follow-up date, the planned "
            "action is documented, duplicate or closed entries are cleaned up, and urgent "
            "follow-ups are scheduled."
        ),
        starter_path="roadmap_starters/application_followups.md",
        category="General",
        destination=7,
        estimated_minutes=25,
        priority=2,
        energy="Low",
    ),
    "Complete the 90-day retrospective": RoadmapTaskSpec(
        key="program_retrospective",
        description=(
            "Review the full program, document measurable progress, identify remaining gaps, "
            "and define the next 30-day plan."
        ),
        definition_of_done=(
            "Summarize completed learning and projects, compare results with the original goals, "
            "identify strengths and gaps, record the strongest evidence, and create a dated "
            "30-day continuation plan with weekly outcomes."
        ),
        starter_path="roadmap_starters/program_retrospective.md",
        category="Review",
        destination=8,
        estimated_minutes=60,
        priority=1,
    ),
}


_WEEKLY_RETROSPECTIVE_PATTERN = re.compile(r"^Complete the Week (\d+) retrospective$", re.IGNORECASE)


def task_spec(label: str) -> RoadmapTaskSpec | None:
    text = str(label or "").strip()
    if _WEEKLY_RETROSPECTIVE_PATTERN.match(text):
        return _WEEKLY_RETROSPECTIVE
    return EXACT_TASK_SPECS.get(text)


def task_key(label: str) -> str | None:
    spec = task_spec(label)
    if spec is None:
        return None
    match = _WEEKLY_RETROSPECTIVE_PATTERN.match(str(label or "").strip())
    if match:
        return f"weekly_retrospective_{int(match.group(1)):02d}"
    return spec.key


def interview_task_label(label: str) -> bool:
    text = str(label or "").strip().casefold()
    markers = (
        "interview walkthrough",
        "interview answer",
        "star stories",
        "explain one completed sql solution aloud",
    )
    return any(marker in text for marker in markers)
