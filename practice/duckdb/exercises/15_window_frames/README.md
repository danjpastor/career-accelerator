# DuckDB Exercise 19: Calculate running totals and moving averages

**Week:** 5  
**Estimated time:** 50 minutes  
**Concepts:** window frames, ROWS BETWEEN, LAG, running totals, moving averages

## Scenario

Operations wants trends that preserve daily rows while adding running totals, moving averages, changes, and ranks.

## Tables

- `ex15_daily_revenue`

## Questions

1. Number each region’s rows in date order.
2. Calculate cumulative revenue by region.
3. Calculate a trailing three-day moving average by region.
4. Use LAG to calculate the day-over-day revenue change.
5. Rank each day within its region from highest to lowest revenue.
6. Return only the top two revenue days per region.
7. Explain in a SQL comment how ROWS BETWEEN changes the moving-average frame.

## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
