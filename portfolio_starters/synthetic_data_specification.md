# {project_name} — Synthetic Data Specification

**Milestone:** {label}  
**Started:** {date}

## 1. Business coverage

- Business problem supported:
- Questions the data must answer:
- Date range:
- Expected scale:

## 2. Table plan

| Table | One row represents | Primary key | Expected rows | Parent tables | Purpose |
|---|---|---|---:|---|---|
|  |  |  |  |  |  |

## 3. Relationship plan

| Parent table | Parent key | Child table | Foreign key | Expected relationship | Required? |
|---|---|---|---|---|---|
|  |  |  |  | One-to-many | Yes / No |

## 4. Field specification

For each table, document:

| Field | Type | Meaning | Allowed values/range | Missing allowed? | Generation rule |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 5. Realistic behavior

- Important distributions:
- Seasonal or time patterns:
- Correlations that should exist:
- Business rules that must always hold:
- Rare but valid exceptions:

## 6. Intentional quality issues

| Issue | Table/field | Approximate frequency | Reason included | Expected cleaning response |
|---|---|---:|---|---|
|  |  |  |  |  |

## 7. Validation before generation

- [ ] Every business question maps to required fields.
- [ ] Every table has a clear grain and key.
- [ ] Relationships are defined before rows are generated.
- [ ] Row volumes are realistic for the project.
- [ ] Intentional errors are documented and bounded.
