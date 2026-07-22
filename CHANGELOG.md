# v10.19.2 — Guided Relationship Validation Workflow
- Moved detailed relationship-validation instruction into the Markdown task guide.
- Kept the Jupyter notebook clean and SQL-first: setup, queries, outputs, interpretations, and conclusion only.
- Added the complete validation order: baseline grain, primary-key nulls and duplicates, foreign-key nulls and orphans, join cardinality, and project-specific checks.
- Clarified that relationship validation documents issues but does not clean raw data.
- Added safe migration for existing managed notebooks and task guides, with notebook archiving when learner work or outputs exist.

# v10.19.1 — Dedicated Career Accelerator Notebook Kernel
- Added JupySQL and IPykernel to the managed application environment.
- Registered the repository `.venv` as `Python (Career Accelerator)` on every launch.
- Generated relationship-validation notebooks now target the dedicated kernel automatically.
- Existing notebooks receive a metadata-only kernel repair that preserves SQL, notes, and outputs.
- Generated VS Code workspaces continue to use the repository `.venv` and now recommend both Python and Jupyter extensions.

# v10.19.0 — Native SQL Portfolio Notebooks

- Replaced Python-string query cells with native JupySQL `%%sql` cells.
- Reduced the relationship-validation notebook to one collapsed setup cell, four focused SQL work sections, interpretation prompts, and a final conclusion.
- Kept schemas, keys, and relationship maps in the Task Workspace Visual Guide instead of duplicating them in the notebook.
- Continued using an isolated in-memory DuckDB session so the VS Code DuckDB extension can remain open without locking the notebook.
- Added `jupysql` to the managed environment.
- Added a v2-to-v3 notebook migration that copies recognized learner SQL into the new sections and archives notebooks containing work or outputs.
- Preserved project data, source configuration, milestone state, learner files, Academy progress, task history, and both application databases.

# v10.18.1 — Notebook DuckDB Lock Hotfix

- Replaced the relationship-validation notebook's direct file connection with an isolated in-memory DuckDB session built from the project's configured raw sources.
- Removed automatic `project.duckdb` attachment from the generated VS Code workspace to prevent Windows file-lock conflicts.
- Added a targeted migration that repairs only the managed notebook setup cell while preserving learner queries, Markdown notes, and outputs.
- Kept the prepared project database available for other project tools without making it a prerequisite for notebook execution.

# v10.18.0 — Portfolio Validation Notebooks and SQL Submission Repair

- Replaced the standalone relationship-validation SQL starter and separate findings document with one guided Jupyter notebook.
- Kept the task instructions, table schemas, learner-written SQL, query output, interpretation, and final conclusion together in the notebook.
- Prepared the project DuckDB connection and table-list cells automatically while leaving every real validation query for the learner to write.
- Added project-specific uniqueness, orphan-key, join-cardinality, and consistency prompts generated from each project's source manifest.
- Added **Open Notebook in VS Code** and generated a project workspace that recommends Jupyter and uses the repository Python environment.
- Safely deleted untouched superseded generated SQL/findings files and archived edited managed copies during migration.
- Added `ipykernel` to the managed environment so generated notebooks can run through VS Code without a separate manual kernel setup.
- Fixed false “untouched starting template” errors for DataLemur submissions by evaluating executable SQL after comments are removed.
- Preserved databases, project source files, learner-authored SQL, notebook work, Academy progress, task history, and evidence.

# v10.17.0 — Portfolio SQL Workspace Simplification

- Rebuilt portfolio relationship-validation tasks around one runnable SQL starter, one findings document, one project DuckDB database, and one generated VS Code workspace.
- Automatically attach each project database through workspace-scoped DuckDB settings and select it as the active database.
- Added **Open Starter in VS Code** as the primary portfolio SQL action.
- Removed learner-facing setup scripts and fragmented generated validation-query files.
- Replaced completed project-specific query examples with table schemas, relationship metadata, small placeholder syntax patterns, and blank TODO sections.
- Moved project source configuration to `config/project_sources.yaml` while safely migrating the previous location.
- Added project-neutral source discovery, schema display, relationship inference, and data refresh behavior.
- Added generated `documentation/relationship_validation.md` findings templates.
- Delete untouched obsolete generated files; archive edited managed files before removing them.
- Removed the obsolete VFX-only relationship starter and project-specific task override.
- Preserved learner-created SQL, Markdown, source data, databases, milestone state, and other portfolio work.

# v10.16.0 — Project Data Workspaces and Academy Sync

