# Test Whether Email Is a Reliable Key

> **Challenge structure source:** [DataCamp — Exploratory Data Analysis in SQL — Chapter 1: What's in the Database?](https://www.datacamp.com/courses/exploratory-data-analysis-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A contact-import analyst wants to know whether email is safe to use when grouping or joining records.

## Your task

Profile `email` and summarize the missing and duplicate-value risks that could distort analysis.

## Result requirements

- Return one row with `total_rows`, `missing_emails`, and `duplicate_email_rows`.
- `duplicate_email_rows` is the number of extra rows beyond the first occurrence of each non-null email.

## Skill focus

**Table grain, missing values, and duplicate checks**

Profile a raw identifier for missing and duplicate values before using it in analysis.
