# {project_name} — Load Data

**Milestone:** {label}  
**Started:** {date}

## Load plan

| Source file | Destination table | Expected rows | Transform during load? | Load order |
|---|---|---:|---|---:|
|  |  |  |  |  |

## Steps

1. Create a repeatable load script under `sql/load/` or a documented notebook.
2. Load parent tables before child tables when constraints are active.
3. Record parsing choices for dates, booleans, decimals, and missing values.
4. Do not silently discard rejected rows.

## Reconciliation

| Table | Source rows | Loaded rows | Rejected rows | Difference explained? |
|---|---:|---:|---:|---|
|  |  |  |  |  |

## Spot checks

- [ ] Sample text values were inspected.
- [ ] Date columns parsed correctly.
- [ ] Numeric fields are numeric.
- [ ] Primary keys remain unique.
- [ ] Foreign-key values were not altered unexpectedly.
