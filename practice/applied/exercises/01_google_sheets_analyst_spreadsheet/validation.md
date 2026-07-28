# Validation checklist

- `Raw Orders` contains 24 data rows and 24 unique order IDs.
- `Targets` contains four regions.
- `Analysis` contains one row for each order.
- Region values are cleaned with `TRIM` and `PROPER` rather than edited in the raw data.
- Cancelled orders calculate zero gross and net sales.
- The 2% processing-fee reference remains fixed when formulas are copied.
- With Region set to All, the summary shows 20 completed orders, $1,650 gross sales, $1,617 net sales, and $80.85 average net order value.
- The region dropdown changes the KPI values.
- The pivot table shows January at $755 and February at $895.
- One chart and a short takeaway are complete.
