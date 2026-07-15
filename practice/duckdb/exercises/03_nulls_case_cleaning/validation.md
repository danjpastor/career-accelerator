# Validation Checkpoints — Exercise 03

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **1**

| count(DISTINCT main."trim"(channel_raw)) | count(DISTINCT main."trim"(resolved_raw)) |
|---|---|
| 9 | 12 |

## Q2

Expected rows: **1**

| count_star() |
|---|
| 1 |

## Q3

Expected rows: **1**

| count_star() |
|---|
| 13 |

## Q4

Expected rows: **1**

| count_star() |
|---|
| 14 |

## Q5

Expected rows: **1**

| sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('yes', 'y', '1', 'true'))) THEN (1) ELSE 0 END) | sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('no', 'n', '0', 'false'))) THEN (1) ELSE 0 END) |
|---|---|
| 9 | 8 |

## Q6

Expected rows: **1**

| count_star() |
|---|
| 1 |

## Q7

Expected rows: **1**

| count_star() |
|---|
| 9 |
