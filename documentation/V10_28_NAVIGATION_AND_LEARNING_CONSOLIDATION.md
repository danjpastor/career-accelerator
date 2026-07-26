# Career Accelerator v10.28.0 — Navigation and Learning Consolidation

## Final application shell

The active sidebar contains only destinations with a distinct learner purpose:

1. Dashboard
2. Learning
3. Portfolio Workspace
4. Study Session
5. Job Readiness
6. Applications
7. Publish & Git
8. Task Workspaces
9. Settings

Daily Plan is now the Dashboard planning engine rather than a duplicate page. Accelerator Academy is the Path section of Learning. SQL Companion is the Practice section of Learning. Weekly Summary is generated and reviewed through weekly Task Workspaces.

## Learning workspace

Learning contains four sections:

- **Path** — sequential Academy curriculum, embedded practice, mastery checks, and assessments.
- **Certificate** — Google Data Analytics Certificate progress and weekly target tracking.
- **Practice** — SQL Interview Problems and DuckDB Exercises.
- **Skills Lab** — applied labs and capstone-style work.

The legacy Exercise Packs browser and installer are retired. Shared feedback and collapsed-rail controls were moved into the active course UI library so Academy and Skills Lab no longer depend on a retired page module. Existing historical exercise-pack records and local pack folders are preserved but are not active application destinations.

## Task icons

Task icons are selected from canonical metadata rather than visible-title substitutions. Dashboard and workspace lists use distinct Google, spreadsheet, SQL, Power BI, Python, portfolio, review, assessment, lab, career, and general icons.

## Routing and migration

A single navigation registry owns all page indexes. Active task producers use the registry, and startup migration aligns persisted Learning, SQL, Portfolio, and Review task destinations with the consolidated shell. No completion, evidence, study-session, application, Academy, DuckDB, SQL, or portfolio progress is removed.
