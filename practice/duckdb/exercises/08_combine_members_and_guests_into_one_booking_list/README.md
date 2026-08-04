# Combine Members and Guests into One Booking List

> **Challenge structure source:** [PostgreSQL Exercises — Combining results from multiple queries](https://pgexercises.com/questions/basic/union.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

The facilities coordinator wants one list showing whether each booking belongs to a member or a guest.

## Your task

Return a combined list of booking IDs and booking types for member and guest bookings.

## Result requirements

- Return `booking_id` and `booking_type`.
- Use `Member` for rows whose `member_id` is not 0 and `Guest` for rows whose `member_id` is 0.
- Sort by `booking_id`.

## Skill focus

**UNION**

Combine compatible result sets into one duplicate-free list.
