# Career Accelerator Changelog

## v10.44.0 — Day-Assigned Focus and Weekly Gate Update

- Today’s Focus now shows every incomplete task assigned to the current day, including locked tasks in grey.
- Completed tasks are removed immediately from Today’s Focus and Next Tasks.
- Catch-up work enters Today’s Focus only after all tasks assigned to today are complete.
- Next Tasks orders today’s tasks first, then catch-up tasks, while preserving locked rows in place.
- Weekly knowledge checks are normal Friday tasks and exclude Saturday/Sunday DataCamp projects from the coursework gate.
- Weekly retrospectives remain locked until the matching knowledge check is passed.
- Weekend DataCamp projects now require the matching weekly knowledge check in addition to their existing prerequisites.
- Current and missed retrospective tasks are reconciled automatically as normal planner tasks.

# Changelog

## 10.43.4 — DuckDB planner completion exclusion hotfix

- Fixed completed DuckDB exercises returning to Today’s Focus and Next Tasks after restart.
- Added DuckDB durable completion evidence to adaptive-track completion repair.
- Made the unified planner treat DuckDB completion evidence as authoritative even if a sprint row is stale.
- Reasserted submitted DuckDB completion after the final startup track synchronization.

## 10.43.3 — DuckDB live completion and dashboard checkbox hotfix

- Fixed dashboard completion refreshes querying `category` from the wrong SQLite table.
- Prevented the `no such column: category` error after clicking a task checkbox.
- Reasserted every validated DuckDB task digest after successful exercise submission.
- Repainted DuckDB task checkmarks immediately after submission instead of waiting for restart restoration.
- Upgraded completed-exercise task restoration so an existing failed/stale validation row is repaired to the submitted answer digest.

## 10.43.2 — Durable DuckDB completion and responsive planner follow-up

- Persisted DuckDB task pass evidence in the learner database instead of relying only on local UI settings.
- Added durable DuckDB completion evidence and restored it before startup planning and track synchronization.
- Prevented routine autosave or synchronization from downgrading an already submitted exercise.
- Kept explicit Undo Completion behavior by clearing the durable exercise and task evidence only on an intentional undo.
- Includes the v10.43.1 sprint-dialog, retrospective-gate, and DuckDB submission performance corrections.

## 10.43.1 — Sprint, retrospective, and DuckDB performance

- Reduced View Sprint Tasks database work by using one canonical task-pool lookup instead of rebuilding it for each row.
- Locked weekly retrospectives until the matching Week N Knowledge Check is passed, including direct workspace routes.
- Reused unchanged passed DuckDB task validations during Check Exercise and Submit Exercise.
- Replaced full roadmap reconciliation on DuckDB submission with a targeted completion/unlock update.
- Replaced the full DuckDB workspace/application reload after submission with focused navigation and dashboard refreshes.

## 10.40.1 - Integrated Python exercises and roadmap-order numbering

- Added a dedicated **Python Exercises** tab under Learning → Practice beside SQL Interview Problems and DuckDB Exercises.
- Added an integrated local Python editor with contextual completion, Run, Check Exercise, Save Draft, Submit Exercise, printed output, error-line navigation, and Matplotlib chart capture.
- Added durable Python exercise progress, notes, local submissions, evidence records, and task-completion synchronization without uploading learner code.
- Kept all 13 Python exercises locked to their Week 8 DataCamp chapters and prior-exercise sequence.
- Renumbered all 33 learner-facing DuckDB exercises in the order they appear in the roadmap while preserving stable internal IDs, existing completion records, managed task keys, and submission compatibility.
- Updated frozen Today’s Focus titles, task workspaces, evidence labels, guides, and the DuckDB task index to use the new roadmap-order numbers.
- Preserved greyed-out prerequisite-locked supplementary tasks in Today’s Focus and the Coming Soon section in Next Tasks.

## 10.40.0 - Week-aligned SQL and Python practice

