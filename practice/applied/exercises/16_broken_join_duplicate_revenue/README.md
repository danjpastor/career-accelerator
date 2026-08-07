# Applied Lab 04: Fix a join that duplicates revenue

> This is one of the five required integration labs in the roadmap. The lab is designed for about 30 minutes and should not become a project.

## Assignment

Diagnose one join that inflates revenue, correct it, and prove the corrected total with a simple reconciliation.

## Skills you will apply

join cardinality, grain, duplicate amplification, reconciliation

## Scope guardrails

- Use one tool and the supplied dataset.
- Complete only the listed actions.
- Produce one primary result plus a short takeaway.
- Stop when the validation checks pass; do not expand the lab into a portfolio project.

## Stage 1: Understand the task

Define the small result you need before opening the analysis tool.

### What to do

1. Read the assignment and restate the goal in one sentence: Diagnose one join that inflates revenue, correct it, and prove the corrected total with a simple reconciliation.
2. Identify the source table or file, what one row represents, and the fields needed for the result.
3. Write down one quick check you can use to catch a missing row, duplicate, wrong filter, or incorrect total.

### Required output

A one-sentence goal, a grain statement, and one planned validation check.

### Check your work

- The goal matches the requested output and does not add project-scale work.
- The source grain and required fields are clear.

### Evidence to record

Record the goal, source grain, and planned check in a few lines.

### Common mistakes

- Expanding the lab into a dashboard, pipeline, report package, or portfolio case study.
- Starting with calculations before deciding what one row represents.

## Stage 2: Build the required result

Complete only the two-to-four actions listed in the lab brief.

### What to do

1. Run the broken join and compare its row count and revenue total with the source tables.
2. Identify which join key or table grain causes duplication, then write one corrected query.
3. Reconcile the corrected revenue total to an independent source total and write a two-sentence explanation.

### Required output

One corrected SQL query. A before-and-after reconciliation note.

### Check your work

- The corrected query returns the intended grain.
- The corrected revenue total matches the independent source total.
- The explanation identifies the duplication cause.

### Evidence to record

Record what you created and the result of one intermediate check.

### Common mistakes

- Adding extra analysis that is not required by the brief.
- Hard-coding a final answer instead of deriving it from the supplied data.
- Continuing after a row-count, key, filter, or total check does not make sense.

### Hints

- Complete one listed action at a time and inspect its output before continuing.
- Use the smallest table, chart, query, formula, or script that satisfies the brief.

## Stage 3: Check and explain

Confirm the result is trustworthy and explain the main finding briefly.

### What to do

1. Verify: The corrected query returns the intended grain.
2. Verify: The corrected revenue total matches the independent source total.
3. Verify: The explanation identifies the duplication cause.
4. Save or reopen the required artifact to confirm it is readable and reproducible.
5. Write a two-to-three-sentence takeaway: the result, why it matters, and one limitation or next question.

### Required output

A checked artifact and a short evidence-based takeaway.

### Check your work

- At least one check is independent of the main calculation.
- The takeaway is supported by the result and includes a limitation or next question.
- The saved artifact can be reopened.

### Evidence to record

Record the validation result, artifact location, takeaway, and limitation.

### Common mistakes

- Repeating technical steps instead of explaining the result.
- Claiming causation, certainty, or business impact that the data does not support.

## Completion rule

Complete the three Studio stages, save a changed artifact or linked result, pass the listed checks, and write a two-to-three-sentence takeaway. Extra analysis is not required.
