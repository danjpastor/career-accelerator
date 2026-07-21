<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Explore distributions

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 120 minutes  
**Guide updated:** 2026-07-21

## Purpose

Explore the data systematically to understand distributions, segments, trends, relationships, and potential quality issues before drawing conclusions.

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

- `notebooks/eda.ipynb`
- `reports/eda/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Begin with table grain, coverage, and descriptive summaries.
2. Examine distributions for measures and frequencies for categories.
3. Compare meaningful segments and time periods.
4. Investigate relationships relevant to approved business questions.
5. Identify anomalies and quality concerns without silently correcting them.
6. Create purposeful, labeled visuals with written interpretations.
7. Maintain a findings log that separates observation from hypothesis.

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

Complete the EDA checklist; save summary tables and purposeful charts; investigate notable patterns and anomalies; and write a short findings log linked to the business questions.

## Demonstrated skills

Completing this milestone may support evidence for:

- Exploratory data analysis
- Data visualization

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Promote validated patterns into anomaly rules, derived metrics, or candidate insights.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Explore distributions  
**Started:** 2026-07-21

## EDA questions

- What does one row represent in each table?
- Which fields are complete and reliable?
- What are the important category distributions?
- How are key numeric values distributed?
- What changes over time?
- Which segments differ meaningfully?
- Which records or patterns need investigation?

## Analysis log

| Question | Method | Output table/chart | Result | Business relevance | Follow-up |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Minimum coverage

- [ ] Dataset shape and types
- [ ] Missing values and duplicates
- [ ] Numeric distributions
- [ ] Categorical distributions
- [ ] Time trends where applicable
- [ ] Segment comparisons
- [ ] Outlier review
- [ ] Findings linked to business questions

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
