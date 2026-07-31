-- DuckDB Exercise 13: Refactor an unreadable analytics query
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex12_campaign_performance;


-- -----------------------------------------------------------------
-- Q1. Refactor the starting campaign query shown in the exercise guide without changing its result. Return `campaign_channel`, `spend`, `revenue`, `profit`, and `return_on_spend`, with return on spend rounded to four decimal places.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Rewrite the starting query with each major SQL clause on its own line and consistent indentation. Then return the number of source rows as `formatted_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Build the channel report so it sorts by the `return_on_spend` alias instead of column position 5. Then return the number of distinct channels as `channel_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Move channel aggregation into a clearly named CTE. Return total `total_spend` and `total_revenue`, each rounded to two decimal places.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Add short SQL comments that explain the channel-summary CTE and its final filter. Return `campaign_channel` and `profit` for the four report rows.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Confirm the refactored query still covers every source row. Return the matching row count as `matching_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Write two SQL-comment sentences explaining how readable SQL reduces analytics risk, then return the source row count as `reviewed_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
