<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Review and finalize data dictionary

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 45 minutes  
**Guide updated:** 2026-07-22

## Purpose

Audit the existing generated data dictionary against the actual schemas rather than recreating documentation already produced by earlier milestones.

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

- `DATA_DICTIONARY.md`
- `documentation/data_dictionary.md`
- `documentation/data_dictionary.csv`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Open the existing generated data dictionary; do not create a second dictionary.
2. Compare its table list with Data Explorer and project_sources.yaml.
3. Compare every documented column with DuckDB's detected schema.
4. Add missing business definitions, key roles, null meanings, units, allowed values, and authoritative-source notes.
5. Update descriptions affected by relationship validation or cleaning decisions.
6. Remove obsolete fields and document derived fields in their authoritative analytical layer.
7. Confirm all KPIs and business questions trace to documented fields.

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

Every current table and column is represented; types, business definitions, key roles, null meanings, units, allowed values, and important cleaning rules are accurate.

## Demonstrated skills

Completing this milestone may support evidence for:

- Metadata management
- Schema documentation
- Data governance

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use approved field definitions during cleaning, schema design, analysis, and reporting.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

- [ ] Record your work, decisions, and validation results here.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
