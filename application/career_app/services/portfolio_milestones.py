"""Canonical portfolio milestones and non-destructive legacy migration.

The old portfolio catalog mixed true stage gates with minor implementation
steps. This service consolidates those rows into a stable set of meaningful
milestones while retaining the original records in an archive table.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable


MIGRATION_VERSION = "true-milestones-v1"
MANAGED_PREFIX = "milestone:"


@dataclass(frozen=True)
class Milestone:
    key: str
    label: str
    stage: str
    minutes: int
    description: str
    definition_of_done: str
    component_aliases: tuple[str, ...]
    completion_aliases: tuple[str, ...] = ()
    completion_rule: str = "all"
    auto_artifact: str = ""


MILESTONES: tuple[Milestone, ...] = (
    Milestone(
        "project_brief",
        "Review and approve project brief",
        "Discovery",
        45,
        (
            "Review the project plan and make sure the problem, audience, "
            "questions, scope, deliverables, and success criteria all fit together."
        ),
        (
            "The approved brief clearly explains who the project is for, what "
            "decision it supports, what it will answer, and what success looks like."
        ),
        (
            "finalize business problem",
            "finalise business problem",
            "define business problem",
            "finalize stakeholder",
            "finalise stakeholder",
            "identify stakeholder",
            "finalize kpi",
            "finalise kpi",
            "define kpi",
            "finalize business question",
            "finalise business question",
            "define business question",
            "project charter",
        ),
        completion_rule="all",
        auto_artifact="project_brief",
    ),
    Milestone(
        "data_source_spec",
        "Approve data source and specification",
        "Dataset",
        60,
        (
            "Review where the data comes from, what each table represents, "
            "what it covers, and whether it can answer the approved questions."
        ),
        (
            "The source is documented, its limits are clear, and it contains "
            "the information needed for the project."
        ),
        (
            "create synthetic data specification",
            "synthetic dataset specification",
            "data specification",
            "source manifest",
            "approve data source",
        ),
        completion_rule="any",
    ),
    Milestone(
        "raw_dataset",
        "Create or acquire raw dataset",
        "Dataset",
        75,
        (
            "Bring the original data files into the project and record where "
            "they came from without changing them."
        ),
        (
            "Every required raw file is present, unchanged, and listed in the "
            "source manifest."
        ),
        (
            "generate dataset",
            "generate synthetic dataset",
            "source dataset",
            "acquire dataset",
            "create dataset",
            "collect dataset",
        ),
        completion_rule="any",
        auto_artifact="raw_dataset",
    ),
    Milestone(
        "validate_relationships",
        "Validate Relationships",
        "Dataset",
        90,
        (
            "Validate table grain, primary keys, foreign keys, relationship "
            "cardinality, join preservation, and cross-table consistency."
        ),
        (
            "The validation notebook and reports document every relationship as "
            "safe, conditional, or unsafe and identify required cleaning actions."
        ),
        (
            "validate relationships",
            "validate relationship",
            "relationship validation",
            "validate data model",
        ),
        completion_rule="any",
        auto_artifact="relationship_validation",
    ),
    Milestone(
        "data_dictionary_review",
        "Review and finalize data dictionary",
        "Dataset",
        45,
        (
            "Compare the existing data dictionary with the real tables and "
            "finish the definitions, rules, keys, and relationship notes."
        ),
        (
            "Every current field is documented clearly and there are no "
            "unexplained differences between the dictionary and the data."
        ),
        (
            "complete data dictionary",
            "build data dictionary",
            "create data dictionary",
            "finalize data dictionary",
            "finalise data dictionary",
        ),
        completion_rule="any",
    ),
    Milestone(
        "clean_analytical_data",
        "Clean and validate analytical data",
        "Dataset",
        150,
        (
            "Find data-quality problems, choose and apply the right fixes, and "
            "save reviewed cleaned datasets without changing the raw files."
        ),
        (
            "Cleaned outputs are saved, the raw files are untouched, and every "
            "important change has been checked and explained."
        ),
        (
            "clean and validate data",
            "clean validate data",
            "clean data",
            "prepare clean data",
            "data cleaning",
            "document assumptions",
        ),
        (
            "clean and validate data",
            "clean validate data",
            "clean data",
            "data cleaning",
        ),
        completion_rule="any",
    ),
    Milestone(
        "analytical_database",
        "Build reproducible analytical database",
        "SQL",
        120,
        (
            "Write a repeatable script that builds the analytical database from "
            "the reviewed cleaned data."
        ),
        (
            "The database can be rebuilt from the saved script, contains the "
            "expected tables, and passes the final loading checks."
        ),
        (
            "create schema",
            "create sql schema",
            "load data",
            "load dataset",
            "quality checks",
            "data quality checks",
            "run quality checks",
        ),
        completion_rule="all",
    ),
    Milestone(
        "sql_analysis",
        "Complete SQL analysis",
        "SQL",
        180,
        (
            "Write clear SQL that answers the approved business questions and "
            "uses the agreed KPI definitions."
        ),
        (
            "The final queries run cleanly, return the intended results, and "
            "include checks and short interpretations."
        ),
        (
            "write analysis queries",
            "analysis queries",
            "answer business questions with sql",
            "sql analysis",
            "document sql queries",
            "documented queries",
            "create derived metrics",
        ),
        (
            "write analysis queries",
            "analysis queries",
            "answer business questions with sql",
            "sql analysis",
        ),
        completion_rule="any",
    ),
    Milestone(
        "exploratory_analysis",
        "Complete exploratory analysis",
        "Python",
        150,
        (
            "Explore the cleaned data for useful patterns, segments, trends, "
            "and unusual records tied to the project questions."
        ),
        (
            "The notebook runs from top to bottom and clearly separates what "
            "was observed from what still needs to be tested."
        ),
        (
            "perform exploratory analysis",
            "exploratory analysis",
            "explore data",
            "eda",
            "detect anomalies",
            "anomaly detection",
            "document insights",
            "derived metrics",
        ),
        (
            "perform exploratory analysis",
            "exploratory analysis",
            "explore data",
            "eda",
        ),
        completion_rule="any",
    ),
    Milestone(
        "validate_findings",
        "Validate findings across tools",
        "Validation",
        90,
        (
            "Compare the headline numbers across SQL, Python, and Power BI and "
            "work out why any values do not match."
        ),
        (
            "Every number that will be published is confirmed or has a clear "
            "note explaining the mismatch and final decision."
        ),
        (
            "validate findings",
            "validate sql findings",
            "reconcile findings",
            "cross tool validation",
        ),
        completion_rule="any",
    ),
    Milestone(
        "power_bi_model",
        "Build and validate Power BI semantic model",
        "Power BI",
        150,
        (
            "Build the Power BI model, relationships, date table, and measures "
            "needed for the final report."
        ),
        (
            "The model behaves correctly under filters and its headline values "
            "match the approved SQL results."
        ),
        (
            "build power bi model",
            "power bi model",
            "build data model",
            "create dax measures",
            "dax measures",
        ),
        completion_rule="all",
    ),
    Milestone(
        "power_bi_report",
        "Build and test Power BI report",
        "Power BI",
        210,
        (
            "Build and test the Power BI report that the project audience will "
            "actually use."
        ),
        (
            "The report answers the approved questions, shows the correct values, "
            "and works under realistic filter and navigation choices."
        ),
        (
            "build dashboards",
            "build dashboard",
            "create dashboard",
            "executive dashboard",
            "workload dashboard",
            "filters and drillthrough",
            "filters drillthrough",
            "drill-through",
            "drill through",
        ),
        completion_rule="all",
    ),
    Milestone(
        "executive_summary",
        "Write executive summary and recommendations",
        "Communication",
        90,
        (
            "Write a clear summary that connects the strongest findings to "
            "practical recommendations, owners, limits, and next steps."
        ),
        (
            "The summary gives the audience a clear decision, three to five "
            "supported findings, and realistic actions."
        ),
        (
            "write executive summary",
            "executive summary",
            "document assumptions and limitations",
            "assumptions limitations",
            "document insights",
            "write recommendations",
        ),
        (
            "write executive summary",
            "executive summary",
        ),
        completion_rule="any",
    ),
    Milestone(
        "publish_case_study",
        "Publish reproducible portfolio case study",
        "Publication",
        120,
        (
            "Package the finished work into a clear public case study that an "
            "employer can understand and review."
        ),
        (
            "The public project has a complete README, readable visuals, working "
            "links, clear setup notes, and no private or unfinished material."
        ),
        (
            "capture screenshots",
            "screenshots",
            "complete readme",
            "write readme",
            "readme",
            "publish project",
            "publish",
        ),
        (
            "publish project",
            "publish",
        ),
        completion_rule="any",
    ),
)

CANONICAL_BY_KEY = {item.key: item for item in MILESTONES}
CANONICAL_LABELS = {item.label.casefold(): item for item in MILESTONES}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _matches(label: str, aliases: Iterable[str]) -> bool:
    normalized = _normalize(label)
    for alias in aliases:
        candidate = _normalize(alias)
        if not candidate:
            continue
        if normalized == candidate or candidate in normalized or normalized in candidate:
            return True
    return False


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {
        str(row[1])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _project_directory(root: Path, project_id: int) -> Path:
    projects = Path(root) / "projects"
    matches = sorted(projects.glob(f"project-{int(project_id):02d}-*"))
    if matches:
        return matches[0]
    known = {
        1: "project-01-vfx-production-intelligence",
        2: "project-02-retail-operations",
        3: "project-03-movie-industry-financial-analytics",
    }
    return projects / known.get(int(project_id), f"project-{int(project_id):02d}")


def _has_project_brief(project_dir: Path) -> bool:
    parts = []
    for relative in (
        "README.md",
        "PROJECT_CHARTER.md",
        "documentation/project_charter.md",
        "documentation/business_problem.md",
    ):
        path = project_dir / relative
        if path.is_file():
            try:
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    text = "\n".join(parts).casefold()
    required_groups = (
        ("business problem", "problem statement", "business objective"),
        ("stakeholder", "audience"),
        ("kpi", "key performance indicator", "metric"),
        ("business question", "analysis question", "analytical question"),
    )
    return bool(text) and all(any(token in text for token in group) for group in required_groups)


def _has_raw_dataset(project_dir: Path) -> bool:
    raw = project_dir / "data" / "raw"
    return raw.is_dir() and any(path.is_file() for path in raw.rglob("*"))


def _has_relationship_validation(project_dir: Path) -> bool:
    candidates = (
        project_dir / "notebooks" / "validate_relationships.ipynb",
        project_dir / "reports" / "relationship_validation",
    )
    return candidates[0].is_file() or (
        candidates[1].is_dir() and any(path.is_file() for path in candidates[1].rglob("*"))
    )


def _artifact_complete(kind: str, project_dir: Path) -> bool:
    if kind == "project_brief":
        return _has_project_brief(project_dir)
    if kind == "raw_dataset":
        return _has_raw_dataset(project_dir)
    if kind == "relationship_validation":
        return _has_relationship_validation(project_dir)
    return False


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS portfolio_milestone_archive (
            original_task_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            canonical_key TEXT NOT NULL,
            original_label TEXT NOT NULL,
            original_stage TEXT,
            original_completed INTEGER NOT NULL DEFAULT 0,
            original_sort_order INTEGER,
            snapshot_json TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            PRIMARY KEY(original_task_id, project_id)
        );

        CREATE TABLE IF NOT EXISTS portfolio_milestone_components (
            project_id INTEGER NOT NULL,
            canonical_key TEXT NOT NULL,
            original_task_id INTEGER NOT NULL,
            original_label TEXT NOT NULL,
            original_completed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(project_id, canonical_key, original_task_id)
        );

        CREATE TABLE IF NOT EXISTS portfolio_milestone_migrations (
            migration_key TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
        """
    )


