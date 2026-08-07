WITH avs AS (
    SELECT
    facility_id,
    ROUND(AVG(slots), 2) AS avg_slots
FROM bookings
GROUP BY facility_id)

SELECT
    b.booking_id,
    b.facility_id,
    b.slots
FROM bookings AS b
LEFT JOIN avs AS avs ON avs.facility_id = b.facility_id
WHERE b.slots > avs.avg_slots
ORDER BY facility_id, booking_id
