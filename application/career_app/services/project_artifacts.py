"""Project artifact registry and upstream milestone context.

The registry is intentionally derived from project files instead of treating a
completed checkbox as proof that an artifact still exists.  Later milestone
workspaces can therefore consume the outputs of earlier milestones without
asking the learner to re-enter the same information.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable


MILESTONE_ORDER = (
    "project_brief",
    "data_source_spec",
    "raw_dataset",
    "validate_relationships",
    "data_dictionary_review",
    "clean_analytical_data",
    "analytical_database",
    "sql_analysis",
    "exploratory_analysis",
    "validate_findings",
    "power_bi_model",
    "power_bi_report",
    "executive_summary",
    "publish_case_study",
)

MILESTONE_LABELS = {
    "project_brief": "Project brief",
    "data_source_spec": "Data source and specification",
    "raw_dataset": "Raw datasets",
    "validate_relationships": "Relationship validation",
    "data_dictionary_review": "Data dictionary",
    "clean_analytical_data": "Cleaned and validated data",
    "analytical_database": "Analytical database",
    "sql_analysis": "SQL analysis",
    "exploratory_analysis": "Exploratory analysis",
    "validate_findings": "Validated findings",
    "power_bi_model": "Power BI semantic model",
    "power_bi_report": "Power BI report",
    "executive_summary": "Executive summary",
    "publish_case_study": "Published case study",
}


def _relative(project_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError:
        return str(path)


def _existing(project_dir: Path, values: Iterable[str | Path]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        path = project_dir / Path(value)
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            candidates = [path]
        else:
            candidates = []
        for candidate in candidates:
            relative = _relative(project_dir, candidate)
            if relative not in seen:
                seen.add(relative)
                result.append(relative)
    return result


def _artifact_candidates(project_dir: Path, milestone_key: str) -> list[str]:
    project_dir = Path(project_dir)
    candidates: dict[str, tuple[str | Path, ...]] = {
        "project_brief": (
            "documentation/project_brief.md",
            "PROJECT_CHARTER.md",
            "docs/project_brief.md",
        ),
        "data_source_spec": (
            "documentation/data_source_review.md",
            "documentation/data_source_manifest.csv",
            "docs/synthetic_data_specification.md",
            "docs/source_brief",
            "config/project_sources.yaml",
        ),
        "raw_dataset": (
            "data/raw",
        ),
        "validate_relationships": (
            "notebooks/validate_relationships.ipynb",
            "reports/relationship_validation",
            "documentation/relationship_validation.md",
        ),
        "data_dictionary_review": (
            "documentation/data_dictionary.csv",
            "documentation/data_dictionary.md",
            "DATA_DICTIONARY.md",
            "workspaces/studios/data_dictionary_review.json",
        ),
        "clean_analytical_data": (
            "data/processed",
            "data/cleaned",
            "notebooks/cleaning",
            "documentation/cleaning",
            "workspaces/studios/clean_analytical_data.json",
        ),
        "analytical_database": (
            "sql/schema/build_analytical_database.sql",
            "data/working/analytical.duckdb",
            "data/working/project.duckdb",
        ),
        "sql_analysis": (
            "sql/analysis",
        ),
        "exploratory_analysis": (
            "notebooks/eda.ipynb",
            "documentation/eda_summary.md",
        ),
        "validate_findings": (
            "documentation/findings_validation.md",
        ),
        "power_bi_model": (
            "power-bi",
            "outputs/screenshots/power-bi-model",
        ),
        "power_bi_report": (
            "power-bi",
            "outputs/screenshots/power-bi-report",
        ),
        "executive_summary": (
            "documentation/executive_summary.md",
        ),
        "publish_case_study": (
            "README.md",
            "outputs/screenshots",
        ),
    }
    return _existing(project_dir, candidates.get(str(milestone_key), ()))


def registry_path(project_dir: Path) -> Path:
    return Path(project_dir) / "workspaces" / "project_artifacts.json"


def build_registry(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    milestones: dict[str, Any] = {}
    for key in MILESTONE_ORDER:
        artifacts = _artifact_candidates(project_dir, key)
        milestones[key] = {
            "label": MILESTONE_LABELS[key],
            "status": "available" if artifacts else "missing",
            "artifacts": artifacts,
        }
    return {
        "version": 1,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "milestones": milestones,
    }


def refresh_registry(project_dir: Path) -> dict[str, Any]:
    payload = build_registry(project_dir)
    path = registry_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return payload


def upstream_milestones(project_dir: Path, milestone_key: str) -> list[dict[str, Any]]:
    payload = refresh_registry(project_dir)
    try:
        stop = MILESTONE_ORDER.index(str(milestone_key))
    except ValueError:
        stop = len(MILESTONE_ORDER)
    result: list[dict[str, Any]] = []
    for key in MILESTONE_ORDER[:stop]:
        record = dict(payload["milestones"][key])
        record["key"] = key
        result.append(record)
    return result


def upstream_context_markdown(project_dir: Path, milestone_key: str) -> str:
    rows = upstream_milestones(project_dir, milestone_key)
    if not rows:
        return "## Previous milestone context\n\nThis is the first project milestone.\n"
    lines = [
        "## Previous milestone context",
        "",
        "This workspace continues from the project artifacts below. Do not recreate decisions that have already been approved.",
        "",
    ]
    for row in rows:
        mark = "✓" if row["artifacts"] else "○"
        lines.append(f"### {mark} {row['label']}")
        if row["artifacts"]:
            lines.extend(f"- `{path}`" for path in row["artifacts"][:12])
            if len(row["artifacts"]) > 12:
                lines.append(f"- …and {len(row['artifacts']) - 12} more")
        else:
            lines.append("- No project artifact was detected.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
