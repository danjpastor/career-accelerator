# Applied Lab 02: Clean, merge, append, pivot, and unpivot with Power Query

**Category:** Power BI  
**Roadmap week:** 7  
**Estimated working time:** 60 minutes  
**Skills:** Power Query cleaning, merge, append, pivot, unpivot

## Scenario

You are the **BI developer**. The monthly VFX exports arrive in shapes that cannot be analyzed together. You have been asked to create a repeatable Power Query flow that cleans, combines, and reshapes them without editing the source files.

## Your assignment

Create a repeatable transformation flow that converts raw exports into analysis-ready tables.

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

- Transformation-flow screenshots or notes.
- Before-and-after row counts.
- Explanation of why the long target table is easier to analyze.

## Guided workflow

### 1. Trim and standardize text and replace invalid blanks with nulls

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- Preserve the raw value or raw layer, make one transformation at a time, and compare counts or distinct values before and after the change.
- Do not silently replace or remove the record. Count it, retain enough identifying information to investigate it, and state how it affects the result.
- In Power Query, enable Column Quality, Column Distribution, and Column Profile. Change profiling to the entire dataset when available, then capture the issue counts you will act on.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

### 2. Merge shots to projects and verify join cardinality

- Test key uniqueness on both sides first. Predict the expected row count and cardinality, then compare that prediction with the result.
- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.

**Checkpoint:** The result has the expected cardinality, row count, and unmatched-key behavior.

### 3. Append the monthly time-entry files

- Confirm the inputs have compatible columns, add a source-period field if useful, and reconcile the appended row count to the sum of the inputs.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Unpivot the wide stage-target table

- State what one row should represent after reshaping. Reconcile totals before and after so the shape changes without changing the underlying amount.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The transformation is reproducible and the before/after counts or totals are reconciled.

### 5. Name and document every transformation step

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

- [ ] The merge does not duplicate shot grain.
- [ ] The appended total equals both inputs combined.
- [ ] The unpivoted data reconciles to the wide source.
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
