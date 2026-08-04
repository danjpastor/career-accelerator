# Number Sessions Within Each Team

> **Challenge structure source:** [PostgreSQL Exercises — Produce a numbered list of members](https://pgexercises.com/questions/aggregates/nummembers.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Team leads want each work session numbered from earliest to latest within the team.

## Your task

Assign a sequence number to every work session within its team.

## Result requirements

- Return `team`, `session_date`, `employee_id`, and `team_session_number`.
- Number rows by `session_date`, then `session_id` within each team.
- Sort by `team`, then `team_session_number`.

## Skill focus

**ROW_NUMBER window function**

Number rows independently inside each group.
