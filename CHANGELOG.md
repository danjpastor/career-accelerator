# Changelog

This file is the single maintained changelog for the project.
























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
