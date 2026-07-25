"""Small, file-preserving helpers for integrated Jupyter notebook workspaces."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import base64
import html
import json
from pathlib import Path
import re
from typing import Any, Iterable


NOTEBOOK_FORMAT = 4
NOTEBOOK_MINOR = 5


_ANSI_ESCAPE_RE = re.compile(
    r"(?:\x1B[@-_][0-?]*[ -/]*[@-~])|(?:\x9B[0-?]*[ -/]*[@-~])"
)
_SQL_MAGIC_RE = re.compile(r"^\s*%%?sql(?:\s|$)", re.IGNORECASE)
_SQL_START_RE = re.compile(
    r"^(?:SELECT|WITH|CREATE|INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|"
    r"DESCRIBE|DESC|SHOW|PRAGMA|EXPLAIN|COPY|VALUES|CALL|EXPORT|IMPORT|"
    r"ATTACH|DETACH|INSTALL|LOAD|PIVOT|UNPIVOT)\b",
    re.IGNORECASE,
)


def strip_ansi(value: str) -> str:
    """Remove terminal color/control sequences from notebook output text."""
    return _ANSI_ESCAPE_RE.sub("", str(value or ""))


def detect_execution_language(source: str, fallback: str = "python") -> str:
    """Identify SQL cells even when comments or blank lines precede the magic."""
    lines = str(source or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _SQL_MAGIC_RE.match(stripped):
            return "sql"
        if stripped.startswith("#") or stripped.startswith("--"):
            continue
        if _SQL_START_RE.match(stripped):
            return "sql"
        break
    return str(fallback or "python").casefold()


def _sql_comment_line(line: str) -> str:
    """Translate whole-line Python comments to SQL comments."""
    leading = line[: len(line) - len(line.lstrip())]
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return leading + "--" + stripped[1:]
    return line


def sql_text_for_execution(source: str) -> str:
    """Extract executable SQL while preserving the saved notebook source.

    The learner may keep explanatory comments or blank lines above ``%%sql``.
    They may also write a plain SQL cell.  This helper removes only the magic
    line from the execution copy and converts whole-line Python comments to SQL
    comments.
    """
    original = str(source or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = original.splitlines()
    magic_index: int | None = None
    inline_sql = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r"^%%?sql\b(.*)$", stripped, flags=re.IGNORECASE)
        if match:
            magic_index = index
            inline_sql = str(match.group(1) or "").strip()
            break

    body: list[str] = []
    if magic_index is not None:
        for line in lines[:magic_index]:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("--"):
                body.append(line)
            elif stripped.startswith("#"):
                body.append(_sql_comment_line(line))
            else:
                body.append("-- " + stripped)
        if inline_sql:
            body.append(inline_sql)
        body.extend(_sql_comment_line(line) for line in lines[magic_index + 1 :])
    else:
        body = [_sql_comment_line(line) for line in lines]

    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return "\n".join(body)


def prepare_execution_source(source: str, language: str = "") -> str:
    """Return kernel-ready source while preserving the notebook's saved text.

    SQL cells execute through Career Accelerator's persistent DuckDB helper.
    This avoids IPython treating SQL as Python and guarantees that statements
    returning rows, including ``DESCRIBE`` and ``SHOW``, are displayed as a
    dataframe instead of a generic success message.
    """
    original = str(source or "").replace("\r\n", "\n").replace("\r", "\n")
    resolved_language = str(language or "").casefold()
    if resolved_language != "sql":
        resolved_language = detect_execution_language(
            original,
            resolved_language or "python",
        )
    if resolved_language != "sql":
        return original

    sql_text = sql_text_for_execution(original)
    return f"_dca_execute_sql({sql_text!r})"

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


_NOTEBOOK_OUTPUT_STYLE = """
<style>
.jp-OutputArea {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #e5edf8;
  background-color: #0b1324;
}
.jp-OutputArea .jp-table-wrap {
  margin: 4px 0 8px 0;
  overflow-x: auto;
  border: 1px solid #3b4b66;
  border-radius: 7px;
  background-color: #0f172a;
  color: #e5edf8;
}
.jp-OutputArea table,
.jp-OutputArea .dataframe {
  border-collapse: collapse;
  border-spacing: 0;
  width: 100%;
  min-width: 420px;
  background-color: #0f172a;
  color: #e5edf8;
  font-size: 12px;
}
.jp-OutputArea thead tr,
.jp-OutputArea .dataframe thead tr {
  background-color: #1e293b;
}
.jp-OutputArea th {
  padding: 7px 10px;
  text-align: left;
  font-weight: 650;
  color: #f8fafc;
  background-color: #1e293b;
  border: 1px solid #475569;
  white-space: nowrap;
}
.jp-OutputArea td {
  padding: 6px 10px;
  color: #e5edf8;
  background-color: #111c31;
  border: 1px solid #334155;
  vertical-align: top;
  white-space: nowrap;
}
.jp-OutputArea tbody tr:nth-child(even) td {
  background-color: #16223a;
}
.jp-OutputArea tbody th {
  background-color: #17243b;
  color: #f8fafc;
  font-weight: 600;
}
.jp-OutputArea pre {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid #334155;
  border-radius: 7px;
  background-color: #0f172a;
  color: #e5edf8;
  font-family: Consolas, "Cascadia Code", monospace;
  font-size: 12px;
  white-space: pre-wrap;
}
.jp-OutputArea img {
  display: block;
  max-width: 100%;
  margin: 4px auto;
}
.jp-OutputArea .jp-output-separator {
  height: 1px;
  margin: 10px 0;
  background-color: #334155;
}
</style>
"""


def _merge_inline_style(tag: str, style: str) -> str:
    """Append inline CSS so QTextDocument renders tables consistently."""
    style_match = re.search(
        r'\sstyle\s*=\s*([\'"])(.*?)\1',
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if style_match:
        existing = style_match.group(2).rstrip().rstrip(";")
        merged = existing + ";" + style
        return (
            tag[: style_match.start(2)]
            + merged
            + tag[style_match.end(2) :]
        )
    return tag[:-1] + f' style="{style}">' if tag.endswith(">") else tag


def _safe_notebook_html(value: str) -> str:
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        str(value or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(
        r'\son\w+\s*=\s*([\'"]).*?\1',
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if "<table" in text.casefold():
        table_style = (
            "border-collapse:collapse;width:100%;min-width:420px;"
            "background-color:#0f172a;color:#e5edf8;font-size:12px"
        )
        th_style = (
            "padding:7px 10px;text-align:left;font-weight:650;"
            "background-color:#1e293b;color:#f8fafc;"
            "border:1px solid #475569;white-space:nowrap"
        )
        td_style = (
            "padding:6px 10px;background-color:#111c31;color:#e5edf8;"
            "border:1px solid #334155;vertical-align:top;white-space:nowrap"
        )
        text = re.sub(
            r"<table\b[^>]*>",
            lambda match: _merge_inline_style(match.group(0), table_style),
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"<th\b[^>]*>",
            lambda match: _merge_inline_style(match.group(0), th_style),
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"<td\b[^>]*>",
            lambda match: _merge_inline_style(match.group(0), td_style),
            text,
            flags=re.IGNORECASE,
        )
        return (
            '<div class="jp-table-wrap" style="margin:4px 0 8px 0;'
            'overflow-x:auto;border:1px solid #3b4b66;border-radius:7px;'
            'background-color:#0f172a;color:#e5edf8">'
            + text
            + "</div>"
        )
    return text


def output_to_html(output: dict[str, Any]) -> str:
    """Render a notebook output without executing arbitrary HTML scripts."""
    output_type = str(output.get("output_type") or "")
    if output_type == "stream":
        text = output.get("text", "")
        if isinstance(text, list):
            text = "".join(str(part) for part in text)
        return f"<pre>{html.escape(strip_ansi(str(text)))}</pre>"
    if output_type == "error":
        traceback = output.get("traceback") or []
        if isinstance(traceback, str):
            traceback = [traceback]
        return "<pre>" + html.escape(strip_ansi("\n".join(str(line) for line in traceback))) + "</pre>"
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
            # QTextBrowser does not run JavaScript. Strip active content and
            # keep the generated table markup inside a Jupyter-style wrapper.
            return _safe_notebook_html(str(value))
        value = data.get("text/plain", "")
        if isinstance(value, list):
            value = "".join(str(part) for part in value)
        return f"<pre>{html.escape(strip_ansi(str(value)))}</pre>"
    return ""


def outputs_html(outputs: Iterable[dict[str, Any]]) -> str:
    rendered = [output_to_html(item) for item in outputs]
    rendered = [item for item in rendered if item]
    if not rendered:
        return ""
    separator = '<div class="jp-output-separator"></div>'
    return (
        _NOTEBOOK_OUTPUT_STYLE
        + '<div class="jp-OutputArea">'
        + separator.join(rendered)
        + "</div>"
    )
