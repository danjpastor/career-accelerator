# Applied Lab 20: Load and profile data with pandas

**Category:** Python  
**Roadmap week:** 8  
**Estimated working time:** 45 minutes  
**Skills:** read_csv, dtypes, shape, missing values, duplicates, statistics

## Scenario

You are the **operations analyst**. You have received several operational exports and must determine whether they are safe to analyze. Your first deliverable is a reproducible pandas profile that identifies grain, types, missingness, duplicates, and suspicious values.

## Your assignment

Use a reproducible script to inspect data before cleaning.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Use **Create / Open Submission** to create a working copy of the starter Python file.
2. Run the file in small sections and inspect intermediate shapes, columns, and values before moving on.
3. Use assertions or explicit checks for grain, row counts, and totals; do not rely only on the final printed output.

## Provided files

| File | Purpose |
|---|---|
| `customers.csv` | Customer attributes used for grouping and joins. |
| `finance_report.csv` | Independent finance totals used for reconciliation. |
| `orders.csv` | Order-level operational records. |
| `products.csv` | Product attributes, prices, or costs. |
| `returns.csv` | Return transactions that may contain multiple rows per order. |
| `targets.csv` | Regional or monthly performance targets. |
| `tickets.csv` | Support-ticket dates, status, and service information. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Runnable Python submission.
- Generated profile.
- Three quality findings.

## Guided workflow

### 1. Load orders and customers

- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Use the starter script to print or record shape, column names, data types, missing counts, duplicate counts, and a small sample. Keep these checks readable rather than dumping the entire DataFrame.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 2. Print shape, columns, dtypes, and samples

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Measure nulls, duplicates, and unexpected categories

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 4. Calculate descriptive statistics

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 5. Export a compact profile

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.
- Use the starter script to print or record shape, column names, data types, missing counts, duplicate counts, and a small sample. Keep these checks readable rather than dumping the entire DataFrame.
- Write outputs to the Applied Labs submissions folder with stable column names and no accidental index column. Read the saved file back to verify it.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Relative paths are used.
- [ ] Key uniqueness is checked.
- [ ] The script reruns without manual edits.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Overwriting the original DataFrame before verifying the transformation.
- Merging without checking key uniqueness and row-count changes.
- Printing a result without saving a reusable output or validation evidence.
- Hardcoding a value that should be calculated from the data.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
