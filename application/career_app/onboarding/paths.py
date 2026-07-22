from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MANIFEST_ENV = "CAREER_ACCELERATOR_RESET_MANIFEST"
HOME_ENV = "CAREER_ACCELERATOR_HOME"
DEFAULT_MANIFEST_RELATIVE = Path("application/config/reset_manifest.json")


class ResetLayoutError(RuntimeError):
    """Raised when the configured reset layout is unsafe or incomplete."""


def _normalized_relative(value: str, *, field: str) -> Path:
    text = str(value or "").strip().replace("\\", "/")
    pure = PurePosixPath(text)
    if not text or pure.is_absolute() or ".." in pure.parts:
        raise ResetLayoutError(f"{field} must be a non-empty path relative to the application root: {value!r}")
    if any(part in {"", "."} for part in pure.parts):
        raise ResetLayoutError(f"{field} contains an unsupported path segment: {value!r}")
    return Path(*pure.parts)


def _is_application_root(candidate: Path) -> bool:
    """Use marker files rather than a repository name or checkout depth."""
    return (
        (candidate / "application" / "career_app").is_dir()
        and (candidate / "pathways" / "index.json").is_file()
    )


def discover_application_root(start: Path | None = None) -> Path:
    """Resolve the install root without assuming GitHub, a folder name, drive, or depth.

    The host should normally pass its already-resolved ROOT. Environment override is
    provided for packaged/relocated installations and tests. Marker discovery is only
    a final fallback for modules imported outside the normal application startup.
    """
    override = os.environ.get(HOME_ENV, "").strip()
    if override:
        root = Path(override).expanduser().resolve()
        if not _is_application_root(root):
            raise ResetLayoutError(
                f"{HOME_ENV} does not point to a Career Accelerator application root: {root}"
            )
        return root

    current = Path(start or __file__).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if _is_application_root(candidate):
            return candidate
    raise ResetLayoutError(
        "Could not locate the Career Accelerator application root. Pass it explicitly "
        f"or set {HOME_ENV}."
    )


@dataclass(frozen=True, slots=True)
class ResetLayout:
    root: Path
    manifest_path: Path
    raw: dict[str, Any]

    def relative_path(self, value: str, *, field: str) -> Path:
        return _normalized_relative(value, field=field)

    def path(self, value: str, *, field: str) -> Path:
        relative = self.relative_path(value, field=field)
        return self.root / relative

    def configured_path(self, key: str) -> Path:
        value = self.raw.get(key)
        if not isinstance(value, str):
            raise ResetLayoutError(f"reset manifest requires string field {key!r}")
        return self.path(value, field=key)

    def strings(self, key: str) -> tuple[str, ...]:
        values = self.raw.get(key, [])
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise ResetLayoutError(f"reset manifest field {key!r} must be a string list")
        for index, value in enumerate(values):
            self.relative_path(value, field=f"{key}[{index}]")
        return tuple(values)

    def mappings(self, key: str) -> tuple[dict[str, Any], ...]:
        values = self.raw.get(key, [])
        if not isinstance(values, list) or not all(isinstance(item, dict) for item in values):
            raise ResetLayoutError(f"reset manifest field {key!r} must be an object list")
        return tuple(dict(item) for item in values)

    def glob(self, pattern: str, *, field: str) -> Iterable[Path]:
        relative = self.relative_path(pattern, field=field)
        # pathlib glob accepts wildcard segments after lexical safety validation.
        yield from self.root.glob(relative.as_posix())


def load_reset_layout(
    application_root: Path | None = None,
    manifest_path: Path | None = None,
) -> ResetLayout:
    root = Path(application_root).expanduser().resolve() if application_root else discover_application_root()
    manifest_override = os.environ.get(MANIFEST_ENV, "").strip()
    selected = Path(manifest_path or manifest_override or (root / DEFAULT_MANIFEST_RELATIVE))
    if not selected.is_absolute():
        selected = root / selected
    selected = selected.expanduser().resolve()
    try:
        raw = json.loads(selected.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResetLayoutError(f"Missing reset manifest: {selected}") from exc
    except json.JSONDecodeError as exc:
        raise ResetLayoutError(f"Invalid reset manifest JSON in {selected}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ResetLayoutError(f"Reset manifest must contain one JSON object: {selected}")
    if str(raw.get("schema_version", "")) != "1.0":
        raise ResetLayoutError("Unsupported reset manifest schema_version")
    layout = ResetLayout(root=root, manifest_path=selected, raw=raw)
    for required in (
        "pathways_root",
        "projects_root",
        "portfolio_import_staging",
        "portfolio_import_backup",
        "portfolio_import_archive",
        "portfolio_setup_template",
        "portfolio_package_schema",
        "reset_marker",
        "portfolio_catalog",
        "sql_practice_log",
    ):
        layout.configured_path(required)
    # Validate every configured destructive target before any reset can begin.
    layout.strings("remove_files")
    layout.strings("remove_globs")
    layout.strings("backup_paths")
    layout.strings("primary_database_files")
    layout.strings("runtime_database_files")
    layout.strings("runtime_database_globs")
    layout.strings("generated_file_globs")
    for index, item in enumerate(layout.mappings("clear_and_recreate")):
        if "path" not in item:
            raise ResetLayoutError(f"clear_and_recreate[{index}] requires path")
        layout.relative_path(str(item["path"]), field=f"clear_and_recreate[{index}].path")
    for index, item in enumerate(layout.mappings("scaffold_directories")):
        if "path" not in item:
            raise ResetLayoutError(f"scaffold_directories[{index}] requires path")
        layout.relative_path(str(item["path"]), field=f"scaffold_directories[{index}].path")
    return layout
