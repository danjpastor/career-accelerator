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
