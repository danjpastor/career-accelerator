# Career Accelerator v10.27.0

## Unified learning and planning system

- Replaced the overlapping adaptive, manual-focus, Added Today, and Get Ahead planners with one deterministic task/readiness runtime.
- Keeps the Google Data Analytics Certificate as the first unfinished priority every day until completion.
- Generates up to five prerequisite-ready Today’s Focus tasks and shows fewer when fewer tasks are available.
- Generates six prerequisite-ready Next Tasks and separates locked work into a clear Coming Up list.
- Replaces the old time/energy queue and editable sprint backlog with a simplified Daily Plan page showing Today’s Ready Plan and Next Ready Tasks.
- Uses canonical task IDs and source metadata so Google module text cannot overwrite Academy, DuckDB, interview, or portfolio tasks.
- Establishes the sequential Academy path: Spreadsheets, SQL, Power BI, Python and pandas, then Portfolio Readiness.
- Centralizes DuckDB, SQL interview, weekly mastery, Academy, and portfolio lockouts behind one readiness facade.
- Removes the retired DataCamp catalog from active roadmap and concept inference while preserving historical database fields and migration support.
- Converts catch-up into a derived presentation label instead of storing it inside task titles.
- Replaces the Get Ahead workflow with non-persistent Optional Practice.
- Preserves completed Academy work, Google progress, SQL and DuckDB completions, portfolio milestones, study history, applications, and evidence.
- Adds explicit empty-focus guidance when no prerequisite-ready task exists.

# Career Accelerator v10.26.3

## Startup routing repair

- Fixed dashboard startup failure when a non-DuckDB task label was checked by the DuckDB source-routing helper.
- DuckDB source detection now accepts either an exercise number or a task label and safely returns no match for unrelated tasks.
- Spreadsheet catch-up tasks can now render in Today's Focus and Next Tasks without being passed to `int()`.
- Preserves all learner progress and planner data.

# v10.26.2 - Catch-Up Planner Startup Recovery

- Repairs malformed numeric values in catch-up sprint tasks, task metadata, Today’s Focus, and the durable Added Today store before track or dashboard refreshes.
- Recovers task links from source keys and matching sprint-task labels instead of allowing one damaged derived row to block application startup.
- Hardens Today’s Focus, track presentation, and pacing-detail helpers against malformed transient task identifiers.
- Changes managed catch-up labels to an ASCII-safe `Catch-Up:` prefix so hidden-launcher error messages no longer display mojibake.
- Preserves learner progress and regenerates only derived scheduling values that cannot be safely interpreted.

# v10.26.1 - Integrated Roadmap Scheduling and Practice Lockout Repair

- Rebuilt Weeks 1-8 around the prerequisite sequence: spreadsheets, SQL, Power BI, then Python and pandas.
- Added lesson-level spreadsheet reconciliation so existing learners receive missing spreadsheet lessons and mastery checks as catch-up work without losing completed progress.
- Regenerates Today's Focus after roadmap reconciliation and resynchronizes tracks so obsolete Week 2 portfolio execution no longer remains active.
- Added phase-aware Today's Focus slots and a dedicated Next Tasks queue that shows ready and blocked catch-up work with exact reasons.
- Audited all SQL Companion interview problems, removed DataCamp and Google Course 5 as SQL prerequisite evidence, and applied corrected all-of/any-of skill requirements.
- Shows all SQL Companion problems with Completed, Ready, or Locked status and disables editors and completion actions while prerequisites are unmet.
- Audited all DuckDB exercises and enforced prerequisites through both DuckDB interfaces and the underlying run, check, save, and submit services.
- Preserved completed SQL problems and DuckDB exercises for review while preventing incomplete advanced practice from bypassing Academy mastery gates.
- Added Academy track gates: Spreadsheet Mastery before unfinished SQL work, SQL Mastery before Power BI, and Power BI Mastery before Python.
- Retired legacy DataCamp tasks from active scheduling while preserving historical records in the database.

# v10.25.9 - Dictionary-Aware Cleaned CSV Validation

- Fixed the cleaned-CSV importer treating formats, examples, ranges, identifiers, names, dates, numeric measures, foreign keys, and email patterns as exhaustive allowed-value lists.
- Strict allowed-value validation now applies only to clearly enumerated controlled categories.
- Added targeted validation for documented dates, numeric ranges, identifier patterns, email domains, nullability, uniqueness, and relationships.
- Self-referencing foreign keys are now checked against the CSV being imported instead of an older processed copy.
- Added a dedicated **Structural changes to review** section showing removed and added primary-key records.
- Row-count changes now remain reviewable without generating dozens of false value warnings.
- Import status remains **Ready for review** when records were added or removed, even when all business rules pass.
- Updated the review dialog to separate blocking issues, structural changes, business-rule warnings, and validation notes.

