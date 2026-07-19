# Today Complete Workflow

Career Accelerator creates one stable required plan per day.

## Required daily plan

The first dashboard refresh of the day creates the plan and stores its
exact assignments. Later refreshes update completion state but do not
refill completed slots with additional required work.

Completed assignments remain part of the day's saved plan, including
adaptive assignments whose underlying sprint row is later reused.

## Today complete

When every original focus assignment is complete, the card shows:

- a clear success state
- completed task count and planned time
- one optional Continue & Get Ahead recommendation
- a non-binding Tomorrow Preview

## Optional extra work

Extra work is inserted only after the original plan is complete. It is
marked separately from the required plan and does not increase the
required task count.

An unfinished optional item is not treated as missed-yesterday
carryover. It may still be recommended normally later if it remains a
useful in-progress task.

## Tomorrow preview

The preview does not create tomorrow's plan. It shows up to three likely
eligible priorities based on current weekly targets, prerequisites, and
adaptive state. The actual plan is generated the next day.


## Upgrade-day recovery

When Career Accelerator is updated after the current day's work has already
been completed, there may be no previously saved base focus plan.

The dashboard now detects that no eligible required work remains and enters
the Today Complete state. It summarizes completion events or study sessions
recorded today when available. This prevents the former empty 0/0 display.

When the current week is exhausted, Continue & Get Ahead may select the next
prerequisite-ready future-week roadmap task.


## Compact completed-day presentation

Once the required plan is complete, the card uses a condensed layout:

- one-line success summary
- one short optional get-ahead assignment
- one-line tomorrow preview
- no duplicate time and task footer boxes

Full adaptive details remain available in tooltips and the Preview dialog.
The normal incomplete-day layout is unchanged.
