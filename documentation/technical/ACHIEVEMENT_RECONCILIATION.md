# Achievement Reconciliation

Achievements are derived from current verified evidence.

## Reversible achievements

These are removed when their source is undone or deleted:

- roadmap task achievements
- portfolio milestone achievements
- SQL Problem Solved achievements
- study-session achievements
- application achievements
- count and readiness milestone achievements

## SQL behavior

A SQL record counts only when `sql_practice.status = 'Completed'`.

Restoring a SQL problem to Not Started or In Progress preserves its
solution path, notes, mastery value, and review date, but removes:

- the matching SQL Problem Solved achievement
- the matching completed roadmap-task achievement
- any SQL count milestone no longer supported

Other achievements remain when their own evidence still exists.
