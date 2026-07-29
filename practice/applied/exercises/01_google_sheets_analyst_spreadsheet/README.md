# Applied Lab 01: Build a guided Google Sheets sales summary

> This is a beginner application lab for the spreadsheet skills taught in Weeks 1–2. The guide explains exactly what to build and how to check it, but it does not provide the finished formula or numerical answer.

## Assignment

Use a small order table and regional target table to create one clean analysis table and one interactive management summary. The completed file should demonstrate references, text cleaning, dates, percentages, conditional logic, conditional counting and sums, exact-match lookup, error handling, pivot tables, and a chart.

## Stage 1: Create the spreadsheet and inspect the sources

Set up a small, traceable Google Sheets file and understand the two source tables before writing formulas.

### What to do

1. Create a blank Google Sheet, give it a clear Northstar sales-analysis name, copy its shareable link, and save the link in this Studio.
2. Create exactly four tabs named Raw Orders, Targets, Analysis, and Summary. Keep the Raw Orders and Targets tabs reserved for imported source data.
3. Import each supplied CSV into the matching source tab. Confirm that the headers are in the first row and that no extra blank columns or title rows were introduced during import.
4. Inspect the order table and write down what one row represents, which field appears to identify an order, and which columns contain dates, categories, status, quantity, and currency values.
5. Inspect the target table and identify the field that can connect a region to its target. Confirm that each region appears only once before planning a lookup.
6. Freeze the source header rows and apply readable date, number, percentage, and currency formatting without changing the underlying values.

### Required output

A linked Google Sheet with four named tabs, both source files imported, and a short source-grain note recorded in the stage evidence.

### Check your work

- The order identifier is populated and unique for the imported rows.
- The target lookup field contains one row per region rather than repeated region values.
- Source tabs still contain the imported values and have not been used for cleaning or calculations.
- Dates, quantities, prices, and targets display with appropriate formats.

### Evidence to record

Record the Google Sheets link, the grain and candidate key of each source, and any formatting or import issue you corrected.

### Common mistakes

- Building calculations directly on the source tabs.
- Assuming a lookup field is unique without checking it.
- Deleting a row that looks unusual before confirming whether it is a valid record.

## Stage 2: Clean the fields and calculate order-level sales

Build one analysis row per order using the spreadsheet cleaning, reference, logic, and error-handling skills taught in Weeks 1–2.

### What to do

1. Create Analysis headers for the original order fields plus Month, Clean Region, Gross Sales, Processing Fee, Net Sales, and Quality Check. Keep the columns in a logical left-to-right order.
2. Bring the source order fields into Analysis using same-row references so the analysis remains connected to the imported data.
3. Create a month field from the order date using the date-to-text technique taught in the spreadsheet coursework. Use a consistent year-month format that will sort correctly.
4. Standardize region text by removing extra spaces and applying consistent capitalization. Combine the cleaning functions rather than editing individual region cells manually.
5. On Summary, create one clearly labeled processing-fee input and enter the required percentage as a true percentage value.
6. For Gross Sales, use conditional logic so only completed orders contribute sales. The calculation should use quantity and unit price from the same row.
7. Calculate the processing fee as the row's gross sales multiplied by the single fee-rate input. Use an absolute reference for the fee-rate cell so the reference remains fixed when copied.
8. Calculate Net Sales from the row's gross sales and processing fee. Think about whether subtracting the percentage cell itself is logically correct before writing the formula.
9. Create a Quality Check that flags missing order identifiers, blank cleaned regions, or nonpositive quantities and otherwise marks the row as acceptable.
10. Copy the calculated formulas through every imported order row, then use sorting and filtering to inspect completed, cancelled, and flagged records.

### Required output

An Analysis table with one row per order, cleaned region and month fields, formula-driven sales columns, and a visible quality check.

### Check your work

- The Analysis row count and unique order count still match the imported order table.
- Region variants that differ only by capitalization or extra spaces now group under one cleaned value.
- Cancelled orders do not contribute gross or net sales.
- Changing the fee-rate input updates Processing Fee and Net Sales but does not change Gross Sales.
- The fee-rate reference remains fixed in every copied row.
- No calculated cell contains an unexplained spreadsheet error.

### Evidence to record

Record the Analysis range, the cleaning and calculation logic you used in words, the fee-reference test, and one row you checked manually.

### Common mistakes

- Subtracting the percentage itself from a currency value instead of calculating the percentage of that value.
- Using a relative reference for the single fee-rate input.
- Typing cleaned regions or calculated sales manually instead of using formulas.
- Copying formulas beyond the source rows and accidentally including blank records in later summaries.

### Progressive hints

- For a percentage fee, first determine the fee amount, then subtract that amount from gross sales.
- List the true and false outcomes of the completed-order rule in words before choosing the conditional formula structure.
- Check the first copied row and the last copied row to confirm the fixed and relative references moved as intended.

## Stage 3: Build an interactive summary, pivot table, and chart

