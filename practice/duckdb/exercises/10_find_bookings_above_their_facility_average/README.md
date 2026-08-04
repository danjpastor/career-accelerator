# Find Bookings Above Their Facility Average

> **Challenge structure source:** [PostgreSQL Exercises — Produce a list of costly bookings, using a subquery](https://pgexercises.com/questions/joins/tjsub.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

The facilities manager wants unusually long bookings reviewed by facility.

## Your task

Return bookings whose slot count is greater than the average slot count for the same facility.

## Result requirements

- Return `booking_id`, `facility_id`, and `slots`.
- Sort by `facility_id`, then `booking_id`.

## Skill focus

**Correlated subquery**

Compare each row with an aggregate calculated for its own group.
