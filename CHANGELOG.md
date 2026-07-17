# Changelog

## 10.0.5 - 2026-07-17

- Corrected Dashboard action buttons so their fixed responsive heights can never be smaller than the scaled font and stylesheet size hint, preventing vertically clipped labels on Start Study Session, Pause, Reset, Log, View Full Summary, and Mission Control actions.
- Added compact Dashboard-specific button padding that retains clear hover and pressed states without consuming excessive no-scroll card height.
- Rebuilt the sidebar navigation as a flexible equal-height region so links expand into the available space between the logo and progress cards instead of leaving a large empty vertical band.
- Added a Settings action to rebuild the current day’s frozen Today’s Focus snapshot from live progress and adaptive planning data.
- Snapshot rebuilding preserves task completions, study sessions, notes, achievements, previous days, and restores the original snapshot automatically if regeneration fails.
- Added regressions for scaled button height, Study Session control containment, flexible sidebar navigation, Settings action availability, successful daily snapshot replacement, and failed-rebuild rollback.

## 10.0.4 - 2026-07-17

- Removed the Dashboard vertical scroll path so the front page always fits its live viewport.
- Recalculated Dashboard row heights from the actual client height, including Windows display-scaled window sizes.
- Added a dedicated timer stage based on the circular timer's real scaled dimensions, preventing overlap with Study Session controls.
- Kept page-header dates on one line; compact layouts move the complete date below the title rather than wrapping it.
- Added regressions for the 1680×944 display-scaled layout, timer/control separation, and one-line dates across every page.

## 10.0.3 - 2026-07-17

- Removed the large vertical bands that could appear between Dashboard rows on shorter or display-scaled screens.
- Changed Dashboard rows to wrap tightly around their cards instead of allowing empty QGridLayout hosts to absorb spare height.
- Added fluid row-height interpolation so available vertical space grows the metric, priority, analytics, and footer cards themselves.
- Preserved the complete no-scroll Dashboard and sidebar at 900×620, 1024×768, 1280×800, 1366×768, and 1536×1020.
- Added regression checks that ensure visible Dashboard rows remain separated only by the configured responsive spacing.

## 10.0.2 - 2026-07-17

- Kept every Dashboard card visible without vertical or horizontal scrolling across the supported 900×620 through 1536×1020 desktop-size matrix.
- Added height-aware sidebar density so navigation, Current Streak, Total Study Time, and the footer also remain visible without scrolling at every supported front-page size.
- Added height-aware Dashboard density modes that compact card heights, typography, spacing, charts, timers, task rows, focus rows, badges, and secondary details while preserving the complete front-page card set.
- Rebuilt circular progress-ring painting to center its text dynamically, scale safely with card height, elide long labels, and prevent vertically clipped values or captions.
- Rebuilt the circular Study Session timer painting with the same density-aware sizing and clipping protections.
- Removed the transient ghost pill/backdrop in Learning lesson headers by safely hiding and reinserting embedded course extension widgets during content rebuilds.
- Made rounded lesson subtitle and subheader pills calculate and receive their full wrapped height, preventing vertical clipping in Applied Labs, Exercise Packs, and DuckDB Exercises.
- Preserved wide presentation at larger sizes while using compact and ultra-compact density rules at shorter displays instead of forcing Dashboard scrolling.
- Added regression coverage for a no-scroll Dashboard size matrix, metric-ring containment, embedded-widget header placement, and rounded-pill height-for-width behavior.

## 10.0.1 - 2026-07-17

- Completed a full responsive-layout polish pass across every main application tab and the unified Task Workspace dialog.
- Lowered the supported minimum window size to 900×620 while keeping all main pages free of horizontal overflow.
- Replaced the dashboard's forced wide layout with true wide, medium, and compact breakpoints, including single-column compact cards and adaptive action labels.
- Fixed stale QGridLayout row and column stretch values that could leave compact cards constrained to half width after resizing.
- Changed reusable cards and long task rows to ignore oversized content hints, wrap at narrow widths, and expand vertically instead of forcing hidden horizontal overflow.
- Added dynamic application-wide typography and inline-style scaling, responsive sidebar widths, and scalable ring/timer painting.
- Made every main page vertically scroll-safe with adaptive margins, headers, card grids, action rows, forms, and tab workspaces.
- Reflowed Exercise Packs and DuckDB Exercises into tall outer-scrollable compact workspaces so navigation, Learn, and Practice receive usable heights instead of compressed nested panes.
- Added responsive layouts for Learning, Portfolio, SQL Companion, Study Session, Job Readiness, Applications, Weekly Summary, Publish & Git, Task Workspaces, and Settings.
- Fixed transient duplicate course titles when lesson content is rebuilt quickly during navigation or resizing.
- Made long list entries and dashboard completion summaries wrap without clipping.
- Added responsive regression coverage for resize cycles, breakpoints, full-width compact cards, guided SQL workspace heights, course-title rebuilding, and horizontal-overflow prevention across every page.

## 10.0.0 - 2026-07-16

- Rebuilt Exercise Packs around lesson-linked practice questions so every lesson immediately offers one or more concept-specific SQL questions in the Practice card.
- Added per-lesson question selection, question numbering, independent saved SQL, notes, results, hint progress, and completion state.
- Changed new Exercise Pack answers to load only an intentionally minimal starting template; lesson examples and official solutions are never inserted automatically.
- Added progressive Exercise Hint behavior and a separate solution walkthrough that preserves the learner's work unless Copy to Editor is explicitly chosen.
- Strengthened Check Answer with isolated in-memory DuckDB execution, read-only protections, expected-result comparison, ordering rules, required SQL patterns, and nested-query validation.
- Added a reusable line-numbered SQL editor with syntax highlighting, current-line emphasis, error-line emphasis, and DuckDB line navigation across Exercise Packs, DuckDB Exercises, Applied Labs, and Interview Problems.
- Added editable Interview Problem submissions, in-app saving, completion validation, submission-file reopening, and duplicate-resistant Demonstrated Evidence creation from original learner work.
- Preserved exact DuckDB Exercise and Interview Problem routing from Dashboard and roadmap actions.
- Restored completed Today’s Focus styling with checked state, muted strikethrough text, disabled actions, and safe refresh behavior.
- Reworked automatic backups to use consistent SQLite snapshots, SHA-256 duplicate detection, newest/daily/weekly retention groups, and recoverable pruning reports.
- Added Settings storage reporting, Clean Old Backups, and Open Data Folder controls.
- Updated the Subqueries, Joins, and standard template packs to schema-compatible v2.0.0 content with every lesson mapped to practice questions and answer-safe starter templates.
- Added v10 regression coverage for pack validation, official solutions, lesson-question mapping, starter-template safety, editor line navigation, backup deduplication and retention, application startup, routing, Interview Problem evidence, and package cleanliness.
- Added a cumulative, idempotent v10 installer that validates the repository, skips identical files, backs up every replaced file, and preserves local progress, submissions, databases, and custom packs.


