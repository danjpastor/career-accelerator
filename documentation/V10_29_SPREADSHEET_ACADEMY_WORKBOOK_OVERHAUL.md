# Career Accelerator v10.29.0 — Spreadsheet Academy Workbook Overhaul

## Continuing workbook

Spreadsheet Academy now uses one continuing workbook:

- `curriculum/data/workbooks/Northstar Operations Practice Workbook.xlsx`
- Learner copy: `academy_workspace/spreadsheets/Northstar Operations Practice Workbook.xlsx`
- Archived resets: `academy_workspace/spreadsheets/archive/`
- Validated capstone snapshot: `workspaces/academy/workbook_capstones/spreadsheet_mastery_review.xlsx`

The template is never opened for editing. The Academy service creates a personal copy on first use and archives the current copy before a reset.

## Workbook sheets

- Orders
- Customers
- Products
- Employees
- Inventory
- Lookup Tables
- Analysis Workspace

## Lesson flow

Every Spreadsheet Academy lesson contains:

1. Learn — a short plain-language explanation and recognition check.
2. Try It — a guided task in the real workbook.
3. Practice — a related task with less guidance.
4. Check Your Work — validation of the saved `.xlsx` file or a result-based evidence answer.
5. Continue — enabled only after the practical activity passes.

## Workbook controls

Practical workbook steps provide:

- Open Practice Workbook
- Use in Google Sheets
- Reset Lesson Workbook
- Open Lesson Instructions
- Check Workbook
- Expected Result

The Google Sheets workflow copies the local workbook path, opens Google Sheets, and explains how to import the workbook and download the completed file back as `.xlsx` before validation.

## Structured metadata

Every practical activity declares:

- Workbook and template name
- Sheet
- Columns
- Row range
- Column descriptions
- Sample values
- Starting state
- Expected result
- Save instructions
- Optional evidence prompt

The Academy renderer uses this configured metadata directly, so workbook tasks do not depend on SQL-table schema detection.

## Workbook validation

The validator reads the Open XML package with the Python standard library and checks durable structures that survive Excel and Google Sheets export:

- Required sheets and headers
- Saved formulas, including shared formulas
- Populated ranges and reconciliation outputs
- Tables and filters
- Data-validation rules
- Conditional formatting
- Pivot output or pivot structures
- Charts
- Evidence answers for results that are not consistently detectable across applications

## Demonstrated Evidence

The final mastery activity snapshots the validated workbook and registers it as an `Academy Capstone`. The evidence record demonstrates the spreadsheet skills accumulated across the course without exposing or modifying the continuing learner copy.

## Next Tasks scroll repair

`ContentSizedScrollArea` keeps the Next Tasks content widget at the exact height requested by its rendered rows. It recalculates after layout requests, viewport resizing, task refreshes, and dashboard density changes. Optional Practice remains outside the scroll region.
