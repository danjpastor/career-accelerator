# Roadmap Dependency and Task-Ordering Audit

## Scope

This audit covers the 12-week Data Analytics roadmap, the dashboard task queues, and the prerequisite mappings for Google Certificate modules, DataCamp chapters, 33 SQL Challenges, 13 Python exercises, 36 Applied Labs, SQL interview problems, weekly checks, and retrospectives.

## Ordering rules now enforced

1. Completed tasks are excluded from active queues.
2. Every open/ready task appears before every locked task.
3. Google Certificate work is the highest-priority open work.
4. Open DataCamp chapters appear immediately after Google work.
5. Other open practice and lab work follows DataCamp.
6. Locked work remains visible underneath open work with its prerequisite reason.
7. Incomplete work from an earlier day in the current week remains in Next Tasks as catch-up.
8. Logical duplicates are collapsed across Today’s Focus, Next Tasks, sprint-day lists, and View All Tasks.

## Dependency scheduling

Flexible practice is assigned only on or after the date of its final required DataCamp chapter. Direct SQL Challenge and Python exercise prerequisites are also considered. Flexible work is balanced toward a three-hour weekday target instead of being blindly pushed onto Friday.

The specific regression was corrected:

- `Data Manipulation in SQL — Chapter 1: We'll Take the CASE`: Tuesday, August 4, 2026
- `Solve Laptop Vs. Mobile Viewership`: Thursday, August 6, 2026

`Solve Second Day Confirmation` was moved from Week 4 to Week 5 because its date-logic prerequisite is not taught until Week 5.

## Duplicate cleanup

The database contains a durable roadmap row and an adaptive-track row for `Page With No Likes`. They use different task IDs but represent one assignment. Task queues now resolve both rows to one semantic identity, merge completion state, and display the problem once.

## Current Week 4 workload

| Day | Assigned minutes |
|---|---:|
| Monday | 140 |
| Tuesday | 150 |
| Wednesday | 155 |
| Thursday | 165 |
| Friday | 115 |

All current-week days remain below the 180-minute flexible-work balancing target.

## Full-roadmap validation

- 33 SQL Challenge gates checked.
- 13 Python exercise gates and direct chains checked.
- 36 Applied Lab terminal chapters checked.
- Every SQL interview problem checked against its required DataCamp chapters.
- Google Certificate sequence checked for week inversions.
- DataCamp chapter order and unique day/order positions checked.
- Weekly runtime queues checked for ready/locked order and logical duplicates.
- Migration executed twice against a copy of the learner database.

Result: **262 checks passed, 0 failed.**

Historical completed-task dates are preserved. The audit does not rewrite past completion history; it corrects active and future task scheduling.
