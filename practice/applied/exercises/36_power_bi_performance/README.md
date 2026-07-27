# Applied Lab 36: Optimize Power BI model and refresh performance

**Category:** Power BI  
**Roadmap week:** 12  
**Estimated working time:** 60 minutes  
**Skills:** query folding, model size, cardinality, storage mode, measure versus column, incremental refresh, Performance Analyzer

## Scenario

You are the **Power BI owner**. An existing report is slow to refresh and interact with. You will identify likely transformation, model, measure, and report bottlenecks and prioritize safe improvements.

## Your assignment

Review an existing Power BI project for transformation, model, refresh, and report-performance opportunities.

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

- Performance review checklist.
- Before-and-after model or refresh observations.
- Prioritized optimization plan.

## Guided workflow

### 1. Identify transformations that can preserve query folding

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Remove unused columns and reduce high-cardinality text where appropriate

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Review calculated columns versus measures

- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Document Import, DirectQuery, or composite-model tradeoffs

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Use **Get Data** and open **Transform Data** before loading. Give each query a business-readable name and avoid loading helper queries that are not needed in the model.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 5. Draft an incremental-refresh policy

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.

**Checkpoint:** The artifact is saved in the submissions area and contains enough context for another analyst to continue.

### 6. Use or simulate Performance Analyzer findings and prioritize fixes

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

- [ ] Optimizations preserve analytical meaning.
- [ ] Performance claims are supported by a measurement or documented expectation.
- [ ] The incremental-refresh policy includes date boundaries and retention.
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
