from __future__ import annotations

"""Standalone weekly eight-question knowledge checks.

This replaces the retired Academy assessment dependency while preserving the
program's original weekly mastery contract: one eight-question multiple-choice
check per week, seven correct answers required to pass, graded review after
failed attempts, and progression gates for later skill work.
"""

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
from typing import Any

import yaml

from career_app.navigation import PAGE_LEARNING

CHECKS: tuple[tuple[int, str, str], ...] = tuple(
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

_BY_WEEK = {week: (assessment_id, title) for week, assessment_id, title in CHECKS}
_BY_ID = {assessment_id: (week, title) for week, assessment_id, title in CHECKS}
_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "weekly_checks"


@dataclass(frozen=True)
class GateResult:
    ready: bool
    missing: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class AttemptResult:
    week: int
    score: int
    total: int
    passed: bool
    attempt_number: int
    review: tuple[dict[str, Any], ...]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS weekly_check_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week INTEGER NOT NULL,
            assessment_id TEXT NOT NULL,
            attempt_number INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            passed INTEGER NOT NULL DEFAULT 0,
            answers_json TEXT NOT NULL,
            review_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(week, attempt_number)
        );
        CREATE TABLE IF NOT EXISTS weekly_check_progress (
            week INTEGER PRIMARY KEY,
            assessment_id TEXT NOT NULL,
            best_score INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            passed INTEGER NOT NULL DEFAULT 0,
            passed_at TEXT
        );
        """
    )


def assessment_id(week: int) -> str:
    return _BY_WEEK[int(week)][0]


def title(week: int) -> str:
    return _BY_WEEK[int(week)][1]


def week_for_assessment(value: str) -> int | None:
    row = _BY_ID.get(str(value or ""))
    return int(row[0]) if row else None


def managed_key(week: int) -> str:
    return f"weekly_check:{int(week)}"


def target_key(week: int) -> str:
    return f"weekly_check:{int(week)}"


def week_from_task(task: dict[str, Any]) -> int | None:
    kind = str(task.get("kind") or "")
    if kind == "weekly_check":
        return int(task.get("week") or 0) or None
    for value in (task.get("managed_key"), task.get("target_key")):
        match = re.fullmatch(r"weekly_check:(\d{1,2})", str(value or ""))
        if match:
            return int(match.group(1))
    label = str(task.get("label") or "")
    match = re.fullmatch(r"Week\s+(\d{1,2})\s+Knowledge\s+Check", label, re.I)
    return int(match.group(1)) if match else None


def definition(week: int) -> dict[str, Any]:
    week = int(week)
    candidates = sorted(_DATA_DIR.glob(f"week_{week}_*.yaml"))
    if not candidates:
        raise FileNotFoundError(f"Weekly check definition missing for Week {week}.")
    data = yaml.safe_load(candidates[0].read_text(encoding="utf-8")) or {}
    activities = list(data.get("activities") or [])
    if len(activities) != 8:
        raise ValueError(f"Week {week} Knowledge Check must contain exactly 8 questions.")
    for activity in activities:
        options = list(activity.get("answer_options") or [])
        if len(options) != 4:
            raise ValueError(f"{activity.get('title', 'Question')} must have four answer options.")
        activity.setdefault("presentation", {})
        activity["presentation"].setdefault(
            "review_recommendation",
            f"Review the Week {week} coursework connected to {activity.get('title', 'this topic')}.",
        )
    data["activities"] = activities
    data["passing_count"] = 7
    return data


def _repair_progress_from_attempts(conn: sqlite3.Connection) -> int:
    """Repair durable weekly progress from the authoritative attempt history.

    Earlier builds could save a passing attempt while leaving the summary row or
    linked sprint task incomplete.  The attempt table is append-only, so any
    attempt with at least 7 of 8 correct is sufficient proof that the weekly
    check was passed.  This repair is idempotent and preserves the best score,
    attempt count, and earliest known pass time.
    """
    ensure_schema(conn)
    rows = conn.execute(
        """SELECT week,
                  MAX(score) AS best_score,
                  COUNT(*) AS attempt_count,
                  MAX(CASE WHEN passed=1 OR score>=7 THEN 1 ELSE 0 END) AS has_pass,
                  MIN(CASE WHEN passed=1 OR score>=7 THEN created_at END) AS first_passed_at
             FROM weekly_check_attempts
            GROUP BY week"""
    ).fetchall()
    repaired = 0
    for row in rows:
        week = int(row["week"])
        existing = conn.execute(
            "SELECT best_score,attempts,passed,passed_at FROM weekly_check_progress WHERE week=?",
            (week,),
        ).fetchone()
        best_score = max(
            int(row["best_score"] or 0),
            int(existing["best_score"] if existing else 0),
        )
        attempts = max(
            int(row["attempt_count"] or 0),
            int(existing["attempts"] if existing else 0),
        )
        final_passed = bool(row["has_pass"]) or bool(existing and existing["passed"])
        passed_at = (
            str(existing["passed_at"])
            if existing and existing["passed_at"]
            else (str(row["first_passed_at"]) if row["first_passed_at"] else None)
        )
        before = (
            int(existing["best_score"]),
            int(existing["attempts"]),
            int(existing["passed"]),
            str(existing["passed_at"] or ""),
        ) if existing else None
        after = (best_score, attempts, 1 if final_passed else 0, str(passed_at or ""))
        conn.execute(
            """INSERT INTO weekly_check_progress(week,assessment_id,best_score,attempts,passed,passed_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(week) DO UPDATE SET
                   assessment_id=excluded.assessment_id,
                   best_score=MAX(weekly_check_progress.best_score,excluded.best_score),
                   attempts=MAX(weekly_check_progress.attempts,excluded.attempts),
                   passed=MAX(weekly_check_progress.passed,excluded.passed),
                   passed_at=CASE
                       WHEN weekly_check_progress.passed_at IS NULL THEN excluded.passed_at
                       WHEN excluded.passed_at IS NULL THEN weekly_check_progress.passed_at
                       WHEN excluded.passed_at < weekly_check_progress.passed_at THEN excluded.passed_at
                       ELSE weekly_check_progress.passed_at
                   END""",
            (week, assessment_id(week), best_score, attempts, 1 if final_passed else 0, passed_at),
        )
        if before != after:
            repaired += 1
    return repaired


def passed(conn: sqlite3.Connection, week: int) -> bool:
    ensure_schema(conn)
    row = conn.execute(
        "SELECT passed FROM weekly_check_progress WHERE week=?", (int(week),)
    ).fetchone()
    if row and row["passed"]:
        return True
    # Fall back to the immutable attempt history so a previously passed quiz can
    # never be reported as incomplete because its summary row was missed.
    attempt = conn.execute(
        """SELECT 1 FROM weekly_check_attempts
            WHERE week=? AND (passed=1 OR score>=7) LIMIT 1""",
        (int(week),),
    ).fetchone()
    return attempt is not None


def _is_optional(label: str, managed: str) -> bool:
    text = f"{label} {managed}".casefold()
    return any(token in text for token in ("optional", "bonus", "stretch goal"))


def _is_post_check_review(label: str, managed: str, category: str) -> bool:
    text = f"{label} {managed} {category}".casefold()
    return (
        "retrospective" in text
        or managed.casefold().startswith("weekly_retrospective_")
        or category.casefold() == "review"
    )


def incomplete_required_tasks(conn: sqlite3.Connection, week: int) -> list[dict[str, Any]]:
    if not _table_exists(conn, "sprint_tasks"):
        return []
    rows = conn.execute(
        """SELECT s.id,s.week,s.label,s.completed,
                  COALESCE(m.managed_key,'') AS managed_key,
                  COALESCE(m.status,'') AS metadata_status,
                  COALESCE(m.category,'') AS category
             FROM sprint_tasks s
             LEFT JOIN task_metadata m ON m.task_id=s.id
            WHERE s.week<=? AND COALESCE(s.completed,0)=0
            ORDER BY s.week,s.sort_order,s.id""",
        (int(week),),
    ).fetchall()
    blockers: list[dict[str, Any]] = []
    for row in rows:
        label = str(row["label"] or "").strip()
        managed = str(row["managed_key"] or "")
        category = str(row["category"] or "")
        if managed.startswith("weekly_check:") or re.fullmatch(
            r"Week\s+\d+\s+Knowledge\s+Check", label, re.I
        ):
            continue
        if managed.startswith("roadmap_v1026:assessment:"):
            continue
        if managed.startswith("roadmap_v1026:lesson:"):
            continue
        if _is_optional(label, managed):
            continue
        if _is_post_check_review(label, managed, category):
            continue
        if str(row["metadata_status"] or "").casefold() in {"archived", "retired"}:
            continue
        blockers.append(
            {
                "task_id": int(row["id"]),
                "label": label or f"Task {row['id']}",
                "week": int(row["week"]),
                "catch_up": int(row["week"]) < int(week),
            }
        )
    return blockers


def readiness(conn: sqlite3.Connection, week: int) -> GateResult:
    week = int(week)
    if passed(conn, week):
        return GateResult(True)
    state = conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone()
    current_week = int(state["current_week"] if state else 1)
    if week > current_week:
        return GateResult(False, (), f"Scheduled for Week {week}.")
    missing: list[str] = []
    if week > 1 and not passed(conn, week - 1):
        missing.append(title(week - 1))
    blockers = incomplete_required_tasks(conn, week)
    if blockers:
        catchup = [item for item in blockers if item["week"] < week]
        current = [item for item in blockers if item["week"] == week]
        if catchup:
            labels = ", ".join(item["label"] for item in catchup[:3])
            missing.append("Catch-up work: " + labels + ("…" if len(catchup) > 3 else ""))
        if current:
            labels = ", ".join(item["label"] for item in current[:3])
            missing.append(f"Week {week} tasks: " + labels + ("…" if len(current) > 3 else ""))
    if missing:
        return GateResult(
            False,
            tuple(missing),
            f"Complete all Week {week} coursework and earlier catch-up work before taking this check.",
        )
    return GateResult(True)


def progression_gate(
    conn: sqlite3.Connection,
    *,
    task_week: int,
    current_week: int,
    kind: str,
) -> GateResult:
    task_week = max(1, int(task_week))
    current_week = max(1, int(current_week))
    kind = str(kind or "general")
    if task_week < current_week:
        return GateResult(True)
    if kind in {"google", "review", "career_readiness", "weekly_check"}:
        return GateResult(True)
    if task_week <= 1 or passed(conn, task_week - 1):
        return GateResult(True)
    prior = title(task_week - 1)
    return GateResult(
        False,
        (prior,),
        f"Pass {prior} before starting new Week {task_week} skill work.",
    )


def task_id_for_week(conn: sqlite3.Connection, week: int) -> int | None:
    row = conn.execute(
        """SELECT s.id
             FROM sprint_tasks s
             LEFT JOIN task_metadata m ON m.task_id=s.id
            WHERE m.managed_key=? OR LOWER(s.label)=LOWER(?)
            ORDER BY s.id LIMIT 1""",
        (managed_key(week), title(week)),
    ).fetchone()
    return int(row["id"]) if row else None


def reconcile(conn: sqlite3.Connection) -> dict[str, int]:
    ensure_schema(conn)
    repaired = _repair_progress_from_attempts(conn)
    created = updated = 0
    state = conn.execute("SELECT current_week FROM program_state WHERE id=1").fetchone()
    current_week = int(state["current_week"] if state else 1)
    for week, check_id, check_title in CHECKS:
        task_id = task_id_for_week(conn, week)
        complete = passed(conn, week)
        gate = readiness(conn, week)
        if task_id is None:
            sort_order = 11
            occupied = conn.execute(
                "SELECT 1 FROM sprint_tasks WHERE week=? AND sort_order=?", (week, sort_order)
            ).fetchone()
            while occupied:
                sort_order -= 1
                occupied = conn.execute(
                    "SELECT 1 FROM sprint_tasks WHERE week=? AND sort_order=?", (week, sort_order)
                ).fetchone()
            cursor = conn.execute(
                "INSERT INTO sprint_tasks(week,sort_order,label,completed) VALUES(?,?,?,?)",
                (week, sort_order, check_title, 1 if complete else 0),
            )
            task_id = int(cursor.lastrowid)
            created += 1
        else:
            conn.execute(
                "UPDATE sprint_tasks SET week=?,label=?,completed=? WHERE id=?",
                (week, check_title, 1 if complete else 0, task_id),
            )
            updated += 1
        status = "Completed" if complete else "Not Started"
        prereq_state = "Ready" if gate.ready else "Locked"
        prereq_reason = None if gate.ready else gate.reason
        conn.execute(
            """INSERT INTO task_metadata(
                   task_id,status,priority,estimated_minutes,energy,deferred_until,
                   destination,category,prerequisite_state,prerequisite_reason,
                   description,definition_of_done,starter_path,managed_key
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(task_id) DO UPDATE SET
                   status=excluded.status,
                   priority=excluded.priority,
                   estimated_minutes=excluded.estimated_minutes,
                   energy=excluded.energy,
                   deferred_until=NULL,
                   destination=excluded.destination,
                   category=excluded.category,
                   prerequisite_state=excluded.prerequisite_state,
                   prerequisite_reason=excluded.prerequisite_reason,
                   description=excluded.description,
                   definition_of_done=excluded.definition_of_done,
                   starter_path=excluded.starter_path,
                   managed_key=excluded.managed_key""",
            (
                task_id,
                status,
                1,
                25,
                "Normal",
                None,
                PAGE_LEARNING,
                "Assessment",
                prereq_state,
                prereq_reason,
                "Answer all eight multiple-choice questions independently.",
                "Score at least 7 of 8. Review missed questions and retake until passed.",
                target_key(week),
                managed_key(week),
            ),
        )
        # Remove stale Academy/track routing for the same durable task.
        conn.execute("DELETE FROM track_tasks WHERE task_id=?", (task_id,))
    conn.commit()
    return {
        "created": created,
        "updated": updated,
        "repaired_progress": repaired,
        "current_week": current_week,
    }


def record_attempt(
    conn: sqlite3.Connection,
    week: int,
    answers: dict[str, str],
) -> AttemptResult:
    week = int(week)
    ensure_schema(conn)
    check = definition(week)
    review: list[dict[str, Any]] = []
    score = 0
    normalized_answers = {str(key): str(value or "") for key, value in answers.items()}
    for index, item in enumerate(check["activities"], start=1):
        activity_id = str(item["activity_id"])
        selected = normalized_answers.get(activity_id, "").strip()
        correct = str(item.get("solution") or item.get("validator", {}).get("expected_answer") or "").strip()
        is_correct = selected == correct
        score += int(is_correct)
        review.append(
            {
                "number": index,
                "activity_id": activity_id,
                "title": str(item.get("title") or f"Question {index}"),
                "prompt": str(item.get("prompt") or ""),
                "selected": selected or "Not answered",
                "correct": correct,
                "passed": is_correct,
                "recommendation": str(
                    item.get("presentation", {}).get("review_recommendation")
                    or f"Review the Week {week} coursework for this topic."
                ),
            }
        )
    total = 8
    passed_now = score >= 7
    row = conn.execute(
        "SELECT COALESCE(MAX(attempt_number),0)+1 AS n FROM weekly_check_attempts WHERE week=?",
        (week,),
    ).fetchone()
    attempt_number = int(row["n"] if row else 1)
    conn.execute(
        """INSERT INTO weekly_check_attempts(
               week,assessment_id,attempt_number,score,total,passed,
               answers_json,review_json,created_at
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            week,
            assessment_id(week),
            attempt_number,
            score,
            total,
            1 if passed_now else 0,
            json.dumps(normalized_answers, sort_keys=True),
            json.dumps(review, sort_keys=True),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    existing = conn.execute(
        "SELECT best_score,attempts,passed,passed_at FROM weekly_check_progress WHERE week=?",
        (week,),
    ).fetchone()
    best = max(score, int(existing["best_score"] if existing else 0))
    attempts = int(existing["attempts"] if existing else 0) + 1
    already_passed = bool(existing and existing["passed"])
    final_passed = already_passed or passed_now
    passed_at = (
        str(existing["passed_at"])
        if existing and existing["passed_at"]
        else (datetime.now().isoformat(timespec="seconds") if passed_now else None)
    )
    conn.execute(
        """INSERT INTO weekly_check_progress(week,assessment_id,best_score,attempts,passed,passed_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(week) DO UPDATE SET
               assessment_id=excluded.assessment_id,
               best_score=excluded.best_score,
               attempts=excluded.attempts,
               passed=excluded.passed,
               passed_at=excluded.passed_at""",
        (week, assessment_id(week), best, attempts, 1 if final_passed else 0, passed_at),
    )
    task_id = task_id_for_week(conn, week)
    if task_id is not None and final_passed:
        conn.execute("UPDATE sprint_tasks SET completed=1 WHERE id=?", (task_id,))
        conn.execute(
            """UPDATE task_metadata
                  SET status='Completed',prerequisite_state='Ready',prerequisite_reason=NULL
                WHERE task_id=?""",
            (task_id,),
        )
    reconcile(conn)
    conn.commit()
    return AttemptResult(
        week=week,
        score=score,
        total=total,
        passed=passed_now,
        attempt_number=attempt_number,
        review=tuple(review),
    )


def latest_attempt(conn: sqlite3.Connection, week: int) -> dict[str, Any] | None:
    ensure_schema(conn)
    row = conn.execute(
        """SELECT * FROM weekly_check_attempts
            WHERE week=? ORDER BY attempt_number DESC LIMIT 1""",
        (int(week),),
    ).fetchone()
    if row is None:
        return None
    result = {key: row[key] for key in row.keys()}
    result["answers"] = json.loads(str(row["answers_json"] or "{}"))
    result["review"] = json.loads(str(row["review_json"] or "[]"))
    return result


def ready_unpassed_weeks(conn: sqlite3.Connection, current_week: int) -> list[int]:
    weeks: list[int] = []
    for week in range(1, min(12, int(current_week)) + 1):
        if not passed(conn, week) and readiness(conn, week).ready:
            weeks.append(week)
    return weeks


def audit_definitions() -> list[str]:
    issues: list[str] = []
    for week, expected_id, expected_title in CHECKS:
        try:
            check = definition(week)
        except Exception as exc:
            issues.append(str(exc))
            continue
        if str(check.get("assessment_id")) != expected_id:
            issues.append(f"Week {week} assessment_id does not match {expected_id}.")
        if str(check.get("title")) != expected_title:
            issues.append(f"Week {week} title does not match {expected_title}.")
        activities = list(check.get("activities") or [])
        if len(activities) != 8:
            issues.append(f"Week {week} has {len(activities)} questions instead of 8.")
        for index, activity in enumerate(activities, start=1):
            if str(activity.get("runtime")) != "recognition":
                issues.append(f"Week {week} question {index} is not multiple choice.")
            if len(activity.get("answer_options") or []) != 4:
                issues.append(f"Week {week} question {index} does not have four options.")
            if not str(activity.get("presentation", {}).get("review_recommendation") or "").strip():
                issues.append(f"Week {week} question {index} lacks a review recommendation.")
    return issues
