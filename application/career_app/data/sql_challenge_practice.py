"""Read-only access to the Career Accelerator SQL challenge catalog."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "content"
    / "sql_challenge_practice"
    / "catalog.json"
)


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def exercises() -> tuple[dict[str, Any], ...]:
    return tuple(load_catalog()["exercises"])


def exercise_by_display_number(number: int) -> dict[str, Any]:
    index = int(number) - 1
    rows = exercises()
    if index < 0 or index >= len(rows):
        raise KeyError(number)
    return dict(rows[index])


def exercise_by_internal_id(number: int) -> dict[str, Any]:
    target = int(number)
    for item in exercises():
        if int(item["internal_id"]) == target:
            return dict(item)
    raise KeyError(number)
