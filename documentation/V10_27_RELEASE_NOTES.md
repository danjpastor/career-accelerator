# Career Accelerator v10.27.0

## Unified planning

Career Accelerator now uses one deterministic runtime for Today’s Focus, Next Tasks, Coming Up, optional practice, and prerequisite state.

- Google Certificate work is always the first unfinished priority.
- Today’s Focus targets five tasks but only includes currently ready work.
- Next Tasks contains the next six ready items.
- Coming Up contains locked items and exact unlock requirements.
- Optional Practice replaces Get Ahead and never modifies the required plan.
- The former Adaptive Planner page is now a simplified Daily Plan view; manual defer/block controls and the raw sprint backlog are removed from the planning workflow.

## Unified learning path

The Data Analytics pathway follows:

1. Spreadsheets
2. SQL
3. Power BI
4. Python and pandas
5. Portfolio Readiness
6. Portfolio execution

DuckDB and interview problems appear only after the corresponding SQL lessons and mastery requirements are complete.

## Program cleanup

- Retired active DataCamp catalogs, task generation, and prerequisite evidence.
- Isolated the old planner as migration-only compatibility code.
- Removed active manual-focus and Added Today persistence.
- Removed copied catch-up prefixes from canonical task titles.
- Centralized SQL and DuckDB readiness presentation.

## Progress protection

The installer backs up source files and the learner database before migration. Existing Google, Academy, DuckDB, SQL Companion, portfolio, evidence, study-session, and application records are preserved.
