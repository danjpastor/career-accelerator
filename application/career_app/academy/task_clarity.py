from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from .models import ActivityDefinition


@dataclass(frozen=True)
class ActivityClarity:
    task: str
    requirements: tuple[str, ...]
    expected_output: str
    enriched: bool


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return tuple(result)


def _contains_all(text: str, values: Iterable[str]) -> bool:
    searchable = text.casefold()
    return all(str(value).casefold() in searchable for value in values)


def _concept_name(pattern: str) -> str | None:
    raw = str(pattern or "")
    normalized = re.sub(r"\\[bBsSwWdD]", " ", raw)
    normalized = re.sub(r"[\^\$\(\)\[\]\{\}\?\*\+\|]", " ", normalized)
    normalized = normalized.replace("\\", " ")
    upper = " ".join(normalized.upper().split())

    concepts = (
        ("PARTITION BY", "PARTITION BY"),
        ("ORDER BY", "ORDER BY"),
        ("GROUP BY", "GROUP BY"),
        ("LEFT JOIN", "LEFT JOIN"),
        ("RIGHT JOIN", "RIGHT JOIN"),
        ("FULL JOIN", "FULL JOIN"),
        ("INNER JOIN", "INNER JOIN"),
        ("CROSS JOIN", "CROSS JOIN"),
        ("UNION ALL", "UNION ALL"),
        ("COUNT DISTINCT", "COUNT(DISTINCT ...)"),
        ("COUNT", "COUNT()"),
        ("SUM", "SUM()"),
        ("AVG", "AVG()"),
        ("MIN", "MIN()"),
        ("MAX", "MAX()"),
        ("COALESCE", "COALESCE()"),
        ("CASE", "CASE"),
        ("HAVING", "HAVING"),
        ("DISTINCT", "DISTINCT"),
        ("LIMIT", "LIMIT"),
        ("OFFSET", "OFFSET"),
        ("WITH", "a CTE using WITH"),
        ("OVER", "a window function using OVER"),
        ("JOIN", "JOIN"),
        ("WHERE", "WHERE"),
        ("SELECT", "SELECT"),
    )
    for needle, label in concepts:
        if needle in upper:
            return label
    return None


def build_activity_clarity(
    activity: ActivityDefinition,
    *,
    expected_columns: Iterable[str] = (),
    expected_row_count: int | None = None,
) -> ActivityClarity:
    presentation = dict(activity.presentation)
    validator = dict(activity.validator)

    prompt = str(activity.prompt or "").strip()
    short_task = str(presentation.get("task") or "").strip()
    task = prompt or short_task or f"Complete the activity: {activity.title}."

    requirements = _text_list(presentation.get("requirements"))
    enriched = task != short_task and bool(short_task)

    columns = tuple(str(item).strip() for item in expected_columns if str(item).strip())
    combined_before = " ".join((task, *requirements))

    if columns and not _contains_all(combined_before, columns):
        column_text = ", ".join(f"`{name}`" for name in columns)
        if bool(validator.get("column_sensitive", True)):
            requirements.insert(0, f"Return these columns in this exact order: {column_text}.")
        else:
            requirements.insert(0, f"Return these columns: {column_text}.")
        enriched = True

    allow_subset = bool(validator.get("allow_subset", False))
    configured_count = validator.get("expected_row_count")
    if configured_count is not None:
        try:
            expected_row_count = int(configured_count)
        except (TypeError, ValueError):
            pass

    if expected_row_count is not None and not allow_subset:
        count_text = f"Return exactly {expected_row_count} row" + (
            "" if expected_row_count == 1 else "s"
        ) + "."
        if str(expected_row_count) not in " ".join((task, *requirements)):
            requirements.append(count_text)
            enriched = True

    if bool(validator.get("order_sensitive", False)):
        ordering = (
            "Preserve the requested row order; use an appropriate `ORDER BY` "
            "so the result is deterministic."
        )
        if "order by" not in " ".join((task, *requirements)).casefold():
            requirements.append(ordering)
            enriched = True

    existing = " ".join((task, *requirements)).casefold()
    for pattern in validator.get("required_patterns", []) or []:
        concept = _concept_name(str(pattern))
        if concept and concept.casefold().replace("()", "") not in existing:
            requirements.append(f"Use {concept} as part of the solution.")
            existing += " " + concept.casefold()
            enriched = True

    for pattern in validator.get("forbidden_patterns", []) or []:
        concept = _concept_name(str(pattern))
        if concept and f"do not use {concept.casefold()}" not in existing:
            requirements.append(
                f"Do not use {concept}; solve the step with the concepts introduced so far."
            )
            existing += " do not use " + concept.casefold()
            enriched = True

    if not requirements:
        requirements.append(
            "Follow the complete task above and return only the requested result."
        )
        enriched = True

    expected = str(presentation.get("expected_output") or "").strip()
    shape_parts: list[str] = []
    if expected_row_count is not None and not allow_subset:
        shape_parts.append(
            f"{expected_row_count} row" + ("" if expected_row_count == 1 else "s")
        )
    if columns:
        shape_parts.append(
            f"{len(columns)} column" + ("" if len(columns) == 1 else "s")
        )
    shape = " × ".join(shape_parts)

    if not expected:
        expected = (
            f"A result with {shape} that satisfies every requirement above."
            if shape
            else "A result that satisfies every requirement above."
        )
        enriched = True
    elif shape and shape.casefold() not in expected.casefold():
        expected = expected.rstrip(".") + f". Result shape: {shape}."
        enriched = True

    if columns and not _contains_all(expected, columns):
        expected += " Column order: " + ", ".join(f"`{name}`" for name in columns) + "."
        enriched = True

    return ActivityClarity(
        task=task,
        requirements=_unique(requirements),
        expected_output=expected,
        enriched=enriched,
    )
