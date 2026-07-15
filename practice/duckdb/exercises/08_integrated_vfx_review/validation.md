# Validation Checkpoints — Exercise 08

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **5**

| shot_id |
|---|
| SH004 |
| SH007 |
| SH008 |
| SH011 |
| SH012 |

## Q2

Expected rows: **14**

| shot_id | sum("hours") |
|---|---|
| SH001 | 25 |
| SH002 | 37 |
| SH003 | 17 |
| SH004 | 31 |
| SH005 | 23 |
| SH006 | 9 |
| SH007 | 21 |
| SH008 | 8 |
| SH009 | 37 |
| SH010 | 35 |

_Only the first 10 of 14 rows are shown._

## Q3

Expected rows: **1**

| count_star() |
|---|
| 4 |

## Q4

Expected rows: **4**

| department | round(((100.0 * sum(CASE  WHEN (((status = 'Final') AND (completed_date <= due_date))) THEN (1) ELSE 0 END)) / "nullif"(sum(CASE  WHEN ((status = 'Final')) THEN (1) ELSE 0 END), 0)), 2) |
|---|---|
| Animation | 0.00 |
| Compositing | 100.00 |
| FX | 50.00 |
| Lighting | 100.00 |

## Q5

Expected rows: **1**

| sum(CASE  WHEN (((s.status != 'Final') AND ((s.due_date < CAST('2026-06-30' AS "DATE")) OR (s.revision_count >= 3) OR (COALESCE(a.actual_hours, 0) > s.estimated_hours)))) THEN (1) ELSE 0 END) |
|---|
| 5 |

## Q6

Expected rows: **4**

| project_id | sum(estimated_hours) | sum(COALESCE(actual_hours, 0)) | sum(revision_count) |
|---|---|---|---|
| P001 | 102 | 110 | 10 |
| P002 | 72 | 61 | 5 |
| P003 | 106 | 91 | 10 |
| P004 | 74 | 36 | 2 |

## Q7

Expected rows: **7**

| artist_id | hours | workload_rank |
|---|---|---|
| A05 | 78 | 1 |
| A04 | 50 | 2 |
| A02 | 45 | 3 |
| A01 | 41 | 4 |
| A03 | 38 | 5 |
| A06 | 35 | 6 |
| A07 | 11 | 7 |

## Q8

Expected rows: **1**

| project_id | risk_shots |
|---|---|
| P002 | 2 |
