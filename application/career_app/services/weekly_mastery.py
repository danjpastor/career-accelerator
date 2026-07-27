from __future__ import annotations

"""Weekly mastery gates shared by the planner and Accelerator Academy.

The 90-day program uses one eight-question knowledge check for each of the
12 sprint weeks. A check becomes available only after that week's required work
and all earlier catch-up work are complete. Passing the previous week's check
unlocks new skill-dependent work in the next sprint without blocking Google
Certificate work, review, or the rest of the application.
"""

from dataclasses import dataclass
import re
import sqlite3


WEEKLY_KNOWLEDGE_CHECKS: tuple[tuple[int, str, str], ...] = tuple(
    (
        week,
        {
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
        }[week],
        f"Week {week} Knowledge Check",
    )
    for week in range(1, 13)
)

_BY_ID = {assessment_id: (week, title) for week, assessment_id, title in WEEKLY_KNOWLEDGE_CHECKS}
_BY_WEEK = {week: (assessment_id, title) for week, assessment_id, title in WEEKLY_KNOWLEDGE_CHECKS}


@dataclass(frozen=True)
class GateResult:
    ready: bool
    missing: tuple[str, ...] = ()
    reason: str = ""

    def as_dict(self) -> dict:
        return {"ready": self.ready, "missing": list(self.missing), "reason": self.reason}


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def knowledge_check_week(assessment_id: str) -> int | None:
    item = _BY_ID.get(str(assessment_id))
    return int(item[0]) if item else None


def knowledge_check_id(week: int) -> str | None:
    item = _BY_WEEK.get(int(week))
    return str(item[0]) if item else None


def knowledge_check_title(week_or_id: int | str) -> str:
    if isinstance(week_or_id, int) or str(week_or_id).isdigit():
        week = int(week_or_id)
        return _BY_WEEK.get(week, ("", f"Week {week} Knowledge Check"))[1]
    item = _BY_ID.get(str(week_or_id))
    return item[1] if item else str(week_or_id).replace("_", " ").title()


def assessment_passed(conn: sqlite3.Connection, assessment_id: str) -> bool:
    if not _table_exists(conn, "academy_assessment_attempts"):
        return False
    return conn.execute(
        """SELECT 1 FROM academy_assessment_attempts
           WHERE assessment_id=? AND passed=1 AND COALESCE(solution_assisted,0)=0
           LIMIT 1""",
        (str(assessment_id),),
    ).fetchone() is not None


def previous_week_gate(conn: sqlite3.Connection, target_week: int) -> GateResult:
    target_week = max(1, int(target_week))
    if target_week <= 1:
        return GateResult(True)
    prior_id = knowledge_check_id(target_week - 1)
    if prior_id and assessment_passed(conn, prior_id):
        return GateResult(True)
    title = knowledge_check_title(target_week - 1)
    return GateResult(False, (title,), f"Pass {title} before starting new Week {target_week} skill work.")


def _effective_due_week(row: sqlite3.Row) -> int:
    try:
        due = row["due_week"]
    except (IndexError, KeyError):
        due = None
    return int(due if due is not None else row["week"])


def _is_optional(label: str, managed_key: str) -> bool:
    text = f"{label} {managed_key}".casefold()
    return any(token in text for token in ("optional", "bonus", "stretch goal"))


def _is_post_check_review(label: str, managed_key: str, category: str) -> bool:
    """Return True for retrospectives that intentionally follow the quiz."""
    text = f"{label} {managed_key} {category}".casefold()
    return (
        managed_key.casefold().startswith("weekly_retrospective_")
        or "retrospective" in text
        or category.casefold() == "review"
    )


def _is_current_check_task(row: sqlite3.Row, assessment_id: str, week: int) -> bool:
    target = str(row["target_key"] or "")
    managed = str(row["managed_key"] or "")
    label = str(row["label"] or "")
    return (
        target == f"academy:assessment:{assessment_id}"
        or managed.endswith(f"assessment:{assessment_id}")
        or label.casefold() == knowledge_check_title(week).casefold()
    )


