<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Write analysis queries

**Project:** Retail Operations Performance Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 150 minutes  
**Guide updated:** 2026-07-21

## Purpose

Write organized SQL that directly answers the approved business questions and produces interpretable, validated results.

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

- `sql/analysis/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Create a query index tied to the approved business questions.
2. State the required output grain before writing each query.
3. Build and validate joins before adding calculations.
4. Use readable CTEs or staged views for complex logic.
5. Calculate governed KPIs from their approved definitions.
6. Validate totals, filters, null behavior, and edge cases.
7. Save final outputs or result checkpoints with interpretation notes.

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

Save one clearly labeled query or query section per business question; include comments, readable CTEs or aliases, explicit grain, and result validation; export or document the final outputs.

## Demonstrated skills

Completing this milestone may support evidence for:

- SQL analysis
- Business-question translation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Package final queries and validate findings across tools.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Write analysis queries  
**Started:** 2026-07-21

## Query index

| Question ID | Business question | Required grain | Main tables | Metric/output | SQL file | Validation |
|---|---|---|---|---|---|---|
| Q01 |  |  |  |  |  |  |

## Query workflow

For each question:

1. Restate the question and expected output grain.
2. Identify the minimum required tables.
3. Validate joins before calculating metrics.
4. Build the result in readable steps or CTEs.
5. Check row counts and totals.
6. Save the final query with comments.
7. Record the result and interpretation without overstating causality.

## Findings log

| Question | Key result | Supporting value | Validation completed | Limitation | Follow-up |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