# v10.25.8 - Cleaning Notebook Import and Windows Workspace Geometry

- Added **Import Cleaning Notebook** to every table in the Data Cleaning Studio.
- Validates imported `.ipynb` files, checks the apparent table, and prevents obvious cross-table imports.
- Saves the active integrated notebook before replacement.
- Backs up the previous managed notebook under `backups/cleaning-notebooks/`.
- Copies the imported notebook into the table's managed `notebooks/cleaning/` path and loads it immediately in the integrated Cleaning Notebook tab.
- Records notebook provenance, import time, managed table, and Data Dictionary fingerprint in notebook metadata and studio state.
- Keeps imported notebooks connected to the normal table dropdown, autosave, execution, and completion workflow.
- Promoted Task Workspace and Portfolio Milestone windows to native top-level Windows windows with minimize, maximize, close, and snap support.
- Fits workspace window frames to the monitor's actual available work area so the title bar and bottom controls cannot open behind the Windows taskbar.

# v10.25.7 - Notebook Results and Editor Readability

- Executes integrated SQL cells through a persistent DuckDB helper instead of relying on JupySQL to decide whether a statement returns rows.
- Displays `DESCRIBE`, `SHOW`, `PRAGMA`, `EXPLAIN`, `SELECT`, and other row-returning SQL statements as readable dataframe tables.
- Keeps `%%sql` in the learner notebook while sending a safe execution wrapper to the kernel.
- Applies explicit dark-theme colors to table wrappers, headers, cells, indexes, text, and borders.
- Adds inline table styles for reliable rendering in Qt's notebook output browser.
- Repositions autocomplete below the active line, or above it when the bottom of the screen has insufficient room.
- Removes cell execution errors from the notebook header next to Save Notebook; errors remain with the output cell where they occurred.
- Keeps the kernel toolbar status short and places technical detail in its tooltip.

# v10.25.6 - Reliable Notebook SQL Installer Repair

- Fixed the v10.25.5 installer rejecting its own valid SQL language-detection payload.
- Installer validation now checks `detect_notebook_language`, `_SQL_START_RE`, and `prepare_execution_source`, matching the actual implementation.
- Preserved execution-time normalization for comments or blank lines before `%%sql` and for plain SQL cells.
- Preserved readable ANSI-free notebook errors.

# v10.25.5 - Reliable Notebook SQL Execution

- Fixed SQL cells being passed to Python when blank lines or comments appeared before `%%sql`.
- Plain SQL notebook cells are now routed through JupySQL automatically.
- The execution runner moves `%%sql` to the required first physical line without rewriting the saved notebook cell.
- Whole-line `#` comments in SQL cells are translated to `--` for execution.
- SQL-like cells are recognized from their first meaningful statement, not only their first physical line.
- Removed ANSI terminal color codes from notebook errors and text output so failures are readable in the integrated output panel.
- Preserved all v10.25.4 autocomplete, paired-character, JupySQL connection, Jupyter table styling, and detached-window behavior.

# v10.25.4 - VS Code Editing, JupySQL, and Native Detached Windows

- Added per-window Windows AppUserModelIDs for separately listed detached tabs.

- Added a reusable VS Code-inspired assistance layer for SQL and Python code editors.
- Added content-aware completion from SQL keywords/functions, Python built-ins, variables already written in the editor, peer notebook cells, Data Dictionary fields, and project CSV table/column names.
- Added `Ctrl+Space` completion, Tab acceptance, paired parentheses/brackets/quotes, paired deletion, selection wrapping, indentation, and VS Code line-comment shortcuts.
- Applied the assisted editor to every shared SQL practice editor, integrated Jupyter code cell, analytical database build editor, and SQL analysis editor.
- Added context-aware DuckDB exercise table and column completion.
- Added a dedicated **+ SQL** notebook-cell action that creates a native `%%sql` cell.
- Automatically loads the JupySQL extension when the integrated kernel starts and connects it to the project DuckDB database, with an in-memory DuckDB fallback.
- Added `duckdb-engine` to application requirements and launcher verification so `%%sql` is installed and validated automatically.
- Styled pandas and SQL result tables with Jupyter-like headers, borders, zebra rows, index cells, spacing, and scrollable table containers.
- Added a live floating window preview when a tab is dragged beyond its workspace; releasing drops the tab window at that location.
- Preserved the original tab widget instance while dragging so notebook kernels, outputs, unsaved edits, and form state remain intact.
- Forced detached workspace windows to receive their own native Windows taskbar/Alt-Tab entry while retaining task-dialog ownership and modal interaction.
- Preserved all v10.25.3 detachable-tab restoration, v10.25.2 fast-close behavior, and v10.25.1 guided cleaning workflows.

