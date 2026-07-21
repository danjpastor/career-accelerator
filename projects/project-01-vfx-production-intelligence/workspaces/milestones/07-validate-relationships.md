# VFX Production Intelligence — Validate Table Relationships

**Milestone:** Validate relationships  
**Started:** 2026-07-20

## What this task means

The VFX data is split across clients, projects, artists, shots, time entries, and reviews. Before analyzing production performance, prove that these tables connect correctly. A query can run successfully and still produce wrong totals if a key is duplicated, missing, or joined at the wrong grain.

## Expected VFX relationships

| Parent table | Unique parent key | Child table | Child foreign key | Expected relationship |
|---|---|---|---|---|
| `raw_clients` | `client_id` | `raw_projects` | `client_id` | One client to many projects |
| `raw_projects` | `project_id` | `raw_shots` | `project_id` | One project to many shots |
| `raw_projects` | `project_id` | `raw_time_entries` | `project_id` | One project to many time entries |
| `raw_projects` | `project_id` | `raw_reviews` | `project_id` | One project to many reviews |
| `raw_artists` | `artist_id` | `raw_shots` | `assigned_artist_id` | One artist to many assigned shots |
| `raw_artists` | `artist_id` | `raw_time_entries` | `artist_id` | One artist to many time entries |
| `raw_shots` | `shot_id` | `raw_time_entries` | `shot_id` | One shot to many time entries |
| `raw_shots` | `shot_id` | `raw_reviews` | `shot_id` | One shot to many reviews |

## Step 1 — Confirm primary keys are unique

Create `sql/validation/01_primary_key_checks.sql` and test:

- `raw_clients.client_id`
- `raw_projects.project_id`
- `raw_artists.artist_id`
- `raw_shots.shot_id`
- `raw_time_entries.time_entry_id`
- `raw_reviews.review_id`

Starter pattern:

```sql
SELECT client_id, COUNT(*) AS row_count
FROM raw_clients
GROUP BY client_id
HAVING COUNT(*) > 1;
```

Repeat for every key. Expected result: zero duplicate IDs unless the issue is intentionally documented in the synthetic source brief.

## Step 2 — Find orphan foreign keys

Create `sql/validation/02_orphan_key_checks.sql`.

Example: projects whose client does not exist.

```sql
SELECT
    p.client_id,
    COUNT(*) AS orphan_projects
FROM raw_projects AS p
LEFT JOIN raw_clients AS c
    ON p.client_id = c.client_id
WHERE p.client_id IS NOT NULL
  AND c.client_id IS NULL
GROUP BY p.client_id;
```

Write equivalent checks for every relationship in the table above.

## Step 3 — Check duplicated relationship fields

Some child tables contain both `shot_id` and `project_id`. Confirm they agree with the project attached to the referenced shot.

```sql
SELECT
    t.time_entry_id,
    t.shot_id,
    t.project_id AS time_entry_project,
    s.project_id AS shot_project
FROM raw_time_entries AS t
JOIN raw_shots AS s
    ON t.shot_id = s.shot_id
WHERE t.project_id <> s.project_id;
```

Run the same consistency check for `raw_reviews`.

## Step 4 — Test join cardinality

For each many-to-one lookup, compare the child row count before and after the join.

```sql
SELECT COUNT(*) AS time_entry_rows
FROM raw_time_entries;

SELECT COUNT(*) AS joined_rows
FROM raw_time_entries AS t
LEFT JOIN raw_shots AS s
    ON t.shot_id = s.shot_id;
```

If `joined_rows` is larger than `time_entry_rows`, the supposed parent key is not unique or the join condition is incomplete.

## Step 5 — Record the results

| Relationship | Duplicate parent keys | Orphan child rows | Inconsistent project IDs | Rows multiplied? | Safe to use? | Action |
|---|---:|---:|---:|---|---|---|
| clients → projects |  |  | N/A |  |  |  |
| projects → shots |  |  | N/A |  |  |  |
| artists → shots |  |  | N/A |  |  |  |
| artists → time entries |  |  | N/A |  |  |  |
| shots → time entries |  |  |  |  |  |  |
| shots → reviews |  |  |  |  |  |  |

## Definition of done

- [ ] All six primary keys were checked for duplicates.
- [ ] Every relationship was checked for orphan keys.
- [ ] Time-entry and review project IDs were compared with their referenced shot project.
- [ ] Join row counts were compared before and after each many-to-one lookup.
- [ ] Exceptions were classified as intentional source issues or errors to clean.
- [ ] Validation SQL was saved under `sql/validation/`.
- [ ] The completed results table was saved in this document.
