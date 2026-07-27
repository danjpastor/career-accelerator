# Aggregating DataFrames

Aggregation turns many detailed rows into a smaller business summary. In pandas, `groupby()` defines the groups, and an aggregation such as sum, mean, count, minimum, or maximum calculates one result per group.

## Main idea

Aggregation turns many detailed rows into a smaller business summary. In pandas, `groupby()` defines the groups, and an aggregation such as sum, mean, count, minimum, or maximum calculates one result per group.

```python
team_summary = tickets.groupby("team", as_index=False).agg(
    ticket_count=("ticket_id", "count"),
    average_hours=("resolution_hours", "mean")
)
```

The result has one row per team. Choose the aggregation that matches the question: counting records is different from summing a numeric measure.

## Example

A warehouse analyst groups shipment rows by carrier, counts shipments, and averages delivery days. They keep clear output column names so another person can understand the summary. The graded exercise summarizes orders by region and status.
