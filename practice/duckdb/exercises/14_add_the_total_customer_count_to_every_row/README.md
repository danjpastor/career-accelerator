# Add the Total Customer Count to Every Row

> **Challenge structure source:** [PostgreSQL Exercises — Produce member names with the total member count on every row](https://pgexercises.com/questions/aggregates/countmembers.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A customer export needs the total number of customers repeated beside every customer row.

## Your task

Return each customer with the total customer count shown on every row.

## Result requirements

- Return `customer_id`, `customer_name`, and `total_customers`.
- Sort by `customer_id`.

## Skill focus

**Aggregate window function**

Add overall context without collapsing row-level results.
