# Portfolio Workspace v10.20.0

The Portfolio Workspace is a project command center. It does not replace the
project's real files with application-only notes.

## Tabs

### Overview

Renders the selected project's `README.md` as Markdown across the full tab.

### Milestones

Shows every portfolio task, stage, completion state, estimate, and detected
artifact. Open a milestone to use its detailed task guide.

### Data Explorer

Reads `config/project_sources.yaml` or discovers supported files under
`data/raw/`. It displays:

- all table schemas,
- DuckDB-inferred data types,
- candidate key indicators,
- source row counts,
- the first five rows of the selected table,
- and declared or inferred relationships.

The Data Explorer is read-only.

### Workbench

Indexes the actual project files and groups them into notebooks, SQL, Power BI,
reports, documentation, configuration, data, images, and other artifacts.

### Deliverables

Combines milestone status with expected artifact paths and actual file
detection. A milestone can therefore be complete while still being flagged as
missing its portfolio evidence artifact.

### Evidence & Readiness

Shows skills supported by completed milestones and detected artifacts, existing
Demonstrated Evidence rows, and task-guide coverage.

## Task guides

Every guide now contains:

- purpose and business context,
- prerequisites and inputs,
- expected artifact locations,
- a detailed task-specific workflow,
- investigation questions,
- validation checks,
- common mistakes,
- interpretation prompts,
- definition of done,
- demonstrated skills,
- and the next-step handoff.

Managed guide sections can be upgraded without overwriting learner work.
Existing generated documents are retained during migration.

## Legacy notes

Content previously stored in the generic stage-note tabs is preserved in
`documentation/legacy_portfolio_workspace_notes.md` for each affected project.
The original database records remain unchanged.
