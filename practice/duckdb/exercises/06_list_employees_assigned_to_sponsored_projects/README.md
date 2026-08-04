# List Employees Assigned to Sponsored Projects

> **Challenge structure source:** [PostgreSQL Exercises — Produce a list of all members who have used a tennis court](https://pgexercises.com/questions/joins/threejoin.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Program leadership needs to know who is working on each sponsored initiative.

## Your task

List every project assignment with the project name, employee name, and allocated hours.

## Result requirements

- Return `project_name`, `employee_name`, and `hours_allocated`.
- Sort by `project_name`, then `employee_name`.

## Skill focus

**Multiple INNER JOINs**

Join three related tables to produce one deduplicated assignment list.