def _row_dict(row) -> dict:
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return dict(row)


def _canonical_key_for_legacy(label: str) -> str:
    for milestone in MILESTONES:
        if _matches(label, milestone.component_aliases):
            return milestone.key
    return "optional_history"


def _derived_completed(
    milestone: Milestone,
    legacy_rows: list[dict],
    project_dir: Path,
) -> bool:
    aliases = milestone.completion_aliases or milestone.component_aliases
    matched = [row for row in legacy_rows if _matches(row.get("label", ""), aliases)]
    if milestone.completion_rule == "any":
        history_complete = any(bool(row.get("completed")) for row in matched)
    else:
        history_complete = bool(matched) and all(bool(row.get("completed")) for row in matched)

    return history_complete or (
        bool(milestone.auto_artifact)
        and _artifact_complete(milestone.auto_artifact, project_dir)
    )


def _insert_project_task(
    conn: sqlite3.Connection,
    columns: set[str],
    project_id: int,
    sort_order: int,
    milestone: Milestone,
    completed: bool,
) -> int:
    values = {
        "project_id": int(project_id),
        "sort_order": int(sort_order),
        "stage": milestone.stage,
        "label": milestone.label,
        "completed": 1 if completed else 0,
        "description": milestone.description,
        "definition_of_done": milestone.definition_of_done,
        "starter_path": "",
        "estimated_minutes": int(milestone.minutes),
        "managed_key": MANAGED_PREFIX + milestone.key,
    }
    selected = [name for name in values if name in columns]
    sql = (
        f"INSERT INTO project_tasks ({','.join(selected)}) "
        f"VALUES ({','.join('?' for _ in selected)})"
    )
    cursor = conn.execute(sql, tuple(values[name] for name in selected))
    return int(cursor.lastrowid)


