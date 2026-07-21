<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Build dashboards

**Project:** Movie Industry Financial Analytics  
**Stage:** Power BI  
**Estimated focused time:** about 150 minutes  
**Guide updated:** 2026-07-21

## Purpose

Build report pages that answer the prioritized business questions with an intentional information hierarchy and appropriate visuals.

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
- `images/dashboard/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Map each report page to stakeholder questions and decisions.
2. Define the visual hierarchy before formatting.
3. Use the simplest visual that communicates each comparison.
4. Add governed KPI definitions and useful context.
5. Implement only decision-useful interactions.
6. Test filters, cross-highlighting, empty states, and accessibility.
7. Reconcile all displayed values and capture review screenshots.

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

Create the required report pages, add titles and metric definitions, use appropriate visuals and interactions, test filters, confirm accessibility and readability, and reconcile displayed values.

## Demonstrated skills

Completing this milestone may support evidence for:

- Dashboard design
- Business intelligence

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Refine the executive and operational pages, then validate all findings.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Build dashboards  
**Started:** 2026-07-21

## Page plan

| Page | Audience | Decision supported | KPIs | Main visuals | Filters/interactions | Key takeaway |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Build sequence

1. Sketch the information hierarchy before formatting.
2. Add validated measures.
3. Build the simplest visual that answers each question.
4. Add context such as targets, prior periods, or benchmarks.
5. Test interactions and empty states.
6. Perform accessibility and consistency review.
7. Reconcile displayed values with SQL.

## Quality checklist

- [ ] Each page answers a clear question.
- [ ] Important metrics are visible first.
- [ ] Titles describe the insight or purpose.
- [ ] Colors have consistent meaning.
- [ ] Labels and units are unambiguous.
- [ ] Visual clutter is removed.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
