<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Detect anomalies

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-21

## Purpose

Identify unusual records or patterns that could represent errors, operational exceptions, or meaningful business behavior.

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

- `reports/anomalies.csv`
- `documentation/anomaly_review.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Define what unusual means for each relevant metric or process.
2. Use business rules, distribution checks, or comparative baselines.
3. Produce a review table with identifiers and supporting context.
4. Inspect representative records from each anomaly pattern.
5. Classify patterns as data error, valid exception, or meaningful signal.
6. Document treatment and downstream impact.
7. Retain reproducible rules rather than manual record lists.

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

Define the anomaly rules, produce a reviewed anomaly table, inspect representative records, classify each pattern as error or valid exception, and document how it affects the analysis.

## Demonstrated skills

Completing this milestone may support evidence for:

- Anomaly detection
- Exception classification

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Apply the documented treatment before final metrics and insights.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Detect anomalies  
**Started:** 2026-07-21

## Define anomaly rules

| Rule | Field(s) | Threshold or logic | Business reason | Expected frequency |
|---|---|---|---|---|
|  |  |  |  |  |

## Review results

| Record or group | Rule triggered | Error or valid exception? | Evidence | Action | Analysis impact |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Done check

- [ ] Rules are documented before removing records.
- [ ] Representative anomalies were inspected manually.
- [ ] Valid extreme values were not automatically discarded.
- [ ] Cleaning and analysis decisions are traceable.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
