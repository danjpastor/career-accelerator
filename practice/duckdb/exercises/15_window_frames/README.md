# DuckDB Exercise 17: Calculate running totals and moving averages

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** window frames, ROWS BETWEEN, LAG, running totals, moving averages

## Scenario

Operations wants trends that preserve daily rows while adding running totals, moving averages, changes, and ranks.

## Tables

- `ex15_daily_revenue`

## Questions

1. Task: Number each region’s rows in date order. Required output: return only these columns in this order: `region`, `revenue_date`, `row_number`. Use these exact names for calculated or summarized columns: `row_number`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate cumulative revenue by region. Required output: return only these columns in this order: `region`, `final_running_total`. Use these exact names for calculated or summarized columns: `final_running_total`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Calculate a trailing three-day moving average by region. Required output: return only these columns in this order: `region`, `moving_avg_on_2026_06_07`. Use these exact names for calculated or summarized columns: `moving_avg_on_2026_06_07`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Use LAG to calculate the day-over-day revenue change. Required output: return only these columns in this order: `region`, `change_on_2026_06_07`. Use these exact names for calculated or summarized columns: `change_on_2026_06_07`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Rank each day within its region from highest to lowest revenue. Required output: return only these columns in this order: `region`, `highest_revenue_date`. Use these exact names for calculated or summarized columns: `highest_revenue_date`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Return only the top two revenue days per region. Required output: return only these columns in this order: `region`, `revenue_date`, `revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Explain in a SQL comment how ROWS BETWEEN changes the moving-average frame. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
