<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Create derived metrics

**Project:** Movie Industry Financial Analytics  
**Stage:** Overview  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-21

## Purpose

Create calculated fields and analytical features that are required for the approved KPIs and business questions.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Open the generated project workspace and select the Career Accelerator kernel.
- Keep raw files unchanged and write outputs to staging, processed, or reports folders.
- Tie every transformation or chart to an approved business question or quality finding.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `documentation/derived_metrics.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Trace each derived field to an approved KPI or business question.
2. Define formula, grain, type, units, and source fields.
3. Specify edge cases, null handling, and zero-denominator behavior.
4. Implement calculations in the authoritative analytical layer.
5. Test representative records manually.
6. Reconcile aggregate results with source values.
7. Document the metric so SQL, Python, and Power BI use the same rule.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] The notebook or script runs top-to-bottom without manual hidden state.
- [ ] Outputs are written to documented paths and raw sources remain unchanged.
- [ ] Key totals and derived values reconcile with SQL or source checks.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Relying on notebook execution order instead of a reproducible top-to-bottom run.
- Applying transformations without recording before-and-after checks.
- Creating charts because columns exist rather than because they answer a question.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Document and calculate each derived field with its formula, grain, data type, edge-case handling, and validation; confirm that the results reconcile with source values.

## Demonstrated skills

Completing this milestone may support evidence for:

- Feature engineering
- Metric validation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use the governed definitions consistently in SQL, Python, and Power BI.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Create derived metrics  
**Started:** 2026-07-21

| Derived field | Business purpose | Formula | Input fields | Grain | Null/zero handling | Validation |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Validation checklist

- [ ] Units are consistent.
- [ ] Date periods align.
- [ ] Ratios handle zero denominators.
- [ ] Categories are mutually exclusive where required.
- [ ] Aggregated results reconcile with source totals.
- [ ] The same metric is defined consistently across SQL, Python, and Power BI.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
