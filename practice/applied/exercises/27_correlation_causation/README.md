# Applied Lab 22: Separate correlation from causal evidence

**Category:** Statistics  
**Roadmap week:** 9  
**Estimated working time:** 45 minutes  
**Skills:** correlation, confounding, reverse causality, omitted variables, causal claim, observational evidence

## Scenario

You are the **strategy team**. Two variables move together, and someone has described the relationship as causal. You will separate association from causal evidence and identify plausible confounders.

## Your assignment

Review a strong observed relationship, identify plausible confounders, and rewrite an unsupported causal claim.

Complete the work as a handoff-ready analyst artifact. A reviewer should be able to understand the business rule, reproduce the work, inspect the evidence, and see any limitation without guessing what you did.

## Start here

1. Create the submission or working script before calculating anything.
2. Write the population, sample, variable, and decision question in plain language.
3. Report assumptions and uncertainty alongside every numerical result.

## Provided files

| File | Purpose |
|---|---|
| `convenience_sample.csv` | Intentionally biased sample for comparison. |
| `experiment_users.csv` | Randomized experiment assignments and outcomes. |
| `marketing_regression.csv` | Marketing input and outcome data for regression. |
| `population.csv` | Target population used to assess representativeness. |

Open the **Dataset Folder** from Career Accelerator. Do not change the packaged source files. Put working files, screenshots, and exports in the Applied Labs submissions area.

## What you must produce

- Association summary.
- Confounder and alternative-explanation list.
- Revised claim and stronger study proposal.

## Guided workflow

### 1. Measure and describe the observed association

- Write the business definition before the formula. Identify numerator, denominator, filters, date rule, and behavior when the denominator is zero or data is missing.
- Include both a numerical result and a plain-language interpretation that names the population and avoids certainty beyond the study design.

**Checkpoint:** The result changes correctly under at least two relevant filters and reconciles to a small independent check.

### 2. List plausible confounders and reverse-causality explanations

- Include both a numerical result and a plain-language interpretation that names the population and avoids certainty beyond the study design.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 3. Identify what the current data can and cannot establish

- Include both a numerical result and a plain-language interpretation that names the population and avoids certainty beyond the study design.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 4. Propose an experiment or quasi-experimental design

- Include both a numerical result and a plain-language interpretation that names the population and avoids certainty beyond the study design.
- Save or capture evidence at this point so you can prove the step was completed before moving to the next one.

**Checkpoint:** The step has a visible artifact or recorded evidence and does not introduce an unexplained row-count or total change.

### 5. Rewrite the conclusion using appropriately cautious language

- Include both a numerical result and a plain-language interpretation that names the population and avoids certainty beyond the study design.
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

- [ ] Correlation is not treated as proof of causation.
- [ ] At least one plausible alternative mechanism is considered.
- [ ] The proposed design addresses the main confounder.
- [ ] The work is saved outside the packaged starter files and can be reopened.
- [ ] The submission is driven by data, formulas, queries, code, or documented evidence rather than manually typed final results.
- [ ] A reviewer can reproduce the main result from the supplied source files.
- [ ] The Progress & Evidence notes identify the artifact location, validation performed, and remaining limitations.

## Common mistakes to avoid

- Reporting a p-value or coefficient without the effect size and context.
- Treating a non-significant result as proof that no effect exists.
- Ignoring sampling design or independence assumptions.
- Describing association as causation.

## Submission workflow

1. Select **Create / Open Submission** and work in the created copy, not the packaged starter.
2. Save the main artifact and any screenshots or exports in the Applied Labs submissions folder.
3. Record artifact paths, validation evidence, decisions, and limitations in **Progress & Evidence** and in the submission file when one is provided.
4. Open **Validation** and resolve every required item you can verify.
5. Select **Save Progress**. Mark the lab complete only when the minimum deliverables and definition of done are satisfied.

## Interview-ready reflection

Be prepared to explain the business problem, your chosen grain or metric definition, the most important validation check, one issue you found, and how your final artifact supports a decision.
