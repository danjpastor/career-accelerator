# Task Architecture

Career Accelerator uses a hybrid model.

## Fixed source-of-truth catalogs

These define what valid work exists:

- official DataCamp courses and chapters
- Google Certificate progression
- SQL practice problem bank
- DuckDB exercise library
- portfolio milestones and prerequisites
- weekly retrospective and publishing requirements

A task catalog must be defined somewhere. Removing all fixed content would force
the scheduler to invent work and would make the learning path inconsistent.

## Adaptive behavior

The app decides:

- which eligible item comes next
- how much is due today and this week
- whether another item should appear after completion
- whether a task is blocked by missing skills
- whether work should be carried forward
- when daily-complete and weekly-complete tracks return
- which task fills Today's Focus

## Hard-coded tasks that should remain

Fixed one-time deliverables remain appropriate when they have a stable completion
condition, such as:

- complete the weekly retrospective
- publish a project release
- create a project README
- document assumptions and limitations

## Hard-coded tasks that should not remain

The daily plan should not use:

- invented external-course lesson names
- generic reminders such as “practice joins”
- duplicate template tasks when an adaptive track already has a real assignment
- concept-only tasks without a platform, exercise, deliverable, or completion rule

Roadmap templates are now structural fallbacks only. When a real adaptive track
exists, the fallback reads that track's current assignment rather than supplying
a separate hard-coded task.
