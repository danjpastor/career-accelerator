<!-- DCA Relationship Validation Guide v4 -->
# VFX Production Intelligence Dashboard — Validate Table Relationships

**Milestone:** Validate relationships

## Purpose

Validate that the raw tables connect correctly before using them together in analysis.
SQL can run without errors while still producing incorrect totals when keys are missing,
duplicated, unmatched, or joined at the wrong grain.

> **This milestone validates and documents issues. It does not clean the data.** Keep
> the raw sources unchanged. Record what needs to be corrected later in the cleaning
> stage.

<!-- DCA:PROJECT-DATA:START -->
## Your validation notebook is ready

The app prepares this project's DuckDB database in the background. You do not need to register files, run setup SQL, or calculate data paths before starting.

- Guided notebook: `projects/project-01-vfx-production-intelligence/notebooks/validate_relationships.ipynb`
- Project database: `projects/project-01-vfx-production-intelligence/data/working/project.duckdb`
- VS Code workspace: `projects/project-01-vfx-production-intelligence/project-01-vfx-production-intelligence.code-workspace`
- Source configuration: `projects/project-01-vfx-production-intelligence/config/project_sources.yaml`
- Status: **Ready — open the notebook in VS Code and run it with the project's Python environment.**

> The relationship-validation notebook was upgraded to the clean v4 workflow. The previous notebook was archived at archive/portfolio-workspace-migration/20260721-113306/notebooks/validate_relationships.ipynb.

Click **Open Notebook in VS Code**. Run the setup cell once, then write normal SQL directly in the `%%sql` cells. Query results appear beneath each cell. Use this Visual Guide for schemas, keys, and relationships.

### Available tables

| Raw source | SQL table | Primary-key candidate | Columns |
|---|---|---|---:|
| `data/raw/csv/raw_artists.csv` | `raw.artists` | `artist_id` | 12 |
| `data/raw/csv/raw_clients.csv` | `raw.clients` | `client_id` | 10 |
| `data/raw/csv/raw_projects.csv` | `raw.projects` | `project_id` | 16 |
| `data/raw/csv/raw_reviews.csv` | `raw.reviews` | `review_id` | 12 |
| `data/raw/csv/raw_shots.csv` | `raw.shots` | `shot_id` | 23 |
| `data/raw/csv/raw_time_entries.csv` | `raw.time_entries` | `time_entry_id` | 11 |

### Table schemas

### `raw.artists`

| Column | Data type |
|---|---|
| `artist_id` | `VARCHAR` |
| `artist_name` | `VARCHAR` |
| `department` | `VARCHAR` |
| `role` | `VARCHAR` |
| `seniority` | `VARCHAR` |
| `location` | `VARCHAR` |
| `weekly_capacity_hours` | `VARCHAR` |
| `hourly_cost_usd` | `VARCHAR` |
| `hire_date` | `DATE` |
| `active_flag` | `VARCHAR` |
| `manager_id` | `VARCHAR` |
| `email` | `VARCHAR` |

### `raw.clients`

| Column | Data type |
|---|---|
| `client_id` | `VARCHAR` |
| `client_name` | `VARCHAR` |
| `client_type` | `VARCHAR` |
| `region` | `VARCHAR` |
| `contract_tier` | `VARCHAR` |
| `revision_tendency_index` | `DOUBLE` |
| `default_review_sla_hours` | `BIGINT` |
| `active_flag` | `VARCHAR` |
| `account_manager` | `VARCHAR` |
| `notes` | `VARCHAR` |

### `raw.projects`

| Column | Data type |
|---|---|
| `project_id` | `VARCHAR` |
| `client_id` | `VARCHAR` |
| `project_name` | `VARCHAR` |
| `project_type` | `VARCHAR` |
| `start_date` | `VARCHAR` |
| `target_delivery_date` | `DATE` |
| `actual_delivery_date` | `VARCHAR` |
| `status` | `VARCHAR` |
| `priority` | `VARCHAR` |
| `planned_shot_count` | `BIGINT` |
| `budget_hours` | `VARCHAR` |
| `producer` | `VARCHAR` |
| `vfx_supervisor` | `VARCHAR` |
| `fps` | `DOUBLE` |
| `resolution` | `VARCHAR` |
| `delivery_format` | `VARCHAR` |

### `raw.reviews`

