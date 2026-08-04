# Show Employees and Their Managers

> **Challenge structure source:** [PostgreSQL Exercises — Produce a list of all members, along with their recommender](https://pgexercises.com/questions/joins/self2.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

HR needs an organization-directory extract that still includes department heads without managers.

## Your task

Return every employee with the employee’s manager name when one exists.

## Result requirements

- Return `employee_name` and `manager_name`.
- Use `NULL` for employees without a manager.
- Sort by `employee_name`.

## Skill focus

**Self join and LEFT JOIN**

Preserve every employee while looking up an optional manager in the same table.
