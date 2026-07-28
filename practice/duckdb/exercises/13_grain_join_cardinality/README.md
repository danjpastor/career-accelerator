# DuckDB Exercise 13: Audit table grain and join cardinality

**Week:** 4  
**Estimated time:** 50 minutes  
**Concepts:** table grain, primary keys, join cardinality, pre-aggregation

## Scenario

An analyst joined order-level data to a one-to-many contact table and inflated revenue. Audit the table grains and build a safe result.

## Tables

- `ex13_accounts`
- `ex13_orders`
- `ex13_contacts`

## Questions

1. Profile the row count and distinct business key count for each table.
2. Find account IDs that appear more than once in the contacts table.
3. Join orders directly to contacts and compare the resulting row count with the original order count.
4. Calculate the multiplication factor created by the direct join.
5. Pre-aggregate contacts to one row per account, then join that result to orders without changing the order grain.
6. Find accounts with no orders.
7. Write a short SQL comment stating the grain of the safe final result.

## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
