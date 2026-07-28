<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Create or acquire raw dataset

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 75 minutes

## What you're doing

Bring the original data files into the project and record where they came from without changing them.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

A protected raw layer gives the project a reliable starting point.

## Before you start

- Review the approved source and specification.
- Know which files or tables are expected.

## Steps

1. Open the Data Intake Studio.
2. Add or acquire the original source files.
3. Check that the expected files, tables, and columns are present.
4. Preview a few rows without editing the source.
5. Save the source inventory and fingerprints.
6. Leave the raw files unchanged for the rest of the project.

## You're done when

- [ ] Every required raw file is present, unchanged, and listed in the source manifest.
- [ ] Every required raw file is present and readable.
- [ ] The source inventory matches the files in the raw-data folder.
- [ ] The original files have not been cleaned or overwritten.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `data/raw/`
- `config/project_sources.yaml`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not fix values in the raw files.
- Do not mix cleaned outputs into the raw-data folder.

## Next step

Validate the table model and relationships before transformation.

## Working notes

**Milestone:** Create or acquire raw dataset  
**Started:** 2026-07-28

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
