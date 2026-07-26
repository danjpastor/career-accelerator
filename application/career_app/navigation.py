from __future__ import annotations

"""Canonical application navigation destinations.

Task metadata stores a logical destination index for compatibility with the
existing SQLite schema.  These constants keep every task producer and route in
sync with the consolidated v10.28 application shell.
"""

PAGE_DASHBOARD = 0
PAGE_LEARNING = 1
PAGE_PORTFOLIO = 2
PAGE_STUDY = 3
PAGE_READINESS = 4
PAGE_APPLICATIONS = 5
PAGE_PUBLISH = 6
PAGE_WORKSPACES = 7
PAGE_SETTINGS = 8

NAV_ITEMS = (
    ("🏠 Dashboard", PAGE_DASHBOARD),
    ("📚 Learning", PAGE_LEARNING),
    ("📁 Portfolio Workspace", PAGE_PORTFOLIO),
    ("⏱️ Study Session", PAGE_STUDY),
    ("🎯 Job Readiness", PAGE_READINESS),
    ("💼 Applications", PAGE_APPLICATIONS),
    ("🚀 Publish & Git", PAGE_PUBLISH),
    ("🗂️ Task Workspaces", PAGE_WORKSPACES),
    ("⚙️ Settings", PAGE_SETTINGS),
)

CATEGORY_DESTINATIONS = {
    "learning": PAGE_LEARNING,
    "sql": PAGE_LEARNING,
    "portfolio": PAGE_PORTFOLIO,
    "review": PAGE_WORKSPACES,
    "job readiness": PAGE_READINESS,
    "career": PAGE_READINESS,
    "applications": PAGE_APPLICATIONS,
    "publish": PAGE_PUBLISH,
    "general": PAGE_WORKSPACES,
}

TRACK_DESTINATIONS = {
    "google": PAGE_LEARNING,
    "academy": PAGE_LEARNING,
    "sql": PAGE_LEARNING,
    "applied": PAGE_LEARNING,
    "portfolio": PAGE_PORTFOLIO,
    "review": PAGE_WORKSPACES,
}


def destination_for(*, category: str = "", track_key: str = "", default: int = PAGE_WORKSPACES) -> int:
    """Return the consolidated destination for task metadata."""
    track = str(track_key or "").strip().casefold()
    if track in TRACK_DESTINATIONS:
        return TRACK_DESTINATIONS[track]
    category_key = str(category or "").strip().casefold()
    return CATEGORY_DESTINATIONS.get(category_key, int(default))
