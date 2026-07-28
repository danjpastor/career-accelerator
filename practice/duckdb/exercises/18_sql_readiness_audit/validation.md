# Validation Checkpoints — Exercise 18

Open this file after attempting the questions. These checkpoints show results, not solution queries.

## Q1

Expected rows: **3**

| table_name | row_count |
|---|---|
| customers | 6 |
| orders | 8 |
| payments | 7 |

## Q2

Expected rows: **1**

| order_id | row_count |
|---|---|
| O004 | 2 |

## Q3

Expected rows: **1**

| order_id | customer_id |
|---|---|
| O005 | C999 |

## Q4

Expected rows: **1**

| payment_id | order_id |
|---|---|
| P006 | O999 |

## Q5

Expected rows: **1**

| order_id | issue |
|---|---|
| O006 | MISSING_ORDER_TOTAL |

## Q6

Expected rows: **2**

| order_id | difference |
|---|---|
| O005 | 50 |
| O006 | NULL |

## Q7

Expected rows: **5**

| issue_type | issue_count |
|---|---|
| DUPLICATE_ORDER_ID | 1 |
| ORPHAN_ORDER_CUSTOMER | 1 |
| ORPHAN_PAYMENT_ORDER | 1 |
| MISSING_ORDER_TOTAL | 1 |
| PAYMENT_MISMATCH | 1 |

## Q8

Expected rows: **1**

| count_star() |
|---|
| 8 |

