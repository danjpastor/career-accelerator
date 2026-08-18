# Standardize and Count Contact Regions

> **Challenge structure source:** [DataCamp — Exploratory Data Analysis in SQL — Chapter 3: Exploring Categorical Data and Unstructured Text](https://www.datacamp.com/courses/exploratory-data-analysis-in-sql)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A customer-operations analyst notices that region labels differ in capitalization and surrounding whitespace.

## Your task

Normalize the region labels and count how many imported contacts belong to each standardized region.

## Result requirements

- Return `region` and `contact_count`.
- Normalize region labels by trimming surrounding whitespace and converting them to lowercase.
- Sort by `region`.

## Skill focus

**Categorical cleaning and aggregation**

Standardize inconsistent category labels before counting category frequency.
