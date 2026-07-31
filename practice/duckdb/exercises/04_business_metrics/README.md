# DuckDB Exercise 22: Calculate subscription KPIs

**Week:** 4
**Estimated time:** 45 minutes  
**Concepts:** ratios, conditional aggregation, date filters

## Scenario

Leadership needs a June 30, 2026 subscription snapshot with clearly defined recurring-revenue and churn metrics.

## Tables

- `ex04_subscriptions`

## Source CSV files

- `subscriptions.csv`

## Tasks

### Task 1

Leadership needs the monthly recurring revenue from subscriptions active on June 30, 2026. Return the total as `active_mrr`.

**Result requirements**

- Return columns in this order: `active_mrr`.
- Return 1 row.

### Task 2

Count the subscriptions active on June 30, 2026. Return the result as `active_subscriptions`.

**Result requirements**

- Return columns in this order: `active_subscriptions`.
- Return 1 row.

### Task 3

Calculate average monthly revenue per active subscription on June 30, 2026. Round it to two decimal places and name it `average_revenue_per_subscription`.

**Result requirements**

- Return columns in this order: `average_revenue_per_subscription`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 4

Show active monthly recurring revenue for each plan on June 30, 2026. Return `plan` and the total as `active_mrr`.

**Result requirements**

- Return columns in this order: `plan`, `active_mrr`.
- Return 3 rows.

### Task 5

Count subscriptions cancelled during June 2026. Return the result as `june_cancellations`.

**Result requirements**

- Return columns in this order: `june_cancellations`.
- Return 1 row.

### Task 6

Calculate June logo churn as June cancellations divided by subscriptions active at the start of June. Return a percentage rounded to two decimal places as `june_logo_churn_pct`.

**Result requirements**

- Return columns in this order: `june_logo_churn_pct`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 7

Show each region’s share of active monthly recurring revenue. Return `region` and the percentage rounded to two decimal places as `active_mrr_share_pct`.

**Result requirements**

- Return columns in this order: `region`, `active_mrr_share_pct`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

