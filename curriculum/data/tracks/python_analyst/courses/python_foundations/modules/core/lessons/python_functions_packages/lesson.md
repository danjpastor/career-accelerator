# Functions and Packages

A **function** groups a repeatable set of instructions behind a meaningful name. Inputs are called parameters, and `return` sends the result back to the caller.

## Main idea

A **function** groups a repeatable set of instructions behind a meaningful name. Inputs are called parameters, and `return` sends the result back to the caller.

```python
def calculate_rate(completed, total):
    if total == 0:
        return 0
    return completed / total
```

Functions reduce copy-and-paste errors and make a calculation easier to test. A **package** is a collection of reusable code written by other developers. You import only the tools you need, such as `numpy` for array calculations or `pandas` for tables.

## Example

An operations analyst writes `calculate_fill_rate(shipped, ordered)` once and uses it for many products. The function handles a zero order quantity so the report does not crash. The graded exercise builds reusable profit calculations.
