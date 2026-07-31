# DuckDB Exercise 24: Standardize messy text, dates, and numeric fields

**Week:** 6
**Estimated time:** 50 minutes  
**Concepts:** TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME

## Scenario

A contact export contains inconsistent text, dates, phone numbers, and currency values. Standardize it without allowing bad values to crash the query.

## Tables

- `ex17_contacts_dirty`

## Tasks

### Task 1

Trim the full name and normalize repeated spaces.

**Result requirements**

- **Return columns:** `record_id`, `clean_name`
- **Exact names for new columns:** `clean_name`
- **Expected rows:** 8

### Task 2

Normalize valid email values to lowercase and extract the email domain.

**Result requirements**

- **Return columns:** `email_domain`, `record_count`
- **Exact names for new columns:** `email_domain`, `record_count`
- **Expected rows:** 2

### Task 3

Flag email values that do not match a basic email pattern.

**Result requirements**

- **Return columns:** `invalid_email_count`
- **Exact names for new columns:** `invalid_email_count`
- **Expected rows:** 1

### Task 4

Remove phone punctuation and return digits only.

**Result requirements**

- **Return columns:** `valid_phone_count`
- **Exact names for new columns:** `valid_phone_count`
- **Expected rows:** 1

### Task 5

Parse the different signup-date formats without failing on invalid dates.

**Result requirements**

- **Return columns:** `invalid_date_count`
- **Exact names for new columns:** `invalid_date_count`
- **Expected rows:** 1

### Task 6

Convert annual_spend to a numeric value without failing on bad values.

**Result requirements**

- **Return columns:** `invalid_spend_count`
- **Exact names for new columns:** `invalid_spend_count`
- **Expected rows:** 1

### Task 7

Create one cleaned result with a data-quality flag for every record.

**Result requirements**

- **Return columns:** `record_id`, `quality_flag`
- **Exact names for new columns:** `quality_flag`
- **Expected rows:** 8
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
