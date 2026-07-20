# Accelerator Academy v10.8.0 Validation

## Planner migration

- DataCamp is excluded from active track ordering, adaptive allocations, generated tasks, available candidates, carryover, stored focus, completion evidence, and tomorrow previews.
- Existing DataCamp track events and completion history remain intact as External Learning History.
- Untouched frozen daily-focus snapshots are regenerated when needed so Accelerator Academy immediately fills the replacement learning slot.
- Academy task titles no longer include a redundant `[Accelerator Academy]` prefix; the source metadata remains `Accelerator Academy`.

## Replacement curriculum

- Curriculum content version 1.4.0 contains 8 courses, 31 lessons, and 112 interactive activities, checkpoint questions, and projects.
- The 26 newly added lessons cover the remaining required SQL, Power BI, Python, and pandas topics previously assigned through DataCamp.
- Every new lesson contains three required interactive steps, including a mastery check.
- All 48 SQL activities expose valid table schemas and pass their official result validators.
- All 64 recognition activities pass their answer validators.
- Recommendation order completes each course before advancing to the next course.

## Layout and copy

- Track, course, lesson, checkpoint, and project headers use tinted custom cards with explicit item heights and spacing, preventing overlap on Windows.
- The lesson completion message is transparent and sits directly on the footer card.
- Shared Course UI subtitles and subheaders use transparent backgrounds in Academy, Exercises, and Applied Labs.
- Multiple-choice steps continue to remove the SQL editor/output divider.

## Regression and packaging

- Python compilation, catalog loading, SQL and recognition validation, schema resolution, planner migration, full Academy construction, responsive layouts, full-application construction, installer application, repeat installation, and manifest hashes are verified.
- Existing public/private databases and learner files are excluded from the payload and preserved during installation.
- A final native Windows mouse-and-keyboard walkthrough remains outside the Linux build environment.
