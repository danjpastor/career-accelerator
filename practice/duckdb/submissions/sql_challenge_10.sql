SELECT
    booking_id,
    facility_id,
    slots
FROM bookings
ORDER BY facility_id, booking_id;

-- SELECT
    -- facility_id,
    -- ROUND(AVG(slots), 2) AS avg_slots
-- FROM bookings
-- GROUP BY facility_id
-- ORDER BY facility_id
