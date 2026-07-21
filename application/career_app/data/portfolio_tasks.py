"""Guided portfolio milestone definitions.

Portfolio checklists remain concise, while this module supplies the detailed
brief, completion standard, time estimate, and starter document for each
milestone.  The definitions are shared by all projects unless a project-specific
override is declared.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioTaskSpec:
    key: str
    description: str
    definition_of_done: str
    starter_path: str
    estimated_minutes: int = 45


def _spec(
    key: str,
    description: str,
    done: str,
    starter: str,
    minutes: int = 45,
) -> PortfolioTaskSpec:
    return PortfolioTaskSpec(
        key=key,
        description=description,
        definition_of_done=done,
        starter_path=f"portfolio_starters/{starter}",
        estimated_minutes=minutes,
    )


BUSINESS_PROBLEM = _spec(
    "business_problem",
    "Define the decision this project should support, who needs the answer, and why the problem matters. Keep the scope narrow enough to solve with the planned data.",
    "Save a one-paragraph problem statement that names the stakeholder, decision, current pain point, analytical objective, in-scope period, and a measurable sign of success.",
    "business_problem.md",
    40,
)

STAKEHOLDERS = _spec(
    "stakeholders",
    "Identify the people who will use, influence, or be affected by the analysis so the project can prioritize the right questions and outputs.",
    "Document at least three stakeholders, the decision each one makes, the information each needs, their likely concerns, and which stakeholder is primary.",
    "stakeholders.md",
    35,
)

KPIS = _spec(
    "kpis",
    "Define the small set of metrics that will show whether the business problem is improving. Each KPI needs an exact formula and interpretation.",
    "Document each KPI with its business definition, formula, grain, filters, time window, data source, target or benchmark, and validation rule; flag any KPI that cannot yet be calculated.",
    "kpis.md",
    60,
)

BUSINESS_QUESTIONS = _spec(
    "business_questions",
    "Turn the business problem into answerable analytical questions that guide the SQL, Python, and dashboard work instead of exploring the data without a purpose.",
    "Save 8–12 prioritized questions. Each question identifies the stakeholder decision it supports, the metric or comparison required, the expected grain, and the planned output.",
    "business_questions.md",
    50,
)

SYNTHETIC_SPEC = _spec(
    "synthetic_data_specification",
    "Specify the tables, fields, relationships, date range, row volumes, business rules, and intentional quality issues needed before generating synthetic data.",
    "Complete the specification with table grains, primary and foreign keys, column definitions, realistic distributions, relationship rules, row counts, date range, and intentional errors; review it against every business question.",
    "synthetic_data_specification.md",
    90,
)

DATASET_SOURCE = _spec(
    "dataset_source",
    "Obtain or create a dataset that can answer the project questions while preserving a clearly documented raw-data source.",
    "Place untouched source files in data/raw, record where they came from or how they were generated, confirm licensing or synthetic status, list row counts, and verify that the required tables and fields exist.",
    "dataset_source.md",
    75,
)

VALIDATE_RELATIONSHIPS = _spec(
    "validate_relationships",
    "Confirm that the keys connecting the tables behave as intended. This means checking that primary keys are unique, foreign keys point to real parent rows, and joins do not unexpectedly lose or multiply records.",
    "Complete the relationship matrix; run uniqueness, orphan-key, and join-cardinality checks for every planned relationship; investigate exceptions; save the validation SQL or notebook; and record whether each relationship is safe to use.",
    "validate_relationships.md",
    75,
)

DATA_DICTIONARY = _spec(
    "data_dictionary",
    "Create a field-level reference that explains what each column means and how it should be interpreted during cleaning, analysis, and reporting.",
    "Document every retained field with table, data type, business meaning, grain, allowed values or range, missing-value meaning, source, transformation notes, and whether it is a key or sensitive field.",
    "data_dictionary.md",
    75,
)

CLEAN_VALIDATE_DATA = _spec(
    "clean_validate_data",
    "Profile the raw data, define reproducible cleaning rules, produce cleaned outputs, and prove that the cleaning did not create new errors.",
    "Save the profiling results, cleaning rules, reproducible cleaning code, before-and-after row counts, validation checks, exception log, and cleaned files in data/processed or data/staging.",
    "clean_validate_data.md",
    120,
)

ASSUMPTIONS = _spec(
    "document_assumptions",
    "Record the assumptions required to interpret the data and analysis so reviewers can distinguish known facts from analyst judgment.",
    "Document each assumption, why it was needed, its effect on the analysis, how it was tested where possible, and what would change if the assumption were wrong.",
    "assumptions.md",
    35,
)

SCHEMA = _spec(
    "create_schema",
    "Design the analytical tables and SQL data types before loading data. The schema should make table grain, keys, relationships, and constraints explicit.",
    "Save executable schema SQL that creates every required table with appropriate types and keys; add comments or documentation for table grain; and run the script successfully in the project database.",
    "create_schema.md",
    75,
)

LOAD_DATA = _spec(
    "load_data",
    "Load the source or cleaned files into the analytical database in a repeatable way and verify that the load matches the source files.",
    "Save a repeatable load script; load every required table; compare loaded row counts with the source manifest; inspect sample rows and data types; and document rejected or transformed records.",
    "load_data.md",
    60,
)

QUALITY_CHECKS = _spec(
    "quality_checks",
    "Run SQL checks that establish whether the analytical tables are complete, valid, internally consistent, and safe to use for the project questions.",
    "Save and run checks for row counts, key uniqueness, missing required values, invalid categories or ranges, date logic, duplicates, and relationship integrity; record every exception and its resolution.",
    "quality_checks.md",
    90,
)

ANALYSIS_QUERIES = _spec(
    "analysis_queries",
    "Write organized SQL that directly answers the approved business questions and produces interpretable, validated results.",
    "Save one clearly labeled query or query section per business question; include comments, readable CTEs or aliases, explicit grain, and result validation; export or document the final outputs.",
    "analysis_queries.md",
    150,
)

DOCUMENTED_QUERIES = _spec(
    "documented_queries",
    "Package the final SQL so another analyst can understand what each query does, run it in the correct order, and trace its output to a business question.",
    "Organize the final SQL files, add a table of contents or query index, document inputs and outputs, include assumptions and validation notes, and verify that all files run from a clean setup.",
    "documented_queries.md",
    60,
)

VALIDATE_FINDINGS = _spec(
    "validate_findings",
    "Challenge the analysis before presenting it by reconciling totals, checking alternative explanations, and confirming that SQL, Python, and dashboard outputs agree.",
    "Recalculate key metrics independently, compare outputs across tools, test edge cases and filters, explain discrepancies, and mark each major finding as confirmed, revised, or unsupported.",
    "validate_findings.md",
    75,
)

CLEAN_DATA = _spec(
    "clean_data",
    "Create a reproducible Python cleaning workflow that transforms the raw or staging data into analysis-ready files without altering the original sources.",
    "Save the cleaning notebook or script, document every transformation, preserve raw files, produce processed outputs, and verify row counts, types, missing values, duplicates, and key fields after cleaning.",
    "python_clean_data.md",
    120,
)

EDA = _spec(
    "eda",
    "Explore the data systematically to understand distributions, segments, trends, relationships, and potential quality issues before drawing conclusions.",
    "Complete the EDA checklist; save summary tables and purposeful charts; investigate notable patterns and anomalies; and write a short findings log linked to the business questions.",
    "eda.md",
    120,
)

ANOMALIES = _spec(
    "detect_anomalies",
    "Identify unusual records or patterns that could represent errors, operational exceptions, or meaningful business behavior.",
    "Define the anomaly rules, produce a reviewed anomaly table, inspect representative records, classify each pattern as error or valid exception, and document how it affects the analysis.",
    "detect_anomalies.md",
    75,
)

DERIVED_METRICS = _spec(
    "derived_metrics",
    "Create calculated fields and analytical features that are required for the approved KPIs and business questions.",
    "Document and calculate each derived field with its formula, grain, data type, edge-case handling, and validation; confirm that the results reconcile with source values.",
    "derived_metrics.md",
    75,
)

INSIGHTS = _spec(
    "document_insights",
    "Turn exploratory results into concise, evidence-based observations without overstating causality or business impact.",
    "Write at least five prioritized insights with the supporting metric, comparison, segment or period, business relevance, limitation, and recommended follow-up; link each insight to an output table or chart.",
    "document_insights.md",
    60,
)

POWER_BI_MODEL = _spec(
    "power_bi_model",
    "Build a Power BI model with clear fact and dimension roles, correct relationships, a dedicated date table, and predictable filter behavior.",
    "Save the model with documented table grains, one-to-many relationships where appropriate, no unexplained many-to-many relationships, an active date table, hidden technical fields, and reconciled row and KPI totals.",
    "power_bi_model.md",
    105,
)

DAX_MEASURES = _spec(
    "dax_measures",
    "Create reusable DAX measures for the approved KPIs rather than relying on implicit aggregations or duplicated visual calculations.",
    "Create and organize the required measures; document each formula and formatting choice; test filter context and edge cases; and reconcile every headline measure with SQL or source totals.",
    "dax_measures.md",
    105,
)

DASHBOARDS = _spec(
    "dashboards",
    "Build report pages that answer the prioritized business questions with an intentional information hierarchy and appropriate visuals.",
    "Create the required report pages, add titles and metric definitions, use appropriate visuals and interactions, test filters, confirm accessibility and readability, and reconcile displayed values.",
    "dashboards.md",
    150,
)

EXECUTIVE_DASHBOARD = _spec(
    "executive_dashboard",
    "Create an executive overview that communicates the most important KPIs, trends, risks, and decisions without requiring the viewer to inspect detailed operational pages.",
    "Build one polished overview page with headline KPIs, trend and variance context, the most important drivers or risks, clear filters, and a concise takeaway; validate every displayed value.",
    "executive_dashboard.md",
    105,
)

WORKLOAD_DASHBOARD = _spec(
    "workload_dashboard",
    "Create an operational page that helps production leaders understand workload, capacity, schedule risk, and where attention is needed.",
    "Build the workload page with agreed capacity and workload measures, useful breakdowns, risk indicators, filters, drill paths, and a documented interpretation; reconcile totals with SQL.",
    "workload_dashboard.md",
    105,
)

FILTERS_DRILLTHROUGH = _spec(
    "filters_drillthrough",
    "Add interactions that let users move from summary findings to the specific records or segments behind them without creating confusing filter behavior.",
    "Add only decision-useful slicers and drill-through paths; document their purpose; test single and combined selections, reset behavior, empty states, and cross-filtering; fix any misleading interactions.",
    "filters_drillthrough.md",
    60,
)

EXECUTIVE_SUMMARY = _spec(
    "executive_summary",
    "Write a concise stakeholder summary that explains the problem, approach, strongest findings, recommendations, and important limitations.",
    "Save a one-page summary with business context, methods, three to five quantified findings, prioritized recommendations, limitations, and links to the dashboard or supporting artifacts.",
    "executive_summary.md",
    75,
)

SCREENSHOTS = _spec(
    "screenshots",
    "Create clean portfolio images that make the final work understandable before a reviewer opens the dashboard, notebook, or repository.",
    "Capture the most important pages or outputs at readable resolution, remove personal or irrelevant UI, use consistent filenames, add captions or alt text, and verify that the README references the correct files.",
    "screenshots.md",
    45,
)

ASSUMPTIONS_LIMITATIONS = _spec(
    "assumptions_limitations",
    "Explain what the project assumes, what the data cannot prove, and where the analysis may be incomplete so the final recommendations remain credible.",
    "Document material assumptions, data limitations, methodological limitations, unresolved quality issues, likely effect on conclusions, and the next data or analysis that would reduce uncertainty.",
    "assumptions_limitations.md",
    45,
)

README = _spec(
    "readme",
    "Create an employer-facing project README that quickly explains the business problem, analytical process, tools, results, and how to inspect or reproduce the work.",
    "Complete every README section, include final visuals and artifact links, provide setup or navigation instructions, disclose synthetic data where applicable, remove placeholders, and test every link from the repository root.",
    "readme.md",
    90,
)

PUBLISH = _spec(
    "publish",
    "Perform a final quality and privacy review, create a clear release point, and publish the project so an employer can access the intended artifacts without setup confusion.",
    "Run the publication checklist, remove secrets and temporary files, verify reproducibility and links, confirm the repository description and topics, commit the final state, create a versioned release or tag, and test the public view.",
    "publish.md",
    60,
)


EXACT_TASK_SPECS: dict[str, PortfolioTaskSpec] = {
    "Finalize business problem": BUSINESS_PROBLEM,
    "Define business problem": BUSINESS_PROBLEM,
    "Finalize stakeholders": STAKEHOLDERS,
    "Identify stakeholders": STAKEHOLDERS,
    "Finalize KPIs": KPIS,
    "Define KPIs": KPIS,
    "Finalize business questions": BUSINESS_QUESTIONS,
    "Create synthetic data specification": SYNTHETIC_SPEC,
    "Generate dataset": DATASET_SOURCE,
    "Source or generate dataset": DATASET_SOURCE,
    "Validate relationships": VALIDATE_RELATIONSHIPS,
    "Complete data dictionary": DATA_DICTIONARY,
    "Build data dictionary": DATA_DICTIONARY,
    "Clean and validate data": CLEAN_VALIDATE_DATA,
    "Document assumptions": ASSUMPTIONS,
    "Create schema": SCHEMA,
    "Load data": LOAD_DATA,
    "Run quality checks": QUALITY_CHECKS,
    "Answer business questions": ANALYSIS_QUERIES,
    "Write analysis queries": ANALYSIS_QUERIES,
    "Save documented queries": DOCUMENTED_QUERIES,
    "Validate SQL findings": VALIDATE_FINDINGS,
    "Validate findings": VALIDATE_FINDINGS,
    "Clean data": CLEAN_DATA,
    "Explore distributions": EDA,
    "Perform EDA": EDA,
    "Detect anomalies": ANOMALIES,
    "Create derived metrics": DERIVED_METRICS,
    "Document insights": INSIGHTS,
    "Build data model": POWER_BI_MODEL,
    "Create DAX measures": DAX_MEASURES,
    "Create measures": DAX_MEASURES,
    "Build dashboards": DASHBOARDS,
    "Build executive dashboard": EXECUTIVE_DASHBOARD,
    "Build workload dashboard": WORKLOAD_DASHBOARD,
    "Add filters and drill-through": FILTERS_DRILLTHROUGH,
    "Write executive summary": EXECUTIVE_SUMMARY,
    "Add screenshots": SCREENSHOTS,
    "Document assumptions and limitations": ASSUMPTIONS_LIMITATIONS,
    "Finalize README": README,
    "Publish project": PUBLISH,
    "Publish release": PUBLISH,
}


PROJECT_OVERRIDES: dict[tuple[int, str], PortfolioTaskSpec] = {
    (1, "Validate relationships"): _spec(
        "vfx_validate_relationships",
        "Verify that the VFX production tables connect correctly before analysis. Check that each client, project, shot, artist, time entry, and review uses valid keys and that joining the tables does not unexpectedly duplicate or remove records.",
        "Complete the prefilled VFX relationship matrix; test client→project, project→shot, artist→time entry, shot→time entry, and shot→review links; run primary-key uniqueness and orphan-key SQL; compare row counts before and after joins; investigate exceptions; and save the completed guide plus validation queries under sql/validation.",
        "vfx_validate_relationships.md",
        90,
    ),
}


def task_spec(label: str, project_id: int | None = None) -> PortfolioTaskSpec | None:
    if project_id is not None:
        override = PROJECT_OVERRIDES.get((int(project_id), str(label)))
        if override is not None:
            return override
    return EXACT_TASK_SPECS.get(str(label))


def all_labels() -> tuple[str, ...]:
    return tuple(sorted(EXACT_TASK_SPECS))
