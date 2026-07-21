# Guided Portfolio Milestones

Career Accelerator v10.12.0 gives every portfolio milestone a clear task brief, a measurable definition of done, an estimated time, and a guided starter document.

## Opening a guide

Open **Portfolio Workspace**, select a project, and choose **Guide** beside any milestone. The guide opens inside the application and is saved automatically under:

```text
projects/<project-folder>/workspaces/milestones/
```

The milestone workspace includes:

- What the task means
- What must be completed
- A structured starter document
- Save and autosave
- Open Externally
- Open Folder
- Mark Complete or Reopen Milestone

## Existing work

Starter documents are created only when a milestone guide is opened for the first time. Existing milestone documents are not overwritten. Database migration adds guidance metadata without changing completion states.

## Validate relationships

Relationship validation confirms that tables can be joined without corrupting the analysis. The guide checks:

1. Primary keys are unique.
2. Foreign keys point to existing parent rows.
3. Child rows are not lost unexpectedly.
4. Joins do not multiply rows because the parent key is duplicated or the join condition is incomplete.
5. Duplicated relationship fields agree, such as a time entry’s `project_id` matching the project attached to its `shot_id`.

For Project 1, the guide includes the expected links among clients, projects, artists, shots, time entries, and reviews, plus starter SQL for each validation type.