- Expanded DuckDB practice from 18 to 33 exercises and aligned every exercise to the week its DataCamp concept is taught.
- Aligned 16 SQL interview problems across Weeks 3–5 and added 13 Python exercises for Week 8.
- Kept due locked supplementary work visible as grey prerequisite guidance in Today’s Focus without making optional practice a weekly-check blocker.

## 10.39.0 - Topic-aligned Google roadmap and guided Applied Lab Studios

- Rebuilt Google Certificate scheduling around a verified 39-module, nine-course curriculum mapped to the subject taught in each roadmap week.
- Kept Google work first priority while holding future-topic modules outside Today’s Focus, Next Tasks, and Catch-Up until their assigned week.
- Preserved completed Google progress and continued to advance modules sequentially without reopening prior work.
- Added synthetic weekly-check blockers for every incomplete Google module assigned through that week, so a checkpoint cannot unlock after only the currently displayed module is finished.
- Updated Learning status and Open Current Google Task behavior to distinguish active work from modules intentionally held for a future topic week.
- Added a persisted Guided Applied Lab Studio for every Applied Lab, with five assignment-specific stages, evidence capture, artifact tracking, independent validation, and final handoff review.
- Rewrote all active Applied Lab guides to explain goals, preparation, decisions, actions, outputs, validation, evidence, common mistakes, and progressive hints without revealing finished formulas, queries, DAX, Python code, or numeric answers.
- Rebuilt beginner Google Sheets Lab 01 as four detailed, solution-safe stages aligned only to Week 1–2 spreadsheet skills.
- Kept weekly eight-question Knowledge Checks, DataCamp chapter locks, Today’s Focus, Next Tasks, and portfolio gates linked to the new roadmap.

## 10.38.0 - Beginner Lab 01 and weekly knowledge checks

- Simplified Applied Lab 01 into a four-stage beginner Google Sheets sales-summary project using only skills taught in Weeks 1–2.
- Replaced the seven-source portfolio-style workbook with two small CSV files, four tabs, one dropdown, four KPIs, one pivot table, one chart, and a short takeaway.
- Removed the screenshot and independent finance-reconciliation requirements from the first lab.
- Replaced Applied Lab status-bar confirmations with the application-wide floating notification panel so messages no longer compress the workspace.
- Restored one `Week N Knowledge Check` task for every week from Week 1 through Week 12.
- Each check contains exactly eight multiple-choice questions, requires 7 of 8 to pass, provides answer-by-answer review and targeted recommendations, and permits unlimited retakes.
- A weekly check appears only after all required work for that week and earlier catch-up work are complete.
- Later skill-dependent work remains locked until the prior week's check is passed; Google Certificate, review, and career-readiness work remain available.
- Newly ready checks are promoted into Today’s Focus and Next Tasks and generate a one-time unlock notification.

## 10.37.2 - Share-link-only Google Sheets labs

- Removed the Google account/OAuth connection requirement from Applied Lab 01.
- Replaced API-created spreadsheets with a shareable Google Sheets URL field.
- Added Save Sheet Link, Open Linked Sheet, and Open Blank Google Sheet actions.
- Career Accelerator now stores only the URL and does not read or modify the linked spreadsheet.
- Updated the lab guide, catalog, validation rubric, and submission instructions for manual CSV import and protected Raw tabs.
- Preserved existing linked Google Sheets URLs and all learner progress.

# 10.37.0

- Converted the spreadsheet Applied Lab to a Google Sheets-first workflow using the existing connected-account integration.
- Added a guided Google Sheets Studio that creates protected raw-data tabs, analysis and reconciliation structures, controls, a management summary, and a data dictionary without completing the learner’s work.
- Renumbered all 36 Applied Labs by their actual unlock order so the Week 3 Google Sheets lab is Applied Lab 01 and Power BI begins later in the sequence.
- Added a one-time, idempotent migration that preserves Applied Lab progress, notes, submissions, evidence, achievements, task links, and daily-focus references under the new lab numbers.
- Preserved legacy Excel labels and files only as migration aliases; an old Excel artifact does not satisfy the new Google Sheets artifact requirement.

# 10.36.9

