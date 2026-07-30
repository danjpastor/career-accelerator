<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Build reproducible analytical database

**Project:** VFX Production Intelligence Dashboard  
**Stage:** SQL  
**Estimated focused time:** about 120 minutes

## What you're doing

Write a repeatable script that builds the analytical database from the reviewed cleaned data.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

A repeatable build makes the analytical data easy to check and rebuild.

## Before you start

- Finish and register the reviewed cleaned datasets.
- Know the table names, grains, keys, and load order.

## Steps

1. Open the Database Build tab.
2. Write the SQL that creates and loads the analytical tables or views.
3. Use the reviewed cleaned files as the inputs.
4. Add the checks needed to confirm row counts, keys, and relationships.
5. Run Rebuild from Script.
6. Fix any error and run the complete script again.
7. Save the final build script.

## You're done when

- [ ] The database can be rebuilt from the saved script, contains the expected tables, and passes the final loading checks.
- [ ] The database is created from the saved script in one clean run.
- [ ] The expected analytical tables are present.
- [ ] The final load and validation checks pass or have clear notes.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `sql/schema/build_analytical_database.sql`
- `data/working/analytical.duckdb`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not rely on manual database changes that are missing from the script.
- Do not load unreviewed raw files into the final analytical layer.

## Next step

Use the governed analytical layer to complete SQL analysis.

## Working notes

**Milestone:** Build reproducible analytical database  
**Started:** 2026-07-30

## Plan the tables

| Table | Grain | Primary key | Foreign keys | Source file | Purpose |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Data-type decisions

| Field | Planned SQL type | Why | Null allowed? | Constraint or validation |
|---|---|---|---|---|
|  |  |  |  |  |  |

## Build steps

1. Create a script under `sql/schema/`.
2. Add `CREATE TABLE` statements in dependency order.
3. Use types that match the actual data, not only what the CSV parser guessed.
4. Add primary and foreign keys where supported and appropriate.
5. Add comments or companion documentation for grain and business meaning.
6. Run the script from a clean database.

## Validation

- [ ] Every table creates successfully.
- [ ] Column names and types match the data dictionary.
- [ ] Keys match the relationship plan.
- [ ] The script can be rerun safely or includes clear reset instructions.

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