- Added a project-neutral raw-data workspace generator for portfolio relationship-validation milestones.
- Discover CSV, Parquet, JSON, JSONL, and NDJSON sources beneath each project’s `data/raw/` folder, or load an editable `data/project_sources.yaml` manifest.
- Generate a reusable DuckDB database, portable source-registration SQL, primary-key checks, orphan-key checks, join-cardinality checks, and a project-specific validation guide.
- Replaced invalid filename-as-table examples such as `raw_clients` with registered schema-qualified views such as `raw.clients`.
- Added **Refresh Data Setup**, **Open Setup SQL**, and **Open Project Database** controls to the guided portfolio milestone workspace.
- Made source discovery, table naming, key inference, and relationship inference work from project configuration rather than hardcoded VFX tables.
- Rebuilt Academy Today/Week counters from passed interactive activities instead of static zero values.
- Preserved each completed Academy focus assignment before advancing to the next recommended step, preventing a new lesson from appearing already completed.
- Archived completed Academy adaptive tasks and created a fresh task for the next activity instead of reusing one task row indefinitely.
- Kept routine Academy progress separate from employer-facing Demonstrated Evidence.
- Connected every Learning Overview **Continue** button to its actual workspace.
- Added live Academy progress notifications so the Learning Dashboard and Dashboard refresh immediately after a checked answer.
- Hardened Academy **Continue** navigation against stale roadmap targets and unresolved prerequisite transitions.
- Preserved databases, learner answers, portfolio files, generated source manifests, task history, and Demonstrated Evidence.

# v10.15.0 — Academy Progression and Today’s Focus Repair

- Separated internal Academy skill mastery from employer-facing Demonstrated Evidence.
- Derived prerequisite skills from lessons whose required interactive steps and unassisted mastery activity are complete.
- Reconciled cached lesson states from authoritative activity progress when Academy starts.
- Fixed the false pathway-complete banner caused by an empty lesson-evidence table.
- Fixed **Customize Query Results** (`DISTINCT` and `LIMIT`) remaining locked after mastering **Write Your First SQL**.
- Prevented the recommendation engine from skipping a blocked lesson and moving to later course material.
- Marked the Academy track complete only after every required lesson step, checkpoint, and project has passed.
- Repaired falsely completed Academy planner tasks and restored the current Academy step to Today’s Focus without deleting completed history.
- Preserved all answers, hints, attempts, lesson progress, projects, evidence, databases, and external-learning history.

# v10.14.0 — Readable Task Guides and Exact DataLemur Links

- Added an **Open on DataLemur ↗** control to SQL Companion's interview-problem workspace.
- Mapped every SQL Companion catalog problem to its exact official DataLemur question page.
- Kept Task Workspace routing local: Today’s Focus and Adaptive Planner open the exact problem in SQL Companion first, then the learner chooses when to open DataLemur in the browser.
- Replaced plain rendered code with high-contrast, line-numbered code boxes in Task and Portfolio Visual Guides.
- Improved inline code, file-path, URL, guide-document path, and Raw Markdown readability with larger monospace typography and stronger contrast.
- Preserved all local submissions, notes, mastery, completion state, task workspaces, portfolio files, Academy progress, and databases.

# v10.13.0 — Guided Task Workbench and SQL Completion Repair

- Made rendered Markdown the default view in both general Task Workspaces and Portfolio Milestone workspaces.
- Added a separate Raw Markdown tab with autosave and live preview refresh.
- Added safe guide-reference detection and one-click creation of selected or all missing files and folders.
- Kept all created paths inside the repository and prevented existing learner files from being overwritten.
- Added exact DataLemur-to-SQL-Companion routing from the task workspace.
- Added descriptive briefs and definitions of done to generated SQL interview tasks.
- Fixed the `task_metadata.description` NOT NULL failure that occurred when completing Teams Power Users and generating the next SQL task.
- Preserved saved SQL paths, notes, mastery, and completion data during SQL task advancement.
- Required a saved, non-template SQL submission before dashboard or Task Workspace completion can finish a SQL interview task.
- Preserved databases, portfolio milestone states, Academy progress, evidence, submissions, and user-authored files.

# v10.12.0 — Guided Portfolio Milestones

- Added detailed descriptions, definitions of done, time estimates, and managed starter documents to all portfolio milestones across all three projects.
- Added a Guide button and dedicated Portfolio Milestone workspace with autosave, external editing, folder access, and completion controls.
- Added project-aware starter generation under each project’s `workspaces/milestones/` directory without overwriting existing learner work.
- Added a comprehensive VFX relationship-validation guide covering key uniqueness, orphan foreign keys, cross-table project consistency, and join-cardinality checks.
- Routed adaptive Portfolio tasks and planner actions directly to the matching guided milestone.
- Preserved all existing project completion states, notes, datasets, submissions, databases, Academy progress, and Demonstrated Evidence.

