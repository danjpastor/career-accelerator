# Release Readiness and Known Boundaries

## Covered edge cases

- Google always appears first in Today’s Focus.
- Sprint week changes do not reset learning-track positions.
- Supplemental tracks pause before Google when weekly hours are limited.
- SQL distinguishes between completed and prerequisite-locked states.
- Portfolio tasks are withheld until all declared skills are unlocked.
- Skills unlock after completing a course, not simply entering it.
- Manual Google progress jumps count each crossed module within the same course.
- Manual rewinds do not create false completion events.
- Stale, orphaned, or completed active-track links are repaired automatically.
- Factory Reset rebuilds independent tracks, skills, pacing, and prerequisites.
- Empty SQL or portfolio tracks transition to Completed rather than crashing.
- Today’s Focus is deterministic: Google, DataCamp, SQL, Portfolio, then
  carryover/general work.

## Intentional boundaries

No application can guarantee every career outcome or anticipate every external
change. Career Accelerator does not currently know the official module count
inside each Google course, so finishing a module advances the module number and
course boundaries remain manually correctable on the Learning page.

DataCamp course structure and SQL problem catalogs are local curated sequences,
not live account integrations. Changes completed directly on external websites
must be reflected in the app manually.

Portfolio prerequisites are competency gates, not formal assessments. The
learner may still manually check a Portfolio Workspace item when equivalent
prior experience provides the needed skill.

The application does not search live job boards, evaluate current hiring-market
conditions, or submit applications automatically. Those choices remain human
decisions and should be reviewed regularly.

## Success practices outside the software

The app provides planning, learning progression, evidence tracking, portfolio
workflow, readiness scoring, applications, weekly reviews, and backups. The
highest-value practices that still require the learner are:

- Complete the recommended work consistently.
- Produce polished public portfolio evidence rather than only recording tasks.
- Ask humans for feedback on projects, résumé positioning, and interviews.
- Network and apply while continuing to learn.
- Back up the database before major updates.
- Reassess the plan when career goals, available hours, or course structures
  change.
