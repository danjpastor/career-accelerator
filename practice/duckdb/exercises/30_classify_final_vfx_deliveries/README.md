# Classify Final VFX Deliveries

> **Challenge structure source:** [DataCamp — Data-Driven Decision Making in SQL — Chapter 1: Introduction to business intelligence for a online movie rental database](https://www.datacamp.com/courses/data-driven-decision-making-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A VFX production manager wants a shot-level review of completed deliveries before the weekly status meeting.

## Your task

Classify every final shot as on time or late and show its variance from estimated hours.

## Result requirements

- Return `shot_id`, `project_id`, `department`, `delivery_status`, and `hours_variance`.
- Use `Late` when `delivery_date` is after `deadline`; otherwise use `On Time`.
- Calculate `hours_variance` as `actual_hours - estimated_hours`.
- Keep only shots whose status is `Final`.
- Sort by `project_id`, then `shot_id`.

## Skill focus

**Business filtering, date comparison, and CASE classification**

Turn a business delivery rule into a clear row-level classification query.
