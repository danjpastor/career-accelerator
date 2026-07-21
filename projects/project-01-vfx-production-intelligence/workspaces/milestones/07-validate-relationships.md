# VFX Production Intelligence Dashboard — Validate Table Relationships

**Milestone:** Validate relationships

## What this task means

Before using joins in your analysis, confirm that the tables connect the way you expect. A query can run successfully and still produce incorrect totals when IDs are duplicated, child records point to missing parents, or a join multiplies rows.

<!-- DCA:PROJECT-DATA:START -->
## Your SQL workspace is ready

The app prepares this project's DuckDB database in the background. You do not need to register CSV files, run setup SQL, or calculate file paths before starting.

- Starter SQL: `projects/project-01-vfx-production-intelligence/sql/validation/validate_relationships.sql`
- Findings document: `projects/project-01-vfx-production-intelligence/documentation/relationship_validation.md`
- Project database: `projects/project-01-vfx-production-intelligence/data/working/project.duckdb`
- VS Code workspace: `projects/project-01-vfx-production-intelligence/project-01-vfx-production-intelligence.code-workspace`
- Source configuration: `projects/project-01-vfx-production-intelligence/config/project_sources.yaml`
- Status: **Ready — open the starter in VS Code and run SQL with the DuckDB extension.**

Click **Open Starter in VS Code**. The generated workspace automatically attaches the project database as `project` and selects it as the active DuckDB database. Use **Ctrl+Enter** to run SQL or the **Run** link above an individual statement.

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

## How to complete the task

### 1. Open the starter SQL

Click **Open Starter in VS Code**. The file contains the actual table schemas, relationship list, short syntax reminders, and blank TODO areas. It intentionally does not contain the finished project queries.

### 2. Check primary-key uniqueness

For every table with a declared primary key, group by that identifier and count how many rows use it. Keep only identifiers whose count is greater than one.

A basic pattern looks like this, using placeholder names:

```sql
SELECT example_id, COUNT(*) AS row_count
FROM example_table
GROUP BY example_id
HAVING COUNT(*) > 1;
```

Write the real checks yourself using the project tables listed above.

### 3. Check for orphaned foreign keys

For each child-to-parent relationship, use a `LEFT JOIN` to keep every child row. Then identify child rows where the corresponding parent key is missing. The starter names the relationships but leaves the join SQL for you to write.

### 4. Check join cardinality

Count the child table before the join and compare it with the joined result. A many-to-one lookup should normally preserve the child-row count. If the count grows, investigate duplicate parent keys or an incomplete join condition.

### 5. Record what you found

Open the findings document and record duplicate IDs, orphaned records, row-count changes, exceptions, and your final conclusion about whether each relationship is safe.

## Definition of done

- [ ] The project database opened successfully in the generated VS Code workspace.
- [ ] Every declared primary-key candidate was checked for duplicates.
- [ ] Every required relationship was checked for missing parent records.
- [ ] Join row counts were compared for the relationships used in the analysis.
- [ ] Project-specific consistency checks were added where needed.
- [ ] The findings document contains results, exceptions, and a final conclusion.


## Notes carried forward from the previous guide

Review these entries and move confirmed results into the new findings document.

| Raw source | SQL table | Inferred primary key | Columns |
| `data/raw/csv/raw_artists.csv` | `raw.artists` | `artist_id` | 12 |
| `data/raw/csv/raw_clients.csv` | `raw.clients` | `client_id` | 10 |
| `data/raw/csv/raw_projects.csv` | `raw.projects` | `project_id` | 16 |
| `data/raw/csv/raw_reviews.csv` | `raw.reviews` | `review_id` | 12 |
| `data/raw/csv/raw_shots.csv` | `raw.shots` | `shot_id` | 23 |
| `data/raw/csv/raw_time_entries.csv` | `raw.time_entries` | `time_entry_id` | 11 |
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
