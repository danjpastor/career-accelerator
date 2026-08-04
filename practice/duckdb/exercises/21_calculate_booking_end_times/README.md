# Calculate Booking End Times

> **Challenge structure source:** [PostgreSQL Exercises — Work out the end time of bookings](https://pgexercises.com/questions/date/endtimes.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Facility bookings use 30-minute slots, and the scheduling screen needs each end time.

## Your task

Calculate the end timestamp for every booking.

## Result requirements

- Return `booking_id`, `start_time`, and `end_time`.
- Each slot lasts 30 minutes.
- Sort by `start_time`, then `booking_id`.

## Skill focus

**Timestamp and interval arithmetic**

Add a duration to a timestamp to calculate an end time.
