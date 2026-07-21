<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Run quality checks

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 90 minutes  
**Guide updated:** 2026-07-21

## Purpose

Run SQL checks that establish whether the analytical tables are complete, valid, internally consistent, and safe to use for the project questions.

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

- `sql/validation/`
- `reports/data_quality/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Capture baseline table counts and grains.
2. Test candidate keys, required fields, accepted categories, ranges, and dates.
3. Test foreign keys and join cardinality.
4. Add project-specific cross-field and cross-table rules.
5. Summarize failures by rule and affected record count.
6. Classify each failure and identify its downstream risk.
7. Save queries and results so they can be rerun after changes.

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

Save and run checks for row counts, key uniqueness, missing required values, invalid categories or ranges, date logic, duplicates, and relationship integrity; record every exception and its resolution.

## Demonstrated skills

Completing this milestone may support evidence for:

- SQL data-quality testing
- Exception analysis

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Resolve or document exceptions before answering business questions.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Run quality checks  
**Started:** 2026-07-21

Save the checks under `sql/validation/` and record the results here.

## Required checks

| Check | Table/field | SQL file or query section | Expected result | Actual result | Pass? | Action |
|---|---|---|---|---|---|---|
| Row count |  |  |  |  |  |  |
| Primary-key uniqueness |  |  | Zero duplicates |  |  |  |
| Required values |  |  | Zero unexpected nulls |  |  |  |
| Allowed categories/ranges |  |  |  |  |  |  |
| Date logic |  |  |  |  |  |  |
| Relationship integrity |  |  | Zero unexpected orphans |  |  |  |
| Reconciliation total |  |  |  |  |  |  |

## Completion rules

- A check is not “passed” merely because the query ran.
- Explain every exception.
- Separate intentional synthetic issues from accidental pipeline errors.
- Save the final validated query set and results.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
