# DuckDB Exercise 24: Standardize messy text, dates, and numeric fields

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME

## Scenario

A contact export contains inconsistent names, emails, phone numbers, dates, and currency values. Standardize it without allowing bad values to stop the query.

## Tables

- `ex17_contacts_dirty`

## Tasks

### Task 1

Trim the full name and normalize repeated spaces.

**Result requirements**

- Return columns in this order: `record_id`, `clean_name`.
- Return 8 rows.

### Task 2

Normalize valid email values to lowercase and extract the email domain.

**Result requirements**

- Return columns in this order: `email_domain`, `record_count`.
- Return 2 rows.

### Task 3

Flag email values that do not match a basic email pattern.

**Result requirements**

- Return columns in this order: `invalid_email_count`.
- Return 1 row.

### Task 4

Remove phone punctuation and return digits only.

**Result requirements**

- Return columns in this order: `valid_phone_count`.
- Return 1 row.

### Task 5

Parse the different signup-date formats without failing on invalid dates.

**Result requirements**

- Return columns in this order: `invalid_date_count`.
- Return 1 row.

### Task 6

Convert annual_spend to a numeric value without failing on bad values.

**Result requirements**

- Return columns in this order: `invalid_spend_count`.
- Return 1 row.

### Task 7

Create one cleaned result with a data-quality flag for every record.

**Result requirements**

- Return columns in this order: `record_id`, `quality_flag`.
- Return 8 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

