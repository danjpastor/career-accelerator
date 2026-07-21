<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Create synthetic data specification

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Overview  
**Estimated focused time:** about 90 minutes  
**Guide updated:** 2026-07-21

## Purpose

Specify the tables, fields, relationships, date range, row volumes, business rules, and intentional quality issues needed before generating synthetic data.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Preserve all files under `data/raw/` unchanged.
- Review the approved business questions and KPI definitions.
- Confirm table grain, candidate keys, and required relationships before transforming data.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `documentation/synthetic_data_specification.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Define one row's meaning for every table.
2. Specify primary keys, foreign keys, and relationship cardinality.
3. List each field with type, allowed range, null behavior, and business meaning.
4. Set realistic row volumes and date coverage.
5. Define distributions and correlations needed for realistic analysis.
6. Specify business rules that must always hold.
7. Add intentional data-quality issues that will exercise cleaning skills.
8. Verify that the design can answer every approved business question.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] Raw source files remain unchanged.
- [ ] Row counts, columns, data types, and keys are reconciled before and after any transformation.
- [ ] Every exception is classified as corrected, intentionally retained, excluded, or unresolved.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Editing raw files directly.
- Treating repeated foreign keys as duplicate entity records.
- Cleaning exceptions before documenting why they are exceptions.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Complete the specification with table grains, primary and foreign keys, column definitions, realistic distributions, relationship rules, row counts, date range, and intentional errors; review it against every business question.

## Demonstrated skills

Completing this milestone may support evidence for:

- Data specification
- Data modeling

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use the approved specification to generate the raw dataset without changing the business rules.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Create synthetic data specification  
**Started:** 2026-07-21

## 1. Business coverage

- Business problem supported:
- Questions the data must answer:
- Date range:
- Expected scale:

## 2. Table plan

| Table | One row represents | Primary key | Expected rows | Parent tables | Purpose |
|---|---|---|---:|---|---|
|  |  |  |  |  |  |

## 3. Relationship plan

| Parent table | Parent key | Child table | Foreign key | Expected relationship | Required? |
|---|---|---|---|---|---|
|  |  |  |  | One-to-many | Yes / No |

## 4. Field specification

For each table, document:

| Field | Type | Meaning | Allowed values/range | Missing allowed? | Generation rule |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 5. Realistic behavior

- Important distributions:
- Seasonal or time patterns:
- Correlations that should exist:
- Business rules that must always hold:
- Rare but valid exceptions:

## 6. Intentional quality issues

| Issue | Table/field | Approximate frequency | Reason included | Expected cleaning response |
|---|---|---:|---|---|
|  |  |  |  |  |

## 7. Validation before generation

- [ ] Every business question maps to required fields.
- [ ] Every table has a clear grain and key.
- [ ] Relationships are defined before rows are generated.
- [ ] Row volumes are realistic for the project.
- [ ] Intentional errors are documented and bounded.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
