# Python Lists

A **list** stores several values in a specific order. Lists are useful for a small sequence such as daily counts, region names, or review statuses.

## Main idea

A **list** stores several values in a specific order. Lists are useful for a small sequence such as daily counts, region names, or review statuses.

```python
wait_times = [4, 7, 3, 9]
```

Python positions begin at 0, so `wait_times[0]` returns the first value. A **slice** selects part of a list: `wait_times[-2:]` returns the final two values. Functions such as `sum()`, `len()`, `min()`, and `max()` can summarize numeric lists.

## Example

A service analyst stores five daily wait times in a list and uses `sum(wait_times) / len(wait_times)` to calculate the average. They use a slice to review only the most recent three days. The graded exercise uses order counts instead.
