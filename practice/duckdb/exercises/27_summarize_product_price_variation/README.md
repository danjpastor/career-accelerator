# Summarize Product Price Variation

> **Challenge structure source:** [DataCamp — Exploratory Data Analysis in SQL — Chapter 2: Summarizing and Aggregating Numeric Data](https://www.datacamp.com/courses/exploratory-data-analysis-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A merchandising analyst is profiling raw order-line prices before using them in a product performance report.

## Your task

Summarize the observed unit-price level and variation for each product.

## Result requirements

- Return `product_id`, `product_name`, `average_price`, `min_price`, `max_price`, and `price_range`.
- Round `average_price` to two decimals.
- Calculate `price_range` as maximum price minus minimum price.
- Sort by `product_id`.

## Skill focus

**Numeric summarization and variation**

Use grouped numeric summaries to compare typical values and spread across products.
