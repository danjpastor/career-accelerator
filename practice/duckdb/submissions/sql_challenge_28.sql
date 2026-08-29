SELECT
   TRIM(LOWER(region)) AS region,
   COUNT() AS contact_count
FROM raw_contacts
GROUP BY TRIM(LOWER(region))
ORDER BY TRIM(LOWER(region))
