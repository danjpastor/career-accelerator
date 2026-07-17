from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import shutil


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def prune_backups(backup_dir: Path) -> int:
    files = sorted(backup_dir.glob("career_accelerator_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    keep = set(files[:10])
    now = datetime.now()
    daily = {}
    weekly = {}
    for path in files[10:]:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
        age = now - stamp
        if age <= timedelta(days=7):
            daily.setdefault(stamp.date(), path)
        elif age <= timedelta(weeks=4):
            weekly.setdefault(stamp.isocalendar()[:2], path)
    keep.update(daily.values()); keep.update(weekly.values())
    removed = 0
    for path in files:
        if path not in keep:
            path.unlink(missing_ok=True); removed += 1
    return removed


def create_backup(root: Path):
    source = root / "data" / "career_accelerator.db"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(backup_dir.glob("career_accelerator_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    if source.exists() and existing:
        try:
            if source.stat().st_size == existing[0].stat().st_size and _digest(source) == _digest(existing[0]):
                prune_backups(backup_dir)
                return existing[0]
        except OSError:
            pass
    target = backup_dir / f"career_accelerator_{datetime.now():%Y%m%d_%H%M%S}.db"
    if source.exists():
        shutil.copy2(source, target)
    prune_backups(backup_dir)
    return target