# v10.11.0 — Roadmap, Evidence, and Interview-Metric Cleanup

- Audited the legacy 12-week sprint roadmap and archived static tasks already owned by Google, Accelerator Academy, SQL Practice, Applied Labs, or Portfolio tracks.
- Preserved removed task history in `roadmap_task_archive` while excluding those rows from current sprint totals and recommendations.
- Retained only weekly retrospectives plus focused interview, job-readiness, portfolio-polish, résumé, LinkedIn, application, and program-review milestones.
- Added clear descriptions, definitions of done, and guided starter documents for every retained roadmap task.
- Upgraded Task Workspaces to display the task brief and completion criteria and to seed new workspaces from the task-specific starter file.
- Removed routine Academy lesson and mastery completions from Demonstrated Evidence.
- Limited automatic Academy evidence to validated projects, capstones, and labs, with one employer-facing evidence row per substantial submission.
- Replaced the inflated Interview Practice formula with a score based only on completed SQL interview questions and explicit interview rehearsals.
- Added transparent Interview Practice progress text and removed DataCamp wording from weekly guidance.

# v10.10.0 — SQL Fundamentals Course and Chapter Reorganization

- Reworked the Accelerator Academy SQL roadmap into seven courses following the requested SQL Fundamentals course order.
- Added the complete public chapter hierarchy beneath each course and displayed chapter headers in the collapsible pathway list.
- Expanded the SQL curriculum to 35 lessons with 193 total Academy journey nodes across all active tracks.
- Added seven integrated course checkpoints.
- Added Bonus Project — Analyzing Students' Mental Health after Intermediate SQL.
- Added Bonus Project — Impact Analysis of GoodThought NGO Initiatives after Database Design.
- Added original datasets for customer, order-item, monthly-performance, student-wellbeing, and community-impact analysis.
- Preserved compatible progress by reusing stable lesson and activity identifiers where earlier Academy topics map to the new structure.
- Kept all instructional text, examples, exercises, datasets, solutions, and project work original to Accelerator Academy.
- Removed the four superseded SQL course-package folders after migrating their active content into the new seven-course structure.

# v10.9.0 — Collapsible Academy Courses, Performance, and Weekly Sprint Rollover

- Made every Accelerator Academy course header collapsible in the pathway list.
- Kept the active course expanded while future courses begin collapsed.
- Replaced per-node Academy database queries with bulk progress snapshots.
- Cached the immutable Academy journey structure and rendered only expanded course rows.
- Reduced Academy refresh time substantially for the current 112-step curriculum.
- Made Sprint Progress explicitly identify the active roadmap week.
- Added automatic Monday sprint advancement based on the configured program start date.
- Preserved completed tasks and manual future-week advancement during rollover.

# v10.8.0 — Accelerator Academy DataCamp Replacement and Roadmap Fixes

- Removed DataCamp from active daily recommendations, adaptive tasks, weekly quotas, and frozen focus snapshots while preserving completed records as External Learning History.
- Replaced DataCamp requirements with Accelerator Academy recommendations using plain task titles and the existing source metadata label.
- Added 26 original interactive replacement lessons across SQL, Power BI, Python, and pandas.
- Expanded the unified path to 8 courses, 31 lessons, and 112 interactive steps.
- Updated recommendation sequencing so each course's lessons, checkpoint, and project occur before the next course.
- Fixed overlapping tinted track, course, and lesson headers in the left pathway list.
- Removed the backdrop behind the lesson-completion message and shared Learning workspace subtitle/subheader text.
- Preserved Academy progress, legacy external-learning records, databases, submissions, evidence, Exercise Packs, Applied Labs, and portfolio work.

# v10.7.0 — Accelerator Academy Visual and Voice Polish

- Made Run Query, Check Answer, Show Hint, View Solution, and Continue share all available editor-side footer width until each control reaches its full comfortable size.
- Kept the controls dynamically aligned to the live lesson/editor divider and retained compact labels when space is limited.
- Replaced plain pathway headings with visible tinted header cards for the SQL track, courses, lessons, checkpoint, and applied project.
- Filled the path-progress rail from the course marker through Lesson 1 as soon as the learner enters the course.
- Added a graduation-cap emoji to Accelerator Academy in the application sidebar.
- Centered the Data Career Accelerator logo horizontally within the sidebar at every responsive width.
- Reworked learner-facing Academy copy to sound warmer, clearer, and less system-generated.
- Preserved all v10.6.0 behavior, curriculum content, progress, answers, schemas, mastery, checkpoint gating, project work, and Demonstrated Evidence.

