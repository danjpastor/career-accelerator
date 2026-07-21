# {project_name} — SQL Data Quality Checks

**Milestone:** {label}  
**Started:** {date}

Save the checks under `sql/validation/` and record the results here.

## Required checks

| Check | Table/field | SQL file or query section | Expected result | Actual result | Pass? | Action |
|---|---|---|---|---|---|---|
| Row count |  |  |  |  |  |  |
| Primary-key uniqueness |  |  | Zero duplicates |  |  |  |
| Required values |  |  | Zero unexpected nulls |  |  |  |
| Allowed categories/ranges |  |  |  |  |  |  |
| Date logic |  |  |  |  |  |  |
| Relationship integrity |  |  | Zero unexpected orphans |  |  |  |
| Reconciliation total |  |  |  |  |  |  |

## Completion rules

- A check is not “passed” merely because the query ran.
- Explain every exception.
- Separate intentional synthetic issues from accidental pipeline errors.
- Save the final validated query set and results.
