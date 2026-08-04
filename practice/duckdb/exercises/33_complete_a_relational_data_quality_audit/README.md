# Complete a Relational Data-Quality Audit

> **Challenge structure source:** [PostgreSQL Exercises — Combining results from multiple queries](https://pgexercises.com/questions/basic/union.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A data engineer needs one audit table showing the number of key, relationship, and value problems in a raw customer-order extract.

## Your task

Return issue counts for duplicate customer IDs, missing customer emails, orphaned orders, duplicate order IDs, and negative order amounts.

## Result requirements

- Return `issue_type` and `issue_count`.
- Use the exact issue labels `duplicate_customer_ids`, `missing_customer_emails`, `orphaned_orders`, `duplicate_order_ids`, and `negative_order_amounts`.
- Include all five rows, even when a count is zero.
- Sort by `issue_type`.

## Skill focus

**Final audit with UNION ALL**

Combine several integrity checks into one compact audit result.
