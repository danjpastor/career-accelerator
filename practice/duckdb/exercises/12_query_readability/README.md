# DuckDB Exercise 12: Refactor an unreadable analytics query

**Week:** 6  
**Estimated time:** 30 minutes  
**Concepts:** aliases, formatting, comments, CTE refactoring

## Scenario

A working query produces the right answer but is difficult to review. Refactor it without changing the result.

## Tables

- `ex12_campaign_performance`

## Source CSV files

- `campaign_performance.csv`

## Questions

1. Run `messy_query.sql` and record its output.
2. Reformat the query using one clause per line and consistent indentation.
3. Replace positional `ORDER BY 5` with a descriptive alias.
4. Move channel aggregation into a clearly named CTE.
5. Add short comments explaining the CTE and final filter.
6. Confirm the refactored result exactly matches the original.
7. Write two sentences explaining how readability reduces analytics risk.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex12_query_readability.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