## 9.6.3 - 2026-07-16

- Fixed Exercise Pack navigation when Start Course, Continue, or direct selection targets an already-highlighted learning-path row.
- Restored interactive Practice content after direct exercise navigation and added a runnable lesson SQL sandbox instead of leaving the Practice card disabled.
- Added responsive course breakpoints that stack lesson columns and reduce spacing at narrow Learn-card widths.
- Routed DuckDB roadmap tasks directly to their exact DuckDB exercise.
- Routed SQL interview tasks directly to their exact Interview Problems selection.

## 9.6.2 - 2026-07-16

- Added a comprehensive Exercise Pack authoring guide covering pedagogy, layout, styling, validation, recommendations, versioning, and installation testing.
- Added a dedicated visual style guide and pre-release quality checklist.
- Added a copyable standard-pack template with a lesson, exercise, dataset, solution, and manifest.
- Added the standalone SQL Joins: Match, Preserve, and Combine Rows pack for manual ZIP or folder installation testing.

## 9.6.1 - 2026-07-16

- Made the DuckDB Learn and Practice cards genuinely resizable with a visible, persistent splitter.
- Removed horizontal clipping from native course titles, subtitles, code cards, tables, and wrapped lesson content.
- Split DuckDB submissions into independently editable question answers while preserving the standard repository SQL submission file.
- Added per-question SQL, notes, results, validation state, and remembered question selection.
- Updated Run Question and Check Question to operate only on the selected question; Check Exercise and Submit Exercise still validate all answers.
- Removed Question 1 text from the exercise-level subtitle and replaced it with question and dataset counts.
- Fixed hidden-tab header controls so the Applied Labs status dropdown appears beside Bookmark instead of leaving an empty floating pill.

## 9.6.0 - 2026-07-16

- Reworked Exercises into a permanent three-column layout with course navigation, Learn, and Practice visible together.
- Reworked Applied Labs into a single Learn workspace with status in the header and submission actions in the footer.
- Set the default Applied Labs divider to one-third navigation and two-thirds Learn.
- Added a native three-column DuckDB Exercises workspace to SQL Companion using the same course styling as Exercise Packs.
- Added read-only in-app DuckDB execution for the selected exercise question.
- Added validation-file result checking for individual questions and complete exercises.
- Added standard submission saving and gated Submit Exercise completion tracking.
- Preserved the existing DuckDB exercise folders, starter files, datasets, validation checkpoints, notes, evidence, and roadmap synchronization.

## 9.5.0 - 2026-07-16

- Rebuilt Exercise Pack and Applied Lab learning pages with shared native Qt course components to closely match the approved learning-site reference.
- Added breadcrumb navigation, installed-pack selector, course overview, pack progress, lesson navigation, bookmarks, page menus, code Copy controls, polished tables, and reference-style lesson footers.
- Replaced the monolithic ExerciseLearnView QTextEdit renderer, eliminating its repeated Qt stylesheet parse warnings.
- Added matching collapsible library behavior to Applied Labs, including the vertical rail, side-by-side Learn and Practice cards, centered divider, remembered state, and preserved selections.
- Kept existing SQL execution, checking, hints, notes, progress, pack installation, and adaptive roadmap behavior intact.

## 9.4.9 - 2026-07-16

- Fixed the startup crash caused by refreshing deleted legacy Applied Labs filter widgets after the new course-style Applied Labs tab replaced the old page.
- Added a guarded refresh path that uses the new AppliedLabsWidget and calls the legacy refresh only as a compatibility fallback.
- Retained the legacy page wrapper during the transition so any remaining compatibility methods cannot reference deleted Qt controls.
- Added upgrade and idempotence regression tests for repositories already patched with v9.4.8.

## 9.4.8 - 2026-07-16

- Matched Exercise Pack lesson headers to the approved learning-site reference with compact type pills, large titles, subtle subtitle labels, calmer section headings, and quiet divider lines.
- Added lesson and exercise subtitle metadata to the bundled SQL Subqueries pack v1.1.2.
- Replaced the legacy Applied Labs form tab with a polished Learn/Practice workspace using the same course renderer as Exercise Packs.
- Added an isolated in-memory DuckDB SQL workspace for SQL Applied Labs, including automatic dataset views, multi-statement execution, result tables, saved submissions, and lab-specific automated rubric checks.
- Added sandbox protections that block external database, file-export, extension-loading, and arbitrary file-reader commands.
- Added DuckDB to the application requirements while preserving existing progress and submissions.

## 9.4.7 - 2026-07-16

- Replaced platform-default Markdown rendering with a dependency-free course-material renderer for Exercise Pack lessons, guided exercises, and solution walkthroughs.
- Added boxed SQL/code examples with labeled headers, inline code chips, and lightweight SQL syntax highlighting.
- Restyled learning tables with strong header bands, alternating rows, cleaner spacing, numeric alignment, and subtle row dividers instead of plain full-cell borders.
- Added course-style title cards, section headers, accent bars, divider lines, callout cards, and more consistent reading spacing.
- Upgraded the bundled SQL Subqueries pack to v1.1.1 and converted sample outputs into polished data tables.

## 9.4.6 - 2026-07-16

- Upgraded the bundled SQL Subqueries pack to v1.1.0 with seven consistently structured lessons, twelve enriched exercises, progressive build steps, expected output shapes, common mistakes, reflection prompts, stretch goals, and stage-by-stage solution walkthroughs.
- Added result-shape teaching throughout the pack and a clearer transition between subqueries, joins, and CTEs.
- Polished the Exercise workspace with themed learning typography, styled SQL and notes editors, state-aware feedback banners, clearer result tables, richer learning-path rows, and a dedicated solution walkthrough dialog.
- Added concept-pattern validation for required SQL phrases and minimum nested SELECT counts while preserving result-based answer checking.
- Updated untouched packs to open at Lesson 1 while retaining resume behavior for in-progress learners.

