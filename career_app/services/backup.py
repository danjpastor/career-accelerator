from pathlib import Path
from datetime import datetime
import shutil

def create_backup(root: Path):
    source = root / "data" / "career_accelerator.db"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"career_accelerator_{datetime.now():%Y%m%d_%H%M%S}.db"
    if source.exists():
        shutil.copy2(source, target)
    return target
