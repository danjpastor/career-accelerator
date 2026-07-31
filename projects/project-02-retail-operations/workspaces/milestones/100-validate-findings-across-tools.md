<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 4 -->

# Validate findings across tools

**Project:** Retail Operations Performance Dashboard  
**Stage:** Validation  
**Estimated focused time:** about 90 minutes

## What you're doing

Compare the headline numbers across SQL, Python, and Power BI and work out why any values do not match.

Use the Studio or Notebook tab in this milestone when one is available. Open an external tool only when the work genuinely belongs there, such as Power BI or a spreadsheet editor.

## Why it matters

The headline numbers should agree because the logic agrees, not by accident.

## Before you start

- Choose the small set of metrics and findings that will appear in the final report.
- Have the final SQL, Python, and Power BI results available.

## Steps

1. Open Results Verification.
2. Add each headline metric that will be published.
3. Enter the independently calculated values from SQL, Python, and Power BI.
4. Use a tolerance only when rounding makes it reasonable.
5. Investigate every mismatch in filters, dates, joins, null handling, and calculation rules.
6. Fix the source logic or write a clear resolution note.
7. Save the final verification matrix.

## You're done when

- [ ] Every number that will be published is confirmed or has a clear note explaining the mismatch and final decision.
- [ ] Every published metric matches across the tools used for that metric.
- [ ] Any remaining difference has a clear reason and an approved final value.
- [ ] You saved the real project artifact, not only a note inside Career Accelerator.
- [ ] Any assumptions, exceptions, and unresolved questions are easy to find.

## What to save

- `documentation/findings_validation.md`
- `documentation/findings_validation.csv`

Keep only the files that help another analyst understand or reproduce the work.

## Keep in mind

- Do not force values to match by changing a number manually.
- Do not compare results that use different filters or time periods.

## Next step

Use confirmed findings and governed metrics in Power BI.

## Working notes

**Milestone:** Validate findings across tools  
**Started:** 2026-07-31

## Findings validation matrix

| Finding | Original result | Independent check | Alternative explanation tested | SQL/Python/BI agree? | Final status |
|---|---|---|---|---|---|
|  |  |  |  |  | Confirmed / Revised / Unsupported |

## Required checks

- Recalculate headline metrics using a second query or method.
- Reconcile totals with source or processed files.
- Test the effect of nulls, filters, date boundaries, and duplicates.
- Compare SQL, Python, and dashboard results where more than one tool is used.
- Inspect the records behind surprising results.
- Separate correlation from causation.

## Discrepancy log

| Discrepancy | Cause | Correction | Files updated |
|---|---|---|---|
|  |  |  |  |

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add short notes, decisions, unresolved questions, or links to the finished artifact.
