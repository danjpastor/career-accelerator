# Portfolio Validation Notebook Workspace

Portfolio validation milestones such as **Validate relationships** open into a prepared,
project-specific Jupyter notebook. The app handles source registration so the learner can
focus on writing validation SQL, inspecting results, and explaining what those results mean.

## Learner flow

```text
Open portfolio task
→ Read schemas and relationships in the Visual Guide
→ Open Notebook in VS Code
→ Run the collapsed setup cell once
→ Write SQL directly in native %%sql cells
→ Review each result beneath its query
→ Explain the result in the following Markdown prompt
→ Restart the kernel and run all cells
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
│   └── portfolio_workspace_migration.md   when cleanup occurs
├── notebooks/
│   └── validate_relationships.ipynb
└── <project>.code-workspace
```

## Notebook design

The generated notebook contains only:

- One collapsed setup cell
- Four concise work sections
- Native `%%sql` cells
- Query results directly beneath each SQL cell
- Short interpretation prompts
- A final relationship-validation conclusion

The notebook intentionally does not duplicate:

- Table schemas
- Column dictionaries
- Primary-key candidates
- Relationship maps
- Full task instructions
- Finished project queries

Those reference details remain in the Task Workspace **Visual Guide**, where they can be
reviewed beside the notebook without making the notebook noisy.

## Native SQL cells

The setup cell loads JupySQL, creates an isolated in-memory DuckDB session, and registers
the project's configured raw sources. Learner cells begin with:

```sql
%%sql

-- Write your query here.
```

The learner writes SQL normally. There are no Python strings, `con.sql(...)` calls, or
custom query-runner scripts in the learner-facing sections.

## VS Code and the Python environment

The generated `.code-workspace` opens the exact notebook, points VS Code at the repository
`.venv`, and recommends the Jupyter extension. The managed requirements include `duckdb`,
`ipykernel`, and `jupysql`.

The notebook uses a native DuckDB connection registered with JupySQL. It loads project
sources into memory, so the VS Code DuckDB extension may keep `project.duckdb` open without
causing a Windows file-lock conflict.

## Project-neutral source configuration

When no configuration exists, the app scans `data/raw/` recursively for CSV, Parquet,
JSON, JSONL, and NDJSON files. It generates `config/project_sources.yaml` with safe table
names, column metadata, primary-key candidates, and inferred relationships.

Different projects can declare different source files, schemas, keys, and relationships
without application-code changes. The Visual Guide and notebook setup are generated from
that project-local configuration.

## Migration from older notebooks

Managed v2 notebooks used Python variables containing SQL strings. On the next task open:

- The notebook is upgraded to native `%%sql` cells.
- Recognized learner SQL is copied into the matching new section.
- A notebook containing learner SQL or outputs is archived under
  `archive/portfolio-workspace-migration/<timestamp>/`.
- The archive preserves the previous outputs and written notes.
- Untouched notebooks are replaced directly.

## Data refresh

**Refresh Project Data** rescans source files, preserves configured table names and key
choices where possible, rebuilds the project database, and refreshes an untouched managed
notebook. A notebook containing learner work or outputs is preserved.

## Legacy cleanup

The former workflow produced standalone setup SQL, validation SQL, and findings files.
During migration:

- Untouched generated files are deleted.
- Edited managed files are archived.
- Learner-created files without a managed marker are left alone.
- Cleanup actions are recorded in `documentation/portfolio_workspace_migration.md`.
