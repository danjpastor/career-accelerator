# Assess VFX Delivery Performance

> **Challenge structure source:** [StrataScratch — Acceptance Rate By Date](https://platform.stratascratch.com/coding/10285-acceptance-rate-by-date)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A VFX production executive wants to know which projects are struggling to deliver completed shots on time.

## Your task

Summarize final-shot delivery performance for each project.

## Result requirements

- Return `project_name`, `final_shots`, `late_shots`, and `on_time_percentage`.
- Count a final shot as late when `delivery_date` is after `deadline`.
- Round `on_time_percentage` to two decimals.
- Sort by `on_time_percentage` ascending, then `project_name`.

## Skill focus

**Integrated joins, conditional aggregation, and percentages**

Combine project and shot data into a decision-ready delivery summary.
