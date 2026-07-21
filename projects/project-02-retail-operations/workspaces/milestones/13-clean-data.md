<!-- DCA MANAGED PORTFOLIO GUIDE START -->
<!-- Guide version: 3 -->

# Clean data

**Project:** Retail Operations Performance Dashboard  
**Stage:** Dataset  
**Estimated focused time:** about 120 minutes  
**Guide updated:** 2026-07-21

## Purpose

Create a reproducible Python cleaning workflow that transforms the raw or staging data into analysis-ready files without altering the original sources.

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

- Open the generated project workspace and select the Career Accelerator kernel.
- Keep raw files unchanged and write outputs to staging, processed, or reports folders.
- Tie every transformation or chart to an approved business question or quality finding.

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

- `notebooks/clean_data.ipynb`
- `src/clean_data.py`
- `data/processed/`

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

1. Profile the raw inputs before transforming them.
2. Define transformations in an ordered cleaning plan.
3. Implement the plan in a reproducible notebook or script.
4. Keep raw inputs immutable and write new processed outputs.
5. Track row-count changes, type conversions, null handling, and deduplication.
6. Validate keys, relationships, and business rules after cleaning.
7. Restart the kernel and run the workflow top-to-bottom.

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

- [ ] The notebook or script runs top-to-bottom without manual hidden state.
- [ ] Outputs are written to documented paths and raw sources remain unchanged.
- [ ] Key totals and derived values reconcile with SQL or source checks.

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

- Relying on notebook execution order instead of a reproducible top-to-bottom run.
- Applying transformations without recording before-and-after checks.
- Creating charts because columns exist rather than because they answer a question.

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

Save the cleaning notebook or script, document every transformation, preserve raw files, produce processed outputs, and verify row counts, types, missing values, duplicates, and key fields after cleaning.

## Demonstrated skills

Completing this milestone may support evidence for:

- Python data cleaning
- Reproducible workflows

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

Use processed outputs for EDA, derived metrics, and downstream tools.

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

**Milestone:** Clean data  
**Started:** 2026-07-21

## Notebook or script plan

1. Import libraries and configure paths relative to the repository.
2. Load raw files without modifying them.
3. Profile shape, types, missing values, duplicate keys, and categories.
4. Apply one documented cleaning rule at a time.
5. Validate after each major transformation.
6. Save processed outputs and a cleaning summary.

## Cleaning register

| Issue | DataFrame/column | Detection | Transformation | Rows affected | Validation |
|---|---|---|---|---:|---|
|  |  |  |  |  |  |

## Required outputs

- [ ] Reproducible notebook or `.py` script
- [ ] Processed files under `data/processed/`
- [ ] Before-and-after profile
- [ ] Exception log
- [ ] No hard-coded personal file paths

<!-- DCA MANAGED PORTFOLIO GUIDE END -->

<!-- DCA LEARNER WORK START -->

## Learner work and decisions

- Add concise notes, decisions, unresolved questions, or links to the real project artifact.
