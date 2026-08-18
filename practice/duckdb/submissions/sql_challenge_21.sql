SELECT
    booking_id,
    start_time AS start_time,
    start_time + slots * INTERVAL '30 minutes' AS end_time
FROM bookings
ORDER BY start_time, booking_id
