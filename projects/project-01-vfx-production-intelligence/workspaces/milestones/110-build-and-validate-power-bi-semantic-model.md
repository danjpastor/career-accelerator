<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Build and validate Power BI semantic model

**Project:** VFX Production Intelligence Dashboard  
**Stage:** Power BI  
**Estimated focused time:** about 150 minutes

## What you're doing

Build the Power BI model, relationships, date table, and measures needed for the final report.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

A well-tested model keeps every report page on the same business logic.

## Before you start

- Use the reviewed analytical database and finalized relationship decisions.
- Keep the SQL validation totals available for comparison.

## Steps

1. Build the tables, relationships, date table, and measures in Power BI.
2. Open the Model Review tab beside the guide.
3. Work through each model check while testing the real `.pbix` file.
4. Compare the headline totals with SQL.
5. Save a model screenshot and short review note.

## You're done when

- [ ] The model behaves correctly under filters and its headline values match the approved SQL results.
- [ ] Every model-review check is complete.
- [ ] The saved screenshot shows the reviewed model.
- [ ] The final measures match the approved SQL values under tested filters.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `power-bi/`
- `documentation/dax_measures.md`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not create relationships before checking grain and keys.
- Do not hide a mismatch behind formatting or rounding.

## Next step

Build and test the report on the validated model.

## Working notes

**Milestone:** Build and validate Power BI semantic model  
**Started:** 2026-07-29

## Table roles

| Table | Fact / Dimension / Bridge | Grain | Key | Main measures or attributes |
|---|---|---|---|---|
|  |  |  |  |  |

## Relationship plan

| From table/key | To table/key | Cardinality | Filter direction | Active? | Why |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Build checklist

- [ ] A dedicated date table is created and marked as a date table.
- [ ] Fact and dimension grains are documented.
- [ ] Relationships use the intended keys.
- [ ] Many-to-many and bidirectional relationships are avoided unless justified.
- [ ] Technical key fields are hidden from report users.
- [ ] Headline totals reconcile with SQL.
- [ ] A model-view screenshot is saved.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
