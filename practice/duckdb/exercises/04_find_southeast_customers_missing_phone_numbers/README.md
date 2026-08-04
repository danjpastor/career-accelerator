# Find Southeast Customers Missing Phone Numbers

> **Challenge structure source:** [SQL Practice — Combine filters and require a recorded value](https://www.sql-practice.com/)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

The customer-success team is cleaning contact details before an outreach campaign.

## Your task

Return Southeast customers who do not have a phone number recorded.

## Result requirements

- Return `customer_id`, `first_name`, `last_name`, and `city`.
- Sort by `city`, then `last_name`, then `customer_id`, all ascending.

## Skill focus

**NULL handling and multi-level sorting**

Combine a text filter with a missing-value condition and deterministic sorting.
