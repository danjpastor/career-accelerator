# Applied Lab 32: Reconcile a finance total discrepancy

**Category:** Timed Analysis  
**Roadmap week:** 10  
**Estimated working time:** 40 minutes  
**Skills:** reconciliation, scope differences, exclusions, grain, audit trail

## Scenario

You are the **finance manager**. Two revenue totals do not agree and a meeting is approaching. You must reconcile the difference, identify the cause, and state which number should be used.

## Your assignment

Explain why a dashboard differs from a finance report and produce an auditable bridge.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Start a timer and spend the first few minutes defining the decision, metric, and minimum evidence required.
2. Prefer a small validated answer over a broad unfinished analysis.
3. Reserve the final minutes for reconciliation and a concise stakeholder response.

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

- Reconciliation bridge.
- Corrected logic or explanation.
- Stakeholder update.

## Guided workflow

### 1. Compare scope, dates, grain, filters, and currency

- Record the time spent on definition, analysis, validation, and communication. Stop adding scope once the minimum decision-ready answer is supported.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Build a bridge between totals

- Record the time spent on definition, analysis, validation, and communication. Stop adding scope once the minimum decision-ready answer is supported.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Identify each difference group

- Record the time spent on definition, analysis, validation, and communication. Stop adding scope once the minimum decision-ready answer is supported.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Determine what requires correction

- Record the time spent on definition, analysis, validation, and communication. Stop adding scope once the minimum decision-ready answer is supported.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Write a neutral stakeholder update

- Record the time spent on definition, analysis, validation, and communication. Stop adding scope once the minimum decision-ready answer is supported.
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

- [ ] Bridge sums exactly.
- [ ] Difference groups are mutually exclusive.
- [ ] Confirmed and open causes are separated.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Spending the time limit building a perfect dashboard instead of answering the question.
- Skipping basic row-count or total reconciliation because of the deadline.
- Giving a precise conclusion when the data supports only a directional answer.
- Failing to state what you did not have time to investigate.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
