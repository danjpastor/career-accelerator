<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Document assumptions

**Project:** Retail Operations Performance Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 35 minutes  
**Guide updated:** 2026-07-21

## Purpose

Record the assumptions required to interpret the data and analysis so reviewers can distinguish known facts from analyst judgment.

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

- `documentation/assumptions.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. List every place where the project relies on judgment or incomplete information.
2. Explain why each assumption is necessary.
3. Describe how the assumption affects metrics, filters, or recommendations.
4. Test the assumption where the data allows.
5. Rate the risk if the assumption is wrong.
6. Identify the information needed to replace it with a verified fact.

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

Document each assumption, why it was needed, its effect on the analysis, how it was tested where possible, and what would change if the assumption were wrong.

## Demonstrated skills

Completing this milestone may support evidence for:

- Analytical judgment
- Risk documentation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Carry material assumptions into metric definitions, findings, and final limitations.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Document assumptions  
**Started:** 2026-07-21

| ID | Assumption | Why needed | Evidence or test | Effect if wrong | Status |
|---|---|---|---|---|---|
| A-01 |  |  |  |  | Open / Supported / Rejected |

## Categories to consider

- Date and reporting-period assumptions
- Missing-value interpretation
- Business-rule assumptions
- Synthetic-data realism
- KPI denominator and filter assumptions
- Relationship and grain assumptions
- Currency, units, time zone, and locale

## Done check

- [ ] Assumptions are separated from known facts.
- [ ] Material assumptions include an impact statement.
- [ ] Assumptions are tested where possible.
- [ ] Rejected assumptions are reflected in the analysis.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