- Fixed the active Applied Lab prerequisite pass immediately re-blocking the same lab after DataCamp requirements were completed.
- Applied Lab 07 now enters Today’s Focus when a locked preview slot is available and always enters the actionable Next Tasks queue before Coming Soon items.
- Added a one-time in-app notification when the active Applied Lab unlocks.
- Fixed stale daily completion markers causing Today’s Tasks to show 1/1 while the same Google task remained active.
- Preserved greyed-out DataCamp chapters in Today’s Focus and the dedicated COMING SOON divider in Next Tasks.

# 10.36.8

- Preserved greyed-out prerequisite-locked DataCamp chapters in Today’s Focus.
- Restored the dedicated COMING SOON divider in Next Tasks.
- Moved locked Focus previews beneath the Next Tasks divider instead of displaying them as active rows.
- Kept actionable Focus assignments above the divider and removed duplicate locked previews from the fixed four-row card.

# 10.36.7

- Study Session logging now saves immediately and refreshes only linked session, dashboard, readiness, achievement, and workspace surfaces instead of running a full application/Git refresh.
- Today’s Focus fills available positions with due DataCamp chapters even when an earlier chapter still locks them. Locked chapters are grey, non-actionable, and name the exact chapter that must be completed first.
- Today’s Focus keeps locked DataCamp chapters visible as grey prerequisite guidance; Next Tasks presents those chapters beneath its Coming Soon divider.
- Weekly and total study-hour displays are rounded and rendered to exactly two decimal places.

# 10.36.6

- Added explicit DataCamp chapter prerequisites to every Applied Lab, DuckDB exercise, SQL interview problem, and portfolio milestone lock.
- Applied Lab 07 now requires all Week 1–2 spreadsheet chapters before its workspace becomes active.
- Locked Applied Labs remain visible for planning but cannot create, edit, run, save, or complete submissions.
- Removed Google Certificate bypasses from Power BI and Python Applied Lab gates.
- Added a content-lock regression audit covering all gated learning surfaces.

# 10.36.5

- Changed manual Study Session duration entry from decimal hours to separate Hours and Minutes controls.
- Timer-to-log actions now convert elapsed time into hours and whole minutes while preserving decimal-hour storage for analytics.
- Added a full Excel Analyst Workbook Studio for Applied Lab 07 with seven tracked stages, stage evidence, source-file profiles and previews, workbook planning, artifact controls, and a final review gate.
- Added a polished Excel starter workbook shell with Controls, Order Analysis, Management Summary, Reconciliation, Data Dictionary, and handoff guidance sheets.
- Made the in-app Studio the primary Applied Lab 07 workspace while retaining the full written guide as reference.
- Linked Studio progress into the existing Applied Lab submission record without overwriting learner-authored content.

# 10.36.4

- Removed the redundant `DataCamp —` prefix from every DataCamp chapter task title.
- Kept frozen Today’s Focus titles synchronized with the canonical shorter chapter title.

# 10.36.3

- Fixed dashboard completion checkboxes triggering an expensive full-application refresh and Git status operation.
- Today’s Focus and Next Tasks now hide and disable both copies of an assignment immediately, then refresh only linked planning and learning surfaces.
- Fixed failed checkbox callbacks leaving tasks visually stuck or apparently incomplete.
- Fixed track repair resetting newly completed DataCamp chapters because their provider progress evidence was recorded too late.
- Added a dedicated Coming Soon divider and section label in the Next Tasks card.
- Shortened DataCamp Catch-Up metadata from `Catch-Up • DataCamp` to `Catch-Up` so more of the chapter title remains visible.

# 10.36.2

- Restored Today’s Focus tasks to the top of the four-row Next Tasks card.
- Added completion checkboxes directly to active Today’s Focus rows.
- Linked both dashboard cards to the same canonical task-completion handler.
- Preserved the frozen five-task daily snapshot while allowing newly unlocked work to remain queued behind the active focus assignments.
- Restored Open buttons for DataCamp focus and Next Tasks rows so assigned chapters launch in the browser.

# 10.36.1

