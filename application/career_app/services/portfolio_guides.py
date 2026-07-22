"""Managed, detailed portfolio milestone guides.

The guide is application-managed while learner work is preserved in a separate
section.  This keeps instructions upgradeable without overwriting project work.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from typing import Iterable

from career_app.data.portfolio_tasks import task_spec

GUIDE_START = "<!-- DCA MANAGED PORTFOLIO GUIDE START -->"
GUIDE_END = "<!-- DCA MANAGED PORTFOLIO GUIDE END -->"
LEARNER_START = "<!-- DCA LEARNER WORK START -->"
GUIDE_VERSION = "3"

EXPECTED_ARTIFACTS = {
    "business_problem": ("documentation/business_problem.md",),
    "stakeholders": ("documentation/stakeholders.md",),
    "kpis": ("documentation/kpi_definitions.md", "documentation/kpis.md"),
    "business_questions": ("documentation/business_questions.md",),
    "synthetic_data_specification": ("documentation/synthetic_data_specification.md",),
    "dataset_source": ("data/raw/", "documentation/data_source_manifest.md"),
    "validate_relationships": (
        "notebooks/validate_relationships.ipynb",
        "reports/relationship_validation/",
    ),
    "data_dictionary": (
        "documentation/data_dictionary.md",
        "documentation/data_dictionary.csv",
    ),
    "clean_validate_data": (
        "data/processed/",
        "sql/cleaning/",
        "notebooks/clean_data.ipynb",
    ),
    "document_assumptions": ("documentation/assumptions.md",),
    "create_schema": ("sql/schema/", "sql/create_schema.sql"),
    "load_data": ("sql/load/", "sql/load_data.sql"),
    "quality_checks": ("sql/validation/", "reports/data_quality/"),
    "analysis_queries": ("sql/analysis/",),
    "documented_queries": ("sql/README.md", "sql/query_index.md"),
    "validate_findings": ("documentation/findings_validation.md",),
    "clean_data": ("notebooks/clean_data.ipynb", "src/clean_data.py", "data/processed/"),
    "eda": ("notebooks/eda.ipynb", "reports/eda/"),
    "detect_anomalies": ("reports/anomalies.csv", "documentation/anomaly_review.md"),
    "derived_metrics": ("documentation/derived_metrics.md",),
    "document_insights": ("documentation/insights.md",),
    "power_bi_model": ("power-bi/",),
    "dax_measures": ("documentation/dax_measures.md", "power-bi/"),
    "dashboards": ("power-bi/", "images/dashboard/"),
    "executive_dashboard": ("power-bi/", "images/dashboard/executive_overview.png"),
    "workload_dashboard": ("power-bi/", "images/dashboard/workload.png"),
    "filters_drillthrough": ("documentation/dashboard_interactions.md", "power-bi/"),
    "executive_summary": ("documentation/executive_summary.md",),
    "screenshots": ("images/",),
    "assumptions_limitations": ("documentation/assumptions_and_limitations.md",),
    "readme": ("README.md",),
    "publish": ("README.md", "CHANGELOG.md"),
}

SKILLS = {
    "business_problem": ("Business problem framing", "Stakeholder alignment"),
    "stakeholders": ("Stakeholder analysis", "Requirements gathering"),
    "kpis": ("KPI definition", "Metric governance"),
    "business_questions": ("Analytical question design", "Scope management"),
    "synthetic_data_specification": ("Data specification", "Data modeling"),
    "dataset_source": ("Data sourcing", "Source documentation"),
    "validate_relationships": (
        "SQL relationship validation",
        "Primary and foreign key testing",
        "Join cardinality",
        "Data-quality automation",
    ),
    "data_dictionary": ("Data documentation", "Metadata management"),
    "clean_validate_data": ("Data cleaning", "Quality assurance"),
    "document_assumptions": ("Analytical judgment", "Risk documentation"),
    "create_schema": ("SQL schema design", "Data types and constraints"),
    "load_data": ("Reproducible data loading", "Row-count reconciliation"),
    "quality_checks": ("SQL data-quality testing", "Exception analysis"),
    "analysis_queries": ("SQL analysis", "Business-question translation"),
    "documented_queries": ("SQL documentation", "Reproducibility"),
    "validate_findings": ("Result validation", "Cross-tool reconciliation"),
    "clean_data": ("Python data cleaning", "Reproducible workflows"),
    "eda": ("Exploratory data analysis", "Data visualization"),
    "detect_anomalies": ("Anomaly detection", "Exception classification"),
    "derived_metrics": ("Feature engineering", "Metric validation"),
    "document_insights": ("Analytical storytelling", "Evidence-based insights"),
    "power_bi_model": ("Power BI data modeling", "Dimensional modeling"),
    "dax_measures": ("DAX", "Filter context"),
    "dashboards": ("Dashboard design", "Business intelligence"),
    "executive_dashboard": ("Executive communication", "Visual hierarchy"),
    "workload_dashboard": ("Operational analytics", "Capacity reporting"),
    "filters_drillthrough": ("Dashboard interaction design", "Usability testing"),
    "executive_summary": ("Executive writing", "Recommendation development"),
    "screenshots": ("Portfolio presentation", "Visual communication"),
    "assumptions_limitations": ("Limitations analysis", "Responsible communication"),
    "readme": ("Technical documentation", "Portfolio communication"),
    "publish": ("Release management", "Quality and privacy review"),
}

FAMILY = {
    "business_problem": "discovery",
    "stakeholders": "discovery",
    "kpis": "discovery",
    "business_questions": "discovery",
    "synthetic_data_specification": "data",
    "dataset_source": "data",
    "validate_relationships": "data",
    "data_dictionary": "data",
    "clean_validate_data": "data",
    "document_assumptions": "discovery",
    "create_schema": "sql",
    "load_data": "sql",
    "quality_checks": "sql",
    "analysis_queries": "sql",
    "documented_queries": "sql",
    "validate_findings": "validation",
    "clean_data": "python",
    "eda": "python",
    "detect_anomalies": "python",
    "derived_metrics": "python",
    "document_insights": "communication",
    "power_bi_model": "powerbi",
    "dax_measures": "powerbi",
    "dashboards": "powerbi",
    "executive_dashboard": "powerbi",
    "workload_dashboard": "powerbi",
    "filters_drillthrough": "powerbi",
    "executive_summary": "communication",
    "screenshots": "delivery",
    "assumptions_limitations": "communication",
    "readme": "delivery",
    "publish": "delivery",
}

FAMILY_PREREQUISITES = {
    "discovery": (
        "Review the project README and the most recent approved project scope.",
        "Confirm which stakeholder decision this milestone supports.",
        "Use only facts already supported by the project brief or source data; mark judgment as an assumption.",
    ),
    "data": (
        "Preserve all files under `data/raw/` unchanged.",
        "Review the approved business questions and KPI definitions.",
        "Confirm table grain, candidate keys, and required relationships before transforming data.",
    ),
    "sql": (
        "Confirm the source or cleaned tables are registered in DuckDB.",
        "Review table grain and relationship-validation findings.",
        "Use explicit columns and preserve a reproducible setup path.",
    ),
    "python": (
        "Open the generated project workspace and select the Career Accelerator kernel.",
        "Keep raw files unchanged and write outputs to staging, processed, or reports folders.",
        "Tie every transformation or chart to an approved business question or quality finding.",
    ),
    "powerbi": (
        "Use the validated analytical layer rather than raw source files where possible.",
        "Reconcile source row counts and headline measures before formatting visuals.",
        "Review the approved KPI definitions and stakeholder questions.",
    ),
    "validation": (
        "Identify the authoritative source for every metric being compared.",
        "Preserve the original outputs so discrepancies can be traced.",
        "Do not resolve differences silently; document the cause and decision.",
    ),
    "communication": (
        "Use only validated outputs and distinguish observation from recommendation.",
        "Quantify claims and identify the comparison period, segment, or baseline.",
        "State limitations that could materially change the decision.",
    ),
    "delivery": (
        "Complete the analytical and validation milestones first.",
        "Remove temporary files, personal information, secrets, and broken links.",
        "Review the project from an employer's perspective rather than the builder's perspective.",
    ),
}

COMMON_VALIDATION = {
    "discovery": (
        "A new reviewer can identify the stakeholder, decision, scope, and success measure without additional explanation.",
        "Every statement is either supported, explicitly assumed, or marked for confirmation.",
        "The scope is narrow enough to be answered by the planned data and project timeline.",
    ),
    "data": (
        "Raw source files remain unchanged.",
        "Row counts, columns, data types, and keys are reconciled before and after any transformation.",
        "Every exception is classified as corrected, intentionally retained, excluded, or unresolved.",
    ),
    "sql": (
        "Queries run from a clean setup in the intended order.",
        "Output grain is stated and row counts or totals are independently checked.",
        "Joins do not silently multiply or discard records.",
    ),
    "python": (
        "The notebook or script runs top-to-bottom without manual hidden state.",
        "Outputs are written to documented paths and raw sources remain unchanged.",
        "Key totals and derived values reconcile with SQL or source checks.",
    ),
    "powerbi": (
        "Model relationships and filter directions are intentional.",
        "Headline measures reconcile with independently calculated SQL totals.",
        "Filters, empty states, and combined selections behave predictably.",
    ),
    "validation": (
        "Every major finding is marked confirmed, revised, unsupported, or pending.",
        "Discrepancies include a documented root cause and chosen source of truth.",
        "Edge cases and alternative explanations are tested.",
    ),
    "communication": (
        "Every finding includes a number, comparison, scope, and business implication.",
        "Recommendations are proportional to the evidence and identify an owner or next step.",
        "Limitations are visible rather than buried.",
    ),
    "delivery": (
        "All links work from the repository root and the public view.",
        "A reviewer can find the business problem, methods, strongest findings, and final artifacts quickly.",
        "No placeholders, temporary files, credentials, or private data remain.",
    ),
}

COMMON_MISTAKES = {
    "discovery": (
        "Writing a broad topic instead of a decision-focused problem.",
        "Listing stakeholders without explaining the decisions they make.",
        "Defining metrics without grain, filters, time windows, or validation rules.",
    ),
    "data": (
        "Editing raw files directly.",
        "Treating repeated foreign keys as duplicate entity records.",
        "Cleaning exceptions before documenting why they are exceptions.",
    ),
    "sql": (
        "Using `SELECT *` in final analysis queries.",
        "Grouping at a different grain than the business question.",
        "Trusting a joined total without comparing pre- and post-join row counts.",
    ),
    "python": (
        "Relying on notebook execution order instead of a reproducible top-to-bottom run.",
        "Applying transformations without recording before-and-after checks.",
        "Creating charts because columns exist rather than because they answer a question.",
    ),
    "powerbi": (
        "Building visuals before validating the model and measures.",
        "Using implicit aggregations for governed KPIs.",
        "Adding slicers or drill paths that do not support a decision.",
    ),
    "validation": (
        "Accepting matching rounded values as proof of agreement.",
        "Changing one output to match another without locating the source of the difference.",
        "Ignoring nulls, exclusions, or filter context during reconciliation.",
    ),
    "communication": (
        "Calling correlation or timing evidence causal.",
        "Writing generic insights without quantified support.",
        "Making recommendations that cannot be traced to a validated finding.",
    ),
    "delivery": (
        "Publishing from the local builder's perspective instead of testing the public experience.",
        "Including screenshots that are unreadable or do not explain the result.",
        "Leaving setup instructions, links, or repository structure outdated.",
    ),
}

TASK_STEPS = {
    "business_problem": (
        "Name the primary stakeholder and the specific decision they need to make.",
        "Describe the current pain point, cost, delay, risk, or missed opportunity.",
        "Write the analytical objective as a question that the project can answer.",
        "Define the in-scope population, process, and time period.",
        "List what is explicitly out of scope.",
        "Choose a measurable sign that the analysis was useful.",
        "Test the statement against the available or planned data.",
    ),
    "stakeholders": (
        "List people who use, influence, provide, or are affected by the analysis.",
        "Record the decision, information need, and likely concern for each stakeholder.",
        "Identify the primary stakeholder and explain why that role has priority.",
        "Separate decision-makers from data owners and subject-matter experts.",
        "Record communication format and level of detail each stakeholder needs.",
        "Identify conflicts between stakeholder goals and how the project will handle them.",
    ),
    "kpis": (
        "Start from each approved stakeholder decision rather than from available columns.",
        "Define each KPI in plain business language.",
        "Write the exact numerator, denominator, aggregation, grain, filters, and time window.",
        "Identify the source table and required fields.",
        "Define null, zero, cancellation, and partial-period handling.",
        "Choose a target, benchmark, or comparison when one is justified.",
        "Write an independent validation rule for the final value.",
        "Flag metrics that cannot yet be calculated and name the missing requirement.",
    ),
    "business_questions": (
        "Translate the business problem into 8–12 answerable questions.",
        "Identify the stakeholder decision supported by each question.",
        "Specify the metric, comparison, segment, period, and expected grain.",
        "Prioritize must-answer questions above exploratory questions.",
        "Map each question to planned SQL, Python, or dashboard output.",
        "Remove questions that are interesting but cannot change a decision.",
        "Review coverage against every approved KPI.",
    ),
    "synthetic_data_specification": (
        "Define one row's meaning for every table.",
        "Specify primary keys, foreign keys, and relationship cardinality.",
        "List each field with type, allowed range, null behavior, and business meaning.",
        "Set realistic row volumes and date coverage.",
        "Define distributions and correlations needed for realistic analysis.",
        "Specify business rules that must always hold.",
        "Add intentional data-quality issues that will exercise cleaning skills.",
        "Verify that the design can answer every approved business question.",
    ),
    "dataset_source": (
        "Confirm whether the source is public, licensed, internal, or synthetic.",
        "Place untouched source files under `data/raw/`.",
        "Record provenance, generation method, retrieval date, and usage constraints.",
        "Create a source manifest with filenames, formats, row counts, and table grains.",
        "Verify required tables and fields against the business questions.",
        "Inspect representative rows without modifying the source.",
        "Record missing fields, coverage gaps, and planned mitigations.",
    ),
    "validate_relationships": (
        "Record the expected grain and candidate key for every table.",
        "Capture baseline row counts.",
        "Test candidate primary keys for nulls and duplicate groups.",
        "Test foreign keys for null and orphaned references.",
        "Compare child row counts before and after every many-to-one join.",
        "Run project-specific cross-table consistency checks.",
        "Document whether each relationship is safe, conditional, or unsafe.",
        "Automate the checks and save machine-readable results.",
    ),
    "data_dictionary": (
        "Inventory every retained field across all source and analytical tables.",
        "Record table grain and identify primary, foreign, derived, and sensitive fields.",
        "Describe business meaning rather than repeating the column name.",
        "Document type, unit, allowed values, range, null meaning, and source.",
        "Record transformations and authoritative source rules.",
        "Check that every KPI and business question can trace to documented fields.",
        "Review ambiguous fields with the project assumptions.",
    ),
    "clean_validate_data": (
        "Profile row counts, nulls, duplicates, categories, ranges, and date logic.",
        "Create an issue log that separates errors from valid exceptions.",
        "Define a reproducible rule for each confirmed issue.",
        "Implement transformations in SQL or Python without editing raw sources.",
        "Write cleaned outputs to staging or processed locations.",
        "Repeat key, relationship, and business-rule checks on cleaned data.",
        "Compare before-and-after row counts and explain every difference.",
        "Preserve unresolved exceptions with an explicit downstream rule.",
    ),
    "document_assumptions": (
        "List every place where the project relies on judgment or incomplete information.",
        "Explain why each assumption is necessary.",
        "Describe how the assumption affects metrics, filters, or recommendations.",
        "Test the assumption where the data allows.",
        "Rate the risk if the assumption is wrong.",
        "Identify the information needed to replace it with a verified fact.",
    ),
    "create_schema": (
        "Translate each approved table grain into a table definition.",
        "Choose types that preserve identifiers, dates, decimals, and categorical values correctly.",
        "Define primary and foreign keys where supported.",
        "Add constraints only when the data and business rule justify them.",
        "Separate raw, staging, and analytical layers where useful.",
        "Run the schema from a clean database.",
        "Inspect the created tables and document any DuckDB limitations.",
    ),
    "load_data": (
        "Create a repeatable load order based on parent-child dependencies.",
        "Use explicit source paths and table names.",
        "Load each required file without modifying the original.",
        "Capture rejected, transformed, or skipped records.",
        "Compare loaded row counts with the source manifest.",
        "Inspect data types and five representative rows per table.",
        "Rerun the load from a clean state to prove reproducibility.",
    ),
    "quality_checks": (
        "Capture baseline table counts and grains.",
        "Test candidate keys, required fields, accepted categories, ranges, and dates.",
        "Test foreign keys and join cardinality.",
        "Add project-specific cross-field and cross-table rules.",
        "Summarize failures by rule and affected record count.",
        "Classify each failure and identify its downstream risk.",
        "Save queries and results so they can be rerun after changes.",
    ),
    "analysis_queries": (
        "Create a query index tied to the approved business questions.",
        "State the required output grain before writing each query.",
        "Build and validate joins before adding calculations.",
        "Use readable CTEs or staged views for complex logic.",
        "Calculate governed KPIs from their approved definitions.",
        "Validate totals, filters, null behavior, and edge cases.",
        "Save final outputs or result checkpoints with interpretation notes.",
    ),
    "documented_queries": (
        "Organize SQL into setup, validation, transformation, and analysis sections.",
        "Add a query index mapping files or sections to business questions.",
        "Document inputs, outputs, grain, assumptions, and expected checks.",
        "Remove abandoned experiments from the final execution path.",
        "Run every file from a clean setup in the documented order.",
        "Confirm another analyst can navigate and reproduce the results.",
    ),
    "validate_findings": (
        "List every finding intended for the dashboard or executive summary.",
        "Recalculate each headline metric independently.",
        "Compare SQL, Python, and Power BI results under identical filters.",
        "Test alternative explanations, segments, and time windows.",
        "Review nulls, exclusions, and denominator definitions.",
        "Classify each finding as confirmed, revised, unsupported, or pending.",
        "Document discrepancies and the chosen source of truth.",
    ),
    "clean_data": (
        "Profile the raw inputs before transforming them.",
        "Define transformations in an ordered cleaning plan.",
        "Implement the plan in a reproducible notebook or script.",
        "Keep raw inputs immutable and write new processed outputs.",
        "Track row-count changes, type conversions, null handling, and deduplication.",
        "Validate keys, relationships, and business rules after cleaning.",
        "Restart the kernel and run the workflow top-to-bottom.",
    ),
    "eda": (
        "Begin with table grain, coverage, and descriptive summaries.",
        "Examine distributions for measures and frequencies for categories.",
        "Compare meaningful segments and time periods.",
        "Investigate relationships relevant to approved business questions.",
        "Identify anomalies and quality concerns without silently correcting them.",
        "Create purposeful, labeled visuals with written interpretations.",
        "Maintain a findings log that separates observation from hypothesis.",
    ),
    "detect_anomalies": (
        "Define what unusual means for each relevant metric or process.",
        "Use business rules, distribution checks, or comparative baselines.",
        "Produce a review table with identifiers and supporting context.",
        "Inspect representative records from each anomaly pattern.",
        "Classify patterns as data error, valid exception, or meaningful signal.",
        "Document treatment and downstream impact.",
        "Retain reproducible rules rather than manual record lists.",
    ),
    "derived_metrics": (
        "Trace each derived field to an approved KPI or business question.",
        "Define formula, grain, type, units, and source fields.",
        "Specify edge cases, null handling, and zero-denominator behavior.",
        "Implement calculations in the authoritative analytical layer.",
        "Test representative records manually.",
        "Reconcile aggregate results with source values.",
        "Document the metric so SQL, Python, and Power BI use the same rule.",
    ),
    "document_insights": (
        "Review only validated tables, charts, and metrics.",
        "Prioritize findings by decision impact rather than surprise.",
        "Quantify each finding with comparison, segment, and period.",
        "Explain business relevance without overstating causality.",
        "State the limitation or uncertainty attached to each finding.",
        "Recommend a follow-up question or action where justified.",
        "Link each insight to a reproducible supporting artifact.",
    ),
    "power_bi_model": (
        "Classify tables as facts, dimensions, bridges, or supporting tables.",
        "Confirm table grain and keys before creating relationships.",
        "Build one-to-many relationships with intentional filter direction.",
        "Create and mark a dedicated date table.",
        "Hide technical keys and organize user-facing fields.",
        "Check ambiguous paths and unexplained many-to-many relationships.",
        "Reconcile row counts and baseline metrics with SQL.",
    ),
    "dax_measures": (
        "Create explicit measures for every governed KPI.",
        "Organize measures in a dedicated table or display folders.",
        "Implement approved filters, denominator rules, and time windows.",
        "Test total rows, segment filters, combined filters, and empty states.",
        "Apply consistent names and formatting.",
        "Reconcile every headline measure with SQL.",
        "Document formula purpose and known limitations.",
    ),
    "dashboards": (
        "Map each report page to stakeholder questions and decisions.",
        "Define the visual hierarchy before formatting.",
        "Use the simplest visual that communicates each comparison.",
        "Add governed KPI definitions and useful context.",
        "Implement only decision-useful interactions.",
        "Test filters, cross-highlighting, empty states, and accessibility.",
        "Reconcile all displayed values and capture review screenshots.",
    ),
    "executive_dashboard": (
        "Select the small set of headline KPIs an executive needs first.",
        "Add trend, variance, target, or prior-period context.",
        "Show the most important drivers, risks, or exceptions.",
        "Use restrained filters and a clear reading order.",
        "Add a concise takeaway or decision prompt.",
        "Validate every value against SQL.",
        "Test the page at presentation and screenshot sizes.",
    ),
    "workload_dashboard": (
        "Define capacity, assigned work, actual effort, and schedule risk consistently.",
        "Choose the operational grain and reporting period.",
        "Build measures for workload, utilization, backlog, and risk.",
        "Show useful team, project, status, and time breakdowns.",
        "Provide drill paths to the records requiring action.",
        "Test capacity edge cases and missing assignments.",
        "Reconcile totals with SQL and document interpretation.",
    ),
    "filters_drillthrough": (
        "List the decisions each filter or drill path supports.",
        "Remove interactions that add exploration but not decision value.",
        "Configure clear default and reset states.",
        "Test single, combined, contradictory, and empty selections.",
        "Verify cross-filtering and drill-through context.",
        "Add titles or context that reflect active filters.",
        "Document the final interaction behavior.",
    ),
    "executive_summary": (
        "State the business problem and stakeholder decision.",
        "Summarize the data and analytical approach without implementation detail.",
        "Present three to five validated quantified findings.",
        "Prioritize recommendations by impact and feasibility.",
        "State assumptions, limitations, and unresolved risks.",
        "Link to the dashboard and supporting artifacts.",
        "Edit to one page of decision-focused content.",
    ),
    "screenshots": (
        "Select only views that help a reviewer understand the project quickly.",
        "Set readable dimensions, filters, and zoom.",
        "Remove irrelevant application chrome and private information.",
        "Capture consistent images with descriptive filenames.",
        "Add captions or alt text that explain what each image proves.",
        "Reference the correct relative paths from the README.",
        "Test readability in the rendered public repository.",
    ),
    "assumptions_limitations": (
        "Collect assumptions from discovery, cleaning, analysis, and reporting.",
        "Separate data limitations from methodological limitations.",
        "Explain the likely direction and magnitude of impact.",
        "Identify findings most sensitive to each limitation.",
        "State what additional data or analysis would reduce uncertainty.",
        "Ensure recommendations remain credible under the documented limits.",
    ),
    "readme": (
        "Write a one-sentence value proposition for the project.",
        "Explain the business problem, stakeholder, questions, and KPIs.",
        "Summarize data, tools, cleaning, validation, and analytical approach.",
        "Present quantified findings and recommendations.",
        "Add readable visuals and links to final artifacts.",
        "Document repository structure and navigation or setup.",
        "Disclose synthetic data, assumptions, and limitations.",
        "Remove placeholders and test every link from the repository root.",
    ),
    "publish": (
        "Review the repository for secrets, personal information, and temporary files.",
        "Confirm reproducibility, artifact paths, and public links.",
        "Test the README and images in the public repository view.",
        "Review filenames, commit history, description, and repository topics.",
        "Create a clear final commit and version tag or release.",
        "Open the public project in a clean browser session.",
        "Record any intentionally excluded data or setup requirements.",
    ),
}

NEXT_HANDOFF = {
    "business_problem": "Use the approved problem to identify stakeholders, KPIs, and business questions.",
    "stakeholders": "Use stakeholder decisions to prioritize KPIs and output formats.",
    "kpis": "Use governed KPI definitions in business questions, SQL, Python, and Power BI.",
    "business_questions": "Use the prioritized questions to verify the dataset design and plan analysis outputs.",
    "synthetic_data_specification": "Use the approved specification to generate the raw dataset without changing the business rules.",
    "dataset_source": "Use the immutable raw sources for relationship validation and the data dictionary.",
    "validate_relationships": "Carry documented issues into cleaning; rerun the same tests against the cleaned layer.",
    "data_dictionary": "Use field definitions during cleaning, schema design, analysis, and dashboard modeling.",
    "clean_validate_data": "Use validated processed data for schema loading, analysis, and dashboards.",
    "document_assumptions": "Carry material assumptions into metric definitions, findings, and final limitations.",
    "create_schema": "Load data in dependency order and reconcile source-to-table counts.",
    "load_data": "Run the complete SQL quality suite before analysis.",
    "quality_checks": "Resolve or document exceptions before answering business questions.",
    "analysis_queries": "Package final queries and validate findings across tools.",
    "documented_queries": "Use the clean query set as the SQL source of truth for validation and reporting.",
    "validate_findings": "Only confirmed findings should enter dashboards and executive communication.",
    "clean_data": "Use processed outputs for EDA, derived metrics, and downstream tools.",
    "eda": "Promote validated patterns into anomaly rules, derived metrics, or candidate insights.",
    "detect_anomalies": "Apply the documented treatment before final metrics and insights.",
    "derived_metrics": "Use the governed definitions consistently in SQL, Python, and Power BI.",
    "document_insights": "Use prioritized validated insights to design dashboard hierarchy and recommendations.",
    "power_bi_model": "Build and validate explicit DAX measures on the approved model.",
    "dax_measures": "Use reconciled measures to construct stakeholder-focused report pages.",
    "dashboards": "Refine the executive and operational pages, then validate all findings.",
    "executive_dashboard": "Use the overview in screenshots, the README, and executive communication.",
    "workload_dashboard": "Connect operational risks to recommendations and supporting detail.",
    "filters_drillthrough": "Complete usability testing before screenshots and publication.",
    "executive_summary": "Use the summary as the decision-focused narrative in the README and portfolio.",
    "screenshots": "Use optimized images in the README and portfolio presentation.",
    "assumptions_limitations": "Include material limitations beside findings and recommendations.",
    "readme": "Run the publication checklist and test the public repository experience.",
    "publish": "Use the release as the stable employer-facing version of the project.",
}


def _bullet(values: Iterable[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def _numbered(values: Iterable[str]) -> str:
    return "\n".join(f"{index}. {value}" for index, value in enumerate(values, 1))


def _key_for(label: str, project_id: int) -> str:
    canonical = globals().get(
        "TRUE_MILESTONE_LABEL_KEYS",
        {},
    ).get(str(label).strip().casefold())
    if canonical:
        return canonical
    spec = task_spec(label, project_id)
    if spec is None:
        return re.sub(
            r"[^a-z0-9]+",
            "_",
            str(label).casefold(),
        ).strip("_")
    return spec.key


def _worksheet_body(starter_text: str) -> str:
    text = str(starter_text or "").strip()
    if not text:
        return "- [ ] Record your work, decisions, and validation results here."
    lines = text.splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def guide_markdown(
    *,
    label: str,
    project_id: int,
    project_name: str,
    stage: str,
    description: str,
    definition_of_done: str,
    estimated_minutes: int,
    starter_text: str = "",
) -> str:
    canonical_key = TRUE_MILESTONE_LABEL_KEYS.get(str(label).strip().casefold())
    spec = task_spec(label, project_id)
    key = canonical_key or (spec.key if spec is not None else _key_for(label, project_id))
    family = FAMILY.get(key, "delivery")
    artifacts = EXPECTED_ARTIFACTS.get(key, ("documentation/",))
    skills = SKILLS.get(key, (stage, "Portfolio project execution"))
    workflow = TASK_STEPS.get(
        key,
        (
            "Review the task purpose and expected output.",
            "Inspect the relevant source data and prior project decisions.",
            "Complete the work in the correct project artifact.",
            "Validate the result independently.",
            "Record decisions, exceptions, and the next handoff.",
        ),
    )
    prerequisites = FAMILY_PREREQUISITES[family]
    validation = COMMON_VALIDATION[family]
    mistakes = COMMON_MISTAKES[family]
    handoff = NEXT_HANDOFF.get(
        key,
        "Use the validated output as the input to the next incomplete project milestone.",
    )
    worksheet = _worksheet_body(starter_text)

    managed = f"""
{GUIDE_START}
<!-- Guide version: {GUIDE_VERSION} -->

