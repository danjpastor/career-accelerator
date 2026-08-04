# Find Product Values That Break Normalization

> **Challenge structure source:** [HackerRank — Top Competitors](https://www.hackerrank.com/challenges/full-score/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A denormalized order-line import repeats product details, and the data modeler needs to find products whose stored prices disagree.

## Your task

Return products that have more than one distinct unit price in the raw order-line table.

## Result requirements

- Return `product_id`, `product_name`, and `distinct_prices`.
- Sort by `product_id`.

## Skill focus

**Normalization and update anomalies**

Identify repeated descriptive values that disagree for the same entity.