| Column | Data type |
|---|---|
| `review_id` | `VARCHAR` |
| `shot_id` | `VARCHAR` |
| `project_id` | `VARCHAR` |
| `review_date` | `VARCHAR` |
| `review_round` | `VARCHAR` |
| `review_type` | `VARCHAR` |
| `feedback_source` | `VARCHAR` |
| `outcome` | `VARCHAR` |
| `note_category` | `VARCHAR` |
| `response_hours` | `VARCHAR` |
| `reviewer` | `VARCHAR` |
| `notes` | `VARCHAR` |

### `raw.shots`

| Column | Data type |
|---|---|
| `shot_id` | `VARCHAR` |
| `project_id` | `VARCHAR` |
| `sequence_code` | `VARCHAR` |
| `shot_name` | `VARCHAR` |
| `department` | `VARCHAR` |
| `assigned_artist_id` | `VARCHAR` |
| `assigned_date` | `VARCHAR` |
| `start_date` | `VARCHAR` |
| `deadline` | `VARCHAR` |
| `delivery_date` | `VARCHAR` |
| `first_pass_date` | `VARCHAR` |
| `final_approval_date` | `VARCHAR` |
| `status` | `VARCHAR` |
| `priority` | `VARCHAR` |
| `complexity` | `VARCHAR` |
| `estimated_hours` | `VARCHAR` |
| `actual_hours` | `VARCHAR` |
| `internal_revision_count` | `BIGINT` |
| `client_revision_count` | `BIGINT` |
| `revision_count_reported` | `BIGINT` |
| `hold_days` | `BIGINT` |
| `vendor_dependencies` | `VARCHAR` |
| `notes` | `VARCHAR` |

### `raw.time_entries`

| Column | Data type |
|---|---|
| `time_entry_id` | `VARCHAR` |
| `shot_id` | `VARCHAR` |
| `project_id` | `VARCHAR` |
| `artist_id` | `VARCHAR` |
| `work_date` | `VARCHAR` |
| `hours_logged` | `VARCHAR` |
| `task_type` | `VARCHAR` |
| `billable_flag` | `VARCHAR` |
| `overtime_flag` | `VARCHAR` |
| `source_system` | `VARCHAR` |
| `comment` | `VARCHAR` |

### Relationships to validate

These relationships are inferred from matching ID columns. Confirm them against the project documentation before treating them as business rules.

| Child table | Foreign key | Parent table | Parent key | Expected relationship |
|---|---|---|---|---|
| `raw.shots` | `assigned_artist_id` | `raw.artists` | `artist_id` | one-to-many |
| `raw.time_entries` | `artist_id` | `raw.artists` | `artist_id` | one-to-many |
| `raw.projects` | `client_id` | `raw.clients` | `client_id` | one-to-many |
| `raw.reviews` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.shots` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.time_entries` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.reviews` | `shot_id` | `raw.shots` | `shot_id` | one-to-many |
| `raw.time_entries` | `shot_id` | `raw.shots` | `shot_id` | one-to-many |
<!-- DCA:PROJECT-DATA:END -->

## What belongs where

- **This Markdown task guide:** workflow, schemas, relationship definitions, syntax
  patterns, result interpretation, and completion criteria.
- **The Jupyter notebook:** setup, your SQL queries, result output, short interpretations,
  and the final validation decision.
- **Later cleaning work:** deduplication, key correction, row removal, imputation, or
  rebuilt clean tables and views.

## Before running SQL

For every table and relationship you intend to use, identify:

1. **Table grain:** what one row represents.
2. **Primary-key candidate:** the column or column combination expected to identify one row.
3. **Foreign key:** the child column expected to match a parent key.
4. **Expected cardinality:** one-to-one, one-to-many, or many-to-one.
5. **Optionality:** whether a missing foreign key is allowed by the business process.

A repeated value is only a defect when the column is expected to be unique at that
specific table grain. A foreign key may repeat normally because many child rows can
belong to one parent.

## Exact validation workflow

### Step 1 — Open the notebook and run setup

Click **Open Notebook in VS Code**, confirm the selected kernel is **Python (Career
Accelerator)**, and run the collapsed setup cell once. The setup cell loads the configured
raw sources into an isolated DuckDB session and activates the native `%%sql` cells.

Do not rewrite the setup plumbing. It is provided because environment setup is not the
skill being assessed.

### Step 2 — Establish baseline row counts and table grain

Before testing relationships, record the row count for every table you will join. These
counts provide the baseline used to detect accidental row multiplication or loss later.

Generic syntax pattern:

```sql
SELECT COUNT(*) AS row_count
FROM table_name;
```

In the notebook interpretation, state what one row represents and record the baseline
count. If the apparent grain is unclear, stop and resolve it before choosing a key.

### Step 3 — Validate each primary-key candidate

Run two separate checks for each candidate key needed by the analysis.

#### 3A. Missing key values

A primary key should not be null or blank. Use a filter that checks both null values and,
when the key is text, empty or whitespace-only values.

Generic syntax pattern:

```sql
SELECT *
FROM table_name
WHERE key_column IS NULL;
```

#### 3B. Duplicate key values

Group by the candidate key and return only values appearing more than once.

Generic syntax pattern:

```sql
SELECT key_column, COUNT(*) AS row_count
FROM table_name
GROUP BY key_column
HAVING COUNT(*) > 1;
```

How to interpret the result:

- **Zero returned rows:** the tested key is unique for the current data.
- **Returned rows:** each returned key appears `row_count` times.
- **Duplicates in a true primary key:** the proposed key does not currently identify one row.
- **Duplicates that match the table grain:** the column may be a foreign key or only part of
  a composite key rather than a primary key.

Do not delete or deduplicate records during this milestone. Document whether the result
suggests exact duplicate records, conflicting records, an incomplete key, or an incorrect
assumption about table grain.

### Step 4 — Validate each foreign key

Check both missing child-key values and missing parent records.

#### 4A. Null or blank foreign keys

Determine whether the relationship is required or optional. A null foreign key is a defect
only when every child row is expected to have a parent.

#### 4B. Orphaned foreign keys

Use the child table as the left side of a `LEFT JOIN`, match it to the parent key, and keep
non-null child keys for which no parent row was found.

Generic syntax pattern:

```sql
SELECT child.foreign_key, COUNT(*) AS orphan_rows
FROM child_table AS child
LEFT JOIN parent_table AS parent
    ON child.foreign_key = parent.primary_key
