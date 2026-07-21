from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATHWAY_ROOT = REPO_ROOT / "pathways"


class PathwayCatalogError(ValueError):
    """Raised when a pathway definition is missing or malformed."""


@dataclass(frozen=True, slots=True)
class PathwayDefinition:
    pathway_id: str
    display_name: str
    short_name: str
    description: str
    status: str
    enabled: bool
    application_name: str
    window_title: str
    logo_path: str
    horizontal_logo_path: str
    app_icon_path: str
    app_user_model_id: str
    learning_system_name: str
    learner_noun: str
    portfolio_noun: str
    accent_label: str
    track_shells: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return self.enabled and self.status == "available"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any], *, source: Path) -> "PathwayDefinition":
        required = {
            "pathway_id",
            "display_name",
            "short_name",
            "description",
            "status",
            "enabled",
            "brand",
            "learning",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise PathwayCatalogError(
                f"{source.name} is missing required keys: {', '.join(missing)}"
            )
        brand = raw.get("brand")
        learning = raw.get("learning")
        if not isinstance(brand, dict) or not isinstance(learning, dict):
            raise PathwayCatalogError(f"{source.name} brand and learning must be objects")

        pathway_id = _identifier(raw["pathway_id"], "pathway_id", source)
        status = str(raw["status"]).strip().lower()
        if status not in {"available", "coming_soon", "disabled"}:
            raise PathwayCatalogError(f"{source.name} has unsupported status {status!r}")

        tracks = raw.get("track_shells", [])
        if not isinstance(tracks, list) or not all(isinstance(item, str) for item in tracks):
            raise PathwayCatalogError(f"{source.name} track_shells must be a string list")

        return cls(
            pathway_id=pathway_id,
            display_name=_text(raw["display_name"], "display_name", source),
            short_name=_text(raw["short_name"], "short_name", source),
            description=_text(raw["description"], "description", source),
            status=status,
            enabled=bool(raw["enabled"]),
            application_name=_text(brand.get("application_name"), "brand.application_name", source),
            window_title=_text(brand.get("window_title"), "brand.window_title", source),
            logo_path=_text(brand.get("logo_path"), "brand.logo_path", source),
            horizontal_logo_path=_text(
                brand.get("horizontal_logo_path"),
                "brand.horizontal_logo_path",
                source,
            ),
            app_icon_path=_text(brand.get("app_icon_path"), "brand.app_icon_path", source),
            app_user_model_id=_text(
                brand.get("app_user_model_id"),
                "brand.app_user_model_id",
                source,
            ),
            learning_system_name=_text(
                learning.get("system_name"),
                "learning.system_name",
                source,
            ),
            learner_noun=_text(learning.get("learner_noun"), "learning.learner_noun", source),
            portfolio_noun=_text(
                learning.get("portfolio_noun", "portfolio project"),
                "learning.portfolio_noun",
                source,
            ),
            accent_label=_text(
                learning.get("accent_label", raw["display_name"]),
                "learning.accent_label",
                source,
            ),
            track_shells=tuple(item.strip() for item in tracks if item.strip()),
        )


@dataclass(frozen=True, slots=True)
class PathwayCatalog:
    neutral_brand: dict[str, str]
    pathways: tuple[PathwayDefinition, ...]

    def get(self, pathway_id: str | None) -> PathwayDefinition | None:
        if not pathway_id:
            return None
        key = str(pathway_id).strip().lower()
        return next((item for item in self.pathways if item.pathway_id == key), None)

    def require(self, pathway_id: str) -> PathwayDefinition:
        definition = self.get(pathway_id)
        if definition is None:
            raise PathwayCatalogError(f"Unknown pathway: {pathway_id}")
        return definition

    @property
    def available(self) -> tuple[PathwayDefinition, ...]:
        return tuple(item for item in self.pathways if item.is_available)


def _text(value: Any, field: str, source: Path) -> str:
    text = str(value or "").strip()
    if not text:
        raise PathwayCatalogError(f"{source.name} requires {field}")
    return text


def _identifier(value: Any, field: str, source: Path) -> str:
    text = _text(value, field, source).lower()
    if not all(char.islower() or char.isdigit() or char == "_" for char in text):
        raise PathwayCatalogError(
            f"{source.name} {field} may contain only lowercase letters, numbers, and underscores"
        )
    return text


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PathwayCatalogError(f"Missing pathway catalog file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PathwayCatalogError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PathwayCatalogError(f"{path} must contain a JSON object")
    return value


def load_pathway_catalog(pathway_root: Path | None = None) -> PathwayCatalog:
    root = Path(pathway_root or DEFAULT_PATHWAY_ROOT)
    index_path = root / "index.json"
    index = _load_json(index_path)

    neutral = index.get("neutral_brand")
    if not isinstance(neutral, dict):
        raise PathwayCatalogError("pathways/index.json requires neutral_brand")
    neutral_required = {
        "application_name",
        "window_title",
        "horizontal_logo_path",
        "app_icon_path",
        "app_user_model_id",
    }
    missing_neutral = sorted(neutral_required.difference(neutral))
    if missing_neutral:
        raise PathwayCatalogError(
            "neutral_brand is missing: " + ", ".join(missing_neutral)
        )

    files = index.get("pathway_files")
    if not isinstance(files, list) or not files:
        raise PathwayCatalogError("pathways/index.json requires pathway_files")

    definitions: list[PathwayDefinition] = []
    seen: set[str] = set()
    for filename in files:
        if not isinstance(filename, str) or not filename.strip():
            raise PathwayCatalogError("pathway_files entries must be filenames")
        source = root / filename
        raw = _load_json(source)
        definition = PathwayDefinition.from_mapping(raw, source=source)
        if definition.pathway_id in seen:
            raise PathwayCatalogError(
                f"Duplicate pathway_id {definition.pathway_id!r} in {source.name}"
            )
        seen.add(definition.pathway_id)
        definitions.append(definition)

    if not any(item.is_available for item in definitions):
        raise PathwayCatalogError("At least one pathway must be available")
    return PathwayCatalog(
        neutral_brand={key: str(value) for key, value in neutral.items()},
        pathways=tuple(definitions),
    )


def serialize_catalog(catalog: PathwayCatalog) -> dict[str, Any]:
    """Return a small public representation suitable for generated setup files."""
    return {
        "pathways": [
            {
                "pathway_id": item.pathway_id,
                "display_name": item.display_name,
                "description": item.description,
                "status": item.status,
                "track_shells": list(item.track_shells),
            }
            for item in catalog.pathways
        ]
    }
