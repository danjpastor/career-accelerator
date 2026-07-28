# Validation Checkpoints — Exercise 14

Open this file after attempting the questions. These checkpoints show results, not solution queries.

## Q1

Expected rows: **4**

| signup_month | subscriptions |
|---|---|
| 2026-01-01 | 3 |
| 2026-02-01 | 3 |
| 2026-03-01 | 3 |
| 2026-04-01 | 3 |

## Q2

Expected rows: **12**

| subscription_id | days_to_activation |
|---|---|
| S001 | 1 |
| S002 | 3 |
| S003 | 8 |
| S004 | 0 |
| S005 | 3 |
| S006 | 12 |
| S007 | 1 |
| S008 | 7 |
| S009 | 24 |
| S010 | 1 |
| S011 | 41 |
| S012 | NULL |

## Q3

Expected rows: **4**

| signup_month | activated_within_7_days |
|---|---|
| 2026-01-01 | 2 |
| 2026-02-01 | 2 |
| 2026-03-01 | 2 |
| 2026-04-01 | 1 |

## Q4

Expected rows: **4**

| signup_month | activation_rate_30d |
|---|---|
| 2026-01-01 | 1.0000 |
| 2026-02-01 | 1.0000 |
| 2026-03-01 | 1.0000 |
| 2026-04-01 | 0.3333 |

## Q5

Expected rows: **4**

| signup_month | cancelled_within_60_days |
|---|---|
| 2026-01-01 | 1 |
| 2026-02-01 | 1 |
| 2026-03-01 | 1 |
| 2026-04-01 | 1 |

## Q6

Expected rows: **4**

| signup_month | active_mrr |
|---|---|
| 2026-01-01 | 140 |
| 2026-02-01 | 220 |
| 2026-03-01 | 225 |
| 2026-04-01 | 125 |

## Q7

Expected rows: **1**

| count_star() |
|---|
| 12 |

