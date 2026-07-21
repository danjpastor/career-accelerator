# VFX Production Intelligence Dashboard — Validate Table Relationships

**Milestone:** Validate relationships

## What this task means

Before using joins in your analysis, confirm that the tables connect the way you expect. A query can run successfully and still produce incorrect totals when IDs are duplicated, child records point to missing parents, or a join multiplies rows.

<!-- DCA:PROJECT-DATA:START -->
## Your validation notebook is ready

The app prepares this project's DuckDB database in the background. You do not need to register files, run setup SQL, or calculate data paths before starting.

- Guided notebook: `projects/project-01-vfx-production-intelligence/notebooks/validate_relationships.ipynb`
- Project database: `projects/project-01-vfx-production-intelligence/data/working/project.duckdb`
- VS Code workspace: `projects/project-01-vfx-production-intelligence/project-01-vfx-production-intelligence.code-workspace`
- Source configuration: `projects/project-01-vfx-production-intelligence/config/project_sources.yaml`
- Status: **Ready — open the notebook in VS Code and run it with the project's Python environment.**

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

## How to complete the task

### 1. Open the guided notebook

Click **Open Notebook in VS Code**. The notebook keeps the instructions, SQL cells, results, and your written interpretation together. It contains table schemas and small generic syntax examples, but it does not contain the finished project queries.

### 2. Run the setup and table-list cells

The first code cell connects to the project database. The next cell confirms which tables are available. This setup is provided because connection plumbing is not the skill being assessed.

### 3. Write and run each validation check

Complete the notebook sections for key uniqueness, missing parent records, join cardinality, and project-specific consistency. Each SQL result appears directly under the cell that produced it.

### 4. Explain what each result means

Replace the Markdown prompts with your own observations. Record duplicates, orphaned records, row-count changes, exceptions, cleanup decisions, and your final conclusion.

### 5. Run the notebook from a fresh kernel

Use **Restart Kernel and Run All Cells** in VS Code. A reproducible notebook should run in order without relying on hidden state.

## Definition of done

- [ ] The notebook connects to the prepared project database.
- [ ] Every declared primary-key candidate was checked for duplicates.
- [ ] Every required relationship was checked for missing parent records.
- [ ] Join row counts were compared for the relationships used in the analysis.
- [ ] Project-specific consistency checks were considered.
- [ ] Every result has a written interpretation.
- [ ] The final conclusion states which relationships are safe to use.
- [ ] The notebook runs from top to bottom in a fresh kernel.


## Notes carried forward from the previous guide

Review these entries and move confirmed results into the new notebook.

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
