# Calculate Workforce Cost by Team

> **Challenge structure source:** [DataCamp — Data-Driven Decision Making in SQL — Chapter 2: Decision Making with simple SQL queries](https://www.datacamp.com/courses/data-driven-decision-making-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Operations leadership needs a team-level labor-cost summary for staffing decisions.

## Your task

Calculate total labor cost for each team.

## Result requirements

- Regular cost is `regular_hours * hourly_rate`.
- Overtime cost is `overtime_hours * hourly_rate * 1.5`.
- Return `team_name`, `worker_count`, `total_hours`, and `total_labor_cost`.
- Round hours and cost to two decimals.
- Sort by `total_labor_cost` descending, then `team_name`.

## Skill focus

**JOINs, GROUP BY, and business KPI aggregation**

Combine related tables and aggregate a management KPI by business group.
