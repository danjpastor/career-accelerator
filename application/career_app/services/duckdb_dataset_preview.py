"""Markdown dataset previews for the native SQL challenge workspace."""
from __future__ import annotations

from typing import Any


def _cell(value: Any) -> str:
    if value is None:
        return "NULL"
    return str(value).replace("|", "\\|").replace("\n", " ")


def inject_preview(*, root, number: int, markdown: str, inventory, row_limit: int = 5) -> str:
    """Append schema and first-row previews using runner-provided inventory."""
    del root, number
    datasets = list(inventory or [])
    if not datasets:
        return markdown
    parts = [str(markdown or "").rstrip(), "", "## Data available"]
    parts.append(
        "Use the table names and columns below in the integrated SQL editor. "
        "The preview shows the first few rows; Check Task uses the full bundled dataset."
    )
    for dataset in datasets:
        table = str(dataset.get("table") or "dataset")
        grain = str(dataset.get("grain") or "").strip()
        columns = list(dataset.get("columns") or [])
        types = list(dataset.get("column_types") or [])
        rows = list(dataset.get("rows") or [])[: max(0, int(row_limit))]
        parts.extend(["", f"### `{table}`"])
        if grain:
            parts.append(f"**Table grain:** {grain}")
        if columns:
            schema = ", ".join(
                f"`{name}` {types[index] if index < len(types) else ''}".rstrip()
                for index, name in enumerate(columns)
            )
            parts.append(f"**Columns:** {schema}")
        if columns and rows:
            parts.append("")
            parts.append("| " + " | ".join(_cell(value) for value in columns) + " |")
            parts.append("| " + " | ".join("---" for _ in columns) + " |")
            for row in rows:
                parts.append("| " + " | ".join(_cell(value) for value in row) + " |")
    return "\n".join(parts).rstrip() + "\n"
