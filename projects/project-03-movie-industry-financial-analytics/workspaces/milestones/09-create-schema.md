<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Create schema

**Project:** Movie Industry Financial Analytics  
**Stage:** SQL  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-21

## Purpose

Design the analytical tables and SQL data types before loading data. The schema should make table grain, keys, relationships, and constraints explicit.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Confirm the source or cleaned tables are registered in DuckDB.
- Review table grain and relationship-validation findings.
- Use explicit columns and preserve a reproducible setup path.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `sql/schema/`
- `sql/create_schema.sql`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Translate each approved table grain into a table definition.
2. Choose types that preserve identifiers, dates, decimals, and categorical values correctly.
3. Define primary and foreign keys where supported.
4. Add constraints only when the data and business rule justify them.
5. Separate raw, staging, and analytical layers where useful.
6. Run the schema from a clean database.
7. Inspect the created tables and document any DuckDB limitations.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] Queries run from a clean setup in the intended order.
- [ ] Output grain is stated and row counts or totals are independently checked.
- [ ] Joins do not silently multiply or discard records.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Using `SELECT *` in final analysis queries.
- Grouping at a different grain than the business question.
- Trusting a joined total without comparing pre- and post-join row counts.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Save executable schema SQL that creates every required table with appropriate types and keys; add comments or documentation for table grain; and run the script successfully in the project database.

## Demonstrated skills

Completing this milestone may support evidence for:

- SQL schema design
- Data types and constraints

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Load data in dependency order and reconcile source-to-table counts.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Create schema  
**Started:** 2026-07-21

## Plan the tables

| Table | Grain | Primary key | Foreign keys | Source file | Purpose |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Data-type decisions

| Field | Planned SQL type | Why | Null allowed? | Constraint or validation |
|---|---|---|---|---|
|  |  |  |  |  |  |

## Build steps

1. Create a script under `sql/schema/`.
2. Add `CREATE TABLE` statements in dependency order.
3. Use types that match the actual data, not only what the CSV parser guessed.
4. Add primary and foreign keys where supported and appropriate.
5. Add comments or companion documentation for grain and business meaning.
6. Run the script from a clean database.

## Validation

- [ ] Every table creates successfully.
- [ ] Column names and types match the data dictionary.
- [ ] Keys match the relationship plan.
- [ ] The script can be rerun safely or includes clear reset instructions.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
