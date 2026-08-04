# Combine Members and Guests into One Booking List

> **Challenge structure source:** [PostgreSQL Exercises — Combining results from multiple queries](https://pgexercises.com/questions/basic/union.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

The facilities coordinator needs one list from the `bookings` table showing whether each booking belongs to a member or a guest. The `booking_type` field does not exist in the dataset; create it as a text alias in each SELECT.

## Your task

Using the `bookings` table, return each `booking_id` and create a calculated text column named `booking_type`. Label rows with a nonzero `member_id` as `Member`, label rows with `member_id = 0` as `Guest`, and combine the two compatible queries with `UNION`.

## Result requirements

- Use the `bookings` table for both SELECT statements.
- Return `booking_id` and a calculated alias named `booking_type`.
- Use `'Member' AS booking_type` when `member_id <> 0` and `'Guest' AS booking_type` when `member_id = 0`.
- Combine the two result sets with `UNION` and sort by `booking_id`.

## Skill focus

**UNION**

Combine compatible result sets into one duplicate-free list.
