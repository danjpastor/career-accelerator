# Standardize Customer Phone Numbers

> **Challenge structure source:** [PostgreSQL Exercises — Clean up telephone numbers](https://pgexercises.com/questions/string/translate.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

The CRM import needs phone values reduced to digits so matching rules work consistently.

## Your task

Return every recorded phone number as digits only.

## Result requirements

- Return `customer_id` and `phone_digits`.
- Exclude customers whose phone is `NULL`.
- Sort by `customer_id`.

## Skill focus

**Text cleanup functions**

Remove formatting characters from text while preserving the underlying digits.
