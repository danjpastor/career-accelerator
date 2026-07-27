# Applied Lab 09: Clean and merge operational tables with pandas

**Category:** Python  
**Roadmap week:** 8  
**Estimated working time:** 55 minutes  
**Skills:** string cleaning, dates, missing values, merge validation, duplicate control

## Scenario

You are the **operations analyst**. The source tables contain inconsistent values and must be combined without changing the order grain. You will create a clean analytical table and prove that the joins did not create or lose records.

## Your assignment

Create a clean analysis table while protecting its intended grain.

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

- Cleaning script.
- Clean output CSV.
- Reconciliation report.

## Guided workflow

### 1. Standardize text and dates

- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The transformation is reproducible and the before/after counts or totals are reconciled.

### 2. Handle missing identifiers explicitly

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

### 3. Merge orders, customers, products, and returns with validation

- Test key uniqueness on both sides first. Predict the expected row count and cardinality, then compare that prediction with the result.
- Use merge validation or explicit uniqueness checks when possible. Compare the row count and unmatched keys before accepting the result.

**Checkpoint:** The result has the expected cardinality, row count, and unmatched-key behavior.

### 4. Create a row-count reconciliation table

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Export clean detail data

- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.
- Write outputs to the Applied Labs submissions folder with stable column names and no accidental index column. Read the saved file back to verify it.

**Checkpoint:** The transformation is reproducible and the before/after counts or totals are reconciled.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] One row per intended order line.
- [ ] Unexpected many-to-many merges fail.
- [ ] Excluded rows are counted and explained.
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
