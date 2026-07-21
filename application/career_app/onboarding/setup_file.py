from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import PathwayDefinition


REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "portfolio_onboarding" / "chatgpt_portfolio_setup.md"
SCHEMA_PATH = REPO_ROOT / "portfolio_onboarding" / "portfolio_package.schema.json"


def build_setup_file(pathway: PathwayDefinition) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    replacements = {
        "{{PATHWAY_ID}}": pathway.pathway_id,
        "{{PATHWAY_NAME}}": pathway.display_name,
        "{{APPLICATION_NAME}}": pathway.application_name,
        "{{TRACK_SHELLS}}": "\n".join(f"- {name}" for name in pathway.track_shells),
        "{{IMPORT_SCHEMA_JSON}}": json.dumps(schema, indent=2),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template.rstrip() + "\n"


def write_setup_file(destination: Path | str, pathway: PathwayDefinition) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(build_setup_file(pathway), encoding="utf-8", newline="\n")
    temporary.replace(destination)
    return destination
