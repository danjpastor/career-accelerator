# Validation Checkpoints — Exercise 15

Open this file after attempting the questions. These checkpoints show results, not solution queries.

## Q1

Expected rows: **14**

| region | revenue_date | row_number |
|---|---|---|
| East | 2026-06-01 | 1 |
| East | 2026-06-02 | 2 |
| East | 2026-06-03 | 3 |
| East | 2026-06-04 | 4 |
| East | 2026-06-05 | 5 |
| East | 2026-06-06 | 6 |
| East | 2026-06-07 | 7 |
| West | 2026-06-01 | 1 |
| West | 2026-06-02 | 2 |
| West | 2026-06-03 | 3 |
| West | 2026-06-04 | 4 |
| West | 2026-06-05 | 5 |
| West | 2026-06-06 | 6 |
| West | 2026-06-07 | 7 |

## Q2

Expected rows: **2**

| region | final_running_total |
|---|---|
| East | 990 |
| West | 990 |

## Q3

Expected rows: **2**

| region | moving_avg_on_2026_06_07 |
|---|---|
| East | 163.33 |
| West | 176.67 |

## Q4

Expected rows: **2**

| region | change_on_2026_06_07 |
|---|---|
| East | 30 |
| West | -70 |

## Q5

Expected rows: **2**

| region | highest_revenue_date |
|---|---|
| East | 2026-06-05 |
| West | 2026-06-06 |

## Q6

Expected rows: **4**

| region | revenue_date | revenue |
|---|---|---|
| East | 2026-06-05 | 200 |
| East | 2026-06-04 | 170 |
| West | 2026-06-06 | 210 |
| West | 2026-06-05 | 180 |

## Q7

Expected rows: **1**

| count_star() |
|---|
| 14 |

