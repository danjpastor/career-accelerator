# Applied Lab 24: Ingest paginated REST API and JSON data

**Category:** Data Acquisition  
**Roadmap week:** 9  
**Estimated working time:** 65 minutes  
**Skills:** HTTP status, pagination, JSON parsing, schema drift, retries, missing fields, deduplication, extraction timestamp

## Scenario

You are the **data integration analyst**. A paginated API returns changing JSON structures, a duplicate record, and a simulated rate-limit response. You must ingest it reliably without using the internet.

## Your assignment

Build a reproducible ingestion script using local API-response fixtures, including pagination, errors, duplicate records, and missing optional fields.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Create the working submission and begin with the supplied local JSON fixtures; internet access is not required.
2. Preserve the raw responses before normalizing them.
3. Log pagination, duplicate handling, type conversion, and schema changes as part of the result.

## Provided files

| File | Purpose |
|---|---|
| `error_429.json` | Simulated rate-limit response. |
| `page_1.json` | First API page and starting pagination link. |
| `page_2.json` | Second API page with additional records. |
| `page_3.json` | Final API page with schema drift. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Runnable ingestion script.
- Flattened CSV output.
- Extraction and validation log.

## Guided workflow

### 1. Read the first response and follow next-page references

- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Preserve each raw response, follow the provided next-page value, normalize only after all pages are collected, and log duplicates or schema changes.
- Write the ingestion as a repeatable loop or function rather than manually copying each page. Keep retry behavior bounded and visible.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 2. Handle a simulated rate-limit or server-error response

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Do not silently replace or remove the record. Count it, retain enough identifying information to investigate it, and state how it affects the result.
- Write the ingestion as a repeatable loop or function rather than manually copying each page. Keep retry behavior bounded and visible.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 3. Flatten nested customer and order fields

- Write the ingestion as a repeatable loop or function rather than manually copying each page. Keep retry behavior bounded and visible.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Detect duplicate identifiers and schema changes

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Write the ingestion as a repeatable loop or function rather than manually copying each page. Keep retry behavior bounded and visible.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 5. Add extraction timestamp, source page, and row-count logging

- Preserve each raw response, follow the provided next-page value, normalize only after all pages are collected, and log duplicates or schema changes.
- Write the ingestion as a repeatable loop or function rather than manually copying each page. Keep retry behavior bounded and visible.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Every page is processed exactly once.
- [ ] Duplicate IDs are detected explicitly.
- [ ] Missing optional fields do not crash the ingestion.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Stopping after the first page of results.
- Flattening data before preserving the raw response.
- Dropping fields when the schema changes on a later page.
- Ignoring duplicate IDs or rate-limit behavior.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
