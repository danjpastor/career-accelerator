<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Clean and validate data

**Project:** Retail Operations Performance Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 120 minutes  
**Guide updated:** 2026-07-21

## Purpose

Profile the raw data, define reproducible cleaning rules, produce cleaned outputs, and prove that the cleaning did not create new errors.

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

- `data/processed/`
- `sql/cleaning/`
- `notebooks/clean_data.ipynb`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Profile row counts, nulls, duplicates, categories, ranges, and date logic.
2. Create an issue log that separates errors from valid exceptions.
3. Define a reproducible rule for each confirmed issue.
4. Implement transformations in SQL or Python without editing raw sources.
5. Write cleaned outputs to staging or processed locations.
6. Repeat key, relationship, and business-rule checks on cleaned data.
7. Compare before-and-after row counts and explain every difference.
8. Preserve unresolved exceptions with an explicit downstream rule.

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

Save the profiling results, cleaning rules, reproducible cleaning code, before-and-after row counts, validation checks, exception log, and cleaned files in data/processed or data/staging.

## Demonstrated skills

Completing this milestone may support evidence for:

- Data cleaning
- Quality assurance

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use validated processed data for schema loading, analysis, and dashboards.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Clean and validate data  
**Started:** 2026-07-21

## 1. Profile before cleaning

Record for each table:

| Table | Rows | Duplicate keys | Missing required values | Invalid types | Invalid categories/ranges | Date issues |
|---|---:|---:|---:|---:|---:|---:|
|  |  |  |  |  |  |  |

## 2. Cleaning rule register

| Issue | Detection rule | Cleaning action | Why this action is valid | Rows affected | Reversible? |
|---|---|---|---|---:|---|
|  |  |  |  |  | Yes / No |

## 3. Required outputs

- Preserve original files under `data/raw/`.
- Put intermediate files under `data/staging/`.
- Put final analysis-ready files under `data/processed/`.
- Save reproducible code in SQL or Python rather than editing cells manually.

## 4. Validate after cleaning

| Check | Before | After | Expected | Pass? | Notes |
|---|---:|---:|---:|---|---|
| Row count |  |  |  |  |  |
| Unique primary keys |  |  |  |  |  |
| Required values present |  |  |  |  |  |
| Valid relationships |  |  |  |  |  |

## Completion checklist

- [ ] Every transformation is documented.
- [ ] Raw files remain unchanged.
- [ ] Processed files can be recreated from code.
- [ ] Before-and-after validation is saved.
- [ ] Unresolved issues are listed explicitly.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
