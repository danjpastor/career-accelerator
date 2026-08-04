# Build a Safe Customer Reporting View

> **Challenge structure source:** [SQL Practice — Create a reusable reporting object from selected columns](https://www.sql-practice.com/learn/table/create_table/)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Analysts need customer region and lifetime value, but they must not receive email addresses or phone numbers.

## Your task

Create a temporary view named `safe_customer_reporting`, then return all rows from it.

## Result requirements

- The view must contain `customer_id`, `customer_name`, `region`, and `lifetime_value` only.
- Sort the final result by `customer_id`.

## Skill focus

**Database views and column exposure**

Create a reusable view that exposes only approved reporting fields.