# v10.25.3 - Detachable Workspace Tabs

- Added reusable detachable tabs to general Task Workspaces and Portfolio Milestone Workspaces.
- Dragging a tab outside its workspace moves the existing widget into a branded standalone window rather than creating a duplicate.
- Preserved notebook kernels, running-state ownership, unsaved edits, outputs, rendered Markdown state, form values, selected tables, and scroll positions while detaching or reattaching.
- Added drag-back reattachment to the original tab bar and a **Return to Workspace** button in every detached window.
- Closing a detached window automatically returns its tab to the original workspace.
- Added double-click-to-detach as an accessibility alternative to dragging.
- Added tab reordering within the original tab bar.
- Saved detached-window geometry and detached state per task workspace and restored it when the task is reopened.
- Added off-screen recovery when a previously used monitor is unavailable.
- Collected detached tabs before closing the owning workspace so no notebook, retrospective, or studio windows remain orphaned.
- Preserved the v10.25.2 fast-close behavior and asynchronous notebook-kernel shutdown.

# v10.25.2 - Notebook Comment Shortcuts and Fast Workspace Close

- Added VS Code-compatible line-comment shortcuts to integrated Jupyter code cells:
  - `Ctrl+/` toggles comments on the current line or selected lines.
  - `Ctrl+K`, then `Ctrl+C` comments the current line or selected lines.
  - `Ctrl+K`, then `Ctrl+U` uncomments the current line or selected lines.
- Preserved indentation while commenting and uncommenting Python code.
- Changed notebook kernels to start only when the first code cell runs.
- Made notebook kernel shutdown asynchronous so closing a portfolio milestone no longer waits for the Jupyter kernel to stop.
- Prevented duplicate studio shutdown work when a portfolio task closes.
- Replaced the retrospective draft's per-prompt delete/insert loop with one batched transaction.
- Stopped pending autosave and preview timers before task windows close.
- Removed redundant full-application refreshes after task and portfolio dialogs close; explicit task changes still refresh through their existing callbacks.
- Preserved the guided Data Cleaning Studio, per-table notebooks, retrospective restoration, Current Sprint browser, and overdue-track scheduling.

# v10.25.1 - Guided Data Cleaning Installer Repair

- Fixed the v10.25.0 installer treating the expected pre-launch absence of pandas as a fatal PowerShell error.
- Removed the unnecessary installer-time pandas import probe; the launcher already verifies and installs pandas from requirements.txt.
- Added a complete patch-install failure log with the original exception and PowerShell script stack trace.
- Preserved the full Guided Data Cleaning Studio, integrated per-table notebooks, milestone continuity, and Today’s Focus retrospective repair.

# v10.25.0 - Guided Data Cleaning Studio and Milestone Continuity

- Rebuilt **Clean and validate analytical data** as a table-by-table Data Cleaning Studio.
- Lists every configured source table with its inherited business name, purpose, grain, primary key, relationships, field definitions, null rules, key roles, uniqueness rules, valid values, known issues, and cleaning expectations from the completed Data Dictionary milestone.
- Creates one managed integrated cleaning notebook per table under `notebooks/cleaning/`.
- Added a notebook selector at the top of the Cleaning Notebook tab and saves the current notebook before switching files.
- Added direct table-to-notebook routing from the Data Cleaning Studio.
- Added **Export Raw CSV**, **Export Cleaning Package**, **Import Cleaned CSV**, processed-table validation, table summaries, and table completion review.
- External cleaned files are validated and organized under `data/processed/csv/` without overwriting raw data; replaced processed files are backed up.
- Added a project artifact registry and a **Previous Milestones** tab to downstream portfolio workspaces so later milestones can see and open the actual outputs produced earlier.
- Markdown notebook cells now open rendered by default, switch to raw Markdown on double-click, and return to rendered mode when run.
- Notebook execution scrolls to the bottom of the completed output cell; adding a new cell scrolls to the new block.
- Restored the due weekly retrospective as a protected Today’s Focus commitment on Friday, with Monday recovery for a missed prior-week retrospective. Overdue track refreshes can no longer silently displace it.
- Restored the full v10.24.6 Data Dictionary Studio implementation while preserving the v10.24.12 Current Sprint dialog and v10.24.11 overdue-task scheduling repairs.