## 9.4.5 - 2026-07-16

- Centered the collapsed Learn/Practice splitter on the top-level application window rather than merely dividing the remaining workspace equally.
- Grouped the existing expand arrow directly after the rotated Installed Packs label instead of placing it at the bottom of the collapsed rail.
- Increased and stabilized the Dashboard exercise suggestion card height so its border, text, and Practice button are no longer vertically clipped.
- Added regression coverage for app-window centering, collapsed rail control order, and suggestion-card geometry.

## 9.4.4 - 2026-07-16

- Fixed blank Learn and Practice cards by explicitly revealing the real workspace pages after they are removed from the tab widget and reparented.
- Added a counterclockwise vertical **Installed Packs** label to the collapsed rail.
- Reused the existing arrow button by moving the same control between the expanded header and collapsed rail.
- Kept the rail at 42 pixels while preserving the original expanded layout and all active exercise state.
- Expanded regression coverage for visible reparented content and reuse of the existing arrow control.

## 9.4.3 - 2026-07-16

- Reduced the collapsed Installed Packs card to an arrow-only rail for maximum workspace width.
- Added a side-by-side collapsed workspace with Learn in a left card and Practice in a right card.
- Restored the original single Exercise Workspace with Learn and Practice tabs whenever Installed Packs is expanded.
- Preserved the active lesson or exercise and the preferred tab while switching layouts.
- Expanded regression coverage for workspace reparenting, arrow-only collapse, and expanded-layout restoration.

## 9.4.2 - 2026-07-16

- Made the Installed Packs card in Learning → Exercises collapsible.
- Added a compact collapsed header that keeps the active pack and exercise selected while giving the Learn and Practice workspace more width.
- Remembered the collapsed state and the user's preferred expanded width between app launches.
- Added regression coverage for the collapsible layout and persisted settings keys.

## 9.4.1 - 2026-07-16

- Fixed the SQL Subqueries pack recommendation for Google Course 5, Module 3; the original rule incorrectly targeted Module 1.
- Added a persistent canonical concept-tag audit for every stored task, independent of the frozen daily task snapshot.
- Added exact task mappings for Google courses/modules, all verified DataCamp chapters, SQL Companion problems, DuckDB exercises, applied labs, and portfolio milestones.
- Added concept-based Exercise Pack triggers and automatic removal of stale tags when a task changes.
- Added task-tag audit documentation and regression tests for Module 3, DataCamp subqueries, exact SQL mappings, full-catalog coverage, and snapshot independence.

## 9.4.0 - 2026-07-16

- Added a Learning → Exercises tab for portable, manually installable exercise packs.
- Added schema validation, safe zip extraction, versioned updates, independent progress persistence, hints, solutions, and result-based SQL checking.
- Added live Dashboard exercise recommendations that are recalculated outside the frozen daily task snapshot.
- Bundled SQL Subqueries: Foundations to Advanced with 5 lessons, 12 ramped exercises, 4 small datasets, and validated solutions.
- Documented the public Exercise Pack Format v1 for future ChatGPT-generated packs.

This file is the single maintained changelog for the project.





















































## 9.3.25

- Added logical accomplishment identities for achievements
- Normalized punctuation and legacy prefixes such as SQL Challenge:
- Made SQL Companion completions the canonical SQL activity achievement
- Removed matching generic SQL Challenge achievements
- Made project-task completions the canonical portfolio activity achievement
- Removed matching generic Portfolio Milestone achievements
- Collapsed repeated completed sprint rows with the same category and label
- Reconciled and removed existing duplicate managed achievements at startup
- Preserved cumulative milestone badges such as First Query and On Track
- Counted roadmap-task milestone progress using unique logical tasks
- Added achievement-duplication diagnostics to track health
- Preserved completed tasks, SQL progress, portfolio progress, evidence,
  completion history, dates, and study records
- Documented why a two-item focus plan is valid when DataCamp and portfolio
  weekly quotas are already complete

## 9.3.24

- Condensed the Today’s Plan Complete banner
- Reduced the completed banner from 48 to 38 pixels
- Shortened Continue & Get Ahead to the task name and one concise reason
- Removed repeated Today, Week, course-alignment, and pacing text from the
  visible optional row
- Preserved the full optional-task detail in tooltips
- Replaced the multi-item tomorrow text with one likely track and a compact
  “+ N more” summary
- Preserved the full Tomorrow Preview dialog
- Hid the redundant Total Estimated Time and Tasks footer boxes after the
  required daily plan is complete
- Kept the normal incomplete-day Today’s Focus layout unchanged
- Preserved stable daily plans, optional progress, and adaptive scheduling

## 9.3.23

- Fixed the empty 0/0 Today’s Focus state after upgrading on an already
  completed day
- Added upgrade-safe empty-plan completion detection
- Recognized completed track events and SQL completions recorded today
- Recognized today’s logged study sessions when no task completion record
  was available
- Showed Today’s Plan Complete whenever no required eligible work remains
- Changed the empty completed footer from 0 tasks to Complete
- Replaced meaningless 0h 00m with a neutral dash when no original plan
  existed
- Kept optional work active without causing the empty base plan to reopen
- Added future-week prerequisite-ready tasks to Continue & Get Ahead when
  the current week is fully exhausted
- Allowed Tomorrow Preview to show those future-ready priorities
- Preserved the stable-plan, no-refill, duplicate-prevention, and adaptive
  prerequisite behavior

## 9.3.22

- Froze the original Today’s Focus assignments after the first daily plan
  is generated
- Prevented completed focus slots from being silently refilled
- Preserved completed adaptive assignments even when their sprint row is
  reused for the next target
- Kept completed items visible as part of the saved daily plan
- Added a Today’s Plan Complete success state
- Added completed task count and planned-time summary
- Added one optional Continue & Get Ahead recommendation
- Added a Start action for optional extra work
- Kept optional work separate from the required daily target
- Prevented optional extra work from becoming missed-yesterday carryover
- Added a non-binding Tomorrow Preview with up to three likely priorities
- Added exact track and target identity to stored daily-focus assignments
- Updated focus health checks to distinguish a new optional target from a
  duplicate assignment
