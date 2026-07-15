# Validation Checkpoints — Exercise 04

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **1**

| sum(monthly_revenue) |
|---|
| 2878 |

## Q2

Expected rows: **1**

| count_star() |
|---|
| 12 |

## Q3

Expected rows: **1**

| round(avg(monthly_revenue), 2) |
|---|
| 239.83 |

## Q4

Expected rows: **3**

| plan | sum(monthly_revenue) |
|---|---|
| Enterprise | 2096 |
| Growth | 576 |
| Starter | 206 |

## Q5

Expected rows: **1**

| count_star() |
|---|
| 4 |

## Q6

Expected rows: **1**

| round(((100.0 * canceled) / opening), 2) |
|---|
| 26.67 |

## Q7

Expected rows: **4**

| region | round(((100.0 * mrr) / sum(mrr) OVER ()), 2) |
|---|---|
| Midwest | 24.22 |
| Northeast | 36.41 |
| South | 20.78 |
| West | 18.59 |
