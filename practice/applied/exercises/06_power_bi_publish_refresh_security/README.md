# Applied Lab 26: Document publishing, refresh, and row-level security

**Category:** Power BI  
**Roadmap week:** 9  
**Estimated working time:** 45 minutes  
**Skills:** Power BI Service, refresh planning, ownership, row-level security

## Scenario

You are the **analytics manager**. A report is not production-ready until ownership, refresh, release, and security are documented. You will prepare the operating plan another analyst could follow after handoff.

## Your assignment

Document how a real report would be published, refreshed, owned, and secured.

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

- Deployment and refresh plan.
- RLS role definition and tests.
- Release checklist.

## Guided workflow

### 1. Define workspace and audience strategy

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Define refresh frequency and failure handling

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Draft an RLS rule and test matrix

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Use an independent check whenever possible. Record expected result, actual result, pass/fail status, and the action taken for any failure.
- Describe each role as a rule and a test case. Include a user who should see all rows, one who should see a subset, and one who should see none.

**Checkpoint:** The evidence shows expected value, actual value, and a clear pass/fail conclusion.

### 4. Assign report owner, backup owner, and data steward

- Start with the stakeholder question, choose the simplest visual that answers it, label units and time periods, and remove anything that does not support the decision.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** A reader can identify the question, result, unit, time period, and implication without additional explanation.

### 5. Create a release checklist

- Use a clear filename and location, document how to reproduce or refresh the output, and reopen the saved artifact to confirm it still works.
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

- [ ] Refresh timing matches decision cadence.
- [ ] Security scenarios are testable.
- [ ] Ownership is explicit.
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
