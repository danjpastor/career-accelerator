<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Approve data source and specification

**Project:** Retail Operations Performance Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 60 minutes

## What you're doing

Review where the data comes from, what each table represents, what it covers, and whether it can answer the approved questions.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

The project can only answer questions that the planned data can support.

## Before you start

- Keep the approved project brief open for reference.
- Review any supplied data specification or source notes.

## Steps

1. Open the Data Source Studio.
2. Record where the data comes from and how it may be used.
3. Describe the expected tables, row grain, date coverage, and required fields.
4. Check that each business question can be answered with the planned fields.
5. Write down limits, gaps, or synthetic-data rules.
6. Approve the source when it is suitable for the project.

## You're done when

- [ ] The source is documented, its limits are clear, and it contains the information needed for the project.
- [ ] The source, coverage, grain, required fields, and limits are clear.
- [ ] The approved questions are supported by the planned data.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `documentation/data_source_review.md`
- `documentation/data_source_manifest.csv`
- `config/project_sources.yaml`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not approve a source only because it is convenient.
- Do not hide gaps that may affect the final conclusions.

## Next step

Create or acquire the immutable raw dataset.

## Working notes

**Milestone:** Approve data source and specification  
**Started:** 2026-08-08

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

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
