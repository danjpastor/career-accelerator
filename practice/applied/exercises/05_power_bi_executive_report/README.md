# Applied Lab 05: Build an executive report with guided interactions

**Category:** Power BI  
**Roadmap week:** 9  
**Estimated working time:** 75 minutes  
**Skills:** visual hierarchy, slicers, drill-through, tooltips, accessibility

## Scenario

You are the **executive producer**. Leadership needs a concise report that answers a few operational questions quickly. Your assignment is to turn the model into a focused decision tool rather than a collection of unrelated visuals.

## Your assignment

Turn the model into a concise report that supports a named management decision.

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

- Overview and detail pages.
- Portfolio-ready screenshots.
- Decision supported by each page.

## Guided workflow

### 1. Define the audience, decision, and three questions

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Build an overview page with clear visual hierarchy

- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Preserve each raw response, follow the provided next-page value, normalize only after all pages are collected, and log duplicates or schema changes.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

### 3. Add useful slicers, drill-through, and a tooltip page

- Preserve each raw response, follow the provided next-page value, normalize only after all pages are collected, and log duplicates or schema changes.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Check titles, units, contrast, alt text, and layout

- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

### 5. Remove visuals that do not support a question

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

- [ ] Every visual answers a named question.
- [ ] The report fits common laptop resolution.
- [ ] Titles remain meaningful after filters.
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
