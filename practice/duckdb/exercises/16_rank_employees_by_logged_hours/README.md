# Rank Employees by Logged Hours

> **Challenge structure source:** [PostgreSQL Exercises — Rank members by rounded hours used](https://pgexercises.com/questions/aggregates/rankmembers.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Operations wants an hours leaderboard that gives tied employees the same rank.

## Your task

Rank employees by their total logged hours from highest to lowest.

## Result requirements

- Return `employee_id`, `total_hours`, and `hours_rank`.
- Round `total_hours` to one decimal place.
- Sort by `hours_rank`, then `employee_id`.

## Skill focus

**RANK**

Rank aggregated results while preserving ties.