# v10.6.0 — Accelerator Academy Final Layout Polish

- Split the lesson footer into divider-aware left and right control regions aligned with the live Lesson & Practice / Editor & Output divider.
- Kept Back and the completion requirement on the lesson side while Run Query, Check Answer, Show Hint, View Solution, and Continue remain on the editor side.
- Made footer control alignment update whenever the learner moves the main horizontal splitter.
- Replaced the multiple-choice workspace with a single uninterrupted answer surface so the SQL editor/output divider disappears completely when no editor or result table is needed.
- Added segment-level progress rails between course and lesson milestone circles, including complete, current, and future states.
- Strengthened tinted lesson-header backgrounds in the pathway card for current, completed, in-progress, available, and locked lessons.
- Preserved the unified sequential flow, schema visibility, prerequisite gates, progress, answers, and all v10.5.0 curriculum behavior.

# v10.5.0 — Accelerator Academy Workspace and Curriculum Context

- Integrated Try It context into the main lesson panel instead of duplicating it above the editor.
- Reserved the right workspace for the SQL editor or answer control, validation feedback, and output window.
- Consolidated Run Query, Check Answer, Show Hint, View Solution, Back, and Continue into one workflow row.
- Added content-configured SQL track and course headers to the roadmap for future multi-course organization.
- Added course and lesson milestone circles to path progress.
- Displayed the exact DuckDB-inferred schema for every table used by lesson, checkpoint, and applied-project SQL tasks.
- Added package validation requiring SQL activities to declare valid table metadata.
- Updated curriculum content to version 1.3.0 while preserving compatible learner answers and progress.

# v10.4.0 — Accelerator Academy Unified Learning Flow

- Replaced six separate Academy destinations with one coherent, sequential learner journey.
- Added a persistent path roadmap, Resume Learning, automatic next-step routing, and Back/Continue navigation.
- Converted all 26 lesson activities into required interactive steps that pair concise instruction with immediate action.
- Prevented learners from skipping future steps; Continue unlocks only after the current action passes.
- Added visible multiple-choice answer cards for recognition steps.
- Integrated the seven-question checkpoint and Customer Support Queue Analysis project into the same roadmap.
- Added persistent checkpoint drafts and current-target storage.
- Gated the applied project behind a passed course checkpoint.
- Updated mastery reconciliation so all required interactive steps must be passed and mastery work must remain unassisted.
- Updated curriculum content to version 1.2.0 with step-specific concept instruction for every lesson activity.
- Preserved existing SQL answers, compatible passed work, databases, evidence, submissions, Exercise Packs, Applied Labs, and portfolio artifacts.

# v10.3.0 — Accelerator Academy Experience and Curriculum Rewrite

- Rebuilt all Academy pages to match the established Exercises and Applied Labs visual system.
- Replaced generic tabs and controls with responsive cards, section buttons, split workspaces, internal scrolling, existing SQL editors, existing feedback controls, and established action styling.
- Expanded SQL Query Foundations from 18 to 26 original lesson activities across five comprehensive lessons.
- Added richer instruction, learning objectives, worked examples, common mistakes, activity briefs, output expectations, post-completion explanations, and lesson takeaways.
- Expanded the course checkpoint from five to seven independent questions.
- Rebuilt Customer Support Queue Analysis as a full Applied Lab-style Skills Lab with stakeholder context, acceptance criteria, reflection, rubric, saved progress, validation, and Demonstrated Evidence.
- Added curriculum content-version reconciliation that preserves answers while re-evaluating updated practice and mastery requirements.
- Added safe subset validation for unordered `DISTINCT` + `LIMIT` exercises and fixed solution-assisted evidence handling.
- Preserved all existing learner databases, external learning records, Exercise Pack progress, Applied Lab work, SQL submissions, and portfolio artifacts.

# v10.2.0 — Accelerator Academy Phase 2A and 2B

- Added the generic external curriculum engine, four-state mastery, prerequisites, versioning, checkpoints, and evidence integration.
- Added the five-lesson SQL Foundations pilot with 18 original activities, a five-question checkpoint, and one Skills Lab.
- Added adaptive-planner routing and provider-neutral External Learning History storage.
- Preserved all existing learner databases, progress, submissions, backups, and external-learning history.

# Changelog

## 10.20.0 — Portfolio Workspace Command Center

- Replaced generic Portfolio Workspace note tabs with Overview, Milestones,
  Data Explorer, Workbench, Deliverables, and Evidence & Readiness.
