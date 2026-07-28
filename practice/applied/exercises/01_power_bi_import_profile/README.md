# Applied Lab 14: Import and profile operational data in Power BI

**Category:** Power BI  
**Roadmap week:** 7  
**Estimated working time:** 45 minutes  
**Skills:** Power Query import, data types, column profiling, source documentation

## Scenario

You are the **production analytics lead**. Before a VFX operations model can be trusted, the source exports must be profiled and their grain documented. Leadership wants an evidence-based list of data issues before any relationships or measures are built.

## Your assignment

Load operational exports, inspect their grain and quality, and document what must be corrected before modeling.

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

- Power BI file or screenshots of the imported queries.
- Profiling table with issue, impact, and proposed fix.
- Source and refresh assumptions note.

## Guided workflow

### 1. Import the supplied projects, shots, and time-entry files

- Inspect the source names and previews first. Record row counts, columns, and the intended grain before changing data types or values.
- Use **Get Data** and open **Transform Data** before loading. Give each query a business-readable name and avoid loading helper queries that are not needed in the model.

**Checkpoint:** Every required source is present, named clearly, and has a recorded row count and grain.

### 2. Assign data types and use Power Query profiling views

- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- In Power Query, enable Column Quality, Column Distribution, and Column Profile. Change profiling to the entire dataset when available, then capture the issue counts you will act on.

**Checkpoint:** The issue counts and affected fields are recorded, and no treatment is applied without documenting its effect.

### 3. Document missing values, duplicates, suspicious ranges, and source grain

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Use a small profile table with field, expected type or rule, observed issue, affected rows, business impact, and proposed treatment.
- In Power Query, enable Column Quality, Column Distribution, and Column Profile. Change profiling to the entire dataset when available, then capture the issue counts you will act on.

**Checkpoint:** The expected key is unique or the duplicate keys and counts are returned as actionable evidence.

### 4. Rename queries and fields for stakeholder readability

- Use names that describe the business entity or field, keep naming consistent across tables, and avoid abbreviations another analyst would have to decode.
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

- [ ] Every table has a stated grain and candidate key.
- [ ] Dates and numeric fields use correct data types.
- [ ] At least three quality observations are supported by evidence.
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
