# Applied Lab 19: Create reusable DAX measures

**Category:** Power BI  
**Roadmap week:** 8  
**Estimated working time:** 60 minutes  
**Skills:** CALCULATE, DIVIDE, conditional logic, variance, time comparison

## Scenario

You are the **production finance manager**. Managers need a small, reusable measure layer for hours, completion, averages, and variance. The numbers must respond correctly to filters and reconcile to an independent calculation.

## Your assignment

Create a reusable measure layer and independently validate its results.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Use **Create / Open Submission** first and record the `.pbix` path or screenshot folder in the submission file.
2. Open the lab dataset folder from Career Accelerator. Keep the supplied files unchanged so your work remains reproducible.
3. Save the Power BI file early, then save again after every major modeling or report milestone.

## Provided files

| File | Purpose |
|---|---|
| `projects.csv` | Project-level attributes and status. |
| `shots.csv` | Shot-level production records. |
| `stage_targets_wide.csv` | Wide target table that must be reshaped for analysis. |
| `time_entries_2026_01.csv` | January time-entry transactions. |
| `time_entries_2026_02.csv` | February time-entry transactions. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Measure dictionary.
- Validation table comparing measures to source totals.
- Note on one filter-context issue.

## Guided workflow

### 1. Create total hours, shot count, completion rate, and average-hours measures

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 2. Use DIVIDE and CALCULATE appropriately

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 3. Create budget and schedule variance measures

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 4. Add a prior-period comparison

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Document formulas and business meaning

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The artifact is saved in the submissions area and contains enough context for another analyst to continue.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Measures respond correctly to filters.
- [ ] Rates use safe division.
- [ ] Totals reconcile to another tool.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Building visuals before confirming source grain and relationships.
- Using calculated columns when a measure is needed to respond to filters.
- Accepting an automatic relationship or data type without validating it.
- Reporting a total without reconciling it to a source or independent calculation.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
