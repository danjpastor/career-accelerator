# Applied Lab 12: Perform and interpret a hypothesis test

> This guide tells you what decisions to make, what output to produce, and how to validate it. It intentionally does not provide the finished formula, query, measure, code, or numerical answer.

## Assignment

Test a clearly defined difference, interpret the result correctly, and separate insufficient evidence from evidence of no effect.

## Skills you will apply

null hypothesis, alternative hypothesis, test statistic, p-value, significance level, Type I and Type II errors

## Stage 1: Frame the request and define success

Turn the assignment into a clear analytical question before using a tool. The lab objective is to test a clearly defined difference, interpret the result correctly, and separate insufficient evidence from evidence of no effect..

### What to do

1. Read the business assignment, deliverables, and validation criteria from beginning to end before opening the starter.
2. Rewrite the request as one question that names the audience, decision, entity being analyzed, and time period.
3. List the concepts you expect to use: null hypothesis, alternative hypothesis, test statistic, p-value, significance level, Type I and Type II errors.
4. Define what a trustworthy final result must contain and what would make the result unsafe to use.
5. Create the submission and add a short assumptions section. Do not begin the final calculation yet.

### Required output

A clearly stated business question, definition of done, and initial assumptions list inside the lab submission.

### Check your work

- The question can be answered with the supplied data and does not assume a result.
- The intended audience and decision are explicit.
- The definition of done matches the lab deliverables rather than adding portfolio-scale work.

### Evidence to record

Record the business question, intended decision, and the most important assumption you identified.

### Common mistakes

- Starting calculations before deciding what one row or observation represents.
- Expanding the scope beyond the lab's requested decision.
- Treating an assumption as a confirmed fact.

## Stage 2: Inspect the sources and plan the method

Understand the data and choose a safe analysis path before building the result.

### What to do

1. Identify the target population, observed sample, variables, measurement units, and outcome of interest.
2. State the statistical question without assuming the result in advance.
3. Check whether the method's assumptions are reasonable for the available data.
4. Plan both a technical interpretation and a stakeholder-friendly interpretation of uncertainty.
5. Use the source preview or tool profiler to record row counts, columns, data types, missing fields, duplicate candidates, date coverage, and measurement units.
6. Identify the candidate key for each source and state what one row represents.
7. Write a short plan that names the intermediate outputs you will create and the order in which you will validate them.
8. Note any source limitation that could weaken the final conclusion.

### Required output

A source inventory, grain statement, key map, and short analysis plan.

### Check your work

- Every source has a stated grain and candidate key or a documented reason that no unique key exists.
- The planned method uses only skills available from prerequisite coursework unless the guide explicitly introduces a new method.
- The plan includes at least one check that is independent of the final calculation.

### Evidence to record

Record the source grain, candidate key, row-count check, and one data-quality concern or limitation.

### Common mistakes

- Joining or merging sources before checking whether the key is unique.
- Changing raw data instead of creating a traceable cleaned layer.
- Assuming dates, percentages, currency, or identifiers already use the correct type.

## Stage 3: Build the analysis in traceable steps

Apply the required skills while keeping each transformation and calculation understandable and testable.

### What to do

1. State the null and alternative hypotheses before calculating. Before you begin, identify which source fields and assumptions this step depends on. Complete the work in a clearly labeled section of the submission, then run a small check that would expose a missing row, duplicate entity, incorrect filter, or mismatched unit.
2. Choose a significance level and explain the choice. Before you begin, identify which source fields and assumptions this step depends on. Complete the work in a clearly labeled section of the submission, then run a small check that would expose a missing row, duplicate entity, incorrect filter, or mismatched unit.
3. Compare conversion or mean outcome between two groups. Before you begin, identify which source fields and assumptions this step depends on. Complete the work in a clearly labeled section of the submission, then run a small check that would expose a missing row, duplicate entity, incorrect filter, or mismatched unit.
4. Calculate or approximate a test statistic and p-value. Before you begin, identify which source fields and assumptions this step depends on. Complete the work in a clearly labeled section of the submission, then run a small check that would expose a missing row, duplicate entity, incorrect filter, or mismatched unit.
5. Discuss Type I, Type II, and sample-size risks. Before you begin, identify which source fields and assumptions this step depends on. Complete the work in a clearly labeled section of the submission, then run a small check that would expose a missing row, duplicate entity, incorrect filter, or mismatched unit.
6. Use comments, readable names, or labeled worksheet sections so another learner can follow the order of operations.
7. After each major step, compare row counts and unique entity counts with the prior stage before moving on.
8. Keep exact solutions out of notes copied from external sources; explain why the method fits this business question in your own words.