- Rendered each project's README as Markdown across the full Overview tab.
- Added dynamic DuckDB schema, row-count, five-row preview, and relationship
  inspection for every configured dataset table.
- Added project-file inventory, deliverable detection, evidence readiness,
  and task-guide coverage views.
- Upgraded all non-relationship portfolio guides to detailed,
  task-specific, managed guides while preserving existing learner work.
- Retained the specialized dynamic Validate Relationships guide.

## 10.20.0 — Pathway and Portfolio Onboarding

- Added locked first-run pathway selection with neutral Career Accelerator branding.
- Enabled the Data Analytics pathway and added IT Support, Cybersecurity, and Software Engineering shells.
- Added a ChatGPT portfolio setup export and validated `.career-portfolio.json` importer.
- Added dynamic project names/directories while retaining the existing three-project catalog as a migration fallback.
- Added automatic existing-user detection so established profiles are not prompted or overwritten.
- Added a one-time guided application tour and Setup menu actions to restart it.
- Added explicit portfolio replacement backups and a separate full first-run reset.
- Added clean-repository packaging scripts for alternate branches and new users.

## 10.20.1 — Pathway Graphics and Complete First-Run Reset

- Added the approved Option 2 logo family for neutral, Data Analytics, IT Support, Cybersecurity, and Software Engineering states.
- Added pathway-specific stacked selection logos, horizontal application logos, program icons, and Windows app icons.
- Added locked first-run pathway selection with neutral Career Accelerator branding.
- Enabled the Data Analytics pathway and retained the other pathways as configuration-driven shells.
- Added a ChatGPT portfolio setup export and validated `.career-portfolio.json` importer.
- Added dynamic project names/directories while retaining the existing three-project catalog as an existing-user migration fallback.
- Added automatic existing-user detection so established profiles are not prompted or overwritten.
- Added a one-time guided application tour and Setup menu actions to restart it.
- Rebuilt Full First-Run Reset to create an external safety ZIP, clear every application table, remove learner-owned files, and recreate safe onboarding scaffolding.
- Preserved application code, pathway definitions, curriculum, starter templates, datasets, exercises, validation guides, and onboarding assets during a full reset.
- Added clean-repository packaging scripts for alternate branches and new users.

## 10.20.2 — Reset Reliability and Relocatable Paths

- Added the approved Option 2 logo family for neutral, Data Analytics, IT Support, Cybersecurity, and Software Engineering states.
- Added pathway-specific stacked selection logos, horizontal application logos, program icons, and Windows app icons.
- Added locked first-run pathway selection with neutral Career Accelerator branding.
- Enabled the Data Analytics pathway and retained the other pathways as configuration-driven shells.
- Added a ChatGPT portfolio setup export and validated `.career-portfolio.json` importer.
- Added dynamic project names/directories while retaining the existing three-project catalog as an existing-user migration fallback.
- Added automatic existing-user detection so established profiles are not prompted or overwritten.
- Added a one-time guided application tour and Setup menu actions to restart it.
- Rebuilt Full First-Run Reset to create an external safety ZIP, clear every application table, remove learner-owned files, and recreate safe onboarding scaffolding.
- Preserved application code, pathway definitions, curriculum, starter templates, datasets, exercises, validation guides, and onboarding assets during a full reset.
- Added clean-repository packaging scripts for alternate branches and new users.

## 10.20.5 — Fixed 90-Day Completion and Dashboard Reliability

- Added a fixed Day 90 completion contract; adaptive scheduling may reprioritize work but cannot extend the deadline.
- Added deadline-derived quotas for Google, SQL/DuckDB, Applied Labs, Accelerator Academy, and all three portfolio projects.
- Added a 228-hour standard scope that fits the 18-hours-per-week, 90-day capacity with a small buffer.
- Required exactly three integrated portfolio projects, each combining spreadsheet inspection, SQL, Python/pandas, Power BI/DAX/Power Query, GitHub reproducibility, and stakeholder communication.
- Added 15–30 hour per-project and 70-hour total portfolio limits.
- Added preferred-name collection during Step 1 onboarding and dynamic Dashboard greetings.
- Replaced layout-consuming status-bar messages with a transient overlay notifier.
- Restored two-line Today’s Focus rows with Today, Week, and Day n/90 pacing.
- Expanded Today’s Focus to three Learning slots plus SQL and Portfolio.
- Restored approved horizontal logo proportions with aspect-ratio-safe scaling.
- Retained the cumulative pathway onboarding, one-time tour, portfolio importer, comprehensive reset, and fresh-repository builder.
