# Projects Cleaning Summary

- **Source:** `data/raw/csv/raw_projects.csv`
- **Processed output:** `data/processed/csv/projects.csv`
- **Expected primary key:** `project_id`
- **Last updated:** 2026-07-25T16:05:41

## Decisions and remaining exceptions

I removed one exact duplicate project row and kept 15 unique projects. I
trimmed the text fields, standardized the known status variants, converted the
mixed date values into real dates, and converted the budget field into a number.

I also applied the four confirmed business corrections for the missing client,
the two bad budgets, and the impossible target date. The final table has one row
per project, valid client relationships, positive budgets, and valid project
dates.

## Latest validation

- Blocking issues: 0
- Warnings: 1
- Structural changes reviewed: 2
- Processed rows: 15
