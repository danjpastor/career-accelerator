# Applied Lab 03: Build and apply a SQL validation checklist

**Category:** SQL Validation  
**Roadmap week:** 4  
**Estimated working time:** 45 minutes  
**Skills:** row counts, uniqueness, nulls, referential integrity, duplicates, reconciliation, boundaries

## Scenario

You are the **senior analyst**. A query result cannot be approved until a reusable validation checklist proves row counts, grain, nulls, relationships, totals, and date boundaries.

## Your assignment

Create reusable checks that must pass before results are trusted.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Create the SQL submission and review the automatically loaded table names shown in the in-app workspace.
2. Write one labeled validation query at a time and keep the result interpretable as pass/fail evidence.
3. Run checks before and after any correction so the submission proves what changed.

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

- Reusable validation SQL.
- Pass/fail checklist.
- One failed check and correction.

## Guided workflow

### 1. Check source and output row counts

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

### 2. Test expected-grain uniqueness

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Compare total row count with distinct key count and return the offending keys with their occurrence counts so the failure can be investigated.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 3. Measure nulls in required fields

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Count nulls by required field and return example records. State whether a null is invalid, expected, or conditionally allowed.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

### 4. Test referential integrity

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Use an anti-join or equivalent check to return child keys that do not exist in the parent table, then count and inspect them.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

### 5. Detect duplicates and reconcile totals

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Compare total row count with distinct key count and return the offending keys with their occurrence counts so the failure can be investigated.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 6. Test date boundaries and explain the result

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Test the exact start and end dates plus one record just outside each boundary so inclusive and exclusive logic is visible.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Checks return interpretable evidence.
- [ ] Reconciliation is independent.
- [ ] Boundary tests cover both edges.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Writing checks that return numbers without stating what pass or fail means.
- Checking only the final table and not the source or intermediate grain.
- Using the same logic to calculate and validate a total.
- Ignoring boundary dates, nulls, or unmatched keys.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
