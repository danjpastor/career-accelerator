"""Preserve an in-progress study session across unrelated UI refreshes."""

from __future__ import annotations

import time
from typing import Any


TEXT_FIELDS = (
    "session_date",
    "session_hours",
    "session_google",
    "session_datacamp",
    "session_portfolio",
)

VALUE_FIELDS = (
    "session_productivity",
    "session_sql",
    "session_goal_minutes",
)


def _capture_text(window: Any, name: str) -> str | None:
    widget = getattr(window, name, None)
    if widget is None or not hasattr(widget, "text"):
        return None
    return widget.text()


def _capture_value(window: Any, name: str) -> int | None:
    widget = getattr(window, name, None)
    if widget is None or not hasattr(widget, "value"):
        return None
    return int(widget.value())


def capture(window: Any, *, captured_at: float | None = None) -> dict:
    """Capture the timer and unsaved Study Session form values."""
    if captured_at is None:
        captured_at = time.monotonic()

    notes_widget = getattr(window, "session_notes", None)
    notes = (
        notes_widget.toPlainText()
        if notes_widget is not None
        and hasattr(notes_widget, "toPlainText")
        else None
    )

    timer = getattr(window, "timer", None)
    timer_active = bool(
        timer is not None
        and hasattr(timer, "isActive")
        and timer.isActive()
    )

    return {
        "captured_at": float(captured_at),
        "elapsed_seconds": int(
            getattr(window, "elapsed_seconds", 0)
        ),
        "timer_state": str(
            getattr(window, "timer_state", "ready")
        ),
        "timer_active": timer_active,
        "text_fields": {
            name: _capture_text(window, name)
            for name in TEXT_FIELDS
        },
        "value_fields": {
            name: _capture_value(window, name)
            for name in VALUE_FIELDS
        },
        "notes": notes,
    }


def restore(
    window: Any,
    snapshot: dict | None,
    *,
    restored_at: float | None = None,
) -> None:
    """Restore a captured session without losing running timer time."""
    if not snapshot:
        return

    if restored_at is None:
        restored_at = time.monotonic()

    elapsed_seconds = int(
        snapshot.get("elapsed_seconds", 0)
    )
    timer_active = bool(
        snapshot.get("timer_active", False)
    )

    if timer_active:
        refresh_seconds = max(
            0,
            int(
                float(restored_at)
                - float(snapshot.get("captured_at", restored_at))
            ),
        )
        elapsed_seconds += refresh_seconds

    window.elapsed_seconds = elapsed_seconds
    window.timer_state = str(
        snapshot.get("timer_state", "ready")
    )

    for name, value in snapshot.get(
        "text_fields",
        {},
    ).items():
        widget = getattr(window, name, None)
        if (
            value is not None
            and widget is not None
            and hasattr(widget, "setText")
            and (
                not hasattr(widget, "text")
                or widget.text() != value
            )
        ):
            widget.setText(value)

    for name, value in snapshot.get(
        "value_fields",
        {},
    ).items():
        widget = getattr(window, name, None)
        if (
            value is not None
            and widget is not None
            and hasattr(widget, "setValue")
            and (
                not hasattr(widget, "value")
                or int(widget.value()) != int(value)
            )
        ):
            widget.setValue(int(value))

    notes_widget = getattr(window, "session_notes", None)
    notes = snapshot.get("notes")
    if (
        notes is not None
        and notes_widget is not None
        and hasattr(notes_widget, "setPlainText")
        and (
            not hasattr(notes_widget, "toPlainText")
            or notes_widget.toPlainText() != notes
        )
    ):
        notes_widget.setPlainText(notes)

    timer = getattr(window, "timer", None)
    if timer is not None:
        if timer_active and hasattr(timer, "start"):
            timer.start(1000)
            window.timer_state = "running"
        elif hasattr(timer, "stop"):
            timer.stop()

    update_visuals = getattr(
        window,
        "update_timer_visuals",
        None,
    )
    if callable(update_visuals):
        update_visuals()
