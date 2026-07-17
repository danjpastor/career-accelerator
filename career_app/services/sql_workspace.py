"""Local SQL solution-file helpers for the SQL Companion."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def slugify(title: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        str(title or "").lower(),
    ).strip("-")


def solution_path(root: Path, title: str) -> Path:
    return (
        Path(root)
        / "resources"
        / "sql"
        / "datalemur"
        / f"{slugify(title)}.sql"
    )


def starter_template(
    *, title: str, difficulty: str, topic: str, concepts: str
) -> str:
    """Return a minimal learner-owned interview submission template."""
    return (
        f"-- Problem: {title}\n"
        "-- Platform: DataLemur\n"
        f"-- Difficulty: {difficulty}\n"
        f"-- Topic: {topic}\n"
        f"-- Required concepts: {concepts}\n"
        "\n"
        "-- Write and test your own solution below.\n"
        "-- Record assumptions and validation checks as comments.\n"
        "\n"
        "SELECT\n"
        "    -- requested columns\n"
        "FROM\n"
        "    -- source table\n"
        ";\n"
    )


def ensure_solution_file(
    root: Path,
    *,
    title: str,
    difficulty: str,
    topic: str,
    concepts: str,
) -> tuple[Path, bool]:
    """Create a starter solution file when it does not already exist."""
    path = solution_path(root, title)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    created = not path.exists()
    if created:
        path.write_text(
            starter_template(
                title=title,
                difficulty=difficulty,
                topic=topic,
                concepts=concepts,
            ),
            encoding="utf-8",
        )

    return path, created


def open_in_editor(
    path: Path,
    *,
    root: Path | None = None,
) -> str:
    """Open the SQL file in VS Code, then fall back to the OS."""
    path = Path(path).resolve()
    cwd = str(
        Path(root).resolve()
        if root is not None
        else path.parent
    )

    code_command = shutil.which("code")
    if code_command:
        subprocess.Popen(
            [
                code_command,
                "-g",
                str(path),
            ],
            cwd=cwd,
        )
        return "VS Code"

    if os.name == "nt":
        os.startfile(str(path))
        return "the default Windows editor"

    if sys.platform == "darwin":
        subprocess.Popen(
            ["open", str(path)],
            cwd=cwd,
        )
        return "the default macOS editor"

    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        subprocess.Popen(
            [xdg_open, str(path)],
            cwd=cwd,
        )
        return "the default desktop editor"

    raise RuntimeError(
        "No supported editor command was found. "
        f"Open this file manually: {path}"
    )
