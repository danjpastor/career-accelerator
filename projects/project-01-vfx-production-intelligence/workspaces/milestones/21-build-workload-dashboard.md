<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Build workload dashboard

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Power BI  
**Estimated focused time:** about 105 minutes  
**Guide updated:** 2026-07-21

## Purpose

Create an operational page that helps production leaders understand workload, capacity, schedule risk, and where attention is needed.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Use the validated analytical layer rather than raw source files where possible.
- Reconcile source row counts and headline measures before formatting visuals.
- Review the approved KPI definitions and stakeholder questions.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `power-bi/`
- `images/dashboard/workload.png`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Define capacity, assigned work, actual effort, and schedule risk consistently.
2. Choose the operational grain and reporting period.
3. Build measures for workload, utilization, backlog, and risk.
4. Show useful team, project, status, and time breakdowns.
5. Provide drill paths to the records requiring action.
6. Test capacity edge cases and missing assignments.
7. Reconcile totals with SQL and document interpretation.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] Model relationships and filter directions are intentional.
- [ ] Headline measures reconcile with independently calculated SQL totals.
- [ ] Filters, empty states, and combined selections behave predictably.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Building visuals before validating the model and measures.
- Using implicit aggregations for governed KPIs.
- Adding slicers or drill paths that do not support a decision.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Build the workload page with agreed capacity and workload measures, useful breakdowns, risk indicators, filters, drill paths, and a documented interpretation; reconcile totals with SQL.

## Demonstrated skills

Completing this milestone may support evidence for:

- Operational analytics
- Capacity reporting

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Connect operational risks to recommendations and supporting detail.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Build workload dashboard  
**Started:** 2026-07-21

## Operational questions

- Where is workload above capacity?
- Which teams, artists, projects, or periods have the highest schedule risk?
- Which work is overdue, blocked, or repeatedly revised?
- Where can work be rebalanced?

## Page specification

| Visual or KPI | Grain | Business rule | User action supported | Validation |
|---|---|---|---|---|
|  |  |  |  |  |

## Required checks

- [ ] Capacity and workload use compatible time units.
- [ ] Unassigned and inactive resources are handled explicitly.
- [ ] Risk thresholds are documented.
- [ ] Users can move from summary to relevant detail.
- [ ] Totals reconcile with SQL or source data.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
