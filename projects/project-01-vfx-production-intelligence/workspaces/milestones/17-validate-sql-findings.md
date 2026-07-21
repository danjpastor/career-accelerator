<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Validate SQL findings

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-21

## Purpose

Challenge the analysis before presenting it by reconciling totals, checking alternative explanations, and confirming that SQL, Python, and dashboard outputs agree.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Identify the authoritative source for every metric being compared.
- Preserve the original outputs so discrepancies can be traced.
- Do not resolve differences silently; document the cause and decision.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `documentation/findings_validation.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. List every finding intended for the dashboard or executive summary.
2. Recalculate each headline metric independently.
3. Compare SQL, Python, and Power BI results under identical filters.
4. Test alternative explanations, segments, and time windows.
5. Review nulls, exclusions, and denominator definitions.
6. Classify each finding as confirmed, revised, unsupported, or pending.
7. Document discrepancies and the chosen source of truth.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] Every major finding is marked confirmed, revised, unsupported, or pending.
- [ ] Discrepancies include a documented root cause and chosen source of truth.
- [ ] Edge cases and alternative explanations are tested.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Accepting matching rounded values as proof of agreement.
- Changing one output to match another without locating the source of the difference.
- Ignoring nulls, exclusions, or filter context during reconciliation.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Recalculate key metrics independently, compare outputs across tools, test edge cases and filters, explain discrepancies, and mark each major finding as confirmed, revised, or unsupported.

## Demonstrated skills

Completing this milestone may support evidence for:

- Result validation
- Cross-tool reconciliation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Only confirmed findings should enter dashboards and executive communication.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Validate SQL findings  
**Started:** 2026-07-21

## Findings validation matrix

| Finding | Original result | Independent check | Alternative explanation tested | SQL/Python/BI agree? | Final status |
|---|---|---|---|---|---|
|  |  |  |  |  | Confirmed / Revised / Unsupported |

## Required checks

- Recalculate headline metrics using a second query or method.
- Reconcile totals with source or processed files.
- Test the effect of nulls, filters, date boundaries, and duplicates.
- Compare SQL, Python, and dashboard results where more than one tool is used.
- Inspect the records behind surprising results.
- Separate correlation from causation.

## Discrepancy log

| Discrepancy | Cause | Correction | Files updated |
|---|---|---|---|
|  |  |  |  |

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
