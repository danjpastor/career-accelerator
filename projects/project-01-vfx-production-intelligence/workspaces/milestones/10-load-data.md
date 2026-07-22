<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Load data

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 60 minutes  
**Guide updated:** 2026-07-22

## Purpose

Load the source or cleaned files into the analytical database in a repeatable way and verify that the load matches the source files.

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

- `sql/load/`
- `sql/load_data.sql`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Create a repeatable load order based on parent-child dependencies.
2. Use explicit source paths and table names.
3. Load each required file without modifying the original.
4. Capture rejected, transformed, or skipped records.
5. Compare loaded row counts with the source manifest.
6. Inspect data types and five representative rows per table.
7. Rerun the load from a clean state to prove reproducibility.

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

Save a repeatable load script; load every required table; compare loaded row counts with the source manifest; inspect sample rows and data types; and document rejected or transformed records.

## Demonstrated skills

Completing this milestone may support evidence for:

- Reproducible data loading
- Row-count reconciliation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Run the complete SQL quality suite before analysis.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Load data  
**Started:** 2026-07-22

## Load plan

| Source file | Destination table | Expected rows | Transform during load? | Load order |
|---|---|---:|---|---:|
|  |  |  |  |  |

## Steps

1. Create a repeatable load script under `sql/load/` or a documented notebook.
2. Load parent tables before child tables when constraints are active.
3. Record parsing choices for dates, booleans, decimals, and missing values.
4. Do not silently discard rejected rows.

## Reconciliation

| Table | Source rows | Loaded rows | Rejected rows | Difference explained? |
|---|---:|---:|---:|---|
|  |  |  |  |  |

## Spot checks

- [ ] Sample text values were inspected.
- [ ] Date columns parsed correctly.
- [ ] Numeric fields are numeric.
- [ ] Primary keys remain unique.
- [ ] Foreign-key values were not altered unexpectedly.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