- Preserved adaptive prerequisites, weekly pacing, workspace rules, and
  duplicate prevention

## 9.3.21

- Added logical-assignment deduplication to Today’s Focus
- Prevented roadmap fallbacks from duplicating active adaptive tracks
- Added a final semantic deduplication pass before saving daily focus
- Deduplicated Next Tasks by active track and normalized task identity
- Preferred active adaptive tasks over older unlinked roadmap rows
- Made legacy Google Course checklist tasks subordinate to the adaptive Google track
- Preserved the independent DataCamp track as the only active DataCamp assignment
- Removed Task Workspace Open controls from Google and DataCamp rows
- Excluded all bracketed Google Course tasks from Task Workspaces
- Excluded Google course review/checklist tasks and DataCamp tasks from Task Workspaces
- Added migration cleanup for accidental external-learning workspace records
- Preserved linked Study Session task history while removing unnecessary workspace links
- Added duplicate-focus and external-workspace checks to track health reporting
- Deduplicated the Task Workspaces list by workspace or normalized task identity
- Preserved workspace files on disk during cleanup

## 9.3.20

- Restored Today's Focus to its original compact 286-pixel card height
- Restored Next Tasks to its original compact 286-pixel card height
- Restored Study Session to its original compact 286-pixel card height
- Prevented the three primary dashboard cards from extending into the
  Growth Over Time and Achievements row
- Restored compact 38–41-pixel task and focus rows
- Reduced workspace Open controls from 68×32 to 60×28 pixels
- Kept dedicated hover styling and smooth hover animation
- Kept pressed styling and click animation
- Preserved Task Workspaces above Settings
- Preserved the sidebar Current Streak and Total Study Time corrections

## 9.3.19

- Moved Task Workspaces immediately above Settings in the sidebar
- Reduced sidebar navigation spacing and button padding
- Added stable fixed navigation-button heights
- Reduced unused top and bottom sidebar margins
- Added minimum heights for Current Streak and Total Study Time cards
- Prevented the streak and study-time fields from being compressed or
  vertically clipped at the supported minimum window size
- Expanded Today's Focus and Next Tasks rows for full button visibility
- Replaced the clipped generic Open controls with dedicated 68×32 controls
- Added distinct hover styling and smooth hover opacity animation
- Added pressed styling and click opacity animation
- Increased the primary dashboard-card row height for five Next Tasks
- Preserved all page indices, shortcuts, data, workspaces, and navigation
  behavior

## 9.3.18

- Automatically linked DataLemur solution scripts to matching Task Workspaces
- Linked solutions as soon as they are created or opened
- Reconciled solution artifacts before adaptive SQL tasks advance
- Repaired existing historical SQL workspaces when opened
- Used saved `sql_practice.solution_path` with a standard-path fallback
- Referenced original solution files without copying or duplication
- Automatically linked DuckDB and Applied Lab submissions
- Marked app-managed links as Automatic in the artifact list
- Prevented accidental removal of automatic artifact links
- Preserved manually added artifacts and their removal behavior
- Excluded Google Certificate and DataCamp tasks from Task Workspaces
- Preserved Google and DataCamp progress and Study Session tracking
- Added database migration for managed artifact metadata
- Preserved user databases, submissions, solutions, and portfolio work

## 9.3.17

- Added a unified Task Workspace for every sprint task
- Added a Task Workspaces sidebar page with week, status, and search filters
- Added Open Workspace actions to Today's Focus and Next Tasks
- Added workspace actions and double-click access in Adaptive Planner
- Added workspace access from Sprint Backlog and Recent Study Sessions
- Added direct Weekly Review actions for the study plan and retrospective
- Added automatic task-type recognition and document routing
- Routed Applied Labs and DuckDB tasks to their existing saved submissions
- Routed retrospective tasks to weekly RETROSPECTIVE.md files
- Added on-demand weekly STUDY_PLAN.md creation
- Added task-specific Markdown workspaces for learning, SQL, portfolio, and general work
- Added in-app document editing, autosave, reload, external editor, and folder access
- Added task status, priority, estimate, energy, scheduling, and deferral controls
- Added prerequisite-aware task completion and detailed task-editor access from the workspace
- Preserved Applied Lab and DuckDB submission validation when completing from a workspace
- Added linked artifact files and folders
- Added task-linked Study Sessions and session-to-workspace navigation
- Added linking and unlinking of existing study sessions
- Added historical workspace identities for adaptive track assignments
- Added generated Weekly Summary synchronization into retrospective documents
- Added task workspace database tables and Study Session linkage fields
- Preserved the existing adaptive scheduler, evidence, achievements, submissions, and user data

## 9.3.16

- Added 15 prerequisite-driven Applied Labs
- Expanded the Applied Labs library from 21 to 36 exercises
- Added a seven-lab Statistics branch
- Added descriptive statistics and distribution analysis
- Added sampling bias and representativeness
- Added confidence intervals and margin of error
- Added hypothesis testing
- Added A/B-test and practical-significance analysis
- Added correlation-versus-causation reasoning
- Added simple linear-regression interpretation
- Added a four-lab Business Patterns branch
- Added funnel, cohort retention, churn, and forecast-variance analysis
- Added a two-lab Data Workflow branch
- Added local paginated REST API and JSON ingestion
- Added a raw-to-staging-to-clean-to-analytics pipeline
- Added a Responsible AI branch and flawed-analysis audit
- Added optional Power BI performance optimization after the core sequence
- Added synthetic statistics, business-pattern, API, pipeline, and AI-audit datasets
- Added instructions, starters, validation guides, and saved submissions
- Added 18 new tracked analyst skills and evidence routes
- Spaced new work across Weeks 4–12
- Expanded adaptive branch priority rules to ten branches
- Increased Applied Labs allocation from 5% to 8%
- Added two-lab weekly targets from Week 4 at 15+ study hours
- Added three-lab targets in Weeks 7–10 at 20+ study hours
- Preserved the Google Certificate as the primary 67% allocation
- Added a Statistics learning-progress card
- Preserved user data, submissions, achievements, and portfolio work

## 9.3.15

