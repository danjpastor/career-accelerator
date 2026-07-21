# {project_name} — Relationship Validation

**Milestone:** {label}  
**Started:** {date}

## What “validate relationships” means

Tables are related when a key in one table points to a key in another. Before joining them, verify three things:

1. **The parent key is unique.** A client ID or product ID that should identify one row must not appear more than once.
2. **Every required foreign key has a parent.** A child row should not reference a client, product, project, or other parent that does not exist.
3. **The join has the expected cardinality.** A one-to-many join may repeat the parent row, but it should not multiply child rows unexpectedly.

## Relationship matrix

| Parent table | Parent key | Child table | Foreign key | Expected cardinality | Required relationship? | Status |
|---|---|---|---|---|---|---|
|  |  |  |  | One-to-many | Yes / No | Not tested |

## Check 1 — Primary-key uniqueness

Run one query per parent key.

```sql
SELECT
    parent_key,
    COUNT(*) AS row_count
FROM parent_table
GROUP BY parent_key
HAVING COUNT(*) > 1;
```

Expected result: zero rows for a key that should be unique.

## Check 2 — Missing parent records

```sql
SELECT
    c.foreign_key,
    COUNT(*) AS orphan_rows
FROM child_table AS c
LEFT JOIN parent_table AS p
    ON c.foreign_key = p.parent_key
WHERE c.foreign_key IS NOT NULL
  AND p.parent_key IS NULL
GROUP BY c.foreign_key;
```

Expected result: zero rows when every foreign key is required to match.

## Check 3 — Join multiplication

```sql
SELECT COUNT(*) AS child_rows
FROM child_table;

SELECT COUNT(*) AS joined_rows
FROM child_table AS c
LEFT JOIN parent_table AS p
    ON c.foreign_key = p.parent_key;
```

For a valid many-to-one lookup, `joined_rows` should equal `child_rows`.

## Validation log

| Relationship | Parent duplicates | Orphan children | Child rows before join | Rows after join | Safe to use? | Resolution |
|---|---:|---:|---:|---:|---|---|
|  |  |  |  |  | Yes / No |  |

## Deliverables

- Save completed checks under `sql/validation/` or the project notebook folder.
- Update the relationship matrix with results.
- Document every exception and whether it is an error or a valid business case.
- Do not mark this complete only because a join runs without an SQL error.
