-- DuckDB Exercise 32: Complete an end-to-end workforce SQL assessment
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex10_departments;
DESCRIBE ex10_employees;
DESCRIBE ex10_performance_reviews;


-- -----------------------------------------------------------------
-- Q1. Task: Find employees with missing department assignments. Required output: return only these columns in this order: `employee_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Calculate salary expense and headcount by department, retaining departments with no employees. Required output: return only these columns in this order: `department_name`, `count(e.employee_id)`, `COALESCE(sum(e.annual_salary), 0)`. Use these exact names for calculated or summarized columns: `count(e.employee_id)`, `COALESCE(sum(e.annual_salary), 0)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Calculate department salary expense as a percentage of annual budget. Required output: return only these columns in this order: `department_name`, `round(((100.0 * sum(e.annual_salary)) / d.annual_budget), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * sum(e.annual_salary)) / d.annual_budget), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Return each employee's manager name using a self join. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Use a CTE to calculate each employee's average performance score. Required output: return only these columns in this order: `count_star()`, `round(avg(avg_score), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(avg(avg_score), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Rank employees within each department by average performance using `DENSE_RANK`. Required output: return only these columns in this order: `employee_id`, `dense_rank() OVER (PARTITION BY e.department_id ORDER BY s.avg_score DESC)`. Use these exact names for calculated or summarized columns: `dense_rank() OVER (PARTITION BY e.department_id ORDER BY s.avg_score DESC)`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Return employees whose salary is above their department average. Required output: return only these columns in this order: `employee_id`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q8. Task: Create a risk flag for high salary, low performance, or missing department. Required output: return only these columns in this order: `sum(CASE  WHEN (((e.department_id IS NULL) OR (e.annual_salary >= 115000) OR (s.avg_score < 4.0))) THEN (1) ELSE 0 END)`. Use these exact names for calculated or summarized columns: `sum(CASE  WHEN (((e.department_id IS NULL) OR (e.annual_salary >= 115000) OR (s.avg_score < 4.0))) THEN (1) ELSE 0 END)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
