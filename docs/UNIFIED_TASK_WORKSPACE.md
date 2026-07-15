# Unified Task Workspace

Version 9.3.17 gives every roadmap task one workspace for its document,
task settings, schedule, artifacts, and study sessions.

## Access

A workspace can be opened from:

- Today's Focus
- Next Tasks
- Adaptive Planner recommendations
- Sprint Backlog
- Task Workspaces in the sidebar
- Weekly Review quick actions
- linked entries in Recent Study Sessions

Double-clicking supported task or session lists also opens the workspace.

## Document routing

The workspace automatically chooses the appropriate file:

- Applied Labs use their saved submission
- DuckDB exercises use their saved SQL submission
- retrospective tasks use `weeks/week-XX/RETROSPECTIVE.md`
- study-plan tasks use `weeks/week-XX/STUDY_PLAN.md`
- portfolio tasks use the current project's `workspaces` folder
- other tasks use `workspaces/tasks/week-XX/`

Documents can be edited inside the app, autosaved, reloaded, opened in VS
Code or the system editor, and opened in their containing folder.

## Task and schedule

The workspace supports status, priority, estimate, energy, intended
scheduled date, deferred date, the existing detailed task editor, task
completion, and starting a linked Study Session. Applied Lab and DuckDB completion still requires a changed saved submission and all applicable prerequisites.

`Scheduled for` records the intended work date. `Deferred until` keeps a
task out of active planning until that date.

## Artifacts and sessions

Files and folders can be linked as artifacts without moving them. Study
Sessions can be started from a task, automatically linked when logged, or
linked afterward from the workspace.

Adaptive assignments use their track target as the workspace identity. This
preserves historical notes and linked sessions when the same task row is
later reused for a new module, SQL problem, portfolio milestone, or lab.

## Weekly planning and review

Task Workspaces and Weekly Review provide quick actions for the current
week's study plan and retrospective. A study-plan task is created only when
the learner requests one and no matching roadmap task exists.

Generating the Weekly Summary also writes or updates a clearly marked
Generated Weekly Summary section in the retrospective document.
