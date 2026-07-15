# Validation Checkpoints — Exercise 05

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **4**

| severity | target |
|---|---|
| Critical | 2 |
| High | 4 |
| Low | 12 |
| Medium | 8 |

## Q2

Expected rows: **1**

| met | missed |
|---|---|
| 18 | 6 |

## Q3

Expected rows: **6**

| department | sla_status | count_star() |
|---|---|---|
| Access | Met | 6 |
| Access | Missed | 2 |
| Billing | Met | 6 |
| Billing | Missed | 2 |
| Technical | Met | 6 |
| Technical | Missed | 2 |

## Q4

Expected rows: **3**

| department | round(((100.0 * sum(CASE  WHEN ((first_response_hours <= CASE  WHEN ((severity = 'Critical')) THEN (2) WHEN ((severity = 'High')) THEN (4) WHEN ((severity = 'Medium')) THEN (8) ELSE 12 END)) THEN (1) ELSE 0 END)) / count_star()), 2) |
|---|---|
| Access | 75.00 |
| Billing | 75.00 |
| Technical | 75.00 |

## Q5

Expected rows: **3**

| band | count_star() |
|---|---|
| Fast | 7 |
| Slow | 6 |
| Standard | 11 |

## Q6

Expected rows: **3**

| band | round(avg(csat_score), 2) |
|---|---|
| Fast | 4.43 |
| Slow | 2.50 |
| Standard | 4.18 |

## Q7

Expected rows: **3**

| department | sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END) | round(((100.0 * sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)) / count_star()), 2) |
|---|---|---|
| Access | 2 | 25.00 |
| Billing | 2 | 25.00 |
| Technical | 3 | 37.50 |
