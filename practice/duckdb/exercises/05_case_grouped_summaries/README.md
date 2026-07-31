# DuckDB Exercise 11: Group service results with CASE

**Week:** 4
**Estimated time:** 40 minutes  
**Concepts:** CASE expressions, SLA logic, grouped summaries

## Scenario

A service director wants SLA compliance and resolution-speed summaries that are easy to explain.

## Tables

- `ex05_service_requests`

## Source CSV files

- `service_requests.csv`

## Tasks

### Task 1

Create an SLA target with CASE: Critical 2h, High 4h, Medium 8h, Low 12h.

**Result requirements**

- **Return columns:** `severity`, `target`
- **Exact names for new columns:** `target`
- **Expected rows:** 4

### Task 2

Create an `sla_status` of `Met` or `Missed` by comparing first response to the target.

**Result requirements**

- **Return columns:** `met`, `missed`
- **Exact names for new columns:** `met`, `missed`
- **Expected rows:** 1

### Task 3

Count requests by department and SLA status.

**Result requirements**

- **Return columns:** `department`, `sla_status`, `count_star()`
- **Exact names for new columns:** `sla_status`, `count_star()`
- **Expected rows:** 6

### Task 4

Calculate SLA compliance percentage by department.

**Result requirements**

- **Return columns:** `department`, `round(((100.0 * sum(CASE  WHEN ((first_response_hours <= CASE  WHEN ((severity = 'Critical')) THEN (2) WHEN ((severity = 'High')) THEN (4) WHEN ((severity = 'Medium')) THEN (8) ELSE 12 END)) THEN (1) ELSE 0 END)) / count_star()), 2)`
- **Exact names for new columns:** `round(((100.0 * sum(CASE  WHEN ((first_response_hours <= CASE  WHEN ((severity = 'Critical')) THEN (2) WHEN ((severity = 'High')) THEN (4) WHEN ((severity = 'Medium')) THEN (8) ELSE 12 END)) THEN (1) ELSE 0 END)) / count_star()), 2)`
- **Expected rows:** 3

### Task 5

Create resolution bands: `Fast` under 12 hours, `Standard` from 12 through 24, and `Slow` over 24.

**Result requirements**

- **Return columns:** `band`, `count_star()`
- **Exact names for new columns:** `band`, `count_star()`
- **Expected rows:** 3

### Task 6

Return average CSAT by resolution band.

**Result requirements**

- **Return columns:** `band`, `round(avg(csat_score), 2)`
- **Exact names for new columns:** `band`, `round(avg(csat_score), 2)`
- **Expected rows:** 3

### Task 7

Return reopened request count and reopen rate by department.

**Result requirements**

- **Return columns:** `department`, `sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)`, `round(((100.0 * sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)) / count_star()), 2)`
- **Exact names for new columns:** `sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)`, `round(((100.0 * sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)) / count_star()), 2)`
- **Expected rows:** 3
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex05_case_grouped_summaries.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
