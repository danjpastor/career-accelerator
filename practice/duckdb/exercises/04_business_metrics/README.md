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

## Questions

1. Task: Calculate active monthly recurring revenue (MRR). Required output: return only these columns in this order: `sum(monthly_revenue)`. Use these exact names for calculated or summarized columns: `sum(monthly_revenue)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Count active subscriptions. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Calculate average revenue per active subscription. Required output: return only these columns in this order: `round(avg(monthly_revenue), 2)`. Use these exact names for calculated or summarized columns: `round(avg(monthly_revenue), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate active MRR by plan. Required output: return only these columns in this order: `plan`, `sum(monthly_revenue)`. Use these exact names for calculated or summarized columns: `sum(monthly_revenue)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Count June 2026 cancellations. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Calculate June logo churn: June cancellations divided by subscriptions active at the start of June. Required output: return only these columns in this order: `round(((100.0 * canceled) / opening), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * canceled) / opening), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Return each region's share of active MRR as a percentage. Required output: return only these columns in this order: `region`, `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex04_business_metrics.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
