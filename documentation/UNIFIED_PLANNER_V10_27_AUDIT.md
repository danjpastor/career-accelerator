# Career Accelerator v10.27.0 — Program and Planner Audit

## Audit objective

Career Accelerator had accumulated several overlapping systems for deciding what the learner should do next. Academy recommendations, track synchronization, the adaptive planner, Get Ahead, Added Today, SQL readiness, DuckDB readiness, catch-up migration, and persisted Today’s Focus rows could disagree or overwrite one another.

v10.27.0 makes the curriculum and verified progress the source of truth and reduces runtime planning to one deterministic task service.

## Active 90-day learning sequence

| Program period | Required progression |
|---|---|
| Weeks 1–2 | Spreadsheets for Data Analysts |
| Weeks 3–6 | Complete SQL curriculum, DuckDB exercises, and interview practice |
| Week 7 | Power BI and Power Query |
| Week 8 | Python, pandas, and Portfolio Readiness |
| Weeks 9–12 | Three portfolio projects and targeted reinforcement |
| Days 85–90 | Portfolio QA, publishing, interviews, and career launch |

The Google Data Analytics Certificate remains the highest-priority unfinished item throughout the program.

## Canonical runtime services

### Curriculum and existing task records

The existing curriculum packages and sprint-task tables remain the durable content and migration layer. Task identity is always carried by the task ID, managed key, target key, or linked entity—not by copied display text.

### Progress

Validated Academy activity states, assessments, DuckDB completions, SQL problem completions, portfolio milestone states, and Google position remain authoritative evidence.

### Readiness

`roadmap_mastery` is the public readiness facade. It provides the same all-of/any-of prerequisite result to the planner, SQL Companion, and DuckDB interfaces.

### Daily planning

The former Adaptive Planner screen is presented as **Daily Plan**. It no longer asks the learner to construct a competing time-and-energy queue or manually block/defer curriculum tasks.

`unified_tasks` selects:

- up to five ready Today’s Focus items;
- six ready Next Tasks;
- three locked Coming Up items; and
- optional practice that never changes required daily or weekly work.

## Today’s Focus rules

1. Current Google Certificate work is first while incomplete.
2. The next ready mastery gate or Academy progression item follows.
3. A prerequisite-ready practice task is selected when available.
4. A second ready progression item may be selected.
5. A ready assessment, preparation, review, or career task may fill the final slot.

Locked, completed, duplicate, future, and unrelated tasks are never used as filler. Fewer than five ready items produces fewer than five rows.

## Next Tasks rules

Next Tasks shows the next six ready tasks in roadmap order. Locked items are not mixed into that queue. The Coming Up section shows the nearest missing prerequisite before distant assessments or future phases.

## Retired active structures

- Separate Get Ahead persistence and Added Today planning
- Manual daily-focus overrides
- Active DataCamp track tasks and prerequisite evidence
- DataCamp curriculum catalog in the active roadmap
- DataCamp concept inference in exercise-pack audits
- Separate planner selection logic inside SQL Companion and DuckDB
- Copied catch-up prefixes stored inside canonical titles
- Multiple active recommendation pools competing for dashboard rows

The previous planner remains isolated as `legacy_planner.py` only for durable seed, repair, defer, and completion compatibility. It does not choose Today’s Focus or Next Tasks.

## Progress migration

The migration is idempotent and preserves learner evidence. It removes only derived or retired active planner rows, normalizes catch-up presentation titles, keeps one current Google task, and rebuilds Today’s Focus from ready work.

Historical DataCamp columns and events remain readable for backward compatibility but cannot unlock skills or produce active tasks.

## Lockout audit

All 12 DuckDB exercises and all 16 SQL Companion interview problems continue to use the audited v10.26 prerequisite definitions. Direct navigation, editor controls, run/check actions, save, and completion use the same readiness result.

## Acceptance criteria

- Google appears first and at most once while unfinished.
- Today’s Focus contains zero to five unique ready tasks.
- Next Tasks contains no more than six unique ready tasks.
- Coming Up contains locked work with an exact reason.
- No portfolio execution appears before Week 9 or before Portfolio Readiness.
- No active DataCamp task or prerequisite remains.
- Completing progress dynamically changes the next plan without hardcoded daily schedules.
- Existing learner completion and project data remain intact.
