# DuckDB Exercise 04: Calculate subscription KPIs

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

1. Calculate active monthly recurring revenue (MRR).
2. Count active subscriptions.
3. Calculate average revenue per active subscription.
4. Calculate active MRR by plan.
5. Count June 2026 cancellations.
6. Calculate June logo churn: June cancellations divided by subscriptions active at the start of June.
7. Return each region's share of active MRR as a percentage.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex04_business_metrics.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
