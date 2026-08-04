# Group Consecutive Task Dates into Projects

> **Challenge structure source:** [HackerRank — SQL Project Planning](https://www.hackerrank.com/challenges/sql-projects/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A delivery log stores one-day task intervals, but leadership wants the larger continuous project periods.

## Your task

Combine consecutive task intervals into project start and end dates.

## Result requirements

- Return `project_start` and `project_end`.
- Sort shorter projects first; break ties by `project_start`.

## Skill focus

**LAG and gaps-and-islands logic**

Use neighboring rows to identify the beginning of each consecutive date sequence.