# v10.24.12 - Current Sprint Dialog Repair

- Fixed `QListWidgetItem is not defined` when opening Current Sprint.
- Added the missing Qt import used by sprint headers and task rows.
- Applied compact Dashboard button padding and a scale-aware minimum height to prevent vertical text clipping.
- Preserved all v10.24.11 overdue-track and Today’s Focus behavior.

# v10.24.11 - Sprint Browser Reliability and Overdue Track Advancement

- Made the entire Current Sprint metric card clickable and added a visible View Sprint Tasks button.
- Added a guarded sprint-browser opener that surfaces query errors instead of failing silently.
- Added persistent recommended dates for sequential Google, Academy, SQL, Portfolio, and Applied track targets.
- Spread each track's weekly target across Monday through Friday and preserve unfinished target dates across week rollover.
- Kept the next sequential task active when its recommended date is today or overdue, even after the normal daily target was completed.
- Updated Next Tasks immediately after a predecessor completes when the new target is already due.
- Replaced the completed same-track Today’s Focus row with the newly due target while preserving historical days and manually added work.
- Preserved the v10.24.7-r1 startup IndexError repair and all v10.24.10 retrospective improvements.

# v10.24.10 - Retrospective Context and Sprint Task Browser

- Added a This Week's Milestones list inside every retrospective task, grouped by Google Course, SQL, and Portfolio.
- Included both currently assigned milestones and adaptive-track completions from the retrospective week, with names and completion status.
- Reworked retrospective autosave and close behavior so closing the window performs only a lightweight answer flush instead of regenerating Markdown and the full progress snapshot.
- Stopped pending autosave timers during close and prevented duplicate close-time saves.
- Made the Current Sprint progress ring clickable from the Dashboard.
- Added a Current Sprint dialog showing every named active assignment and completed adaptive task for the week, with direct task opening.
- Preserved the startup IndexError planner repair by leaving planner.py untouched.

# v10.24.9 - Integrated Retrospective Tasks

- Moved every weekly retrospective and the 90-day program retrospective into a guided in-app Retrospective tab.
- Added automatic progress snapshots, structured prompts, autosave, required-field validation, and one-click completion.
- Generated the Markdown retrospective record automatically from the in-app form; external editing is no longer required.
- Generated or updated Weekly Summary records whenever a weekly retrospective is saved.
- Replaced the duplicate Weekly Summary form with a direct route to the current retrospective task.
- Prevented dashboard or planner checkboxes from bypassing required retrospective prompts.
- Preserved historical Markdown records, linked artifacts, study sessions, task schedules, and all existing progress.

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

## 10.21.0 — True Milestones and Always-Available Get Ahead

- Consolidated the legacy portfolio checklist into 14 durable stage-gate milestones.
- Archived every removed minor task and preserved its completion history.
- Linked discovery milestones to the generated Overview/project charter.
- Reframed Complete Data Dictionary as Review and Finalize Data Dictionary.
- Added canonical artifact paths and detailed guides for every new milestone.
- Restored a settings-driven personalized Dashboard greeting.
- Centered the visible sidebar logo by trimming transparent asset padding.
- Made Get Ahead available before the daily plan is complete.
- Added prerequisite-ready Get Ahead work to Next Tasks and a full task browser.

## 10.21.2 — Robust Milestones and Get Ahead Installer

- Consolidated the legacy portfolio checklist into 14 durable stage-gate milestones.
- Archived every removed minor task and preserved its completion history.
- Linked discovery milestones to the generated Overview/project charter.
- Reframed Complete Data Dictionary as Review and Finalize Data Dictionary.
- Added canonical artifact paths and detailed guides for every new milestone.
- Restored a settings-driven personalized Dashboard greeting.
- Centered the visible sidebar logo by trimming transparent asset padding.
- Made the Get Ahead browser available before the daily plan is complete.
- Prevented browser candidates from appearing in Next Tasks automatically.
- Added Get Ahead work to Next Tasks only after Start and Add to Today is chosen.
- Pinned the gradient Get Ahead button to the bottom of the Next Tasks card.
- Added scale-safe button height and restored greeting emojis.

