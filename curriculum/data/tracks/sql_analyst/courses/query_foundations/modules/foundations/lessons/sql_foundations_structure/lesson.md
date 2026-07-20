# Tables, Rows, Columns, and Data Types

> **Learning goal:** Build a reliable mental model of a table before you write SQL. You will learn to identify a table's grain, distinguish rows from columns, recognize common data types, and select fields without changing the source data.

## Start with the table's grain

A database table stores records about one kind of thing or event. The **grain** is the precise meaning of one row. In a support-ticket table, one row might represent one ticket. In an order-items table, one row might represent one product line inside an order. Those grains are not interchangeable.

The grain determines what you are allowed to count, compare, or summarize. If one row represents an order item, counting rows does not count customers and may not even count orders. Before every analysis, finish this sentence:

> One row in this table represents **one ______**.

That single habit prevents many analytical mistakes.

## Rows and columns answer different questions

A **row** is one record at the table's grain. A **column** is one attribute stored for every record. For example, a `warehouse_shipments` table might contain one row per shipment and columns such as `shipment_id`, `carrier_name`, `shipped_date`, and `weight_kg`.

| Structure | Meaning | Example |
|---|---|---|
| Row | One record at the table's grain | One shipment |
| Column | One property of each record | Carrier name |
| Cell | One value at the intersection of a row and column | `FedEx` |
| Table | A collection of related records | All shipments |

Columns should have a consistent meaning. A column called `opened_date` should not sometimes contain a ticket status. Consistent columns make filtering, sorting, and calculations dependable.

## Data types describe what values can do

The data type tells the database how to store and compare a value.

- **Text** stores names, labels, IDs, and categories.
- **Integer** stores whole numbers such as quantities or counts.
- **Decimal** stores values that may include fractions, such as prices or hours.
- **Date or timestamp** stores calendar dates and times.
- **Boolean** stores two logical states, commonly `TRUE` and `FALSE`.
- **NULL** represents a missing or unknown value; it is not a data type by itself.

A value that looks numeric is not always meant for arithmetic. Customer IDs, postal codes, and ticket numbers may contain digits but behave like labels. Conversely, a date stored as plain text may look correct while sorting or comparing incorrectly. Analysts should confirm both the displayed value and the underlying type.

## Column names are your query vocabulary

SQL queries refer to exact table and column names. A basic query follows this structure:

```sql
SELECT column_name
FROM table_name;
```

To return more than one column, separate the names with commas:

```sql
SELECT appointment_id, patient_name, appointment_date
FROM clinic_appointments;
```

`SELECT` chooses which columns appear in the result. `FROM` identifies the source table. This query does not edit the table; it creates a result set.

## Worked example 1: understand the grain first

Imagine a `warehouse_shipments` table with one row per shipment. A logistics analyst wants the shipment identifier and carrier:

```sql
SELECT shipment_id, carrier_name
FROM warehouse_shipments;
```

The result has the same number of rows as the source because no rows were filtered. It simply contains fewer columns.

## Worked example 2: recognize the data type

A `maintenance_requests` table contains:

| Column | Likely type | Why |
|---|---|---|
| `request_id` | Text | It is an identifier, not a measurement |
| `submitted_at` | Timestamp | It records a date and time |
| `estimated_cost` | Decimal | It may include cents |
| `is_emergency` | Boolean | It represents yes/no logic |

Understanding the type helps you predict which comparisons and operations will be valid later.

## Common mistakes

### Confusing the table grain

A table called `orders` might contain one row per order, while `order_items` contains several rows per order. Treating both as one row per order can inflate counts.

### Forgetting commas

This is invalid because the database cannot tell where one selected column ends and the next begins:

```sql
SELECT employee_id full_name department
FROM employees;
```

### Assuming `SELECT *` is always best

`SELECT *` is useful for quick inspection, but production analysis should usually name the fields it needs. Explicit columns make the result easier to read and protect the query from unexpected schema changes.

### Treating missing values as zero

A missing satisfaction score does not necessarily mean a score of zero. It may mean the survey was never completed. Later lessons will show how to test for `NULL` correctly.

## A repeatable pre-query checklist

1. State the grain in plain language.
2. Identify the table that contains the needed records.
3. Confirm the exact column names.
4. Check the relevant data types.
5. Select only the fields needed for the current question.

## Lesson recap

- A row represents one record at the table's grain.
- A column stores one attribute of every record.
- Data types determine how values can be compared and calculated.
- `SELECT` chooses result columns; `FROM` chooses the source table.
- A query returns a result set and does not modify the source table.
