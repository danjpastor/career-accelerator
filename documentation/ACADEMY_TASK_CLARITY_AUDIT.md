# Accelerator Academy Task-Clarity Audit

This report checks every installed lesson activity, checkpoint question, and Skills Lab action after the learner-facing clarity renderer is applied.

## Summary

- Lessons checked: **51**
- Total learning actions checked: **193**
- Lesson activities: **164**
- Checkpoint activities: **27**
- Skills Lab activities: **2**
- SQL actions: **95**
- Recognition actions: **98**
- Actions automatically enriched: **101**
- Actions already complete: **92**
- Blocking errors: **0**

## Quality contract

Every rendered task provides the complete prompt, visible schemas, exact output columns and order, fixed result shape when applicable, readable requirements, and a definition of done. Reference SQL and expected result values remain hidden.

## Activity results

| Location | Activity | Runtime | Status | Required columns | Result shape |
|---|---|---|---|---|---|
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL | `structure_grain_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL | `structure_type_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL | `structure_guided` | sql | Enhanced | sku, item_name, category | 6 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL | `structure_debug` | sql | Enhanced | employee_id, full_name, department | 5 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL | `select_projection_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL | `select_guided` | sql | Enhanced | product_id, product_name, unit_price | 7 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL | `alias_guided` | sql | Enhanced | order_id, order_value | 8 × 2 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL | `alias_debug` | sql | Enhanced | subscriber_id, recurring_revenue | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL | `alias_mastery` | sql | Enhanced | account_id, subscription_plan | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results | `distinct_combination_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results | `distinct_guided` | sql | Enhanced | region | 4 × 1 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results | `distinct_limit_independent` | sql | Enhanced | channel | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results | `distinct_limit_mastery` | sql | Enhanced | location | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_operator_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_text_guided` | sql | Enhanced | subscriber_id, plan_name, status | 4 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_threshold` | sql | Enhanced | subscriber_id, plan_name, monthly_fee | 5 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_and_guided` | sql | Enhanced | sku, item_name, units_on_hand, reorder_level | 2 × 4 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_parentheses_transfer` | sql | Enhanced | ticket_id, status, priority, assigned_team | 3 × 4 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_null_debug` | sql | Enhanced | ticket_id, satisfaction_score | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need | `filter_mastery` | sql | Enhanced | ticket_id, customer_id, priority, status, assigned_team | 5 × 5 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `sort_direction_recognition` | recognition | Enhanced | Not applicable | Variable / recognition |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `sort_guided` | sql | Enhanced | product_name, unit_price | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `sort_multiple_keys` | sql | Enhanced | region, plan_name, monthly_fee | 7 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `combine_top_orders` | sql | Enhanced | order_id, region, order_total | 3 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `combine_debug_clause_order` | sql | Enhanced | subscriber_id, plan_name, monthly_fee | 4 × 3 |
| SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation | `sort_mastery` | sql | Enhanced | ticket_id, priority, status, assigned_team, opened_date | 5 × 5 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_select_alias` | sql | Enhanced | item, category | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_distinct_limit` | sql | Enhanced | plan_name | 3 × 1 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_threshold` | sql | Enhanced | sku, units_on_hand | 3 × 2 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_null` | sql | Enhanced | ticket_id, resolution_hours | 7 × 2 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_boolean` | sql | Enhanced | ticket_id, priority, status | 2 × 3 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_multi_sort` | sql | Enhanced | department, full_name, hire_date | 5 × 3 |
| SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint | `checkpoint_composition` | sql | Enhanced | order_id, order_total | 3 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 1: Summary Values | `agg_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 1: Summary Values | `agg_guided` | sql | Enhanced | region, order_count | 4 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 1: Summary Values | `agg_mastery` | sql | Enhanced | status, avg_order_value | 3 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 2: One Grouping Column | `group_one_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 2: One Grouping Column | `group_one_guided` | sql | Enhanced | category, product_count | 4 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 2: One Grouping Column | `group_one_mastery` | sql | Enhanced | category, average_unit_price | 4 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 3: Multiple Grouping Columns | `group_multi_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 3: Multiple Grouping Columns | `group_multi_guided` | sql | Enhanced | region, status, order_count | 5 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 3: Multiple Grouping Columns | `group_multi_mastery` | sql | Enhanced | region, status, total_order_value | 5 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 1: Basic Transformations | `transform_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 1: Basic Transformations | `transform_guided` | sql | Enhanced | product_id, product_name, price_band | 7 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 1: Basic Transformations | `transform_mastery` | sql | Enhanced | order_id, whole_dollars | 8 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 2: Complex Transformations | `complex_transform_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 2: Complex Transformations | `complex_transform_guided` | sql | Enhanced | order_id, discounted_total | 8 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Transformation › Lesson 2: Complex Transformations | `complex_transform_mastery` | sql | Enhanced | subscriber_id, annual_value | 7 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 1: Basic Filtering | `filter_adv_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 1: Basic Filtering | `filter_adv_guided` | sql | Enhanced | order_id, region, order_total | 4 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 1: Basic Filtering | `filter_adv_mastery` | sql | Enhanced | ticket_id, priority, channel | 4 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 2: Multiple Conditions | `multi_cond_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 2: Multiple Conditions | `multi_cond_guided` | sql | Enhanced | ticket_id, priority, status | 5 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 2: Multiple Conditions | `multi_cond_mastery` | sql | Enhanced | subscriber_id, plan_name, monthly_fee | 4 × 3 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 3: Complex Filtering | `complex_filter_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 3: Complex Filtering | `complex_filter_guided` | sql | Enhanced | order_id, order_total | 3 × 2 |
| SQL Fundamentals › Intermediate SQL › Data Filtering › Lesson 3: Complex Filtering | `complex_filter_mastery` | sql | Enhanced | ticket_id, status, satisfaction_score | 7 × 3 |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 1: Conditional Transformation | `cond_transform_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 1: Conditional Transformation | `cond_transform_guided` | sql | Enhanced | order_id, value_band | 8 × 2 |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 1: Conditional Transformation | `cond_transform_mastery` | sql | Enhanced | sku, stock_risk | 6 × 2 |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 2: Conditional Aggregation | `cond_metric_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 2: Conditional Aggregation | `cond_metric_guided` | sql | Enhanced | completed_orders, total_orders | 1 × 2 |
| SQL Fundamentals › Intermediate SQL › Conditional Operations › Lesson 2: Conditional Aggregation | `cond_metric_mastery` | sql | Enhanced | assigned_team, unresolved_tickets | 3 × 2 |
| SQL Fundamentals › Intermediate SQL › Checkpoint: Intermediate SQL Checkpoint | `int_cp_1_question` | sql | Enhanced | region, total_order_value | 4 × 2 |
| SQL Fundamentals › Intermediate SQL › Checkpoint: Intermediate SQL Checkpoint | `int_cp_2_question` | sql | Enhanced | product_id, price_band | 7 × 2 |
| SQL Fundamentals › Intermediate SQL › Checkpoint: Intermediate SQL Checkpoint | `int_cp_3_question` | sql | Enhanced | ticket_id | 5 × 1 |
| SQL Fundamentals › Intermediate SQL › Checkpoint: Intermediate SQL Checkpoint | `int_cp_4_question` | sql | Enhanced | region, completed_value | 4 × 2 |
| SQL Fundamentals › Intermediate SQL › Skills Lab: Bonus Project — Analyzing Students' Mental Health | `student_wellbeing_analysis_query` | sql | Enhanced | program_level, stay_group, student_count, average_wellbeing, average_anxiety | 6 × 5 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Vertically › Lesson 1: Stacking Rows with UNION | `union_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Joining Data in SQL › Combining Data Vertically › Lesson 1: Stacking Rows with UNION | `union_guided` | sql | Enhanced | region | 4 × 1 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Vertically › Lesson 1: Stacking Rows with UNION | `union_mastery` | sql | Enhanced | customer_id | 10 × 1 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 1: Keeping All Rows with LEFT JOIN | `left_join_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 1: Keeping All Rows with LEFT JOIN | `left_join_guided` | sql | Enhanced | customer_id, customer_name, order_id | 7 × 3 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 1: Keeping All Rows with LEFT JOIN | `left_join_mastery` | sql | Enhanced | customer_id, customer_name | 0 × 2 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 2: Keeping Matching Rows with INNER JOIN | `join_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 2: Keeping Matching Rows with INNER JOIN | `join_guided` | sql | Enhanced | order_id, customer_id, ticket_id | 8 × 3 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 2: Keeping Matching Rows with INNER JOIN | `join_mastery` | sql | Enhanced | customer_id, ticket_count | 8 × 2 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 3: Joining on Multiple Columns | `multi_join_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 3: Joining on Multiple Columns | `multi_join_guided` | sql | Enhanced | region, month_start, sales_total, sales_target | 6 × 4 |
| SQL Fundamentals › Joining Data in SQL › Combining Data Horizontally › Lesson 3: Joining on Multiple Columns | `multi_join_mastery` | sql | Enhanced | region, month_start, variance_to_target | 6 × 3 |
| SQL Fundamentals › Joining Data in SQL › Checkpoint: Joining Data in SQL Checkpoint | `join_cp_1_question` | sql | Enhanced | order_id, customer_name | 7 × 2 |
| SQL Fundamentals › Joining Data in SQL › Checkpoint: Joining Data in SQL Checkpoint | `join_cp_2_question` | sql | Enhanced | product_id, product_name, quantity | 10 × 3 |
| SQL Fundamentals › Joining Data in SQL › Checkpoint: Joining Data in SQL Checkpoint | `join_cp_3_question` | sql | Enhanced | region, month_start, sales_target | 6 × 3 |
| SQL Fundamentals › Data Manipulation in SQL › We'll Take the CASE › Lesson 1: Business Rules with CASE | `case_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Data Manipulation in SQL › We'll Take the CASE › Lesson 1: Business Rules with CASE | `case_guided` | sql | Enhanced | order_id, workflow_label | 8 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › We'll Take the CASE › Lesson 1: Business Rules with CASE | `case_mastery` | sql | Enhanced | ticket_id, response_tier | 10 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Short and Simple Subqueries › Lesson 1: Subqueries | `subquery_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Data Manipulation in SQL › Short and Simple Subqueries › Lesson 1: Subqueries | `subquery_guided` | sql | Enhanced | order_id, order_total | 4 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Short and Simple Subqueries › Lesson 1: Subqueries | `subquery_mastery` | sql | Enhanced | order_id, customer_id | 2 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Correlated Queries, Nested Queries, and Common Table Expressions › Lesson 1: Correlated Queries and CTEs | `cte_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Data Manipulation in SQL › Correlated Queries, Nested Queries, and Common Table Expressions › Lesson 1: Correlated Queries and CTEs | `cte_guided` | sql | Enhanced | region, total_order_value | 4 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Correlated Queries, Nested Queries, and Common Table Expressions › Lesson 1: Correlated Queries and CTEs | `cte_mastery` | sql | Enhanced | order_id, region, order_total | 4 × 3 |
| SQL Fundamentals › Data Manipulation in SQL › Window Functions › Lesson 1: Window Functions | `window_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Data Manipulation in SQL › Window Functions › Lesson 1: Window Functions | `window_guided` | sql | Enhanced | order_id, region, order_total, region_order_number | 8 × 4 |
| SQL Fundamentals › Data Manipulation in SQL › Window Functions › Lesson 1: Window Functions | `window_mastery` | sql | Enhanced | order_id, order_date, order_total, running_order_total | 8 × 4 |
| SQL Fundamentals › Data Manipulation in SQL › Checkpoint: Data Manipulation in SQL Checkpoint | `manip_cp_1_question` | sql | Enhanced | order_id, workflow | 8 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Checkpoint: Data Manipulation in SQL Checkpoint | `manip_cp_2_question` | sql | Enhanced | order_id, order_total | 4 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Checkpoint: Data Manipulation in SQL Checkpoint | `manip_cp_3_question` | sql | Enhanced | region, total_order_value | 4 × 2 |
| SQL Fundamentals › Data Manipulation in SQL › Checkpoint: Data Manipulation in SQL Checkpoint | `manip_cp_4_question` | sql | Enhanced | order_id, order_total, value_rank | 8 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Introduction to Window Functions › Lesson 1: Window Functions versus GROUP BY | `win_basic_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Introduction to Window Functions › Lesson 1: Window Functions versus GROUP BY | `win_basic_guided` | sql | Enhanced | order_id, region, order_total, regional_average | 8 × 4 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Introduction to Window Functions › Lesson 1: Window Functions versus GROUP BY | `win_basic_mastery` | sql | Enhanced | order_id, region, regional_order_number | 8 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Fetching, Ranking, and Paging › Lesson 1: Fetching, Ranking, and Paging | `win_rank_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Fetching, Ranking, and Paging › Lesson 1: Fetching, Ranking, and Paging | `win_rank_guided` | sql | Enhanced | region, month_start, sales_total, prior_sales | 6 × 4 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Fetching, Ranking, and Paging › Lesson 1: Fetching, Ranking, and Paging | `win_rank_mastery` | sql | Enhanced | region, month_start, sales_total, sales_rank | 6 × 4 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Aggregate Window Functions and Frames › Lesson 1: Aggregate Window Functions and Frames | `win_frame_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Aggregate Window Functions and Frames › Lesson 1: Aggregate Window Functions and Frames | `win_frame_guided` | sql | Enhanced | region, month_start, sales_total, running_sales | 6 × 4 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Aggregate Window Functions and Frames › Lesson 1: Aggregate Window Functions and Frames | `win_frame_mastery` | sql | Enhanced | region, month_start, moving_average | 6 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Beyond Window Functions › Lesson 1: Beyond Window Functions | `win_beyond_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Beyond Window Functions › Lesson 1: Beyond Window Functions | `win_beyond_guided` | sql | Enhanced | region, completed_orders, processing_orders | 4 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Beyond Window Functions › Lesson 1: Beyond Window Functions | `win_beyond_mastery` | sql | Enhanced | region, status, order_count | 10 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Checkpoint: PostgreSQL Summary Stats and Window Functions Checkpoint | `win_cp_1_question` | sql | Enhanced | order_id, row_num | 8 × 2 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Checkpoint: PostgreSQL Summary Stats and Window Functions Checkpoint | `win_cp_2_question` | sql | Enhanced | region, month_start, prior_sales | 6 × 3 |
| SQL Fundamentals › PostgreSQL Summary Stats and Window Functions › Checkpoint: PostgreSQL Summary Stats and Window Functions Checkpoint | `win_cp_3_question` | sql | Enhanced | region, month_start, running_sales | 6 × 3 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Overview of Common Data Types › Lesson 1: Overview of Common Data Types | `pg_types_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Overview of Common Data Types › Lesson 1: Overview of Common Data Types | `pg_types_guided` | sql | Enhanced | subscriber_id, fee_whole_dollars | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Overview of Common Data Types › Lesson 1: Overview of Common Data Types | `pg_types_mastery` | sql | Enhanced | product_id, product_id_text | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Working with DATE/TIME Functions and Operators › Lesson 1: Working with DATE/TIME Functions and Operators | `date_time_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Working with DATE/TIME Functions and Operators › Lesson 1: Working with DATE/TIME Functions and Operators | `date_time_guided` | sql | Enhanced | order_id, order_month | 8 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Working with DATE/TIME Functions and Operators › Lesson 1: Working with DATE/TIME Functions and Operators | `date_time_mastery` | sql | Enhanced | customer_id, tenure_days | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Parsing and Manipulating Text › Lesson 1: Parsing and Manipulating Text | `text_func_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Parsing and Manipulating Text › Lesson 1: Parsing and Manipulating Text | `text_func_guided` | sql | Enhanced | product_id, product_label | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Parsing and Manipulating Text › Lesson 1: Parsing and Manipulating Text | `text_func_mastery` | sql | Enhanced | customer_id, first_initial | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Full-Text Search and PostgreSQL Extensions › Lesson 1: Full-Text Search and PostgreSQL Extensions | `sql_search_extensions_1_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Full-Text Search and PostgreSQL Extensions › Lesson 1: Full-Text Search and PostgreSQL Extensions | `sql_search_extensions_2_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Full-Text Search and PostgreSQL Extensions › Lesson 1: Full-Text Search and PostgreSQL Extensions | `sql_search_extensions_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Checkpoint: Functions for Manipulating Data in PostgreSQL Checkpoint | `func_cp_1_question` | sql | Enhanced | order_id, order_year | 8 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Checkpoint: Functions for Manipulating Data in PostgreSQL Checkpoint | `func_cp_2_question` | sql | Enhanced | subscriber_id, plan_name_upper | 7 × 2 |
| SQL Fundamentals › Functions for Manipulating Data in PostgreSQL › Checkpoint: Functions for Manipulating Data in PostgreSQL Checkpoint | `func_cp_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Processing, Storing, and Organizing Data › Lesson 1: Processing, Storage, and Data Models | `database_processing_models_1_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Processing, Storing, and Organizing Data › Lesson 1: Processing, Storage, and Data Models | `database_processing_models_2_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Processing, Storing, and Organizing Data › Lesson 1: Processing, Storage, and Data Models | `database_processing_models_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Schemas and Normalization › Lesson 1: Schemas and Normalization | `database_schemas_normalization_1_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Schemas and Normalization › Lesson 1: Schemas and Normalization | `database_schemas_normalization_2_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Schemas and Normalization › Lesson 1: Schemas and Normalization | `database_schemas_normalization_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Views › Lesson 1: Views and Materialized Views | `database_views_1_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Views › Lesson 1: Views and Materialized Views | `database_views_2_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Views › Lesson 1: Views and Materialized Views | `database_views_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Management › Lesson 1: Database Management Decisions | `database_management_1_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Management › Lesson 1: Database Management Decisions | `database_management_2_recognition` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Database Management › Lesson 1: Database Management Decisions | `database_management_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Checkpoint: Database Design Checkpoint | `db_cp_1_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Checkpoint: Database Design Checkpoint | `db_cp_2_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Checkpoint: Database Design Checkpoint | `db_cp_3_mastery` | recognition | Already clear | Not applicable | Variable / recognition |
| SQL Fundamentals › Database Design › Skills Lab: Bonus Project — Impact Analysis of GoodThought NGO Initiatives | `community_impact_analysis_query` | sql | Enhanced | program_area, region, project_count, total_funding, total_people_reached, cost_per_person | 5 × 6 |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 1: Getting Started with Power BI | `powerbi_getting_started_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 1: Getting Started with Power BI | `powerbi_getting_started_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 1: Getting Started with Power BI | `powerbi_getting_started_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 2: Transforming Data | `powerbi_transforming_data_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 2: Transforming Data | `powerbi_transforming_data_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 2: Transforming Data | `powerbi_transforming_data_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 3: Visualizing Data | `powerbi_visualizing_data_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 3: Visualizing Data | `powerbi_visualizing_data_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 3: Visualizing Data | `powerbi_visualizing_data_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 4: Filtering and Interaction | `powerbi_filtering_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 4: Filtering and Interaction | `powerbi_filtering_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Power BI Foundations › Power BI Foundations › Lesson 4: Filtering and Interaction | `powerbi_filtering_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 1: Defining Tables | `powerbi_defining_tables_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 1: Defining Tables | `powerbi_defining_tables_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 1: Defining Tables | `powerbi_defining_tables_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 2: Shaping Tables | `powerbi_shaping_tables_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 2: Shaping Tables | `powerbi_shaping_tables_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 2: Shaping Tables | `powerbi_shaping_tables_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 3: Dimensional Modeling | `powerbi_dimensional_modeling_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 3: Dimensional Modeling | `powerbi_dimensional_modeling_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 3: Dimensional Modeling | `powerbi_dimensional_modeling_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 4: Star and Snowflake Schemas | `powerbi_star_schema_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 4: Star and Snowflake Schemas | `powerbi_star_schema_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Power BI for Data Analysts › Data Modeling in Power BI › Data Modeling in Power BI › Lesson 4: Star and Snowflake Schemas | `powerbi_star_schema_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 1: Python Basics | `python_basics_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 1: Python Basics | `python_basics_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 1: Python Basics | `python_basics_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 2: Python Lists | `python_lists_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 2: Python Lists | `python_lists_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 2: Python Lists | `python_lists_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 3: Functions and Packages | `python_functions_packages_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 3: Functions and Packages | `python_functions_packages_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 3: Functions and Packages | `python_functions_packages_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 4: NumPy Arrays | `python_numpy_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 4: NumPy Arrays | `python_numpy_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › Python Foundations › Python Foundations › Lesson 4: NumPy Arrays | `python_numpy_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 1: Transforming DataFrames | `pandas_transforming_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 1: Transforming DataFrames | `pandas_transforming_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 1: Transforming DataFrames | `pandas_transforming_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 2: Aggregating DataFrames | `pandas_aggregating_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 2: Aggregating DataFrames | `pandas_aggregating_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 2: Aggregating DataFrames | `pandas_aggregating_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 3: Slicing and Indexing DataFrames | `pandas_indexing_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 3: Slicing and Indexing DataFrames | `pandas_indexing_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 3: Slicing and Indexing DataFrames | `pandas_indexing_step_3` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 4: Creating and Visualizing DataFrames | `pandas_visualization_step_1` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 4: Creating and Visualizing DataFrames | `pandas_visualization_step_2` | recognition | Already clear | Not applicable | Variable / recognition |
| Python for Data Analysts › pandas Foundations › pandas Foundations › Lesson 4: Creating and Visualizing DataFrames | `pandas_visualization_step_3` | recognition | Already clear | Not applicable | Variable / recognition |

## Automatically corrected source gaps

- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL / structure_grain_recognition: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL / structure_type_recognition: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL / structure_guided: exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 1: Meet Databases & SQL / structure_debug: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL / select_projection_recognition: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL / select_guided: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL / alias_guided: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL / alias_debug: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 2: Write Your First SQL / alias_mastery: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results / distinct_limit_independent: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 3: Customize Query Results / distinct_limit_mastery: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_operator_recognition: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_text_guided: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_threshold: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_and_guided: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_parentheses_transfer: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_null_debug: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 4: Filter the Rows You Need / filter_mastery: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation / sort_guided: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation / sort_multiple_keys: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation / combine_top_orders: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation / combine_debug_clause_order: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Introduction to SQL › Lesson 5: Complete Your SQL Foundation / sort_mastery: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_select_alias: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_distinct_limit: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_threshold: short task replaced by full prompt.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_null: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_boolean: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_multi_sort: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Introduction to SQL › Checkpoint: Introduction to SQL Checkpoint / checkpoint_composition: short task replaced by full prompt; exact output columns added.
- SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 1: Summary Values / agg_guided: exact output columns added.
- SQL Fundamentals › Intermediate SQL › Data Aggregation › Lesson 1: Summary Values / agg_mastery: exact output columns added.

## Result

**PASS — every installed Academy learning action has complete learner-facing instructions.**
