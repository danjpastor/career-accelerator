# Validation Checkpoints — Exercise 07

Open this file after attempting the questions.
These checkpoints show results, not solution queries.

## Q1

Expected rows: **1**

| count_star() | round(sum(revenue), 2) |
|---|---|
| 10 | 2654 |

## Q2

Expected rows: **5**

| order_id |
|---|
| O103 |
| O106 |
| O108 |
| O109 |
| O110 |

## Q3

Expected rows: **1**

| count_star() | round(sum(profit), 2) |
|---|---|
| 10 | 1302 |

## Q4

Expected rows: **4**

| category | round(sum((i.quantity * i.sale_price)), 2) | round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2) |
|---|---|---|
| Books | 358 | 204 |
| Electronics | 862 | 382 |
| Fitness | 593 | 313 |
| Home | 841 | 403 |

## Q5

Expected rows: **3**

| product_name | profit |
|---|---|
| Office Chair | 270 |
| Studio Headphones | 207 |
| Mechanical Keyboard | 175 |

## Q6

Expected rows: **4**

| region | round(profit, 2) |
|---|---|
| Midwest | 277 |
| Northeast | 233 |
| South | 352 |
| West | 440 |

## Q7

Expected rows: **2**

| region |
|---|
| South |
| West |
