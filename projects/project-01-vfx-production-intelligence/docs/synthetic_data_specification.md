ChatGPT Plus

Walk me through step by step to create synthetic data specification for my first portfolio project


I built the complete, portfolio-ready specification for Project 1: VFX Production Intelligence.

Place it here in your repository:

project-01-vfx-production-intelligence/
└── docs/
    └── synthetic_data_specification.md

It includes the complete business scenario, stakeholders, relational data model, six table schemas, generation rules, realistic correlations, cleaning defects, KPI formulas, validation requirements, project structure, assumptions, limitations, and definition of done.

Your next implementation file is:

scripts/generate_synthetic_data.py


Next, I’m building the complete generate_synthetic_data.py script, then I’ll run it to verify the six linked CSV files and validation checks work correctly.

what is this script for

No. I generated only the specification document:

docs/synthetic_data_specification.md

That file describes what the dataset should contain, but it does not create any data.

These have not been generated yet:

scripts/generate_synthetic_data.py

data/raw/projects.csv
data/raw/artists.csv
data/raw/shots.csv
data/raw/assignments.csv
data/raw/reviews.csv
data/raw/worklogs.csv

The next step is to build and run the Python generator so those six CSV files actually exist.

These were already generated in another chat

You’re right—I lost track of the work completed in the other chat.

The VFX synthetic dataset was already generated with:

data/raw/vfx_production_intelligence_synthetic_raw.xlsx

data/raw/csv/
├── raw_clients.csv
├── raw_projects.csv
├── raw_artists.csv
├── raw_shots.csv
├── raw_time_entries.csv
└── raw_reviews.csv

It also included supporting files such as:

DATASET_SETUP.md
DATASET_MANIFEST.md
docs/source_brief/
docs/analysis/

So we do not need another data-generation script.

There is also an important mismatch: the specification I just created describes assignments and worklogs, while the existing dataset uses clients and time_entries. The correct next step is to align the specification with the dataset already built, then begin the data inspection and cleaning phase.

do that

I’m locating the existing dataset and its supporting files first, then I’ll rebuild the specification so it matches the actual tables and columns exactly.

Make sure the specification only includes absolutely necesary info that would normally need to be delivered in the real world

I replaced the oversized version with a concise, real-world dataset specification aligned to the existing workbook and its actual six tables: Clients, Projects, Artists, Shots, Time Entries, and Reviews.

It now contains only:

    Dataset purpose and delivery scope

    Actual table grains, columns, and relationships

    Required KPI definitions

    Essential cleaning and validation rules

    Processed deliverables

    Acceptance criteria

Place it here, replacing the earlier version:

project-01-vfx-production-intelligence/
└── docs/
    └── synthetic_data_specification.md


Library
/
Data Analytics Career Change
/synthetic_data_specification.md

# Synthetic Dataset Specification

## VFX Production Intelligence

**Version:** 2.0  
**Prepared by:** Dan Pastor  
**Dataset:** SpectraForge VFX — Production Intelligence Synthetic Dataset  
**Classification:** Fully synthetic portfolio data

---

## 1. Purpose

This dataset supports analysis of VFX production performance, including:

- On-time delivery
- Estimate accuracy
- Artist utilization
- Revision activity
- Overtime and workload
- Project and department risk

All people, clients, projects, and production records are fictional. No confidential or real production data is included.

---

## 2. Delivery Scope

### Primary Source

```text
data/raw/vfx_production_intelligence_synthetic_raw.xlsx
```

### Raw CSV Exports

```text
data/raw/csv/raw_clients.csv
data/raw/csv/raw_projects.csv
data/raw/csv/raw_artists.csv
data/raw/csv/raw_shots.csv
data/raw/csv/raw_time_entries.csv
data/raw/csv/raw_reviews.csv
```

### Dataset Size

| Table | Rows | Grain |
|---|---:|---|
| Clients | 14 | One row per client export record |
| Projects | 16 | One row per project export record |
| Artists | 62 | One row per artist export record |
| Shots | 1,136 | One row per shot export record |
| Time Entries | 6,935 | One row per timesheet entry |
| Reviews | 3,883 | One row per review event |

### Reporting Cutoff

Use **June 30, 2026** as the initial reporting date for open and overdue work.

---

## 3. Data Model

```text
Clients
  1 ───< Projects
            1 ───< Shots
                      1 ───< Time Entries
                      1 ───< Reviews

Artists
  1 ───< Shots
  1 ───< Time Entries
```

### Key Relationships

