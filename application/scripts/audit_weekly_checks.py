#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit all 12 weekly knowledge checks.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "application"))

    from career_app.services import weekly_checks

    issues = weekly_checks.audit_definitions()
    if args.db:
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row
        try:
            weekly_checks.reconcile(conn)
            rows = conn.execute(
                """SELECT s.week,s.label,s.completed,m.managed_key,m.estimated_minutes
                     FROM sprint_tasks s JOIN task_metadata m ON m.task_id=s.id
                    WHERE m.managed_key LIKE 'weekly_check:%' ORDER BY s.week"""
            ).fetchall()
            if len(rows) != 12:
                issues.append(f"Expected 12 weekly check tasks; found {len(rows)}.")
            for expected_week, row in enumerate(rows, start=1):
                if int(row["week"]) != expected_week:
                    issues.append(f"Weekly check order mismatch at Week {expected_week}.")
                if str(row["label"]) != f"Week {expected_week} Knowledge Check":
                    issues.append(f"Week {expected_week} task title is incorrect.")
                if str(row["managed_key"]) != f"weekly_check:{expected_week}":
                    issues.append(f"Week {expected_week} managed key is incorrect.")
        finally:
            conn.close()

    if issues:
        print("Weekly knowledge-check audit FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Weekly knowledge-check audit passed: 12 tasks, 8 questions each, 7/8 required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
