# Applied Lab 07: Fix denominator, date-filter, and grain errors

**Category:** Broken Analysis  
**Roadmap week:** 5  
**Estimated working time:** 50 minutes  
**Skills:** KPI denominator, inclusive dates, weighted rates, analysis grain

## Scenario

You are the **report owner**. Several KPI results disagree because the denominator, date boundary, or data grain is wrong. You will isolate each defect and document why the corrected definition is safer.

## Your assignment

Repair a wrong denominator, incomplete date filter, and average-of-averages error.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Do not immediately rewrite the supplied analysis. First reproduce the bad result and record the evidence.
2. State the expected grain and business definition before diagnosing the defect.
3. Keep a before/after comparison so the correction can be reviewed.

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

- Corrected SQL and definitions.
- Broken-vs-corrected table.
- Largest decision impact.

## Guided workflow

### 1. Define the KPI in words

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 2. Identify numerator and denominator populations

- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Correct the date boundary

- Test the exact start and end dates plus one record just outside each boundary so inclusive and exclusive logic is visible.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Replace average-of-averages with a weighted result

- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Compare business interpretation before and after

- Keep each diagnostic query labeled with a comment describing the question it answers. The starter should guide the sequence without containing the finished solution.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Denominator matches stated population.
- [ ] Date boundaries are tested.
- [ ] Weighted result reconciles.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Fixing the symptom without identifying the underlying grain or definition error.
- Changing multiple pieces at once and losing the before/after evidence.
- Assuming a lower or higher total is automatically more correct.
- Failing to explain the business impact of the defect.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