| Parent Table | Primary Key | Child Table | Foreign Key |
|---|---|---|---|
| Clients | `client_id` | Projects | `client_id` |
| Projects | `project_id` | Shots | `project_id` |
| Projects | `project_id` | Time Entries | `project_id` |
| Projects | `project_id` | Reviews | `project_id` |
| Artists | `artist_id` | Shots | `assigned_artist_id` |
| Artists | `artist_id` | Time Entries | `artist_id` |
| Shots | `shot_id` | Time Entries | `shot_id` |
| Shots | `shot_id` | Reviews | `shot_id` |

---

## 4. Table Definitions

## 4.1 Clients

**File:** `raw_clients.csv`  
**Grain:** One row per client export record  
**Primary key:** `client_id`

| Column | Type | Description |
|---|---|---|
| `client_id` | Text | Client identifier |
| `client_name` | Text | Fictional client or studio name |
| `client_type` | Text | Client business category |
| `region` | Text | Primary operating region |
| `contract_tier` | Text | Commercial service tier |
| `revision_tendency_index` | Decimal | Synthetic multiplier for revision behavior |
| `default_review_sla_hours` | Integer | Expected review turnaround |
| `active_flag` | Boolean-like text | Whether the client is active |
| `account_manager` | Text | Internal account owner |
| `notes` | Text | Optional account notes |

---

## 4.2 Projects

**File:** `raw_projects.csv`  
**Grain:** One row per project export record  
**Primary key:** `project_id`  
**Foreign key:** `client_id`

| Column | Type | Description |
|---|---|---|
| `project_id` | Text | Project identifier |
| `client_id` | Text | Owning client |
| `project_name` | Text | Fictional project title |
| `project_type` | Text | Feature, episodic, commercial, trailer, or game cinematic |
| `start_date` | Date text | Production start date |
| `target_delivery_date` | Date text | Planned delivery date |
| `actual_delivery_date` | Date text | Actual project delivery date |
| `status` | Text | Current project status |
| `priority` | Text | Operational priority |
| `planned_shot_count` | Integer | Planned number of shots |
| `budget_hours` | Decimal | Approved labor-hour budget |
| `producer` | Text | Production owner |
| `vfx_supervisor` | Text | VFX supervisor |
| `fps` | Decimal | Project frame rate |
| `resolution` | Text | Delivery resolution |
| `delivery_format` | Text | Delivery media format |

---

## 4.3 Artists

**File:** `raw_artists.csv`  
**Grain:** One row per artist export record  
**Primary key:** `artist_id`

| Column | Type | Description |
|---|---|---|
| `artist_id` | Text | Artist identifier |
| `artist_name` | Text | Fictional artist name |
| `department` | Text | Primary department |
| `role` | Text | Production role |
| `seniority` | Text | Junior, Mid, Senior, or Lead |
| `location` | Text | Office or remote location |
| `weekly_capacity_hours` | Decimal | Expected weekly capacity |
| `hourly_cost_usd` | Decimal | Synthetic internal labor cost |
| `hire_date` | Date text | Employment start date |
| `active_flag` | Boolean-like text | Whether the artist is active |
| `manager_id` | Text | Self-reference to another artist |
| `email` | Text | Synthetic non-routable email |

---

## 4.4 Shots

**File:** `raw_shots.csv`  
**Grain:** One row per shot export record  
**Primary key:** `shot_id`  
**Foreign keys:** `project_id`, `assigned_artist_id`

| Column | Type | Description |
|---|---|---|
| `shot_id` | Text | Project-sequence-shot identifier |
| `project_id` | Text | Owning project |
| `sequence_code` | Text | Editorial sequence code |
| `shot_name` | Text | Shot name or code |
| `department` | Text | Responsible department |
| `assigned_artist_id` | Text | Primary assigned artist |
| `assigned_date` | Date text | Date assigned |
| `start_date` | Date text | Date work began |
| `deadline` | Date text | Required delivery date |
| `delivery_date` | Date text | Actual delivery date |
| `first_pass_date` | Date text | First review submission date |
| `final_approval_date` | Date text | Final approval date |
| `status` | Text | Shot workflow status |
| `priority` | Text | Shot urgency |
| `complexity` | Text | Estimated complexity |
| `estimated_hours` | Decimal | Planned labor hours |
| `actual_hours` | Decimal | Reported actual labor hours |
| `internal_revision_count` | Integer | Internal revision rounds |
| `client_revision_count` | Integer | Client-requested revision rounds |
| `revision_count_reported` | Integer | Reported total revisions |
| `hold_days` | Integer | Days blocked or on hold |
| `vendor_dependencies` | Text | External dependency category |
| `notes` | Text | Optional production notes |

---

## 4.5 Time Entries

**File:** `raw_time_entries.csv`  
**Grain:** One row per timesheet entry  
**Primary key:** `time_entry_id`  
**Foreign keys:** `shot_id`, `project_id`, `artist_id`

