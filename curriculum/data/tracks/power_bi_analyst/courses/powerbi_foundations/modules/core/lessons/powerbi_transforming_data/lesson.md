# Transforming Data

Power Query is Power BI's preparation area. It records each cleaning action as an **Applied Step** so the same work can run again when the source refreshes.

## Main idea

Power Query is Power BI's preparation area. It records each cleaning action as an **Applied Step** so the same work can run again when the source refreshes.

Common steps include changing data types, removing unused columns, replacing inconsistent values, splitting text, filtering invalid rows, and combining tables. The order of the steps matters. For example, a date calculation cannot work reliably until the source column has a date type.

Power Query does not rewrite the original CSV or Excel file. It creates a repeatable set of instructions that shapes the data before it is loaded into the model.

## Example

A staffing file stores `hire_date` as text. An analyst opens Power Query, changes the column to Date, and checks the preview for errors. A later refresh applies the same type change automatically. If the analyst accidentally filters out blank departments before reviewing them, those records will disappear from every report, so they inspect the Applied Steps before loading the data.
