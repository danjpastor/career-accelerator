# DuckDB Exercise 22: Calculate subscription KPIs

**Week:** 5
**Estimated time:** 45 minutes  
**Concepts:** ratios, conditional aggregation, date filters

## Scenario

Leadership needs a June 30, 2026 subscription snapshot and a defensible set of recurring-revenue KPIs.

## Tables

- `ex04_subscriptions`

## Source CSV files

- `subscriptions.csv`

## Tasks

### Task 1

Calculate active monthly recurring revenue (MRR).

**Result requirements**

- **Return columns:** `sum(monthly_revenue)`
- **Exact names for new columns:** `sum(monthly_revenue)`
- **Expected rows:** 1

### Task 2

Count active subscriptions.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 3

Calculate average revenue per active subscription.

**Result requirements**

- **Return columns:** `round(avg(monthly_revenue), 2)`
- **Exact names for new columns:** `round(avg(monthly_revenue), 2)`
- **Expected rows:** 1

### Task 4

Calculate active MRR by plan.

**Result requirements**

- **Return columns:** `plan`, `sum(monthly_revenue)`
- **Exact names for new columns:** `sum(monthly_revenue)`
- **Expected rows:** 3

### Task 5

Count June 2026 cancellations.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 6

Calculate June logo churn: June cancellations divided by subscriptions active at the start of June.

**Result requirements**

- **Return columns:** `round(((100.0 * canceled) / opening), 2)`
- **Exact names for new columns:** `round(((100.0 * canceled) / opening), 2)`
- **Expected rows:** 1

### Task 7

Return each region's share of active MRR as a percentage.

**Result requirements**

- **Return columns:** `region`, `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`
- **Exact names for new columns:** `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`
- **Expected rows:** 4
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex04_business_metrics.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
