# Applied Lab 35: Audit an AI-generated analysis

**Category:** Responsible AI  
**Roadmap week:** 11  
**Estimated working time:** 60 minutes  
**Skills:** hallucinated fields, duplicated joins, denominator errors, unsupported claims, chart risk, verification trail

## Scenario

You are the **analytics reviewer**. An AI-generated query, summary, and chart recommendation look plausible but contain deliberate flaws. You must verify every important claim against the source data.

## Your assignment

Review a plausible AI-generated query, summary, and chart recommendation; identify every unsupported or incorrect element; and produce a verified replacement.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Treat every AI-produced number, join, definition, and conclusion as unverified.
2. Reproduce the query and claims against the source data before editing them.
3. Keep an audit table that separates confirmed, incorrect, unsupported, and ambiguous claims.

## Provided files

| File | Purpose |
|---|---|
| `ai_chart_recommendation.md` | AI chart recommendation to audit for framing and suitability. |
| `ai_generated_query.sql` | AI-written SQL that may contain logic defects. |
| `ai_generated_summary.md` | AI-written conclusions that must be verified. |
| `customers.csv` | Customer attributes used for grouping and joins. |
| `orders.csv` | Order-level operational records. |
| `products.csv` | Product attributes, prices, or costs. |
| `returns.csv` | Return transactions that may contain multiple rows per order. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Issue log.
- Corrected query and verified results.
- Rewritten summary and chart recommendation.

## Guided workflow

### 1. Identify nonexistent or misused fields

- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Diagnose join duplication and denominator errors

- Test key uniqueness on both sides first. Predict the expected row count and cardinality, then compare that prediction with the result.
- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.

**Checkpoint:** The result has the expected cardinality, row count, and unmatched-key behavior.

### 3. Check every numerical claim against source data

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Trace the claim to a specific query, field, or calculation. Label it confirmed, incorrect, unsupported, or ambiguous and attach the evidence.
- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

### 4. Separate observation, inference, and recommendation

- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Replace the misleading chart recommendation

- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

### 6. Document a reusable AI-output verification checklist

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Trace the claim to a specific query, field, or calculation. Label it confirmed, incorrect, unsupported, or ambiguous and attach the evidence.
- Do not repair the AI output until you have captured the original defect and its impact. The audit should show what a reviewer would need to catch.

**Checkpoint:** The artifact is saved in the submissions area and contains enough context for another analyst to continue.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Every correction links to a validation check.
- [ ] Unsupported causal or universal claims are removed.
- [ ] The final analysis can be reproduced without trusting the AI output.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Correcting the prose without checking the underlying query.
- Trusting a plausible chart choice without checking the metric and denominator.
- Failing to distinguish an incorrect claim from an unsupported claim.
- Using another AI response as the only validation source.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
