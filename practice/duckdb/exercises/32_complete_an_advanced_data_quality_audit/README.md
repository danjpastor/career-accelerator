# Complete an Advanced Data-Quality Audit

> **Challenge structure source:** [DataCamp — Data-Driven Decision Making in SQL — Chapter 3: Data Driven Decision Making with advanced SQL queries](https://www.datacamp.com/courses/data-driven-decision-making-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Before leadership uses a new order feed, an analyst needs one compact audit covering identifier, relationship, and value problems.

## Your task

Return issue counts for duplicate customer IDs, missing customer emails, orphaned orders, duplicate order IDs, and negative order amounts.

## Result requirements

- Return `issue_type` and `issue_count`.
- Use the exact labels `duplicate_customer_ids`, `missing_customer_emails`, `orphaned_orders`, `duplicate_order_ids`, and `negative_order_amounts`.
- Use `NOT EXISTS` to identify orders whose non-null customer ID has no matching customer.
- Include all five audit rows by combining checks with `UNION ALL`.
- Sort by `issue_type`.

## Skill focus

**EXISTS/NOT EXISTS and UNION ALL**

Combine several advanced SQL checks into one management-ready audit result.
