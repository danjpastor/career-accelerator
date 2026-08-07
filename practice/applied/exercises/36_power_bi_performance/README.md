# Applied Lab 36: Diagnose one Power BI performance issue

> This is optional extended practice and does not block the roadmap. The lab is designed for about 35 minutes and should not become a project.

## Assignment

Identify one likely Power BI performance bottleneck and propose one focused improvement with a way to measure it.

## Skills you will apply

query folding, model size, cardinality, storage mode, measure versus column, incremental refresh, Performance Analyzer

## Scope guardrails

- Use one tool and the supplied dataset.
- Complete only the listed actions.
- Produce one primary result plus a short takeaway.
- Stop when the validation checks pass; do not expand the lab into a portfolio project.

## Stage 1: Understand the task

Define the small result you need before opening the analysis tool.

### What to do

1. Read the assignment and restate the goal in one sentence: Identify one likely Power BI performance bottleneck and propose one focused improvement with a way to measure it.
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

1. Review the supplied model or scenario and identify the most likely bottleneck.
2. Choose one improvement involving columns, relationships, measures, query folding, or refresh scope.
3. State how you would compare performance before and after the change.

### Required output

One short performance diagnosis and improvement plan.

### Check your work

- The diagnosis names a specific model or refresh issue.
- The proposed change preserves analytical meaning.
- The measurement plan uses a comparable before-and-after check.

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

1. Verify: The diagnosis names a specific model or refresh issue.
2. Verify: The proposed change preserves analytical meaning.
3. Verify: The measurement plan uses a comparable before-and-after check.
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