- Added Applied Labs as a dedicated adaptive track
- Added six independent prerequisite-driven branches
- Added Power BI, Excel, pandas, Communication, SQL Quality, and Timed
  Requests branch sequences
- Added Auto branch selection based on roadmap week and current evidence
- Added manual branch pinning without bypassing prerequisites
- Limited the active schedule to one Applied Lab at a time
- Reserved at most one Today’s Focus slot for Applied Labs
- Prevented Applied Labs from replacing the Google Certificate priority
- Added one weekly lab target and optional two-lab targets in Weeks 7–10
  for study budgets of at least 18 hours
- Carried unfinished labs across week boundaries
- Preserved task status, estimates, energy, priority, and deferral during
  carryover
- Blocked nonselected lab tasks from normal scheduling
- Hid nonselected managed labs from Sprint Backlog
- Added active-track, next-lab, branch, and pacing details to Learning
- Added readiness and lock reasons to every Applied Lab
- Routed workspace completion through adaptive events and weekly pacing
- Added branch-aware undo that only restricts later work in the same branch
- Preserved submissions, evidence, achievements, Study Sessions, and user data

## 9.3.14

- Added an Applied Labs tab to Learning Dashboard
- Added 21 guided exercises across Weeks 3–11
- Added six Power BI labs from import through deployment planning
- Added an end-to-end Excel analyst workbook challenge
- Added four compact pandas bridge labs
- Added executive summary, walkthrough, and decision-log exercises
- Added a reusable SQL validation checklist
- Added three broken-analysis diagnostic exercises
- Added three timed analyst requests
- Excluded BigQuery exercises as requested
- Added instructions, starters, validation guides, and datasets
- Added saved submissions under practice/applied/submissions
- Added category filtering and full lab workspaces
- Added Not Started, In Progress, and Completed tracking
- Added automatic roadmap tasks without overwriting existing progress
- Migrated compatible existing Power BI, pandas, and stakeholder tasks
- Added applied-lab concept evidence to Skills & Concepts
- Added completed labs automatically to Demonstrated Evidence
- Added Completion History rollback for applied-lab progress and evidence
- Preserved certificate-first pacing, Study Sessions, and user data

## 9.3.13

- Removed stale achievements when their qualifying completion is undone
- Reconciled task, project, SQL, session, application, and milestone badges
  against current verified evidence
- Removed the Data Science Skills task achievement after restoring the task
  to Not Started or In Progress
- Removed SQL Problem Solved when the SQL record is no longer Completed
- Recalculated First Query, SQL Starter, SQL Builder, and SQL Momentum
- Preserved unrelated achievements whose evidence still exists
- Counted only Completed SQL records in achievement progress
- Counted only Completed SQL records in Dashboard SQL Progress
- Counted only Completed SQL records in Job Readiness
- Counted only Completed SQL records in Readiness Coach
- Counted only Completed SQL records in weekly summary generation
- Updated achievement guidance to explain reversible progress badges
- Preserved SQL files, notes, mastery, Study Sessions, and user data

## 9.3.12

- Added Interview Problems and DuckDB Exercises tabs to SQL Companion
- Added a browsable 12-exercise DuckDB library
- Added instruction, starter SQL, validation, and dataset-folder buttons
- Added Create / Open Submission with saved copies under submissions
- Added Not Started, In Progress, and Completed exercise tracking
- Added exercise notes and stored submission paths
- Warned when a completed submission still matches its starter
- Updated matching sprint tasks from the exercise workspace
- Accepted Exercise-tab completions as SQL concept evidence
- Added completed exercises automatically to Demonstrated Evidence
- Reversed exercise progress and auto-evidence through Completion History
- Added Demonstrated Evidence instructions and examples
- Added validation for required evidence fields
- Added View Selected and double-click evidence details
- Preserved Study Sessions, task editing, user data, and project work

## 9.3.11

- Made Job Readiness content vertically scrollable
- Kept the Job Readiness heading outside the scrolling content
- Prevented Skills & Concepts from compressing the upper card grid
- Added minimum heights to all four upper readiness cards
- Added fallback guidance when Readiness Coach has no recommendations
- Prevented Readiness Coach recommendation panels from collapsing
- Gave every Evidence Coverage row a fixed usable height
- Kept coverage dividers to a single pixel
- Gave Continue Highest-Impact Task a fixed usable height
- Preserved concept evidence, task editing, Study Sessions, and user data

## 9.3.10

- Replaced DataCamp-only SQL unlocks with concept evidence
- Accepted completed Google Course 5 for SQL fundamentals and aggregation
- Accepted completed DuckDB exercises for the concepts they cover
- Accepted completed SQL problems only for their required concepts
- Prevented basic evidence from unlocking joins, CTEs, or windows
- Allowed Data Science Skills to unlock from any approved aggregation source
- Kept Histogram of Tweets locked until aggregation and CTE evidence exist
- Added Skills & Concepts to Job Readiness
- Added Learned, In Progress, and Locked concept tabs
- Displayed exact evidence and approved unlock routes
- Included the next locked SQL problem in SQL Companion
- Preserved task editing, Study Sessions, user data, and project files

## 9.3.9

- Fixed restored tasks not displaying their new Sprint Backlog status
- Fixed restored tasks failing to return to the active schedule
- Detected completion using task flags, metadata, adaptive events, and SQL records
- Recovered exact adaptive identity for completed tasks with no active link
- Removed the hidden second track synchronization inside Dashboard refresh
- Made non-blocked editor statuses explicitly restore prerequisite readiness
- Added task schedule eligibility checks after every edit
- Confirmed `Added back to the active schedule` when the task is eligible
- Explained why a task is not scheduled when deferred, out of week, or locked
- Displayed `🔒 Locked` in Sprint Backlog for unmet prerequisites
- Preserved the exact edited row selection after adaptive task relinking
- Preserved Study Sessions, SQL gating, undo history, and user data

## 9.3.8

- Fixed the remaining task-editor refreshed-values mismatch
- Changed task editing to synchronize first and write user values last
- Resolved edited adaptive tasks by exact track and target identity
- Handled legacy week and task-label normalization before the final write
- Prevented the final editor refresh from running a second adaptive sync
- Added field-by-field diagnostics if a database write ever differs
- Added a persistent high-contrast Sprint Backlog selection style
- Kept the selected backlog row highlighted when the list loses focus
- Preserved the selected task when Sprint Backlog refreshes
- Added selection guidance and task-detail tooltips
- Preserved Study Sessions, completion undo, SQL gating, and user data

