# Portfolio Milestone Studios v10.24.0

This release restores the milestone-specific Portfolio Studios on top of the tagged working startup baseline.

## Protected startup baseline

The release does not change:

- `Launch-Career-Accelerator.ps1`
- `Show-Career-Accelerator-Bootstrap.ps1`
- `application/career_app/main.py`
- `application/career_app/services/planner.py`
- `requirements.txt`
- `.venv`

## Milestone workspaces

1. Project Brief Studio
2. Data Source Review Studio
3. Data Intake Studio
4. Relationship Notebook using the existing authoritative notebook
5. Guided Data Dictionary Studio with table navigation, field evidence, specific validation, and generated documentation
6. Cleaning Notebook plus Files & Outputs
7. Reproducible Database Build
8. SQL Analysis
9. EDA Notebook
10. Results Verification
11. Power BI Model Review
12. Power BI Report Review
13. Findings & Recommendations
14. Case Study Publisher

The Visual Guide and Raw Markdown tabs remain available. Studios are contained inside the matching milestone workspace rather than added as global Portfolio Workspace tabs.

## Guided Data Dictionary Studio

The data-dictionary milestone now uses three coordinated panels:

- **Project Tables** records the table description, grain, expected primary key, relationships, notes, and table review status.
- **Fields** presents a compact status list with the observed type, expected type, and most important unresolved issue.
- **Field Review** shows read-only project evidence beside labeled business-rule controls and specific review feedback.

Refreshing observed data never overwrites learner-entered definitions or decisions. Studio progress and the generated Markdown dictionary are saved separately, and milestone completion requires an up-to-date successful validation and document generation.

## Manual work remains manual

The studios organize files, preserve work, run validation, track artifacts, and provide focused guidance. They do not write the learner's SQL, Python, cleaning decisions, Power BI model, report, interpretation, or case study.

Google Sheets remains optional and is loaded only when its controls are used.
