"""Small, file-preserving helpers for integrated Jupyter notebook workspaces."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import base64
import html
import json
from pathlib import Path
from typing import Any, Iterable


NOTEBOOK_FORMAT = 4
NOTEBOOK_MINOR = 5


def _source_text(cell: dict[str, Any]) -> str:
    value = cell.get("source", "")
    if isinstance(value, list):
        return "".join(str(part) for part in value)
    return str(value or "")


def set_source_text(cell: dict[str, Any], text: str) -> None:
    cell["source"] = str(text)


def new_markdown_cell(text: str = "") -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": str(text),
    }


def new_code_cell(text: str = "") -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": str(text),
    }


def new_notebook(
    *,
    title: str,
    cells: Iterable[dict[str, Any]] | None = None,
    template: str = "portfolio-notebook",
) -> dict[str, Any]:
    payload_cells = list(cells or ())
    if not payload_cells:
        payload_cells = [new_markdown_cell(f"# {title}\n")]
    return {
        "cells": payload_cells,
        "metadata": {
            "dcaManaged": True,
            "dcaTemplate": template,
            "dcaCreatedAt": datetime.now().isoformat(timespec="seconds"),
            "kernelspec": {
                "display_name": "Python (Career Accelerator)",
                "language": "python",
                "name": "career-accelerator",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": NOTEBOOK_FORMAT,
        "nbformat_minor": NOTEBOOK_MINOR,
    }


def load_notebook(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"The notebook could not be read: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("cells"), list):
        raise ValueError(f"The file is not a valid Jupyter notebook: {path}")
    payload.setdefault("metadata", {})
    payload.setdefault("nbformat", NOTEBOOK_FORMAT)
    payload.setdefault("nbformat_minor", NOTEBOOK_MINOR)
    for cell in payload["cells"]:
        if not isinstance(cell, dict):
            raise ValueError(f"The notebook contains an invalid cell: {path}")
        cell.setdefault("metadata", {})
        if cell.get("cell_type") == "code":
            cell.setdefault("execution_count", None)
            cell.setdefault("outputs", [])
        set_source_text(cell, _source_text(cell))
    return payload


def save_notebook(path: Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = deepcopy(payload)
    clean["nbformat"] = int(clean.get("nbformat") or NOTEBOOK_FORMAT)
    clean["nbformat_minor"] = int(clean.get("nbformat_minor") or NOTEBOOK_MINOR)
    clean.setdefault("metadata", {})
    for cell in clean.get("cells", []):
        set_source_text(cell, _source_text(cell))
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(clean, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def ensure_notebook(
    path: Path,
    *,
    title: str,
    cells: Iterable[dict[str, Any]],
    template: str,
) -> Path:
    path = Path(path)
    if path.is_file():
        # Read once to prove it is valid, but never replace learner work.
        load_notebook(path)
        return path
    save_notebook(
        path,
        new_notebook(title=title, cells=cells, template=template),
    )
    return path


def _meaningful_code(source: str) -> bool:
    lines = []
    for line in str(source or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("--"):
            continue
        lines.append(stripped)
    return bool(lines)


def _meaningful_markdown(source: str, marker: str) -> bool:
    text = str(source or "")
    if marker.casefold() not in text.casefold():
        return False
    content = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        if any(
            phrase in stripped.casefold()
            for phrase in (
                "what changed, why",
                "separate observations",
                "record your conclusion",
                "write your conclusion",
                "add your conclusion",
            )
        ):
            continue
        content.append(stripped)
    return len(" ".join(content).split()) >= 12


def notebook_completion_issues(payload: dict[str, Any], policy: str = "") -> list[str]:
    """Use light evidence checks without pretending to judge the analysis itself."""
    cells = list(payload.get("cells") or [])
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code" and _meaningful_code(_source_text(cell))]
    executed = [
        cell
        for cell in code_cells
        if cell.get("execution_count") is not None or bool(cell.get("outputs"))
    ]
    markdown = [
        _source_text(cell)
        for cell in cells
        if cell.get("cell_type") == "markdown"
    ]
    policy = str(policy or "").casefold()
    issues: list[str] = []
    if policy == "relationship":
        if len(code_cells) < 4:
            issues.append("Write the relationship-validation queries in the notebook.")
        if len(executed) < 3:
            issues.append("Run the relationship checks and save their outputs.")
        if not any(_meaningful_markdown(text, "conclusion") for text in markdown):
            issues.append("Write the final relationship-validation conclusion in the notebook.")
    elif policy == "cleaning":
        if len(code_cells) < 2:
            issues.append("Add your profiling and cleaning work to the notebook.")
        if len(executed) < 2:
            issues.append("Run the cleaning and validation cells and save their outputs.")
        if not any(_meaningful_markdown(text, "cleaning summary") for text in markdown):
            issues.append("Complete the cleaning summary in the notebook.")
    elif policy == "eda":
        if len(code_cells) < 3:
            issues.append("Add the main exploratory checks and visuals to the notebook.")
        if len(executed) < 3:
            issues.append("Run the exploratory analysis and save its outputs.")
        if not any(_meaningful_markdown(text, "candidate findings") for text in markdown):
            issues.append("Write the candidate findings and separate them from open questions.")
    return issues


def output_to_html(output: dict[str, Any]) -> str:
    """Render a notebook output without executing arbitrary HTML scripts."""
    output_type = str(output.get("output_type") or "")
    if output_type == "stream":
        text = output.get("text", "")
        if isinstance(text, list):
            text = "".join(str(part) for part in text)
        return f"<pre>{html.escape(str(text))}</pre>"
    if output_type == "error":
        traceback = output.get("traceback") or []
        if isinstance(traceback, str):
            traceback = [traceback]
        return "<pre>" + html.escape("\n".join(str(line) for line in traceback)) + "</pre>"
    if output_type in {"execute_result", "display_data"}:
        data = output.get("data") or {}
        if "image/png" in data:
            encoded = data["image/png"]
            if isinstance(encoded, list):
                encoded = "".join(str(part) for part in encoded)
            # Validate base64 before putting it into the browser widget.
            try:
                base64.b64decode(str(encoded), validate=True)
            except Exception:
                pass
            else:
                return (
                    '<div style="padding:6px"><img style="max-width:100%" '
                    f'src="data:image/png;base64,{encoded}"></div>'
                )
        if "text/html" in data:
            value = data["text/html"]
            if isinstance(value, list):
                value = "".join(str(part) for part in value)
            # QTextBrowser does not run JavaScript. Keep the generated table/HTML.
            return str(value)
        value = data.get("text/plain", "")
        if isinstance(value, list):
            value = "".join(str(part) for part in value)
        return f"<pre>{html.escape(str(value))}</pre>"
    return ""


def outputs_html(outputs: Iterable[dict[str, Any]]) -> str:
    rendered = [output_to_html(item) for item in outputs]
    rendered = [item for item in rendered if item]
    return "<hr>".join(rendered)