### Required output

A working analysis that produces the requested intermediate and final outputs without manually typing calculated answers.

### Check your work

- The output grain matches the grain defined in Stage 2.
- Filters, exclusions, and missing-value rules are visible and consistent.
- Calculated results update when the source or selected input changes.
- No step silently duplicates or removes entities without explanation.

### Evidence to record

Record the main sections you built, the method chosen for each, and one intermediate check that passed.

### Common mistakes

- Building the entire answer in one expression that cannot be inspected.
- Using a row-level average when the business definition requires a weighted result.
- Hard-coding a total, date, category, or rate that should come from the data or a control.

### Progressive hints

- Start with the smallest intermediate table or calculation that can be checked independently.
- When multiple conditions are required, list each condition in words before selecting a function or clause.
- When a result looks plausible, test a deliberately narrow subset to confirm the logic.

## Stage 4: Validate, reconcile, and challenge the result

Prove that the analysis is structurally correct before interpreting it.

### What to do

1. Verify this requirement independently: The test matches the metric and comparison.. Record how you checked it rather than only stating that it passed.
2. Verify this requirement independently: Statistical significance is not described as business importance.. Record how you checked it rather than only stating that it passed.
3. Verify this requirement independently: Failure to reject is not described as proof of equality.. Record how you checked it rather than only stating that it passed.
4. Test at least one boundary condition, such as the first or last date, a missing value, a zero denominator, or an entity with multiple records.
5. Compare the final result with a simpler independent calculation, source subtotal, or manually inspected sample.
6. Investigate differences rather than changing valid logic merely to force agreement.
7. Document every unresolved issue and explain whether it changes the strength of the conclusion.

### Required output

A completed validation record showing what was checked, how it was checked, and any unresolved difference.

### Check your work

- The final row count and distinct-entity count are consistent with the intended grain.
- At least one total, rate, or distribution is reconciled independently.
- Boundary and missing-value behavior are tested rather than assumed.
- Unresolved differences remain visible and are not hidden by rounding or manual edits.

### Evidence to record

Record the validation checks, the comparison method, and the result of the most important boundary test.

### Common mistakes

- Reusing the same calculation as its own validation.
- Checking only the final number and ignoring duplicated or missing rows.
- Forcing a reconciliation to zero without understanding the difference.

## Stage 5: Explain the finding and complete the handoff

Turn a validated result into a concise, responsible analytical deliverable.

### What to do

1. Create the required deliverable: Hypothesis statement and method.. Make its purpose, scope, and source clear to a reviewer.
2. Create the required deliverable: Test result.. Make its purpose, scope, and source clear to a reviewer.
3. Create the required deliverable: Decision-oriented interpretation.. Make its purpose, scope, and source clear to a reviewer.
4. Write a short takeaway that states the result in plain language, explains why it matters, and names a reasonable next action.
5. Add at least one limitation or assumption that changes how confidently the result should be used.
6. Remove unnecessary technical detail from the main takeaway while keeping validation evidence in the submission.
7. Reopen the saved artifact and confirm that its tables, code, visuals, links, and notes are readable.
8. Complete the Studio checklist and save stage evidence before marking the lab complete.

### Required output

A saved, reopenable lab submission with a concise takeaway, supporting evidence, and visible limitations.

### Check your work

- Every requested deliverable is present and clearly labeled.
- The takeaway is supported by the validated result and does not claim causation or certainty without evidence.
- A reviewer can identify the source, method, assumptions, and remaining limitations.
- The artifact path or share link opens successfully.

### Evidence to record

Record the artifact location, final takeaway, requested next action, and most important limitation.

### Common mistakes

- Repeating technical steps instead of explaining the business meaning.
- Making a recommendation that is not supported by the analysis.
- Marking the lab complete before reopening and checking the saved artifact.

## Completion rule

Complete every Studio stage, save a changed submission or linked artifact, record validation evidence, and finish the final handoff review. The main guide will not reveal the finished solution; use the prerequisite lessons and progressively stronger hints when you are stuck.
