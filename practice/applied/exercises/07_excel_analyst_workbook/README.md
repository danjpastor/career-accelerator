# Applied Lab 07: Build an end-to-end Excel analyst workbook

**Category:** Excel  
**Roadmap week:** 3  
**Estimated working time:** 105 minutes  
**Skills:** tables, validation, XLOOKUP, SUMIFS, PivotTables, Power Query, controls

## Scenario

You are the **operations director**. Separate operational CSV files need to become one refreshable Excel workbook with controlled calculations, reconciliation, and a one-page management summary.

## Your assignment

Build a refreshable Excel workbook that combines the operations CSV files, calculates reliable order and service metrics, reconciles revenue, and presents a one-page management summary.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Create the submission record first, then save a new `.xlsx` workbook in the Applied Labs submissions folder.
2. Import or link to the supplied data rather than editing the source CSV files.
3. Use named tables, clear sheet names, and a visible assumptions or controls area so another analyst can follow the workbook.

## Provided files

| File | Purpose |
|---|---|
| `customers.csv` | Customer attributes used for grouping and joins. |
| `finance_report.csv` | Independent finance totals used for reconciliation. |
| `orders.csv` | Order-level operational records. |
| `products.csv` | Product attributes, prices, or costs. |
| `returns.csv` | Return transactions that may contain multiple rows per order. |
| `targets.csv` | Regional or monthly performance targets. |
| `tickets.csv` | Support-ticket dates, status, and service information. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Refreshable 07_operations_analyst_workbook.xlsx saved in the Applied Labs submissions folder.
- Controls, Order Analysis, and one-page Management Summary sheets.
- Five management KPIs, a regional summary, and two useful charts.
- Revenue reconciliation to finance_report.csv with differences shown and explained.
- Management Summary screenshot and completed submission.md.

## Guided workflow

### 1. Create a new workbook in the submissions folder and define what one row represents in each source file

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Import all operations CSV files with Power Query, clean data types and region values, and load each source as a named table

- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Load sources as named queries or tables and keep the transformations in Power Query so **Refresh All** can reproduce them.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 3. Build one Order Analysis table with customer and product lookups, revenue calculations, returned quantities, and clear error handling

- Do not silently replace or remove the record. Count it, retain enough identifying information to investigate it, and state how it affects the result.
- Use table references and visible error handling. Confirm the lookup key is unique in the source and flag unmatched keys rather than replacing them with zero.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Create a Controls sheet with month and region dropdowns, metric definitions, assumptions, and refresh instructions

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 5. Build a Management Summary with five KPIs, a regional comparison, and two useful PivotCharts or charts

- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

### 6. Reconcile calculated monthly revenue to the Finance report, test the controls and Refresh All, and document every unresolved difference

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

### 7. Save the workbook and summary screenshot, then complete the guided submission record

- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Order Analysis remains one row per order and matches the Orders row count.
- [ ] Lookups, return calculations, and KPI totals are formula- or query-driven rather than typed manually.
- [ ] Month and region controls update the summary, and Refresh All does not duplicate data.
- [ ] Calculated revenue is compared with the Finance report and any mismatch is documented.
- [ ] The workbook includes clear metric definitions, assumptions, refresh instructions, and limitations.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Typing final values into the report instead of using formulas, queries, or PivotTables.
- Using full-column references or disconnected ranges that are hard to refresh.
- Allowing a lookup or merge to change the intended row grain.
- Hiding reconciliation differences instead of documenting them.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
