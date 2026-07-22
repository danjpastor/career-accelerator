from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import PathwayDefinition
from .paths import discover_application_root, load_reset_layout


def _setup_paths() -> tuple[Path, Path]:
    root = discover_application_root(Path(__file__))
    layout = load_reset_layout(root)
    return (
        layout.configured_path("portfolio_setup_template"),
        layout.configured_path("portfolio_package_schema"),
    )


def build_setup_file(pathway: PathwayDefinition, *, learner_name: str = "") -> str:
    template_path, schema_path = _setup_paths()
    template = template_path.read_text(encoding="utf-8")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    replacements = {
        "{{PATHWAY_ID}}": pathway.pathway_id,
        "{{PATHWAY_NAME}}": pathway.display_name,
        "{{APPLICATION_NAME}}": pathway.application_name,
        "{{LEARNER_NAME}}": " ".join(str(learner_name or "").split()),
        "{{TRACK_SHELLS}}": "\n".join(f"- {name}" for name in pathway.track_shells),
        "{{IMPORT_SCHEMA_JSON}}": json.dumps(schema, indent=2),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template.rstrip() + "\n"


def write_setup_file(
    destination: Path | str,
    pathway: PathwayDefinition,
    *,
    learner_name: str = "",
) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        build_setup_file(pathway, learner_name=learner_name),
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(destination)
    return destination
