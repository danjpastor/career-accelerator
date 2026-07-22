<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Clean and validate analytical data

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 150 minutes  
**Guide updated:** 2026-07-22

## Purpose

Produce a reproducible cleaned analytical layer and prove that cleaning decisions preserve the intended grain and relationships.

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
- `notebooks/clean_data.ipynb`
- `sql/cleaning/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Create an issue log from profiling and relationship-validation findings.
2. Separate genuine errors from valid business exceptions.
3. Define a reproducible treatment for each confirmed issue.
4. Implement transformations without editing raw sources.
5. Write processed outputs to documented paths.
6. Re-run row-count, key, relationship, range, category, and business-rule checks.
7. Explain every before-and-after difference and preserve unresolved exceptions.

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

Processed data exists, raw inputs remain unchanged, every row-count change is explained, and key, relationship, and business-rule checks pass.

## Demonstrated skills

Completing this milestone may support evidence for:

- Data cleaning
- Quality assurance
- Exception handling

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Build the reproducible analytical database from the processed layer.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

- [ ] Record your work, decisions, and validation results here.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
