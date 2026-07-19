# Adaptive Deduplication and Workspace Boundaries

Version 9.3.21 makes the adaptive tracks the single scheduling source of truth.

## Today’s Focus

Each adaptive track can appear at most once. A roadmap fallback is not added
when the matching Google, DataCamp, SQL, or Portfolio track is already shown.
The final plan is also deduplicated by logical assignment before it is saved.

## Next Tasks

Available tasks are deduplicated by adaptive track or normalized roadmap
identity. The active adaptive assignment wins over an older unlinked task.
Legacy Google and DataCamp checklist tasks are managed by their adaptive track
and cannot compete with the active assignment.

## Task Workspaces

Google Certificate and DataCamp work is intentionally excluded. It remains
available through Learning, Today’s Focus, Next Tasks, and Study Sessions.
Existing accidental workspace database records are removed during migration;
linked study sessions keep their task association but lose the unnecessary
workspace link. Files on disk are not deleted.
