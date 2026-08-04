# Calculate Workforce Cost by Team

> **Challenge structure source:** [HackerRank — Interviews](https://www.hackerrank.com/challenges/interviews/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Finance needs a team-level labor-cost summary that applies time-and-a-half to overtime hours.

## Your task

Calculate total labor cost for each team.

## Result requirements

- Regular cost is `regular_hours * hourly_rate`.
- Overtime cost is `overtime_hours * hourly_rate * 1.5`.
- Return `team_name`, `worker_count`, `total_hours`, and `total_labor_cost`.
- Round hours and cost to two decimals.
- Sort by `total_labor_cost` descending, then `team_name`.

## Skill focus

**Multi-table assessment and conditional calculations**

Join workforce tables and calculate regular and overtime labor cost.