## 9.3.7

- Fixed Edit Selected Task changes being overwritten after Save
- Preserved adaptive task status, priority, duration, energy, and deferral
  while the same assignment remains active
- Reset adaptive defaults only when the track advances to a new assignment
- Added database read-back verification after task edits
- Added a clear saved-values confirmation in the status bar
- Added task IDs as QListWidget item data instead of relying only on text
- Added Cancel and Save Changes controls to the editor
- Automatically assigned tomorrow when Deferred is selected without a date
- Cleared stale deferred dates when another status is selected
- Preserved task edits when undoing a completion and re-linking the task
- Fixed Today’s Focus footer boxes stretching vertically
- Added a flexible spacer above the compact focus footer
- Preserved adaptive pacing, Study Sessions, SQL gating, and user data

## 9.3.6

- Added Completion History / Undo to Adaptive Planner
- Listed completed tasks across every roadmap week
- Included SQL Companion completions without visible sprint rows
- Reversed exact task, track-event, SQL, and milestone evidence on undo
- Protected sequential Google, DataCamp, and portfolio rollback order
- Preserved SQL solution files, notes, mastery, and review dates
- Bound SQL completion to the exact `problem:<title>` active task
- Prevented one SQL problem from completing the next activated problem
- Repaired false adaptive completions created by the old orphan-task logic
- Changed detached adaptive tasks from auto-completed to safely blocked
- Routed Edit Task completion changes through the same safe completion APIs
- Preserved active Study Sessions, user data, DuckDB work, and VFX files

## 9.3.5

- Added a Monday recovery window for missed Friday retrospectives
- Surfaced the previous week's incomplete retrospective in Today’s Focus
  and Next Tasks on Monday
- Labeled the recovered item `Missed Friday`
- Kept retrospectives hidden on Saturday and Sunday
- Returned missed retrospectives to backlog-only status after Monday
- Restricted calendar gating to retrospective deliverables rather than all
  Review-category tasks
- Preserved adaptive pacing, SQL gating, Study Sessions, and user data

## 9.3.4

- Restricted weekly retrospective recommendations to Fridays
- Kept retrospective tasks accessible in the backlog on other days
- Prevented Review tasks from appearing in Today’s Focus before Friday
- Prevented Review tasks from moving into Next Tasks when earlier work is completed
- Applied the Friday rule to standard availability, carryover, and overflow selection
- Preserved adaptive pacing, SQL gating, Study Sessions, and user data

## 9.3.3

- Made a single SQL problem selection populate the Problem Workspace
- Preserved selected problem metadata with Qt item data instead of parsing text
- Automatically selected the current adaptive SQL assignment
- Made Open My Solution create a starter file before opening it
- Added reliable VS Code and operating-system editor fallbacks
- Made Mark Complete save the problem and advance adaptive SQL progress
- Preserved active Study Sessions during SQL completion refreshes
- Added granular, chapter-based SQL concept skills
- Added title-specific prerequisites for every SQL Companion problem
- Locked Histogram of Tweets until aggregation and CTE concepts are learned
- Prevented difficulty labels from bypassing required knowledge
- Preserved user data, layout, DuckDB exercises, and VFX project files

## 9.3.2

- Fixed task completion stopping or clearing an active Study Session
- Preserved elapsed time and running/paused timer state across task refreshes
- Preserved every unsaved Study Session form field and notes
- Accounted for time spent during a running task-completion refresh
- Restored the task-completion status message
- Preserved adaptive pacing, curriculum progress, layout, and user data

## 9.3.1

- Replaced invented DataCamp lesson names with verified course chapters
- Corrected Introduction to SQL to `Relational Databases` and `Querying`
- Added the current verified SQL, Power BI, Python, and pandas chapter path
- Included the DataCamp course name in Today’s Focus descriptions
- Updated skill unlock thresholds for the expanded chapter-based curriculum
- Replaced hard-coded daily roadmap assignments with adaptive track metadata
- Added DataCamp curriculum and task-architecture documentation
- Preserved progress, daily pacing, app layout, DuckDB exercises, and VFX data

## 9.3.0

- Added twelve guided DuckDB exercises with small CSV datasets
- Added concrete business questions and blank starter SQL files
- Added result checkpoints without completed solution queries
- Added PowerShell and Python database setup workflows for VS Code
- Replaced broad SQL concept reminders with numbered exercise assignments
- Added an idempotent migration for existing task labels and metadata
- Added DuckDB Practice headings and exercise source paths in the Dashboard
- Preserved completion state, database progress, app layout, and VFX data
- Added exercise submissions as commit-ready portfolio evidence

## 9.2.2

- Unified formatting across all Today’s Focus rows
- Put the actionable task name before pacing, status, and priority metadata
- Shortened DataCamp context to `Supports Course N`
- Shortened SQL context to `Reinforces Course N`
- Kept durations only in the right-hand time column
- Presented foundational SQL practice with the `SQL Fundamentals` heading
- Kept adaptive and ordinary sprint tasks under one shared formatter
- Preserved layout, progress data, daily pacing, and the VFX dataset

## 9.2.1

- Replaced generic `Supplemental` Today’s Focus details with specific work
  item names
- Added the current DataCamp lesson to DataCamp focus rows
- Added the assigned SQL problem to SQL Practice focus rows
- Added the current Google course and module to Google focus rows
- Added the active milestone to Portfolio focus rows
- Preserved daily/weekly pacing context, layout, progress, and dataset

## 9.2.0

- Added hybrid daily pacing to Dashboard Next Tasks
- Showed another sequential item only while more work remains due today
- Suppressed daily-complete tracks until tomorrow
- Suppressed weekly-complete tracks until the next week
- Applied pacing limits to Today's Focus and carryover items
- Kept catch-up quotas stable while tasks are completed
- Added Today completed/target indicators to track details
- Added completion messages explaining when the next item returns
- Preserved the existing layout, progress database, and VFX dataset

## 9.1.3

- Fixed the PySide6 `CheckState` conversion error
- Updated `VisibleCheckBox` to emit `Qt.Checked.value` or
  `Qt.Unchecked.value`
