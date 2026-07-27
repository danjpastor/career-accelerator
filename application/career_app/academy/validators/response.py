from __future__ import annotations

import math
import re
from typing import Any

from .base import ValidationResult


def _normalise(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def validate_response(answer: str, spec: dict[str, Any]) -> ValidationResult:
    """Validate a short learner response without pretending prose is code.

    Supported modes are intentionally small and transparent so curriculum
    feedback can stay specific:

    * exact / one_of: a known short result or label
    * contains_all: a short explanation containing required ideas
    * numeric: a number within an optional tolerance
    """

    value = str(answer or "").strip()
    if not value:
        return ValidationResult(False, str(spec.get("empty_feedback") or "Add your answer before checking your work."))

    mode = str(spec.get("mode") or "exact").strip().lower()
    success = str(spec.get("success_feedback") or "That answer matches the result the task asks you to find.")
    failure = str(spec.get("failure_feedback") or "That does not match the expected result yet. Review the task and try again.")

    if mode in {"exact", "one_of"}:
        expected_raw = spec.get("accepted", spec.get("expected", []))
        if isinstance(expected_raw, (str, int, float)):
            expected_raw = [expected_raw]
        expected = {_normalise(str(item)) for item in (expected_raw or [])}
        return ValidationResult(_normalise(value) in expected, success if _normalise(value) in expected else failure)

    if mode == "contains_all":
        terms = [str(item) for item in spec.get("terms", []) if str(item).strip()]
        normalised = _normalise(value)
        missing = [term for term in terms if _normalise(term) not in normalised]
        if not missing:
            return ValidationResult(True, success)
        template = str(spec.get("missing_feedback") or "Your answer is on the right track, but it does not yet mention: {missing}.")
        return ValidationResult(False, template.format(missing=", ".join(missing)))

    if mode == "numeric":
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", value)
        if not match:
            return ValidationResult(False, str(spec.get("number_feedback") or "Enter the number shown by your analysis, then check again."))
        actual = float(match.group(0).replace(",", ""))
        expected = float(spec.get("expected"))
        tolerance = float(spec.get("tolerance", 0.0))
        passed = math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)
        return ValidationResult(passed, success if passed else failure, details={"actual": actual, "expected": expected})

    return ValidationResult(False, f"Unsupported response validation mode: {mode}")
