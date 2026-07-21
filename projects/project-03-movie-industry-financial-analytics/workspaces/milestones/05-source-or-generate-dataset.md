<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Source or generate dataset

**Project:** Movie Industry Financial Analytics  
**Stage:** Dataset  
**Estimated focused time:** about 75 minutes  
**Guide updated:** 2026-07-21

## Purpose

Obtain or create a dataset that can answer the project questions while preserving a clearly documented raw-data source.

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

- `data/raw/`
- `documentation/data_source_manifest.md`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Confirm whether the source is public, licensed, internal, or synthetic.
2. Place untouched source files under `data/raw/`.
3. Record provenance, generation method, retrieval date, and usage constraints.
4. Create a source manifest with filenames, formats, row counts, and table grains.
5. Verify required tables and fields against the business questions.
6. Inspect representative rows without modifying the source.
7. Record missing fields, coverage gaps, and planned mitigations.

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

Place untouched source files in data/raw, record where they came from or how they were generated, confirm licensing or synthetic status, list row counts, and verify that the required tables and fields exist.

## Demonstrated skills

Completing this milestone may support evidence for:

- Data sourcing
- Source documentation

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use the immutable raw sources for relationship validation and the data dictionary.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Source or generate dataset  
**Started:** 2026-07-21

## Source record

- Source or generation method:
- Download or generation date:
- License or synthetic-data disclosure:
- Original location:
- Raw files stored under:
- Files that must remain unchanged:

## File manifest

| File | Table represented | Rows | Columns | Date range | Notes |
|---|---|---:|---:|---|---|
|  |  |  |  |  |  |

## Coverage check

| Required business question or KPI | Required table/fields | Available? | Gap or action needed |
|---|---|---|---|
|  |  | Yes / No / Partial |  |

## Initial inspection

- Encoding and delimiter:
- Header quality:
- Obvious missing values:
- Duplicate-file or duplicate-row risk:
- Date and numeric parsing concerns:
- Sensitive or private information:

## Done check

- [ ] Raw files are preserved unchanged.
- [ ] Source and licensing/synthetic status are documented.
- [ ] Row and column counts are recorded.
- [ ] Required fields are confirmed.
- [ ] Known gaps are documented before analysis begins.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
