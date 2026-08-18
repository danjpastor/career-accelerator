# Summarize Restaurant Revenue with ROLLUP

> **Challenge structure source:** [DataCamp — Data-Driven Decision Making in SQL — Chapter 4: Data Driven Decision Making with OLAP SQL queries](https://www.datacamp.com/courses/data-driven-decision-making-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A delivery-platform manager wants restaurant-level revenue plus an all-restaurants total in a single reporting query.

## Your task

Summarize platform revenue by restaurant and add one overall total using `ROLLUP`.

## Result requirements

- Platform revenue equals `subtotal + service_fee`.
- Return `restaurant_name` and `total_revenue`.
- Use `ALL RESTAURANTS` as the label for the overall rollup row.
- Round `total_revenue` to two decimals.
- Return the restaurant rows alphabetically, followed by the overall row.

## Skill focus

**OLAP aggregation with ROLLUP**

Use an OLAP extension to produce detail-level and overall business totals in one query.
