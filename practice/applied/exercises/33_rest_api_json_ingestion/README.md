# Applied Lab 33: Ingest paginated REST API and JSON data

**Category:** Data Acquisition
**Roadmap week:** 9
**Estimated time:** 65 minutes
**Concepts:** HTTP status, pagination, JSON parsing, schema drift, retries, missing fields, deduplication, extraction timestamp


## Objective

Build a reproducible ingestion script using local API-response fixtures, including pagination, errors, duplicate records, and missing optional fields.

## Steps

1. Read the first response and follow next-page references.
2. Handle a simulated rate-limit or server-error response.
3. Flatten nested customer and order fields.
4. Detect duplicate identifiers and schema changes.
5. Add extraction timestamp, source page, and row-count logging.

## Deliverables

- Runnable ingestion script.
- Flattened CSV output.
- Extraction and validation log.

## Submission workflow

Use **Learning Dashboard → Applied Labs → Create / Open Submission**.
Work in the saved submission rather than changing this starter.
