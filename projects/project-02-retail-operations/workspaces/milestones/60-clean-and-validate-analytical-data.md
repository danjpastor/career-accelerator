<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Clean and validate analytical data

**Project:** Retail Operations Performance Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 150 minutes

## What you're doing

Find data-quality problems, choose and apply the right fixes, and save reviewed cleaned datasets without changing the raw files.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

Cleaning decisions change the analysis, so they need to be deliberate and repeatable.

## Before you start

- Use the finalized dictionary and relationship findings.
- Keep all raw files unchanged.

## Steps

1. Open the Cleaning Notebook and profile the raw tables.
2. List the real quality problems and separate them from valid exceptions.
3. Choose SQL, Python, Google Sheets, or a local spreadsheet for each table.
4. Write or make the cleaning changes yourself.
5. Save each finished cleaned table and register it in Files & Outputs.
6. Compare the raw and cleaned shapes and run the final checks.
7. Write a short cleaning summary that explains what changed and why.

## You're done when

- [ ] Cleaned outputs are saved, the raw files are untouched, and every important change has been checked and explained.
- [ ] Every table has a reviewed cleaned output or a clear note explaining why no cleaning was needed.
- [ ] The notebook or working spreadsheet shows the learner's actual cleaning work.
- [ ] Important row, column, key, and business-rule changes have been checked and explained.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `data/processed/`
- `notebooks/clean_data.ipynb`
- `sql/cleaning/`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not remove unusual records just because they look inconvenient.
- Do not overwrite the raw files.
- Do not accept unexplained row loss or new duplicates.

## Next step

Build the reproducible analytical database from the processed layer.

## Working notes

- [ ] Record your work, decisions, and validation results here.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
