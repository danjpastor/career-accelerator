<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Review and finalize data dictionary

**Project:** Movie Industry Financial Analytics  
**Stage:** Dataset  
**Estimated focused time:** about 45 minutes

## What you're doing

Compare the existing data dictionary with the real tables and finish the definitions, rules, keys, and relationship notes.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

The dictionary gives every later step one trusted meaning for each field.

## Before you start

- Finish the relationship-validation notebook.
- Have the current raw tables and the existing dictionary available.

## Steps

1. Open the Data Dictionary Studio.
2. Use Project Tables to select one table and complete its business description, grain, primary-key decision, and table notes.
3. Choose each field from the middle panel and review the read-only counts, sample values, repeated values, invalid formats, and unmatched relationship values.
4. Complete the editable business definition, expected type, null rule, key role, uniqueness rule, allowed values or format, relationship, unit, and cleaning expectation.
5. Use Check Field for specific feedback. Explain any real warning in the review-decision field before marking the field reviewed.
6. Mark every field reviewed, then mark the table reviewed and continue to the next table.
7. Run Check Dictionary, open any result by double-clicking it, save Studio progress, and generate the final data-dictionary document.

## You're done when

- [ ] Every current field is documented clearly and there are no unexplained differences between the dictionary and the data.
- [ ] Every table has a documented description, grain, primary-key decision, and reviewed status.
- [ ] Every current field is documented and marked reviewed.
- [ ] Keys and relationships agree with the completed validation work.
- [ ] There are no unexplained fields missing from either the data or the dictionary.
- [ ] Check Dictionary passes and the generated Markdown document matches the saved Studio progress.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `DATA_DICTIONARY.md`
- `documentation/data_dictionary.md`
- `documentation/data_dictionary.csv`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not accept suggested business definitions without reviewing them.
- Do not describe a candidate key as proven when the validation found duplicates.

## Next step

Use approved field definitions during cleaning, schema design, analysis, and reporting.

## Working notes

**Milestone:** Review and finalize data dictionary  
**Started:** 2026-07-28

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

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
