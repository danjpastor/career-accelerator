# Separate New and Existing Monthly Users

> **Challenge structure source:** [StrataScratch — New And Existing Users](https://platform.stratascratch.com/coding-question?id=2028)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Product analytics wants to see how many active users each month are new versus returning.

## Your task

Count new and existing active users for each activity month.

## Result requirements

- A user is new when the activity month equals the user’s first activity month.
- Return `activity_month`, `new_users`, and `existing_users`.
- Sort by `activity_month`.

## Skill focus

**Date truncation and cohort logic**

Compare each activity month with a user’s first activity month.
