# Find Gaps in Daily Order Activity

> **Challenge structure source:** [DataCamp — Exploratory Data Analysis in SQL — Chapter 4: Working with Dates and Timestamps](https://www.datacamp.com/courses/exploratory-data-analysis-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

An operations analyst is checking whether there are unexpected gaps between days with recorded orders.

## Your task

Return each order that follows a gap of more than one calendar day in the order activity timeline.

## Result requirements

- Return `order_id`, `order_date`, `previous_order_date`, and `gap_days`.
- Use the previous order date in chronological order.
- Keep only rows where the gap is greater than one day.
- Sort by `order_date`, then `order_id`.

## Skill focus

**Date arithmetic and time-series gaps**

Compare ordered dates to identify breaks in a time series.
