from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG_PATH = REPO_ROOT / "data" / "portfolio_catalog.json"


@dataclass(slots=True)
class ProjectCatalog:
    explicit: bool
    names: dict[int, str]
    directories: dict[int, str]

    @property
    def is_empty(self) -> bool:
        return not self.names


def load_project_catalog(path: Path | None = None) -> ProjectCatalog:
    catalog_path = Path(path or DEFAULT_CATALOG_PATH)
    if not catalog_path.is_file():
        return ProjectCatalog(explicit=False, names={}, directories={})
    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ProjectCatalog(explicit=False, names={}, directories={})
    projects = raw.get("projects") if isinstance(raw, dict) else None
    if not isinstance(projects, list):
        return ProjectCatalog(explicit=False, names={}, directories={})

    names: dict[int, str] = {}
    directories: dict[int, str] = {}
    for index, item in enumerate(projects, start=1):
        if not isinstance(item, dict):
            continue
        project_id = item.get("project_id", index)
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            continue
        title = str(item.get("title", "")).strip()
        directory = str(item.get("directory", "")).strip()
        if project_id < 1 or not title or not directory:
            continue
        names[project_id] = title
        directories[project_id] = directory
    return ProjectCatalog(explicit=True, names=names, directories=directories)


def write_project_catalog(
    projects: Iterable[dict[str, Any]],
    path: Path | None = None,
) -> Path:
    catalog_path = Path(path or DEFAULT_CATALOG_PATH)
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(projects, start=1):
        normalized.append(
            {
                "project_id": int(item.get("project_id", index)),
                "project_key": str(item.get("project_key", f"project_{index}")),
                "title": str(item["title"]),
                "directory": str(item["directory"]),
            }
        )
    payload = {
        "schema_version": "1.0",
        "generated_by": "Career Accelerator portfolio onboarding",
        "projects": normalized,
    }
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = catalog_path.with_suffix(catalog_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(catalog_path)
    return catalog_path


def apply_runtime_catalog(projects: Iterable[dict[str, Any]]) -> ProjectCatalog:
    """Mutate imported roadmap dictionaries so an import is visible without a restart."""
    projects = list(projects)
    names = {
        int(item.get("project_id", index)): str(item["title"])
        for index, item in enumerate(projects, start=1)
    }
    directories = {
        int(item.get("project_id", index)): str(item["directory"])
        for index, item in enumerate(projects, start=1)
    }
    try:
        from career_app.data import roadmap

        roadmap.PROJECT_NAMES.clear()
        roadmap.PROJECT_NAMES.update(names)
        roadmap.PROJECT_DIRS.clear()
        roadmap.PROJECT_DIRS.update(directories)
    except Exception:
        pass
    return ProjectCatalog(explicit=True, names=names, directories=directories)
