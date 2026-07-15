"""Build the local DuckDB practice database from the supplied CSV files."""

from pathlib import Path
import os
import sys

try:
    import duckdb
except ImportError:
    raise SystemExit(
        "DuckDB is not installed. Run: python -m pip install duckdb"
    )

REPO_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = REPO_ROOT / "practice" / "duckdb" / "career_practice.duckdb"
SETUP_SQL = REPO_ROOT / "practice" / "duckdb" / "setup" / "00_build_database.sql"

os.chdir(REPO_ROOT)
connection = duckdb.connect(str(DATABASE_PATH))
try:
    connection.execute(SETUP_SQL.read_text(encoding="utf-8"))
    table_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema='main'
          AND table_name LIKE 'ex%'
        """
    ).fetchone()[0]
finally:
    connection.close()

print(f"Created: {DATABASE_PATH}")
print(f"Practice tables: {table_count}")
