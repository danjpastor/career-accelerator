<!-- Career Accelerator Applied Lab 07: Build an end-to-end Excel analyst workbook -->

# Applied Lab 07 Submission

## Lab
**Build an end-to-end Excel analyst workbook**

## Artifact path
Record any `.pbix`, `.xlsx`, image, recording, or other external artifact path.

`TODO`

## Work completed
- TODO

## Findings or decisions
TODO

## Validation performed
- TODO

## What this demonstrates
Excel analysis, controls, and management reporting

## Reflection
What changed after validation, and what would you explain in an interview?

<!-- BEGIN EXCEL WORKBOOK STUDIO -->
## Excel Workbook Studio progress

- Workbook: `C:\Users\Dan\Documents\MEGA\Dev\GitHub\career-accelerator\practice\applied\submissions\07_operations_analyst_workbook.xlsx`
- Management Summary screenshot: `C:\Users\Dan\Documents\MEGA\Dev\GitHub\career-accelerator\practice\applied\submissions\07_management_summary.png`
- Last Studio update: 2026-07-27T23:06:48

### Guided stages

- [ ] Stage 1: Define the workbook and source grain
- [ ] Stage 2: Import and profile the source files
- [ ] Stage 3: Build the Order Analysis table
- [ ] Stage 4: Create the Controls sheet
- [ ] Stage 5: Build the Management Summary
- [ ] Stage 6: Reconcile revenue and test refresh
- [ ] Stage 7: Complete the analyst handoff

### Final verification

- [ ] Order Analysis has 12 unique order rows.
- [ ] Lookups, returns, revenue, and KPIs are formula- or query-driven.
- [ ] Month and Region controls update the summary correctly.
- [ ] Refresh All does not duplicate source rows or change totals unexpectedly.
- [ ] Revenue is reconciled to finance_report.csv and differences are explained.
- [ ] Metric definitions, assumptions, refresh steps, and limitations are visible.
- [ ] The workbook and Management Summary screenshot can be reopened.

### Stakeholder takeaway and limitations

Not recorded yet.
<!-- END EXCEL WORKBOOK STUDIO -->

<!-- BEGIN GOOGLE SHEETS STUDIO -->
## Google Sheets Analyst Studio progress

- Shared Google Sheet: https://docs.google.com/spreadsheets/d/1SOeKP0ZgyQ3zsukldi9AjbbpOxGvZDwRD3ruOQsV2Ng/edit?usp=sharing
- Management Summary screenshot: `C:\Users\Dan\Documents\MEGA\Dev\GitHub\career-accelerator\practice\applied\submissions\07_management_summary.png`
- Last Studio update: 2026-07-28T15:21:03

### Guided stages

- [x] Stage 1: Define the spreadsheet and source grain
  - Evidence: Created and linked the Northstar Operations Google Sheet. Reviewed all seven source files. Orders contains 12 rows at one row per order and uses order_id as its candidate key. Returns contains one row per return event, so returned quantity must be aggregated by order_id before being attached to Order Analysis.
- [x] Stage 2: Import and profile the source files
  - Evidence: Imported all seven CSV files into separate Raw tabs and confirmed the expected row counts: Orders 12, Customers 6, Products 4, Returns 4, Tickets 10, Targets 4, and Finance 3. Protected all Raw tabs. Noted that customer C006 has an inconsistent region value of “west ” that will be standardized in the analysis layer.
- [ ] Stage 3: Build the Order Analysis table
- [ ] Stage 4: Create the Controls sheet
- [ ] Stage 5: Build the Management Summary
- [ ] Stage 6: Reconcile revenue and test update
- [ ] Stage 7: Complete the analyst handoff

### Final verification

- [ ] Order Analysis has 12 unique order rows.
- [ ] Lookups, returns, revenue, and KPIs are formula- or query-driven.
- [ ] Month and Region controls update the summary correctly.
- [ ] Recalculation does not duplicate source rows or change totals unexpectedly.
- [ ] Revenue is reconciled to finance_report.csv and differences are explained.
- [ ] Metric definitions, assumptions, update steps, and limitations are visible.
- [ ] The Google Sheet and Management Summary screenshot can be reopened.

### Stakeholder takeaway and limitations

Not recorded yet.
<!-- END GOOGLE SHEETS STUDIO -->
