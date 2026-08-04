# Test Whether Email Is a Reliable Key

> **Challenge structure source:** [HackerRank — New Companies](https://www.hackerrank.com/challenges/the-company/problem)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

A contact-import design proposes using email as the primary key, but the data architect wants evidence before approving it.

## Your task

Summarize the problems that prevent `email` from being a reliable primary key.

## Result requirements

- Return one row with `total_rows`, `missing_emails`, and `duplicate_email_rows`.
- `duplicate_email_rows` is the number of extra rows beyond the first occurrence of each non-null email.

## Skill focus

**Table grain and candidate keys**

Use duplicate and missing-value checks to evaluate a proposed business key.
