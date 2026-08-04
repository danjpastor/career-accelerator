# Find Metric Values That Cannot Become Numbers

> **Challenge structure source:** [HackerRank — The Blunder](https://www.hackerrank.com/challenges/the-blunder/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A metric import stores every value as text, and the data engineer needs the unusable rows identified before loading.

## Your task

Return raw metric values that cannot be converted to a decimal number.

## Result requirements

- Return `metric_id` and `metric_value`.
- Do not treat valid zero or negative numbers as conversion failures.
- Sort by `metric_id`.

## Skill focus

**Data types and TRY_CAST**

Use safe conversion to identify values that do not match the intended numeric type.
