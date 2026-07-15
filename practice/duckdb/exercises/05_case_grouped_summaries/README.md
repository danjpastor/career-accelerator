# DuckDB Exercise 05: Segment service performance

**Week:** 5  
**Estimated time:** 40 minutes  
**Concepts:** CASE expressions, SLA logic, grouped summaries

## Scenario

A service director wants SLA compliance and resolution-speed summaries that are easy to explain.

## Tables

- `ex05_service_requests`

## Source CSV files

- `service_requests.csv`

## Questions

1. Create an SLA target with CASE: Critical 2h, High 4h, Medium 8h, Low 12h.
2. Create an `sla_status` of `Met` or `Missed` by comparing first response to the target.
3. Count requests by department and SLA status.
4. Calculate SLA compliance percentage by department.
5. Create resolution bands: `Fast` under 12 hours, `Standard` from 12 through 24, and `Slow` over 24.
6. Return average CSAT by resolution band.
7. Return reopened request count and reopen rate by department.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex05_case_grouped_summaries.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
