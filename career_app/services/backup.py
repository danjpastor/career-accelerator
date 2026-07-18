from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import sqlite3
import tempfile


PROGRESS_PREFIX = "career_accelerator_"
PRIVATE_PREFIX = "career_private_"

def _database_digest(path: Path) -> str:
    """Hash logical SQLite content so page-layout differences do not duplicate backups."""
    hasher = hashlib.sha256()
    conn = sqlite3.connect(str(path))
    try:
        for line in conn.iterdump():
            hasher.update(line.encode("utf-8"))
            hasher.update(b"\n")
    finally:
        conn.close()
    return hasher.hexdigest()


def _backup_files(backup_dir: Path) -> list[Path]:
    """Return progress snapshots, which anchor each paired backup."""
    return sorted(
        (
            path
            for path in Path(backup_dir).glob(f"{PROGRESS_PREFIX}*.db")
            if "snapshot_" not in path.name
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _private_pair(progress_backup: Path) -> Path:
    suffix = progress_backup.name.removeprefix(PROGRESS_PREFIX)
    return progress_backup.with_name(f"{PRIVATE_PREFIX}{suffix}")


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
    progress_files = _backup_files(backup_dir)
    keep = _retained_backups(progress_files)
    removed = 0
    recovered_bytes = 0

    for progress_path in progress_files:
        if progress_path in keep:
            continue
        for path in (progress_path, _private_pair(progress_path)):
            if not path.exists():
                continue
            try:
                recovered_bytes += path.stat().st_size
                path.unlink()
                removed += 1
            except OSError:
                continue

    # Clean private snapshots whose matching progress snapshot no longer exists.
    for private_path in backup_dir.glob(f"{PRIVATE_PREFIX}*.db"):
        suffix = private_path.name.removeprefix(PRIVATE_PREFIX)
        progress_path = backup_dir / f"{PROGRESS_PREFIX}{suffix}"
        if progress_path.exists():
            continue
        try:
            recovered_bytes += private_path.stat().st_size
            private_path.unlink()
            removed += 1
        except OSError:
            continue

    kept_files = 0
    for progress_path in keep:
        kept_files += 1
        if _private_pair(progress_path).exists():
            kept_files += 1

    return {
        "removed": removed,
        "recovered_bytes": recovered_bytes,
        "kept": kept_files,
    }


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


def _same_snapshot(current: Path, previous: Path | None) -> bool:
    if previous is None or not previous.exists():
        return False
    try:
        return _database_digest(current) == _database_digest(previous)
    except (OSError, sqlite3.DatabaseError):
        return False


def _temporary_snapshot(source: Path, backup_dir: Path, prefix: str) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix=f"{prefix}snapshot_",
        suffix=".db",
        dir=backup_dir,
        delete=False,
    ) as handle:
        snapshot = Path(handle.name)
    snapshot.unlink(missing_ok=True)
    _consistent_snapshot(source, snapshot)
    return snapshot


def create_backup(root: Path):
    """Create a timestamp-matched backup pair for public and private data."""
    root = Path(root)
    progress_source = root / "data" / "career_accelerator.db"
    private_source = root / "data" / "career_private.db"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    if not progress_source.exists():
        return backup_dir / f"{PROGRESS_PREFIX}{datetime.now():%Y%m%d_%H%M%S}.db"

    progress_snapshot = _temporary_snapshot(
        progress_source,
        backup_dir,
        PROGRESS_PREFIX,
    )
    private_snapshot = (
        _temporary_snapshot(private_source, backup_dir, PRIVATE_PREFIX)
        if private_source.exists()
        else None
    )

    try:
        existing = _backup_files(backup_dir)
        newest_progress = existing[0] if existing else None
        newest_private = (
            _private_pair(newest_progress)
            if newest_progress is not None
            else None
        )

        progress_unchanged = _same_snapshot(
            progress_snapshot,
            newest_progress,
        )
        private_unchanged = (
            private_snapshot is None
            and (newest_private is None or not newest_private.exists())
        ) or (
            private_snapshot is not None
            and _same_snapshot(private_snapshot, newest_private)
        )

        if newest_progress is not None and progress_unchanged and private_unchanged:
            progress_snapshot.unlink(missing_ok=True)
            if private_snapshot is not None:
                private_snapshot.unlink(missing_ok=True)
            prune_backups_with_report(backup_dir)
            return newest_progress

        stamp = f"{datetime.now():%Y%m%d_%H%M%S}"
        progress_target = backup_dir / f"{PROGRESS_PREFIX}{stamp}.db"
        private_target = backup_dir / f"{PRIVATE_PREFIX}{stamp}.db"
        counter = 1
        while progress_target.exists() or private_target.exists():
            token = f"{stamp}_{counter}"
            progress_target = backup_dir / f"{PROGRESS_PREFIX}{token}.db"
            private_target = backup_dir / f"{PRIVATE_PREFIX}{token}.db"
            counter += 1

        progress_snapshot.replace(progress_target)
        if private_snapshot is not None:
            private_snapshot.replace(private_target)

        prune_backups_with_report(backup_dir)
        return progress_target
    finally:
        progress_snapshot.unlink(missing_ok=True)
        if private_snapshot is not None:
            private_snapshot.unlink(missing_ok=True)
