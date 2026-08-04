# Audit Broken Account Relationships

> **Challenge structure source:** [PostgreSQL Exercises — Delete based on a subquery](https://pgexercises.com/questions/updates/deletewh2.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Before a foreign-key rule is enforced, the database administrator needs a list of orders that would violate it.

## Your task

Return orders whose account ID is missing or does not match an account.

## Result requirements

- Return `order_id`, `account_id`, and `order_total`.
- Sort by `order_id`.

## Skill focus

**Referential integrity and database management**

Use an anti-join to find child rows that do not resolve to a valid parent.
