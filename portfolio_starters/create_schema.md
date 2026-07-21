# {project_name} — Create the SQL Schema

**Milestone:** {label}  
**Started:** {date}

## Plan the tables

| Table | Grain | Primary key | Foreign keys | Source file | Purpose |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Data-type decisions

| Field | Planned SQL type | Why | Null allowed? | Constraint or validation |
|---|---|---|---|---|
|  |  |  |  |  |  |

## Build steps

1. Create a script under `sql/schema/`.
2. Add `CREATE TABLE` statements in dependency order.
3. Use types that match the actual data, not only what the CSV parser guessed.
4. Add primary and foreign keys where supported and appropriate.
5. Add comments or companion documentation for grain and business meaning.
6. Run the script from a clean database.

## Validation

- [ ] Every table creates successfully.
- [ ] Column names and types match the data dictionary.
- [ ] Keys match the relationship plan.
- [ ] The script can be rerun safely or includes clear reset instructions.