- Audited the weekly plan, Today’s Focus, Next Tasks, Coming Soon, Current Sprint, completion history, and 90-day contract as one linked planning system.
- Fixed same-week overdue DataCamp chapters so they enter rolling Catch-Up without consuming the frozen daily new-task quota.
- Fixed Current Sprint grouping so canonical DataCamp chapters appear under DataCamp instead of generic Learning.
- Linked DataCamp completion history and sequential undo to the canonical chapter-progress table.
- Linked the Learning status card to real current-week DataCamp targets and completion totals.
- Fixed the Open Current DataCamp Chapter button state and tooltip refresh.
- Replaced spreadsheet, SQL, Power BI, and Python subject icons on all DataCamp chapter tasks with the DataCamp logomark.
- Added an end-to-end planning-system release audit covering routing, readiness, Catch-Up rollover, completion, undo, weekly totals, icons, and database integrity.

# 10.36.0

- Replaced Accelerator Academy with 74 individual DataCamp chapter tasks across Weeks 1–8.
- Distributed every multi-chapter course across multiple days, including the Week 7 Power BI intensive.
- Added exact chapter-level Campus browser routing without automatic completion.
- Removed the Paths destination and all active Academy curriculum, lesson, assessment, workspace, progress, and evidence systems.
- Purged Academy-owned records without converting them into DataCamp completion.
- Preserved the five-item Today’s Focus limit, ordered Catch-Up behavior, and fixed four-row Next Tasks card.
- Added DuckDB Exercises 13–18 for grain/cardinality, cohorts, window frames, set/semi/anti joins, text/date quality, and final SQL readiness.
- Preserved non-Academy learner progress during migration.

# 10.35.3

- Fixed installer rollback when preserved weekly retrospective files contained retired Academy lesson references.
- Added canonical retrospective templates for Weeks 1–12 to the cumulative payload.
- Retained all v10.35.2 coursework, Catch-Up, Knowledge Check, retrospective, and planner fixes.

# 10.35.2

- Fixed the circular gate that hid unfinished Week 1 Academy coursework behind the Week 1 Knowledge Check.
- Added explicit roadmap-week metadata to every Academy course.
- Kept overdue Academy activities and weekly checks in their original week so Catch-Up labeling and rolling replacement work correctly.
- Prevented duplicate adaptive and durable weekly Knowledge Check tasks.
- Excluded retired static Academy rows and retrospectives from pre-check blockers.
- Added weekly retrospective tasks to Weeks 9, 10, and 11.
- Corrected Spreadsheet, SQL, Power BI, Python, and pandas Academy task classification.

# 10.35.1

- Restored persistent weekly Knowledge Check tasks so a mastery gate can never block later work without showing the quiz that clears it.
- Shows locked checks as `Week N Knowledge Check` with the second line `Complete All Week N Coursework to Unlock`.
- Routes ready Knowledge Check tasks directly to the matching eight-question Academy assessment.
- Preserves canonical weekly assessment rows during stale Academy task cleanup while continuing to remove retired static lesson rows.
- Fixed the weekly retrospective save and completion crash caused by the missing `_table_exists` helper.
- Added database-level regressions for locked Knowledge Check visibility, check routing metadata, retrospective saving, and retrospective completion validation.

# 10.35.0

- Added a full program-integrity audit covering active task references, retired files, curriculum IDs, and prerequisite graphs.
- Enforced a frozen daily limit of five new current-week tasks with rolling prerequisite-ready catch-up work.
- Added factual Catch-Up labels to the second line of previous-week tasks.
- Audited Academy lesson, practice, assessment, Skills Lab, and all 36 Applied Lab prerequisite locks.
- Added twelve weekly eight-question multiple-choice Knowledge Checks with a seven-of-eight passing requirement, graded review, and missed-question recommendations.
- Gated new skill-dependent weekly work behind the previous week’s passed Knowledge Check while leaving review, Google Certificate, and career tools available.
- Simplified the weekly retrospective to Biggest Win, Friction or Blocker, and What I Learned; progress and evidence are filled automatically.
- Restored canonical Title Case task labels while preserving SQL keywords, spreadsheet functions, and product names.
- Made the four fixed Next Tasks rows expand evenly to fill the card above View All Tasks.
- Removed the retired Optional Practice workflow and obsolete Academy files and task references.

