from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import sqlite3
import tempfile


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _backup_files(backup_dir: Path) -> list[Path]:
    return sorted(
        Path(backup_dir).glob("career_accelerator_*.db"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _retained_backups(files: list[Path], now: datetime | None = None) -> set[Path]:
    """Keep newest 10, daily representatives for 7 days, and 4 weekly copies."""
    now = now or datetime.now()
    keep: set[Path] = set(files[:10])
    daily: dict[object, Path] = {}
    weekly: dict[tuple[int, int], Path] = {}

    for path in files:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
        age = now - stamp
        if timedelta(0) <= age <= timedelta(days=7):
            daily.setdefault(stamp.date(), path)
        elif timedelta(days=7) < age <= timedelta(weeks=4):
            iso = stamp.isocalendar()
            weekly.setdefault((iso.year, iso.week), path)

    keep.update(daily.values())
    keep.update(weekly.values())
    return keep


def prune_backups_with_report(backup_dir: Path) -> dict[str, int]:
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    files = _backup_files(backup_dir)
    keep = _retained_backups(files)
    removed = 0
    recovered_bytes = 0
    for path in files:
        if path in keep:
            continue
        try:
            recovered_bytes += path.stat().st_size
            path.unlink()
            removed += 1
        except OSError:
            continue
    return {"removed": removed, "recovered_bytes": recovered_bytes, "kept": len(keep)}


def prune_backups(backup_dir: Path) -> int:
    """Compatibility wrapper returning only the number of removed files."""
    return prune_backups_with_report(backup_dir)["removed"]


def _consistent_snapshot(source: Path, destination: Path) -> None:
    """Create a complete SQLite snapshot even when WAL mode is active."""
    source_conn = sqlite3.connect(str(source))
    destination_conn = sqlite3.connect(str(destination))
    try:
        source_conn.backup(destination_conn)
        destination_conn.commit()
    finally:
        destination_conn.close()
        source_conn.close()


def create_backup(root: Path):
    root = Path(root)
    source = root / "data" / "career_accelerator.db"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        return backup_dir / f"career_accelerator_{datetime.now():%Y%m%d_%H%M%S}.db"

    existing = _backup_files(backup_dir)
    with tempfile.NamedTemporaryFile(
        prefix="career_accelerator_snapshot_", suffix=".db", dir=backup_dir, delete=False
    ) as handle:
        snapshot = Path(handle.name)
    try:
        snapshot.unlink(missing_ok=True)
        _consistent_snapshot(source, snapshot)
        if existing:
            newest = existing[0]
            try:
                if (
                    snapshot.stat().st_size == newest.stat().st_size
                    and _digest(snapshot) == _digest(newest)
                ):
                    snapshot.unlink(missing_ok=True)
                    prune_backups_with_report(backup_dir)
                    return newest
            except OSError:
                pass

        target = backup_dir / f"career_accelerator_{datetime.now():%Y%m%d_%H%M%S}.db"
        counter = 1
        while target.exists():
            target = backup_dir / (
                f"career_accelerator_{datetime.now():%Y%m%d_%H%M%S}_{counter}.db"
            )
            counter += 1
        snapshot.replace(target)
        prune_backups_with_report(backup_dir)
        return target
    finally:
        snapshot.unlink(missing_ok=True)
