# DuckDB Practice Library

This library converts broad roadmap reminders into concrete SQL assignments
designed for DuckDB inside VS Code.

Each exercise includes:

- a small fictional CSV dataset
- a realistic business scenario
- specific questions
- a blank `starter.sql`
- completion evidence requirements
- result checkpoints without completed solution queries

## One-time setup

From the repository root in the VS Code PowerShell terminal:

```powershell
.\practice\duckdb\setup\setup_practice.ps1
```

This installs the Python DuckDB package when necessary and creates:

```text
practice/duckdb/career_practice.duckdb
```

Connect that database in your DuckDB-capable VS Code workflow, then open
the assigned exercise's `starter.sql`.

You can also run the Python setup directly:

```powershell
python -m pip install duckdb
python .\practice\duckdb\setup\build_database.py
```

## Working method

1. Open `TASK_INDEX.md`.
2. Open the assigned exercise README.
3. Copy its `starter.sql` into `submissions/`.
4. Write and run your own SQL.
5. Check `validation.md` only after attempting the questions.
6. Commit the completed submission as portfolio evidence.

## Important boundary

The library does not contain completed SQL answer files. Validation files
contain expected outputs so you can verify your own work without replacing
the learning process.

## DuckDB references

- https://duckdb.org/docs/current/data/csv/overview.html
- https://duckdb.org/docs/current/sql/statements/create_table.html
- https://duckdb.org/docs/current/sql/introduction.html
- https://duckdb.org/docs/current/sql/query_syntax/from.html
- https://duckdb.org/docs/current/sql/functions/window_functions.html
