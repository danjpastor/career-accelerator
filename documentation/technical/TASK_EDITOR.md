# Adaptive Planner Task Editor

## Saving changes

Select a task in Sprint Backlog and choose **Edit Selected Task**.

The editor saves and verifies:

- status
- priority
- estimated minutes
- energy level
- deferred date

A task set to Deferred without a date automatically uses tomorrow.
Choosing any other status clears the deferred date.

Adaptive tasks preserve these edits while the same assignment remains
active. When the adaptive track advances to a genuinely new assignment,
the new task receives its normal track defaults.

After saving, Career Accelerator reads the task back from the database.
The status bar confirms the exact values that persisted.

## Today’s Focus footer

Total Estimated Time and Tasks use compact fixed-height boxes. Any unused
vertical space remains above the footer instead of stretching the boxes.


## Save ordering

The app now performs adaptive synchronization before applying the final
editor values. It captures the task's track and target identity, resolves
the live task row after synchronization, writes the selected values, and
refreshes the interface without immediately synchronizing a second time.

This supports older task rows whose week or label must be normalized during
the first refresh.

## Backlog selection

The selected Sprint Backlog row uses a persistent purple highlight, bright
left border, bold text, and visible outline. Selection remains visible while
the Edit Task dialog or another control has focus and is restored after the
backlog reloads.


## Restoring a task to the schedule

The editor considers a task completed if any of these layers still contains
completion evidence:

- `sprint_tasks.completed`
- `task_metadata.status`
- a matching adaptive `track_events` record
- a completed SQL Companion record

Changing the task to Not Started, In Progress, Deferred, or Blocked reverses
the matching completion evidence before the adaptive plan is rebuilt.

The save confirmation states whether the task was added back to the active
schedule. A restored task may remain unscheduled when its prerequisite
concepts are locked, it is deferred, it belongs to another sprint week, or
its adaptive track has already met the daily or weekly target.
