# Find Orders Above the Overall Average

> **Challenge structure source:** [StrataScratch — Customer Average Orders](https://platform.stratascratch.com/coding-question?id=2013)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Finance wants to review completed orders that are larger than the typical completed order.

## Your task

Return completed orders whose total amount is greater than the average completed-order amount.

## Result requirements

- Return `order_id`, `customer_id`, and `total_amount`.
- Sort by `total_amount` descending, then `order_id`.

## Skill focus

**Scalar subquery**

Use a one-value subquery as a filter threshold.
