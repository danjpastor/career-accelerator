from __future__ import annotations

"""Central icon registry for task presentation.

The registry is driven by canonical task metadata (kind, track, target, and
label) rather than visible title matching in the UI.  This keeps Dashboard and
Learning practice icons consistent as the planner changes wording.
"""

from pathlib import Path

ICON_FILES = {
    "google": "google_g.svg",
    "spreadsheet": "spreadsheet.svg",
    "sql": "sql.svg",
    "power_bi": "power_bi.svg",
    "python": "python.svg",
    "portfolio": "portfolio.svg",
    "review": "review.svg",
    "assessment": "assessment.svg",
    "lab": "lab.svg",
    "career": "career.svg",
    "general": "general.svg",
}


def _haystack(task: dict) -> str:
    values = (
        task.get("kind"),
        task.get("track_key"),
        task.get("target_key"),
        task.get("managed_key"),
        task.get("label"),
        task.get("display_source"),
        task.get("category"),
    )
    return " ".join(str(value or "") for value in values).casefold()


def key_for_task(task: dict, current_week: int | None = None) -> str:
    kind = str(task.get("kind") or "").casefold()
    text = _haystack(task)

    if kind == "google" or str(task.get("track_key") or "").casefold() == "google":
        return "google"
    if kind in {"duckdb", "interview_problem", "sql_practice"}:
        return "sql"
    if kind in {"portfolio_preparation", "portfolio_execution"}:
        return "portfolio"
    if kind == "review":
        return "review"
    if kind == "knowledge_check":
        return "assessment"
    if kind == "applied_lab":
        return "lab"
    if kind == "career_readiness":
        return "career"

    if any(token in text for token in ("power bi", "dax", "power_bi")):
        return "power_bi"
    if any(token in text for token in ("python", "pandas", "dataframe")):
        return "python"
    if any(token in text for token in ("sql", "duckdb", "query", "join", "cte", "window function")):
        return "sql"
    if any(token in text for token in ("spreadsheet", "excel", "sheet", "cell reference", "vlookup", "pivot")):
        return "spreadsheet"

    if kind in {"academy_lesson", "academy_practice"}:
        week = int(current_week or task.get("week") or 1)
        if week <= 2:
            return "spreadsheet"
        if week <= 6:
            return "sql"
        if week == 7:
            return "power_bi"
        if week == 8:
            return "python"
        return "portfolio"

    if str(task.get("category") or "").casefold() == "portfolio":
        return "portfolio"
    return "general"


def path_for_key(asset_root: str | Path, key: str) -> Path:
    filename = ICON_FILES.get(str(key or "general"), ICON_FILES["general"])
    return Path(asset_root) / "task_icons" / filename


def path_for_task(asset_root: str | Path, task: dict, current_week: int | None = None) -> Path:
    return path_for_key(asset_root, key_for_task(task, current_week))