| Column | Type | Description |
|---|---|---|
| `time_entry_id` | Text | Timesheet entry identifier |
| `shot_id` | Text | Shot receiving the time |
| `project_id` | Text | Project receiving the time |
| `artist_id` | Text | Artist logging the time |
| `work_date` | Date text | Date of work |
| `hours_logged` | Decimal | Hours recorded |
| `task_type` | Text | Production, review fixes, setup, QC, or R&D |
| `billable_flag` | Boolean-like text | Whether the time is billable |
| `overtime_flag` | Boolean-like text | Whether the entry is overtime |
| `source_system` | Text | Source application |
| `comment` | Text | Optional timesheet comment |

---

## 4.6 Reviews

**File:** `raw_reviews.csv`  
**Grain:** One row per review event  
**Primary key:** `review_id`  
**Foreign keys:** `shot_id`, `project_id`

| Column | Type | Description |
|---|---|---|
| `review_id` | Text | Review event identifier |
| `shot_id` | Text | Reviewed shot |
| `project_id` | Text | Owning project |
| `review_date` | Date text | Date of review |
| `review_round` | Integer | Sequential review round |
| `review_type` | Text | Internal or client review |
| `feedback_source` | Text | Person or group giving feedback |
| `outcome` | Text | Review result |
| `note_category` | Text | Primary feedback category |
| `response_hours` | Decimal | Time until feedback was addressed |
| `reviewer` | Text | Reviewer name |
| `notes` | Text | Optional review notes |

---

## 5. Required KPI Definitions

| KPI | Calculation |
|---|---|
| On-time delivery rate | Completed shots with `delivery_date <= deadline` ÷ completed shots |
| Average turnaround time | Average valid `delivery_date - start_date` |
| Artist utilization | Weekly `SUM(hours_logged)` ÷ `weekly_capacity_hours` |
| Revision rate | Total internal and client revisions ÷ completed shots |
| Estimate accuracy | `1 - ABS(actual_hours - estimated_hours) / estimated_hours` |
| Hours variance | `actual_hours - estimated_hours` |
| Hours variance percentage | `(actual_hours - estimated_hours) / estimated_hours` |
| Shots completed per week | Count completed shots by delivery week |
| Overdue shot count | Open shots with `deadline < 2026-06-30` |
| Client revision burden | Client review volume and response time by client |
| Actual labor cost | `hours_logged × hourly_cost_usd` |
| Overtime rate | Overtime hours ÷ total hours |

### KPI Exclusions

Exclude records from KPI calculations when required fields remain invalid after cleaning.

Examples:

- Missing or invalid dates
- Non-positive estimated hours
- Invalid capacity values
- Unresolved foreign keys
- Duplicate fact rows

---

## 6. Required Data Cleaning Rules

The raw files intentionally contain data-quality issues. Cleaning must preserve the raw source and produce separate processed tables.

### Standardization

- Trim leading and trailing whitespace.
- Standardize identifier casing.
- Standardize department, status, outcome, region, and task labels.
- Convert boolean-like values to `True`, `False`, or null.
- Parse dates into `YYYY-MM-DD`.
- Convert hours, capacity, cost, counts, and budgets to numeric types.

### Validation

- Enforce unique primary keys.
- Validate all foreign keys.
- Remove exact duplicate rows.
- Quarantine rows with unrecoverable key, date, or numeric errors.
- Reject negative hours, budgets, costs, capacities, and response times.
- Reject time entries above 24 hours.
- Validate logical date order.
- Reconcile project IDs stored in child tables against the related shot.
- Reconcile reported revision counts against review-event records.
- Compare shot `actual_hours` against summed time-entry hours.

### Raw Data Preservation

The raw workbook and raw CSV files must not be edited in place.

---

## 7. Processed Deliverables

```text
data/processed/clients_clean.csv
data/processed/projects_clean.csv
data/processed/artists_clean.csv
data/processed/shots_clean.csv
data/processed/time_entries_clean.csv
data/processed/reviews_clean.csv
```

Supporting deliverables:

```text
docs/data_quality_report.md
docs/data_dictionary.md
sql/schema.sql
sql/data_quality_checks.sql
```

---

## 8. Acceptance Criteria

The processed dataset is ready for analysis when:

- Primary keys are unique and non-null.
- Foreign-key exceptions are resolved or quarantined.
- Dates and numeric fields use consistent types.
- Duplicate fact rows are removed.
- Required categories are standardized.
- Invalid numeric and date values are excluded from KPI calculations.
- Shot hours and revision totals are reconciled or documented.
- All six processed tables load successfully into SQL and Power BI.
- The data-quality report documents removed, corrected, and quarantined records.

