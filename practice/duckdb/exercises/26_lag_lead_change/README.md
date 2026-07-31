# DuckDB Exercise 16: Compare current values with prior and next rows

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** LAG, LEAD, period-over-period change

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex15_daily_revenue`

## Scenario

A regional manager wants to compare each day with the previous and next day so sudden revenue changes are easy to spot.

## Tasks

### Task 1

Add the previous revenue value for the same region to every daily row.

**Result requirements**

- Return columns in this order: `revenue_date`, `region`, `revenue`, `previous_revenue`.
- Return 14 rows.

### Task 2

Calculate day-over-day revenue change for rows that have a prior regional value.

**Result requirements**

- Return columns in this order: `revenue_date`, `region`, `revenue`, `revenue_change`.
- Return 12 rows.

### Task 3

Add the next revenue value for the same region to every daily row.

**Result requirements**

- Return columns in this order: `revenue_date`, `region`, `revenue`, `next_revenue`.
- Return 14 rows.

### Task 4

Calculate the percentage change from the previous regional value and handle the first row safely.

**Result requirements**

- Return columns in this order: `revenue_date`, `region`, `revenue`, `percent_change`.
- Return 14 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