# {label}

**Project:** {project_name}  
**Stage:** {stage}  
**Estimated focused time:** about {int(estimated_minutes or 45)} minutes  
**Guide updated:** {date.today().isoformat()}

## Purpose

{description or "Complete this portfolio milestone and produce a reviewable project artifact."}

This milestone is not a documentation exercise inside the application. Complete the real work in the project files listed below. Use this guide to understand the workflow, validation standard, and handoff.

## Business context

Explain how this task helps answer the approved business problem or reduces risk in the final analysis. Before beginning, identify:

- The stakeholder decision supported by this work.
- The business question, KPI, or delivery requirement it affects.
- The consequence of completing it incorrectly or incompletely.
- The authoritative project artifact where the result will live.

## Prerequisites

{_bullet(prerequisites)}

## Inputs to review

- The project README and approved discovery artifacts.
- The most recent outputs from prerequisite milestones.
- The relevant raw, processed, SQL, notebook, Power BI, or documentation files.
- The project source configuration at `config/project_sources.yaml` when data tables are involved.
- Existing assumptions, exceptions, and validation findings that affect this task.

## Expected output

Create or update the appropriate project artifact. Expected locations include:

{_bullet(f"`{path}`" for path in artifacts)}

The finished output must be understandable outside Career Accelerator. Do not place the substantive project result only in an application note field.

