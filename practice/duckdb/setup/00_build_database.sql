-- Career Accelerator DuckDB practice database
-- Run from the repository root.

DROP TABLE IF EXISTS ex01_support_tickets;
CREATE TABLE ex01_support_tickets AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/01_select_filter_sort_limit/support_tickets.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex02_retail_orders;
CREATE TABLE ex02_retail_orders AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/02_aggregations_grouping_having/retail_orders.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex03_customer_feedback_dirty;
CREATE TABLE ex03_customer_feedback_dirty AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/03_nulls_case_cleaning/customer_feedback_dirty.csv',
    header = true,
    all_varchar = true
);

DROP TABLE IF EXISTS ex04_subscriptions;
CREATE TABLE ex04_subscriptions AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/04_business_metrics/subscriptions.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex05_service_requests;
CREATE TABLE ex05_service_requests AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/05_case_grouped_summaries/service_requests.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex06_customers;
CREATE TABLE ex06_customers AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/06_joins/customers.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex06_orders;
CREATE TABLE ex06_orders AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/06_joins/orders.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex06_payments;
CREATE TABLE ex06_payments AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/06_joins/payments.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex07_products;
CREATE TABLE ex07_products AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/07_ctes_subqueries/products.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex07_orders;
CREATE TABLE ex07_orders AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/07_ctes_subqueries/orders.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex07_order_items;
CREATE TABLE ex07_order_items AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/07_ctes_subqueries/order_items.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex08_projects;
CREATE TABLE ex08_projects AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/08_integrated_vfx_review/projects.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex08_shots;
CREATE TABLE ex08_shots AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/08_integrated_vfx_review/shots.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex08_time_entries;
CREATE TABLE ex08_time_entries AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/08_integrated_vfx_review/time_entries.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex09_users;
CREATE TABLE ex09_users AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/09_timed_sql_challenge/users.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex09_events;
CREATE TABLE ex09_events AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/09_timed_sql_challenge/events.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex09_purchases;
CREATE TABLE ex09_purchases AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/09_timed_sql_challenge/purchases.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex10_departments;
CREATE TABLE ex10_departments AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/10_mixed_sql_assessment/departments.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex10_employees;
CREATE TABLE ex10_employees AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/10_mixed_sql_assessment/employees.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex10_performance_reviews;
CREATE TABLE ex10_performance_reviews AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/10_mixed_sql_assessment/performance_reviews.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex11_customer_accounts;
CREATE TABLE ex11_customer_accounts AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/11_explain_joins_windows/customer_accounts.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex11_support_agents;
CREATE TABLE ex11_support_agents AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/11_explain_joins_windows/support_agents.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex11_tickets;
CREATE TABLE ex11_tickets AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/11_explain_joins_windows/tickets.csv',
    header = true,
    all_varchar = false
);

DROP TABLE IF EXISTS ex12_campaign_performance;
CREATE TABLE ex12_campaign_performance AS
SELECT *
FROM read_csv(
    'practice/duckdb/datasets/12_query_readability/campaign_performance.csv',
    header = true,
    all_varchar = false
);

SELECT COUNT(*) AS practice_table_count
FROM information_schema.tables
WHERE table_schema = 'main'
  AND table_name LIKE 'ex%';