Create a small manager-facing summary that responds to a region selection and compares sales across regions and months.

### What to do

1. On Summary, create a Selected Region control and use data validation to provide All plus every cleaned region represented in the data.
2. Create clearly labeled KPI cells for Completed Orders, Gross Sales, Net Sales, Average Net Order Value, and Regional Sales Target.
3. For Completed Orders, design two counting paths: one for All regions and one requiring both completed status and the selected region. Use conditional logic to choose the correct path.
4. For Gross Sales and Net Sales, design the same All-versus-selected-region behavior using the conditional-sum functions taught in the coursework. Make sure each KPI sums the correct analysis column.
5. Calculate Average Net Order Value from the already calculated Net Sales and Completed Orders KPI cells. Add error handling for a selection with no completed orders.
6. Use the selected region to look up the matching target from the Targets tab. Use exact matching, keep the lookup table fixed, and show a clear message rather than an error when All is selected or no match exists.
7. Test the dropdown with All and at least two individual regions. Confirm that every region-dependent KPI changes and that Gross Sales is not affected by the processing-fee rate.
8. Create a pivot table from the complete Analysis table. Use Clean Region as rows, Month as columns, and the sum of Gross Sales as values.
9. Confirm the pivot is summing the sales field rather than counting records, then create one readable column chart from the useful pivot-table range.
10. Give the chart a decision-oriented title that names the metric and comparison. Remove totals from the chart if they create an extra misleading series.

### Required output

A Summary tab with a working region dropdown, five formula-driven KPIs, one region-by-month pivot table, and one column chart.

### Check your work

- All KPI cells update when the selected region changes and none are typed values.
- The All-region completed-order count agrees with a filter or pivot count of completed rows.
- The All-region gross-sales KPI reconciles with the pivot-table grand total.
- Net Sales is lower than or equal to Gross Sales and responds to changes in the fee-rate input.
- The regional target changes for each region and does not display a spreadsheet error for All.
- Each cleaned region and month appears only once in the pivot layout.
- The chart shows the intended regions, months, and sales values without an unnecessary grand-total series.

### Evidence to record

Record the dropdown selections tested, which KPIs changed, how the pivot total was reconciled, and one issue you corrected while building the summary.

### Common mistakes

- Counting all orders instead of only completed orders.
- Using the raw region field instead of the cleaned region field.
- Using a one-condition function when the selected-region calculation requires both status and region.
- Using approximate lookup matching or allowing the lookup range to move.
- Building the chart directly from raw orders instead of the summarized pivot table.

### Progressive hints

- Write the All rule and the selected-region rule separately before wrapping them in one conditional calculation.
- For conditional sums, identify the values to add separately from every condition range and condition.
- If the pivot total and KPI disagree, check status filtering, the selected sum column, and whether blank rows were included.

## Stage 4: Validate the spreadsheet and explain one finding

Prove that the spreadsheet behaves correctly and communicate one useful observation without overstating the data.

### What to do

1. Return the region control to All and perform a full validation of source row count, Analysis row count, and unique order count.
2. Choose one completed order and independently recalculate its gross sales, processing fee, and net sales using the source quantity, price, and fee rate. Compare your check with the row formulas.
3. Filter Analysis to completed orders and independently total one region. Compare that subtotal with the corresponding Summary KPI.
4. Compare the All-region Gross Sales KPI with the pivot-table grand total and investigate any difference before continuing.
5. Test two different regions in the dropdown and confirm the KPI changes make sense relative to the filtered Analysis rows.
6. Review the chart and identify the region with the strongest sales result. Check the underlying pivot values before writing the takeaway.
7. Write two or three sentences stating the observed pattern, why a manager might care, and one reasonable question or action to investigate next.
8. Add one limitation, such as the small time period, limited order fields, or the fact that the spreadsheet describes performance but does not prove why it occurred.
9. Reopen the share link, review the spreadsheet as a viewer would, complete the Final Review checklist, and save the Studio evidence.

### Required output

A validated beginner spreadsheet, a working share link, and a concise evidence-based takeaway with a limitation.

### Check your work

- Source, Analysis, and unique-order counts reconcile.
- The independently checked order agrees with its formula-driven row values.
- The selected-region subtotal agrees with the Summary KPI.
- The All-region Gross Sales KPI agrees with the pivot-table total.
- The takeaway names a real observed pattern and does not claim a cause that the data cannot prove.
- The shareable Google Sheets link opens and the four required tabs are readable.

### Evidence to record

Record the row-count reconciliation, the independently checked order or region, the pivot comparison, the final takeaway, and the most important limitation.

### Common mistakes

- Treating a plausible total as validated without an independent comparison.
- Writing that one region caused better performance when the data only shows a difference.
- Giving a recommendation that is unrelated to the observed result.
- Marking the lab complete without testing the share link and dropdown behavior.

## Completion rule

Complete all four Studio stages, save the shareable Google Sheets link, verify the final checklist, and write a two-to-three-sentence takeaway with one limitation.
