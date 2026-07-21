<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Add filters and drill-through

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 60 minutes  
**Guide updated:** 2026-07-21

## Purpose

Add interactions that let users move from summary findings to the specific records or segments behind them without creating confusing filter behavior.

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

- `documentation/dashboard_interactions.md`
- `power-bi/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. List the decisions each filter or drill path supports.
2. Remove interactions that add exploration but not decision value.
3. Configure clear default and reset states.
4. Test single, combined, contradictory, and empty selections.
5. Verify cross-filtering and drill-through context.
6. Add titles or context that reflect active filters.
7. Document the final interaction behavior.

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

Add only decision-useful slicers and drill-through paths; document their purpose; test single and combined selections, reset behavior, empty states, and cross-filtering; fix any misleading interactions.

## Demonstrated skills

Completing this milestone may support evidence for:

- Dashboard interaction design
- Usability testing

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Complete usability testing before screenshots and publication.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Add filters and drill-through  
**Started:** 2026-07-21

## Interaction plan

| Interaction | Source page/visual | Destination or affected visuals | User question supported | Reset behavior |
|---|---|---|---|---|
| Slicer |  |  |  |  |
| Drill-through |  |  |  |  |

## Test matrix

| Test | Expected behavior | Actual behavior | Pass? | Fix |
|---|---|---|---|---|
| Single selection |  |  |  |  |
| Multiple selections |  |  |  |  |
| No matching records |  |  |  |  |
| Reset filters |  |  |  |  |
| Cross-filtering |  |  |  |  |

## Rule

Add an interaction only when it helps the user answer a real question. More slicers do not automatically make a dashboard better.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
