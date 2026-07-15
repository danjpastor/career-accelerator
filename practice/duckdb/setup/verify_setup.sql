SELECT
    table_name,
    estimated_size AS rows_loaded
FROM duckdb_tables()
WHERE schema_name = 'main'
  AND table_name LIKE 'ex%'
ORDER BY table_name;
