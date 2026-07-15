# Applied Lab 34: Build a raw-to-analytics data workflow

**Category:** Data Workflow
**Roadmap week:** 10
**Estimated time:** 75 minutes
**Concepts:** raw layer, staging views, clean layer, analytical marts, idempotency, validation, lineage


## Objective

Transform inconsistent raw extracts into documented staging, clean, and analytical layers that can be rebuilt safely.

## Steps

1. Load immutable raw monthly files with source-file metadata.
2. Create staging views that standardize names and data types.
3. Create clean tables with deduplication and explicit rejection logic.
4. Create an analytical mart at a documented grain.
5. Add row-count, uniqueness, referential, and reconciliation checks.
6. Create a lineage document from source to final metric.

## Deliverables

- Layered SQL workflow.
- Validation report.
- Data-lineage diagram or table.

## Submission workflow

Use **Learning Dashboard → Applied Labs → Create / Open Submission**.
Work in the saved submission rather than changing this starter.
