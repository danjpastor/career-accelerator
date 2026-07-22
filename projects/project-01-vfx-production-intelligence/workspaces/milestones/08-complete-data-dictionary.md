<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Complete data dictionary

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-22

## Purpose

Create a field-level reference that explains what each column means and how it should be interpreted during cleaning, analysis, and reporting.

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

- `documentation/data_dictionary.md`
- `documentation/data_dictionary.csv`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Inventory every retained field across all source and analytical tables.
2. Record table grain and identify primary, foreign, derived, and sensitive fields.
3. Describe business meaning rather than repeating the column name.
4. Document type, unit, allowed values, range, null meaning, and source.
5. Record transformations and authoritative source rules.
6. Check that every KPI and business question can trace to documented fields.
7. Review ambiguous fields with the project assumptions.

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

Document every retained field with table, data type, business meaning, grain, allowed values or range, missing-value meaning, source, transformation notes, and whether it is a key or sensitive field.

## Demonstrated skills

Completing this milestone may support evidence for:

- Data documentation
- Metadata management

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use field definitions during cleaning, schema design, analysis, and dashboard modeling.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Complete data dictionary  
**Started:** 2026-07-22

## Instructions

Document the fields actually used by the project. Describe business meaning, not only the technical column name.

| Table | Field | Type | One row represents / grain | Business meaning | Key role | Allowed values or range | Missing-value meaning | Source | Transformation or validation notes |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  | Primary / Foreign / None |  |  |  |  |

## Table-level notes

For each table document:

- Table purpose:
- One row represents:
- Primary key:
- Parent and child relationships:
- Expected row count:
- Important filters or exclusions:

## Done check

- [ ] Every retained field is documented.
- [ ] Keys and relationships are identified.
- [ ] Categorical values and units are explained.
- [ ] Missing values have an interpretation.
- [ ] Transformations are traceable to cleaning code.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.

## Preserved content from the previous guide

> The previous document is retained below so no learner work is lost. Move only useful decisions into the Learner work section when convenient.

# VFX Production Intelligence Dashboard — Data Dictionary

**Milestone:** Complete data dictionary  
**Started:** 2026-07-21

## Instructions

Document the fields actually used by the project. Describe business meaning, not only the technical column name.

| Table | Field | Type | One row represents / grain | Business meaning | Key role | Allowed values or range | Missing-value meaning | Source | Transformation or validation notes |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  | Primary / Foreign / None |  |  |  |  |

## Table-level notes

For each table document:

- Table purpose:
- One row represents:
- Primary key:
- Parent and child relationships:
- Expected row count:
- Important filters or exclusions:

## Done check

- [ ] Every retained field is documented.
- [ ] Keys and relationships are identified.
- [ ] Categorical values and units are explained.
- [ ] Missing values have an interpretation.
- [ ] Transformations are traceable to cleaning code.
