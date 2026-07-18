# Data storage

Career Accelerator now separates shareable progress from local private data.

## Git-safe progress database

`career_accelerator.db` stores learning, study, SQL, portfolio, achievement,
evidence, roadmap, and summary progress. It is intentionally allowed in Git.

## Local private database

`career_private.db` stores job-application details and local application
settings. It is ignored by Git and should never be force-added or uploaded.

When upgrading from an older release, Career Accelerator automatically moves
the legacy `applications` and `settings` tables into `career_private.db`, drops
them from `career_accelerator.db`, and vacuums the progress database before it
can be committed.

SQLite `-wal`, `-shm`, and other transient sidecar files remain ignored.
