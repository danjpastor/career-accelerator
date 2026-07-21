<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Define KPIs

**Project:** Retail Operations Performance Dashboard  
**Stage:** Discovery  
**Estimated focused time:** about 60 minutes  
**Guide updated:** 2026-07-21

## Purpose

Define the small set of metrics that will show whether the business problem is improving. Each KPI needs an exact formula and interpretation.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Review the project README and the most recent approved project scope.
- Confirm which stakeholder decision this milestone supports.
- Use only facts already supported by the project brief or source data; mark judgment as an assumption.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `documentation/kpi_definitions.md`
- `documentation/kpis.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Start from each approved stakeholder decision rather than from available columns.
2. Define each KPI in plain business language.
3. Write the exact numerator, denominator, aggregation, grain, filters, and time window.
4. Identify the source table and required fields.
5. Define null, zero, cancellation, and partial-period handling.
6. Choose a target, benchmark, or comparison when one is justified.
7. Write an independent validation rule for the final value.
8. Flag metrics that cannot yet be calculated and name the missing requirement.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] A new reviewer can identify the stakeholder, decision, scope, and success measure without additional explanation.
- [ ] Every statement is either supported, explicitly assumed, or marked for confirmation.
- [ ] The scope is narrow enough to be answered by the planned data and project timeline.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Writing a broad topic instead of a decision-focused problem.
- Listing stakeholders without explaining the decisions they make.
- Defining metrics without grain, filters, time windows, or validation rules.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Document each KPI with its business definition, formula, grain, filters, time window, data source, target or benchmark, and validation rule; flag any KPI that cannot yet be calculated.

## Demonstrated skills

Completing this milestone may support evidence for:

- KPI definition
- Metric governance

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use governed KPI definitions in business questions, SQL, Python, and Power BI.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Define KPIs  
**Started:** 2026-07-21

## Instructions

Define only metrics that directly support the approved business problem. A KPI is not complete until another analyst could reproduce it from the definition below.

## KPI register

| KPI | Business question supported | Exact formula | Grain | Filters/exclusions | Time window | Source fields | Target/benchmark | Validation |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |

## For each KPI, answer

- What does a higher value mean?
- What does a lower value mean?
- Can the metric be double-counted?
- What should happen when the denominator is zero?
- Which date determines the reporting period?
- Can the planned data calculate it reliably?

## Review checklist

- [ ] Every KPI has an exact formula.
- [ ] Grain and date logic are stated.
- [ ] Exclusions and null handling are stated.
- [ ] A validation method is defined.
- [ ] Unavailable KPIs are clearly flagged instead of invented.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
