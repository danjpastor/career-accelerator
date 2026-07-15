# Validation Checkpoints — Exercise 12

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **4**

| campaign_channel | sum(spend) | sum(revenue) | (sum(revenue) - sum(spend)) | round((sum(revenue) / "nullif"(sum(spend), 0)), 4) |
|---|---|---|---|---|
| Email | 835 | 5860 | 5025 | 7.02 |
| Paid Search | 3440 | 9010 | 5570 | 2.62 |
| Paid Social | 4090 | 8180 | 4090 | 2.00 |
| Display | 2790 | 4670 | 1880 | 1.67 |

## Q2

Expected rows: **1**

| count_star() |
|---|
| 20 |

## Q3

Expected rows: **1**

| count(DISTINCT campaign_channel) |
|---|
| 4 |

## Q4

Expected rows: **1**

| round(sum(spend), 2) | round(sum(revenue), 2) |
|---|---|
| 11155 | 27720 |

## Q5

Expected rows: **4**

| campaign_channel | profit |
|---|---|
| Paid Search | 5570 |
| Email | 5025 |
| Paid Social | 4090 |
| Display | 1880 |

## Q6

Expected rows: **1**

| count_star() |
|---|
| 20 |

## Q7

Expected rows: **1**

| count_star() |
|---|
| 20 |
