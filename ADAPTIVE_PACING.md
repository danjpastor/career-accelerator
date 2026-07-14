# Adaptive Pacing and Skill Gates

## Primary objective

Until the Google certificate is complete, the pacing engine reserves roughly
70% of the learner's weekly study budget for certificate progress. The
remaining time is divided among aligned DataCamp lessons, SQL practice, and
skill-ready portfolio application.

With an 18-hour weekly goal, the engine currently aims for approximately:

- 6 Google module checkpoints
- 2 aligned DataCamp lessons
- 3 skill-appropriate SQL problems
- 1 portfolio milestone, when its prerequisites are unlocked

Targets shrink automatically for lower weekly-hour budgets.

## Daily pacing

The engine calculates:

- Work remaining in the current week
- Days remaining, including today
- The number of certificate checkpoints to target today
- Whether the learner is on pace or needs to catch up

These values appear through the existing Today’s Focus and Learning cards.

## Supplemental alignment

DataCamp stays sequential so foundational knowledge is not skipped, but each
lesson is described in relation to the current Google course. SQL problems are
selected only when their prerequisite concepts have been unlocked and are
chosen from the next unsolved eligible problem.

## Skill gates

The engine derives skills from:

- Current Google course
- DataCamp lessons completed
- SQL problems completed

The derived skills are stored in `skill_state`. Portfolio tasks declare
prerequisites such as data preparation, cleaning, SQL fundamentals, Power BI,
storytelling, or portfolio delivery.

The next portfolio milestone is suggested only when every prerequisite is
unlocked. Otherwise, the Portfolio Learning card explains exactly what must be
learned first and no blocked portfolio task is placed in Today’s Focus.

## Scheduling independence

Sprint Week remains a scheduling layer only. Changing weeks moves ready active
tasks into the new sprint but does not change the position of any learning
track.
