# DuckDB Exercise 11: Segment service performance

**Week:** 4
**Estimated time:** 40 minutes  
**Concepts:** CASE expressions, SLA logic, grouped summaries

## Scenario

A service director is reviewing response-time commitments, resolution speed, customer satisfaction, and reopened requests by department.

## Tables

- `ex05_service_requests`

## Source CSV files

- `service_requests.csv`

## Tasks

### Task 1

Create an SLA target with CASE: Critical 2h, High 4h, Medium 8h, Low 12h.

**Result requirements**

- Return columns in this order: `severity`, `target`.
- Return 4 rows.

### Task 2

Create an `sla_status` of `Met` or `Missed` by comparing first response to the target.

**Result requirements**

- Return columns in this order: `met`, `missed`.
- Return 1 row.

### Task 3

Show how many service requests met or missed the SLA in each department. Return `department`, `sla_status`, and the count as `request_count`.

**Result requirements**

- Return columns in this order: `department`, `sla_status`, `request_count`.
- Return 6 rows.

### Task 4

Calculate the percentage of requests that met the SLA in each department. Round to two decimal places and name it `sla_compliance_pct`.

**Result requirements**

- Return columns in this order: `department`, `sla_compliance_pct`.
- Return 3 rows.
- Round the requested result to 2 decimal places.

### Task 5

Group requests into `Fast` under 12 hours, `Standard` from 12 through 24 hours, and `Slow` over 24 hours. Return each `resolution_band` and its `request_count`.

**Result requirements**

- Return columns in this order: `resolution_band`, `request_count`.
- Return 3 rows.

### Task 6

Compare customer satisfaction across the three resolution bands. Return `resolution_band` and average `csat_score` rounded to two decimal places as `average_csat`.

**Result requirements**

- Return columns in this order: `resolution_band`, `average_csat`.
- Return 3 rows.
- Round the requested result to 2 decimal places.

### Task 7

For each department, count reopened requests and calculate the reopen rate as a percentage. Return `reopened_requests` and `reopen_rate_pct`, rounded to two decimal places.

**Result requirements**

- Return columns in this order: `department`, `reopened_requests`, `reopen_rate_pct`.
- Return 3 rows.
- Round the requested result to 2 decimal places.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

