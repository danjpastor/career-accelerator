-- DuckDB Exercise 32: Mixed workforce assessment
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex10_departments;
DESCRIBE ex10_employees;
DESCRIBE ex10_performance_reviews;


-- -----------------------------------------------------------------
-- Q1. Find employees with missing department assignments.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Show workforce cost by department while keeping departments with no employees. Return `department_name`, employee `headcount`, and total `salary_expense`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Calculate salary expense as a percentage of annual budget for each department. Round to two decimal places and name it `salary_budget_pct`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Use a self join to connect each employee to their manager, then return the number of employee rows as `employee_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Use a CTE to calculate each employee’s average performance score. Return the number of employees as `employee_count` and the overall average of those scores, rounded to two decimal places, as `average_performance_score`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Rank employees within each department by average performance using `DENSE_RANK`. Return `employee_id` and the rank as `performance_rank`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Return employees whose salary is above their department average.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q8. Count employees flagged because they have no department, earn at least 115000, or have an average performance score below 4.0. Return the count as `risk_employee_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
