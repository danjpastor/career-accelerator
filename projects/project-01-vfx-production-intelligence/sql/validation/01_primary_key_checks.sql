SELECT client_id, COUNT(*) AS row_count
FROM raw_clients
GROUP BY client_id
HAVING COUNT(*) > 1;
