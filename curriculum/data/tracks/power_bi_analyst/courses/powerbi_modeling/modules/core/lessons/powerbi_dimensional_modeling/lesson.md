# Dimensional Modeling

A dimensional model separates measurable business events from descriptive context. A **fact table** contains events and numbers, such as orders and revenue. A **dimension table** contains descriptive fields, such as customer segment, product category, or calendar month.

## Main idea

A dimensional model separates measurable business events from descriptive context. A **fact table** contains events and numbers, such as orders and revenue. A **dimension table** contains descriptive fields, such as customer segment, product category, or calendar month.

Relationships allow dimension selections to filter the fact table. For a simple star model, single-direction filtering from dimension to fact is usually the easiest behavior to understand. Bidirectional filtering can be useful in special cases, but it can also create confusing or ambiguous paths.

Good models make measures easier to write and totals easier to trust.

## Example

A training model uses `Attendance` as a fact table and `Employees`, `Courses`, and `Calendar` as dimensions. Choosing a department in Employees filters attendance records, while attendance does not automatically rewrite the list of employees. This one-way flow keeps the model predictable.
