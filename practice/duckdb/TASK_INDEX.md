# DuckDB Exercise Index

Exercises are numbered in the order they appear in the roadmap. Folder and table names may retain stable internal identifiers so existing submissions and progress remain valid.

| Exercise | Week | Title | Concepts |
|---:|---:|---|---|
| 01 | 3 | Filter and sort support tickets | SELECT, FROM, WHERE, ORDER BY, LIMIT |
| 02 | 3 | Summarize retail orders | COUNT, SUM, AVG, GROUP BY, HAVING |
| 03 | 3 | Build clear selected fields and calculated columns | column selection, aliases, arithmetic expressions, DISTINCT |
| 04 | 3 | Filter patterns, ranges, and missing values | WHERE, AND, OR, BETWEEN, IN, LIKE, IS NULL |
| 05 | 3 | Connect orders to customers with inner joins | INNER JOIN, join keys, qualified columns, joined filters |
| 06 | 4 | Calculate subscription KPIs | ratios, conditional aggregation, date filters |
| 07 | 4 | Segment service performance | CASE expressions, SLA logic, grouped summaries |
| 08 | 4 | Join customers, orders, and payments | INNER JOIN, LEFT JOIN, multi-table joins |
| 09 | 4 | Analyze order profitability | subqueries, CTEs, layered analysis |
| 10 | 4 | Refactor an unreadable analytics query | CTEs, aliases, formatting, validation |
| 11 | 4 | Audit table grain and join cardinality | table grain, primary keys, join cardinality, pre-aggregation |
| 12 | 4 | Compare customer populations with set and existence logic | UNION, INTERSECT, EXCEPT, semi joins, anti joins |
| 13 | 4 | Compare outer, cross, and self joins | LEFT JOIN, FULL JOIN, CROSS JOIN, SELF JOIN |
| 14 | 4 | Use subqueries in filters, sources, and calculations | subqueries in WHERE, FROM, and SELECT |
| 15 | 4 | Add row-level context with window functions | OVER, PARTITION BY, window aggregates, row-level context |
| 16 | 5 | Clean customer feedback | NULLIF, TRIM, COALESCE, TRY_CAST, CASE |
| 17 | 5 | Explain joins and window functions | join reasoning, window reasoning, analyst communication |
| 18 | 5 | Build monthly cohorts and retention metrics | DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation |
| 19 | 5 | Calculate running totals and moving averages | window frames, ROWS BETWEEN, LAG, running totals, moving averages |
| 20 | 5 | Standardize messy text, dates, and numeric fields | TRIM, LOWER, SPLIT_PART, REGEXP, TRY_CAST, STRPTIME |
| 21 | 5 | Rank results and select top records | ROW_NUMBER, RANK, DENSE_RANK, top-N per group |
| 22 | 5 | Compare current values with prior and next rows | LAG, LEAD, period-over-period change |
| 23 | 5 | Build subtotal and pivot-style summaries | ROLLUP, CUBE, GROUPING SETS, FILTER-based pivots |
| 24 | 5 | Inspect data types and work with list values | data types, TRY_CAST, LIST, UNNEST, type-safe calculations |
| 25 | 6 | Analyze a VFX production snapshot | joins, CTEs, CASE, window functions, business interpretation |
| 26 | 6 | Timed product challenge | timed SQL analysis, joins, CTEs, business metrics |
| 27 | 6 | Mixed workforce assessment | joins, CTEs, window functions, QA, explanation |
| 28 | 6 | Complete a full relational data-quality audit | grain, duplicates, NULLs, referential integrity, reconciliation, CTEs |
| 29 | 6 | Explore text search and extension-safe SQL | ILIKE, regular expressions, text search, extension inspection |
| 30 | 6 | Profile tables for analytical storage decisions | information_schema, table size, grain, OLTP versus OLAP reasoning |
| 31 | 6 | Reshape operational data into analytical tables | fact tables, dimensions, normalization, star-schema joins |
| 32 | 6 | Create reusable views and analytical snapshots | views, reusable logic, snapshot tables, refresh validation |
| 33 | 6 | Plan partitioning and access-safe outputs | partition-key analysis, restricted projections, database management reasoning |
