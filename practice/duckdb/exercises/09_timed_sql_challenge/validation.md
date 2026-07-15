# Validation Checkpoints — Exercise 09

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **4**

| acquisition_channel | count_star() |
|---|---|
| Organic | 4 |
| Paid Search | 2 |
| Paid Social | 2 |
| Referral | 2 |

## Q2

Expected rows: **1**

| count(DISTINCT p.user_id) | round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2) |
|---|---|
| 6 | 60.00 |

## Q3

Expected rows: **6**

| user_id |
|---|
| U01 |
| U02 |
| U04 |
| U06 |
| U09 |
| U10 |

## Q4

Expected rows: **3**

| acquisition_channel | sum(p.amount) |
|---|---|
| Organic | 515 |
| Paid Search | 129 |
| Paid Social | 499 |

## Q5

Expected rows: **1**

| count_star() | round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2) |
|---|---|
| 10 | 25.60 |
