# Achievement Integrity

Career Accelerator assigns one activity achievement to each logical
accomplishment.

## Canonical activity records

Specialized records take precedence:

- a completed SQL Companion problem produces `SQL Problem Solved`
- a completed portfolio project task produces
  `Portfolio Milestone Complete`

The matching generic roadmap task does not produce a second achievement.

For example, the single canonical result is:

```text
SQL Problem Solved — Data Science Skills
```

rather than both:

```text
SQL Problem Solved — Data Science Skills
SQL Challenge: Solve Data Science Skills
```

The same rule applies to portfolio milestones such as Generate dataset.

## Generic roadmap tasks

Roadmap work without a specialized SQL or portfolio completion record
still receives its normal Learning, SQL, Portfolio, Review, or General
achievement.

Multiple completed sprint rows with the same normalized category and
task label collapse to one activity achievement. Punctuation and legacy
prefixes such as `SQL Challenge:` are normalized before comparison.

## Existing records

Achievement synchronization runs when the application starts and during
normal refreshes. Unsupported duplicate managed achievements are removed
automatically. Completed tasks, SQL progress, project progress, evidence,
and completion history are not changed.

Cumulative milestone badges such as First Query, On Track, and Project
Started remain separate because they reward overall progress thresholds,
not an additional copy of one activity.
