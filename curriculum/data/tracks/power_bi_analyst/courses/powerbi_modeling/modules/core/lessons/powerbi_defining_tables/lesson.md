# Defining Tables

A reliable model begins with a clear definition of what each table represents. The **grain** tells you what one row means. A customer table may have one row per customer, while an orders table has one row per order and can repeat the same customer ID.

## Main idea

A reliable model begins with a clear definition of what each table represents. The **grain** tells you what one row means. A customer table may have one row per customer, while an orders table has one row per order and can repeat the same customer ID.

A key identifies or connects records. The unique key belongs on the **one** side of a relationship. The repeating key belongs on the **many** side. Before creating a relationship, check for duplicates, blanks, and unmatched values. Power BI may allow a relationship that looks reasonable but produces misleading totals when the grain is misunderstood.

## Example

A clinic model contains one row per patient in `Patients` and one row per appointment in `Appointments`. Patient ID is unique in Patients and repeats in Appointments. Patients therefore belongs on the one side of a one-to-many relationship. An appointment with a missing patient ID should be investigated rather than silently ignored.
