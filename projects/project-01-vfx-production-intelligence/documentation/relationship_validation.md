<!-- DCA Portfolio Findings Template v2 -->
# VFX Production Intelligence Dashboard — Relationship Validation

Use this document to record what your SQL checks found. Replace the starter text with your own results and conclusions.

## Relationships tested

| Child table | Foreign key | Parent table | Parent key | Result | Notes |
|---|---|---|---|---|---|
| `raw.shots` | `assigned_artist_id` | `raw.artists` | `artist_id` | Not tested | |
| `raw.time_entries` | `artist_id` | `raw.artists` | `artist_id` | Not tested | |
| `raw.projects` | `client_id` | `raw.clients` | `client_id` | Not tested | |
| `raw.reviews` | `project_id` | `raw.projects` | `project_id` | Not tested | |
| `raw.shots` | `project_id` | `raw.projects` | `project_id` | Not tested | |
| `raw.time_entries` | `project_id` | `raw.projects` | `project_id` | Not tested | |
| `raw.reviews` | `shot_id` | `raw.shots` | `shot_id` | Not tested | |
| `raw.time_entries` | `shot_id` | `raw.shots` | `shot_id` | Not tested | |

## Duplicate primary keys

Describe any duplicate identifiers you found, or state that none were returned.

## Orphaned foreign keys

Describe child records that did not match a parent record, or state that none were returned.

## Join cardinality

Record whether each join preserved the expected child-row count.

## Exceptions and decisions

Document intentional exceptions, source-data problems, and any cleanup decisions.

## Final conclusion

State whether the tested relationships are safe to use for analysis and what must be fixed first.
