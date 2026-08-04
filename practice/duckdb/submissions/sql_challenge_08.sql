SELECT
    booking_id,
    'Member' AS booking_type
FROM bookings
WHERE member_id <> 0

UNION

SELECT
    booking_id,
    'Guest' AS booking_type
FROM bookings
WHERE member_id = 0

ORDER BY booking_id;
