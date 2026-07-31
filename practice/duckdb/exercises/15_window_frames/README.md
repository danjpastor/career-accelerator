# DuckDB Exercise 17: Calculate running totals and moving averages

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** window frames, ROWS BETWEEN, LAG, running totals, moving averages

## Scenario

Operations wants trends that preserve daily rows while adding running totals, moving averages, changes, and ranks.

## Tables

- `ex15_daily_revenue`

## Tasks

### Task 1

Number each region’s rows in date order.

**Result requirements**

- **Return columns:** `region`, `revenue_date`, `row_number`
- **Exact names for new columns:** `row_number`
- **Expected rows:** 14

### Task 2

Calculate cumulative revenue by region.

**Result requirements**

- **Return columns:** `region`, `final_running_total`
- **Exact names for new columns:** `final_running_total`
- **Expected rows:** 2

### Task 3

Calculate a trailing three-day moving average by region.

**Result requirements**

- **Return columns:** `region`, `moving_avg_on_2026_06_07`
- **Exact names for new columns:** `moving_avg_on_2026_06_07`
- **Expected rows:** 2

### Task 4

Use LAG to calculate the day-over-day revenue change.

**Result requirements**

- **Return columns:** `region`, `change_on_2026_06_07`
- **Exact names for new columns:** `change_on_2026_06_07`
- **Expected rows:** 2

### Task 5

Rank each day within its region from highest to lowest revenue.

**Result requirements**

- **Return columns:** `region`, `highest_revenue_date`
- **Exact names for new columns:** `highest_revenue_date`
- **Expected rows:** 2

### Task 6

Return only the top two revenue days per region.

**Result requirements**

- **Return columns:** `region`, `revenue_date`, `revenue`
- **Expected rows:** 4

### Task 7

Explain in a SQL comment how ROWS BETWEEN changes the moving-average frame.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
