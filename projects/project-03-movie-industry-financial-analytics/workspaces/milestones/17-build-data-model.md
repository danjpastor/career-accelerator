<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Build data model

**Project:** Movie Industry Financial Analytics  
**Stage:** Overview  
**Estimated focused time:** about 105 minutes  
**Guide updated:** 2026-07-21

## Purpose

Build a Power BI model with clear fact and dimension roles, correct relationships, a dedicated date table, and predictable filter behavior.

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

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Classify tables as facts, dimensions, bridges, or supporting tables.
2. Confirm table grain and keys before creating relationships.
3. Build one-to-many relationships with intentional filter direction.
4. Create and mark a dedicated date table.
5. Hide technical keys and organize user-facing fields.
6. Check ambiguous paths and unexplained many-to-many relationships.
7. Reconcile row counts and baseline metrics with SQL.

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

Save the model with documented table grains, one-to-many relationships where appropriate, no unexplained many-to-many relationships, an active date table, hidden technical fields, and reconciled row and KPI totals.

## Demonstrated skills

Completing this milestone may support evidence for:

- Power BI data modeling
- Dimensional modeling

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Build and validate explicit DAX measures on the approved model.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Build data model  
**Started:** 2026-07-21

## Table roles

| Table | Fact / Dimension / Bridge | Grain | Key | Main measures or attributes |
|---|---|---|---|---|
|  |  |  |  |  |

## Relationship plan

| From table/key | To table/key | Cardinality | Filter direction | Active? | Why |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Build checklist

- [ ] A dedicated date table is created and marked as a date table.
- [ ] Fact and dimension grains are documented.
- [ ] Relationships use the intended keys.
- [ ] Many-to-many and bidirectional relationships are avoided unless justified.
- [ ] Technical key fields are hidden from report users.
- [ ] Headline totals reconcile with SQL.
- [ ] A model-view screenshot is saved.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
