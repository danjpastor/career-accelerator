# DuckDB Exercise 06: Join customers, orders, and payments

**Week:** 4
**Estimated time:** 45 minutes  
**Concepts:** INNER JOIN, LEFT JOIN, multi-table joins

## Scenario

Finance and Customer Success need one reliable view that connects customers, orders, and payments without dropping or duplicating important records.

## Tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Source CSV files

- `customers.csv`
- `orders.csv`
- `payments.csv`

## Tasks

### Task 1

Check how many orders have a matching customer record. Use an inner join and return the count as `matched_orders`.

**Result requirements**

- Return columns in this order: `matched_orders`.
- Return 1 row.

### Task 2

Check that a left join keeps customers who have no orders. Return the number of rows produced by the join as `customer_order_rows`.

**Result requirements**

- Return columns in this order: `customer_order_rows`.
- Return 1 row.

### Task 3

Find customers with no orders.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 1 row.

### Task 4

Join orders to payments and identify orders with no payment.

**Result requirements**

- Return columns in this order: `order_id`.
- Return 2 rows.

### Task 5

Join customers, orders, and payments, then count the rows in the combined result. Return the count as `joined_payment_rows`.

**Result requirements**

- Return columns in this order: `joined_payment_rows`.
- Return 1 row.

### Task 6

Show delivered-order revenue by customer region. Return `region` and the total as `delivered_revenue`.

**Result requirements**

- Return columns in this order: `region`, `delivered_revenue`.
- Return 4 rows.

### Task 7

Calculate customer lifetime delivered revenue, including customers with zero.

**Result requirements**

- Return columns in this order: `customer_id`, `revenue`.
- Return 10 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

