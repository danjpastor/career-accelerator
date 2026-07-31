# DuckDB Exercise 17: Calculate running totals and moving averages

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** window frames, ROWS BETWEEN, LAG, running totals, moving averages

## Scenario

Operations wants daily revenue trends that keep every date visible while adding running totals, moving averages, changes, and ranks.

## Tables

- `ex15_daily_revenue`

## Tasks

### Task 1

Number each region’s rows in date order.

**Result requirements**

- Return columns in this order: `region`, `revenue_date`, `row_number`.
- Return 14 rows.

### Task 2

Calculate cumulative revenue by region.

**Result requirements**

- Return columns in this order: `region`, `final_running_total`.
- Return 2 rows.

### Task 3

Calculate a trailing three-day moving average by region.

**Result requirements**

- Return columns in this order: `region`, `moving_avg_on_2026_06_07`.
- Return 2 rows.

### Task 4

Use LAG to calculate the day-over-day revenue change.

**Result requirements**

- Return columns in this order: `region`, `change_on_2026_06_07`.
- Return 2 rows.

### Task 5

Rank each day within its region from highest to lowest revenue.

**Result requirements**

- Return columns in this order: `region`, `highest_revenue_date`.
- Return 2 rows.

### Task 6

Return only the top two revenue days per region.

**Result requirements**

- Return columns in this order: `region`, `revenue_date`, `revenue`.
- Return 4 rows.

### Task 7

Add a SQL comment explaining how `ROWS BETWEEN` changes the moving-average frame, then return the source row count as `window_frame_rows`.

**Result requirements**

- Return columns in this order: `window_frame_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