def _update_project_task(
    conn: sqlite3.Connection,
    columns: set[str],
    task_id: int,
    sort_order: int,
    milestone: Milestone,
    completed: bool,
) -> None:
    values = {
        "sort_order": int(sort_order),
        "stage": milestone.stage,
        "label": milestone.label,
        "completed": 1 if completed else 0,
        "description": milestone.description,
        "definition_of_done": milestone.definition_of_done,
        "estimated_minutes": int(milestone.minutes),
        "managed_key": MANAGED_PREFIX + milestone.key,
    }
    selected = [name for name in values if name in columns]
    if not selected:
        return
    assignments = ",".join(f"{name}=?" for name in selected)
    conn.execute(
        f"UPDATE project_tasks SET {assignments} WHERE id=?",
        (*[values[name] for name in selected], int(task_id)),
    )


def reconcile(
    conn: sqlite3.Connection,
    root: Path,
    *,
    write_report: bool = True,
) -> dict:
    """Consolidate legacy task rows into true portfolio milestones.

    Existing canonical completion is never reduced. Legacy rows are archived
    before removal, and their completion state is used to initialize the
    canonical parent milestone.
    """
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)

    columns = _table_columns(conn, "project_tasks")
    if not {"id", "project_id", "label", "completed"}.issubset(columns):
        raise RuntimeError("project_tasks does not contain the required columns.")

    rows = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM project_tasks ORDER BY project_id,sort_order,id"
        ).fetchall()
    ]
    project_ids = sorted({int(row["project_id"]) for row in rows})
    try:
        active_project_row = conn.execute(
            "SELECT current_project FROM program_state WHERE id=1"
        ).fetchone()
        active_project_id = (
            int(active_project_row[0]) if active_project_row is not None else None
        )
    except (sqlite3.OperationalError, TypeError, ValueError):
        active_project_id = None

    result = {
        "projects": len(project_ids),
        "archived": 0,
        "inserted": 0,
        "updated": 0,
        "removed": 0,
        "canonical_total": 0,
    }

    now = datetime.now().isoformat(timespec="seconds")
    report_lines = [
        "# Portfolio Milestone Consolidation",
        "",
        f"Migration: `{MIGRATION_VERSION}`",
        f"Applied: {now}",
        "",
        "Minor implementation tasks were archived and merged into durable stage-gate milestones.",
        "",
    ]

    for project_id in project_ids:
        project_rows = [row for row in rows if int(row["project_id"]) == project_id]
        canonical_existing: dict[str, dict] = {}
        legacy: list[dict] = []

        for row in project_rows:
            managed_key = str(row.get("managed_key") or "")
            key = (
                managed_key[len(MANAGED_PREFIX):]
                if managed_key.startswith(MANAGED_PREFIX)
                else ""
            )
            if not key:
                matched = CANONICAL_LABELS.get(str(row["label"]).casefold())
                key = matched.key if matched is not None else ""
            if key in CANONICAL_BY_KEY:
                canonical_existing[key] = row
            else:
                legacy.append(row)

        # Move legacy sort values away before canonical insertion in case the
        # schema enforces a project/sort uniqueness constraint.
        if legacy and "sort_order" in columns:
            conn.executemany(
                "UPDATE project_tasks SET sort_order=? WHERE id=?",
                [
                    (10000 + index, int(row["id"]))
                    for index, row in enumerate(legacy, 1)
                ],
            )

        for row in legacy:
            key = _canonical_key_for_legacy(str(row["label"]))
            snapshot = json.dumps(row, default=str, sort_keys=True)
            conn.execute(
                """
                INSERT INTO portfolio_milestone_archive(
                    original_task_id,project_id,canonical_key,
                    original_label,original_stage,original_completed,
                    original_sort_order,snapshot_json,archived_at
                )
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(original_task_id,project_id) DO UPDATE SET
                    canonical_key=excluded.canonical_key,
                    original_label=excluded.original_label,
                    original_stage=excluded.original_stage,
                    original_completed=MAX(
                        portfolio_milestone_archive.original_completed,
                        excluded.original_completed
                    ),
                    original_sort_order=excluded.original_sort_order,
                    snapshot_json=excluded.snapshot_json
                """,
                (
                    int(row["id"]),
                    project_id,
                    key,
                    str(row["label"]),
                    str(row.get("stage") or ""),
                    int(bool(row.get("completed"))),
                    int(row.get("sort_order") or 0),
                    snapshot,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO portfolio_milestone_components(
                    project_id,canonical_key,original_task_id,
                    original_label,original_completed
                )
                VALUES(?,?,?,?,?)
                ON CONFLICT(project_id,canonical_key,original_task_id)
                DO UPDATE SET
                    original_label=excluded.original_label,
                    original_completed=MAX(
                        portfolio_milestone_components.original_completed,
                        excluded.original_completed
                    )
                """,
                (
                    project_id,
                    key,
                    int(row["id"]),
                    str(row["label"]),
                    int(bool(row.get("completed"))),
                ),
            )
            result["archived"] += 1

        project_dir = _project_directory(Path(root), project_id)
        canonical_ids: dict[str, int] = {}
        for index, milestone in enumerate(MILESTONES, 1):
            existing = canonical_existing.get(milestone.key)
            inherited = _derived_completed(milestone, legacy, project_dir)
            completed = inherited or bool(existing and existing.get("completed"))

            if existing is None:
                task_id = _insert_project_task(
                    conn,
                    columns,
                    project_id,
                    index * 10,
                    milestone,
                    completed,
                )
                result["inserted"] += 1
            else:
                task_id = int(existing["id"])
                _update_project_task(
                    conn,
                    columns,
                    task_id,
                    index * 10,
                    milestone,
                    completed,
                )
                result["updated"] += 1
            canonical_ids[milestone.key] = task_id
            result["canonical_total"] += 1

        # Repair the live portfolio route only for the active project. The old
        # loop updated the same track row once per project, so the last project
        # silently replaced the correct link used by Today’s Focus and Next Tasks.
        first_incomplete = conn.execute(
            """
            SELECT id,label,stage
            FROM project_tasks
            WHERE project_id=?
              AND (
                    managed_key LIKE ?
                    OR label IN ({})
                  )
              AND completed=0
            ORDER BY sort_order,id
            LIMIT 1
            """.format(",".join("?" for _ in MILESTONES)),
            (
                project_id,
                MANAGED_PREFIX + "%",
                *[item.label for item in MILESTONES],
            ),
        ).fetchone()
        if first_incomplete is not None and project_id == active_project_id:
            try:
                source_label = (
                    f"Portfolio • Project {project_id} • "
                    f"{str(first_incomplete['stage'] or '')}"
                ).rstrip(" •")
                conn.execute(
                    """
                    UPDATE track_tasks
                    SET linked_entity_id=?,
                        target_key=?,
                        source_label=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE track_key='portfolio'
                    """,
                    (
                        int(first_incomplete["id"]),
                        f"project:{project_id}:task:{int(first_incomplete['id'])}",
                        source_label,
                    ),
                )
                conn.execute(
                    """
                    UPDATE sprint_tasks
                    SET label=?
                    WHERE id=(
                        SELECT task_id
                        FROM track_tasks
                        WHERE track_key='portfolio'
                    )
                    """,
                    (str(first_incomplete["label"]),),
                )
            except sqlite3.OperationalError:
                pass

        if legacy:
            ids = [int(row["id"]) for row in legacy]
            conn.execute(
                f"DELETE FROM project_tasks WHERE id IN ({','.join('?' for _ in ids)})",
                ids,
            )
            result["removed"] += len(ids)

        report_lines.extend(
            [
                f"## Project {project_id}",
                "",
                f"- Canonical milestones: {len(MILESTONES)}",
                f"- Legacy rows archived this pass: {len(legacy)}",
                f"- Overview accepted as approved brief: {'yes' if _has_project_brief(project_dir) else 'no'}",
                f"- Raw dataset detected: {'yes' if _has_raw_dataset(project_dir) else 'no'}",
                "",
            ]
        )

    details = json.dumps(result, sort_keys=True)
    conn.execute(
        """
        INSERT INTO portfolio_milestone_migrations(
            migration_key,applied_at,details_json
        )
        VALUES(?,?,?)
        ON CONFLICT(migration_key) DO UPDATE SET
            applied_at=excluded.applied_at,
            details_json=excluded.details_json
        """,
        (MIGRATION_VERSION, now, details),
    )
    conn.commit()

    if write_report:
        report = Path(root) / "documentation" / "PORTFOLIO_MILESTONE_CONSOLIDATION.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report_lines.extend(
            [
                "## Canonical catalog",
                "",
                "| # | Stage | Milestone |",
                "|---:|---|---|",
                *[
                    f"| {index} | {item.stage} | {item.label} |"
                    for index, item in enumerate(MILESTONES, 1)
                ],
                "",
                "Original rows remain available in the SQLite tables "
                "`portfolio_milestone_archive` and `portfolio_milestone_components`.",
                "",
            ]
        )
        report.write_text("\n".join(report_lines), encoding="utf-8")

    return result