def incomplete_required_tasks(
    conn: sqlite3.Connection,
    week: int,
    assessment_id: str,
) -> list[dict]:
    """Return incomplete active tasks due no later than the check's week.

    The check's own adaptive dashboard row is excluded to avoid a circular
    prerequisite. Retired/archived, optional, and future tasks do not block it.
    """
    if not _table_exists(conn, "sprint_tasks"):
        return []
    has_metadata = _table_exists(conn, "task_metadata")
    has_tracks = _table_exists(conn, "track_tasks")
    has_requirements = _table_exists(conn, "roadmap_requirement_state")
    metadata_join = "LEFT JOIN task_metadata m ON m.task_id=s.id" if has_metadata else "LEFT JOIN (SELECT NULL task_id,NULL managed_key,NULL status,NULL category) m ON 1=0"
    track_join = "LEFT JOIN track_tasks tt ON tt.task_id=s.id" if has_tracks else "LEFT JOIN (SELECT NULL task_id,NULL target_key) tt ON 1=0"
    requirement_join = (
        "LEFT JOIN roadmap_requirement_state r ON m.managed_key=('roadmap_v1026:' || r.requirement_key)"
        if has_requirements
        else "LEFT JOIN (SELECT NULL requirement_key,NULL due_week,NULL status) r ON 1=0"
    )
    rows = conn.execute(
        f"""SELECT s.id,s.week,s.label,s.completed,
                    m.managed_key,m.status AS metadata_status,m.category,
                    tt.track_key,tt.target_key,r.due_week,r.status AS requirement_status
               FROM sprint_tasks s
               {metadata_join}
               {track_join}
               {requirement_join}
              WHERE COALESCE(s.completed,0)=0
              ORDER BY COALESCE(r.due_week,s.week),s.sort_order,s.id"""
    ).fetchall()
    blockers: list[dict] = []
    for row in rows:
        due_week = _effective_due_week(row)
        if due_week > int(week):
            continue
        label = str(row["label"] or "").strip()
        managed = str(row["managed_key"] or "")
        category = str(row["category"] or "")
        # The Academy owns one reusable adaptive planner row. Course traversal
        # already proves its lesson/lab prerequisites; counting that stale row
        # here would make the knowledge check block itself for one refresh.
        if str(row["track_key"] or "").casefold() == "academy":
            continue
        # Static Academy rows from pre-overhaul builds are not coursework
        # records. Lesson mastery is read from Academy progress, so these rows
        # must never create an invisible prerequisite even before cleanup runs.
        if managed.startswith("roadmap_v1026:lesson:"):
            continue
        if managed.startswith("roadmap_v1026:assessment:"):
            assessment_key = managed.split("roadmap_v1026:assessment:", 1)[1]
            if assessment_key not in _BY_ID:
                continue
        if _is_optional(label, managed):
            continue
        if _is_post_check_review(label, managed, category):
            continue
        if _is_current_check_task(row, assessment_id, int(week)):
            continue
        if str(row["requirement_status"] or "").casefold() == "completed":
            continue
        # Rows retired by a migration are completed or removed. A leftover row
        # explicitly marked archived/retired must never block a current check.
        if str(row["metadata_status"] or "").casefold() in {"archived", "retired"}:
            continue
        blockers.append(
            {
                "task_id": int(row["id"]),
                "label": label or f"Task {row['id']}",
                "due_week": due_week,
                "catch_up": due_week < int(week),
            }
        )
    return blockers


def knowledge_check_readiness(
    conn: sqlite3.Connection,
    assessment_id: str,
) -> GateResult:
    week = knowledge_check_week(assessment_id)
    if week is None:
        return GateResult(True)
    if assessment_passed(conn, assessment_id):
        return GateResult(True)

    missing: list[str] = []
    prior = previous_week_gate(conn, week)
    if not prior.ready:
        missing.extend(prior.missing)

    blockers = incomplete_required_tasks(conn, week, assessment_id)
    catchup = [item for item in blockers if item["catch_up"]]
    current = [item for item in blockers if not item["catch_up"]]
    if catchup:
        missing.append(
            "Catch-up work: " + ", ".join(item["label"] for item in catchup[:3])
            + ("…" if len(catchup) > 3 else "")
        )
    if current:
        missing.append(
            f"Week {week} tasks: " + ", ".join(item["label"] for item in current[:3])
            + ("…" if len(current) > 3 else "")
        )
    if not missing:
        return GateResult(True)
    return GateResult(
        False,
        tuple(missing),
        "Complete every required task through Week " + str(week) + " before taking this knowledge check.",
    )


def task_progression_gate(
    conn: sqlite3.Connection,
    *,
    task_week: int,
    current_week: int,
    kind: str,
) -> GateResult:
    """Gate new current/future skill work behind the prior week's check."""
    task_week = max(1, int(task_week))
    current_week = max(1, int(current_week))
    kind = str(kind or "general")
    if task_week < current_week:
        return GateResult(True)  # catch-up must remain available
    if kind in {"google", "review", "career_readiness"}:
        return GateResult(True)
    gate = previous_week_gate(conn, task_week)
    return gate


def audit_weekly_check_definitions(catalog) -> list[str]:
    """Return human-readable curriculum defects for release validation."""
    assessments = {item.assessment_id: item for item in catalog.assessments()}
    issues: list[str] = []
    for week, assessment_id, expected_title in WEEKLY_KNOWLEDGE_CHECKS:
        assessment = assessments.get(assessment_id)
        if assessment is None:
            issues.append(f"Missing {expected_title} ({assessment_id}).")
            continue
        if assessment.title != expected_title:
            issues.append(f"{assessment_id} title is {assessment.title!r}, expected {expected_title!r}.")
        if len(assessment.activities) != 8:
            issues.append(f"{expected_title} has {len(assessment.activities)} questions instead of 8.")
        if abs(float(assessment.passing_score) - 0.8) > 1e-9:
            issues.append(f"{expected_title} passing score is not 80%.")
        for activity in assessment.activities:
            if activity.runtime != "recognition":
                issues.append(f"{expected_title}: {activity.title} is not multiple choice.")
            if len(activity.answer_options) != 4:
                issues.append(f"{expected_title}: {activity.title} does not have four options.")
            if not str(activity.presentation.get("review_recommendation") or "").strip():
                issues.append(f"{expected_title}: {activity.title} lacks a review recommendation.")
    return issues
