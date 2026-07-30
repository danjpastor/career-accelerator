# DuckDB Exercise 24: Standardize messy text, dates, and numeric fields

**Week:** 6
**Estimated time:** 50 minutes  
**Concepts:** TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME

## Scenario

A contact export contains inconsistent text, dates, phone numbers, and currency values. Standardize it without allowing bad values to crash the query.

## Tables

- `ex17_contacts_dirty`

## Questions

1. Task: Trim the full name and normalize repeated spaces. Required output: return only these columns in this order: `record_id`, `clean_name`. Use these exact names for calculated or summarized columns: `clean_name`. A correct result contains 8 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Normalize valid email values to lowercase and extract the email domain. Required output: return only these columns in this order: `email_domain`, `record_count`. Use these exact names for calculated or summarized columns: `email_domain`, `record_count`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Flag email values that do not match a basic email pattern. Required output: return only these columns in this order: `invalid_email_count`. Use these exact names for calculated or summarized columns: `invalid_email_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Remove phone punctuation and return digits only. Required output: return only these columns in this order: `valid_phone_count`. Use these exact names for calculated or summarized columns: `valid_phone_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Parse the different signup-date formats without failing on invalid dates. Required output: return only these columns in this order: `invalid_date_count`. Use these exact names for calculated or summarized columns: `invalid_date_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Convert annual_spend to a numeric value without failing on bad values. Required output: return only these columns in this order: `invalid_spend_count`. Use these exact names for calculated or summarized columns: `invalid_spend_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Create one cleaned result with a data-quality flag for every record. Required output: return only these columns in this order: `record_id`, `quality_flag`. Use these exact names for calculated or summarized columns: `quality_flag`. A correct result contains 8 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
