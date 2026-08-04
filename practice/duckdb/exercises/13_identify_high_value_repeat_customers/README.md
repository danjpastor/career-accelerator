# Identify High-Value Repeat Customers

> **Challenge structure source:** [HackerRank — Interviews](https://www.hackerrank.com/challenges/interviews/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Customer success wants a list of repeat buyers whose completed-order value is at least 400 dollars.

## Your task

Return customers with at least two completed orders and at least 400 dollars in completed-order value.

## Result requirements

- Return `customer_id`, `customer_name`, `completed_orders`, and `completed_value`.
- Round `completed_value` to two decimals.
- Sort by `completed_value` descending, then `customer_id`.

## Skill focus

**CTEs and staged aggregation**

Build a readable multi-stage query that calculates customer metrics before filtering.
