# Portfolio SQL Workspace

Portfolio SQL milestones such as **Validate relationships** open into a prepared,
project-specific DuckDB workspace. The learner should be able to open the task,
open its starter in VS Code, and run SQL immediately without registering files or
working out database paths.

## Learner flow

```text
Open portfolio task
→ Read the rendered guide
→ Open Starter in VS Code
→ Run SQL with the installed DuckDB extension
→ Record results in the findings document
→ Mark the milestone complete
```

## Generated project structure

```text
projects/<project>/
├── config/
│   └── project_sources.yaml
├── data/
│   ├── raw/
│   └── working/
│       └── project.duckdb
├── documentation/
│   ├── relationship_validation.md
│   └── portfolio_workspace_migration.md   when cleanup occurs
├── sql/
│   └── validation/
│       └── validate_relationships.sql
└── <project>.code-workspace
```

## VS Code and DuckDB

The generated `.code-workspace` file attaches
`data/working/project.duckdb` as the `project` database and makes it the default
DuckDB database. The learner can run SQL with **Ctrl+Enter** or the statement-level
Run action supplied by the installed DuckDB extension.

The app does not generate a Python runner, batch runner, or learner-facing setup
SQL. DuckDB execution stays inside the existing VS Code extension workflow.

## Starter philosophy

The SQL starter provides:

- The real project tables
- Column names and DuckDB data types
- Primary-key candidates
- Candidate relationships
- Short generic syntax patterns
- Blank TODO sections

It does not provide:

- Completed project queries
- Finished joins
- Exact filters
- Final validation logic
- Findings or conclusions

The learner writes the actual SQL required by the task.

## Source configuration

When no configuration exists, the app scans `data/raw/` recursively for CSV,
Parquet, JSON, JSONL, and NDJSON files. It generates
`config/project_sources.yaml` with safe table names, column metadata, primary-key
candidates, and inferred relationships.

The file is project-specific and editable. Different projects can declare entirely
different source files, schemas, keys, and relationships without application-code
changes.

## Data refresh

**Refresh Project Data** rescans the source files, preserves configured table names
and key choices where possible, rebuilds the DuckDB database, and updates managed
workspace metadata. Learner-authored SQL and findings are not overwritten.

## Legacy cleanup

The previous workflow created learner-facing setup SQL and four fragmented
validation scripts. During migration:

- Untouched generated files are deleted.
- Edited managed files are moved to
  `archive/portfolio-workspace-migration/<timestamp>/`.
- The old `data/project_sources.yaml` location is migrated to
  `config/project_sources.yaml`.
- Learner-created files without the managed marker are left alone.
- Cleanup actions are recorded in
  `documentation/portfolio_workspace_migration.md`.
