# Slicing and Indexing DataFrames

Filtering selects rows that meet a condition. Column selection keeps only the fields needed for the next task.

## Main idea

Filtering selects rows that meet a condition. Column selection keeps only the fields needed for the next task.

```python
open_high = tickets[(tickets["status"] == "Open") & (tickets["priority"] == "High")]
review = open_high[["ticket_id", "team", "opened_date"]]
```

Use `&` for AND and `|` for OR, with each condition inside parentheses. `.loc` can select rows and columns explicitly. A focused result is easier to review than carrying every source column into every step.

## Example

A staffing analyst filters employees to one location and then selects only employee ID, role, and available hours for a scheduling review. The source DataFrame remains unchanged. The graded exercise creates a support-ticket review queue.
