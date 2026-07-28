# Applied Lab 17: Distinguish customer, logo, and revenue churn

**Category:** Business Analysis  
**Roadmap week:** 8  
**Estimated working time:** 60 minutes  
**Skills:** churn count, churn rate, beginning population, MRR churn, contraction, expansion, net revenue retention

## Scenario

You are the **subscription finance manager**. Customer losses, account losses, and recurring-revenue losses tell different stories. You will calculate each churn view and explain why they differ.

## Your assignment

Calculate several churn measures with correct denominators and explain why they answer different business questions.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Define the entity, event, date, and grain before building the metric.
2. Create intermediate tables that can be reconciled instead of one opaque final calculation.
3. Record the business rule used for inclusion, exclusion, and time windows.

## Provided files

| File | Purpose |
|---|---|
| `forecast_actual.csv` | Planned and actual values by period or department. |
| `subscriptions.csv` | Customer and recurring-revenue history. |
| `user_events.csv` | Ordered user events for funnel and retention analysis. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Churn SQL and metric definitions.
- Customer-versus-revenue churn comparison.
- Actionable interpretation.

## Guided workflow

### 1. Define the starting customer and recurring-revenue population

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Create an intermediate table at the correct grain before the final rate. This makes duplicate events, period rules, and denominators auditable.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 2. Calculate churned customers and customer churn rate

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Define the entity and time logic explicitly. Keep the underlying counts beside the rate so a stakeholder can see the denominator.
- Create an intermediate table at the correct grain before the final rate. This makes duplicate events, period rules, and denominators auditable.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 3. Calculate gross revenue churn and net revenue retention

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Define the entity and time logic explicitly. Keep the underlying counts beside the rate so a stakeholder can see the denominator.
- Create an intermediate table at the correct grain before the final rate. This makes duplicate events, period rules, and denominators auditable.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 4. Separate full cancellations from contraction and expansion

- Create an intermediate table at the correct grain before the final rate. This makes duplicate events, period rules, and denominators auditable.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Segment churn by plan or acquisition channel

- Write the definition in plain language before building the artifact. Include the entity, time period, inclusion rules, and intended decision when they apply.
- Define the entity and time logic explicitly. Keep the underlying counts beside the rate so a stakeholder can see the denominator.
- Create an intermediate table at the correct grain before the final rate. This makes duplicate events, period rules, and denominators auditable.

**Checkpoint:** The artifact is saved in the submissions area and contains enough context for another analyst to continue.

## Evidence to record

- The path to the main submission artifact and any supporting screenshots or exports.
- The grain or unit of analysis used for the final result.
- At least one row-count, total, or boundary check that supports the result.
- One decision or assumption that materially affects the output.
- Any unresolved issue, rejected record, mismatch, or limitation and its likely impact.
- A two- or three-sentence stakeholder takeaway stating what the result means and what should happen next.

## Definition of done

- [ ] Rates use the beginning-period population.
- [ ] Expansion is not subtracted from gross revenue churn.
- [ ] The analysis states the measurement period.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Mixing users, accounts, events, or revenue in the same denominator.
- Using calendar periods where lifecycle periods are required.
- Counting repeated events as unique entities.
- Presenting a percentage without the underlying counts.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