- Fixed Dashboard Next Tasks checkbox-state comparison
- Fixed Portfolio Workspace milestone checkbox-state comparison
- Preserved the v9.1.2 layout, data, progress, and completion behavior

## 9.1.2

- Fixed Next Tasks rows not disappearing reliably after checking them
- Hid completed rows immediately before database synchronization
- Queued dashboard completion until the checkbox event finishes
- Ignored unchecked-state events in the completion handler
- Disabled the checkbox while completion is processing to prevent double clicks
- Restored the row and displayed an error if completion fails
- Detached dynamic widgets immediately during dashboard refresh
- Preserved the complete existing layout and VFX dataset package

## 9.1.1

- Made Google certificate work unconditionally first in Today’s Focus
- Added deterministic Google, DataCamp, SQL, Portfolio, and general ordering
- Changed skill unlocks to require completion of the source Google course
- Distinguished prerequisite-locked SQL from a completed SQL track
- Added locked SQL explanations instead of silently ending recommendations
- Added automatic repair of stale, orphaned, and completed active-track links
- Added internal track-engine health reporting
- Recorded each crossed Google module during same-course manual progress updates
- Prevented manual progress rewinds from creating false completion events
- Added RELEASE_READINESS.md with edge-case coverage and known boundaries
- Preserved the complete existing UI layout

## 9.1.0

- Added adaptive certificate-first pacing without changing the finished layout
- Reserved approximately 70% of weekly study time for Google certificate work
- Calculated daily Google targets from remaining weekly work and days available
- Added on-pace, catch-up, and weekly-goal-complete states
- Adapted targets automatically to the configured weekly study-hour budget
- Aligned DataCamp descriptions with the current Google course
- Limited SQL recommendations to unsolved problems whose concepts are unlocked
- Added persistent skill-state records derived from Google, DataCamp, and SQL progress
- Added prerequisite gates for portfolio milestones
- Prevented locked portfolio work from appearing in Today’s Focus or Next Tasks
- Added precise missing-skill explanations to the existing Portfolio Learning card
- Added task-level prerequisite state and reasons without altering task layouts
- Added ADAPTIVE_PACING.md architecture documentation

## 9.0.0

- Added a backend-only modular progress architecture without changing the UI layout
- Separated Sprint Week from Google, DataCamp, SQL, and Portfolio progression
- Added persistent track state, active-task links, weekly targets, and completion events
- Made Today’s Focus pull one independent recommendation from each active track
- Made Next Tasks show active track actions regardless of the sprint week
- Added a sequential DataCamp learning track
- Made SQL recommendations advance by the next unsolved problem rather than assigned week
- Connected Portfolio recommendations directly to the next incomplete project milestone
- Added independent weekly pace reporting to the existing Learning cards
- Made Google task completion advance the current module while retaining manual correction
- Preserved the complete Dashboard, Learning, Portfolio, SQL, and navigation layouts
- Added MODULAR_TRACKS.md architecture documentation

## 8.9.3

- Restored Continue Google Course 5, Module 1 to Today’s Focus and Next Tasks
- Converted the current Google checkpoint into a persistent tracked task
- Assigned it highest Learning priority ahead of DataCamp work
- Retargeted and reopened it when course, module, or sprint changes
- Added accurate Google Course and Module source metadata
- Added Course 1, Module 1 task creation to Factory Reset

## 8.9.2

- Reconciled the active profile with documented Course 5 and Project 1 progress
- Marked completed study-plan, project-selection, audience, GitHub structure,
  charter, KPI, stakeholder, scope, and draft data-dictionary work complete
- Marked the first four Project 1 discovery milestones complete
- Removed already-completed portfolio foundation work from Next Tasks
- Replaced the hardcoded Google Module 3 task source
- Added label-aware Google, DataCamp, SQL, Portfolio, Review, and Roadmap sources
- Restored high-contrast clickable checkboxes beside every Portfolio Workspace task
- Made Portfolio Workspace checkbox changes save immediately
- Removed a legacy timer refresh that could overwrite the circular timer
- Preserved the clean Course 1 factory-reset profile for other users

## 8.9.1

- Fixed the startup crash caused by unescaped braces in the red Reset Progress stylesheet
- Added isolated stylesheet evaluation and full-window startup validation
- Preserved all roadmap, reset, achievement, timer, icon, shortcut, and active-profile data from v8.9.0

## 8.9.0

- Rebuilt the 12-week roadmap to begin at Google Course 1 with no assumed progress
- Rewrote all weekly sprint checklists for a true from-scratch learner
- Added automatic recognition of earlier Google course tasks for advanced learners
- Added a red Reset All Progress control in Settings
- Added three confirmations, including an exact typed confirmation phrase
- Added a detailed pre-reset inventory of every data category that will be cleared
- Added an automatic safety database backup before reset
- Reset now clears roadmap, portfolio, study, SQL, achievement, application,
  evidence, retrospective, summary, and date progress
- Reset preserves application preferences and existing backup files
- Packaged Dan's active profile at Week 1, Google Course 5, Module 1 so work can continue

## 8.8.0

- Converted both circular timers into real goal-based progress indicators
- Added a persistent, adjustable 5–240 minute focus goal
- Added animated grow/shrink feedback to the timer value and status on
  Start, Pause, Reset, and goal changes
- Added Ready, Focusing, Paused, and Goal Reached timer states
- Removed the hardcoded Weekly Summary sparkline fallback
- Connected the Weekly Summary sparkline to Monday–Sunday logged study hours
- Added a custom Career Accelerator PNG/ICO application icon
- Applied the icon to the PySide6 window and Windows taskbar identity
- Updated shortcut creation to build both repository and Desktop shortcuts
  with the custom icon
- Updated the batch launcher to create the branded repository shortcut when missing

## 8.7.4

- Added a distinct named achievement for every completed roadmap task or challenge
- Added category-specific Learning, SQL, Portfolio, Review, and General achievement styles
- Included week, roadmap position, and the complete task label in each accomplishment
- Added task-specific colors and icons to recent Dashboard achievement cards
- Automatically upgraded existing generic Roadmap Task Complete records in place
- Preserved the global button hover and animated click feedback from v8.7.3

## 8.7.3

- Added explicit hover highlights for standard, Primary, Secondary, Link,
  and navigation buttons