WHERE child.foreign_key IS NOT NULL
  AND parent.primary_key IS NULL
GROUP BY child.foreign_key;
```

How to interpret the result:

- **Zero returned rows:** every tested non-null child key has a matching parent.
- **Returned rows:** those child-key values reference parent records that are absent.
- **Null child keys:** interpret separately according to whether the relationship is optional.

Record the number of affected key values and rows, the likely business impact, and the
cleaning or source-system follow-up required later.

### Step 5 — Validate join cardinality

For a many-to-one child-to-parent lookup, compare the child row count with the row count
after a `LEFT JOIN`.

Generic syntax pattern:

```sql
SELECT
    (SELECT COUNT(*) FROM child_table) AS child_rows,
    COUNT(*) AS joined_rows
FROM child_table AS child
LEFT JOIN parent_table AS parent
    ON child.foreign_key = parent.primary_key;
```

Interpretation rules:

- **`joined_rows = child_rows`:** the left join preserved the child grain.
- **`joined_rows > child_rows`:** the join multiplied rows, usually because the parent key
  is duplicated, the join uses an incomplete key, or the relationship is many-to-many.
- **An inner join returns fewer rows:** unmatched or null child keys were removed.
- **A left join returns fewer rows:** recheck the query because a correctly written left join
  should preserve every child row before later filters or aggregation.

A matching row count does not prove that every relationship is valid; use it together with
the duplicate-key and orphan-key checks.

### Step 6 — Add project-specific consistency checks

Test relationship rules that cannot be inferred from column names alone. Examples include:

- A child and its referenced parent should belong to the same project or client.
- A date on a child record should fall within the parent record's valid period.
- A status or category duplicated across tables should agree with the authoritative table.
- A relationship expected to be one-to-one should not have multiple child records per parent.

Write only checks relevant to the documented business model. Do not invent rules solely
because columns happen to share similar names.

### Step 7 — Interpret every result

Each notebook interpretation should answer five questions:

1. **What was tested?**
2. **What did the query return?** Include counts or affected key values.
3. **Does the result pass the expected rule?**
4. **Why does it matter for joins or analysis?**
5. **What should happen later?** Clean, investigate, exclude with approval, or document as
   an intentional exception.

Example interpretation structure:

> The candidate key check returned three duplicated identifiers. Because the table is
> expected to contain one row per entity, the key does not currently satisfy uniqueness.
> The records should be investigated during cleaning to determine whether they are exact
> duplicates, conflicting records, or evidence that a composite key is required.

### Step 8 — Make a relationship decision

Classify each tested relationship as one of the following:

- **Safe to use:** key and cardinality checks pass with no material exceptions.
- **Safe with a documented exception:** the issue is understood, intentional, and will not
  distort the planned analysis.
- **Not safe until cleaned:** the issue can change row counts, attach records to the wrong
  parent, or otherwise invalidate results.

The final notebook conclusion should list safe relationships, issues found, required future
cleaning or documentation, and whether analysis can continue.

### Step 9 — Test reproducibility

Use **Restart Kernel and Run All Cells** in VS Code. The notebook should execute from top to
bottom with the dedicated Career Accelerator kernel and without relying on hidden state.

## Common result guide

| Result | Meaning | Action during this milestone |
|---|---|---|
| Duplicate-key query returns zero rows | Candidate key is unique in the current data | Record that the uniqueness check passed |
| Duplicate-key query returns values | Candidate key is not unique | Investigate and document; do not clean here |
| Primary-key nulls are returned | Some rows cannot be reliably identified | Document as a blocking key-quality issue |
| Orphan query returns zero rows | Every tested non-null child key has a parent | Record that referential integrity passed |
| Orphan query returns values | Child rows reference missing parents | Document affected keys and later resolution |
| Joined rows exceed child rows | The join multiplied the child grain | Treat the relationship as unsafe until explained |
| Inner-join rows are lower | Null or unmatched child rows were dropped | Quantify the loss and document its impact |
| Repeated foreign keys only | Multiple child rows may belong to one parent | Usually expected in one-to-many relationships |

## Definition of done

- [ ] Baseline row counts and table grains are recorded.
- [ ] Every required primary-key candidate was checked for nulls and duplicates.
- [ ] Every required foreign key was checked for nulls and missing parent records.
- [ ] Join cardinality was checked for every relationship used in the analysis.
- [ ] Relevant project-specific consistency rules were tested.
- [ ] Every SQL result has a concise written interpretation.
- [ ] No raw data was changed during validation.
- [ ] The final decision identifies safe and unsafe relationships and required next actions.
- [ ] The notebook runs from top to bottom in a fresh **Python (Career Accelerator)** kernel.


## Notes carried forward from the previous guide

Review these entries and move confirmed findings into the notebook.

| Raw source | SQL table | Primary-key candidate | Columns |
| `data/raw/csv/raw_artists.csv` | `raw.artists` | `artist_id` | 12 |
| `data/raw/csv/raw_clients.csv` | `raw.clients` | `client_id` | 10 |
| `data/raw/csv/raw_projects.csv` | `raw.projects` | `project_id` | 16 |
| `data/raw/csv/raw_reviews.csv` | `raw.reviews` | `review_id` | 12 |
| `data/raw/csv/raw_shots.csv` | `raw.shots` | `shot_id` | 23 |
| `data/raw/csv/raw_time_entries.csv` | `raw.time_entries` | `time_entry_id` | 11 |
| Column | Data type |
| `artist_id` | `VARCHAR` |
| `artist_name` | `VARCHAR` |
| `department` | `VARCHAR` |
| `role` | `VARCHAR` |
| `seniority` | `VARCHAR` |
| `location` | `VARCHAR` |
| `weekly_capacity_hours` | `VARCHAR` |
| `hourly_cost_usd` | `VARCHAR` |
| `hire_date` | `DATE` |
| `active_flag` | `VARCHAR` |
| `manager_id` | `VARCHAR` |
| `email` | `VARCHAR` |
| `client_id` | `VARCHAR` |
| `client_name` | `VARCHAR` |
| `client_type` | `VARCHAR` |
| `region` | `VARCHAR` |
| `contract_tier` | `VARCHAR` |
| `revision_tendency_index` | `DOUBLE` |
| `default_review_sla_hours` | `BIGINT` |
| `account_manager` | `VARCHAR` |
| `notes` | `VARCHAR` |
| `project_id` | `VARCHAR` |
| `project_name` | `VARCHAR` |
| `project_type` | `VARCHAR` |
| `start_date` | `VARCHAR` |
| `target_delivery_date` | `DATE` |
| `actual_delivery_date` | `VARCHAR` |
| `status` | `VARCHAR` |
| `priority` | `VARCHAR` |
| `planned_shot_count` | `BIGINT` |
| `budget_hours` | `VARCHAR` |
| `producer` | `VARCHAR` |
| `vfx_supervisor` | `VARCHAR` |
| `fps` | `DOUBLE` |
| `resolution` | `VARCHAR` |
| `delivery_format` | `VARCHAR` |
| `review_id` | `VARCHAR` |
| `shot_id` | `VARCHAR` |
| `review_date` | `VARCHAR` |
| `review_round` | `VARCHAR` |
| `review_type` | `VARCHAR` |
| `feedback_source` | `VARCHAR` |
| `outcome` | `VARCHAR` |
| `note_category` | `VARCHAR` |
| `response_hours` | `VARCHAR` |
| `reviewer` | `VARCHAR` |
| `sequence_code` | `VARCHAR` |
| `shot_name` | `VARCHAR` |
| `assigned_artist_id` | `VARCHAR` |
| `assigned_date` | `VARCHAR` |
| `deadline` | `VARCHAR` |
| `delivery_date` | `VARCHAR` |
| `first_pass_date` | `VARCHAR` |
| `final_approval_date` | `VARCHAR` |
| `complexity` | `VARCHAR` |
| `estimated_hours` | `VARCHAR` |
| `actual_hours` | `VARCHAR` |
| `internal_revision_count` | `BIGINT` |
| `client_revision_count` | `BIGINT` |
| `revision_count_reported` | `BIGINT` |
| `hold_days` | `BIGINT` |
| `vendor_dependencies` | `VARCHAR` |
| `time_entry_id` | `VARCHAR` |
| `work_date` | `VARCHAR` |
| `hours_logged` | `VARCHAR` |
| `task_type` | `VARCHAR` |
| `billable_flag` | `VARCHAR` |
| `overtime_flag` | `VARCHAR` |
| `source_system` | `VARCHAR` |
| `comment` | `VARCHAR` |
| Child table | Foreign key | Parent table | Parent key | Expected relationship |
| `raw.shots` | `assigned_artist_id` | `raw.artists` | `artist_id` | one-to-many |
| `raw.time_entries` | `artist_id` | `raw.artists` | `artist_id` | one-to-many |
| `raw.projects` | `client_id` | `raw.clients` | `client_id` | one-to-many |
| `raw.reviews` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.shots` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.time_entries` | `project_id` | `raw.projects` | `project_id` | one-to-many |
| `raw.reviews` | `shot_id` | `raw.shots` | `shot_id` | one-to-many |
| `raw.time_entries` | `shot_id` | `raw.shots` | `shot_id` | one-to-many |
| Raw source | SQL table | Inferred primary key | Columns |
| Parent table | Parent key | Child table | Child key | Expected relationship |
| `raw.artists` | `artist_id` | `raw.shots` | `assigned_artist_id` | one-to-many |
| `raw.artists` | `artist_id` | `raw.time_entries` | `artist_id` | one-to-many |
| `raw.clients` | `client_id` | `raw.projects` | `client_id` | one-to-many |
| `raw.projects` | `project_id` | `raw.reviews` | `project_id` | one-to-many |
| `raw.projects` | `project_id` | `raw.shots` | `project_id` | one-to-many |
| `raw.projects` | `project_id` | `raw.time_entries` | `project_id` | one-to-many |
| `raw.shots` | `shot_id` | `raw.reviews` | `shot_id` | one-to-many |
| `raw.shots` | `shot_id` | `raw.time_entries` | `shot_id` | one-to-many |
| Parent table | Unique parent key | Child table | Child foreign key | Expected relationship |
| `raw.clients` | `client_id` | `raw.projects` | `client_id` | One client to many projects |
| `raw.projects` | `project_id` | `raw.shots` | `project_id` | One project to many shots |
| `raw.projects` | `project_id` | `raw.time_entries` | `project_id` | One project to many time entries |
| `raw.projects` | `project_id` | `raw.reviews` | `project_id` | One project to many reviews |
| `raw.artists` | `artist_id` | `raw.shots` | `assigned_artist_id` | One artist to many assigned shots |
| `raw.artists` | `artist_id` | `raw.time_entries` | `artist_id` | One artist to many time entries |
| `raw.shots` | `shot_id` | `raw.time_entries` | `shot_id` | One shot to many time entries |
| `raw.shots` | `shot_id` | `raw.reviews` | `shot_id` | One shot to many reviews |
| Relationship | Duplicate parent keys | Orphan child rows | Inconsistent project IDs | Rows multiplied? | Safe to use? | Action |
| clients → projects |  |  | N/A |  |  |  |
| projects → shots |  |  | N/A |  |  |  |
| artists → shots |  |  | N/A |  |  |  |
| artists → time entries |  |  | N/A |  |  |  |
| shots → time entries |  |  |  |  |  |  |
| shots → reviews |  |  |  |  |  |  |