# 10.34.6

- Removed scrolling from the Dashboard Next Tasks card.
- Limited the card to four priority rows.
- Replaced Optional Practice with View All Tasks.
- Added Ready Now and Coming Soon sections to the full task dialog.

# 10.34.5

- Replaced the regressed resizable Next Tasks QScrollArea with the exact pre-overhaul ContentSizedScrollArea implementation.
- Prevented mouse-wheel scrolling through blank space after the final task row.

# 10.34.4

- Restored the pre-Academy-overhaul exact-height Next Tasks scroll document.
- Prevented scrolling through empty space beneath the final task row.

# 10.34.3

- Fixed startup migration failure: `sqlite3.OperationalError: no such column: PAGE_LEARNING`.
- Added an isolated SQLite execution test for `_update_duckdb_exercise_tasks()`.

# Changelog

## 10.34.2 — Next Tasks and Spreadsheet Guidance Repair

- Replaces the custom Next Tasks scroll document with the same widget-resizable QScrollArea pattern that already works correctly for Today’s Focus.
- Removes stale blank scroll range below the final Next Tasks row while preserving normal scrolling when the visible rows overflow.
- Revises Spreadsheet Lesson 2 Step 5 so absolute references are practiced with a 5% assumption entered on the Orders sheet instead of requiring an untaught cross-sheet reference.
- Rewrites Applied Lab 07 as a complete beginner-friendly build guide with a business scenario, source-file map, required workbook sheets, staged workflow, KPI definitions, reconciliation checks, deliverables, and submission prompts.

## 10.34.1 — Academy Step Focus and Dashboard Rollover Hotfix

- Keeps the Monday sprint rollover persisted after track and deadline synchronization, so Current Sprint, Today’s Focus, and Next Tasks all move to the new week immediately.
- Uses the saved program start date as the single calendar source and preserves manual future-week advancement.
- Rebuilds the Next Tasks scroll document from the real row height with a non-resizable content widget, eliminating scrollable space below the final row.
- Draws the Academy purpose bubble and right-side tail as one continuous shape.
- Removes redundant Markdown subheadings beneath the green lesson concept header.
- Stops repeating unchanged purpose, concept, and example content on practice, challenge, and transfer steps. Those steps now focus on the task and concise helpful requirements.

## 10.34.0 — Academy Experience Overhaul

- Rebuilt the Academy lesson presentation around the approved existing three-panel layout.
- Added a right-tailed “Why does this matter?” speech bubble with no left tail.
- Added lesson-specific concept headings and full-width colored header rules for concept, Example, and Task sections.
- Removed XP/difficulty clutter, Step Goal, duplicate starting-state/success-criteria content, bookmark, and overflow controls.
- Reworked lesson scenarios and tasks into practical, beginner-friendly workplace requests without exposing completed answers.
- Rebuilt the Google Sheet & Feedback panel with a compact workbook card, primary Open Google Sheet action, secondary workbook controls, separate feedback card, and linked-sheet URL.
- Added a live local-date check so an app left open across Sunday night advances the sprint after Monday begins.
- Rebuilds weekly planning, Today’s Focus, Next Tasks, and sprint progress after rollover.
- Orders ready current-week tasks before earlier-week catch-up work.
- Replaced the Next Tasks scroll extent logic with exact visible-row geometry and disables scrolling when all rows fit.
- Preserves the v10.33 curriculum content version, so Academy progress is not reset again for learners who already migrated to the new curriculum.

## 10.33.0 — Universal beginner-first Academy

- Introduced one shared DataCamp-style lesson engine and 63 original lessons across Spreadsheet, SQL, Power BI, and Python tracks.
- Added 448 short activities, progressive hints, solution tracking, executable practice, and plain-language teaching.
