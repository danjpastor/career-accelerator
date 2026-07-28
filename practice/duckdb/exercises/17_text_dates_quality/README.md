# DuckDB Exercise 17: Standardize messy text, dates, and numeric fields

**Week:** 5  
**Estimated time:** 50 minutes  
**Concepts:** TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME

## Scenario

A contact export contains inconsistent text, dates, phone numbers, and currency values. Standardize it without allowing bad values to crash the query.

## Tables

- `ex17_contacts_dirty`

## Questions

1. Trim the full name and normalize repeated spaces.
2. Normalize valid email values to lowercase and extract the email domain.
3. Flag email values that do not match a basic email pattern.
4. Remove phone punctuation and return digits only.
5. Parse the different signup-date formats without failing on invalid dates.
6. Convert annual_spend to a numeric value without failing on bad values.
7. Create one cleaned result with a data-quality flag for every record.

## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