## Detailed workflow

{_numbered(workflow)}

## Questions to answer while working

- What is the exact grain, scope, audience, or decision represented by this output?
- Which prior project definitions must remain consistent?
- What evidence would prove the result is correct?
- Which exceptions require a business decision rather than an automatic correction?
- What could mislead a reviewer if it is not explained?
- Which downstream milestone will consume this output?

## Validation checklist

{_bullet(f"[ ] {item}" for item in validation)}

Also confirm:

- [ ] The expected artifact exists at a clear repository path.
- [ ] The work can be reproduced or reviewed without hidden application state.
- [ ] Material assumptions and unresolved issues are visible.
- [ ] Results are not copied from an example or supplied as an unmodified starter.
- [ ] The artifact is ready to be linked from Demonstrated Evidence when appropriate.

## Common mistakes to avoid

{_bullet(mistakes)}

## Interpretation and decision prompts

When the technical work is complete, record:

1. The strongest result or decision produced by this milestone.
2. The validation evidence supporting that result.
3. Any exceptions, uncertainty, or limitations.
4. The downstream impact on metrics, analysis, dashboards, or recommendations.
5. The specific next action required.

## Definition of done

{definition_of_done or "The real project artifact is complete, validated, saved, and ready for the next milestone."}

## Demonstrated skills

