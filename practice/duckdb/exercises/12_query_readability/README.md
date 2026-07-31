# DuckDB Exercise 13: Refactor a complex query with readable CTEs

**Week:** 4
**Estimated time:** 30 minutes  
**Concepts:** CTEs, aliases, formatting, validation

## Scenario

A working query produces the right answer but is difficult to review. Refactor it without changing the result.

## Tables

- `ex12_campaign_performance`

## Source CSV files

- `campaign_performance.csv`

## Tasks

### Task 1

Run `messy_query.sql` and record its output.

**Result requirements**

- **Return columns:** `campaign_channel`, `sum(spend)`, `sum(revenue)`, `(sum(revenue) - sum(spend))`, `round((sum(revenue) / "nullif"(sum(spend), 0)), 4)`
- **Exact names for new columns:** `sum(spend)`, `sum(revenue)`, `(sum(revenue) - sum(spend))`, `round((sum(revenue) / "nullif"(sum(spend), 0)), 4)`
- **Expected rows:** 4

### Task 2

Reformat the query using one clause per line and consistent indentation.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 3

Replace positional `ORDER BY 5` with a descriptive alias.

**Result requirements**

- **Return columns:** `count(DISTINCT campaign_channel)`
- **Exact names for new columns:** `count(DISTINCT campaign_channel)`
- **Expected rows:** 1

### Task 4

Move channel aggregation into a clearly named CTE.

**Result requirements**

- **Return columns:** `round(sum(spend), 2)`, `round(sum(revenue), 2)`
- **Exact names for new columns:** `round(sum(spend), 2)`, `round(sum(revenue), 2)`
- **Expected rows:** 1

### Task 5

Add short comments explaining the CTE and final filter.

**Result requirements**

- **Return columns:** `campaign_channel`, `profit`
- **Exact names for new columns:** `profit`
- **Expected rows:** 4

### Task 6

Confirm the refactored result exactly matches the original.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 7

Write two sentences explaining how readability reduces analytics risk.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex12_query_readability.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
