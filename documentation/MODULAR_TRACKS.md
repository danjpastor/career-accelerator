# Modular Progress Architecture

Data Career Accelerator uses two independent layers.

## Sprint Layer

The sprint layer controls:

- Current week
- Weekly target hours
- Daily capacity
- Carryover and scheduling
- Weekly summaries and retrospectives

Changing the sprint week never changes a learner's skill-track position.

## Progress Tracks

Each progress track owns its own checkpoint, weekly pace, completion events,
and next recommended action:

- Google Certificate
- DataCamp
- SQL Practice
- Portfolio

The active action from each track is scheduled into the current sprint and
feeds the existing Today’s Focus and Next Tasks components.

## Track Persistence

- `track_state` stores the independent position and weekly target.
- `track_tasks` links each track to its current actionable task.
- `track_events` records dated completions for weekly pacing.
- `sprint_tasks` remains the shared task surface used by the existing UI.

## Dynamic Behavior

- Moving from Week 1 to Week 2 moves active track tasks into Week 2 without
  changing Course 5, the DataCamp lesson, the next SQL problem, or the current
  portfolio milestone.
- Completing a DataCamp task advances the DataCamp sequence.
- Completing a SQL task records the problem and recommends the next unsolved
  problem regardless of sprint week.
- Completing a portfolio task updates the real project milestone and recommends
  the next incomplete milestone.
- Completing a Google task advances the module; the Learning page can still be
  used to correct course or module boundaries manually.

The UI layout is unchanged. The architecture only changes how existing cards,
lists, and focus recommendations obtain their data.