Completing this milestone may support evidence for:

{_bullet(skills)}

Evidence should point to the real artifact and describe what the work proves. A checked milestone without a substantive artifact is progress, not demonstrated evidence.

## Next-step handoff

{handoff}

## Task-specific worksheet

The worksheet below is a planning aid. Complete the substantive work in the project artifact, then use this area for concise decisions, checks, and handoff notes.

{worksheet}

{GUIDE_END}
""".strip()

    return (
        managed
        + "\n\n"
        + LEARNER_START
        + "\n\n"
        + "## Learner work and decisions\n\n"
        + "- Add concise notes, decisions, unresolved questions, or links to the real project artifact.\n"
    )


def upgrade_guide(existing: str, canonical: str) -> str:
    existing = str(existing or "")
    canonical = str(canonical or "").rstrip() + "\n"

    if GUIDE_START in existing and GUIDE_END in existing:
        before, remainder = existing.split(GUIDE_START, 1)
        _, after = remainder.split(GUIDE_END, 1)
        managed = canonical.split(GUIDE_START, 1)[1].split(GUIDE_END, 1)[0]
        return (
            before.rstrip()
            + ("\n\n" if before.strip() else "")
            + GUIDE_START
            + managed
            + GUIDE_END
            + after
        ).rstrip() + "\n"

    if not existing.strip():
        return canonical

    # Preserve existing work in full.  Older documents mixed instructions and
    # learner notes, so the safe migration is to retain the original below the
    # new managed guide rather than attempting to guess which lines are answers.
    return (
        canonical.rstrip()
        + "\n\n"
        + "## Preserved content from the previous guide\n\n"
        + "> The previous document is retained below so no learner work is lost. "
          "Move only useful decisions into the Learner work section when convenient.\n\n"
        + existing.strip()
        + "\n"
    )


def expected_artifacts(label: str, project_id: int) -> tuple[str, ...]:
    return EXPECTED_ARTIFACTS.get(_key_for(label, project_id), ("documentation/",))


def skills_for_task(label: str, project_id: int) -> tuple[str, ...]:
    return SKILLS.get(_key_for(label, project_id), ("Portfolio project execution",))


def audit_guide(content: str) -> list[str]:
    required = (
        "## Purpose",
        "## Business context",
        "## Prerequisites",
        "## Inputs to review",
        "## Expected output",
        "## Detailed workflow",
        "## Validation checklist",
        "## Common mistakes to avoid",
        "## Definition of done",
        "## Demonstrated skills",
        "## Next-step handoff",
    )
    issues = [f"Missing section: {heading}" for heading in required if heading not in content]
    if GUIDE_START not in content or GUIDE_END not in content:
        issues.append("Missing managed-guide markers")
    if len(content.split()) < 350:
        issues.append("Guide is too brief for a substantial portfolio milestone")
    return issues

# BEGIN TRUE PORTFOLIO MILESTONE GUIDE OVERRIDES V10.21.0
TRUE_MILESTONE_LABEL_KEYS = {
    "review and approve project brief": "review_and_approve_project_brief",
    "approve data source and specification": "approve_data_source_and_specification",
    "create or acquire raw dataset": "create_or_acquire_raw_dataset",
    "validate relationships": "validate_relationships",
    "review and finalize data dictionary": "review_and_finalize_data_dictionary",
    "clean and validate analytical data": "clean_and_validate_analytical_data",
    "build reproducible analytical database": "build_reproducible_analytical_database",
    "complete sql analysis": "complete_sql_analysis",
    "complete exploratory analysis": "complete_exploratory_analysis",
    "validate findings across tools": "validate_findings_across_tools",
    "build and validate power bi semantic model": "build_and_validate_power_bi_semantic_model",
    "build and test power bi report": "build_and_test_power_bi_report",
    "write executive summary and recommendations": "write_executive_summary_and_recommendations",
    "publish reproducible portfolio case study": "publish_reproducible_portfolio_case_study",
}
EXPECTED_ARTIFACTS.update(
    {
        "review_and_approve_project_brief": (
            "README.md",
            "PROJECT_CHARTER.md",
            "documentation/project_charter.md",
        ),
        "approve_data_source_and_specification": (
            "config/project_sources.yaml",
            "documentation/synthetic_data_specification.md",
            "documentation/data_source_manifest.md",
        ),
        "create_or_acquire_raw_dataset": (
            "data/raw/",
            "config/project_sources.yaml",
        ),
        "review_and_finalize_data_dictionary": (
            "DATA_DICTIONARY.md",
            "documentation/data_dictionary.md",
            "documentation/data_dictionary.csv",
        ),
        "clean_and_validate_analytical_data": (
            "data/processed/",
            "notebooks/clean_data.ipynb",
            "sql/cleaning/",
        ),
        "build_reproducible_analytical_database": (
            "sql/schema/",
            "sql/load/",
            "sql/create_schema.sql",
            "sql/load_data.sql",
        ),
        "complete_sql_analysis": (
            "sql/analysis/",
            "sql/query_index.md",
            "sql/README.md",
        ),
        "complete_exploratory_analysis": (
            "notebooks/eda.ipynb",
            "reports/eda/",
        ),
        "validate_findings_across_tools": (
            "documentation/findings_validation.md",
            "reports/findings_validation/",
        ),
        "build_and_validate_power_bi_semantic_model": (
            "power-bi/",
            "documentation/dax_measures.md",
        ),
        "build_and_test_power_bi_report": (
            "power-bi/",
            "images/dashboard/",
        ),
        "write_executive_summary_and_recommendations": (
            "documentation/executive_summary.md",
            "EXECUTIVE_SUMMARY.md",
        ),
        "publish_reproducible_portfolio_case_study": (
            "README.md",
            "images/",
            "CHANGELOG.md",
        ),
    }
)

SKILLS.update(
    {
        "review_and_approve_project_brief": (
            "Business problem framing",
            "Stakeholder analysis",
            "KPI governance",
            "Analytical question design",
        ),
        "approve_data_source_and_specification": (
            "Data sourcing",
            "Data specification",
            "Provenance review",
        ),
        "create_or_acquire_raw_dataset": (
            "Source-data management",
            "Reproducibility",
        ),
        "review_and_finalize_data_dictionary": (
            "Metadata management",
            "Schema documentation",
            "Data governance",
        ),
        "clean_and_validate_analytical_data": (
            "Data cleaning",
            "Quality assurance",
            "Exception handling",
        ),
        "build_reproducible_analytical_database": (
            "SQL schema design",
            "Reproducible loading",
            "Row-count reconciliation",
        ),
        "complete_sql_analysis": (
            "SQL analysis",
            "KPI calculation",
            "Query validation",
        ),
        "complete_exploratory_analysis": (
            "Exploratory data analysis",
            "Python",
            "Analytical visualization",
        ),
        "validate_findings_across_tools": (
            "Cross-tool reconciliation",
            "Result validation",
        ),
        "build_and_validate_power_bi_semantic_model": (
            "Power BI data modeling",
            "DAX",
            "Metric governance",
        ),
        "build_and_test_power_bi_report": (
            "Dashboard design",
            "Interaction testing",
            "Business intelligence",
        ),
        "write_executive_summary_and_recommendations": (
            "Executive communication",
            "Recommendation development",
        ),
        "publish_reproducible_portfolio_case_study": (
            "Portfolio presentation",
            "Technical documentation",
            "Release management",
        ),
    }
)

FAMILY.update(
    {
        "review_and_approve_project_brief": "discovery",
        "approve_data_source_and_specification": "data",
        "create_or_acquire_raw_dataset": "data",
        "review_and_finalize_data_dictionary": "data",
        "clean_and_validate_analytical_data": "data",
        "build_reproducible_analytical_database": "sql",
        "complete_sql_analysis": "sql",
        "complete_exploratory_analysis": "python",
        "validate_findings_across_tools": "validation",
        "build_and_validate_power_bi_semantic_model": "powerbi",
        "build_and_test_power_bi_report": "powerbi",
        "write_executive_summary_and_recommendations": "communication",
        "publish_reproducible_portfolio_case_study": "delivery",
    }
)

TASK_STEPS.update(
    {
        "review_and_approve_project_brief": (
            "Open the rendered Overview and project charter.",
            "Confirm the business problem names a stakeholder decision rather than only a topic.",
            "Confirm the primary and supporting stakeholders and what each needs from the analysis.",
            "Review KPI definitions for grain, filters, time windows, null handling, and validation rules.",
            "Review every business question for scope, decision value, and data availability.",
            "Resolve contradictions between the Overview, charter, source specification, and milestone catalog.",
            "Record approval in the project brief instead of duplicating it in an application note.",
        ),
        "approve_data_source_and_specification": (
            "Confirm whether the data is public, licensed, internal, or synthetic.",
            "Review provenance, generation rules, retrieval date, and permitted use.",
            "Confirm table grains, required fields, date coverage, row volumes, keys, and relationships.",
            "Map every business question and KPI to available fields.",
            "Identify coverage gaps and revise either the scope or specification.",
            "Approve the source manifest or synthetic-data specification.",
        ),
        "create_or_acquire_raw_dataset": (
            "Place untouched source files under the raw-data folder.",
            "Confirm every configured source path exists.",
            "Record filenames, formats, row counts, grains, and provenance.",
            "Inspect representative records without editing the source.",
            "Confirm all required tables and fields are present.",
            "Protect raw files from downstream transformation.",
        ),
        "review_and_finalize_data_dictionary": (
            "Open the existing generated data dictionary; do not create a second dictionary.",
            "Compare its table list with Data Explorer and project_sources.yaml.",
            "Compare every documented column with DuckDB's detected schema.",
            "Add missing business definitions, key roles, null meanings, units, allowed values, and authoritative-source notes.",
            "Update descriptions affected by relationship validation or cleaning decisions.",
            "Remove obsolete fields and document derived fields in their authoritative analytical layer.",
            "Confirm all KPIs and business questions trace to documented fields.",
        ),
        "clean_and_validate_analytical_data": (
            "Create an issue log from profiling and relationship-validation findings.",
            "Separate genuine errors from valid business exceptions.",
            "Define a reproducible treatment for each confirmed issue.",
            "Implement transformations without editing raw sources.",
            "Write processed outputs to documented paths.",
            "Re-run row-count, key, relationship, range, category, and business-rule checks.",
            "Explain every before-and-after difference and preserve unresolved exceptions.",
        ),
        "build_reproducible_analytical_database": (
            "Define analytical tables or views and their grain.",
            "Choose types and constraints that preserve identifiers, dates, and measures correctly.",
            "Create a repeatable build and load order based on dependencies.",
            "Load every required table from documented source or processed paths.",
            "Reconcile source and loaded row counts.",
            "Run post-load key, relationship, null, range, and business-rule checks.",
            "Rebuild from a clean database to prove reproducibility.",
        ),
        "complete_sql_analysis": (
            "Create a query plan mapped to approved business questions.",
            "State the intended output grain before each analysis.",
            "Validate joins before adding calculations.",
            "Implement governed KPI definitions with explicit filters and denominator rules.",
            "Test totals, nulls, edge cases, segments, and time periods.",
            "Organize final SQL into a reproducible execution order.",
            "Save result checkpoints and concise interpretations.",
        ),
        "complete_exploratory_analysis": (
            "Run the notebook or script from a clean environment.",
            "Describe coverage, distributions, categories, and important segments.",
            "Explore relationships tied directly to approved business questions.",
            "Investigate anomalies without silently treating them as errors.",
            "Create purposeful labeled visuals and written interpretations.",
            "Separate observations, hypotheses, and validated findings.",
            "Save reproducible outputs to documented locations.",
        ),
        "validate_findings_across_tools": (
            "List every finding intended for the report or executive summary.",
            "Recalculate each headline metric independently.",
            "Align filters, periods, null handling, and denominator rules across tools.",
            "Compare values at total and segment levels.",
            "Investigate discrepancies to their source rather than forcing agreement.",
            "Classify each finding as confirmed, revised, unsupported, or pending.",
            "Record the authoritative source and approved value.",
        ),
        "build_and_validate_power_bi_semantic_model": (
            "Classify tables as facts, dimensions, bridges, or support tables.",
            "Confirm grains and keys before creating relationships.",
            "Build intentional one-to-many relationships and filter directions.",
            "Create and mark the date table.",
            "Create explicit governed DAX measures.",
            "Test totals, filters, combined selections, and empty states.",
            "Reconcile headline measures with SQL.",
        ),
        "build_and_test_power_bi_report": (
            "Map report pages to stakeholder decisions and approved questions.",
            "Build the executive overview and required operational detail pages.",
            "Use the simplest visual that communicates each comparison.",
            "Implement only decision-useful filters, cross-highlighting, and drill paths.",
            "Test default, combined, contradictory, and empty selections.",
            "Review accessibility, labels, hierarchy, and presentation sizing.",
            "Reconcile every displayed value and capture final review screenshots.",
        ),
        "write_executive_summary_and_recommendations": (
            "State the business problem and stakeholder decision.",
            "Summarize the data and analytical approach without unnecessary implementation detail.",
            "Present three to five validated quantified findings.",
            "Explain the business implication of each finding.",
            "Prioritize recommendations by impact, feasibility, owner, and next action.",
            "State assumptions, limitations, and unresolved risks beside affected claims.",
            "Link the narrative to supporting artifacts.",
        ),
        "publish_reproducible_portfolio_case_study": (
            "Write a concise project value proposition.",
            "Present the problem, stakeholders, KPIs, questions, methods, findings, and recommendations.",
            "Add readable visuals and links to final artifacts.",
            "Document repository structure and reproducibility guidance.",
            "Disclose synthetic data, assumptions, and limitations.",
            "Remove placeholders, temporary files, private information, and broken links.",
            "Test the public repository in a clean browser session and create the final release.",
        ),
    }
)

NEXT_HANDOFF.update(
    {
        "review_and_approve_project_brief": "Use the approved brief to finalize the data source and specification.",
        "approve_data_source_and_specification": "Create or acquire the immutable raw dataset.",
        "create_or_acquire_raw_dataset": "Validate the table model and relationships before transformation.",
        "review_and_finalize_data_dictionary": "Use approved field definitions during cleaning, schema design, analysis, and reporting.",
        "clean_and_validate_analytical_data": "Build the reproducible analytical database from the processed layer.",
        "build_reproducible_analytical_database": "Use the governed analytical layer to complete SQL analysis.",
        "complete_sql_analysis": "Use SQL results to guide EDA and cross-tool validation.",
        "complete_exploratory_analysis": "Promote only supported patterns into findings validation.",
        "validate_findings_across_tools": "Use confirmed findings and governed metrics in Power BI.",
        "build_and_validate_power_bi_semantic_model": "Build and test the report on the validated model.",
        "build_and_test_power_bi_report": "Use the final report in the executive summary.",
        "write_executive_summary_and_recommendations": "Package the project into the public case study.",
        "publish_reproducible_portfolio_case_study": "Treat the release as the stable employer-facing version.",
    }
)
# END TRUE PORTFOLIO MILESTONE GUIDE OVERRIDES V10.21.0
