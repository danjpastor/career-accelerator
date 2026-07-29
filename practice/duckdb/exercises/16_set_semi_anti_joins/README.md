# DuckDB Exercise 12: Compare customer populations with set and existence logic

**Week:** 4  
**Estimated time:** 45 minutes  
**Concepts:** UNION, INTERSECT, EXCEPT, semi joins, anti joins

## Scenario

Customer success needs to compare old and current customer populations and identify who did or did not purchase.

## Tables

- `ex16_previous_customers`
- `ex16_current_customers`
- `ex16_orders`

## Questions

1. Combine the previous and current customer IDs with UNION.
2. Combine both customer tables with UNION ALL and count all rows.
3. Find customers present in both periods with INTERSECT.
4. Find customers that are new in the current period with EXCEPT.
5. Return current customers that have at least one order using a semi-join pattern.
6. Return current customers with no orders using an anti-join pattern.
7. Explain when UNION ALL is safer than UNION for audit work.

## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
