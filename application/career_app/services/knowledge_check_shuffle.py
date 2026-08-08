"""Stable display-time answer randomization for weekly knowledge checks.

The current Career Accelerator weekly quiz UI reads each question's canonical
``answer_options`` directly. Canonical weekly-check content intentionally keeps
the correct answer at index 0 for grading/content compatibility, so the UI must
randomize only the *displayed* order.

This helper stores the randomized display order on the quiz/dialog owner:
- one fresh arrangement per quiz window/attempt;
- stable order while moving Back/Next within that window;
- exactly two correct answers in A/B/C/D across the first eight questions;
- distractors shuffled independently;
- canonical question dictionaries are never mutated.
"""
from __future__ import annotations

import random
from typing import Any

CORRECT_FIELDS = (
    "expected_answer",
    "correct_answer",
    "expected",
    "correct",
    "answer",
    "solution",
    "expected_value",
    "answer_text",
)
_STATE_ATTR = "_dca_weekly_answer_shuffle_state_v104615_r5"
_SEED_ATTR = "_dca_weekly_answer_shuffle_seed_v104615_r5"


def _question_value(question: Any, key: str, default=None):
    if isinstance(question, dict):
        return question.get(key, default)
    return getattr(question, key, default)


def _correct_answer(question: Any, choices: list[Any]):
    for field in CORRECT_FIELDS:
        value = _question_value(question, field, None)
        if value is not None:
            return value
    # Current weekly-check definitions use the first canonical answer_options
    # value as the answer key. The UI receives a shuffled copy only for display.
    return choices[0] if choices else None


def _question_key(question: Any, choices: list[Any]):
    for field in ("id", "question_id", "key", "slug"):
        value = _question_value(question, field, None)
        if value not in (None, ""):
            return (field, str(value), tuple(map(repr, choices)))
    for field in ("question", "prompt", "text", "title"):
        value = _question_value(question, field, None)
        if value not in (None, ""):
            return (field, str(value), tuple(map(repr, choices)))
    return ("object", id(question), tuple(map(repr, choices)))


def _rng_for(owner):
    seed = getattr(owner, _SEED_ATTR, None)
    if seed is None:
        return random.SystemRandom()
    return random.Random(seed)


def _new_state(owner):
    rng = _rng_for(owner)
    positions = [0, 0, 1, 1, 2, 2, 3, 3]
    rng.shuffle(positions)
    return {
        "rng": rng,
        "positions": positions,
        "next_position": 0,
        "cache": {},
    }


def _state_for(owner):
    state = getattr(owner, _STATE_ATTR, None)
    if not isinstance(state, dict):
        state = _new_state(owner)
        setattr(owner, _STATE_ATTR, state)
    return state


def shuffled_answer_options_for_view(owner: Any, question: Any) -> list[Any]:
    """Return this question's stable randomized display options for the attempt."""
    raw = _question_value(question, "answer_options", None)
    if not isinstance(raw, (list, tuple)):
        raise ValueError("Weekly knowledge-check question is missing answer_options.")
    choices = list(raw)
    if len(choices) != 4:
        raise ValueError(
            "Weekly knowledge-check question must contain exactly four answer options; "
            f"found {len(choices)}."
        )

    correct = _correct_answer(question, choices)
    matches = [index for index, value in enumerate(choices) if value == correct]
    if len(matches) != 1:
        raise ValueError(
            "Weekly knowledge-check correct answer must appear exactly once in answer_options."
        )

    state = _state_for(owner)
    key = _question_key(question, choices)
    cached = state["cache"].get(key)
    if cached is not None:
        return list(cached)

    position_index = int(state["next_position"])
    positions = state["positions"]
    if position_index < len(positions):
        correct_position = positions[position_index]
    else:
        # Defensive fallback if this UI ever grows beyond the expected 8 questions.
        correct_position = position_index % 4
    state["next_position"] = position_index + 1

    distractors = list(choices)
    distractors.remove(correct)
    state["rng"].shuffle(distractors)
    arranged = list(distractors)
    arranged.insert(correct_position, correct)
    state["cache"][key] = tuple(arranged)
    return arranged


def correct_positions_for_owner(owner: Any, questions: list[Any]) -> list[int]:
    """Test/diagnostic helper: return displayed correct-answer positions."""
    result = []
    for question in questions:
        choices = list(_question_value(question, "answer_options", []))
        correct = _correct_answer(question, choices)
        shown = shuffled_answer_options_for_view(owner, question)
        result.append(shown.index(correct))
    return result