- Added pressed-state color, border, and text-position feedback
- Added application-wide opacity animation on mouse and keyboard activation
- Added pointer cursors to every button, including dynamically created dialogs
- Applied feedback automatically to current and future QPushButton controls

## 8.7.2

- Fixed vertical clipping in the five Dashboard progress cards
- Reduced the Ring component from a 122-pixel minimum to a compact 94–98-pixel height
- Repositioned the circle, percentage, title, subtitle, and status text within the smaller geometry
- Increased metric-card usable height and reduced internal padding without increasing the Dashboard footprint

## 8.7.1

- Restored colored metadata category labels in the Dashboard Next Tasks list
- Added a fixed-width right-aligned metadata column to TaskRow
- Preserved the clean text-only treatment without badge background fills
- Added distinct Learning, SQL, Portfolio, Review, and General category colors

## 8.7.0

- Rebuilt Study Session around the same circular timer used on the Dashboard
- Improved timer spacing and added a direct Use Current Time in Session Log action
- Reorganized the session form into a compact two-column layout
- Rebuilt Settings as a compact two-column control center
- Added repository and local-storage path information
- Added a future AI integration readiness panel that detects OPENAI_API_KEY
  without storing credentials or making API calls

## 8.6.2

- Removed the Dashboard scroll container
- Restored a single full-width Dashboard layout
- Enforced a 1500 × 1020 minimum window size based on the complete interface footprint
- Prevented all resizing below the supported Dashboard dimensions
- Tightened task rows, metric cards, chart height, badge height, and footer metrics
  so the complete Dashboard fits without scrolling or clipping
- Disabled compact Dashboard reflow below the full-layout dimensions

## 8.6.1

- Restored Dashboard card surfaces and button fills
- Removed responsive-container inline styles that cascaded into child widgets
- Replaced container styles with non-cascading transparency attributes where needed
- Enforced a 1024 × 720 minimum window size
- Added named Dashboard breakpoint and minimum-size constants

## 8.6.0

- Converted the Dashboard to a responsive, vertically scrollable layout
- Added wide, medium, and narrow breakpoints
- Prevented progress cards, task cards, charts, and footer controls from horizontal compression
- Prioritized Today’s Focus, Next Tasks, Study Session, Encouragement, and Mission Control in compact mode
- Reflowed metrics into 5-column, 3+2, or 2-column arrangements
- Reflowed analytics cards into 3-column, 2-column, or stacked arrangements
- Stacked Mission Control actions at compact widths
- Reduced the application minimum width from 1180 to 920 pixels

## 8.5.3

- Increased the Dashboard footer-card height so Mission Control is no longer clipped
- Reserved fixed space for the Mission Control action row
- Restored readable button labels for Continue Highest-Impact Task and View Job Readiness
- Added minimum button widths and fixed button heights to prevent text collapse

## 8.5.2

- Added the missing `QSizePolicy` import in `career_app/main.py`
- Restored Dashboard startup after the v8.5.1 layout update

## 8.5.1

- Fixed clipped title/detail lines in Today’s Focus and Next Tasks
- Added fixed-height two-line task row components
- Increased the Dashboard middle-row height to preserve all task content
- Placed the Study Session ring in a dedicated fixed-height area above the controls
- Reduced the circular timer to prevent overlap with Start, Pause, Reset, and Log
- Rebuilt the encouragement card as a compact two-line block beside the star
- Split Encouragement and Mission Control evenly across the Dashboard footer

## 8.5.0

- Rebuilt Job Readiness into compact Evidence, Coach, Highest Leverage, and Coverage panels
- Reduced the Dashboard study timer and prevented control overlap
- Added a confirmed Reset action to Dashboard and Study Session timers
- Added Dashboard Mission Control with live readiness progress and highest-impact guidance
- Added persistent achievements for every completed roadmap task, portfolio milestone,
  SQL problem, study session, and tracked application
- Expanded milestone achievements and added non-intrusive unlock notifications
- Updated Dashboard achievement cards to show recent earned rewards

## 8.4.0

- Connected Today’s Focus to the Adaptive Planner task intelligence
- Kept Learning/Learning/SQL/Portfolio roadmap slots as the ground truth
- Added daily focus history and promotion of up to two unfinished items from yesterday
- Prioritized carryover, in-progress work, task priority, and roadmap category fit
- Added roadmap fallbacks only when no real task can fill a required slot
- Restored Job Readiness and Applications to the visible sidebar

## 8.3.0

- Restored Adaptive Planner to the visible sidebar
- Connected Next Tasks View All to Adaptive Planner
- Added a functional achievements dialog
- Added selectable 7, 14, 30, and 90-day growth periods
- Added rotating quotes and encouragement without immediate repeats
- Made current streak, best streak, week activity, and study totals data-driven
- Made Weekly Summary hours, sessions, SQL count, and focus score current-week aware

## 8.2.2

- Removed obsolete version-specific changelogs and fix notes
- Removed superseded Tkinter, PowerShell, YAML, and legacy tracker files
- Consolidated launch, workflow, and repository documentation
- Updated the Windows launcher title
- Preserved all current PySide6 application features and roadmap content

## 8.2.1

- Added a local-time Dashboard greeting
- Added automatic greeting and date refresh every minute

## 8.2.0

- Completed the reference-matched Dashboard polish pass
- Added visible custom task checkboxes
- Added circular timer controls for Start, Pause, and Log Session
- Added larger progress rings, chart axes, hover details, and sparkline
- Rebalanced focus, tasks, achievements, and weekly-summary layouts
- Replaced symbol-font interface icons with emojis

## 8.0.0

- Rebuilt the Dashboard around the approved visual reference
- Added the purple-led design system, streak card, study-time card,
  focus plan, task queue, area chart, achievements, and weekly summary

## 7.0.0

- Completed the product roadmap for adaptive planning, learning,
  portfolio, SQL, study tracking, job readiness, application CRM,
  weekly review, publishing, backups, and command palette

## 5.0.0

- Added adaptive planning by available time, energy, priority, and
  deferred or blocked status

## 4.0.0

- Migrated the desktop client to PySide6 with sidebar navigation and
  a reusable dark design system

## 2.0.0

- Adopted SQLite as the working data store and added Markdown migration

## 1.0.0

- Released the consolidated desktop application
