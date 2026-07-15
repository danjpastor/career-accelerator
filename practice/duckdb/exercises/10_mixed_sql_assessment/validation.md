# Validation Checkpoints — Exercise 10

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **1**

| employee_id |
|---|
| E12 |

## Q2

Expected rows: **4**

| department_name | count(e.employee_id) | COALESCE(sum(e.annual_salary), 0) |
|---|---|---|
| Analytics | 3 | 279000 |
| Customer Success | 3 | 262000 |
| Finance | 2 | 206000 |
| Operations | 3 | 276000 |

## Q3

Expected rows: **4**

| department_name | round(((100.0 * sum(e.annual_salary)) / d.annual_budget), 2) |
|---|---|
| Analytics | 38.75 |
| Customer Success | 40.94 |
| Finance | 36.79 |
| Operations | 28.16 |

## Q4

Expected rows: **1**

| count_star() |
|---|
| 12 |

## Q5

Expected rows: **1**

| count_star() | round(avg(avg_score), 2) |
|---|---|
| 12 | 4.12 |

## Q6

Expected rows: **12**

| employee_id | dense_rank() OVER (PARTITION BY e.department_id ORDER BY s.avg_score DESC) |
|---|---|
| E01 | 1 |
| E02 | 2 |
| E03 | 3 |
| E04 | 1 |
| E05 | 2 |
| E06 | 3 |
| E07 | 1 |
| E08 | 2 |
| E09 | 3 |
| E10 | 1 |

_Only the first 10 of 12 rows are shown._

## Q7

Expected rows: **6**

| employee_id |
|---|
| E01 |
| E02 |
| E04 |
| E07 |
| E08 |
| E10 |

## Q8

Expected rows: **1**

| sum(CASE  WHEN (((e.department_id IS NULL) OR (e.annual_salary >= 115000) OR (s.avg_score < 4.0))) THEN (1) ELSE 0 END) |
|---|
| 7 |
