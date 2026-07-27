# Applied Lab 34: Build a raw-to-analytics data workflow

**Category:** Data Workflow  
**Roadmap week:** 10  
**Estimated working time:** 75 minutes  
**Skills:** raw layer, staging views, clean layer, analytical marts, idempotency, validation, lineage

## Scenario

You are the **analytics engineer**. Raw monthly files contain updates, invalid values, and unmatched keys. You will preserve the raw layer, build reproducible staging logic, retain rejected records, and create an analytical output.

## Your assignment

Transform inconsistent raw extracts into documented staging, clean, and analytical layers that can be rebuilt safely.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Preserve the supplied files as the raw layer and create separate staging and analytical outputs.
2. Make each transformation rerunnable from the original inputs.
3. Retain rejected records with a reason instead of silently dropping them.

## Provided files

| File | Purpose |
|---|---|
| `raw_customers.csv` | Raw customer dimension with missing or unmatched keys. |
| `raw_orders_2026_01.csv` | January raw order extract with quality issues. |
| `raw_orders_2026_02.csv` | February raw order extract with updates and duplicates. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Layered SQL workflow.
- Validation report.
- Data-lineage diagram or table.

## Guided workflow

### 1. Load immutable raw monthly files with source-file metadata

- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 2. Create staging views that standardize names and data types

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

### 3. Create clean tables with deduplication and explicit rejection logic

- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.

**Checkpoint:** The transformation is reproducible and the before/after counts or totals are reconciled.

### 4. Create an analytical mart at a documented grain

- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Add row-count, uniqueness, referential, and reconciliation checks

- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 6. Create a lineage document from source to final metric

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Use separate raw, staging, rejected, and analytics objects or files. Add row-count checks between layers and rerun from a clean state.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Rerunning the workflow does not duplicate results.
- [ ] Rejected records are counted and retained for review.
- [ ] Final totals reconcile to accepted raw records.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Editing raw files or overwriting the raw layer.
- Dropping rejected rows without a reason and count.
- Building an analytical table before validating staging keys and types.
- Creating a pipeline that cannot be rerun cleanly.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
